# Level trials, lexicon on against off (2026-10-09/10)

## Round 1: invalid (scheduler), kept for the record

**Nominal result:** 183 paired trials. Lexicon on cleared 34 of 183 levels and off cleared 37 (McNemar p = 0.51). This does not measure the agent.

**Trials that never played.** In each arm, 74 of the 158 later-level trials took no action at all.
- They ran out their 60-minute clock waiting for a model stream.
- The notebook's priority gate (`ARC3_MAX_ACTIVE_STREAMS=10`, switched on by `USE_PRIORITY_SCHEDULING`) lets 10 games hold a stream at a time. It frees a slot only when a game's context is first trimmed.

**Level-0 trials stalled too.** They acted for about 15–20 minutes, lost their slot, and never got it back. The second wave began only after about 2 hours.

**What still holds:** level 0 was cleared by 23 of 25 trials in both arms. That matches whole-game play.

**What it shows about the leaderboard regime.** The same gate runs on the leaderboard: 110 games, 10 streams at a time. So how the gate staggers games is a real scheduling lever. This is the review's priority 3.

Round 2 runs without the gate (`level_trials.py`; see the amendment in `DECISION_RULE.md`).

**Data:** `arcaid3-lt-{lex,off}-r1/`, and `compare_level_trials.out` from `python3 kaggle/lexicon-dfranzen/compare_level_trials.py 1`.

## Round 2: invalid (the model server was overloaded), kept for the record

**Lexicon arm (`arcaid3-lt-lex-r2`):** the benchmark ran only 39 minutes (01:03–01:42 UTC), and 170 of 183 trials took no action.
- **The server's limit.** The model server starts with `--max-running-requests 10` (confirmed in `serve.log` and `log.txt`).
- **What happened.** With the gate off, all 92 trials of the first wave asked at once: 10 ran and 82 queued.
- The server's own warm-up request waited in that queue past its 600 s timeout. The server then reported "Initialization failed" and shut down, and every later request got "connection refused" (3,740 failed requests in the log).

**Control arm (`arcaid3-lt-off-r2`):** invalid by design whatever it shows. Its 92 trials share 10 server slots while each trial's 60-minute clock runs.

**What the two failed rounds establish about this setup:**
- One GPU serves 10 streams.
- dfranzen's gate (10 active streams) matches that limit. Our whole-game runs ran 8–10 requests at a time.
- So a fair trial must hold one of only 10 streams for its whole clock. At most 10 trials can run at a time.

## Round 3: valid. No detectable difference; the direction leans against the lexicon

**Setup** (`arcaid3-lt-{lex,off}-r3`, 2026-10-10):
- 183 trials per arm, 10 at a time, 20 minutes each, no priority gate.
- The two arms ran side by side, 10:21–16:32 and 10:21–16:39 UTC.

**Validity.** All 183 trials were logged in each arm, and none failed to act.
- Each trial was active for a median of about 18 of its 20 minutes and used about 76,000 tokens. The arm totals were 13.80 M and 13.94 M tokens.
- No connection errors and no server restarts.

| | Lexicon on | Lexicon off |
|---|---|---|
| Levels cleared (of 183) | 58 | 67 |
| Cleared by this arm only | 8 | 17 |
| Time-weighted score | 0.202 | 0.214 |
| Median time to clear | 421 s | 457 s |

- **Clear-rate difference, on − off:** **−4.9 points** (95% CI −10.2 to +0.4). Exact McNemar p = 0.108.
- **Time-weighted difference:** −0.012 (sign-flip p = 0.42).
- **Decision** (rule fixed before round 1, amended before rounds 2 and 3): **no detectable difference.**

**By level depth** (cleared on / off):

| Levels | Cleared on / off |
|---|---|
| 0 | 23 / 22 of 25 |
| 1–2 | 22 / 25 of 50 |
| 3–5 | 11 / 17 of 75 |
| 6 and up | 2 / 3 of 33 |

**By game**, the largest gaps were:
- ar25 3 / 6, s5i5 2 / 5 and r11l 1 / 2, against the lexicon;
- m0r0 3 / 1 and g50t 1 / 0, for it.

**Usage:** the model read the view in 19.1% of tool calls and read `.rules` 688 times.

## What it means

- **The lexicon view does not help the agent clear levels from a cold start.**
  - The interval excludes any gain above about +0.4 points of clear rate. The estimate is a small loss, which is not significant.
  - This matches every earlier measure: the v2/v4 replicates (−0.33 points), the same-day pair in the leaderboard-like setup (−0.03 over two rounds), and the leaderboard itself.
- **The level-trial test now works, and it is the most sensitive measure we have.**
  - 183 paired trials give a 95% half-width of about 5 points of clear rate from one round.
  - A round costs about 6.3 hours on both GPU sessions.
- **Three things a fair trial needs**, learned at the cost of two rounds:
  - one model stream per trial (the server runs 10);
  - no priority gate;
  - each trial timed from its own start.

**Data:** `arcaid3-lt-{lex,off}-r3/`, and `compare_level_trials.out` from `python3 kaggle/lexicon-dfranzen/compare_level_trials.py 3`.
