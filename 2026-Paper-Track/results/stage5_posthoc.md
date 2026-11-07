# Stage 5: post hoc analyses

**Post hoc.** Added after the Stage 2–4 results were seen ([`../ANALYSIS-PLAN.md`](../ANALYSIS-PLAN.md) §8). These results suggest; they do not confirm, and no Stage 2–4 verdict changes because of them. Script: `analysis/stage5_posthoc.py`; all numbers: `stage5_posthoc.json`.

The six runs are the paired level-trial runs: every level of the 25 public games played from its own start, 20 minutes each, 183 levels per run.

| Label | Run | Role | Started (UTC) | Cleared |
|---|---|---|---|---|
| C1 | `arcaid3-lt-off-r3@v1` | control, lexicon design round 3 | 2026-10-10T10:11 | 67 |
| C2 | `arcaid3-lt-pf-off-r1@v1` | control, probe-first round 1 | 2026-10-24T07:13 | 58 |
| C3 | `arcaid3-lt-pf-off-r2@v1` | control, probe-first round 2 | 2026-10-24T15:46 | 58 |
| PF1 | `arcaid3-lt-pf-on-r1@v1` | probe-first on, round 1 | 2026-10-24T07:13 | 69 |
| PF2 | `arcaid3-lt-pf-on-r2@v1` | probe-first on, round 2 | 2026-10-24T15:46 | 65 |
| LEX | `arcaid3-lt-lex-r3@v1` | lexicon on, round 3 | 2026-10-10T10:11 | 58 |

## Checks

- **The controls installed no add-on:** yes. Each log's add-on lines are in the JSON (`setup.addon_log_lines`).
- **Notebook cells:** the three controls differ in 5 of 29 cells (each carries its own add-on cell, switched off); listed below.
- **The power model reproduces the real A/A disagreement:** yes (P2).
- **The scoring formula reproduces the engine scores** of all whole-game runs: largest difference 4.9e-05 points; levels cleared in order: yes. Each game's level count and human baselines come from the level-trial starts (25 games, 183 levels; consistent across trial runs: yes; whole-game rows agree: yes).
- **P6 starts from Stage 4 M1:** yes (same turns, same estimates).
- **Trial clears match the replayed actions** (a clear has a clearing action, a failure has none): yes.

| Cell | Type | C1 | C2 | C3 |
|---|---|---|---|---|
| 0 | markdown | `# ARCAID3 lexicon view on Daniel Franzen's Milestone 2 solution` | `# ARCAID3 paired level trial, round 1, arm PF=0 (probe-first governor ` | `# ARCAID3 paired level trial, round 2, arm PF=0 (probe-first governor ` |
| 20 | markdown | `## ARCAID3 lexicon view (the one added code cell)` | `## ARCAID3 probe-first governor cell (the arm flag decides whether it ` | `## ARCAID3 probe-first governor cell (the arm flag decides whether it ` |
| 21 | code | `# ARCAID3 evaluation control arm: the lexicon view is switched off, so` | `# ARCAID3 paired level trial: arm flag. The probe-first cell below rea` | `# ARCAID3 paired level trial: arm flag. The probe-first cell below rea` |
| 22 | code | `# --------------------------------------------------------------------` | `# First-run defaults (explicit for the record; the cell reads these fr` | `# First-run defaults (explicit for the record; the cell reads these fr` |
| 28 | code | `# ARCAID3 lexicon view: final counters (how often the model's Python r` | `# Probe-first governor: final counters for this run (never raises).` | `# Probe-first governor: final counters for this run (never raises).` |

## P1. The unchanged agent against itself (A/A)

| Pair | Kind | Cleared | Only first | Only second | Exact McNemar p | Cohen's κ |
|---|---|---|---|---|---|---|
| C1 vs C2 | A/A | 67 vs 58 | 17 | 8 | 0.108 | 0.70 |
| C1 vs C3 | A/A | 67 vs 58 | 19 | 10 | 0.136 | 0.65 |
| C2 vs C3 | A/A | 58 vs 58 | 13 | 13 | 1.000 | 0.67 |
| PF1 vs PF2 | A/A | 69 vs 65 | 19 | 15 | 0.608 | 0.60 |
| PF1 vs C2 | add-on vs same-day control | 69 vs 58 | 18 | 7 | 0.043 | 0.70 |
| PF2 vs C3 | add-on vs same-day control | 65 vs 58 | 19 | 12 | 0.281 | 0.62 |
| LEX vs C1 | add-on vs same-day control | 58 vs 67 | 8 | 17 | 0.108 | 0.70 |

ICC(1) of the clear outcome across the three controls: 0.67 (the share of outcome variation that belongs to the level). Levels by how many of the six runs cleared them: {0: 86, 1: 20, 2: 13, 3: 7, 4: 14, 5: 6, 6: 37}; by how many of the three controls: {0: 100, 1: 26, 2: 14, 3: 43}.

## P2. What the level-trial design can detect

Observed disagreeing levels in the three A/A pairs: [25, 29, 26]. The first, scratch model implied 50.0 per pair and was replaced.

**Model fitted to the 3 controls (primary):** beta-binomial α = 0.166, β = 0.324. Simulated A/A disagreement: mean 26.8 (5–95%: 19–34); covers the observed: yes. Simulations per power cell: 4,000.

| Effect | Power |
|---|---|
| gain 3 pts, 1 round(s) | 0.13 |
| gain 3 pts, 2 round(s) | 0.26 |
| gain 3 pts, 4 round(s) | 0.51 |
| gain 5 pts, 1 round(s) | 0.33 |
| gain 5 pts, 2 round(s) | 0.65 |
| gain 5 pts, 4 round(s) | 0.93 |
| gain 8 pts, 1 round(s) | 0.73 |
| gain 8 pts, 2 round(s) | 0.96 |
| gain 8 pts, 4 round(s) | 1.00 |
| gain 10 pts, 1 round(s) | 0.90 |
| gain 10 pts, 2 round(s) | 1.00 |
| gain 10 pts, 4 round(s) | 1.00 |
| harm 5 pts, 1 round | 0.34 |
| harm 8 pts, 1 round | 0.76 |

| If the true gain is | Power | Significant results average | Ratio |
|---|---|---|---|
| true gain 3.3 pts, 2 rounds | 0.32 | 5.5 pts | ×1.7 |
| true gain 4.9 pts, 2 rounds | 0.62 | 6.1 pts | ×1.2 |

**Model fitted to all 6 runs (sensitivity):** beta-binomial α = 0.171, β = 0.316. Simulated A/A disagreement: mean 27.2 (5–95%: 20–35); covers the observed: yes. Simulations per power cell: 2,000.

| Effect | Power |
|---|---|
| gain 3 pts, 1 round(s) | 0.13 |
| gain 3 pts, 2 round(s) | 0.26 |
| gain 3 pts, 4 round(s) | 0.49 |
| gain 5 pts, 1 round(s) | 0.32 |
| gain 5 pts, 2 round(s) | 0.64 |
| gain 5 pts, 4 round(s) | 0.93 |
| gain 8 pts, 1 round(s) | 0.70 |
| gain 8 pts, 2 round(s) | 0.96 |
| gain 8 pts, 4 round(s) | 1.00 |
| gain 10 pts, 1 round(s) | 0.90 |
| gain 10 pts, 2 round(s) | 1.00 |
| gain 10 pts, 4 round(s) | 1.00 |
| harm 5 pts, 1 round | 0.33 |
| harm 8 pts, 1 round | 0.74 |

| If the true gain is | Power | Significant results average | Ratio |
|---|---|---|---|
| true gain 3.3 pts, 2 rounds | 0.32 | 5.6 pts | ×1.7 |
| true gain 4.9 pts, 2 rounds | 0.62 | 6.1 pts | ×1.3 |

A run's levels get their clear chances from the fitted model; the add-on adds the same log-odds shift to every level, so levels no run can clear stay unclearable. Detection: exact McNemar p < 0.05 (pooled over rounds) in the direction of the effect.

## P3. Each add-on against all three controls

| Comparison | Add-on clear rate | Controls | Difference | Exact permutation p (two-sided) |
|---|---|---|---|---|
| probe-first (PF1, PF2) vs C1-C3 | 36.6% | 33.3% | +3.3 pts | 0.087 |
| lexicon (LEX) vs C1-C3 | 31.7% | 33.3% | -1.6 pts | 0.527 |

Run labels are permuted within each level; the null distribution is exact (convolution over levels). This assumes runs on different days are exchangeable, which the same-day pairing of Stage 2 does not need.

## P4. Did probe-first change what it targets?

Governor counters at the end of each run: PF1 `{'openers': 4847, 'nudged': 328, 'capped_requests': 390, 'max_streak': 16, 'errors': 0}`; PF2 `{'openers': 4728, 'nudged': 298, 'capped_requests': 337, 'max_streak': 16, 'errors': 0}`; C2 `{'openers': 0, 'nudged': 0, 'capped_requests': 0, 'max_streak': 0, 'errors': 0}`; C3 `{'openers': 0, 'nudged': 0, 'capped_requests': 0, 'max_streak': 0, 'errors': 0}`.

No-action streaks (consecutive responses after which the action count did not advance, as in `lt_analysis.py`):

| Run | Streaks | Median | 90th pct | Max | 5 or more | 10 or more | Tokens in streaks of 5+ |
|---|---|---|---|---|---|---|---|
| C1 | 1,523 | 2 | 4 | 25 | 9.3% | 1.3% | 15.1% |
| C2 | 1,542 | 2 | 4 | 15 | 8.7% | 0.8% | 13.8% |
| C3 | 1,512 | 2 | 4 | 20 | 9.1% | 1.1% | 14.0% |
| PF1 | 1,517 | 2 | 4 | 16 | 9.2% | 1.1% | 13.3% |
| PF2 | 1,503 | 2 | 4 | 16 | 7.9% | 1.0% | 11.6% |
| LEX | 1,719 | 2 | 4 | 17 | 9.8% | 1.0% | 14.5% |

| Pair | Moves per trial, median | Mean difference | Median difference | Wilcoxon p | Levels both cleared | Tokens to clear, median ratio (p) | Actions to clear, median ratio (p) |
|---|---|---|---|---|---|---|---|
| PF1 vs C2 | 59 vs 62 | -1.3 | +1 | 0.668 | 51 | 0.93 (0.285) | 0.89 (0.061) |
| PF2 vs C3 | 58 vs 63 | -4.4 | -1 | 0.184 | 46 | 1.00 (0.957) | 1.01 (0.861) |
| LEX vs C1 | 56 vs 62 | -3.7 | -3 | 0.287 | 50 | 0.83 (0.226) | 0.96 (0.313) |
| C1 vs C2 | 62 vs 62 | +2.4 | -1 | 0.953 | 50 | 0.91 (0.347) | 1.02 (0.991) |
| C1 vs C3 | 62 vs 63 | +3.6 | -1 | 0.856 | 48 | 0.96 (0.351) | 0.89 (0.174) |
| C2 vs C3 | 62 vs 63 | +1.1 | -1 | 0.629 | 45 | 1.01 (0.358) | 0.92 (0.518) |

| Run | Median tokens per trial | Total tokens | Cleared | Tokens per cleared level |
|---|---|---|---|---|
| C1 | 75,705 | 13,920,777 | 67 | 207,773 |
| C2 | 76,639 | 13,408,948 | 58 | 231,189 |
| C3 | 75,739 | 13,370,043 | 58 | 230,518 |
| PF1 | 76,191 | 13,634,184 | 69 | 197,597 |
| PF2 | 77,140 | 13,594,221 | 65 | 209,142 |
| LEX | 76,014 | 13,792,384 | 58 | 237,800 |

- PF1 / C2: total tokens ×1.02, levels cleared ×1.19.
- PF2 / C3: total tokens ×1.02, levels cleared ×1.12.
- LEX / C1: total tokens ×0.99, levels cleared ×0.87.

## P5. What limits the score?

### Score anatomy of whole-game runs (grouped by the root base in `run.json`)

| Base | Game-runs | Mean score | Ceiling from levels cleared | Lost to uncleared levels | Lost to inefficiency | Inefficiency share of the loss | Cleared levels over 5× human | Mean score with the 5× rule | Next level raises the ceiling by | Next level, largest possible gain |
|---|---|---|---|---|---|---|---|---|---|---|
| Duck/TAAF-based | 319 | 10.63 | 11.73 | 88.27 | 1.10 | 1.2% | 5 | 10.60 | 8.5 | 8.9 |
| Franzen-based | 340 | 43.80 | 45.14 | 54.86 | 1.34 | 2.4% | 0 | 43.80 | 11.6 | 12.1 |

Points out of 100 per game-run. A game's score is capped at the level-weighted share of levels cleared (the ceiling); per level the score is min((human/ours)², 1.15). The 5× rule is the action budget of the official evaluation ("the agent is terminated after 5n actions", ARC-AGI-3 report §4.3): a cleared level that took more than 5× the human count scores 0 and ends that game. The next-level columns are what clearing one more level could add to that game's score. Runs in each group are listed in the JSON.

### Difficulty: what predicts a clear for the unchanged agent (3 controls)

| Human actions for the level | Levels | Clear rate |
|---|---|---|
| (0.0, 32.5] | 46 | 65.9% |
| (32.5, 60.0] | 46 | 41.3% |
| (60.0, 117.0] | 45 | 20.0% |
| (117.0, inf] | 46 | 5.8% |

| Level depth | Levels | Clear rate |
|---|---|---|
| (0, 1] | 25 | 76.0% |
| (1, 3] | 50 | 49.3% |
| (3, 6] | 75 | 18.7% |
| (6, 10] | 33 | 10.1% |

Logistic regression on 549 trials, standard errors clustered by game (25 games): log human actions -1.28 (95% CI -1.89 to -0.67, p = 3.7e-05); depth -0.43 per level (-0.66 to -0.20, p = 2.5e-04). Per-game clear rate: {'min': 0.0, 'median': 0.27777777777777773, 'max': 0.9166666666666666, 'games_never_cleared': 2}.

### When in the trial clears happen (share of the trial's generated tokens spent at the clear)

| Run | Clears | Median point of the trial | Clears in the last quarter | Cleared by 10k tokens | by 20k | by 40k | by 80k |
|---|---|---|---|---|---|---|---|
| C1 | 67 | 0.44 | 20.9% | 4.4% | 7.7% | 23.0% | 36.6% |
| C2 | 58 | 0.51 | 22.4% | 3.8% | 10.9% | 18.0% | 31.7% |
| C3 | 58 | 0.51 | 24.1% | 3.8% | 6.6% | 17.5% | 31.7% |
| PF1 | 69 | 0.50 | 30.4% | 4.9% | 8.2% | 22.4% | 37.2% |
| PF2 | 65 | 0.57 | 27.7% | 3.3% | 8.7% | 18.6% | 35.5% |
| LEX | 58 | 0.43 | 12.1% | 3.3% | 10.4% | 21.3% | 31.7% |

| Pair | Kind | Cleared by one run only: n, median point | Cleared by both: n, median point | Mann–Whitney p |
|---|---|---|---|---|
| PF1 vs C2 | add-on vs same-day control | 25, 0.78 | 102, 0.46 | 1.0e-05 |
| PF2 vs C3 | add-on vs same-day control | 31, 0.76 | 92, 0.43 | 3.9e-08 |
| LEX vs C1 | add-on vs same-day control | 25, 0.66 | 100, 0.37 | 8.0e-06 |
| C1 vs C2 | A/A | 25, 0.66 | 100, 0.43 | 3.0e-04 |
| C1 vs C3 | A/A | 29, 0.66 | 96, 0.42 | 8.6e-05 |
| C2 vs C3 | A/A | 26, 0.71 | 90, 0.45 | 2.0e-05 |

### Failed trials: moves made against the human count and against what clears needed

Cleared trials needed a median 0.89× the human count (10th percentile 0.38×). Failed trials made a median 0.56× the human count; 71.6% made fewer moves than the human count, but only 32.0% stopped below the 10th percentile of what clears needed. Median moves: failed trials 51; cleared trials, to the clear 34.

| Human actions for the level | Failed trials | Their median moves (human median) | Moves / human, median | Below the human count | Clears | 10th pct of clears | Failed below that |
|---|---|---|---|---|---|---|---|
| (0, 32.5] | 98 | 43 (25) | 1.89 | 15.3% | 178 | 0.49 | 3.1% |
| (32.5, 60] | 162 | 38 (48) | 0.83 | 60.5% | 114 | 0.34 | 9.9% |
| (60, 117] | 206 | 54 (86) | 0.61 | 77.7% | 64 | 0.50 | 35.4% |
| (117, inf] | 257 | 64 (183) | 0.29 | 95.3% | 19 | 0.09 | 3.1% |

New board states per 100 moves on failed trials (median): C1 94.3, C2 93.4, C3 94.3, LEX 92.9, PF1 94.7, PF2 94.0.

Frontier: 97 levels cleared by at least one of the six runs, 37 by all six, 83 by at least one control. Levels no control cleared: PF1 6, PF2 9 (either: 14), LEX 4. For reference, each control clears C1 12, C2 6, C3 8 levels the other two controls never cleared.

## P6. Reading the lexicon, matched on situation

Turns in lexicon-on runs: 12,005 (as Stage 4 M1); with a read of `.code` or `.rules`: 2,868; with a lexicon cue in the prompt: 4,892.

| Position in the level (actions already taken) | Turns | Read rate |
|---|---|---|
| level start | 1,599 | 77.0% |
| 1-5 | 2,819 | 19.3% |
| 6-15 | 2,665 | 22.6% |
| 16-40 | 3,079 | 11.4% |
| >40 | 1,843 | 7.5% |

Read rate with a cue 47.3%, without 7.8%; when stuck 15.7%, otherwise 27.1% (stuck: an unchanged-board action in the last 5 actions, or a revisit in the last 10, on that level).

| Outcome | Comparison | Difference, read minus no read (95% CI) | Strata | Turns | Reads |
|---|---|---|---|---|---|
| completes a level | as Stage 4 M1: same run, game and level | -10.6 pts (-14.3 to -6.7) | 1,190 | 12,005 | 2,868 |
| completes a level | matched: also position in level and stuck status | -2.5 pts (-4.2 to -0.9) | 1,022 | 12,005 | 2,868 |
| completes a level | matched, turns without a cue (unprompted reads) | -1.1 pts (-3.5 to +1.3) | 364 | 7,113 | 555 |
| completes a level | matched, turns with a cue (prompted reads) | -3.2 pts (-5.8 to -1.1) | 405 | 4,892 | 2,313 |
| a level completes within 10 actions of the turn's start | as Stage 4 M1: same run, game and level | -9.3 pts (-14.5 to -5.6) | 1,190 | 12,005 | 2,868 |
| a level completes within 10 actions of the turn's start | matched: also position in level and stuck status | -0.6 pts (-1.4 to +0.2) | 1,022 | 12,005 | 2,868 |
| a level completes within 10 actions of the turn's start | matched, turns without a cue (unprompted reads) | +0.3 pts (-1.5 to +2.1) | 364 | 7,113 | 555 |
| a level completes within 10 actions of the turn's start | matched, turns with a cue (prompted reads) | -2.0 pts (-3.8 to +0.0) | 405 | 4,892 | 2,313 |

Stratified differences weight each stratum by n₁n₀/(n₁+n₀); intervals are 2,000 bootstrap resamples of games (seed 6).
