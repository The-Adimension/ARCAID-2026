# Is the "operational lexicon" plan worth building before 2026-11-02? No. 2026-10-12

## Verdict

- **Don't build proposals 1–5 or 7 as score levers.** Proposal 6 (ablations) is already in place.
- **One piece survives: "reset when stuck" from proposal 4.** It is triggered by tokens, not by the lexicon. It is built, checked offline, and running on Kaggle now as a pre-registered mechanism test.
  - If the test passes, the same notebook is the submission.
  - If it fails, submit nothing from this line.

## Why: the evidence on the branches and on Kaggle

**The passive lexicon has been measured four ways. None shows a gain.** All of these are on `origin/claude/gracious-thompson-6is9pp`.

| Measure | On − off | Notes |
|---|---|---|
| Level trials, 183 paired levels, cold start | **−4.9 points** of clear rate (95% CI −10.2 to +0.4) | McNemar p = 0.11 |
| Leaderboard-like A/B, 25 games, 2 rounds | −0.03 points | rounds +7.42 and −7.49 |
| Save-run replicates v2 vs v4, 3 runs each | −0.33 points | permutation p = 0.55 |
| Public LB | 24.95 and 27.05 | unchanged Franzen copies score 21–29 |

**The model already queries the rules.** It read `.rules` 688 times in the level trials and used the view in 19% of tool calls. So "make it queryable" adds less than it seems.

**Where the score is lost** (Franzen's 4 × 25 run, `origin/claude/vibrant-keller-ksqha6:memo-2026-10-10.md` §4):
- Completed levels already use a median 0.64× the human action count. 80% use at most 1×, and 73% sit at the 1.15 cap. (Corrected 2026-10-15: this line first said "80% at the cap". Recomputed from the same benchmark.json: 417 completed levels.)
- The loss is in stuck attempts: 36% of tokens go into attempts that never finish, and 40 of 67 such attempts were on levels another pass completed.

**New today: a pre-registered offline test of the plan on exactly those stuck attempts** (`experiments/2026-10-12__lexicon-proposals-offline/`).
- **Data:** 100 runs replayed on the engine, 4,883 graded steps in stuck attempts.
- **Rule:** committed as `6ebf3049` before any run.

| Proposal | Test | Result |
|---|---|---|
| 1. `predict(action)` | Informative and right on stuck steps; bar 30% | **5.7%** (CI 2.8–9.8%); misleading 69.7%. Lenient grading: 49% right, but 26% on rarely tried actions, where an answer would be news. |
| 1. `unexplained_recent()` | Fires on ≤ 50% of stuck steps | **90.3%**: a constant alarm |
| 4. Loop-based stuck detector | AUC ≥ 0.70 for "never finishes" at 40K tokens | **0.49**: chance |
| 2, 3. Grammar, tracking | Pay off only through test 1 | On the same level, the rules predict stuck and completed attempts equally well (51% vs 49%, 29 levels). ft09's rules predict 97% of its stuck steps exactly, and it is still stuck. |

The failure is in finding the goal, not in modelling the mechanics. A better mechanics model does not reach it.

**The rest of the list:**
- **5. Token efficiency:** tokens are near saturation, at +0.26 demo points per +10% tokens.
- **7. Object-id clicks, probe actions, auto-verification:** these save actions on levels the agent already completes efficiently. That is worth 0–2 points at most.

## What was built instead: stuck-level restart (`kaggle/restart-dfranzen/`)

- **The change:** an 84-line patch on Franzen M2 v1's `tool_agent.py`. Once one level's conversation has used 100,000 generated tokens without completing, its messages are cleared once. The board, system prompt and retained functions stay, and the scheduler re-prices the level as a fresh attempt.
  - Flag `STUCK_RESTART_TOKENS = 0` gives Franzen v1's behaviour.
  - No lexicon, no added advice text.
- **Why tokens and not the lexicon:** test C above. Tokens already select well on their own: 91% of attempts still open at 100K never finish.
- **Submission safety:** the competition branch asserts concurrency 120, 532 min and the 10-stream gate. A mis-set flag now fails loudly instead of scoring 7.16 (the 2026-10-11 `arcaid3-lt-lex-r3` submission).
- **Checks:**
  - 15/15 hook checks (`test_restart.py`);
  - 15/15 notebook checks (`verify_notebook.py`): Franzen's 23 cells are unchanged except anchored lines in cells 4 and 16, and both patches apply as cell 4 applies them;
  - the patched harness compiles and imports.
- **Running now:** `habanwer/arcaid3-restart-dfranzen-m2` and `-r2`, private, pushed 2026-10-12 03:16 UTC, in the same leaderboard-like setup as the earlier controls. About 2 h 40 min each.
- **Pre-registered rule** (`kaggle/restart-dfranzen/DECISION_RULE.md`):

  | Outcome | Condition |
  |---|---|
  | Pass | At least 40% of fired restarts go on to complete their level, and restarts fire on at most 15% of attempts |
  | Fail | Below 25% |
  | Inconclusive | In between |

  - The control in this setup converts 9 of 46 attempts past 100K tokens (19.6%).
  - Read the result with `python kaggle/restart-dfranzen/compare_restart.py --fetch`.
- **Known counter-evidence:** rellik13 reports that a fresh-context restart "bought nothing" (few runs, different base). That is why the run comes before any submission.

## Calendar

| When | What |
|---|---|
| 10-12, about 06:00 UTC | Runs finish. Apply the rule. If pass, submit `arcaid3-restart-dfranzen-m2` v1. |
| Until 10-31 | Daily slots: the flag-on notebook if it passed, otherwise Franzen v1 (or the 27.05 lexicon notebook, equivalent within noise). Never the 7.16 one. |
| 10-26 | Entry and merger deadline. |
| 11-02 | Select two healthy draws of the best-evidence configuration (memo-2026-10-10 §7). |

## If you still want a lexicon experiment

The only version the data leaves open is one the model never reads: the lexicon used inside the harness to save LLM calls (scripted probes, `click(sym)` macros). Its ceiling is the 0–2 points that efficiency is worth on completed levels. I would not spend a GPU day on it before the restart result is in.

## Outcome of the restart test (2026-10-12, 06:15 UTC)

Details: `experiments/2026-10-12__restart-dfranzen/RESULT.md`.

- **Health:** both runs valid. Flag active, no tracebacks, 25 games each.
- **Conversion:** 4 of 10 restarts went on to complete their level (40.0%), against 19.6% for the control (9 of 46). Restarts fired on 4.3% of level attempts. **PASS by the pre-registered rule.**
- **The pass is weak:**
  - Only 10 restarts fired, against the ~22 the rule assumed. They fire late in the game clock (median about 6,100 of 7,254 s).
  - At n = 10, a restart that does nothing would clear 40% with probability 0.11. Fisher's exact p against the control is 0.16.
- **Score was lower:** 37.60 and 37.99, the two lowest of six runs (controls 40.08–51.20; 1/15 = 0.067 if the arms were exchangeable).
  - The loss is spread evenly: −4.05 points from the 8 restarted games and −3.81 from the 17 that never restarted.
  - The 17 games that never restarted play like Franzen v1, so the restart is not the obvious cause. ft09, never restarted, fell from 100 to 47.6 and 28.6.
  - The controls ran three days earlier. There is no same-day control.
- **Submitted** per the rule: `arcaid3-restart-dfranzen-m2` v1, 2026-10-12 06:13 UTC (scriptVersionId 357524957), pending. The API reports 0 submissions left today.
- **Before it becomes a final-selection default:** run one same-day pair in this setup, restart against `STUCK_RESTART_TOKENS = 0`. Until then the 27.05 notebook and Franzen v1 remain the best-evidence draws.

## Hidden-set draw of the restart build (read 2026-10-12 17:16 UTC)

- **Public LB 25.76**, against unchanged Franzen copies at mean 25.77 (SD 3.93): no detectable effect in one draw.
- The build ran cleanly in the competition rerun.
- **Standings for final selection, as of today:**
  - It is a healthy draw of the base configuration, equivalent to the 27.05 and 24.95 lexicon draws.
  - It is not evidence that the restart helps. Only the same-day paired save run (restart against `STUCK_RESTART_TOKENS = 0`) can say that.

## Correction (2026-10-13)

**The restart's "PASS" was an artifact of the decision rule.** The rule compared restarts that fired with all control attempts past 100K tokens. Counted the same way in both arms:
- restart on: 5 of 21 (23.8%);
- restart off: 9 of 46 (19.6%);
- one-sided p = 0.46.

**So there is no evidence the restart adds value.** That agrees with its LB draw of 25.76, at the copy mean.

A same-day pair (restart on vs flag 0) with the corrected statistic is the next measure (`kaggle/restart-dfranzen/DECISION_RULE_PAIR.md`).

## Outcome of the same-day pair (2026-10-14)

Details: `experiments/2026-10-13__restart-pair/RESULT.md`. Restart v2 against restart off, same day, both arms healthy.

- **Conversion of attempts past 100K tokens:** 0 of 7 with the restart, 1 of 13 without (p = 1.0). Pooled over every run: 17.9% against 16.9% (stratified p = 0.80).
- **Score:** 50.48 against 47.91. The difference of +2.6 has a 95% CI of −6.5 to +12.8, so it is noise.
- **Decision rule:** "no change".
- **v2 works mechanically:** it reached all 7 stuck attempts, 5 of them during no-action deliberation.
- **But every restart came with 64–2,171 s left on the clock, and none led to a completion.**
- **Day check:** the control (47.91) sits inside the 10-09 range. The 10-12 drop (37.6 and 38.0) belongs to that day or to v1's re-pricing, not to restarting as such.

**The restart line is closed.** No evidence was found, on any measure, that it adds value. The base configuration (Franzen v1, or the 27.05 lexicon notebook) remains the default for submissions and the final selection.

## Franzen M2 v3 (checked 2026-10-14)

Details: `experiments/2026-10-14__franzen-v3-check/NOTE.md`.

- **v3 differs from v1 only in its header note and its Save & Run settings:** 4 passes on all 25 demo games, with leaderboard-scaled time.
- **The competition path is byte-identical to v1:** harness patch, environment, serving, run cell and the `TRUE_SUBMISSION` branch. So v3 offers nothing to port into the 27.05 lexicon build.
- **His public LB is nonetheless 35.86 (rank 28) since 2026-10-13, up from 27.89.** That is about a 1.5% chance from the public code over 3 draws, so it most likely comes from an unpublished version.
- **Watch for a public v4.**

## Resubmission of the lexicon build (2026-10-14 14:02 UTC, scored by 2026-10-15 01:04 UTC)

- **The draw:** `arcaid3-lexicon-view-dfranzen-m2` v4, the same notebook that scored 27.05, scored **31.90**. Public rank 186 of 4,310 (it was 1,068).
- **Draws of this exact notebook:** 27.05 and 31.90, mean 29.5. The earlier 24.95 came from that notebook's v1, a different lexicon version.
- **Against unchanged Franzen copies** (mean 25.77, SD 3.93): z = 1.56. That is a good draw, inside the band best-of-k draws reach. One draw changes nothing about the configuration's mean, which no measure so far separates from Franzen v1.
- **Final selection, as of today:** the two healthy draws of this notebook, **31.90 (2026-10-14) and 27.05 (2026-10-08)**. Both are the best-evidence configuration and both ran cleanly. The 31.90 draw is the higher public one, but private scores come from different games, so its edge there is small.
- **Do not select** the 7.16 run (misconfigured). The 25.76 restart run is healthy but no better.

