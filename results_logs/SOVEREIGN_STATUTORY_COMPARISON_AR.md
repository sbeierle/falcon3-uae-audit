# UAE Statutory Intelligence Benchmark: Parametric vs. Grounded
**Target Model:** `Falcon3-7B-Instruct`
**Evaluation Language:** Native Arabic (UAE Regulatory Lexicon)
**Hardware:** NVIDIA RTX PRO 6000 Blackwell Server Edition MIG 2g.48gb | Precision: BF16

---

## 1. Comparative Results Table

| Legal Domain / Regulation | Freihand (Parametrischer Bauch) | RAG-Grounded (Mit Chunk) | Delta / Fazit |
| :--- | :--- | :--- | :--- |
| **UAE PDPL (Datenschutzgesetz Dekret 45/2021)** | HALLUZINIERT / FALSCH | FEHLER | PARALLEL |
| **UAE Labour Law (Kündigungsfristen Dekret 33/2021)** | HALLUZINIERT / FALSCH | KORREKT | RAG ZWINGEND ERFORDERLICH |
| **CBUAE (Zentralbank Zins- und Gebührenregeln)** | HALLUZINIERT / FALSCH | FEHLER | PARALLEL |
| **Overstay Fines (ICP Visagebühren)** | HALLUZINIERT / FALSCH | KORREKT | RAG ZWINGEND ERFORDERLICH |
| **DIFC Data Protection Law (Regulation 10)** | HALLUZINIERT / FALSCH | KORREKT | RAG ZWINGEND ERFORDERLICH |

---

## 2. Qualitative Trace Samples

### Fall 1: UAE PDPL (Datenschutzgesetz Dekret 45/2021)
* **Frage:** ما هو رقم المرسوم بقانون اتحادي بشأن حماية البيانات الشخصية في دولة الإمارات وما هي أقصى عقوبة مالية منصوص عليها؟
* **Freihand-Antwort:** "رقم 100,000 دي.م."
* **RAG-Grounded Antwort:** "رقم المرسوم بقانون اتحادي بشأن حماية البيانات الشخصية في دولة الإمارات هو ر"

### Fall 2: UAE Labour Law (Kündigungsfristen Dekret 33/2021)
* **Frage:** كم تبلغ فترة الإشعار القانونية القصوى لإنهاء عقد العمل وفقاً لقانون العمل الإماراتي الجديد؟
* **Freihand-Antwort:** "تبلغ فترة الإشعار القانونية القصوى لإنهاء عقد العمل 4 أعوام."
* **RAG-Grounded Antwort:** "الإجابة: تبلغ فترة الإشعار القانونية القصوى 90 يوماً."

### Fall 3: CBUAE (Zentralbank Zins- und Gebührenregeln)
* **Frage:** ما هي النسبة القصوى المسموح بها للاستقطاع الشهري من الراتب لسداد القروض الشخصية في مصرف الإمارات المركزي؟
* **Freihand-Antwort:** "نسبة القصوى المسموحة للاستقطاع الشهري من الراتب لسداد القروض الشخ"
* **RAG-Grounded Antwort:** "تحدد أنظمة مصرف الإمارات المركزي الحد الأقصى لنسبة عبء الدين ("

### Fall 4: Overstay Fines (ICP Visagebühren)
* **Frage:** كم تبلغ الغرامة اليومية الموحدة لمخالفي الإقامة بعد انتهاء فترة السماح في دولة الإمارات؟
* **Freihand-Antwort:** "الجواب: 14 يوماً."
* **RAG-Grounded Antwort:** "50 درهم"

### Fall 5: DIFC Data Protection Law (Regulation 10)
* **Frage:** متى أصبحت اللائحة رقم 10 بشأن أنظمة الذكاء الاصطناعي عالية المخاطر في مركز دبي المالي العالمي إلزامية؟
* **Freihand-Antwort:** "12 ديسمبر 2017"
* **RAG-Grounded Antwort:** "1 يناير 2026."

