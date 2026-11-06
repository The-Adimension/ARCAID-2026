# Hypothesis test: results

**Question:** given a hypothesis an agent wrote about a game level, can a model trained on *other* games predict that it will turn out wrong better than the stated confidence of the agent that wrote it?

**Data:** 1,027 hypotheses, each with the author's stated confidence and a later verdict. They come from public ARA Labs ledgers (CC-BY-4.0, pinned to commits).
- 7 authoring setups and 11 public games; 58.6% of hypotheses were wrong.
- Four games dominate: ls20 302, g50t 228, s5i5 165, su15 162.
- Build rules and every dropped row are in `RUNLOG.md`.

**Protocol:** leave-one-game-out, with pooled held-out predictions (`predictions.csv`). Pre-set rule: the text model must beat the **strongest** baseline, with the lower bound of the 95% bootstrap CI above 0.

## Pooled held-out results

| Model | AUC | Brier |
|---|---|---|
| Chance | 0.500 | 0.243 |
| **Stated confidence alone** (strongest baseline) | **0.720** | n/a (rank only) |
| Confidence + authoring setup (logistic) | 0.655 | 0.221 |
| Hypothesis text only (TF-IDF + logistic) | 0.623 | 0.242 |
| Text + confidence + setup | 0.701 | **0.212** |

| Comparison with stated confidence | ΔAUC | 95% CI | Pre-set rule |
|---|---|---|---|
| Text only | −0.081 | [−0.312, +0.175] | **not met** |
| Text + confidence + setup | −0.002 | [−0.060, +0.090] | **not met** |

**Correction, visible in the git history:** the first run tested against the *second*-strongest baseline (confidence + setup) and printed "MET". That comparison was not the pre-set one and is withdrawn. Both numbers are in `results.json`.

## Per-game AUC (games with both outcomes)

| Game | n | Confidence | Text only | Text + conf + setup |
|---|---|---|---|---|
| ls20 | 302 | **0.924** | 0.757 | 0.904 |
| g50t | 228 | 0.543 | **0.663** | 0.589 |
| s5i5 | 165 | 0.362 | **0.827** | 0.601 |
| su15 | 162 | **0.704** | 0.467 | 0.698 |
| r11l | 83 | 0.756 | 0.755 | **0.851** |
| ar25 | 30 | 0.444 | **0.642** | 0.617 |
| tr87 | 21 | **0.861** | 0.413 | 0.769 |
| lf52 | 15 | 0.375 | 0.278 | 0.250 |

(ft09, ka59 and wa30 have 13 rows or fewer, or only one outcome, so they are pooled only.)

## Reading

1. **Stated confidence is the best single signal** (AUC 0.72). It is also the cheapest to get, since the author already writes it down.
2. **Text doesn't reliably add to it.** Pooled, the combination ties with confidence alone. The 95% intervals are wide because the result depends on 4 games.
3. **Text and confidence fail on different games.** On s5i5, text reaches 0.83 where confidence is *inverted* (0.36); on g50t and ar25, text also beats confidence. On ls20, su15 and tr87 it is the reverse. A per-game switch between them can't be chosen in advance on this data.
4. **Combining gives the best-calibrated probabilities** (Brier 0.212, the lowest), but not better ranking.

## Limits

- The data covers **11 public games**, and 84% of rows come from 4 of them. The hidden set is different games.
- The hypotheses were written by frontier models. Whether the Flash-Next model's hypotheses follow the same patterns is untested.
- **The verdicts were written by the same agents that made the predictions.** The label rules are in `build_dataset.py`, and 131 partial or unresolved verdicts were excluded.
- Only a TF-IDF and logistic-regression model was tested. A stronger text model might do better, but would need more games to evaluate fairly.

## Files

- `inputs/hypotheses/`: `fetch_ledgers.py`, `build_dataset.py`, `logo_test.py`, `runlog.py`
- `inputs/hypotheses/data/`: raw ledger, manifest, dataset and attribution
- This folder: `RUNLOG.md`, `results.json`, `predictions.csv`
