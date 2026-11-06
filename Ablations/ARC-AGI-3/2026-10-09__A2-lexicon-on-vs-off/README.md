# A2-lexicon-on-vs-off

**Question.** With a same-day control in a leaderboard-like setup, does the lexicon view (v5) help?

| | |
|---|---|
| **Design** | One notebook with the view on (`arcaid3-lb-lex-r*`) or switched off by flag (`arcaid3-lb-off-r*`); all 25 public games at once, 7,254 s each; two rounds. |
| **Decision rule** | `DECISION_RULE.md`, committed 2026-10-09 16:02 UTC, after round 1 and before round 2 (`../PREREGISTRATION.csv`). |
| **Recorded outcome** | From `analysis/compare_lb_setup.out`: on − off +7.42 (round 1), −7.49 (round 2); primary −0.03; decision **no measurable effect**. |
| **Code** | `analysis/`, `build/lb_setup.py` |
| **Runs** | Offline or in `Submissions/ARC-AGI-3/`; no Kaggle runs in this folder |

`records/` holds the write-ups as they were written at the time. The outcome above is quoted from the analysis outputs, not reinterpreted.
