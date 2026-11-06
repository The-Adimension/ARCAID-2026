# `submissions/` and `experiments/`: audit and added value (2026-09-27)

**Scope:** two independent read-only audits of every directory and file.
- `submissions/`: 86 directories, 680 files, 401 MB.
- `experiments/`: 958 files, 714 MB.

No file failed to open. Pickles were inspected with pickletools or class stand-ins, so none of their code ran.

**Key claims re-verified here:**
- Every Flash-Next run log prints `TRUE_SUBMISSION=False`.
- dead-sign v2 ran 2 passes at 7,920 s per game with concurrency 28.
- Counting runs with empty histories, the corpus has 195 unique action signatures.

## 1. What the folders contain

- **Only save runs.** Every output folder comes from the interactive Save & Run on **public** games. The starter-agent save runs play no games at all. **No output of the scored hidden-set rerun exists anywhere;** Kaggle returns only the score.
- **Placeholder parquets.** All 27 `submission.parquet` files are the same one-row placeholder.
- **Same data types as the collection.** The per-run data (transcripts, events with 64×64 boards, benchmark histories, serving logs) matches what `arc3-collections/1345` holds.
- **Solver-analysis HTML copies the transcripts:** 83 of 83 in `submissions/` and 108 of 108 in `experiments/`.
- **Media only re-render the logs.**
  - The MP4s decode to the logged boards: 53 of 53 frames exact in `submissions/`, and 99.998% of cells in `experiments/`.
  - The thumbnails decode to within 98% of cells or better.
  - The charts plot `benchmark.json`.
  - No image holds a board missing from the JSON logs.

## 2. Content that exists only in these folders

| Content | Where |
|---|---|
| **18 submitted notebooks, each paired with its public leaderboard score.** This is the only hidden-set evidence in the repo. | `submissions/*/__notebook__.ipynb`, `submission.json` |
| The notebook code of 09-20 (reset v3) and 09-23 to 09-26, plus 9 experiment notebooks | not duplicated anywhere |
| Save-run outputs of 09-23, 09-24, 09-25 and 09-26 (19 game runs), and of dead-sign v2, v4 and v4A (24 runs, 7,658 actions) | not duplicated anywhere |
| Kernel logs of every version, including the two failed setups (kvfp8, dead-sign v5) | `__output__.json` |

Everything else, the 09-16 to 09-22 run outputs and the ab, depth, stall and reset v1/v2 experiments, is byte-identical to `arc3-collections/1345`.

## 3. What these outputs let you answer, and what they don't

| Question | Answerable? | Evidence and limits |
|---|---|---|
| Which code change moved the hidden score? | **Weakly** | One leaderboard draw per version, with no replicates. Only two steps change a single thing: starter v7→v8 (0.13→0.07, reverted to 0.13) and reset v3→v4 (3.37→2.84). The spread of 8 Flash-Next draws (SD 0.35) is an upper bound on the noise, and neither step is clearly outside it. |
| Does the offline public-game score predict the leaderboard? | **Yes: it doesn't** | 6-game probes: Pearson r = −0.32, Spearman −0.40 (n = 5). The two 25-game runs go the opposite way too: 0.89 vs 0.79 offline against 2.49 vs 3.04 on the leaderboard. |
| How noisy is one save run? | **Yes, measured** | Identical config, repeated passes: dead-sign v2 pass means 23.73 vs 15.64 (lp85 64.4 vs 14.6); reset v2 22.80 vs 43.94. Probe differences under about 20 points are noise. |
| How was the time budget spent on the hidden run? | **No** | No rerun logs. Only the save-run timing and the code settings (7,920 or 7,750 s per game, concurrency 28) are known. |
| Setup and serving overhead | **Yes** | Setup grew from 456 s (09-18) to 1,295 s (09-26). CUDA allocator failures appear during MoE autotune in every Flash-Next run, and the teardown error in 7 of 9 runs; neither was fatal. Serving settings were identical in all Flash-Next runs. |
| Where was GPU time wasted? | **Yes** | About 30 min of runs produced no game data (import errors, a duplicate-game-id crash, fp8 KV refused, one run on T4 instead of RTX). About 3.4 h of play lost `score.json` to a coverage check, though `benchmark.json` survived. |
| Is there more decision-turn data? | **Yes, modestly** | 43 runs exist only here, and they are already included in `inputs/jev/extract_turns.py`. |

## 4. Record-keeping errors found

- **dead-sign v2's markdown is wrong.** It says 1 pass, 3,600 s and concurrency 6; the code ran 2 passes, 7,920 s and 28. Its probe score of 19.68 isn't comparable to the other probes.
- **ab-tricks v3** says 3 passes per arm; the code gives 2.
- **Unreproducible or stale numbers in older notebook text and docs:**
  - the reset v2 figures "23.33 vs 28.81" (the raw data gives 19.83 vs 28.30);
  - the ab-tricks v1 figures "29.37 vs 28.81";
  - `PLAN-v5` and `EVAL-v4A` cite a `presubmissions/` folder that no longer exists (renamed to `experiments/`).
- **Folder names hide content.** "error-coverage-check" folders contain full play data (reset v2 has the highest mean, 33.37). "dead-sign v5" and "notebook7c0bf2022d" are the same notebook.
- **`submissions/` bookkeeping.** `submissions.csv` has 2 rows and `index.csv` has 18. `ANALYSIS-2026-09-26.md` says 2 submissions are present; there are 18. Starter v5 lives in `experiments/`.
- **Misleading log lines.** Logs print `PUBLIC25_AUDIT runs=25` from a hard-coded string. 09-22 and 09-23 print `cap_s=3600` but ran with a 1,200 s budget.
- **My own replay counts.** `SYSTEM1-REPLAY` reports 186 unique runs, because it drops the 38 runs with empty histories. Counting them gives 195 signatures.
- **MP4 decoding accuracy depends on the method.** Luminance-weighted matching gives 96.9% of frames exact; plain nearest-colour gives 93.4%.
