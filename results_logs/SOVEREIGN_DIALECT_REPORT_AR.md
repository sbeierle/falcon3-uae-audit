# Regional Dialect RAG Robustness Audit (Khaleeji vs. Levantine)
**Target Model:** `Falcon3-7B-Instruct`
**Evaluation Scope:** Spoken Dialects in Native Arabic Script (Zero-Arabizi)
**Hardware:** NVIDIA RTX PRO 6000 Blackwell Server Edition MIG 2g.48gb | Precision: BF16

---

## 1. Quantitative Performance Matrix (95% Wilson CI)

| Dialect Group | Sample Size | Fact Extraction Accuracy | 95% Wilson CI | Mean Latency | Operational Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Khaleeji (Gulf Arabic)** | N = 20 | **100.0%** (20/20) | [83.9%, 100.0%] | **378.3 ms** | NATIVE SUPPORT |
| **Levantine (Shami)** | N = 20 | **100.0%** (20/20) | [83.9%, 100.0%] | **303.6 ms** | NATIVE SUPPORT |

---

## 2. Qualitative Trace Samples

### Khaleeji (Emirati/Saudi Script)
* **Prompt:** "كم الرسوم حق تجديد الرخصة وكم يبيلي ادفع؟"
* **Extracted Response:** "165 درهم إماراتي."

### Levantine (Shami Script)
* **Prompt:** "بدي اعرف قديش لازم ادفع مشان جدد الرخصة تبعي؟"
* **Extracted Response:** "220 درهم إماراتي."

---

## 3. Engineering Conclusion
* Verifies whether dialectal syntactic markers (e.g., 'حق', 'شلون', 'بدي', 'مشان') disrupt attention heads during in-context entity retrieval.
