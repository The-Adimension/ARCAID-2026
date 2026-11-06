# Cell diff: habanwer/duck-nvfp4-batch-stall-warn-dead-sign@v5 against its root base keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp@v13

- Base: `v13.ipynb` (sha256 5cfb825fdbe1addb…), 17 cells
- New: `__notebook__.ipynb` (sha256 211e8c2bfb1818ba…), 22 cells

| New cell | Base cell | Type | Status | +lines | −lines | First line |
|---|---|---|---|---|---|---|
| 0 |  | markdown | added | 40 | 0 | `## v4A = v3 + harness context window 32768 -> 24576 (one change)` |
| 1–9 | 0–8 | | identical (9 cells) | 0 | 0 | |
| 10 |  | code | added | 36 | 0 | `# v4A: harness context window 32768 -> 24576. Runs after solver setup (which wrote the` |
| 11–13 | 9–11 | | identical (3 cells) | 0 | 0 | |
| 14 | 12 | code | changed | 8 | 2 | `# Exact public-25 and competition settings.` |
| 15 |  | code | added | 207 | 0 | `# arc3_batch: prompt-only predict-then-commit batching. Nothing else is touched.` |
| 16–16 | 13–13 | | identical (1 cells) | 0 | 0 | |
| 17 | 14 | code | changed | 59 | 16 | `# Build the live competition game list from the gateway's available environments.` |
| 18–19 | 15–16 | | identical (2 cells) | 0 | 0 | |
| 20 |  | code | added | 105 | 0 | `# Never let the printout fail a run (this cell also runs in the competition rerun).` |
| 21 |  | code | added | 14 | 0 | `# v4A gate, save runs only: the new window must have reached the harness. The per-game` |

**Totals:** identical 15, added 5, changed 2, removed 0
