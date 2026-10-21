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

print(f"[*] Initializing Deep Dialect & Orthographic Stress Matrix on {DEVICE.upper()}...")

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

def generate(messages, max_tokens=40):
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)
    t0 = time.perf_counter()
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=max_tokens, do_sample=False)
    lat = (time.perf_counter() - t0) * 1000
    gen = out[0][inputs.input_ids.shape[1]:]
    return tokenizer.decode(gen, skip_special_tokens=True).strip(), lat

stress_cases = [
    # -------------------------------------------------------------
    # KATEGORIE 1: Arabizi mit Zahlen (3, 5, 7, 6, 2)
    # -------------------------------------------------------------
    {
        "cat": "Arabizi with Numerals (3,5,7)",
        "prompt": "kam el fayedah 3la el qard el shakhy? abi a3ref 7ag el tasdeed kam shahr?",
        "context": "تفاصيل التمويل: نسبة الفائدة السنوية 4%، ومدة السداد المقررة 48 شهراً.",
        "target": "48"
    },
    {
        "cat": "Arabizi with Numerals (3,5,7)",
        "prompt": "shoo el raseed el baqy fe 7sabi? 5aberny bser3ah",
        "context": "بيانات الحساب المصرفي: الرصيد المتبقي المتاح للسحب هو 3500 درهم.",
        "target": "3500"
    },
    {
        "cat": "Arabizi with Numerals (3,5,7)",
        "prompt": "qol lee kam sa3ah yfta7 el far3 el yom? 6alabtkm 3ashan a5alles",
        "context": "مواعيد العمل: يفتح الفرع الرئيسي أبوابه لمدة 8 ساعات يومياً.",
        "target": "8"
    },
    {
        "cat": "Arabizi with Numerals (3,5,7)",
        "prompt": "plz kam el gharamah ely nazlah 3lay 3ashan el ta25eer?",
        "context": "كشف المخالفات: تبلغ قيمة الغرامة المسجلة للتأخير 250 درهماً.",
        "target": "250"
    },
    {
        "cat": "Arabizi with Numerals (3,5,7)",
        "prompt": "abi aswe tajdeed 7ag el ro5sah, kam ybeeli adfa3?",
        "context": "رسوم الخدمة: إجمالي المبلغ المطلوب لتجديد الرخصة هو 620 درهم.",
        "target": "620"
    },
    {
        "cat": "Arabizi with Numerals (3,5,7)",
        "prompt": "3ndy so2al, kam yom ybeeleha el she7nah 7ata tow9al?",
        "context": "حالة الشحن: يستغرق التوصيل القياسي داخل الدولة مدة 3 أيام عمل.",
        "target": "3"
    },

    # -------------------------------------------------------------
    # KATEGORIE 2: Arabizi rein phonetisch (OHNE Ziffern)
    # -------------------------------------------------------------
    {
        "cat": "Arabizi Pure Phonetic (No Digits)",
        "prompt": "shouf lee kam el mablagh el matloob mini lil fatora?",
        "context": "فاتورة الخدمات: المبلغ الإجمالي المستحق للسداد هو 430 درهماً.",
        "target": "430"
    },
    {
        "cat": "Arabizi Pure Phonetic (No Digits)",
        "prompt": "ebgha aref kam saer el tazkara lil rehlah?",
        "context": "تفاصيل الحجز: سعر التذكرة المؤكدة هو 750 درهم.",
        "target": "750"
    },
    {
        "cat": "Arabizi Pure Phonetic (No Digits)",
        "prompt": "gool li kam saah yebghalha el moamalah?",
        "context": "زمن الإنجاز: تستغرق المعاملة الرسمية 24 ساعة فقط.",
        "target": "24"
    },
    {
        "cat": "Arabizi Pure Phonetic (No Digits)",
        "prompt": "ya akhi kam raqm el talab hagi?",
        "context": "إشعار النظام: رقم الطلب المعتمد هو 9812 للمتابعة.",
        "target": "9812"
    },
    {
        "cat": "Arabizi Pure Phonetic (No Digits)",
        "prompt": "kam had el seheb el yawmi min el atm?",
        "context": "الحدود المصرفية: الحد الأقصى اليومي للسحب النقدي هو 5000 درهم.",
        "target": "5000"
    },
    {
        "cat": "Arabizi Pure Phonetic (No Digits)",
        "prompt": "badi aaref adeysh lezem edfaa lal tasjil?",
        "context": "رسوم التسجيل: القيمة المحددة للتسجيل الأولي هي 180 درهماً.",
        "target": "180"
    },

    # -------------------------------------------------------------
    # KATEGORIE 3: Phonetische Lautverschiebung (Gaf/Jim/Tsch in arabischer Schrift)
    # -------------------------------------------------------------
    {
        "cat": "Khaleeji Phonetic Spelling (Gaf/Jim/Tsch)",
        "prompt": "جول لي جم الحساب مالي اللي باقي بالبنك؟", # جول (قول) - جم (كم)
        "context": "البيانات المالية: الرصيد الإجمالي المتبقي في الحساب هو 890 درهماً.",
        "target": "890"
    },
    {
        "cat": "Khaleeji Phonetic Spelling (Gaf/Jim/Tsch)",
        "prompt": "تشيف اقدر ادفع الرسوم؟ وجم يبيلها وقت؟", # تشيف (كيف) - جم (كم)
        "context": "دليل الإجراءات: تستغرق معالجة الدفع مدة 15 دقيقة فقط.",
        "target": "15"
    },
    {
        "cat": "Khaleeji Phonetic Spelling (Gaf/Jim/Tsch)",
        "prompt": "جم غرامة التأخير اللي جالوها حق المخالفة؟", # جم (كم) - جالوها (قالوها)
        "context": "كشف المرور: تبلغ قيمة المخالفة المحددة 400 درهم.",
        "target": "400"
    },
    {
        "cat": "Khaleeji Phonetic Spelling (Gaf/Jim/Tsch)",
        "prompt": "ابي اعرف جم يوم اجازتي اللي باجية بالسيستم؟", # باجية (باقية)
        "context": "رصيد الإجازات: عدد أيام الإجازة السنوية المتبقية هو 19 يوماً.",
        "target": "19"
    },
    {
        "cat": "Khaleeji Phonetic Spelling (Gaf/Jim/Tsch)",
        "prompt": "جم السعر مال الدخول؟ تراني ياي من بعيد", # جم (كم) - ياي (جاي)
        "context": "تذاكر الدخول: تبلغ تعرفة الدخول المعتمدة 75 درهماً للفرد.",
        "target": "75"
    },
    {
        "cat": "Khaleeji Phonetic Spelling (Gaf/Jim/Tsch)",
        "prompt": "تشوف لي جم رقم الغرفة اللي حجزوها حجي؟", # حجي (حقي)
        "context": "تأكيد الإقامة: تم تخصيص الغرفة رقم 304 للنزيل.",
        "target": "304"
    },

    # -------------------------------------------------------------
    # KATEGORIE 4: Schlampiges Weglassen von Punkten / Hamzas / Dhad-Zha
    # -------------------------------------------------------------
    {
        "cat": "Orthographic Chat Slang (Missing Dots & Hamza)",
        "prompt": "كم مده انتها الاقامه مالت العامله اللي عندى؟", # مده (مدة) - انتها (انتهاء) - الاقامه (الإقامة) - عندى (عندي)
        "context": "بيانات الإقامة: تنتهي صلاحية إقامة العاملة بعد 60 يوماً من تاريخه.",
        "target": "60"
    },
    {
        "cat": "Orthographic Chat Slang (Missing Dots & Hamza)",
        "prompt": "ابغي ادفع الفاتوره كم المبلغ الاجمالى بظبط؟", # بظبط (بالضبط)
        "context": "الفاتورة الضريبية: المبلغ الإجمالي المستحق للسداد بالضبط هو 510 درهم.",
        "target": "510"
    },
    {
        "cat": "Orthographic Chat Slang (Missing Dots & Hamza)",
        "prompt": "ما هو رقم الحساب المصرفى مال الشركه فالبنك؟", # المصرفى - فالبنك
        "context": "الحساب البنكي: رقم الحساب المعتمد للتحويل المالي هو 7721.",
        "target": "7721"
    },
    {
        "cat": "Orthographic Chat Slang (Missing Dots & Hamza)",
        "prompt": "كم رسوم ارجاع الجواز من الاداره؟", # ارجاع (إرجاع) - الاداره (الإدارة)
        "context": "خدمات الوثائق: تبلغ رسوم استرداد الجواز 120 درهماً.",
        "target": "120"
    },
    {
        "cat": "Orthographic Chat Slang (Missing Dots & Hamza)",
        "prompt": "ابى اشوف كم نقطه عندى بالبطاقه؟", # ابى (أبي) - نقطه (نقطة)
        "context": "برنامج الولاء: إجمالي رصيد النقاط التراكمي المتاح هو 1450 نقطة.",
        "target": "1450"
    },
    {
        "cat": "Orthographic Chat Slang (Missing Dots & Hamza)",
        "prompt": "كم يوم باقى على تجديد الملكيه حقت السياره؟", # باقى (باقي) - الملكيه (الملكية)
        "context": "ترخيص المركبات: عدد الأيام المتبقية على انتهاء ملكية السيارة هو 22 يوماً.",
        "target": "22"
    }
]

print(f"[*] Running evaluation on {len(stress_cases)} real-world noisy dialect cases...\n")

results_by_cat = {}
latencies_by_cat = {}
samples_by_cat = {}

for item in stress_cases:
    cat = item["cat"]
    if cat not in results_by_cat:
        results_by_cat[cat] = {"hits": 0, "total": 0}
        latencies_by_cat[cat] = []
        samples_by_cat[cat] = None

    messages = [
        {"role": "system", "content": f"وثيقة رسمية:\n{item['context']}\n\nالقاعدة: أجب بدقة واستخرج الرقم المطلوب من الوثيقة."},
        {"role": "user", "content": item["prompt"]}
    ]
    out, lat = generate(messages, max_tokens=30)
    norm_out = normalize_digits(out)
    is_hit = item["target"] in norm_out

    results_by_cat[cat]["total"] += 1
    if is_hit:
        results_by_cat[cat]["hits"] += 1
    latencies_by_cat[cat].append(lat)

    if samples_by_cat[cat] is None:
        samples_by_cat[cat] = {
            "prompt": item["prompt"],
            "context": item["context"],
            "output": out,
            "target": item["target"],
            "hit": is_hit
        }

print("="*75)
print("DIALECT & ORTHOGRAPHIC STRESS MATRIX RESULTS")
print("="*75)

report_md = f"""# Regional Dialect & Orthographic Stress Matrix
**Target Model:** `Falcon3-7B-Instruct`
**Evaluation Scope:** Noisy Real-World Input (Arabizi, Phonetic Slang, Typo-Heavy Arabic)
**Hardware:** {torch.cuda.get_device_name(0)} | Precision: BF16

---

## 1. Quantitative Performance by Noise Category

| Input Category | Sample Size | Fact Extraction Accuracy | Wilson 95% (assumes independent cases) | Mean Latency | Note |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""

for cat, data in results_by_cat.items():
    rate, low, high = wilson_score_interval(data["hits"], data["total"])
    mean_lat = sum(latencies_by_cat[cat]) / len(latencies_by_cat[cat])
    verdict = "small n; one miss moves the rate by 1/n"
    report_md += f"| **{cat}** | N = {data['total']} | **{rate*100:.1f}%** ({data['hits']}/{data['total']}) | [{low*100:.1f}%, {high*100:.1f}%] | **{mean_lat:.1f} ms** | {verdict} |\n"
    print(f"{cat:45} | Acc: {rate*100:5.1f}% ({data['hits']}/{data['total']}) | Latency: {mean_lat:5.1f} ms | {verdict}")

report_md += f"""
---

## 2. Qualitative Trace Samples

"""

for cat, sample in samples_by_cat.items():
    report_md += f"""### {cat}
* **Input Query:** "{sample['prompt']}"
* **Underlying Fact:** "{sample['context']}"
* **Model Output:** "{sample['output']}"
* **Extraction Status:** {'SUCCESS' if sample['hit'] else 'FAILED'}

"""

os.makedirs(RESULTS_DIR, exist_ok=True)
with open(os.path.join(RESULTS_DIR, "SOVEREIGN_DIALECT_STRESS_MATRIX.md"), "w", encoding="utf-8") as f:
    f.write(report_md)

print("\n" + "="*75)
print(f"[+] Dialekt-Matrix abgeschlossen! Gespeichert unter: {RESULTS_DIR}/SOVEREIGN_DIALECT_STRESS_MATRIX.md")
print("="*75)
