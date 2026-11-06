# restart-v1

**Question.** Does restarting a stuck level's conversation once at 100,000 tokens let it be cleared?

| | |
|---|---|
| **Design** | Two byte-identical runs of `arcaid3-restart-dfranzen-m2` in the leaderboard-like setup; control rates from the A2 'off' runs. `arcaid3-restart-dfranzen-m2` v1 was also submitted (25.76). |
| **Decision rule** | `DECISION_RULE.md`, committed 2026-10-12 03:16 UTC, before the runs. |
| **Recorded outcome** | `analysis/compare_restart.out` recorded **PASS** (4/10 restarts cleared vs 19.6% control). On 2026-10-13 this was corrected as a selection artifact: with equal accounting, 5/21 vs 9/46, p = 0.46 (commit 1907f66e, see `../2026-10-13__restart-pair/DECISION_RULE.md`). |
| **Code** | `analysis/`, `ARCAID/stuck-level-restart/` |
| **Runs** | Offline or in `Submissions/ARC-AGI-3/`; no Kaggle runs in this folder |

`records/` holds the write-ups as they were written at the time. The outcome above is quoted from the analysis outputs, not reinterpreted.
