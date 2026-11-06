# Decision rule for level trials, lexicon on against off (fixed before the first run, 2026-10-09)

## Design

**Trials.** Every level of the 25 public games is its own trial: 183 in all.
- Each trial starts cold at its level, using the engine's `set_level` and then a RESET (`kaggle/lexicon-dfranzen/level_trials_cell.py`).
- Each trial has 60 minutes, with 92 trials running at a time.
- A trial that clears its level keeps playing until its time is up, so the GPU load does not depend on the outcomes.

**Arms.** The two arms run side by side in the two GPU sessions:
- the v5 lexicon notebook;
- the same notebook with `ARCAID3_LEXICON=0`.

**Validity, checked before the run:**
- On 42 recorded level solutions, replaying the level's actions from a cold start at that level clears it, as in the original runs.
- Started through the harness's own `GameAPI._start_game`, 26 entries opened on the right level with the same screen as a direct engine start.

## Rule

**Primary measure:** levels cleared, lexicon on against off, paired by (game, level) over all trials.

**Test:** exact two-sided McNemar on the trials that only one arm cleared.

| Outcome | Condition |
|---|---|
| **Lexicon helps** | On − off > 0 and p < 0.05 |
| **Lexicon hurts** | On − off < 0 and p < 0.05 |
| **No detectable difference** | p ≥ 0.05. The 95% interval for the difference in clear rate says how large an effect is still possible |

**Reported but not decisive:** the time-weighted score (sooner clears count more), and the results by level depth and by game.

## Limits

- **Cold starts are harder than real play.** In a real game the agent reaches level k after playing levels 1 to k − 1, and it carries what it learned there. These trials measure solving one level from a standing start.
- **Power.** One run gives one trial per level per arm. At about 183 pairs, a difference of roughly 8–10 points in clear rate should be detectable, depending on how many trials only one arm clears.

## Amendment before round 2 (2026-10-10)

**Round 1 is excluded.** In each arm, 74 of the 158 later-level trials took no action, so round 1 does not measure the agent.
- **Cause:** the notebook's priority gate (`ARC3_MAX_ACTIVE_STREAMS=10`, switched on by `USE_PRIORITY_SCHEDULING`) lets only 10 games hold a model stream at a time.
- A slot frees only when a game's context is first trimmed. With 92 trials running at once on 60-minute clocks, most trials never got a slot.

**Round 2 runs without the gate.** Everything else is unchanged. The rule above applies to round 2 alone.

**New validity check:** a round in which more than 5% of the trials never act is reported as invalid. It is not judged.

## Amendment before round 3 (2026-10-10)

**Round 2 is excluded as well.**
- **What happened:** the model server runs 10 requests at a time (`--max-running-requests 10`). Round 2 put 92 trials on it at once, and the server shut down during its own warm-up check. In the lexicon arm, 170 of 183 trials took no action.
- **The control arm is invalid by design:** its 92 trials shared 10 slots while their clocks ran.

**Round 3 changes the setup only.** The 183 trials run 10 at a time, so each trial holds one model stream for its whole clock. Each trial gets 20 minutes, chosen by the user. There is no priority gate.

**The rule and the validity check are unchanged** and apply to round 3 alone.
