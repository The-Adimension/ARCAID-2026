# Lexicon view v2 (per-level scale lock) on dfranzen M2: save-run result, 2026-10-07

- **Kernel:** `habanwer/arcaid3-lexicon-view-dfranzen-m2` version 2 (private), built by `kaggle/lexicon-dfranzen/build.py`.
  - Pushed 10:55 UTC, once a GPU slot freed up. Both slots had been held by the gemma4-deva notebooks.
  - Run 11:04:57 → 11:30:07 UTC, with the same save settings as v1: 10 public games, 25 min each, 10 streams, 1 pass.
- **Reproduce:** `python3 kaggle/lexicon-dfranzen/compare_three.py` (output in `compare_three.out`). Per-request usage is in `request_usage.csv`; the raw request logs are not committed.

## Did it run as intended?

- **Yes.** `ARCAID3_LEXICON_READY`: `scale_lock: on, self-test ok`, all 4 prompt edits applied, cue installed, view self-test ok, 0 errors.
- **View usage:** 67 of 604 tool calls (11.1%), against 12.1% in v1: `.code` 52, `.objects` 15, `changes_since` 0.

## Three runs, same 10 games and budget

| | dfranzen v1 | lexicon v1 | lexicon v2 (lock) |
|---|---|---|---|
| Levels cleared | 40 | 42 | **43** |
| 10-game mean | 36.56 | 41.13 | **42.61** |
| Generated tokens | 927,167 | 922,516 | 860,015 |
| Tokens/s (per-game notes ÷ longest game) | 616 | 602 | 570 |
| LLM requests | 531 | 516 | 607 |
| Prompt tokens from cache | 94.2% | 94.3% | 94.7% |

Per game (levels / score): see `compare_three.out`.

## Where the lock actually acted

v2's recorded actions were replayed on the official engine, and every frame was read with and without the lock (`kaggle/lexicon-dfranzen/eval_scale_lock.py` logic; 1,477 steps):

- **Only vc33's readings changed:** flips 8.2% → 1.4%, block size equal to the camera's 34% → 39%, lost pixels 60.6 → 53.1 per frame, move recall 27.5% → 32.1%.
- **vc33 scored the same in all three runs** (3 levels, about 21).
- **The score swings are elsewhere:** ft09 0 → 100 against v1, and sc25, lp85, tr87, tu93. Those are games where the lock changed no reading, so they are run-to-run noise, not the lock.
- **The throughput dip is not explained by the lock.** The lock runs only when the view is read (67 calls). Each call costs at most about 0.3 s of sandbox time, about 20 s in total, against 25 minutes of game time per game.

## Verdict

- **The lock works as designed, in the real harness, and costs nothing measurable.** On these 10 games it only acts on vc33, where it makes the readings steadier and more accurate.
- **It cannot be credited with the higher score.** The +1.5 over v1 and +6 over dfranzen v1 sit within the noise of single 10-game runs (SD of a difference ≈ 10 points, `RESULT.md` of v1).
