# Cell diff: habanwer/duck-nvfp4-batch-stall-warn-dead-sign-compact v1 against habanwer/duck-nvfp4-batch-stall-warn-dead-sign@v5

- Base: `__notebook__.ipynb` (sha256 211e8c2bfb1818ba…), 22 cells
- New: `__notebook__.ipynb` (sha256 fe20206e853560a1…), 22 cells

| New cell | Base cell | Type | Status | +lines | −lines | First line |
|---|---|---|---|---|---|---|
| 0 | 0 | markdown | changed | 9 | 8 | `## v5 = v3 + arc3_compact (one change: smaller requests, same history)` |
| 1–9 | 1–9 | | identical (9 cells) | 0 | 0 | |
| | 10 | code | removed | 0 | 36 | `# v4A: harness context window 32768 -> 24576. Runs after solver setup (which wrote the` |
| 10–14 | 11–15 | | identical (5 cells) | 0 | 0 | |
| 15 |  | code | added | 42 | 0 | `# v5: arc3_compact. Shrinks each chat request to the local vLLM server without dropping` |
| 16–19 | 16–19 | | identical (4 cells) | 0 | 0 | |
| 20 | 20 | code | changed | 47 | 13 | `# Never let the printout fail a run (this cell also runs in the competition rerun).` |
| 21 | 21 | code | changed | 6 | 12 | `# v5 gate, save runs only: the rewrite must have fired on the harness's own model calls.` |

**Totals:** identical 18, added 1, changed 3, removed 1
