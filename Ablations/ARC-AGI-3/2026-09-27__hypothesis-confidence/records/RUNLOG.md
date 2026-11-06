# Hypothesis test: run log

**Question.** Given a stated hypothesis about how a game level works (a goal, a mechanic, or a win condition), can a model trained on other games predict whether it will turn out wrong, better than the stated confidence of the model that wrote it?

**Protocol.**
- Leave-one-game-out: every score comes from a game that was never seen in training.
- Every step appends a line below and is committed on its own.

## Log
- `2026-09-27 07:49:56 UTC` **step 1**: created run log and folders (inputs/hypotheses for code, experiments/hypothesis-test for results)
- `2026-09-27 07:50:12 UTC` **step 2**: found 81 ARA Labs arc-agi3 dataset repos
- `2026-09-27 07:50:41 UTC` **step 2**: downloaded 2648 ledger rows from 57 of 81 repos, each pinned to its commit sha (ledger_manifest.json)
- `2026-09-27 07:50:51 UTC` **step 2**: added CC-BY attribution (data/ATTRIBUTION.md); committing fetch script, raw ledger and manifest
- `2026-09-27 07:51:00 UTC` **step 2 fix**: removed an accidentally committed __pycache__/runlog.cpython-312.pyc from commit 74dbbce; __pycache__ now git-ignored
- `2026-09-27 07:51:39 UTC` **step 3**: read 2648 raw ledger rows
- `2026-09-27 07:51:39 UTC` **step 3**: joined 1185 prediction/verdict pairs; dropped: verdict with no matching prediction 17; ambiguous (several predictions/verdicts share an id) 28; verdict without consult_id 48; predictions never given a verdict 115
- `2026-09-27 07:51:39 UTC` **step 3**: verdict classes: wrong 619, right 431, partial/unresolved 131, other 3, mixed 1
- `2026-09-27 07:51:39 UTC` **step 3**: wrote 1027 labelled hypotheses after removing 23 duplicate texts; wrong-rate 0.59; games 11 (ls20:302, g50t:228, s5i5:165, su15:162, r11l:83, ar25:30, tr87:21, lf52:15, ft09:13, ka59:5, wa30:3); setups 8; confidence missing on 12 rows
- `2026-09-27 07:51:55 UTC` **step 3**: read 2648 raw ledger rows
- `2026-09-27 07:51:55 UTC` **step 3**: joined 1185 prediction/verdict pairs; dropped: verdict with no matching prediction 17; ambiguous (several predictions/verdicts share an id) 28; verdict without consult_id 48; predictions never given a verdict 115
- `2026-09-27 07:51:55 UTC` **step 3**: verdict classes: wrong 619, right 431, partial/unresolved 131, other 3, mixed 1
- `2026-09-27 07:51:55 UTC` **step 3**: wrote 1027 labelled hypotheses after removing 23 duplicate texts; wrong-rate 0.59; games 11 (ls20:302, g50t:228, s5i5:165, su15:162, r11l:83, ar25:30, tr87:21, lf52:15, ft09:13, ka59:5, wa30:3); setups 7; confidence missing on 12 rows
- `2026-09-27 07:51:55 UTC` **step 3**: fixed setup label for *-agent-trajectories repos (model not stated) -> 'unknown-agent'; committing dataset
- `2026-09-27 07:52:24 UTC` **step 4**: teacher decisions (0393 rounds, 206) NOT added: replay gives one action list per round, not per-decision outcomes, and the only objective per-decision label ('did its actions clear the level', 16/206 positive) measures plan success, not hypothesis correctness. Main test uses the 1,027 public hypotheses only.
- `2026-09-27 07:52:52 UTC` **step 5**: loaded 1027 rows, 11 games, wrong-rate 0.586; starting 11 folds
- `2026-09-27 07:53:00 UTC` **step 5**: pooled held-out AUC: B1_confidence 0.720, B2_conf+setup 0.655, T1_text 0.623, T2_text+conf+setup 0.701, B0_chance 0.500
- `2026-09-27 07:53:00 UTC` **step 5**: AUC(text+conf+setup) - AUC(conf+setup) = +0.048, 95% CI [+0.014, +0.103] -> pre-set pass rule MET
- `2026-09-27 07:53:19 UTC` **step 5 correction**: the first run compared text against B2 (confidence+setup, AUC 0.655), but the pre-set rule named the STRONGEST baseline, which is B1 (stated confidence alone, AUC 0.720). The earlier 'MET' is withdrawn; re-running with the comparison against B1.
- `2026-09-27 07:53:20 UTC` **step 5**: loaded 1027 rows, 11 games, wrong-rate 0.586; starting 11 folds
- `2026-09-27 07:53:40 UTC` **step 5**: pooled held-out AUC: B1_confidence 0.720, B2_conf+setup 0.655, T1_text 0.623, T2_text+conf+setup 0.701, B0_chance 0.500
- `2026-09-27 07:53:40 UTC` **step 5**: (secondary) AUC(text+conf+setup) - AUC(conf+setup) = +0.048, 95% CI [+0.014, +0.103]
- `2026-09-27 07:53:40 UTC` **step 5**: PRE-SET RULE vs strongest baseline (stated confidence): AUC(T1_text) - AUC(confidence) = -0.081, 95% CI [-0.312, +0.175] -> NOT met
- `2026-09-27 07:53:40 UTC` **step 5**: PRE-SET RULE vs strongest baseline (stated confidence): AUC(T2_text+conf+setup) - AUC(confidence) = -0.002, 95% CI [-0.060, +0.090] -> NOT met
- `2026-09-27 07:54:11 UTC` **step 6**: wrote RESULTS.md: pre-set rule NOT met; stated confidence (AUC 0.720) is the strongest signal; text adds calibration (Brier 0.212) but not ranking; game-level heterogeneity documented
