# Cell diff: habanwer/arc3-duck-ab-tricks v2 against habanwer/arc3-duck-ab-tricks@v1

- Base: `__notebook__.ipynb` (sha256 e466f9a20a2751ae…), 13 cells
- New: `__notebook__.ipynb` (sha256 95db2c29ff543e82…), 13 cells

| New cell | Base cell | Type | Status | +lines | −lines | First line |
|---|---|---|---|---|---|---|
| 0 | 0 | markdown | changed | 5 | 3 | `# ARC-AGI-3: Duck harness + arc3 tricks (A/B)` |
| 1–4 | 1–4 | | identical (4 cells) | 0 | 0 | |
| 5 | 5 | code | changed | 25 | 0 | `ARC3_SERVING_PATCHES = [` |
| 6 | 6 | code | changed | 3 | 2 | `# arc3 tricks: write the add-on, choose the arm policy, install before the benchmark is un` |
| 7 | 7 | code | changed | 3 | 1 | `def _soft_end_time(max_runtime_s: float, *, run_as_submission: bool) -> datetime \| None:` |
| 8–8 | 8–8 | | identical (1 cells) | 0 | 0 | |
| 9 | 9 | code | changed | 10 | 14 | `# Inline customization hook — Q38 P1-style public evaluation.` |
| 10 | 10 | code | changed | 20 | 0 | `run_context = contextlib.nullcontext() if run_as_submission else _tee_to_file(WORKING_DIR ` |
| 11 | 11 | code | changed | 47 | 25 | `# A/B report: plain Duck (even passes) vs Duck + arc3 tricks (odd passes)` |
| 12–12 | 12–12 | | identical (1 cells) | 0 | 0 | |

**Totals:** identical 6, added 0, changed 7, removed 0
