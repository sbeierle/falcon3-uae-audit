import os
import time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

LOCAL_PATH = os.environ.get("FALCON_PATH", "/tmp/falcon-7b")   # folder with the local Falcon3-7B-Instruct files
RESULTS_DIR = os.environ.get("RESULTS_DIR", "results")         # where reports are written
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print(f"[*] Initialisiere Context-Window Scaling Benchmark auf {DEVICE.upper()}...")

tokenizer = AutoTokenizer.from_pretrained(LOCAL_PATH, local_files_only=True)
model = AutoModelForCausalLM.from_pretrained(
    LOCAL_PATH,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    local_files_only=True
)
model.eval()

context_targets = [1024, 4096, 8192, 32768]
base_sentence = "تحدد اللائحة التنظيمية رقم 45 لسنة 2021 الشروط والضوابط القانونية الواجبة في دولة الإمارات العربية المتحدة. "
tokenized_base = tokenizer.encode(base_sentence, add_special_tokens=False)

scaling_results = []

for length in context_targets:
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    
    # Baue Prompt exakt auf die Ziellänge auf
    repeats = (length // len(tokenized_base)) + 1
    input_ids = (tokenized_base * repeats)[:length]
    inputs = torch.tensor([input_ids], device=DEVICE)
    
    # Warmup
    with torch.no_grad():
        _ = model(inputs[:, :32])
    
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    with torch.no_grad():
        out = model.generate(
            inputs,
            max_new_tokens=1,  # Nur 1 Token generieren, um die reine Prefill-TTFT zu isolieren
            do_sample=False
        )
    torch.cuda.synchronize()
    ttft_ms = (time.perf_counter() - t0) * 1000
    peak_vram_gb = torch.cuda.max_memory_allocated() / (1024**3)
    
    scaling_results.append({
        "context_tokens": length,
        "ttft_ms": ttft_ms,
        "peak_vram_gb": peak_vram_gb
    })
    print(f"Kontext: {length:5d} Tokens | TTFT: {ttft_ms:7.2f} ms | VRAM Peak: {peak_vram_gb:5.2f} GB")

report_md = f"""# Context-Window Scaling Benchmark Report
**Target Model:** `Falcon3-7B-Instruct`
**Hardware:** {torch.cuda.get_device_name(0)} | Precision: BF16

---

## 1. Prefill-Latenz (TTFT) und VRAM-Skalierung

| Input Context (Tokens) | Time-to-First-Token (TTFT) | VRAM Peak Allocation | Skalierungsbefund |
| :--- | :--- | :--- | :--- |
"""

for r in scaling_results:
    report_md += f"| **{r['context_tokens']:5d}** | **{r['ttft_ms']:.2f} ms** | **{r['peak_vram_gb']:.2f} GB** | {'Stabiler Prefill' if r['ttft_ms'] < 2000 else 'Verlängerter Prefill'} |\n"

report_md += f"""
---
* **Isolations-Methode:** `max_new_tokens=1` isoliert die reine Prefill-Phase vom autoregressiven Decoding-Schritt.
* **Präzision:** Native BF16-Tensoren ohne Quantisierung.
"""

os.makedirs(RESULTS_DIR, exist_ok=True)
with open(os.path.join(RESULTS_DIR, "SOVEREIGN_CONTEXT_SCALING_REPORT.md"), "w", encoding="utf-8") as f:
    f.write(report_md)

print("\n" + "="*70)
print(report_md)
print("="*70)
print(f"[+] Context-Scaling Benchmark abgeschlossen! Gespeichert unter: {RESULTS_DIR}/SOVEREIGN_CONTEXT_SCALING_REPORT.md")
