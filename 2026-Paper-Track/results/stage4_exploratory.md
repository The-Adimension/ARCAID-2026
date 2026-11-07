# Stage 4: exploratory mechanism analyses

**Exploratory.** Specified in [`../ANALYSIS-PLAN.md`](../ANALYSIS-PLAN.md) §4. Nothing here is confirmed; patterns are reported with counts and 95% bootstrap intervals over games (2,000 resamples, seed 0). Script: `analysis/stage4_exploratory.py`; all numbers: `stage4_exploratory.json`.

## M1. Reading vs acting (lexicon-on runs)

Turns in lexicon-on runs: 12,005; turns whose tool code read `current_frame.code` or `.rules`: 2,868. The stratified difference compares turns with and without a read within the same run, game and level.

| Outcome of the turn | With a read | Without | Stratified difference (95% CI) | Lexicon-off runs, for reference |
|---|---|---|---|---|
| executes at least one action | 96.3% | 94.2% | +2.3 pts (+1.5 to +3.2) | 96.4% |
| share of its actions that change the board | 89.8% | 92.9% | -4.1 pts (-6.0 to -2.2) | 91.7% |
| completes a level | 3.8% | 9.4% | -10.6 pts (-14.3 to -6.8) | 6.0% |
| a level completes within 10 actions of the turn's start | 9.9% | 12.8% | -9.3 pts (-14.1 to -5.5) | 9.3% |
| ends in a game over | 1.6% | 2.0% | -0.2 pts (-1.3 to +1.6) | 1.7% |

## M2. Spending in the paired level trials

| Arm | Trials | Cleared | Completion tokens per cleared level | Median tokens per trial | No-action response share | No-action token share | Median tokens before the first action | Turns without an action | Truncated responses |
|---|---|---|---|---|---|---|---|---|---|
| A3 lexicon on (r3) | 183 | 58 | 237,800 | 76,014 | 52.9% | 55.3% | 2,233 | 4.8% | 51 |
| A3 lexicon off (r3) | 183 | 67 | 207,773 | 75,705 | 49.7% | 53.1% | 2,565 | 4.8% | 63 |
| probe-first on (r1) | 183 | 69 | 197,597 | 76,191 | 49.6% | 51.2% | 2,303 | 4.9% | 110 |
| probe-first off (r1) | 183 | 58 | 231,189 | 76,639 | 50.1% | 52.9% | 2,199 | 5.1% | 58 |
| probe-first on (r2) | 183 | 65 | 209,142 | 77,140 | 49.6% | 51.2% | 2,386 | 5.1% | 116 |
| probe-first off (r2) | 183 | 58 | 230,518 | 75,739 | 49.8% | 51.4% | 2,275 | 5.1% | 51 |

No-action shares follow the definition in `Ablations/ARC-AGI-3/2026-10-24__level-trials-probe-first/analysis/lt_analysis.py` (a response after which the action count did not advance).

## M3. Stuck levels against cleared levels

| Generation | Levels | Cleared? | Median actions | Median share of actions revisiting a seen board | Median unchanged-board share | Game-overs per 100 actions | Median generated tokens per action |
|---|---|---|---|---|---|---|---|
| Duck/TAAF-based whole games (Sept to 4 Oct) | 316 | not cleared | 34 | 5.3% | 3.1% | 0.66 | 705 |
| Duck/TAAF-based whole games (Sept to 4 Oct) | 510 | cleared | 21 | 0.0% | 0.0% | 0.19 | 612 |
| Franzen-based whole games (Oct) | 265 | not cleared | 39 | 1.0% | 0.0% | 0.72 | 1,267 |
| Franzen-based whole games (Oct) | 1415 | cleared | 24 | 0.0% | 0.0% | 0.30 | 617 |
| level trials (Oct) | 1359 | not cleared | 48 | 6.0% | 6.4% | 0.57 | 1,367 |
| level trials (Oct) | 471 | cleared | 31 | 0.7% | 1.6% | 0.29 | 869 |

## M4. Efficiency on cleared levels (our actions / human baseline)

| Group | Cleared levels | Median (95% CI) | IQR | At or below the human count |
|---|---|---|---|---|
| Duck/TAAF-based whole games (Sept to 4 Oct) | 510 | 0.72 (0.61–0.83) | 0.55–1.00 | 75.3% |
| Franzen-based whole games (Oct) | 1415 | 0.65 (0.58–0.79) | 0.48–0.90 | 83.7% |
| level trials (Oct) | 471 | 0.86 (0.72–1.00) | 0.56–1.31 | 62.0% |
| A3 lexicon on (r3) | 58 | 0.86 | 0.59–1.35 | 62.1% |
| A3 lexicon off (r3) | 67 | 0.86 | 0.58–1.20 | 64.2% |
| probe-first on (r1) | 69 | 0.81 | 0.56–1.21 | 65.2% |
| probe-first off (r1) | 58 | 0.82 | 0.58–1.89 | 62.1% |
| probe-first on (r2) | 65 | 0.95 | 0.55–1.49 | 50.8% |
| probe-first off (r2) | 58 | 1.14 | 0.70–1.50 | 46.6% |

## M5. Across harness generations

| Generation | Turns | Actions | Turns without an action | Median reasoning characters per turn | Unchanged-board actions | Revisits of a seen board | Game-overs per 100 actions | Mean generated tokens per action |
|---|---|---|---|---|---|---|---|---|
| Duck/TAAF-based whole games (Sept to 4 Oct) | 7,729 | 40,832 | 3.7% | 3,345 | 10.0% | 12.9% | 0.48 | 528 |
| Franzen-based whole games (Oct) | 12,214 | 58,376 | 2.1% | 5,429 | 2.1% | 3.0% | 0.39 | 785 |
| level trials (Oct) | 26,273 | 92,466 | 6.2% | 6,625 | 8.1% | 7.9% | 0.46 | 1,030 |

The generations differ in setup (time per game, number of games, harness), which is stated rather than adjusted away.

## M6. ARC-AGI-2 transfer (description only)

| Version | Run started | Minutes | Exception |
|---|---|---|---|
| v1 | 2026-10-31T11:30:59.482398+00:00 | 0.1 | none |
| v2 | 2026-11-01T12:10:45.199693+00:00 | 7.8 | none |
| v3 | 2026-11-01T12:29:30.812120+00:00 | 6.7 | none |
| v4 | 2026-11-01T12:24:40.381150+00:00 | 30.0 | none |
| v5 | 2026-11-01T12:58:41.429458+00:00 | 46.8 | none |
| v6 | 2026-11-01T13:53:05.167587+00:00 | 39.3 | none |

| Submitted (UTC) | Public score | Status | Late, not counted |
|---|---|---|---|
| 2026-10-31T12:04 | 0.0 | COMPLETE |  |
| 2026-11-01T16:13 | 10.83 | COMPLETE |  |
| 2026-11-02T23:37 | 10.69 | COMPLETE | yes |
| 2026-11-04T20:48 | 11.25 | COMPLETE | yes |

The ARC-AGI-2 save runs are install checks with a 3-task smoke test; no agent transcripts were saved, so no behavioural analysis is possible.
