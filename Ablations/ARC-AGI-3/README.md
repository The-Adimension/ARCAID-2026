# ARC-AGI-3 ablations and controlled tests

One folder per test, by start date. Each has a `README.md` (question, design, decision rule, recorded outcome), the decision rule where one was written, the analysis scripts with their saved outputs, the write-ups of the time (`records/`), and the Kaggle runs (`runs/`).

[`PREREGISTRATION.csv`](PREREGISTRATION.csv) lists, from the git history of the working repository, when each decision rule and each first result was committed. That is the evidence for "written before the runs".

| Test | Kind | Decision rule committed before the result |
|---|---|---|
| [`2026-09-18__ab-tricks`](2026-09-18__ab-tricks/) | Kaggle runs | no |
| [`2026-09-27__change-a-world-model-reasoning`](2026-09-27__change-a-world-model-reasoning/) | leaderboard pairs (notebooks in Submissions) | no |
| [`2026-09-27__hypothesis-confidence`](2026-09-27__hypothesis-confidence/) | offline | yes |
| [`2026-09-27__hypothesis-duck`](2026-09-27__hypothesis-duck/) | offline | yes |
| [`2026-09-27__surprise-walls`](2026-09-27__surprise-walls/) | offline | no |
| [`2026-09-27__system1-replay`](2026-09-27__system1-replay/) | offline | no |
| [`2026-10-04__lexicon-view-read-or-not`](2026-10-04__lexicon-view-read-or-not/) | Kaggle runs | no |
| [`2026-10-05__lexicon-save-runs-v1-v4`](2026-10-05__lexicon-save-runs-v1-v4/) | Kaggle runs (notebooks in Submissions) | no |
| [`2026-10-09__A1-replicates-v2-vs-v4`](2026-10-09__A1-replicates-v2-vs-v4/) | Kaggle runs | test fixed in code; no separate rule |
| [`2026-10-09__A2-lexicon-on-vs-off`](2026-10-09__A2-lexicon-on-vs-off/) | Kaggle runs | yes, before round 2 (after round 1) |
| [`2026-10-09__A3-level-trials-lexicon`](2026-10-09__A3-level-trials-lexicon/) | Kaggle runs | yes, before round 1; revised between rounds |
| [`2026-10-12__operational-lexicon-offline`](2026-10-12__operational-lexicon-offline/) | offline | yes |
| [`2026-10-12__restart-v1`](2026-10-12__restart-v1/) | Kaggle runs | yes |
| [`2026-10-13__restart-pair`](2026-10-13__restart-pair/) | Kaggle runs | yes |
| [`2026-10-24__level-trials-probe-first`](2026-10-24__level-trials-probe-first/) | Kaggle runs | yes |
