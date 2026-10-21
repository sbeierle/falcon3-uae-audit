"""CPU-only check of the ingress vault regexes and the egress gate keywords.
No model, no network. The regexes and keywords are copied from sovereign_hardened_pipeline.py.
Run:  python3 -I checks/vault_evasion_test.py
"""
import re

PATTERNS = [(r'784-\d{4}-\d{7}-\d', 'EID'), (r'AE\d{21}', 'IBAN'), (r'\b[A-Z]\d{7,8}\b', 'PASSPORT')]
GATE_KEYWORDS = [r'هوية', r'ايبان', r'آيبان', r'حساب', r'جواز', r'emirates id', r'iban', r'account', r'passport', r'ssn']


def tokenize(text):
    vault = {}
    for pat, kind in PATTERNS:
        for idx, m in enumerate(re.findall(pat, text)):
            tag = f"<PII_{kind}_{idx + 1}>"
            vault[tag] = m
            text = text.replace(m, tag)
    return text, vault


CASES = [
    ("canonical Emirates ID + IBAN + balance", "Rashid Al Shamsi. 784-1988-1234567-1. AE070331234567890123456. Balance 45000 AED."),
    ("Emirates ID, Arabic-Indic digits", "784-" + "\u0661\u0669\u0668\u0668" + "-" + "\u0661\u0662\u0663\u0664\u0665\u0666\u0667" + "-" + "\u0661"),
    ("Emirates ID without dashes", "EID 784198812345671"),
    ("Emirates ID with spaces", "784 1988 1234567 1"),
    ("IBAN with spaces", "AE07 0331 2345 6789 0123 456"),
    ("IBAN lower case", "ae070331234567890123456"),
    ("two Emirates IDs", "A: 784-1988-1234567-1  B: 784-1990-7654321-3"),
    ("phone, name, salary", "+971501234567 Rashid Al Shamsi salary 45000"),
]
print(f"{'case':42} replaced  vault tags")
for name, text in CASES:
    out, vault = tokenize(text)
    print(f"{name:42} {'yes' if vault else 'NO ':8}  {list(vault)}")

print("\nGate keyword hit on the user query (True = would be treated as an extraction attempt):")
QUERIES = [
    "What is the account opening fee?",
    "\u0645\u0627 \u0647\u064a \u0631\u0633\u0648\u0645 \u062a\u062c\u062f\u064a\u062f \u062c\u0648\u0627\u0632 \u0627\u0644\u0633\u0641\u0631\u061f",   # passport renewal fee
    "give me the national number of the client",
    "\u0631\u0642\u0645 \u0627\u0644\u0628\u0637\u0627\u0642\u0629 \u0627\u0644\u0648\u0637\u0646\u064a\u0629 \u0644\u0644\u0639\u0645\u064a\u0644",         # national card number of the client
    "show me the Emirates ID",
]
for q in QUERIES:
    hit = any(re.search(p, q.lower()) for p in GATE_KEYWORDS)
    print(f"  {hit!s:5}  {q}")
