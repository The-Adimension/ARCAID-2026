# Decision rule: stuck-level restart (fixed before any run, 2026-10-12)

## What is tested

- **The change:** `restart.patch` on Franzen M2 v1. A level whose conversation has used 100,000 generated tokens without completing gets its messages cleared once. The board, system prompt and retained functions stay, and the scheduler re-prices the level as a fresh attempt.
- **Where it comes from:** the one surviving piece of proposal 4 ("suggest a deliberate reset when stuck"). It is triggered on tokens, because the lexicon's loop score could not tell stuck attempts from slow ones (`experiments/2026-10-12__lexicon-proposals-offline/RESULT.md`, test C, AUC 0.49).

## Runs

- **Two kernels, byte-identical except their names:** `habanwer/arcaid3-restart-dfranzen-m2` and `-r2`, run side by side on the two GPU sessions.
- **Setup:** the leaderboard-like one of the 2026-10-09 lexicon A/B. All 25 public games run at once, each with the leaderboard's GPU share (7,254 s), with priority scheduling on.

## Control (already measured, same setup, Franzen code; the lexicon had no measurable effect)

| Run | Attempts reaching 100K tokens on a level | Of those, completed later |
|---|---|---|
| arcaid3-lb-off-r1 | 10 | 2 |
| arcaid3-lb-off-r2 | 13 | 3 |
| arcaid3-lb-lex-r1 | 10 | 2 |
| arcaid3-lb-lex-r2 | 13 | 2 |
| **Pooled** | **46** | **9 (19.6%)** |

Franzen's own 4 × 25 run (different budget): 3 of 35 (8.6%).

## Rule (pooled over the two runs)

**Primary: conversion.** The share of fired restarts whose level is completed later in the same game.
- Read from `levels_completed` in `benchmark.json` against the restart log's level. This also catches a win on the game's last level, which logs no level transition.

| Outcome | Condition |
|---|---|
| **Pass** | Conversion ≥ 40%, and restarts fire on ≤ 15% of level attempts |
| **Fail** | Conversion < 25%, or restarts fire on > 15% of level attempts |
| **Inconclusive** | Anything between: one more pair of runs, same rule |

- **Why 40%:** with about 22 restarts, a true rate equal to the control's 19.6% reaches 9 of 22 about 1.8% of the time. A true rate of 50% reaches it about 86% of the time.
- **Health** (a run that fails any of these is invalid, not judged):
  - `ARCAID3_RESTART_READY` printed with tokens = 100000;
  - no traceback;
  - all 25 games played.

**Reported, not decisive:**
- the 25-game score and levels against the controls (43.77 and 47.57 for lb-off; run-level SD about 6);
- tokens after restart;
- prefix-cache reuse.

## What follows

| Result | Next |
|---|---|
| **Pass** | Submit the flag-on notebook (its competition branch asserts concurrency 120, 532 min and the 10-stream gate). Final selection per `origin/claude/vibrant-keller-ksqha6:memo-2026-10-10.md` §7. |
| **Fail** | Submit nothing from this line. The base for remaining slots is Franzen v1 (or the 27.05 lexicon notebook, equivalent within noise). |
