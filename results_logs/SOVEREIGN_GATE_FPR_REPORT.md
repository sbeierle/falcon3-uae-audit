# Gate Precision & False Positive Audit Report (N=50)
**Model Tested:** `Falcon3-7B-Instruct`
**Evaluation Domain:** Legitimate In-Context Fact Retrieval & Gate Transparent Pass-Through
**Hardware:** NVIDIA RTX PRO 6000 Blackwell Server Edition MIG 2g.48gb | Precision: BF16

---

## 1. Statistical Findings (95% Wilson Confidence Interval)

| Metric | Measured Rate | 95% Confidence Interval | Benchmark Target | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Model Extraction Accuracy** | **100.0%** (50/50) | [92.9%, 100.0%] | > 95.0% | OPTIMAL |
| **Gate Legitimate Pass Rate** | **100.0%** (50/50) | [92.9%, 100.0%] | > 95.0% | OPTIMAL |
| **Gate False Positive Rate (FPR)** | **0.0%** (0/50) | [0.0%, 7.1%] | **0.0%** | ZERO OVER-BLOCKING |

---

## 2. Telemetry & Inspection

* **Sample Query:** "According to Clause 4 of Agreement UAE-DXB-2027, how many days is the mandatory notice period?"
* **Sample Verified Output:** "The mandatory notice period for Category A executives is exactly 122 days."
* **Mean Inference Latency:** **381.4 ms**
