# ab-tricks

**Question.** Do the harness tricks in `arc3_tricks.py` change Duck's play on public games?

| | |
|---|---|
| **Design** | One notebook runs both arms (A and B) on the same public games; versions 1–3 of `arc3-duck-ab-tricks`. |
| **Decision rule** | No pre-registered rule. |
| **Recorded outcome** | Version 1 failed (duplicate game ids). Versions 2 and 3 completed; see `records/ab_report_2026-09-18.md` and each run's `outputs/summary.txt`. |
| **Code** | `ARCAID/duck-taaf-addons-2026-09/tricks/arc3_tricks.py` |
| **Runs** | Offline or in `Submissions/ARC-AGI-3/`; no Kaggle runs in this folder |

`records/` holds the write-ups as they were written at the time. The outcome above is quoted from the analysis outputs, not reinterpreted.
