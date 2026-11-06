# Cell diff: habanwer/duck-nvfp4-batch-stall-warn-dead-sign-compact@v1 against its root base keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp@v13

- Base: `v13.ipynb` (sha256 5cfb825fdbe1addb…), 17 cells
- New: `__notebook__.ipynb` (sha256 fe20206e853560a1…), 22 cells

| New cell | Base cell | Type | Status | +lines | −lines | First line |
|---|---|---|---|---|---|---|
| 0 |  | markdown | added | 41 | 0 | `## v5 = v3 + arc3_compact (one change: smaller requests, same history)` |
| 1–12 | 0–11 | | identical (12 cells) | 0 | 0 | |
| 13 | 12 | code | changed | 8 | 2 | `# Exact public-25 and competition settings.` |
| 14 |  | code | added | 207 | 0 | `# arc3_batch: prompt-only predict-then-commit batching. Nothing else is touched.` |
| 15 |  | code | added | 42 | 0 | `# v5: arc3_compact. Shrinks each chat request to the local vLLM server without dropping` |
| 16–16 | 13–13 | | identical (1 cells) | 0 | 0 | |
| 17 | 14 | code | changed | 59 | 16 | `# Build the live competition game list from the gateway's available environments.` |
| 18–19 | 15–16 | | identical (2 cells) | 0 | 0 | |
| 20 |  | code | added | 139 | 0 | `# Never let the printout fail a run (this cell also runs in the competition rerun).` |
| 21 |  | code | added | 8 | 0 | `# v5 gate, save runs only: the rewrite must have fired on the harness's own model calls.` |

**Totals:** identical 15, added 5, changed 2, removed 0
