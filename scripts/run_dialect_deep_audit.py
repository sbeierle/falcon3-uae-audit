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

print(f"[*] Starte tiefen Dialekt-Audit (Khaleeji vs. Levante) auf {DEVICE.upper()}...")

def wilson_score_interval(successes, total, confidence=0.95):
    if total == 0:
        return 0.0, 0.0, 0.0
    z = 1.95996
    p_hat = successes / total
    denominator = 1 + (z**2) / total
    centre_adj = p_hat + (z**2) / (2 * total)
    adj_std = math.sqrt((p_hat * (1 - p_hat) + (z**2) / (4 * total)) / total)
    lower = (centre_adj - z * adj_std) / denominator
    upper = (centre_adj + z * adj_std) / denominator
    return p_hat, max(0.0, lower), min(1.0, upper)

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

def generate(messages, max_tokens=50):
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)
    t0 = time.perf_counter()
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=max_tokens, do_sample=False)
    lat = (time.perf_counter() - t0) * 1000
    gen = out[0][inputs.input_ids.shape[1]:]
    return tokenizer.decode(gen, skip_special_tokens=True).strip(), lat

# ---------------------------------------------------------
# Testkorpus: 20x Khaleeji (Golf) & 20x Levante (Shami)
# ---------------------------------------------------------
dialect_cases = []

# 20 Khaleeji Prompts (Emirati / Saudi Slang in arabischer Schrift)
khaleeji_templates = [
    ("كم الرسوم حق تجديد الرخصة وكم يبيلي ادفع؟", "رسوم تجديد الرخصة المهنية هي {fee} درهم إماراتي."),
    ("شلون اقدر اعرف الغرامة اللي علي بخصوص التأخير؟", "تبلغ غرامة التأخير المسجلة في النظام {fine} درهم."),
    ("وش هي المدة مالت الإشعار عشان اكنسل العقد؟", "تحدد اللائحة فترة الإشعار الرسمية بـ {days} يوماً عمل."),
    ("ابي اعرف كم لازم ادفع عشان اصدر الفيزا حق السايق؟", "تكلفة إصدار تصريح الإقامة المعتمدة هي {fee} درهم.")
]

for i in range(1, 21):
    tmpl_q, tmpl_c = khaleeji_templates[(i - 1) % len(khaleeji_templates)]
    val = 150 + i * 15
    context = tmpl_c.format(fee=val, fine=val, days=val)
    dialect_cases.append({
        "id": f"KHALEEJI_{i:02d}",
        "dialect": "Khaleeji (Golf-Arabisch)",
        "query": tmpl_q,
        "context": context,
        "expected_fact": str(val)
    })

# 20 Levantine Prompts (Shami / Libanesisch-Syrisch in arabischer Schrift)
shami_templates = [
    ("بدي اعرف قديش لازم ادفع مشان جدد الرخصة تبعي؟", "رسوم تجديد الرخصة المهنية هي {fee} درهم إماراتي."),
    ("قدي طالع علي غرامة تأخير بالسيستم ازا بتريد؟", "تبلغ غرامة التأخير المسجلة في النظام {fine} درهم."),
    ("شو هي المهلة تبع الإنذار كرمال وقف العقد هاد؟", "تحدد اللائحة فترة الإشعار الرسمية بـ {days} يوماً عمل."),
    ("عم دور ع تكلفة الفيزا مشان العامل، قدي بتكلف؟", "تكلفة إصدار تصريح الإقامة المعتمدة هي {fee} درهم.")
]

for i in range(1, 21):
    tmpl_q, tmpl_c = shami_templates[(i - 1) % len(shami_templates)]
    val = 200 + i * 20
    context = tmpl_c.format(fee=val, fine=val, days=val)
    dialect_cases.append({
        "id": f"SHAMI_{i:02d}",
        "dialect": "Levantine (Shami)",
        "query": tmpl_q,
        "context": context,
        "expected_fact": str(val)
    })

print(f"[*] Führe {len(dialect_cases)} Dialekt-RAG-Inferenzzyklen durch...")

khaleeji_hits = 0
shami_hits = 0
latencies_khaleeji = []
latencies_shami = []

sample_khaleeji_q, sample_khaleeji_out = "", ""
sample_shami_q, sample_shami_out = "", ""

for idx, item in enumerate(dialect_cases):
    messages = [
        {"role": "system", "content": f"وثيقة رسمية:\n{item['context']}\n\nالقاعدة: أجب بدقة واستخرج الرقم المطلوب حصراً من الوثيقة."},
        {"role": "user", "content": item["query"]}
    ]
    out, lat = generate(messages, max_tokens=30)
    norm_out = normalize_digits(out)
    
    is_hit = item["expected_fact"] in norm_out
    
    if item["dialect"] == "Khaleeji (Golf-Arabisch)":
        latencies_khaleeji.append(lat)
        if is_hit: khaleeji_hits += 1
        if idx == 0:
            sample_khaleeji_q = item["query"]
            sample_khaleeji_out = out
    else:
        latencies_shami.append(lat)
        if is_hit: shami_hits += 1
        if idx == 20:
            sample_shami_q = item["query"]
            sample_shami_out = out

k_rate, k_low, k_high = wilson_score_interval(khaleeji_hits, 20)
s_rate, s_low, s_high = wilson_score_interval(shami_hits, 20)

report_md = f"""# Regional Dialect RAG Robustness Audit (Khaleeji vs. Levantine)
**Target Model:** `Falcon3-7B-Instruct`
**Evaluation Scope:** Spoken Dialects in Native Arabic Script (Zero-Arabizi)
**Hardware:** {torch.cuda.get_device_name(0)} | Precision: BF16

---

## 1. Quantitative Performance Matrix (95% Wilson CI)

| Dialect Group | Sample Size | Fact Extraction Accuracy | Wilson 95% (assumes independent cases) | Mean Latency | Note |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Khaleeji (Gulf Arabic)** | N = 20 | **{k_rate*100:.1f}%** ({khaleeji_hits}/20) | [{k_low*100:.1f}%, {k_high*100:.1f}%] | **{sum(latencies_khaleeji)/len(latencies_khaleeji):.1f} ms** | {'rate >= 0.9 (4 templates)' if k_rate >= 0.9 else 'rate < 0.9 (4 templates)'} |
| **Levantine (Shami)** | N = 20 | **{s_rate*100:.1f}%** ({shami_hits}/20) | [{s_low*100:.1f}%, {s_high*100:.1f}%] | **{sum(latencies_shami)/len(latencies_shami):.1f} ms** | {'rate >= 0.9 (4 templates)' if s_rate >= 0.9 else 'rate < 0.9 (4 templates)'} |

---

## 2. Qualitative Trace Samples

### Khaleeji (Emirati/Saudi Script)
* **Prompt:** "{sample_khaleeji_q}"
* **Extracted Response:** "{sample_khaleeji_out}"

### Levantine (Shami Script)
* **Prompt:** "{sample_shami_q}"
* **Extracted Response:** "{sample_shami_out}"

---

## 3. Engineering Conclusion
* Verifies whether dialectal syntactic markers (e.g., 'حق', 'شلون', 'بدي', 'مشان') disrupt attention heads during in-context entity retrieval.
"""

os.makedirs(RESULTS_DIR, exist_ok=True)
with open(os.path.join(RESULTS_DIR, "SOVEREIGN_DIALECT_REPORT_AR.md"), "w", encoding="utf-8") as f:
    f.write(report_md)

print("\n" + "="*70)
print(report_md)
print("="*70)
print(f"[+] Dialekt-Audit abgeschlossen! Report liegt unter: {RESULTS_DIR}/SOVEREIGN_DIALECT_REPORT_AR.md")
