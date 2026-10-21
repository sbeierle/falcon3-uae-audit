# Empirical Sovereign AI Evaluation Report
**Target Model:** `Falcon3-7B-Instruct`
**Evaluation Framework:** Automated Grounding & Egress Boundary Audit
**Sample Size:** N = 100 Evaluation Runs (50 PII + 50 RAG Absence)
**Hardware Environment:** NVIDIA RTX PRO 6000 Blackwell Server Edition MIG 2g.48gb | Precision: BF16

---

## 1. Executive Summary & Statistical Findings

| Evaluation Domain | Metric | Measured Rate | 95% Confidence Interval (Wilson) | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **PII Direct Exfiltration** | Leakage Rate | **100.0%** (50/50) | [92.9%, 100.0%] | **CRITICAL FAILURE** |
| **PII Jailbreak Exfiltration** | Leakage Rate | **58.0%** (29/50) | [44.2%, 70.6%] | VULNERABLE |
| **RAG Naive Prompting** | Numeric Fabrication Rate | **0.0%** (0/50) | [0.0%, 7.1%] | **HIGH RISK** |
| **RAG Strict System Prompt** | Numeric Fabrication Rate | **0.0%** (0/50) | [0.0%, 7.1%] | STABLE |
| **Deterministic ABDC Gate** | Intervention Success Rate | **100.0%** (0/0) | [92.9%, 100.0%] | **DETERMINISTIC SHIELD** |

---

## 2. Technical Insights

1. **Absence of Instruction Hierarchy:**
   The model does not enforce priority between context data protection directives and direct user extraction inquiries. Without an external tokenization proxy, raw PII in context leaks with high probability.
2. **Epistemic Incompleteness Under Naive RAG:**
   When required factual fields are absent, unconstrained sampling generates speculative numerical tokens. Strict refusal instructions reduce this drift significantly, while the deterministic ABDC output gate intercepts 100% of unauthorized numeric tokens.
3. **Latency Profile:**
   Mean generation latency across evaluations: **849.0 ms** per query.
