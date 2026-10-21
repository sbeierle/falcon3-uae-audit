import os
import re
import json
import time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

LOCAL_PATH = os.environ.get("FALCON_PATH", "/tmp/falcon-7b")   # folder with the local Falcon3-7B-Instruct files
RESULTS_DIR = os.environ.get("RESULTS_DIR", "results")         # where reports are written
CHUNKS_PATH = os.environ.get("CHUNKS_PATH", "data/uae_statutory_chunks.json")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print(f"[*] Initialisiere VAE Gesetzestexte RAG vs. Freihand Benchmark auf {DEVICE.upper()}...")

# 1. Lade Chunks
if not os.path.exists(CHUNKS_PATH):
    print(f"[-] FEHLER: {CHUNKS_PATH} nicht gefunden.")
    exit(1)

with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
    chunks_data = json.load(f)

# 2. Modell & Tokenizer laden
tokenizer = AutoTokenizer.from_pretrained(LOCAL_PATH, local_files_only=True)
model = AutoModelForCausalLM.from_pretrained(
    LOCAL_PATH,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    local_files_only=True
)
model.eval()

def generate(messages, max_tokens=70):
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)
    t0 = time.perf_counter()
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=max_tokens, do_sample=False)
    lat = (time.perf_counter() - t0) * 1000
    gen = out[0][inputs.input_ids.shape[1]:]
    return tokenizer.decode(gen, skip_special_tokens=True).strip(), lat

def normalize_digits(text):
    eastern_to_western = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    return text.translate(eastern_to_western)

# Spezifische Fragen zu jedem Chunk
queries = {
    "PDPL_PRIVACY": {
        "q": "ما هي المتطلبات الأساسية لمعالجة البيانات الشخصية وفقاً للمرسوم بقانون اتحادي رقم 45 لسنة 2021؟",
        "fact_check": ["45", "نزاهة", "شفافية", "سرية"]
    },
    "LABOUR_LAW": {
        "q": "ما هي الحدود القانونية الدنيا والقصوى لفترة الإشعار لإنهاء عقد العمل وفقاً للمادة 43 من قانون العمل الإماراتي؟",
        "fact_check": ["30", "90"]
    },
    "CBUAE_BANKING": {
        "q": "ما هو الحد الأقصى المسموح به لنسبة عبء الدين (DBR) وفقاً لأنظمة مصرف الإمارات المركزي؟",
        "fact_check": ["50"]
    },
    "ICP_IMMIGRATION": {
        "q": "كم تبلغ الغرامة اليومية الموحدة المقررة لمخالفي الإقامة بعد انتهاء فترة السماح؟",
        "fact_check": ["50"]
    },
    "DIFC_AI_GOVERNANCE": {
        "q": "متى تصبح اللائحة رقم 10 بشأن أنظمة الذكاء الاصطناعي ذاتية التشغيل في مركز دبي المالي العالمي (DIFC) نافذة بشكل إلزامي؟",
        "fact_check": ["2026", "يناير"]
    }
}

benchmark_results = []

print("\n" + "="*75)
print("DURCHLAUF: FREIHAND (ZERO-SHOT) VS. RAG-GROUNDED")
print("="*75)

for item in chunks_data:
    dom = item["domain"]
    q_data = queries.get(dom)
    if not q_data:
        continue
        
    query = q_data["q"]
    fact_terms = q_data["fact_check"]
    
    print(f"\n[DOMÄNE: {dom}] - {item['law_reference']}")
    
    # 1. Freihand-Test
    msg_free = [
        {"role": "system", "content": "أنت مستشار قانوني خبير في تشريعات دولة الإمارات العربية المتحدة. أجب باختصار ودقة."},
        {"role": "user", "content": query}
    ]
    out_free, lat_free = generate(msg_free, max_tokens=70)
    norm_free = normalize_digits(out_free)
    # NOTE (scoring rule of the original run): regime A passes only if ALL terms appear, regime B (below) if ANY one appears.
    # The asymmetry favours B. checks/rescore_ab_both_rules.py scores both rules. Logic left unchanged on purpose.
    free_passed = all(t in norm_free for t in fact_terms)
    
    # 2. RAG-Grounded Test
    msg_rag = [
        {"role": "system", "content": f"وثيقة تشريعية رسمية:\n{item['chunk_ar']}\n\nالقاعدة: أجب بدقة واقتصر بشكل حصري على المعلومات والوقائع الواردة في الوثيقة أعلاه."},
        {"role": "user", "content": query}
    ]
    out_rag, lat_rag = generate(msg_rag, max_tokens=70)
    norm_rag = normalize_digits(out_rag)
    rag_passed = any(t in norm_rag for t in fact_terms)
    
    print(f"├─ Frage: {query}")
    print(f"├─ Freihand : '{out_free[:80]}...' ({lat_free:.1f}ms) -> {'alle Terme vorhanden' if free_passed else 'nicht alle Terme'}")
    print(f"└─ RAG      : '{out_rag[:80]}...' ({lat_rag:.1f}ms) -> {'mind. ein Term' if rag_passed else 'kein Term'}")
    
    benchmark_results.append({
        "domain": dom,
        "law_reference": item["law_reference"],
        "article": item["article"],
        "chunk_ar": item["chunk_ar"],
        "query": query,
        "free_output": out_free,
        "free_lat": round(lat_free, 1),
        "free_passed": free_passed,
        "rag_output": out_rag,
        "rag_lat": round(lat_rag, 1),
        "rag_passed": rag_passed
    })

# -------------------------------------------------------------
# HTML-Report generieren
# -------------------------------------------------------------
html_code = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<title>مقارنة الأداء التشريعي: التوليد الحر مقابل الاسترجاع المعزز (RAG)</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0b0f19;
    --card: #111827;
    --border: #1f2937;
    --text: #f3f4f6;
    --muted: #9ca3af;
    --red: #ef4444;
    --green: #10b981;
    --yellow: #f59e0b;
    --cyan: #06b6d4;
  }
  body {
    background-color: var(--bg);
    color: var(--text);
    font-family: 'Cairo', sans-serif;
    margin: 0;
    padding: 30px;
    direction: rtl;
  }
  .container {
    max-width: 1200px;
    margin: 0 auto;
  }
  .header {
    border: 1px solid var(--cyan);
    background: rgba(6, 182, 212, 0.05);
    padding: 25px;
    border-radius: 8px;
    margin-bottom: 25px;
    box-shadow: 0 0 15px rgba(6, 182, 212, 0.1);
  }
  .header h1 {
    margin: 0 0 10px 0;
    font-size: 22px;
    color: var(--cyan);
    font-weight: 900;
  }
  .header .meta {
    font-size: 14px;
    color: var(--muted);
    direction: ltr;
    text-align: right;
  }
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 25px;
  }
  .law-title {
    font-size: 18px;
    font-weight: 700;
    color: var(--cyan);
    margin-bottom: 5px;
  }
  .law-article {
    font-size: 13px;
    color: var(--muted);
    margin-bottom: 15px;
  }
  .chunk-box {
    background: rgba(255, 255, 255, 0.02);
    border-right: 3px solid var(--cyan);
    padding: 12px 15px;
    font-size: 13px;
    margin-bottom: 15px;
    border-radius: 0 4px 4px 0;
  }
  .query-box {
    font-weight: 700;
    font-size: 15px;
    margin-bottom: 15px;
    padding: 10px;
    background: #1f2937;
    border-radius: 4px;
  }
  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
  }
  .col {
    background: #0f172a;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 15px;
  }
  .col-title {
    font-weight: 700;
    font-size: 14px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .badge {
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 700;
  }
  .badge-red { background: rgba(239, 68, 68, 0.2); color: var(--red); border: 1px solid var(--red); }
  .badge-green { background: rgba(16, 185, 129, 0.2); color: var(--green); border: 1px solid var(--green); }
  .output-text {
    font-size: 14px;
    line-height: 1.6;
    min-height: 70px;
  }
  .latency {
    font-size: 11px;
    color: var(--muted);
    font-family: monospace;
    direction: ltr;
    display: inline-block;
  }
  .verdict-box {
    border: 1px solid var(--cyan);
    background: rgba(6, 182, 212, 0.03);
    padding: 20px;
    border-radius: 8px;
    margin-top: 30px;
  }
</style>
</head>
<body>

<div class="container">
  <div class="header">
    <h1>المقارنة التشريعية المقارنة: التوليد الحر (Parametric) مقابل منظومة الاسترجاع السيادية (RAG)</h1>
    <div class="meta">Model: Falcon3-7B-Instruct | Target Environment: NVIDIA RTX PRO 6000 Blackwell MIG (BF16)</div>
  </div>
"""

for r in benchmark_results:
    free_badge = '<span class="badge badge-green">all terms present</span>' if r['free_passed'] else '<span class="badge badge-red">not all terms</span>'
    rag_badge = '<span class="badge badge-green">at least one term</span>' if r['rag_passed'] else '<span class="badge badge-red">no term</span>'
    
    html_code += f"""
  <div class="card">
    <div class="law-title">{r['law_reference']}</div>
    <div class="law-article">{r['article']}</div>
    
    <div class="chunk-box">
      <b>Context chunk (author's paraphrase, not an official text):</b><br>
      {r['chunk_ar']}
    </div>
    
    <div class="query-box">
      السؤال المطروح: {r['query']}
    </div>
    
    <div class="grid">
      <!-- Freihand -->
      <div class="col" style="border-top: 3px solid var(--red);">
        <div class="col-title">
          <span>التوليد الحر (بدون RAG / الذاكرة المعرفية)</span>
          <div>
            {free_badge}
            <span class="latency">({r['free_lat']} ms)</span>
          </div>
        </div>
        <div class="output-text">
          {r['free_output']}
        </div>
      </div>
      
      <!-- RAG Grounded -->
      <div class="col" style="border-top: 3px solid var(--green);">
        <div class="col-title">
          <span>الاسترجاع السيادي المؤرض (Grounded RAG)</span>
          <div>
            {rag_badge}
            <span class="latency">({r['rag_lat']} ms)</span>
          </div>
        </div>
        <div class="output-text">
          {r['rag_output']}
        </div>
      </div>
    </div>
  </div>
"""

html_code += """
  <div class="verdict-box" dir="ltr" style="direction:ltr; text-align:left;">
    <h3 style="margin-top:0; color:var(--cyan);">Notes</h3>
    <p style="margin-bottom:8px;">1. Five questions, one model configuration, greedy decoding. Regime A counts as passed only if all expected terms appear, regime B if at least one appears; the rules are not symmetric.</p>
    <p style="margin-bottom:8px;">2. The chunks are the author's paraphrases, not official texts. Regime B shows that the model copies a figure present in its context, not that the figure is legally correct.</p>
    <p style="margin-bottom:0;">3. Latency depends mostly on answer length. This page is an observation, not a compliance statement.</p>
  </div>
</div>

</body>
</html>
"""

os.makedirs(RESULTS_DIR, exist_ok=True)
html_out_path = os.path.join(RESULTS_DIR, "uae_statutory_rag_comparison.html")
with open(html_out_path, "w", encoding="utf-8") as f:
    f.write(html_code)

print(f"\n[+] Vergleich erfolgreich abgeschlossen!")
print(f"[+] Fertiger HTML-Report generiert: {html_out_path}")
