# Cell diff: habanwer/arc3-duck-fp4-reset@v3 against its root base keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp@v13

- Base: `v13.ipynb` (sha256 5cfb825fdbe1addb…), 17 cells
- New: `__notebook__.ipynb` (sha256 c015fa0f56ecaf70…), 20 cells

| New cell | Base cell | Type | Status | +lines | −lines | First line |
|---|---|---|---|---|---|---|
| 0 |  | markdown | added | 11 | 0 | `## Duck + NVFP4 + batching + stall RESET (2 passes)` |
| 1–12 | 0–11 | | identical (12 cells) | 0 | 0 | |
| 13 | 12 | code | changed | 6 | 2 | `# Exact public-25 and competition settings.` |
| 14 |  | code | added | 42 | 0 | `# arc3_batch: prompt-only predict-then-commit batching. Nothing else is touched.` |
| 15–15 | 13–13 | | identical (1 cells) | 0 | 0 | |
| 16 | 14 | code | changed | 30 | 8 | `# Build the live competition game list from the gateway's available environments.` |
| 17–18 | 15–16 | | identical (2 cells) | 0 | 0 | |
| 19 |  | code | added | 91 | 0 | `# RESET branch. Judge on the five non-sb26 games and on actions, not on the mean.` |

**Totals:** identical 15, added 3, changed 2, removed 0
