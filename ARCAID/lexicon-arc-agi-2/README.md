# Lexicon tools for ARC-AGI-2 (transfer demonstration)

**Layer:** perception, carried from ARC-AGI-3 to static grids. **Kill switch:** `ARCAID3_LEXICON=0`.

**Kaggle notebook:** [`habanwer/arcaid3-lexicon-agent-arc-agi-2`](https://www.kaggle.com/code/habanwer/arcaid3-lexicon-agent-arc-agi-2), versions 1–6.

**Base:** madarshbb, [*ARC Qwen 3.8 27B agent*](https://www.kaggle.com/code/madarshbb/arc-qwen-3-8-27b-agent). It is a REPL program-synthesis agent modelled on Tufa Labs' Duck harness: the model explores with `python` and verifies a `transform` with `submit`. It runs Qwen3.8-27B FP8 on vLLM over 4 L4 GPUs.

## What we changed

The cell-by-cell diff of the submitted version 6 against the base is in `Submissions/ARC-AGI-2/2026-10-31__arcaid3-lexicon-agent-arc-agi-2/v6__…/vs-root-base/DIFF.md`; every agent file as it ran, per version, is in `as-run/` (`INDEX.csv`).

| File in the agent | Base | Ours |
|---|---|---|
| `lexicon2.py` | — | **New, 417 lines:**<br>• `lexicon(g)` and `lex_objects(g)`: one name per picture across the task<br>• `changes(i)`: train input → output as objects that moved, became, appeared or disappeared<br>• `rules()`: facts that hold on every train pair |
| `repl.py`, `client.py`, `repl_agent.py`, `run_submit.py`, `submit_main.py` | madarshbb | Changed to expose the lexicon, cue it in the first prompt, restart an unverified attempt once at half its token cap, and add direct-answer phases |
| run cell | madarshbb | Changed: precaching, a server-start ladder, a 12 h deadline, and a save-run install check |
| `grids.py`, `sandbox.py`, `backend.py`, `agent.py`, `run_direct.py` | madarshbb | Unchanged |

## Scores

| Kaggle version | Submitted (UTC) | Public score | Counted on the leaderboard |
|---|---|---|---|
| v1 | 2026-10-31 12:04 | 0.00 | Yes. Scoring failed: the notebook header records that the cp312 wheels could not install on Kaggle's Python 3.13 image. |
| v6 | 2026-11-01 16:13 | **10.83** | Yes: the entry's leaderboard score |
| v6 | 2026-11-02 23:37 | 10.69 | No: late (the leaderboard counts 2 submissions, the last at 2026-11-01 16:13) |
| v6 | 2026-11-04 20:48 | 11.25 | No: after the 2026-11-02 deadline |

The two late runs are kept for their logs and outputs only. The evidence is in `Submissions/ARC-AGI-2/late.csv` and `leaderboard-own-row-2026-11-06.csv`.

**No ablation.** No run of the base, or of this notebook with `ARCAID3_LEXICON=0`, was scored. The scores therefore cannot be attributed to the lexicon.
