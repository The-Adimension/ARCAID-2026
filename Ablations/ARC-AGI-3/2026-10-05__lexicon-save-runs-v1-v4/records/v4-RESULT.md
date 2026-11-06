# Lexicon view v4 (rules cue, perception fixes) on dfranzen M2: save-run result, 2026-10-08

- **Kernel:** `habanwer/arcaid3-lexicon-view-dfranzen-m2` version 4 (private), built by `kaggle/lexicon-dfranzen/build.py`.
- **Run:** pushed 18:41 UTC, ran 18:51–19:17 UTC.
- **Settings:** the same 10 public games and settings as the four earlier runs: 25 min per game, 10 streams, 1 pass.
- **Reproduce:** `python3 kaggle/lexicon-dfranzen/compare_five.py` (output in `compare_five.out`).
  - Per-request usage is in `request_usage.csv`; the raw request logs are not committed.
  - `rules_outputs.txt` holds every distinct `.rules` output the model received.

## Did it install?

**Yes.** `ARCAID3_LEXICON_READY` reports:
- `scale_lock: on, self-test ok`;
- `rules: on, self-test ok`;
- all 4 prompt edits applied, and the new-board cue installed;
- 0 errors.

The sandbox program fits the 128 KiB argument limit: 97,325 bytes, packed.

## Five runs, same 10 games (one run each)

| | dfranzen v1 | lexicon v1 | v2 (lock) | v3 (rules) | **v4 (cue + fixes)** |
|---|---|---|---|---|---|
| Levels cleared | 40 | 42 | 43 | 42 | **50** |
| 10-game mean | 36.56 | 41.13 | 42.61 | 41.76 | **55.36** |
| Generated tokens | 927,167 | 922,516 | 860,015 | 887,432 | 871,078 |
| Aggregate tok/s | 616 | 602 | 570 | 584 | 572 |
| Prompt tokens from cache | 94.2% | 94.3% | 94.7% | 95.2% | 93.9% |
| Tool calls reading the view | — | 12.1% | 11.1% | 12.0% | **17.0%** |
| Tool calls reading `.rules` | — | — | — | 21 | **40** |
| Turns carrying the rules cue | — | — | — | — | 111 |

Per game (levels / score):

| Game | dfranzen v1 | lexicon v1 | v2 | v3 | v4 |
|---|---|---|---|---|---|
| ar25 | 5 / 41.7 | 7 / 77.8 | 5 / 41.7 | 5 / 41.7 | 5 / 41.7 |
| ft09 | 4 / 47.6 | 0 / 0.0 | 6 / 100.0 | 6 / 100.0 | 6 / 100.0 |
| lp85 | 5 / 41.7 | 5 / 40.1 | 4 / 22.1 | 6 / 58.3 | 6 / 58.3 |
| r11l | 2 / 14.3 | 2 / 14.3 | 1 / 4.8 | 2 / 14.3 | 2 / 14.3 |
| re86 | 3 / 16.7 | 5 / 41.7 | 5 / 41.7 | 5 / 41.7 | 5 / 41.7 |
| sb26 | 8 / 93.3 | 8 / 100.0 | 8 / 100.0 | 8 / 99.8 | 8 / 100.0 |
| sc25 | 3 / 28.6 | 2 / 11.3 | 4 / 44.5 | 1 / 0.2 | 3 / 28.6 |
| tr87 | 4 / 47.6 | 5 / 71.4 | 4 / 39.1 | 1 / 4.8 | **6 / 100.0** |
| tu93 | 3 / 13.1 | 5 / 33.3 | 3 / 10.9 | 4 / 21.1 | 5 / 33.3 |
| vc33 | 3 / 21.1 | 3 / 21.4 | 3 / 21.4 | 4 / 35.7 | 4 / 35.7 |

## How to read it

- **This is the best of the five runs, but it is one run.**
  - The difference between two single runs has an SD of about 10 points.
  - v4 is +12.75 over the best earlier run (v2, about 1.3 SD) and +18.8 over dfranzen v1 (about 1.9 SD).
  - Levels went from 43 (v2) to 50.
  - The gain is concentrated in tr87 (6 levels, against 1–5 before), tu93 and sc25. Six games score the same as in v3.
- **The rules' content does not explain the gain on its own.**
  - Of the 40 distinct `.rules` outputs the model saw, only 4 came before any action on the level (v3: 8 of 19).
  - 17 said "none yet": no change had repeated often enough to form a rule.
  - In tr87, every rules output it got said "no steps yet" or "none yet".
  - What changed visibly is behaviour: the view was read in 17.0% of tool calls (12% before), and the cue appeared on 111 turns.
  - So the cue prompting a structured look may matter more than what the rules said, or the gain may be noise. One run cannot tell.
- **No failures:** no `.rules` call failed or timed out (0 tool timeouts in the whole run).
- **Serving cost** stayed within the earlier runs' range: cache reuse 93.9%, 572 tok/s, fewer requests (577).

## Next

1. **Replicates before believing it.** Two or three more save runs of v4, and of v2 or v3 at the same settings, would show whether +13 is real. Alternatively, submit v4: the hidden set is the real test, though copies of identical code already span 21–29 on the leaderboard.
2. **Rules that say something sooner.** 17 of 40 outputs had no rule yet. Option: show the strongest candidates seen twice, marked as tentative, instead of nothing.
3. **Look-alike tiles that change colour:** a frame-pair rule made perception worse (see `kaggle/lexicon-dfranzen/README.md`). It needs evidence across steps.

## Submission

- **Submission `56975852`:** kernel version 4, the code checked by `verify_port.py` and run above; output file `submission.parquet`. Submitted 2026-10-08 22:29 UTC; scored by 2026-10-09 07:34 UTC.
- **Earlier result for comparison:** v1 of this notebook scored 24.95 on the public leaderboard (submission `56873728`).
- **Noise band:** unchanged dfranzen copies score 25.8 ± 2.9, with identical-code draws spanning 21.01–29.08. A v4 score inside that band would show no measurable effect on the hidden set.

**Result: public LB 27.05**, rank 764 of 4,024 teams (leaderboard snapshot 2026-10-09 07:35 UTC).
- **Against v1:** +2.10 over v1's 24.95.
- **Against the noise band:** unchanged dfranzen copies score 25.8 ± 2.9, with identical-code draws spanning 21.01–29.08. 27.05 sits inside that band.
- **Conclusion:** the save run's +12.75 on the 10 demo games did not show up as a measurable gain on the hidden set. One submission can't detect an effect much smaller than the band, so v4 neither helps nor hurts on present evidence.

## Replicates (2026-10-09)

Two more save runs each of v4 and v2 (byte-identical notebooks, run in pairs) settle the question in "How to read it":
- v4 averages **47.81** over three runs (55.36, 43.70, 44.38), and v2 averages **48.15** (42.61, 47.46, 54.37).
- The difference is −0.33 points (permutation p = 0.55).
- This run's +12.75 was noise.

See `experiments/2026-10-09__replicates-v2-vs-v4/RESULT.md`.
