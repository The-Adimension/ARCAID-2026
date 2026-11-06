# A1-replicates-v2-vs-v4

**Question.** Is the save-run difference between lexicon v2 and v4 larger than the run-to-run noise?

| | |
|---|---|
| **Design** | Three runs per version: the original save run plus two byte-identical copies (`runs/`). |
| **Decision rule** | No separate decision-rule file; the test (exact one-sided permutation) is in `analysis/compare_replicates.py`. |
| **Recorded outcome** | From `analysis/compare_replicates.out`: v4 − v2 = −0.33 points, p = 0.55; levels +0.0, p = 0.60. |
| **Code** | `analysis/`, `build/replicates.py` |
| **Runs** | Offline or in `Submissions/ARC-AGI-3/`; no Kaggle runs in this folder |

`records/` holds the write-ups as they were written at the time. The outcome above is quoted from the analysis outputs, not reinterpreted.
