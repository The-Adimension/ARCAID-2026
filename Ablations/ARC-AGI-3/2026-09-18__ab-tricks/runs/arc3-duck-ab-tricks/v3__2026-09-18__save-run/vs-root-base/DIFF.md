# Cell diff: habanwer/arc3-duck-ab-tricks@v3 against its root base foysalemonshanto/lb-9-arc3-duck-v12-with-qwen-3-8-27b@v6

- Base: `v6.ipynb` (sha256 6c1a7fcc160d088f…), 11 cells
- New: `__notebook__.ipynb` (sha256 194dbfdf76c7942f…), 13 cells

| New cell | Base cell | Type | Status | +lines | −lines | First line |
|---|---|---|---|---|---|---|
| 0 | 0 | markdown | changed | 8 | 2 | `# ARC-AGI-3: Duck harness + arc3 tricks (A/B)` |
| 1–4 | 1–4 | | identical (4 cells) | 0 | 0 | |
| 5 | 5 | code | changed | 25 | 0 | `ARC3_SERVING_PATCHES = [` |
| 6 | 6 | code | changed | 13 | 61 | `# arc3 tricks: write the add-on, choose the arm policy, install before the benchmark is un` |
| 7 |  | code | added | 64 | 0 | `def _soft_end_time(max_runtime_s: float, *, run_as_submission: bool) -> datetime \| None:` |
| 8–8 | 7–7 | | identical (1 cells) | 0 | 0 | |
| 9 | 8 | code | changed | 11 | 30 | `# Inline customization hook — Q38 P1-style public evaluation.` |
| 10 | 9 | code | changed | 20 | 0 | `run_context = contextlib.nullcontext() if run_as_submission else _tee_to_file(WORKING_DIR ` |
| 11 |  | code | added | 91 | 0 | `# A/B report: plain Duck (even passes) vs Duck + arc3 tricks (odd passes)` |
| 12–12 | 10–10 | | identical (1 cells) | 0 | 0 | |

**Totals:** identical 6, added 2, changed 5, removed 0
