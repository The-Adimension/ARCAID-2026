# Cell diff: habanwer/arc3-duck-fp4-kvfp8@v1 against its root base keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp@v13

- Base: `v13.ipynb` (sha256 5cfb825fdbe1addb…), 17 cells
- New: `__notebook__.ipynb` (sha256 445c28cf60d651e7…), 21 cells

| New cell | Base cell | Type | Status | +lines | −lines | First line |
|---|---|---|---|---|---|---|
| 0 |  | markdown | added | 24 | 0 | `## Duck + NVFP4 + batch + stall warn + dead-signature ban` |
| 1–2 | 0–1 | | identical (2 cells) | 0 | 0 | |
| 3 | 2 | code | changed | 6 | 2 | `import json` |
| 4–12 | 3–11 | | identical (9 cells) | 0 | 0 | |
| 13 | 12 | code | changed | 8 | 2 | `# Exact public-25 and competition settings.` |
| 14 |  | code | added | 207 | 0 | `# arc3_batch: prompt-only predict-then-commit batching. Nothing else is touched.` |
| 15–15 | 13–13 | | identical (1 cells) | 0 | 0 | |
| 16 | 14 | code | changed | 52 | 16 | `# Build the live competition game list from the gateway's available environments.` |
| 17–18 | 15–16 | | identical (2 cells) | 0 | 0 | |
| 19 |  | code | added | 91 | 0 | `# RESET branch. Judge on the five non-sb26 games and on actions, not on the mean.` |
| 20 |  | code | added | 35 | 0 | `# arc3 v5: throughput readout from the vLLM server log. Scores are too noisy to rank varia` |

**Totals:** identical 14, added 4, changed 3, removed 0
