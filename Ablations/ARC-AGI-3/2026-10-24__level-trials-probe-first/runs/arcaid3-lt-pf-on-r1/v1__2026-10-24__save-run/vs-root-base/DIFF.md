# Cell diff: habanwer/arcaid3-lt-pf-on-r1@v1 against its root base dfranzen/arc-agi-3-milestone-2-solution@v1

- Base: `v1.ipynb` (sha256 5796431ea6bbd58b…), 23 cells
- New: `__notebook__.ipynb` (sha256 2d7004c1160ea8ff…), 29 cells

| New cell | Base cell | Type | Status | +lines | −lines | First line |
|---|---|---|---|---|---|---|
| 0 |  | markdown | added | 3 | 0 | `# ARCAID3 paired level trial, round 1, arm PF=1 (probe-first governor ON)` |
| 1–4 | 0–3 | | identical (4 cells) | 0 | 0 | |
| 5 | 4 | code | changed | 1 | 1 | `import json` |
| 6–16 | 5–15 | | identical (11 cells) | 0 | 0 | |
| 17 | 16 | code | changed | 3 | 3 | `# Make one-off changes to `bm`, `bm.games`, or `bm.solver` here before the run starts.` |
| 18–19 | 17–18 | | identical (2 cells) | 0 | 0 | |
| 20 |  | markdown | added | 1 | 0 | `## ARCAID3 probe-first governor cell (the arm flag decides whether it installs)` |
| 21 |  | code | added | 5 | 0 | `# ARCAID3 paired level trial: arm flag. The probe-first cell below reads PF from the envir` |
| 22 |  | code | added | 251 | 0 | `# First-run defaults (explicit for the record; the cell reads these from the environment).` |
| 23–23 | 19–19 | | identical (1 cells) | 0 | 0 | |
| 24 | 20 | code | changed | 58 | 88 | `# ARCAID3 level trials (evaluation only): every level of every game becomes its own trial.` |
| 25 |  | code | added | 93 | 0 | `print('Starting benchmark...')` |
| 26–27 | 21–22 | | identical (2 cells) | 0 | 0 | |
| 28 |  | code | added | 5 | 0 | `# Probe-first governor: final counters for this run (never raises).` |

**Totals:** identical 20, added 6, changed 3, removed 0
