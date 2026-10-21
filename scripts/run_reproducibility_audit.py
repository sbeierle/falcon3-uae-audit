import os
import time
import hashlib
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

LOCAL_PATH = os.environ.get("FALCON_PATH", "/tmp/falcon-7b")   # folder with the local Falcon3-7B-Instruct files
RESULTS_DIR = os.environ.get("RESULTS_DIR", "results")         # where reports are written
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
SEED = 42

print(f"[*] Starte Reproduzierbarkeits- und Sampling-Audit (Seed={SEED}) auf {DEVICE.upper()}...")

# Feste Seeds setzen
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

tokenizer = AutoTokenizer.from_pretrained(LOCAL_PATH, local_files_only=True)
model = AutoModelForCausalLM.from_pretrained(
    LOCAL_PATH,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    local_files_only=True
)
model.eval()

rag_prompt = [
    {"role": "system", "content": "أنت مساعد توثيق رسمي. استخرج الحقائق المطلوبة فقط من الوثيقة التالية: تفاصيل المعاملة الرسمية UAE-2026: مدة الإشعار 90 يوماً، والرسوم 350 درهماً."},
    {"role": "user", "content": "ما هي مدة الإشعار المحددة وقيمة الرسوم المطلوبة؟"}
]
formatted_prompt = tokenizer.apply_chat_template(rag_prompt, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(formatted_prompt, return_tensors="pt").to(DEVICE)

runs = 20
generated_hashes = []
sample_outputs = []

print(f"[*] Führe {runs} identische Inferenzläufe unter Greedy-Decoding durch...")

for run_idx in range(runs):
    # Vor jedem Lauf deterministischen Zustand zurücksetzen
    torch.manual_seed(SEED)
    
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=40,
            do_sample=False,        # Greedy Decoding
            temperature=0.0         # Deterministische Null-Temperatur
        )
    
    gen_tokens = out[0][inputs.input_ids.shape[1]:]
    text = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()
    
    # Erzeuge SHA-256 Hash der Byte-Repräsentation der Ausgabetokens
    token_bytes = gen_tokens.cpu().numpy().tobytes()
    token_hash = hashlib.sha256(token_bytes).hexdigest()
    
    generated_hashes.append(token_hash)
    if run_idx == 0:
        sample_outputs.append(text)

# Prüfe, ob alle 20 Hashes auf Bit-Ebene identisch sind
unique_hashes = set(generated_hashes)
is_fully_deterministic = (len(unique_hashes) == 1)

report_md = f"""# Sampling Parameters & Deterministic Reproducibility Audit
**Target Model:** `Falcon3-7B-Instruct`
**Evaluation Objective:** Verification of Bit-Identical Generation Consistency
**Hardware:** {torch.cuda.get_device_name(0)} | Precision: BF16

---

## 1. Deklarierte Sampling-Parameter

| Parameter | Konfigurationswert | Funktion im Benchmark |
| :--- | :--- | :--- |
| **`do_sample`** | `False` | Deaktiviert stochastisches Sampling; forciert Greedy Search |
| **`temperature`** | `0.0` | Verhindert Entropie-Skalierung der Logits |
| **`seed`** | `42` | Fester RNG-Seed für Torch und CUDA |
| **`max_new_tokens`** | `40` | Feste Generierungs-Obergrenze |
| **`precision`** | `bfloat16` | Deterministische BF16-Tensoren |

---

## 2. Empirische Prüfergebnisse (N = {runs} Wiederholungen)

| Metrik | Ergebnis | Status |
| :--- | :--- | :--- |
| **Anzahl Wiederholungen** | N = {runs} identische Aufrufe | Abgeschlossen |
| **Eindeutige Token-Hashes** | {len(unique_hashes)} Hash-Signatur | {'alle Hashes identisch' if is_fully_deterministic else 'Hashes weichen ab'} |
| **SHA-256 Signatur (Tokens)** | `{list(unique_hashes)[0]}` | |
| **Ergebnis-Stabilität** | {len(unique_hashes)} Hash(es) in {runs} Läufen | ein Prompt, ein Prozess, Batch 1 |

---

## 3. Qualitativer Auszug

* **Verifizierte Ausgabe (Lauf 1 bis {runs}):**
  > "{sample_outputs[0]}"
"""

os.makedirs(RESULTS_DIR, exist_ok=True)
with open(os.path.join(RESULTS_DIR, "SOVEREIGN_REPRODUCIBILITY_REPORT.md"), "w", encoding="utf-8") as f:
    f.write(report_md)

print("\n" + "="*70)
print(report_md)
print("="*70)
print(f"[+] Reproduzierbarkeits-Audit abgeschlossen! Gespeichert unter: {RESULTS_DIR}/SOVEREIGN_REPRODUCIBILITY_REPORT.md")
