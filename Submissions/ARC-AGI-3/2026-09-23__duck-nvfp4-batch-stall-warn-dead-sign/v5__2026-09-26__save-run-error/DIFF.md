# Cell diff: habanwer/duck-nvfp4-batch-stall-warn-dead-sign v5 against habanwer/duck-nvfp4-batch-stall-warn-dead-sign@v3

- Base: `__notebook__.ipynb` (sha256 e9b950f2e1753f58…), 20 cells
- New: `__notebook__.ipynb` (sha256 211e8c2bfb1818ba…), 22 cells

| New cell | Base cell | Type | Status | +lines | −lines | First line |
|---|---|---|---|---|---|---|
| 0 | 0 | markdown | changed | 16 | 0 | `## v4A = v3 + harness context window 32768 -> 24576 (one change)` |
| 1–9 | 1–9 | | identical (9 cells) | 0 | 0 | |
| 10 |  | code | added | 36 | 0 | `# v4A: harness context window 32768 -> 24576. Runs after solver setup (which wrote the` |
| 11–19 | 10–18 | | identical (9 cells) | 0 | 0 | |
| 20 | 19 | code | changed | 102 | 88 | `# Never let the printout fail a run (this cell also runs in the competition rerun).` |
| 21 |  | code | added | 14 | 0 | `# v4A gate, save runs only: the new window must have reached the harness. The per-game` |

**Totals:** identical 18, added 2, changed 2, removed 0
