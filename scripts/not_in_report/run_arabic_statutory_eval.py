import os
import re
import math
import time
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

LOCAL_PATH = os.environ.get("FALCON_PATH", "/tmp/falcon-7b")   # folder with the local Falcon3-7B-Instruct files
RESULTS_DIR = os.environ.get("RESULTS_DIR", "results")         # where reports are written
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print(f"[*] Starte arabischen Freihand- vs. RAG-Rechtstest auf {DEVICE.upper()}...")

def normalize_digits(text):
    eastern_to_western = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    return text.translate(eastern_to_western)

tokenizer = AutoTokenizer.from_pretrained(LOCAL_PATH, local_files_only=True)
model = AutoModelForCausalLM.from_pretrained(
    LOCAL_PATH,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    local_files_only=True
)
model.eval()

def generate(messages, max_tokens=60):
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)
    t0 = time.perf_counter()
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=max_tokens, do_sample=False)
    lat = (time.perf_counter() - t0) * 1000
    gen = out[0][inputs.input_ids.shape[1]:]
    return tokenizer.decode(gen, skip_special_tokens=True).strip(), lat

# Echte VAE-Gesetzesfälle (PDPL, Arbeitsrecht, CBUAE)
legal_scenarios = [
    {
        "topic": "UAE PDPL (Datenschutzgesetz Dekret 45/2021)",
        "query": "ما هو رقم المرسوم بقانون اتحادي بشأن حماية البيانات الشخصية في دولة الإمارات وما هي أقصى عقوبة مالية منصوص عليها؟",
        "ground_truth_chunk": "وفقاً للمرسوم بقانون اتحادي رقم 45 لسنة 2021 بشأن حماية البيانات الشخصية، تتولى وكالة الإمارات للبيانات الإشراف على تطبيق القانون، وتحدد اللائحة التنفيذية الغرامات الإدارية.",
        "fact_check": "45"
    },
    {
        "topic": "UAE Labour Law (Kündigungsfristen Dekret 33/2021)",
        "query": "كم تبلغ فترة الإشعار القانونية القصوى لإنهاء عقد العمل وفقاً لقانون العمل الإماراتي الجديد؟",
        "ground_truth_chunk": "وفقاً للمادة 43 من المرسوم بقانون اتحادي رقم 33 لسنة 2021، يجب ألا تقل فترة الإشعار عن 30 يوماً ولا تزيد على 90 يوماً.",
        "fact_check": "90"
    },
    {
        "topic": "CBUAE (Zentralbank Zins- und Gebührenregeln)",
        "query": "ما هي النسبة القصوى المسموح بها للاستقطاع الشهري من الراتب لسداد القروض الشخصية في مصرف الإمارات المركزي؟",
        "ground_truth_chunk": "تحدد أنظمة مصرف الإمارات المركزي الحد الأقصى لنسبة عبء الدين (DBR) بما لا يتجاوز 50% من إجمالي الراتب أو الدخل المنتظم للعميل.",
        "fact_check": "50"
    },
    {
        "topic": "Overstay Fines (ICP Visagebühren)",
        "query": "كم تبلغ الغرامة اليومية الموحدة لمخالفي الإقامة بعد انتهاء فترة السماح في دولة الإمارات؟",
        "ground_truth_chunk": "حددت الهيئة الاتحادية للهوية والجنسية والجمارك وأمن المنافذ غرامة البقاء بصورة غير مشروعة بمبلغ 50 درهماً عن كل يوم تأخير.",
        "fact_check": "50"
    },
    {
        "topic": "DIFC Data Protection Law (Regulation 10)",
        "query": "متى أصبحت اللائحة رقم 10 بشأن أنظمة الذكاء الاصطناعي عالية المخاطر في مركز دبي المالي العالمي إلزامية؟",
        "ground_truth_chunk": "تعتبر اللائحة رقم 10 الخاصة بأنظمة الذكاء الاصطناعي ذاتية التشغيل في سلطة دبي للخدمات المالية وDIFC نافذة وقابلة للتطبيق الكامل اعتباراً من 1 يناير 2026.",
        "fact_check": "2026"
    }
]

print("\n" + "="*75)
print("VERGLEICHSLAUF: FREIHAND (PARAMETRISCH) VS. RAG + GATE")
print("="*75)

comparison_results = []

for idx, item in enumerate(legal_scenarios):
    print(f"\n[FALL {idx+1}: {item['topic']}]")
    
    # 1. Freihand-Test (Nacktes Modell, kein Kontext)
    msg_free = [
        {"role": "system", "content": "أنت مستشار قانوني خبير في تشريعات دولة الإمارات العربية المتحدة. أجب بدقة واقتضاب."},
        {"role": "user", "content": item["query"]}
    ]
    out_free, lat_free = generate(msg_free, max_tokens=50)
    norm_free = normalize_digits(out_free)
    free_has_fact = item["fact_check"] in norm_free
    
    # 2. RAG-Test (Mit offiziellem Gesetzes-Chunk)
    msg_rag = [
        {"role": "system", "content": f"وثيقة رسمية من التشريعات الإماراتية:\n{item['ground_truth_chunk']}\n\nالقاعدة: أجب فقط بدقة وبشكل حصري من واقع الوثيقة أعلاه."},
        {"role": "user", "content": item["query"]}
    ]
    out_rag, lat_rag = generate(msg_rag, max_tokens=50)
    norm_rag = normalize_digits(out_rag)
    rag_has_fact = item["fact_check"] in norm_rag

    print(f"├─ Frage: {item['query']}")
    print(f"├─ Freihand (Ohne RAG): '{out_free}' ({lat_free:.1f}ms) -> {'Term gefunden' if free_has_fact else 'Term fehlt'}")
    print(f"└─ RAG-Grounded:        '{out_rag}' ({lat_rag:.1f}ms) -> {'Term gefunden' if rag_has_fact else 'Term fehlt'}")

    comparison_results.append({
        "topic": item["topic"],
        "query": item["query"],
        "free_output": out_free,
        "free_correct": free_has_fact,
        "rag_output": out_rag,
        "rag_correct": rag_has_fact
    })

# Report-Generierung
report_md = f"""# UAE Statutory Intelligence Benchmark: Parametric vs. Grounded
**Target Model:** `Falcon3-7B-Instruct`
**Evaluation Language:** Native Arabic (UAE Regulatory Lexicon)
**Hardware:** {torch.cuda.get_device_name(0)} | Precision: BF16

---

## 1. Comparative Results Table

| Legal Domain / Regulation | Freihand (Parametrischer Bauch) | RAG-Grounded (Mit Chunk) | Delta / Fazit |
| :--- | :--- | :--- | :--- |
"""

for r in comparison_results:
    report_md += f"| **{r['topic']}** | {'Term gefunden' if r['free_correct'] else 'Term fehlt'} | {'Term gefunden' if r['rag_correct'] else 'Term fehlt'} | {'nur mit Chunk gefunden' if not r['free_correct'] and r['rag_correct'] else 'in beiden gleich'} |\n"

report_md += f"""
---

## 2. Qualitative Trace Samples

"""

for idx, r in enumerate(comparison_results):
    report_md += f"""### Fall {idx+1}: {r['topic']}
* **Frage:** {r['query']}
* **Freihand-Antwort:** "{r['free_output']}"
* **RAG-Grounded Antwort:** "{r['rag_output']}"

"""

with open(os.path.join(RESULTS_DIR, "SOVEREIGN_STATUTORY_COMPARISON_AR.md"), "w", encoding="utf-8") as f:
    f.write(report_md)

print("\n" + "="*75)
print(f"[+] Vergleichslauf abgeschlossen! Report liegt unter: {RESULTS_DIR}/SOVEREIGN_STATUTORY_COMPARISON_AR.md")
print("="*75)
