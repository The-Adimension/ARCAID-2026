# Duck-transcript hypothesis test: run log

This is the same question as `../hypothesis-test/`, asked of our own Duck transcripts: can a model trained on other games tell which of the agent's hypotheses will turn out wrong?

## Pre-set rules (committed before any result)

- **Hypothesis:** the `World model:` line, plus `Goal model:` when present, in the world model carried at each turn. Consecutive turns count as one hypothesis until the text changes substantially: word-set overlap (Jaccard) with the current hypothesis falls below **0.5**.
- **right (0):** the hypothesis current when the level was cleared.
- **wrong (1):** a hypothesis the agent itself replaced with a substantially different one, on any level.
- **Excluded:** the final hypothesis on a level never cleared (censored by the time limit).
- **Input text:** the hypothesis text only, with digits removed.
- **Baselines (no stated confidence exists):**
  - H, hedge-word count;
  - C, counters: turns and actions on the level before the hypothesis, level number, and index of the hypothesis within the level;
  - S, run configuration (source folder);
  - the combinations of these.
- **Protocol:** leave-one-game-out, with pooled held-out AUC and Brier score. The **pass rule** compares text + baselines against the **strongest** baseline: the 95% bootstrap CI (2,000 reps, games then rows) must have its lower bound above 0.
- **Sensitivity:** the Jaccard threshold is also run at 0.3 and 0.7.
- **Deduplication:** transcripts are deduplicated by (game, first 30 executed-action strings).

## Log
- `2026-09-27 07:55:38 UTC` **duck step 1**: pre-registered rules in experiments/hypothesis-test-duck/RUNLOG.md (before any data built)
- `2026-09-27 07:56:10 UTC` **duck step 2**: threshold 0.5: scanning 339 transcript files
- `2026-09-27 07:56:14 UTC` **duck step 2**: threshold 0.5: unique transcripts 190; excluded: final hypothesis on uncleared level 96; duplicate transcript 149; wrote 584 labelled hypotheses (wrong 440, right 144) over 16 games: lp85:162, sb26:134, re86:75, ft09:62, vc33:53, ar25:42, m0r0:17, cn04:11, su15:7, tu93:6, s5i5:6, sc25:3, dc22:2, lf52:2, sk48:1, wa30:1
- `2026-09-27 07:56:14 UTC` **duck step 2**: threshold 0.3: scanning 339 transcript files
- `2026-09-27 07:56:19 UTC` **duck step 2**: threshold 0.3: unique transcripts 190; excluded: final hypothesis on uncleared level 96; duplicate transcript 149; wrote 473 labelled hypotheses (wrong 329, right 144) over 15 games: lp85:125, sb26:124, re86:64, ft09:54, vc33:37, ar25:33, cn04:9, m0r0:8, tu93:6, s5i5:5, su15:3, dc22:2, lf52:1, sk48:1, wa30:1
- `2026-09-27 07:56:19 UTC` **duck step 2**: threshold 0.7: scanning 339 transcript files
- `2026-09-27 07:56:24 UTC` **duck step 2**: threshold 0.7: unique transcripts 190; excluded: final hypothesis on uncleared level 96; duplicate transcript 149; wrote 614 labelled hypotheses (wrong 470, right 144) over 16 games: lp85:165, sb26:140, re86:78, ft09:68, vc33:54, ar25:50, m0r0:17, cn04:13, su15:7, s5i5:7, tu93:6, sc25:3, dc22:2, lf52:2, sk48:1, wa30:1
- `2026-09-27 07:56:37 UTC` **duck step 2**: note: only 144 of 316 cleared levels yield a labelled 'right' hypothesis (no carried world model on many turns); field n_hyps_level is post-hoc and is NOT used as a feature; the heartbeat print was skipped for duplicate transcripts (cosmetic, counts unaffected)
- `2026-09-27 07:57:05 UTC` **duck step 3**: threshold 0.5: 584 rows, 16 games, wrong-rate 0.753; running 16 folds
- `2026-09-27 07:57:17 UTC` **duck step 3**: threshold 0.5: pooled held-out AUC: H_hedges 0.510, C_counters 0.677, S_config 0.549, HCS_all 0.660, T_text 0.555, T+HCS 0.650, chance 0.500; strongest baseline = C_counters
- `2026-09-27 07:57:17 UTC` **duck step 3**: threshold 0.5: PRE-SET RULE AUC(T_text) - AUC(C_counters) = -0.123, 95% CI [-0.220, -0.027] -> NOT met
- `2026-09-27 07:57:17 UTC` **duck step 3**: threshold 0.5: PRE-SET RULE AUC(T+HCS) - AUC(C_counters) = -0.013, 95% CI [-0.103, +0.132] -> NOT met
- `2026-09-27 07:57:25 UTC` **duck step 3**: threshold 0.3: 473 rows, 15 games, wrong-rate 0.696; running 15 folds
- `2026-09-27 07:57:36 UTC` **duck step 3**: threshold 0.3: pooled held-out AUC: H_hedges 0.471, C_counters 0.683, S_config 0.535, HCS_all 0.657, T_text 0.580, T+HCS 0.646, chance 0.500; strongest baseline = C_counters
- `2026-09-27 07:57:36 UTC` **duck step 3**: threshold 0.3: PRE-SET RULE AUC(T_text) - AUC(C_counters) = -0.101, 95% CI [-0.188, -0.001] -> NOT met
- `2026-09-27 07:57:36 UTC` **duck step 3**: threshold 0.3: PRE-SET RULE AUC(T+HCS) - AUC(C_counters) = -0.020, 95% CI [-0.120, +0.160] -> NOT met
- `2026-09-27 07:57:37 UTC` **duck step 3**: threshold 0.7: 614 rows, 16 games, wrong-rate 0.765; running 16 folds
- `2026-09-27 07:57:50 UTC` **duck step 3**: threshold 0.7: pooled held-out AUC: H_hedges 0.517, C_counters 0.676, S_config 0.556, HCS_all 0.681, T_text 0.548, T+HCS 0.667, chance 0.500; strongest baseline = HCS_all
- `2026-09-27 07:57:50 UTC` **duck step 3**: threshold 0.7: PRE-SET RULE AUC(T_text) - AUC(HCS_all) = -0.145, 95% CI [-0.313, +0.000] -> NOT met
- `2026-09-27 07:57:50 UTC` **duck step 3**: threshold 0.7: PRE-SET RULE AUC(T+HCS) - AUC(HCS_all) = -0.012, 95% CI [-0.035, +0.010] -> NOT met
- `2026-09-27 07:58:13 UTC` **duck step 4**: wrote RESULTS.md: pre-set rule NOT met at any threshold; text alone significantly worse than counters; hedges uninformative
- `2026-09-27 07:58:23 UTC` **housekeeping**: a cache cleanup (find inputs -name __pycache__) briefly deleted 105 committed .pyc files of inputs/arc3-collections from the working tree; restored with git checkout before any commit
