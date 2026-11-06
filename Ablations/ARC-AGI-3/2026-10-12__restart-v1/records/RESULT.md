# Stuck-level restart, mechanism test (2026-10-12): PASS by the pre-registered rule, with weak power

**Runs:** `habanwer/arcaid3-restart-dfranzen-m2` and `-r2`, version 1, byte-identical cells.
- Franzen M2 v1 plus `kaggle/restart-dfranzen/restart.patch`, threshold 100,000 tokens.
- Leaderboard-like setup: 25 public games at once, 7,254 s each, priority scheduling on.
- Pushed 03:16 UTC; both COMPLETE by 06:11 UTC.
- Rule: `kaggle/restart-dfranzen/DECISION_RULE.md`, committed before the runs.

## Health: both valid

| | r1 | r2 |
|---|---|---|
| `ARCAID3_RESTART_READY` with tokens 100000 | yes | yes |
| Tracebacks | 0 | 0 |
| Games played | 25 | 25 |

## Restarts

| Run | Game | Level | Tokens at restart | Actions on level | Game clock at restart (of 7,254 s) | Completed later | Tokens after restart |
|---|---|---|---|---|---|---|---|
| r1 | cd82 | 4 | 110,011 | 17 | 5,539 s | **yes** | 88,612 |
| r1 | tn36 | 2 | 100,322 | 87 | 6,006 s | **yes** | 35,805 |
| r1 | bp35 | 2 | 114,796 | 23 | 6,111 s | no | |
| r1 | su15 | 4 | 118,200 | 13 | 6,114 s | no | |
| r1 | m0r0 | 3 | 104,648 | 35 | 6,429 s | no | |
| r2 | sp80 | 2 | 100,066 | 48 | 4,829 s | no | |
| r2 | tn36 | 2 | 100,223 | 98 | 5,975 s | **yes** | 41,438 |
| r2 | m0r0 | 1 | 102,513 | 123 | 6,299 s | **yes** | 34,834 |
| r2 | vc33 | 4 | 106,487 | 46 | 6,309 s | no | |
| r2 | cn04 | 2 | 116,676 | 49 | 7,028 s | no | |

## Decision

| | Restart | Control (4 earlier runs, same setup) |
|---|---|---|
| Completed after reaching 100K | **4 of 10 (40.0%)** | 9 of 46 (19.6%) |
| Restarts per level attempt | 10 of 231 (4.3%) | |

**Rule:** conversion ≥ 40% and fire rate ≤ 15% → **PASS**.

## Caveats (reported, not decisive under the rule)

**Power was lower than planned.**
- The rule assumed about 22 restarts. Only 10 fired, against the 23 attempts that reached 100K in the two lb-off control runs. That is because restarts fire on the turn after the threshold, and late in the game clock: a median of about 6,100 of 7,254 s.
- At n = 10, a restart that does nothing (true rate 19.6%) reaches 4 of 10 with probability 0.11. Fisher's exact test against the control is p = 0.16 (one-sided).
- This is a pass by the letter of the rule, not strong evidence.

**Score was below every earlier control.**

| | Score | Levels |
|---|---|---|
| Restart, r1 | 37.60 | 94 |
| Restart, r2 | 37.99 | 95 |
| Control (lb-off r1/r2, lb-lex r1/r2) | 43.77 / 47.57 / 51.20 / 40.08 | 101 / 107 / 112 / 95 |

- The two restart runs are the two lowest of six. If the arms were exchangeable, that happens with probability 1/15 = 0.067.
- **The loss is not where the restart acts.** Per-game differences against the four controls' mean, summed and divided by 25:
  - the 8 games with a restart: −4.05 points;
  - the 17 games without one: −3.81 points.
- In a game that never reaches 100K tokens on a level, the patched code returns at its first check, so it plays like Franzen v1. Its only exposure is the scheduler re-pricing the few restarted games.
- **The largest single loss is ft09** (100 in all four controls; 47.6 and 28.6 here), which never restarted. It ran out its 7,254 s clock with 110–121K tokens, against 69–90K tokens and 3–4.4K s in the controls. ft09 swung between 22 and 100 in earlier save runs (independent review, 2026-10-09).
- **Restarted games will always look worse than the controls whatever the restart does,** because restarts fire only in games that are going badly.
- **Generated tokens per run match the controls** (4.29–4.30M against 4.28–4.47M), so throughput did not drop.
- **The controls ran on 2026-10-09; these on 2026-10-12.** There is no same-day control.

## What follows

- **Per the rule:** submit `arcaid3-restart-dfranzen-m2` version 1. Its competition branch was exercised offline: it sets concurrency 120, 532 min and 10 streams, and a mis-set flag raises.
- **Before making it the default for the final selection:** run one same-day pair, restart against flag 0, in this setup. The second arm is the same notebook with `STUCK_RESTART_TOKENS = 0`. A same-day pair answers both the score question and the power shortfall.

## Reproduce

```
python kaggle/restart-dfranzen/compare_restart.py           # reads the files here; --fetch downloads them again
```
Output: `compare_restart.out`.

## Hidden-set draw (public LB, scored 2026-10-12, read 17:16 UTC)

- **The draw:** `arcaid3-restart-dfranzen-m2` v1 (scriptVersionId 357524957), submitted 06:13 UTC, complete, **public LB 25.76**.
- **Against unchanged Franzen copies** (first-day copies: mean 25.77, SD 3.93; single draws range 21.01–27.89): z = 0.00. It sits at the copy mean.
- **Earlier draws on the same base:** the lexicon notebook drew 24.95 and 27.05.
- **What this shows:**
  - The restart build runs cleanly in the competition rerun. The asserts held and it scored a normal value, not a 7.16-type failure.
  - Its effect is not visible in one draw. A +2 point true gain would sit at z ≈ 0.5, inside the band.
- **One draw cannot settle the effect;** the same-day paired run is still the next measure. Until it is in, this configuration counts as one more healthy draw of the base, not as evidence for the restart.

## Correction (2026-10-13): the PASS came from the rule, not the restart

**The flaw.** The rule compared the conversion of restarts that **fired** (4 of 10) with the conversion of **all** control attempts that passed 100K tokens (9 of 46). The two groups are selected differently:
- A restart fires only at the start of a fresh turn, so the game must still have clock left.
- The control's 46 include attempts that crossed 100K in the last minutes of their game and could not have finished either way.

So the comparison favoured the restart.

**Counted the same way in both arms** (every level attempt that used ≥100K generated tokens, from `benchmark.json`):

| | Completed later | Rate |
|---|---|---|
| Restart on, 10-12 r1 | 2 of 10 | |
| Restart on, 10-12 r2 | 3 of 11 | |
| **Restart on, total** | **5 of 21** | **23.8%** |
| Restart off, 10-09 controls | 9 of 46 | 19.6% |

- One-sided Fisher p = 0.46. **No evidence the restart adds value.**
- 11 of the 21 attempts crossed 100K without a restart firing. In every one of them the last action came before 100K: the model crossed the threshold while deliberating without acting, and restart v1 skipped those resumed turns. 10 of the 11 ran to the end of the 7,254 s clock. r11l L2 completed at 108K tokens without a restart, so 4 of the 5 completions in the restart arm followed a restart.
- The 10-12 submission (LB 25.76, the copy mean) agrees.

**The fix.** The same-day pair (`kaggle/restart-dfranzen/DECISION_RULE_PAIR.md`, `compare_pair.py`) uses this same accounting for both arms.
