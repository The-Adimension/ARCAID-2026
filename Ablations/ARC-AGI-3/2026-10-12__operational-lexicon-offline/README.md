# operational-lexicon-offline

**Question.** Would three proposed 'operational' uses of the lexicon (rules predicting the next step, an unexplained-change trigger, a loop detector) work on recorded play?

| | |
|---|---|
| **Design** | Offline replay of Franzen's own 4 × 25 save-run histories (input: the `benchmark.json` of his public notebook, version 3; not redistributed here) on the official engine. |
| **Decision rule** | `DECISION_RULE.md`, committed 2026-10-12 03:03 UTC, before the result (03:15). |
| **Recorded outcome** | From `analysis/summarize.out`: decision A **kill**, decision B **kill** (90.3% of steps unexplained), decision C **do not wire in** (loop detector AUC 0.491). |
| **Code** | `analysis/` (replay, summary, per-step output, the lexicon and grammar versions used) |
| **Runs** | Offline or in `Submissions/ARC-AGI-3/`; no Kaggle runs in this folder |

`records/` holds the write-ups as they were written at the time. The outcome above is quoted from the analysis outputs, not reinterpreted.
