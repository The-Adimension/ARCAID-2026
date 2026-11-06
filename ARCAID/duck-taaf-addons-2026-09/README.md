# Duck/TAAF add-ons, September 2026 (ARC-AGI-3)

Modules we added to the Duck/TAAF harness on the keithtyser NVFP4 and Scott Le Grand sheetu bases, before the move to Franzen's notebook. Each module's docstring states the measurement that motivated it.

| Folder | Module | What it does | Notebooks that carried it |
|---|---|---|---|
| `batch/` | `arc3_batch.py` | Prompt-only predict-then-commit action batching (several actions per decision) | `arc3-duck-fp4-batch` and every later FP4/NVFP4 notebook |
| `stall/` | `arc3_stall.py` | Warns the agent when it loops on a level it cannot clear | `arc3-duck-fp4-stall`, `-reset`, `-ledger`, `-prompts`, `duck-nvfp4-batch-stall-warn-dead-sign` |
| `ledger/` | `arc3_ledger.py` | Prompt-only hypothesis bookkeeping after a failed attempt | `arc3-duck-fp4-ledger`, `arc3-duck-fp4-prompts` |
| `compact/` | `arc3_compact.py` (+ test) | Drops old reasoning and repeated instruction lines from each request | `duck-nvfp4-batch-stall-warn-dead-sign-compact`, `v5b-…` |
| `world-model-reasoning/` | `wmreason_cell.py` ("Change A") | Carries world-model lines from the model's reasoning when its visible reply has none | `duck-v3-wmreason`, `taaf-flashnext-sheetu12b-reasoning-notes` |

**What ran.** These files are the working copies from our records. The exact text that ran in each notebook version is in that version's folder under `../../Submissions/ARC-AGI-3/` or `../../Ablations/ARC-AGI-3/`. Two working copies of `arc3_compact.py` exist, and they differ; the notebook text is authoritative.
