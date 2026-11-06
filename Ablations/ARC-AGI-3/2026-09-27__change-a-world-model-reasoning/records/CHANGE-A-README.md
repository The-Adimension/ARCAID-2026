# Change A: carry world-model lines from the model's reasoning

## The defect (verified by an independent agent from code and data)

- **The harness ignores the reasoning.** It updates the "Working world model carried from earlier turns" block only from the model's visible reply (`tool_agent.py:1105-1111`, called only at `:1896` and `:1930`). The reasoning is never parsed.
- **On the v3 save run (402 turns):**
  - a world-model or goal-model label appeared in the visible reply on 8.2% of turns and in the reasoning on 33.8%;
  - a world model was carried into the prompt on 41.3% of turns.
- **Offline, with the harness's own parser:** the visible reply yields labels on 50 turns and the reasoning on 76. **66 of those 76 turns were ignored.**
- **Why the cap:** text taken from reasoning can reach 12,230 characters in one turn, so it is capped at 400 characters per field.

## The change (`wmreason_cell.py`)

1. **After every model response,** if the visible reply has no labels, the cell parses the reasoning with the parser the harness currently has installed (in the 5.19 notebook, that is F3's tolerant one).
2. **It writes the fields found into the carried world model,** capped as above. The visible reply still wins, because the harness applies it afterwards exactly as before.
3. **Any error leaves the response untouched** and increments `errors`.
4. **Kill switch:** set `WMREASON=0` before the cell runs.

**Tested locally** against the real `tool_agent.py`, with a fake server response:
- a reasoning-only response fills the carried block and the next prompt;
- a visible reply is left to the harness;
- long text is capped;
- re-running the cell is idempotent;
- F3's tolerant parser works through it.

## The two notebooks

Each is its base with exactly **3 added cells**: a markdown note, the change cell, and a final stats cell. Every original cell is kept unchanged and in order (verified by `build.py`'s check).

| Folder | Kaggle id (private) | Base | Save-run behaviour of the base |
|---|---|---|---|
| `notebooks/2026-09-27__v3-LB3.59__plus-changeA-wmreason__kaggle-habanwer-duck-v3-wmreason/` | `habanwer/duck-v3-wmreason` | our submitted v3 (LB 3.59) | 6 public games × 3,600 s at concurrency 6; about 70–80 min |
| `notebooks/2026-09-27__sheetu12b-LB5.19__plus-changeA-wmreason__kaggle-habanwer-sheetu12b-wmreason/` | `habanwer/sheetu12b-wmreason` | `scottlegrand/taaf-flashnext-sheetu12b-0922` v1 (LB 5.19, Apache-2.0) | 25 public games, capped at 7,200 s after vLLM boot; the author's run took 2 h 10 m |

Both use the same datasets, model, docker image and RTX Pro 6000 as their bases. The two datasets were last updated on 08-30/08-31, before v3 ran.

## Manual upload (if not pushed by API)

1. Kaggle → **New Notebook** → **File → Import Notebook**, and upload the `.ipynb` from the folder.
2. Attach the same inputs listed in that folder's `kernel-metadata.json`: the competition, the 2 datasets and the model.
3. **Accelerator:** RTX Pro 6000. **Internet:** off.
4. **Save Version → Save & Run All.**

Or from the folder: `kaggle kernels push -p notebooks/2026-09-27__v3-LB3.59__plus-changeA-wmreason__kaggle-habanwer-duck-v3-wmreason`.

## What to check in each save-run log

1. **`ARC3_WMREASON_READY cap=400 self_test=ok`.** If absent, the change is not installed; do not submit.
2. **`ARC3_WMREASON_STATS` every 100 responses, and `ARC3_WMREASON_FINAL` at the end.**
   - **Mechanism works:** `reasoning_applied > 0` and `errors == 0`.
   - **Expected size:** from the v3 transcripts, roughly 1 reasoning-applied update for each visible one or more (66 vs 50 per 402 turns).
3. **Carried world model:** the share of `[USER PROMPT]` turns in `transcripts/` that contain a non-empty "Working world model carried" block should rise above the base's (v3: 41.3%). I can compute this from the downloaded outputs.
4. **No new failures:** watch for CUDA OOM (the prompt grows by at most about 7 × 400 characters), runtime within budget, and an ordinary teardown.

## How to choose today's submission, honestly

- **What a save run can show:** whether the change works, crashes or bloats prompts.
- **What a save run cannot show:** which notebook will score higher on the hidden set. Offline public-game scores correlated with the leaderboard at r = −0.32, and the same config swings 16–44 points between runs.
- **So:**
  1. Drop any notebook that fails a check above.
  2. If both pass, the only prior evidence is the bases' single leaderboard draws: 5.19 for the sheetu base, and 3.59 (best of 8, range 2.57–3.59) for v3.
  3. Neither base has evidence that Change A raises its score.
