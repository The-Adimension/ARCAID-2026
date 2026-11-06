# The two selected ARC-AGI-3 submissions

These are the two submissions selected for final (private) scoring. Everything below was read from the code and logs, not from descriptions:
- the exact notebook versions, pulled from Kaggle by `scriptVersionId`;
- their Save & Run logs;
- their output files;
- a cell-by-cell diff against the base notebook (`Tools/lineage/notebook_diff.py`).

| | **Lexicon view v4** | **Probe-first + startup guard v1** |
|---|---|---|
| **Kaggle notebook** | [`arcaid3-lexicon-view-dfranzen-m2`, Version 4](https://www.kaggle.com/code/habanwer/arcaid3-lexicon-view-dfranzen-m2?scriptVersionId=356505353) | [`arcaid3-probe-first-dfranzen-m2-sg`, Version 1](https://www.kaggle.com/code/habanwer/arcaid3-probe-first-dfranzen-m2-sg?scriptVersionId=362275314) |
| **Folder here** | [`Submissions/ARC-AGI-3/2026-10-05__arcaid3-lexicon-view-dfranzen-m2/v4__…__SELECTED`](../Submissions/ARC-AGI-3/2026-10-05__arcaid3-lexicon-view-dfranzen-m2/) | [`Submissions/ARC-AGI-3/2026-10-25__arcaid3-probe-first-dfranzen-m2-sg/v1__…__SELECTED`](../Submissions/ARC-AGI-3/2026-10-25__arcaid3-probe-first-dfranzen-m2-sg/) |
| **Selected draw** | Submission 57184726, 2026-10-14: **31.90** | Submission 57904036, 2026-11-02: **30.57** |
| **All draws of this exact code** | 27.05 (10-08), 31.90 (10-14), 26.83 (10-15); mean 28.59 | 23.41 (10-26), 30.57 (11-02); mean 26.99 |
| **Base** | Daniel Franzen, *ARC-AGI-3 Milestone 2 Solution*, Version 1 (scriptVersionId 354090904; public LB 27.89). Built on Tufa Labs' Duck harness. | The same base. The direct parent is our `arcaid3-probe-first-dfranzen-m2` Version 2, which is the base plus probe-first. |
| **Unchanged from the base** | All 23 base cells, byte-identical and in order | 22 of 23 base cells, byte-identical and in order |
| **Model and serving** | Qwen3.8-Flash-Next W4A16 (AutoRound) with a speculative drafter, SGLang, 128K context, priority scheduler. All from the base. | Identical |
| **What we added** | **1 code cell, 2,018 lines**, standard library only. Plus 1 counter cell and 2 markdown cells. | **2 code cells**: probe-first (251 lines) and startup guard (223 lines). **1 changed line** in the base's *Run the benchmark* cell: the gateway wait goes from 600 s to 1,800 s. Plus 2 counter cells and 2 markdown cells. |
| **What the added code does** | **Datafies perception.** It adds to the agent's Python sandbox:<br>• `current_frame.code`: true cell size, a legend of objects with stable names, their placements<br>• `.objects`<br>• `.native`<br>• `.changes_since(prev)`<br>• `.rules`: induced "when ⟨action⟩ [if ⟨relation⟩] then ⟨change⟩" rules, with hit and miss counts<br>It also:<br>• edits 4 prompt anchors and adds a first-turn cue and a `.rules` cue;<br>• locks the scale per level, and cuts merged objects back apart;<br>• tests itself through the real sandbox and rolls back on failure. | **Probe-first datafies the agent's own economics.** It keeps a per-level ledger of actions spent and of consecutive turns that executed no action.<br>• From the 3rd such turn, it adds a paragraph on the scoring economics.<br>• From the 5th, it caps replies at 4,096 tokens.<br>• It never issues or blocks an action.<br>**The startup guard is infrastructure.** Each game waits for the model server's `/health`, and one game sends a RESET every 7 min so the scorecard stays open, up to a 2 h limit. |
| **Kill switches** | `ARCAID3_LEXICON`, `ARCAID3_SCALE_LOCK`, `ARCAID3_RULES` | `PF`, `SG` |
| **Save run** (10 public games, 25 min each, one run) | **55.36 mean, 50 of 72 levels.**<br>• Self-tests passed; every prompt edit applied.<br>• View read in **98 of 576** tool calls; 0 errors. | **30.92 mean, 34 of 72 levels.**<br>• `ARC3_PF_FINAL`: 267 turn openers; nudged 9; capped 8 requests; 0 errors.<br>• `ARC3_SG_FINAL`: 10 games held; server healthy after 1,202 s; longest hold 475 s; 2 keep-alive RESETs; 0 errors. |
| **Base's own save run** (same settings) | 36.56 mean, 40 of 72 levels | Same |
| **Caveat on the save run** | One draw. Over three repeats each, v4 averaged 47.81 and v2 48.15 (A1 below). | **Not comparable with the base.** The startup hold does not stop each game's 25-minute clock, so games lost up to 475 s of play. The governor also rarely fired. |
| **Controlled tests (ablations)** | **A1 repeats**, v2 vs v4, 3 runs each: −0.33 points, permutation p = 0.55.<br>**A2 on vs off**, 25 games at the leaderboard's time per game, two rounds: +7.42, then −7.49; mean −0.03. Rule fixed before round 2: no measurable effect.<br>**A3 level trials**, 183 levels, each a paired cold-start trial: on cleared 58, off 67; on-only 8, off-only 17; exact McNemar p = 0.108. Rule fixed before round 1: no detectable difference.<br>**Offline replay** of Franzen's own runs: on stuck attempts, the rules predicted the next step informatively and correctly 5.7% of the time. | **Paired level trials, probe-first on vs off**, 2 rounds × 183 levels:<br>• Round 1: +19.0%, p = 0.043.<br>• Round 2: +12.1%, p = 0.281.<br>• **Pooled: off 116, on 134, +15.5%, exact McNemar p = 0.022.**<br>• Agent/human actions on cleared levels: 0.88 (on) vs 0.94 (off).<br>Pre-registered gates: 4 passed. The "no-action token share ≤ 45%" gate **failed** (51% in both arms), so the rule's verdict was **"DO NOT submit"**.<br>**Startup guard:** no outcome ablation. The same code without it scored 0.00 during Kaggle's slow-load incident (21–25 October). |
| **Reference noise** | Copies of the base score 25.77 ± 3.93 (Son Pham, discussion 745062). 31.90 is +1.56 SD. | 30.57 is +1.22 SD |
| **Key actionable difference** | Changes **what the model sees**: a structured description of the board it may read through Python | Changes **what the model spends**: a ledger of its own actions and action-free turns, fed back as a nudge and a token cap. Plus a startup guard against slow model loads. |

## Evidence

| Claim | Where |
|---|---|
| Cell diffs | In each version folder: `DIFF.md` (against its inferred parent) and `vs-root-base/DIFF.md` (against Franzen M2 v1), written by `Tools/lineage/notebook_diff.py` |
| Save-run numbers and counters | `log.txt` in each version folder (lines `mean score`, `ARCAID3_LEXICON_FINAL`, `ARC3_PF_FINAL`, `ARC3_SG_FINAL`) |
| A1, A2, A3 | `Ablations/ARC-AGI-3/2026-10-09__A1-replicates-v2-vs-v4/`, `2026-10-09__A2-lexicon-on-vs-off/`, `2026-10-09__A3-level-trials-lexicon/` |
| Probe-first paired trials | `Ablations/ARC-AGI-3/2026-10-24__level-trials-probe-first/` |
| Offline replay | `Ablations/ARC-AGI-3/2026-10-12__operational-lexicon-offline/` |
| Draw scores | `Submissions/ARC-AGI-3/submissions.csv` |
