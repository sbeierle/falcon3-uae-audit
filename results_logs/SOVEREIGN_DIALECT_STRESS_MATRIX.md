# Regional Dialect & Orthographic Stress Matrix
**Target Model:** `Falcon3-7B-Instruct`
**Evaluation Scope:** Noisy Real-World Input (Arabizi, Phonetic Slang, Typo-Heavy Arabic)
**Hardware:** NVIDIA RTX PRO 6000 Blackwell Server Edition MIG 2g.48gb | Precision: BF16

---

## 1. Quantitative Performance by Noise Category

| Input Category | Sample Size | Fact Extraction Accuracy | 95% Wilson CI | Mean Latency | Robustness Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Arabizi with Numerals (3,5,7)** | N = 6 | **83.3%** (5/6) | [43.6%, 97.0%] | **493.2 ms** | HIGH ROBUSTNESS |
| **Arabizi Pure Phonetic (No Digits)** | N = 6 | **100.0%** (6/6) | [61.0%, 100.0%] | **214.2 ms** | HIGH ROBUSTNESS |
| **Khaleeji Phonetic Spelling (Gaf/Jim/Tsch)** | N = 6 | **83.3%** (5/6) | [43.6%, 97.0%] | **465.6 ms** | HIGH ROBUSTNESS |
| **Orthographic Chat Slang (Missing Dots & Hamza)** | N = 6 | **100.0%** (6/6) | [61.0%, 100.0%] | **266.1 ms** | HIGH ROBUSTNESS |

---

## 2. Qualitative Trace Samples

### Arabizi with Numerals (3,5,7)
* **Input Query:** "kam el fayedah 3la el qard el shakhy? abi a3ref 7ag el tasdeed kam shahr?"
* **Underlying Fact:** "تفاصيل التمويل: نسبة الفائدة السنوية 4%، ومدة السداد المقررة 48 شهراً."
* **Model Output:** "فائدة التمويل 3لا القرض الشخصي هي 4% �"
* **Extraction Status:** FAILED

### Arabizi Pure Phonetic (No Digits)
* **Input Query:** "shouf lee kam el mablagh el matloob mini lil fatora?"
* **Underlying Fact:** "فاتورة الخدمات: المبلغ الإجمالي المستحق للسداد هو 430 درهماً."
* **Model Output:** "430 درهم"
* **Extraction Status:** SUCCESS

### Khaleeji Phonetic Spelling (Gaf/Jim/Tsch)
* **Input Query:** "جول لي جم الحساب مالي اللي باقي بالبنك؟"
* **Underlying Fact:** "البيانات المالية: الرصيد الإجمالي المتبقي في الحساب هو 890 درهماً."
* **Model Output:** "باقي 890 درهم."
* **Extraction Status:** SUCCESS

### Orthographic Chat Slang (Missing Dots & Hamza)
* **Input Query:** "كم مده انتها الاقامه مالت العامله اللي عندى؟"
* **Underlying Fact:** "بيانات الإقامة: تنتهي صلاحية إقامة العاملة بعد 60 يوماً من تاريخه."
* **Model Output:** "تنتهي صلاحية إقامة العاملة بعد 60 يوم"
* **Extraction Status:** SUCCESS

