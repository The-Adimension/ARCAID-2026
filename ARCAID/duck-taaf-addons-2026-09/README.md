# Duck/TAAF add-ons, September 2026 (ARC-AGI-3)

Modules we added to the Duck/TAAF harness on the keithtyser NVFP4 and Scott Le Grand sheetu bases, before the move to Franzen's notebook. Each module's docstring states the measurement that motivated it.

| Folder | Module | What it does | Notebook versions whose added cells contain it |
|---|---|---|---|
| `batch/` | `arc3_batch.py` | Prompt-only predict-then-commit action batching (several actions per decision) | `arc3-duck-fp4-batch` v1, `-depth` v2, `-stall` v1–2, `-reset` v1–4, `-ledger` v1, `-prompts` v1, `-kvfp8` v1; `duck-nvfp4-batch-stall-warn-dead-sign` v1–5, `-compact` v1; `duck-v3-wmreason` v1; `notebook7c0bf2022d` v1; `v5b-…` v1 |
| `stall/` | `arc3_stall.py` | Warns the agent when it loops on a level it cannot clear | The same notebooks except `arc3-duck-fp4-batch` and `-depth`; also `arc3-duck-ab-tricks` v2–3 |
| `ledger/` | `arc3_ledger.py` | Prompt-only hypothesis bookkeeping after a failed attempt | `arc3-duck-fp4-ledger` v1, `-prompts` v1, `-kvfp8` v1; `duck-nvfp4-batch-stall-warn-dead-sign` v1–5, `-compact` v1; `duck-v3-wmreason` v1; `notebook7c0bf2022d` v1; `v5b-…` v1 |
| `compact/` | `arc3_compact.py` (+ test) | Drops old reasoning and repeated instruction lines from each request | `duck-nvfp4-batch-stall-warn-dead-sign-compact` v1; `v5b-…` v1 |
| `world-model-reasoning/` | `wmreason_cell.py` ("Change A") | Carries world-model lines from the model's reasoning when its visible reply has none | `duck-v3-wmreason` v1; `taaf-flashnext-sheetu12b-reasoning-notes` v1–3 |
| `tricks/` | `arc3_tricks.py` | The harness tricks compared in the A/B notebook | `arc3-duck-ab-tricks` v1–3 |

The last column is generated from `as-run/INDEX.csv`. It lists the versions whose added or changed cells (against their parent or their root base) contain the module's name. `as-run/` holds each distinct cell text once.

**What ran.** These files are the working copies from our records. The exact text that ran in each notebook version is in that version's folder under `../../Submissions/ARC-AGI-3/` or `../../Ablations/ARC-AGI-3/`. Two working copies of `arc3_compact.py` exist, and they differ; the notebook text is authoritative.
