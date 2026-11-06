# Tools

Scripts that collect, organise, check and analyse the record. They are not part of any submission.

| Folder | What |
|---|---|
| `kaggle/` | `collect_runs.py` (every notebook version, log and output manifest), `collect_submissions.py` (submission records per track), `pull_bases.py` (third-party base notebooks), `collect_external_notebooks.py` (the 154 other teams' notebooks, 2026-10-01), and the September collectors as used then |
| `lineage/` | `notebook_diff.py` (cell-by-cell diff of two notebooks), `infer_parents.py` (nearest earlier notebook by code distance) |
| `catalogue/` | `placement.csv` (which notebook goes where; hand-written), `build_catalogue.py` (writes `Submissions/` and `Ablations/*/runs/`), `build_indexes.py` (track indexes, `LINKS.md`, `LINEAGE.md`) |
| `release/` | `release_check.py`: secrets, e-mail addresses, local paths, private links, large and binary files, competition data, private notebooks, unverified licences |
| `analysis/` | Analyses of 2026-10-05 (luck test), 2026-10-10 (Milestone 2 base), 2026-10-11 (RubiQ probes) and 2026-10-17 (trim regime), with their saved outputs |
| `corpus/` | The 2026-10-01 corpus derivations and their small row files; the per-step rows (about 94 MB) will be hosted with the run outputs |
| `replay/` | Engine replay checks: re-scoring a save run from its `benchmark.json`, verifying local-play records |
| `diagnostics/` | `arcaid3-mount-diag`: the Kaggle input read-speed diagnostic, with its runs |

How they fit together is in [`../Documentation/REPRODUCE.md`](../Documentation/REPRODUCE.md).
