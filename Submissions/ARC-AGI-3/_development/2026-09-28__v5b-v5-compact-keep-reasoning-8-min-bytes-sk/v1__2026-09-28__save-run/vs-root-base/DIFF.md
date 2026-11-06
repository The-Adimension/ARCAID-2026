# Cell diff: habanwer/v5b-v5-compact-keep-reasoning-8-min-bytes-sk@v1 against its root base keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp@v13

- Base: `v13.ipynb` (sha256 5cfb825fdbe1addb…), 17 cells
- New: `__notebook__.ipynb` (sha256 2b2684a62e379672…), 22 cells

| New cell | Base cell | Type | Status | +lines | −lines | First line |
|---|---|---|---|---|---|---|
| 0 |  | markdown | added | 45 | 0 | `## v5b = v5 compact + KEEP_REASONING=8 + min-bytes skip` |
| 1–12 | 0–11 | | identical (12 cells) | 0 | 0 | |
| 13 | 12 | code | changed | 8 | 2 | `# Exact public-25 and competition settings.` |
| 14 |  | code | added | 207 | 0 | `# arc3_batch: prompt-only predict-then-commit batching. Nothing else is touched.` |
| 15 |  | code | added | 44 | 0 | `# v5b: same compact hook as v5, but KEEP_REASONING=8 after the self-test and` |
| 16–16 | 13–13 | | identical (1 cells) | 0 | 0 | |
| 17 | 14 | code | changed | 59 | 16 | `# Build the live competition game list from the gateway's available environments.` |
| 18–19 | 15–16 | | identical (2 cells) | 0 | 0 | |
| 20 |  | code | added | 145 | 0 | `# Never let the printout fail a run (this cell also runs in the competition rerun).` |
| 21 |  | code | added | 14 | 0 | `# v5 gate, save runs only: the rewrite must have fired on the harness's own model calls.` |

**Totals:** identical 15, added 5, changed 2, removed 0
