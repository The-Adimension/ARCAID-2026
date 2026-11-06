# Lexicon view v3 (`current_frame.rules`) on dfranzen M2: save-run result, 2026-10-08

- **Kernel:** `habanwer/arcaid3-lexicon-view-dfranzen-m2` version 3 (private), built by `kaggle/lexicon-dfranzen/build.py`.
- **Run:** pushed 12:46 UTC, ran 12:59–13:25 UTC.
- **Settings:** the same 10 public games and settings as dfranzen v1, lexicon v1 and lexicon v2: 25 min per game, 10 streams, 1 pass.
- **Reproduce:** `python3 kaggle/lexicon-dfranzen/compare_four.py` (output in `compare_four.out`).
  - Per-request usage is in `request_usage.csv`; the raw request logs (340 MB) are not committed.
  - `rules_outputs.txt` holds every distinct `.rules` output the model received.

## Did it install?

**Yes.** The `ARCAID3_LEXICON_READY` line reports:
- `scale_lock: on, self-test ok`;
- `rules: on, self-test ok`;
- all 4 prompt edits applied, and the new-board cue installed;
- 0 errors.

## Four runs, same 10 games (one run each)

| | dfranzen v1 | lexicon v1 | lexicon v2 (lock) | **lexicon v3 (rules)** |
|---|---|---|---|---|
| Levels cleared | 40 | 42 | 43 | **42** |
| 10-game mean | 36.56 | 41.13 | 42.61 | **41.76** |
| Generated tokens | 927,167 | 922,516 | 860,015 | 887,432 |
| Aggregate tok/s | 616 | 602 | 570 | 584 |
| Prompt tokens from cache | 94.2% | 94.3% | 94.7% | 95.2% |
| Tool calls reading the view | — | 12.1% | 11.1% | 12.0% |
| Tool calls reading `.rules` | — | — | — | **21 of 624 (3.4%)** |

Per game (levels / score), from `compare_four.out`:

| Game | dfranzen v1 | lexicon v1 | lexicon v2 | lexicon v3 |
|---|---|---|---|---|
| ar25 | 5 / 41.7 | 7 / 77.8 | 5 / 41.7 | 5 / 41.7 |
| ft09 | 4 / 47.6 | 0 / 0.0 | 6 / 100.0 | 6 / 100.0 |
| lp85 | 5 / 41.7 | 5 / 40.1 | 4 / 22.1 | 6 / 58.3 |
| r11l | 2 / 14.3 | 2 / 14.3 | 1 / 4.8 | 2 / 14.3 |
| re86 | 3 / 16.7 | 5 / 41.7 | 5 / 41.7 | 5 / 41.7 |
| sb26 | 8 / 93.3 | 8 / 100.0 | 8 / 100.0 | 8 / 99.8 |
| sc25 | 3 / 28.6 | 2 / 11.3 | 4 / 44.5 | 1 / 0.2 |
| tr87 | 4 / 47.6 | 5 / 71.4 | 4 / 39.1 | 1 / 4.8 |
| tu93 | 3 / 13.1 | 5 / 33.3 | 3 / 10.9 | 4 / 21.1 |
| vc33 | 3 / 21.1 | 3 / 21.4 | 3 / 21.4 | 4 / 35.7 |

**The score difference is noise.** One run of a 10-game mean has an SD of about 7 points, and a difference between two single runs about 10 points. v3 sits between v1 and v2. Per-game swings go both ways: lp85 and vc33 went up, while sc25 and tr87 went down. tr87 and sc25 never read `.rules` after their first steps (see below), so those drops can't come from the rules.

## How the model used the rules

- **21 tool calls read `.rules`.** The model saw 19 distinct outputs:
  - 8 said "no steps yet": `.rules` was printed at the very start of a level, before any action;
  - 4 had too few repeats for any rule;
  - 7 contained rules.
- **No `.rules` call failed or timed out.** None of the outputs says "rules unavailable". The run had 2 sandbox timeouts, both from other code.
- **Examples from real games:**
  ```
  ft09 level 2   when any then recolor(clicked, {b:O})                           # 7 right, 0 wrong
  ar25 level 2   when LEFT|RIGHT then move(colour:W, by action: LEFT (+0,-3) | RIGHT (+0,+3))
  sc25 level 1   when any unless touch:p then recolor(clicked, {W:N, g:N, N:W})   # 25 right, 8 wrong
                 when RIGHT then move(colour:S, (+0,+2))                          # 5 right, 0 wrong
  vc33 level 1   when any then resize(colour:c, +1)                               # 5 right, 2 wrong
  ```
- **What this shows:** the rules work in the real harness and cost nothing measurable in serving (cache reuse 95.2%, throughput within the runs' spread). But the model mostly asks for them at the wrong moment. The new-board flow leads it to look at a level's start, when there is nothing to learn from yet. Rules become useful after a few repeated actions, or when an action does something unexpected.

## Next

- **Cue `.rules` when it can answer.** Add it after an action fails or surprises (the harness already reports `no_op` and stale-state errors), or after several steps on a level, rather than on a new board.
- **Fix the known perception limits** before reading anything into scores:
  - objects that merge on contact;
  - identity read by picture, so same-looking tiles that change colour look like moves;
  - the lock accepting a coarser grid that "mostly fits".
- **Submission:** not submitted. A submission would test the hidden set but couldn't separate this change from noise (copies of identical code score 21–29).
