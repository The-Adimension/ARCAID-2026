# Decision rule: same-day pair, restart v2 on vs off (fixed before the runs, revised 2026-10-14 after review)

## Arms

Two kernels run side by side on the two GPU sessions, in the leaderboard-like setup of every earlier run: 25 public games at once, 7,254 s each, priority scheduling on.

| Kernel | Flag | What it is |
|---|---|---|
| `habanwer/arcaid3-pair-restart-r1` | `STUCK_RESTART_TOKENS = 100000` | Restart **v2** (`restart.patch`) |
| `habanwer/arcaid3-pair-flag0-r1` | `STUCK_RESTART_TOKENS = 0` | Restart off. The cells differ only in this flag and the head note |

**v2 differs from the submitted v1** (`restart_v1.patch`, LB 25.76) in six ways, each from the 2026-10-14 reviews (corrected 2026-10-15: this line said "seven"; the pending-note fix is the "never carries over" clause of the re-send item):
- **Fires on no-action stretches.** It also fires while the model is deliberating without acting. v1 skipped every resumed turn, so 11 of the 21 attempts past 100K were never treated: each crossed 100K after its last action.
- **No re-pricing.** The level keeps its token count, so the scheduler prices the game as with the flag off. The one scheduling difference left is a single slot handover at the restart, the same as after any context trim.
- **Fresh opener after a no-action stretch.** When the restart fires on a re-issued no-action invocation, the opener is rebuilt from the last executed step. Without this it would be the resumption restatement, which after a game over points at the diagnosis messages the restart just removed and drops the death images.
- **The note is re-sent** if the turn that carried it is rolled back, but only while the level and action count are unchanged. It never carries over to a new level.
- **A final-level win** after a restart is logged.
- **The note is worded correctly** after a game over.

**What flag 0 adds: nothing to the agent.**
- With the flag at 0, the restart code returns at its first check.
- In the end-to-end simulation (`sim_restart.py`), every request sent is byte-identical to Franzen v1's.
- Its value is as the **same-day control**: it is cell-for-cell the restart build, run on the same day.

## Health (a pair that fails any of these is invalid, not judged)

- `ARCAID3_RESTART_READY` shows tokens 100000 (restart arm) and 0 (control).
- No traceback in either log.
- 25 games played in each.
- Every game ended `won` or `gave_up`, and no solver note starts with `error:` or `analyzer failed`. A crashed game is caught by the solver without a traceback.
- `benchmark.json` has an `end_time`, and the summary cell ran: the run was not killed partway.
- The control writes no restart events.

## Statistics

**Primary: same-day conversion.** Among level attempts that used at least 100K generated tokens, the share that went on to complete the level, restart arm against control.
- Both arms are counted the same way: every such attempt, from `benchmark.json`, whether or not a restart fired.
- Test: one-sided Fisher exact.

**Secondary: pooled conversion** over every run in this setup.
- Restart on: v1 ×2 (10-12) and v2 (this pair).
- Restart off: four 10-09 runs and this control.
- Test: a permutation of arm labels **within each game-level**, because the same game-levels recur across runs. The naive Fisher test is printed too, marked anti-conservative.

**Same-day score:** the per-game paired difference (restart − off), with a bootstrap 95% CI and a sign-flip p, plus a day check of this control against the 10-09 controls.

## What this pair can and cannot answer (stated before the run)

| Question | Answerable? |
|---|---|
| **Was the 10-12 score drop (37.6 and 38.0) a day effect or the build?** | Yes, roughly. Compare this control's score with the 10-09 controls (40.1–51.2) and with the restart arm. |
| **Does v2 reach the stuck attempts v1 missed, and does anything break?** | Yes. Restarts per attempt past 100K, how many fire on a no-action resumption, and health. |
| **Does the restart raise conversion?** | Not reliably. Using the deciding test, which is stratified by game-level, the review's simulation gives P(p < 0.05) of about 1% if the restart doubles conversion to 40%, and about 2–3% at 50% (naive Fisher: about 6% and 18%). A "not confirmed" result is expected whether or not the mechanism works. |
| **Does the restart raise the score?** | **No.** A same-day difference must exceed about ±13–17 points to reach p < 0.05; about 20–24 is needed for 80% power. The plausible effect is about +0.4 to +0.8 points per run, from about one extra completed level. That is computed with the official scorer on the 14 completed past-100K levels in the six runs. A large difference either way is noise. |

**No affordable test before 11-02 can show a score jump from this change, and its plausible size is about 1 point.**

## Decision

| Result | Next |
|---|---|
| Same-day conversion higher, pooled stratified p < 0.05, and same-day score difference ≥ 0 | Restart v2 becomes the default for remaining submissions and the final selection |
| Anything else | No change. The base configuration remains the default; restart builds count as equivalent draws |

**No submission follows from this pair by itself.**
