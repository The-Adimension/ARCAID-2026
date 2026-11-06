# Franzen M2 v3: does it change anything the lexicon 27.05 build could use? No (2026-10-14)

**Source:** `dfranzen/arc-agi-3-milestone-2-solution`, current version 3, pulled through the Kaggle API on 2026-10-14 and saved here as `dfranzen-m2-v3.ipynb`. It is compared with v1 (`external_submission/2026-09-30__dfranzen__arc-agi-3-milestone-2-solution__v1__teambest-27.89/__notebook__.ipynb`, sha256 `7b76c194…`). Our lexicon notebook, LB 27.05, is v1 plus the lexicon cell.

## What changed from v1 to v3

Same 23 cells in the same order. Only two differ:

| Cell | Change | Affects the competition run? |
|---|---|---|
| 0 (markdown) | Adds a note: "This version reruns the open-sourced submission (v1) with 4 passes on all 25 demo games, using a runtime budget scaled to match the time available per game in the competition … The notebook is otherwise identical." | No |
| 16 (customisation) | Save run only: `bm.n_passes = 4`, no games excluded, `max_runtime_s_per_game = 532*60 * concurrency // 110` | No. The `if TRUE_SUBMISSION:` branch is unchanged: 1 pass, concurrency 120, 532 min |

**Byte-identical to v1:**
- the harness patch (cell 2);
- the environment and flags (cell 4);
- the SGLang serving cell (cell 12);
- the benchmark run (cell 20).

**Inputs are also unchanged:**
- same datasets (`pennyroyal-v253`, last updated 2026-09-29; `taaf-kaggle-source-bundle-copy`, 2026-09-28) and the same model versions (both `/1`);
- same pinned image (`sha256:57e612b4…`);
- Franzen has no other new public notebook.

**v3's save run is the 4 × 25 run from 2026-10-03 we already used.** It underlies `memo-2026-10-10.md` §4 on `origin/claude/vibrant-keller-ksqha6` and the restart analyses. Its settings match our leaderboard-like evaluation, except for 4 passes instead of 1.

**Conclusion: there is nothing in v3 to port into the lexicon build.** A notebook built on v3 plays the hidden games exactly as one built on v1.

## Franzen's leaderboard entry moved anyway

Public LB CSV, 2026-10-14 14:00 UTC:

| Team | Score | Submissions | Last submission | Rank |
|---|---|---|---|---|
| Daniel Franzen | **35.86** | 94 | 2026-10-13 12:52 | 28 |
| Shehab Anwer | 27.05 | 26 | 2026-10-12 06:13 | 1,068 |

- **His change since 10-10:** 27.89 and 91 submissions then; 3 new submissions since.
- **How likely is that from the public code?** Unchanged copies of his code draw a mean of 25.77 with an SD of 3.93 (first-day copies, discussion 745062). 35.86 is z = 2.57, so P ≈ 0.5% for one draw and about 1.5% for the best of 3.
- **Most likely he is submitting an unpublished version.** A lucky draw of v1/v3 is possible but unlikely. The kernel list shows only his public notebook, so the code behind 35.86 is not visible.

**Board context:** #10 = 40.09, #50 = 33.68, #100 = 32.99, #200 = 31.66, #500 = 29.94, of 4,283 teams. Top: Tufa Labs 68.91, Yi-Chia Chen 67.49.

## What to do

1. **Do not rebuild the lexicon notebook on v3:** it would be the same submission.
2. **Watch Franzen's public notebook for a version 4.** If he publishes the code behind 35.86, port the lexicon cell onto it the way `kaggle/lexicon-dfranzen/build.py` ported it onto v1. Then check that the lexicon still installs, and run the same-day on/off pair before any submission.
3. **Until then, the final-selection plan is unchanged:** two healthy draws of the best-evidence configuration (27.05 lexicon, or Franzen v1).
