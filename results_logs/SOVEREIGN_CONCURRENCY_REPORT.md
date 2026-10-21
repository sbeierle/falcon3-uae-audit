# Concurrency & Scaling Performance Profile
**Target Model:** `Falcon3-7B-Instruct`
**Hardware:** NVIDIA RTX PRO 6000 Blackwell Server Edition MIG 2g.48gb | Precision: BF16

---

## 1. Multi-Stream Ingestion & Throughput Matrix

| Concurrency (Batch Size) | Generation Throughput | Step Latency (ITL) | VRAM Peak Allocation |
| :--- | :--- | :--- | :--- |
| **B = 01** | **46.0 tokens/s** | **21.7 ms/step** | **13.93 GB** |
| **B = 04** | **174.4 tokens/s** | **22.9 ms/step** | **13.95 GB** |
| **B = 08** | **340.1 tokens/s** | **23.5 ms/step** | **13.98 GB** |
| **B = 16** | **649.6 tokens/s** | **24.6 ms/step** | **14.05 GB** |

---
* **Base Static VRAM:** ~14.9 GB
* **Scaling Overhead:** Lineare VRAM-Skalierung im Eager-Modus ohne OOM bis Batch 16.
