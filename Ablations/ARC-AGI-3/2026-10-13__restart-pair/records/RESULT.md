# Same-day pair, restart v2 against restart off (2026-10-14): no change

**Rule:** `kaggle/restart-dfranzen/DECISION_RULE_PAIR.md`, fixed before the runs. Output of `compare_pair.py`: `compare_pair.out`.

**Verdict:**
- **Mechanism not confirmed.** The same-day rate is lower with the restart, and the pooled stratified p = 0.80.
- **Decision: no change.** The restart stays an equivalent draw, and the base configuration remains the default.

## Runs

| Arm | Kernel | Started (UTC) | Flag |
|---|---|---|---|
| Restart on | `habanwer/arcaid3-pair-restart-r1` v1 | 2026-10-14 05:41 | 100000 (restart v2) |
| Restart off | `habanwer/arcaid3-pair-flag0-r1b` v1 | 2026-10-14 10:43 | 0 |

- **Same day, not side by side.** The arms started 5 h 02 min apart. The control waited for a GPU slot and then hit a stuck-slug mount error; see `RUN_LOG.md`.
- **Setup, identical in both arms and as in every earlier run:** 25 public games at once, 7,254 s each, priority scheduling on.
- **The notebooks differ only** in the flag line and the head note.

## Health: both valid

Both arms passed every health check:
- the flag was printed as set;
- no traceback, no crashed game, no failed solver note;
- the run finished and the summary cell ran;
- the control wrote no restart event.

## Primary: same-day conversion

Attempts that used at least 100K generated tokens on a level, counted the same way in both arms, from `benchmark.json`:

| | Completed later | Rate |
|---|---|---|
| Restart on | 0 of 7 | 0% |
| Restart off | 1 of 13 | 7.7% |

One-sided Fisher p = 1.000.

## Secondary: pooled conversion, all runs in this setup

| | Completed later | Rate |
|---|---|---|
| Restart on (v1 ×2 on 10-12, v2 today) | 5 of 28 | 17.9% |
| Restart off (four 10-09 runs, today's control) | 10 of 59 | 16.9% |

- Stratified by game-level: p = 0.797, from 14 strata seen in both arms (52 attempts).
- Naive Fisher: p = 0.569 (anti-conservative).

## Coverage: the v2 fix works, but restarts come too late

v2 reached all 7 of its attempts past 100K tokens, against 10 of 21 for v1. 5 of the 7 restarts fired on a no-action resumption, which v1 could never reach.

| Game | Level | Tokens at restart | Actions on level | No-action turn | Clock left |
|---|---|---|---|---|---|
| s5i5 | 3 | 106,172 | 19 | yes | 2,171 s |
| sp80 | 2 | 110,567 | 40 | yes | 2,039 s |
| ka59 | 3 | 102,037 | 159 | no | 1,423 s |
| su15 | 4 | 102,622 | 120 | no | 1,144 s |
| tn36 | 4 | 104,283 | 66 | yes | 846 s |
| cn04 | 6 | 102,327 | 39 | yes | 551 s |
| r11l | 6 | 102,875 | 72 | yes | 64 s |

- **None of the 7 restarted levels was completed afterwards.**
- In the 10-12 transcripts, relearning took 4–18 min after a restart. Here every restart had at most 36 min left, and three had under 15.

## Same-day score (reported, not decisive)

| | Score | Levels |
|---|---|---|
| Restart on | 50.48 | 109 |
| Restart off | 47.91 | 105 |

- **Difference: +2.57**, per-game bootstrap 95% CI −6.47 to +12.81, sign-flip p = 0.63.
- A difference must exceed about ±13–17 points to reach p < 0.05. The plausible effect of the mechanism is about +1 point.
- Games that diverged a lot do not line up with restarts. vc33 (100 against 21) and ka59 (11 against 54) moved by more than the mechanism could explain:
  - in vc33 no attempt in the restart arm reached 100K tokens;
  - in ka59 the restart never completed its level.
- These are per-game draws.

## Day check

- **Today's control:** 47.91, inside the 10-09 controls' range (40.08–51.20, mean 45.66).
- **Today's restart arm:** 50.48.
- **The 10-12 restart v1 runs** (37.60 and 37.99) are the two lowest of all eight runs in this setup.
  - Today's v2 arm does not reproduce that drop, so the drop is not a property of restarting as such.
  - v1 also re-priced the restarted level in the scheduler, which v2 does not. There was no same-day control on 10-12, so a day effect and v1's re-pricing cannot be told apart.

## What it means

- **Restart v2 runs cleanly** and reaches the stuck attempts the review said v1 missed.
- **It shows no added value.**
  - Today: 0 of 7 restarted levels completed.
  - Pooled over all runs: 17.9% against 16.9% for restart off.
  - Its two LB-relevant draws are at the copy mean (v1 LB 25.76) and inside the save-run band (v2 today 50.48).
- **The mechanism acts too late.** Attempts reach 100K tokens late in a game's clock, and a fresh context needs 4–18 min before it acts again. A lower threshold would fire earlier, but the 10-10 policy model already priced that: restarting at 60K cuts slow successes.
- **The restart line is closed.** No submission follows. Per `memo-2026-10-12-lexicon-proposals.md`, any score gain has to come from the roughly 80% of level attempts that never reach 100K tokens.
