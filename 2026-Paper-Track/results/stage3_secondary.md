# Stage 3: secondary analyses (descriptive)

Specified in [`../ANALYSIS-PLAN.md`](../ANALYSIS-PLAN.md) §3. Scores are RHAE on the public games, re-derived by the engine replay (`data/replay.csv`). Script: `analysis/stage3_secondary.py`; all numbers: `stage3_secondary.json`.

## S1. Run-to-run noise of identical code

| Arm (setup) | Run | Mean score | Levels | Game-bootstrap 95% CI |
|---|---|---|---|---|
| A1 lexicon v2 (10 games x 25 min) | `arcaid3-lexicon-view-dfranzen-m2@v2` | 42.61 | 43 | 24.9–63.3 |
| A1 lexicon v2 (10 games x 25 min) | `arcaid3-rep-v2-r1@v1` | 47.46 | 45 | 29.9–67.4 |
| A1 lexicon v2 (10 games x 25 min) | `arcaid3-rep-v2-r2@v1` | 54.37 | 51 | 36.8–72.8 |
| | **between runs** | **48.15** (SD 5.91, range 42.61–54.37) | | |
| A1 lexicon v4, the selected code (10 games x 25 min) | `arcaid3-lexicon-view-dfranzen-m2@v4` | 55.36 | 50 | 37.1–75.6 |
| A1 lexicon v4, the selected code (10 games x 25 min) | `arcaid3-rep-v4-r1@v1` | 43.70 | 44 | 28.3–61.2 |
| A1 lexicon v4, the selected code (10 games x 25 min) | `arcaid3-rep-v4-r2@v1` | 44.38 | 45 | 31.1–59.4 |
| | **between runs** | **47.81** (SD 6.54, range 43.70–55.36) | | |
| A2 lexicon v5 on (25 games x 121 min) | `arcaid3-lb-lex-r1@v1` | 51.20 | 112 | 35.7–66.5 |
| A2 lexicon v5 on (25 games x 121 min) | `arcaid3-lb-lex-r2@v1` | 40.08 | 95 | 24.2–56.7 |
| | **between runs** | **45.64** (SD 7.86, range 40.08–51.20) | | |
| A2 lexicon off (25 games x 121 min) | `arcaid3-lb-off-r1@v1` | 43.77 | 101 | 29.9–58.3 |
| A2 lexicon off (25 games x 121 min) | `arcaid3-lb-off-r2@v1` | 47.57 | 107 | 32.5–63.0 |
| | **between runs** | **45.67** (SD 2.68, range 43.77–47.57) | | |

## S2. Recorded whole-game tests, recomputed on replayed scores

| Test | Recomputed | Recorded in October | Agree |
|---|---|---|---|
| A1: v4 − v2, mean of 3 runs each | -0.33 points, one-sided permutation p = 0.55 | −0.33, p = 0.55 | yes |
| A1: levels v4 − v2 | +0.0, p = 0.60 | +0.0, p = 0.60 | yes |
| A2: on − off per round | +7.42, -7.49 | +7.42, −7.49 | yes |
| A2: primary (mean over rounds), sign-flip p | -0.03, p = 0.995 | −0.03, p = 0.995 | yes |
| A2: outcome under its own rule | no measurable effect | no measurable effect | yes |

The restart tests (`Ablations/ARC-AGI-3/2026-10-12__restart-v1`, `2026-10-13__restart-pair`) are defined on restart events (`stuck_restarts.jsonl`), not on replayable outcomes; they are not recomputed here and remain as recorded.

## S3. Leaderboard draws of the Franzen-based notebooks

Reference: unchanged copies of Franzen's notebook scored 25.77 ± 3.93 (third party: Son Pham, Kaggle discussion 745062). Excluded: 0.00 scores (slow model loads, 21-25 October; Kaggle discussion 751598) and 7.16 (a level-trial build submitted with trial settings).

| Notebook | Public score | Selected | Distance from the copies' mean, in their SD |
|---|---|---|---|
| `arcaid3-lexicon-view-dfranzen-m2` | 31.90 | yes | +1.56 |
| `arcaid3-probe-first-dfranzen-m2-sg` | 30.57 | yes | +1.22 |
| `arcaid3-lexicon-view-dfranzen-m2` | 27.79 |  | +0.51 |
| `arcaid3-lexicon-dprime-dfranzen-m2-sg` | 27.47 |  | +0.43 |
| `arcaid3-lexicon-view-dfranzen-m2` | 27.05 |  | +0.33 |
| `arcaid3-lexicon-view-dfranzen-m2` | 26.83 |  | +0.27 |
| `arcaid3-pair-flag0-r1b` | 26.22 |  | +0.11 |
| `arcaid3-restart-dfranzen-m2` | 25.76 |  | -0.00 |
| `arcaid3-lexicon-dprime-dfranzen-m2-sg` | 25.26 |  | -0.13 |
| `arcaid3-lexicon-view-dfranzen-m2` | 24.95 |  | -0.21 |
| `arcaid3-pair-restart-r1` | 24.42 |  | -0.34 |
| `arcaid3-lexicon-view-dfranzen-m2` | 24.35 |  | -0.36 |
| `arcaid3-probe-first-dfranzen-m2-sg` | 23.41 |  | -0.60 |
| `arcaid3-lexicon-dprime-dfranzen-m2-sg` | 22.23 |  | -0.90 |
| `arcaid3-lexicon-dprime-dfranzen-m2` | 21.18 |  | -1.17 |

Our 15 draws: mean 25.96, SD 2.85. Each public score is one run on half of the hidden games; hidden-set runs cannot be replayed, so this comparison is descriptive only.
