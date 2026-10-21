# Falcon3-7B-Instruct under UAE statutory frameworks: pilot audit (v2)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23547527.svg)](https://doi.org/10.5281/zenodo.23547527)

Small deterministic stress tests on one checkpoint (Falcon3-7B-Instruct, BF16, greedy decoding, one NVIDIA Blackwell MIG slice) and a rule-based vault/gate prototype around it.

**Not** a compliance assessment, certification or production test. No activation monitoring or logit intervention is performed.

Report: [`Falcon3-7B_UAE_Statutory_Audit_v2.pdf`](Falcon3-7B_UAE_Statutory_Audit_v2.pdf) (source: `report_v2.md`, figures in `figures/`).

## Evidence tiers

| Tier | Meaning | Can you regenerate it from this repo? |
|:-:|:--|:--|
| A | Script is in `scripts/`; numbers come from the author's run | Yes (GPU needed) |
| B | Numbers come from the author's run logs; script not (yet) in this repo | No |

The table assigning every reported result to a tier is in section 1 of the report. Nothing was re-run for v2.

## Layout

```
README.md  LICENSE  requirements.txt
Falcon3-7B_UAE_Statutory_Audit_v2.pdf   report_v2.md   figures/
scripts/      Tier-A measurement scripts (+ not_in_report/, CHANGES_FROM_ORIGINAL.diff, ORIGINAL_SHA256.txt)
checks/       offline checks from Appendix B + record_run_metadata.py
data/         uae_statutory_chunks.json (author paraphrases, not official texts)
results_logs/ raw logs of the original run (see EXPECTED_FILES.md)
build/        regenerates figures and PDF
```

## Quick start

```
export FALCON_PATH=/path/to/Falcon3-7B-Instruct     # local model folder
export RESULTS_DIR=results                           # optional
python3 -I checks/vault_evasion_test.py              # CPU, no model needed
python3 -I checks/tokenizer_fragmentation.py "$FALCON_PATH"
python3 scripts/run_reproducibility_audit.py         # GPU
python3 scripts/run_statutory_rag_benchmark.py       # GPU, reads data/uae_statutory_chunks.json
python3 -I checks/record_run_metadata.py "$FALCON_PATH"
```

Rebuild report: `python3 -I build/figs.py figures && python3 -I build/build_pdf.py .` (needs matplotlib, pandoc, Playwright Chromium).

## What is not included

- Scripts for batch throughput, single-turn and maintenance tests, English multi-turn/injection, the false-block test and the six-style dialect matrix (tier B in the report).
- The terminal/HTML dashboards: their numbers were typed in, not computed.
- Model weights.

## Notes

- Scripts keep their original measurement logic. Changes (paths via env vars, neutral output labels, comments) are in `scripts/CHANGES_FROM_ORIGINAL.diff`.
- The legal chunks are the author's paraphrases. Statements about DIFC Regulation 10 and CBUAE limits are not verified against primary sources.
- Cases are template variations under greedy decoding, so the report gives counts, not confidence intervals.

## License

MIT (see `LICENSE`), copyright Stefan Beierle 2026. The model Falcon3-7B-Instruct has its own license (TII Falcon License); check it before redistributing outputs or weights.

## Citation

```bibtex
@misc{beierle2026falcon3uae,
  author    = {Beierle, Stefan},
  title     = {Falcon3-7B-Instruct under UAE Statutory Frameworks: Pilot Measurements and a Rule-Based Containment Prototype},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.23547527},
  url       = {https://doi.org/10.5281/zenodo.23547527},
  note      = {Code and replication archive: https://github.com/sbeierle/falcon3-uae-audit}
}
```
