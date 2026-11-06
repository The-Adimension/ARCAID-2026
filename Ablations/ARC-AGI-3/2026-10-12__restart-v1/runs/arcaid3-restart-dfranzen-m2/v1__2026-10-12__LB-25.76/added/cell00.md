# ARCAID3: stuck-level restart on Franzen's Milestone 2 notebook

**Base:** `dfranzen/arc-agi-3-milestone-2-solution` version 1 (27.89). Every cell of it is here, in order. Three are edited, at anchors checked by `kaggle/restart-dfranzen/build.py`:
- **Cell 4** applies one more patch after Franzen's (`restart.patch`) and sets `STUCK_RESTART_TOKENS`.
- **Cell 16:** the save run plays all 25 public games at once with the leaderboard's GPU share per game (7,254 s), priority scheduling on. The submission branch asserts the competition settings.
- **A cell at the end** summarises the restart events.

**The change:** when one level's conversation has used `STUCK_RESTART_TOKENS` generated tokens (100,000) without completing it, the harness clears that level's messages once and starts a fresh turn on the current board. The system prompt, the retained functions and the board stay, and the level is re-priced by the scheduler as a fresh attempt. `STUCK_RESTART_TOKENS = 0` gives Franzen v1's behaviour.

**Why:** in Franzen's own 4-pass run, an attempt still open at 100K tokens finished by 140K only 14.6% of the time, while 40 of its 67 unfinished attempts were on levels another pass completed, typically with half the tokens.

**Mechanism test** (fixed before the run, `kaggle/restart-dfranzen/DECISION_RULE.md`): pass if at least 40% of fired restarts go on to complete their level (control in this setup: 9 of 46 attempts past 100K tokens, 19.6%) and restarts fire on at most 15% of level attempts; fail below 25% or above 15%.

Licence: Franzen's notebook and patch are his; the restart patch is MIT-0.
