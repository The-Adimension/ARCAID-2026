# Stage 2: confirmatory tests

Specified in [`../ANALYSIS-PLAN.md`](../ANALYSIS-PLAN.md) §2, committed before this analysis was run. Outcomes are from the engine replay (`data/levels.csv.gz`). Script: `analysis/stage2_confirmatory.py`. All numbers: `stage2_confirmatory.json`.

## Primary results

| | Design | Paired levels | Cleared: on / off | On only / off only | Clear-rate difference (95% CI) | Conditional OR (95% CI) | Exact p | Holm p | Same sign every round | Verdict by the plan's rule |
|---|---|---|---|---|---|---|---|---|---|---|
| **H1** | Lexicon on vs off, A3 round 3 | 183 | 58 / 67 | 8 / 17 | -4.9 pts (-10.3 to +0.5) | 0.47 (0.18–1.15) | 0.108 | 0.108 | yes | **not detected at this size** |
| **H2** | Probe-first on vs off, rounds 1+2 | 366 | 134 / 116 | 37 / 19 | +4.9 pts (+0.9 to +8.9) | 1.95 (1.09–3.58) | 0.022 | 0.044 | yes | **supported** |

Per round:

| | Round | Paired | Clear on | Clear off | On only / off only | Difference (95% CI) | Exact p |
|---|---|---|---|---|---|---|---|
| H1 | `arcaid3-lt-lex-r3` vs `arcaid3-lt-off-r3` | 183 | 31.7% | 36.6% | 8 / 17 | -4.9 pts (-10.3 to +0.5) | 0.108 |
| H2 | `arcaid3-lt-pf-on-r1` vs `arcaid3-lt-pf-off-r1` | 183 | 37.7% | 31.7% | 18 / 7 | +6.0 pts (+0.6 to +11.4) | 0.043 |
| H2 | `arcaid3-lt-pf-on-r2` vs `arcaid3-lt-pf-off-r2` | 183 | 35.5% | 31.7% | 19 / 12 | +3.8 pts (-2.2 to +9.8) | 0.281 |

**Rule** (plan §2): supported only if the Holm-adjusted p < 0.05 and the sign is the same in every round run; otherwise *not detected at this size*, with the interval — not "no effect".

## Sensitivity analyses (pre-set; reported whatever they show)

**1. H1 including the two rounds that failed their validity checks** (labelled as such):

| Round | Paired | On only / off only | Difference | Exact p |
|---|---|---|---|---|
| `arcaid3-lt-lex-r1` | 183 | 3 / 6 | -1.6 pts | 0.508 |
| `arcaid3-lt-lex-r2` | 183 | 4 / 19 | -8.2 pts | 0.003 |
| `arcaid3-lt-lex-r3` | 183 | 8 / 17 | -4.9 pts | 0.108 |
| pooled, stratified | 549 | 15 / 42 | -4.9 pts (-7.7 to -2.2) | 0.000 |

**2. By level depth:**

| | Depth | Paired | On only / off only | Difference (95% CI) | Exact p |
|---|---|---|---|---|---|
| H1 | level 1 | 25 | 3 / 2 | +4.0 pts (-15.4 to +23.5) | 1.000 |
| H1 | levels 2-3 | 50 | 3 / 6 | -6.0 pts (-17.7 to +6.0) | 0.508 |
| H1 | levels 4+ | 108 | 2 / 9 | -6.5 pts (-13.2 to -0.2) | 0.065 |
| H2 | level 1 | 50 | 8 / 1 | +14.0 pts (+2.1 to +26.0) | 0.039 |
| H2 | levels 2-3 | 100 | 7 / 8 | -1.0 pts (-8.7 to +6.7) | 1.000 |
| H2 | levels 4+ | 216 | 22 / 10 | +5.6 pts (+0.4 to +10.8) | 0.050 |

**3. Leave one game out** (25 games):

| | Difference range | Exact p range | Games whose removal moves p across 0.05 |
|---|---|---|---|
| H1 | -6.2 to -3.4 pts | 0.035 to 0.286 | m0r0-492f87ba |
| H2 | +4.0 to +6.0 pts | 0.005 to 0.070 | dc22-fdcac232, re86-8af5384d, s5i5-18d95033, wa30-ee6fef47 |

**4. Logistic models** (robustness of the primary test):

| | Conditional logit by level pair: OR (95% CI), p | Mixed logit with game and pair effects (variational Bayes): OR (95% interval) |
|---|---|---|
| H1 | 0.47 (0.20–1.09), p = 0.079 | 0.58 (0.36–0.94) |
| H2 | 1.95 (1.12–3.39), p = 0.018 | 1.66 (1.19–2.32) |

The mixed model is fitted by variational Bayes (statsmodels `BinomialBayesMixedGLM`); its interval is the approximate posterior mean ± 1.96 SD of the log odds ratio.
