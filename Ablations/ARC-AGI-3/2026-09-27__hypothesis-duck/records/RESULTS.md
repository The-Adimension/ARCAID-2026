# Duck-transcript hypothesis test: results

**Question:** can a model trained on other games tell which of our own agent's hypotheses it will later abandon, better than simple progress counters? Rules were pre-registered in `RUNLOG.md` before any data was built.

**Data:** 190 unique Duck transcripts. At the pre-set threshold (Jaccard 0.5) they give 584 hypotheses, 440 wrong and 144 right, over 16 games.
- **Right** means the hypothesis was current when the level was cleared.
- **Wrong** means the agent replaced it with a substantially different one.
- Six games supply 90% of rows: lp85, sb26, re86, ft09, vc33, ar25.

## Pooled held-out AUC (leave-one-game-out)

| Model | J 0.3 (473 rows) | **J 0.5 (584, pre-set)** | J 0.7 (614) |
|---|---|---|---|
| Hedge words | 0.471 | 0.510 | 0.517 |
| Counters (turn/actions on level, level, hypothesis index) | **0.683** | **0.677** | 0.676 |
| Run configuration | 0.535 | 0.549 | 0.556 |
| All baselines | 0.657 | 0.660 | **0.681** |
| Text only | 0.580 | 0.555 | 0.548 |
| Text + all baselines | 0.646 | 0.650 | 0.667 |

## Pre-set rule: text vs the strongest baseline (chosen automatically)

| Threshold | Text only | Text + baselines | Rule |
|---|---|---|---|
| 0.3 | −0.101 [−0.188, −0.001] | −0.020 [−0.120, +0.160] | **not met** |
| **0.5** | **−0.123 [−0.220, −0.027]** | **−0.013 [−0.103, +0.132]** | **not met** |
| 0.7 | −0.145 [−0.313, +0.000] | −0.012 [−0.035, +0.010] | **not met** |

## Reading

1. **The wording of the agent's hypothesis doesn't reveal whether it will be abandoned.** Text alone is significantly worse than simple counters at 0.5 and 0.3 (CI entirely below 0), and adds nothing when combined with them. This holds at all three thresholds.
2. **When the hypothesis appears carries the signal, not what it says.** The counters reach about 0.68. A hypothesis formed late in a level, after many turns and actions, is more likely to be the one held when the level clears. That is partly built into the label: the right hypothesis is by definition the last one on a level.
3. **Hedge words carry no signal (AUC ≈ 0.5).** The agent's wording of uncertainty says nothing about outcome. Unlike the public ledgers, where stated confidence was the best signal (AUC 0.72), our agent states no calibrated confidence.
4. **This matches both earlier findings.** The public-ledger test also found no ranking gain from text. Earlier on this corpus, text predicting "level cleared" vanished once run configuration was controlled.

## Limits

- **The labels are behavioural, not verdicts.** A replaced hypothesis may be a refinement rather than an error; the threshold sensitivity bounds this but doesn't remove it.
- **Only 144 "right" examples.** Many levels have no carried world model, including levels cleared quickly.
- **Games:** 6 public games dominate, and the hidden set is different games.
- **One model type:** TF-IDF with logistic regression.

## Files

- **Here:** `RUNLOG.md`, `results_j{0.3,0.5,0.7}.json`, `predictions_j{0.3,0.5,0.7}.csv`
- **Code:** `inputs/hypotheses/build_duck_dataset.py`, `duck_logo_test.py`
- **Data:** `inputs/hypotheses/data/duck_hypotheses_j*.jsonl`
