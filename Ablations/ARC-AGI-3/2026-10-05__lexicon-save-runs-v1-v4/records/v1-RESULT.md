# Lexicon view on dfranzen M2: save-run result, 2026-10-05

- **Kernel:** `habanwer/arcaid3-lexicon-view-dfranzen-m2` v1 (private). Built by `kaggle/lexicon-dfranzen/build.py`.
- **Run:** 18:50:37 → 19:16:09 UTC. dfranzen's own v1 demo settings: 10 public games, 25 min each, 10 streams, 1 pass.
- **Baseline:** dfranzen v1's saved run with the same settings, in `external_submission/2026-09-30__dfranzen__…__v1__teambest-27.89/outputs/`.
- **Reproduce:** `python kaggle/lexicon-dfranzen/compare_save_run.py`. It reads `outputs/benchmark.json` and `request_usage.csv`, which is derived from the 10 raw request logs (275 MB, not committed; the script re-downloads them if the table is missing).

## Did the port work?

- **Yes, it installed cleanly.**
  - `ARCAID3_LEXICON_READY`: all 4 prompt edits `applied`, cue installed, real-sandbox `self_test` `ok`, 0 errors.
  - Serving started in 655 s, and dfranzen's priority gate and harness ran as in his run.
- **Usage:** 62 of 513 tool calls read the view (12.1%). On the sheetu base it was 22%.
  - By member: `.code` 58, `.objects` 3, `.native` 1, `changes_since` 0. dfranzen's own `frame_diff()` covers object diffs, and the model kept using it.
  - Cue turns: 52.
  - In 9 of 10 games the first `.code` read is the first tool call of the game. The cue drives it, and use then tapers. re86 used it most (19 of 56 calls).

## Mechanics: the view costs nothing in serving

| | dfranzen v1 | + lexicon view |
|---|---|---|
| LLM requests | 531 | 516 |
| Prompt tokens, median / p90 | 66,710 / 103,511 | 66,173 / 104,576 |
| Prompt tokens served from cache | 94.2% | 94.3% |
| Generated tokens (sum of per-game notes) | 927,167 | 922,516 |
| Aggregate generated tok/s (per-game notes ÷ longest game wall) | 616 | 602 |

The run's own summary line reads 558.9 tok/s. That figure is computed against the job wall clock, a different denominator; the table uses the same metric for both runs.

## Score: inside noise

| Game | dfranzen v1 levels / score | + lexicon levels / score |
|---|---|---|
| ar25 | 5 / 41.7 | 7 / 77.8 |
| ft09 | 4 / 47.6 | 0 / 0.0 |
| lp85 | 5 / 41.7 | 5 / 40.1 |
| r11l | 2 / 14.3 | 2 / 14.3 |
| re86 | 3 / 16.7 | 5 / 41.7 |
| sb26 | 8 / 93.3 | 8 / 100.0 |
| sc25 | 3 / 28.6 | 2 / 11.3 |
| tr87 | 4 / 47.6 | 5 / 71.4 |
| tu93 | 3 / 13.1 | 5 / 33.3 |
| vc33 | 3 / 21.1 | 3 / 21.4 |
| **10-game mean / levels** | **36.56 / 40** | **41.13 / 42** |

- **The gap is +4.57 points (+12.5%) and +2 levels, on one run per arm.**
- **The noise is about 10 points.** dfranzen's own 4 replicates of these 10 games (v3 public artifact, `skarin` audit) give per-game SDs of 0–39 points. That makes the SD of a 10-game mean about 7.1, and of a difference between two single runs about 10.0. The gap is about 0.46 SD.
  - Those replicates ran at a longer per-game budget, so this is an order of magnitude, not an exact bar.
- **Per-game swings go both ways and match known instability.** ft09 went 47.6 → 0 (dfranzen's replicates: 100, 47.6, 100, 100). ar25 went 41.7 → 77.8 (replicates: 100, 100, 100, 41.7). The view isn't implicated in ft09: it was read in 3 of 30 calls, once at the start.

## Verdict

- **The port is sound and safe to keep:** it is installed, used, and costs nothing in cache reuse, prompt size or throughput.
- **No score effect is shown.** This run cannot show one, and neither can a single leaderboard draw (hidden-board copies of the base span 21–29).
- **A test that could see a +10% effect** needs multiple replicates per arm at matched tokens, or several hidden-board draws per arm (`report-2026-10-05.md` section 3).

## Leaderboard (added 2026-10-06)

- **Submission `56873728`** (scriptVersionId `355438281`, kernel v1, the same code as pushed): submitted 2026-10-06 07:14 UTC, scored **24.95** on the public LB.
- **Team position:** rank 781 of 3,876 (LB snapshot 2026-10-06 17:48 UTC). Previous team best 4.17.
- **Against the noise band:** unchanged dfranzen copies score 25.8 ± 2.9, with identical-code draws spanning 21.01–29.08. 24.95 sits inside that band, so the lexicon view shows no measurable effect on the hidden set. The gain over 4.17 comes from the dfranzen base.
- **Same day, old base:** lexicon view v2 on sheetu (submission `56845541`) scored 4.56, inside its own 2.3–6.1 band.
