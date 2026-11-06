# Lexicon on against off in a leaderboard-like setup, two rounds (2026-10-09)

**Question:** with a same-day control and conditions closer to the leaderboard run, does the lexicon view (v5) help?

**Answer: no measurable effect.** The two rounds point in opposite directions and cancel. Over both rounds the difference is **−0.03 points**. The decision rule in `DECISION_RULE.md`, committed before round 2, gives "no measurable effect".

| | Lexicon on (v5) | Lexicon off (control) | On − off |
|---|---|---|---|
| Round 1 | 51.20 (112 levels) | 43.77 (101 levels) | **+7.42** |
| Round 2 | 40.08 (95 levels) | 47.57 (107 levels) | **−7.49** |
| Mean of the two rounds | 45.64 | 45.67 | **−0.03** |

- **Levels:** −0.5 per round on average.
- **Levels-over-time area:** −1.17.
- **Per-game sign-flip test** on each game's difference averaged over the rounds: p = 0.995.

## Setup

**Notebooks.** Both come from `kaggle/lexicon-dfranzen/lb_setup.py` and are built from the same v5 notebook (`build.py`).
- **Lexicon on (`arcaid3-lb-lex-r{1,2}`):** the v5 notebook, unchanged except for the setup below.
- **Lexicon off (`arcaid3-lb-off-r{1,2}`):** the same notebook with `ARCAID3_LEXICON=0`. Nothing is installed (the log says `ARCAID3_LEXICON_OFF`), so the harness runs as dfranzen's notebook does.
- **Round 2 reused round 1's notebooks byte for byte**, under new kernel names.

**Setup, closer to the leaderboard run than the earlier save runs:**

| | This setup | Earlier save runs |
|---|---|---|
| Games | All 25 public games at once | 10 of the 25 |
| Time per game | 7,254 s (121 min) | 25 min |
| Priority scheduler | On | — |

- The 7,254 s comes from the notebook's own scaling, `532*60 * concurrency // 110`. It keeps each game's share of the GPU equal to the leaderboard run's: about 110 games at once, each for up to 532 min.
- Each game used a median of about 172,000–175,000 tokens. The earlier save runs used about 86,000.

**Pairing.** In each round, both arms ran side by side on the two GPU sessions.

| Round | Started, on / off (UTC) | Duration | Throughput, on / off |
|---|---|---|---|
| 1 | 11:35:49 / 11:35:45 | about 2 h 2 min | 600 / 605 tokens/s |
| 2 | 16:13 / 16:11 | about 2 h 2 min | 582 / 595 tokens/s |

**Health.** All four runs completed.
- No tracebacks, out-of-memory errors or kills.
- The lexicon's own counters report 0 errors.
- Total tokens per run were 4.28–4.47 M.

**Round 2's collapses were real plays, not failures.** In round 2 the lexicon arm cleared 0 levels on m0r0, sc25 and dc22, which it had cleared 6, 6 and 4 times in round 1. Those games ran their full 2 hours, just with fewer actions.

**Reproduce:** `python3 kaggle/lexicon-dfranzen/compare_lb_setup.py 1 2` (output in `compare_lb_setup.out`; add `--fetch 1 2` to download again). Raw request logs are not committed.

## Noise in this setup

**Run-level noise.** Between the two rounds, identical code moved by 11.1 points (on) and 3.8 points (off). The pooled SD of one run is about **5.9 points**, from only 2 degrees of freedom.
- That is about the same as in the 10-game, 25-minute setup (6.2).
- So 25 games and longer budgets did not make a run steadier. My round-1 estimate of about 5 points for the SD of a difference between runs was too optimistic: it is about 8.

**Single games swing hard with identical code:**
- With the lexicon on: m0r0 went 6 → 0 levels, sc25 6 → 0, dc22 4 → 0, ka59 5 → 1, and s5i5 1 → 6.
- With it off: tn36 went 0 → 5, cn04 6 → 2, and tr87 1 → 5.
- The median change in a game's score between rounds was 5.5 points (on) and 9.5 points (off), and up to 100.

## Per game, both rounds

| Game | Levels on (r1 / r2) | Levels off (r1 / r2) | Score on, mean | Score off, mean |
|---|---|---|---|---|
| ar25 | 8 / 8 | 8 / 8 | 100.0 | 100.0 |
| bp35 | 1 / 1 | 1 / 1 | 1.2 | 1.1 |
| cd82 | 6 / 6 | 3 / 6 | 93.4 | 61.2 |
| cn04 | 4 / 1 | 6 / 2 | 26.2 | 56.5 |
| dc22 | 4 / 0 | 4 / 2 | 15.9 | 31.0 |
| ft09 | 6 / 6 | 6 / 6 | 100.0 | 100.0 |
| g50t | 4 / 2 | 0 / 0 | 23.2 | 0.0 |
| ka59 | 5 / 1 | 3 / 5 | 21.9 | 30.8 |
| lf52 | 2 / 3 | 2 / 3 | 8.2 | 7.6 |
| lp85 | 8 / 8 | 8 / 8 | 100.0 | 100.0 |
| ls20 | 4 / 4 | 4 / 4 | 29.5 | 33.7 |
| m0r0 | 6 / 0 | 5 / 6 | 50.0 | 85.7 |
| r11l | 6 / 6 | 5 / 6 | 100.0 | 85.7 |
| re86 | 5 / 6 | 5 / 5 | 43.2 | 39.2 |
| s5i5 | 1 / 6 | 2 / 2 | 29.3 | 8.3 |
| sb26 | 8 / 8 | 8 / 8 | 98.2 | 100.0 |
| sc25 | 6 / 0 | 5 / 5 | 50.0 | 70.2 |
| sk48 | 2 / 1 | 1 / 1 | 5.4 | 1.6 |
| sp80 | 1 / 1 | 1 / 2 | 4.8 | 9.5 |
| su15 | 4 / 4 | 6 / 3 | 22.2 | 30.0 |
| tn36 | 1 / 1 | 0 / 5 | 3.6 | 24.9 |
| tr87 | 6 / 6 | 1 / 5 | 100.0 | 28.9 |
| tu93 | 8 / 9 | 8 / 9 | 78.5 | 77.3 |
| vc33 | 3 / 3 | 6 / 4 | 21.3 | 51.4 |
| wa30 | 3 / 4 | 3 / 1 | 15.3 | 7.2 |

**Leads, not findings.** With 25 games, some will favour one arm in both rounds by chance.
- With the lexicon on, g50t (4 and 2 levels against 0 and 0) and tr87 (6 and 6 against 1 and 5) are ahead in both rounds.
- With it off, vc33 (6 and 4 against 3 and 3) is ahead in both rounds.

## What this means

- **The lexicon view, as the model uses it, does not move the score in a measurable way.** That holds:
  - in the replicate save runs (v2 against v4: −0.33 over three runs each);
  - in the same-day control in this setup (−0.03 over two rounds);
  - on the leaderboard (24.95 and 27.05, inside the 21–29 band of unchanged dfranzen copies).
- **The model's behaviour does change.** It reads the view in about 13% of tool calls and `.rules` 127–136 times per run. That changes what happens in individual games, but not the total beyond noise.
- **Run-level noise is about 6 points in both setups.** Detecting a 5-point gain would take about 20 or more runs per arm: about 2 days of both GPU sessions running nonstop. Small changes to the agent can't be judged on score at this budget. Offline or decision-level measures are needed.

## Next

As the rule says: keep the code, but stop treating the view as the lever. The independent review's other priorities are now first:
1. **Fewer model calls per level:** a scripted probe of each action at a level's start, and macros such as `click(sym)` that check their own predictions.
2. **Scheduling and time split** across the leaderboard's 110 games.
3. **Decision-level offline tests:** replay a recorded state and grade the model's choice with and without help. Each state is its own pair, so these have much more statistical power than whole runs.
