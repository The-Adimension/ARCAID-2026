# A3-level-trials-lexicon

**Question.** Does the lexicon view change which levels are cleared, level by level?

| | |
|---|---|
| **Design** | Every level of the 25 public games (183) as a cold-start paired trial, 20 min each; view on (`arcaid3-lt-lex-r*`) vs off (`arcaid3-lt-off-r*`). Rounds 1 and 2 failed their validity checks and are kept on record; round 3 is the test. |
| **Decision rule** | `DECISION_RULE.md`, first committed 2026-10-09 21:21 UTC before round 1; revised before rounds 2 and 3 (`../PREREGISTRATION.csv`). |
| **Recorded outcome** | From `analysis/compare_level_trials.out`: cleared by the view only 8, by the control only 17, both 50, neither 108; exact McNemar p = 0.108; decision **no detectable difference at this size**. `arcaid3-lt-lex-r3` was also submitted to the leaderboard by mistake with trial settings and scored 7.16 (`records/submission-7.16-diagnosis.md`). |
| **Code** | `analysis/`, `build/level_trials*.py` |
| **Runs** | Offline or in `Submissions/ARC-AGI-3/`; no Kaggle runs in this folder |

`records/` holds the write-ups as they were written at the time. The outcome above is quoted from the analysis outputs, not reinterpreted.
