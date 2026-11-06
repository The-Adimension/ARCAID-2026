# hypothesis-confidence

**Question.** Given a hypothesis an agent wrote about a level, can a text model trained on other games predict that it is wrong better than the agent's stated confidence?

| | |
|---|---|
| **Design** | Offline. 1,027 hypotheses from public ARA Labs ledgers (CC-BY-4.0; `data/ATTRIBUTION.md`); leave-one-game-out; bootstrap CI. |
| **Decision rule** | Pre-set rule recorded at step 1 of `records/RUNLOG.md` (2026-09-27 07:49 UTC). |
| **Recorded outcome** | From `records/RESULTS.md`: the pre-set rule was **not met** (text vs stated confidence: ΔAUC −0.081 and −0.002). A first 'MET', made against the wrong baseline, was withdrawn in the log at step 5. |
| **Code** | `analysis/` (dataset build and test scripts) |
| **Runs** | Offline or in `Submissions/ARC-AGI-3/`; no Kaggle runs in this folder |

`records/` holds the write-ups as they were written at the time. The outcome above is quoted from the analysis outputs, not reinterpreted.
