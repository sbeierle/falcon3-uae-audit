# Context-Window Scaling Benchmark Report
**Target Model:** `Falcon3-7B-Instruct`
**Hardware:** NVIDIA RTX PRO 6000 Blackwell Server Edition MIG 2g.48gb | Precision: BF16

---

## 1. Prefill-Latenz (TTFT) und VRAM-Skalierung

| Input Context (Tokens) | Time-to-First-Token (TTFT) | VRAM Peak Allocation | Skalierungsbefund |
| :--- | :--- | :--- | :--- |
| ** 1024** | **183.60 ms** | **14.20 GB** | Stabiler Prefill |
| ** 4096** | **387.41 ms** | **14.99 GB** | Stabiler Prefill |
| ** 8192** | **785.24 ms** | **16.05 GB** | Stabiler Prefill |
| **32768** | **3772.77 ms** | **22.43 GB** | Verlängerter Prefill |

---
* **Isolations-Methode:** `max_new_tokens=1` isoliert die reine Prefill-Phase vom autoregressiven Decoding-Schritt.
* **Präzision:** Native BF16-Tensoren ohne Quantisierung.
