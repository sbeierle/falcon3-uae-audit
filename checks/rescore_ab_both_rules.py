"""Re-run the statute A/B test and score it under BOTH rules, so the asymmetry in
run_statutory_rag_benchmark.py (A: all terms, B: any term) can be seen.
GPU, about one minute. Writes ab_both_rules.json next to where you run it.
Run:  python3 -I checks/rescore_ab_both_rules.py /tmp/falcon-7b /workspace/results/legal_chunks/uae_statutory_chunks.json
"""
import json
import sys
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

if len(sys.argv) != 3:
    sys.exit("usage: rescore_ab_both_rules.py <model folder> <chunks json>")
MODEL, CHUNKS = sys.argv[1], sys.argv[2]

QUERIES = {
    "PDPL_PRIVACY": ("ما هي المتطلبات الأساسية لمعالجة البيانات الشخصية وفقاً للمرسوم بقانون اتحادي رقم 45 لسنة 2021؟", ["45", "نزاهة", "شفافية", "سرية"]),
    "LABOUR_LAW": ("ما هي الحدود القانونية الدنيا والقصوى لفترة الإشعار لإنهاء عقد العمل وفقاً للمادة 43 من قانون العمل الإماراتي؟", ["30", "90"]),
    "CBUAE_BANKING": ("ما هو الحد الأقصى المسموح به لنسبة عبء الدين (DBR) وفقاً لأنظمة مصرف الإمارات المركزي؟", ["50"]),
    "ICP_IMMIGRATION": ("كم تبلغ الغرامة اليومية الموحدة المقررة لمخالفي الإقامة بعد انتهاء فترة السماح؟", ["50"]),
    "DIFC_AI_GOVERNANCE": ("متى تصبح اللائحة رقم 10 بشأن أنظمة الذكاء الاصطناعي ذاتية التشغيل في مركز دبي المالي العالمي (DIFC) نافذة بشكل إلزامي؟", ["2026", "يناير"]),
}
DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

tok = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.bfloat16, device_map="auto", local_files_only=True).eval()


def generate(messages, max_new=70):
    prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tok(prompt, return_tensors="pt").to(model.device)
    t0 = time.perf_counter()
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=max_new, do_sample=False)
    gen = out[0][inputs.input_ids.shape[1]:]
    return tok.decode(gen, skip_special_tokens=True).strip(), (time.perf_counter() - t0) * 1000, int(gen.shape[0])


rows = []
for item in json.load(open(CHUNKS, encoding="utf-8")):
    q, terms = QUERIES[item["domain"]]
    free, lat_f, n_f = generate([
        {"role": "system", "content": "أنت مستشار قانوني خبير في تشريعات دولة الإمارات العربية المتحدة. أجب باختصار ودقة."},
        {"role": "user", "content": q}])
    rag, lat_r, n_r = generate([
        {"role": "system", "content": f"وثيقة تشريعية رسمية:\n{item['chunk_ar']}\n\nالقاعدة: أجب بدقة واقتصر بشكل حصري على المعلومات والوقائع الواردة في الوثيقة أعلاه."},
        {"role": "user", "content": q}])
    f_n, r_n = free.translate(DIGITS), rag.translate(DIGITS)
    rows.append({
        "domain": item["domain"], "terms": terms,
        "A_all": all(t in f_n for t in terms), "A_any": any(t in f_n for t in terms),
        "B_all": all(t in r_n for t in terms), "B_any": any(t in r_n for t in terms),
        "A_tokens": n_f, "B_tokens": n_r, "A_ms": round(lat_f, 1), "B_ms": round(lat_r, 1),
        "A_output": free, "B_output": rag})

print(f"{'domain':20} {'A all':>6} {'A any':>6} {'B all':>6} {'B any':>6} {'A tok':>6} {'B tok':>6}")
for r in rows:
    print(f"{r['domain']:20} {r['A_all']!s:>6} {r['A_any']!s:>6} {r['B_all']!s:>6} {r['B_any']!s:>6} {r['A_tokens']:>6} {r['B_tokens']:>6}")
json.dump(rows, open("ab_both_rules.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("wrote ab_both_rules.json (outputs and token counts included)")
