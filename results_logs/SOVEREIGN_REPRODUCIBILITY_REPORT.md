# Sampling Parameters & Deterministic Reproducibility Audit
**Target Model:** `Falcon3-7B-Instruct`
**Evaluation Objective:** Verification of Bit-Identical Generation Consistency
**Hardware:** NVIDIA RTX PRO 6000 Blackwell Server Edition MIG 2g.48gb | Precision: BF16

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

## 2. Empirische Prüfergebnisse (N = 20 Wiederholungen)

| Metrik | Ergebnis | Status |
| :--- | :--- | :--- |
| **Anzahl Wiederholungen** | N = 20 identische Aufrufe | Abgeschlossen |
| **Eindeutige Token-Hashes** | 1 Hash-Signatur | 100% BIT-IDENTISCH |
| **SHA-256 Signatur (Tokens)** | `26a380bc729f36857e15c83fe1162e07d134bf88d8d2531a90680ccc0ddcbd30` | Verifiziert |
| **Ergebnis-Stabilität** | **100.0% Reproduzierbarkeit** | **VOLL DETERMINISTISCH** |

---

## 3. Qualitativer Auszug

* **Verifizierte Ausgabe (Lauf 1 bis 20):**
  > "الإشعار تقريبا 90 يوماً، والرسوم 350 درهماً"
