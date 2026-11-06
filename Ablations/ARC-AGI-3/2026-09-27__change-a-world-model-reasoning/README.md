# change-a-world-model-reasoning

**Question.** Does carrying world-model lines from the model's reasoning (Change A) change the score?

| | |
|---|---|
| **Design** | Two single-change pairs, each scored once on the leaderboard: `duck-nvfp4-batch-stall-warn-dead-sign` v3 vs `duck-v3-wmreason` v1, and `taaf-flashnext-sheetu12b-0922` v1 vs `taaf-flashnext-sheetu12b-reasoning-notes` v3. The notebooks are in `Submissions/ARC-AGI-3/`. |
| **Decision rule** | No pre-registered rule. |
| **Recorded outcome** | Public scores: 3.59 → 3.03 and 4.17 → 3.90 (one draw per arm). |
| **Code** | `ARCAID/duck-taaf-addons-2026-09/world-model-reasoning/` |
| **Runs** | Offline or in `Submissions/ARC-AGI-3/`; no Kaggle runs in this folder |

`records/` holds the write-ups as they were written at the time. The outcome above is quoted from the analysis outputs, not reinterpreted.
