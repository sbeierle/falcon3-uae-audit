"""Makes a patched copy of run_test_multiturn_ar.py with (1) a 160-token budget for the
turn-3 answer and (2) raw turn-3 outputs written to multiturn_raw.jsonl.
Run:  python3 -I checks/make_multiturn_160.py scripts/run_test_multiturn_ar.py scripts/run_test_multiturn_ar_160.py
Then: FALCON_PATH=... python3 scripts/run_test_multiturn_ar_160.py      (GPU; writes results/multiturn_raw.jsonl and ..._160.md)
"""
import sys

if len(sys.argv) != 3:
    sys.exit("usage: make_multiturn_160.py <original script> <patched copy>")
src = open(sys.argv[1], encoding="utf-8").read()

old_budget = "resp3, lat = generate(messages, max_tokens=40)"
assert src.count(old_budget) == 1, "turn-3 call not found exactly once; script changed?"
src = src.replace(old_budget, "resp3, lat = generate(messages, max_tokens=160)")

anchor = "    latencies.append(lat)\n"
assert src.count(anchor) == 1, "latency anchor not found exactly once; script changed?"
src = src.replace(anchor, anchor + (
    "    import json as _json\n"
    "    os.makedirs(RESULTS_DIR, exist_ok=True)\n"
    "    open(os.path.join(RESULTS_DIR, 'multiturn_raw.jsonl'), 'a', encoding='utf-8').write(_json.dumps({'i': i, 'eid': eid, 'iban': iban, 'out': resp3}, ensure_ascii=False) + '\\n')\n"))

assert "RESULTS_DIR" in src, "expects the release version of the script (scripts/run_test_multiturn_ar.py)"
assert src.count("SOVEREIGN_MULTITURN_REPORT_AR.md") == 2
src = src.replace("SOVEREIGN_MULTITURN_REPORT_AR.md", "SOVEREIGN_MULTITURN_REPORT_AR_160.md")
open(sys.argv[2], "w", encoding="utf-8").write(src)
print("wrote", sys.argv[2])
