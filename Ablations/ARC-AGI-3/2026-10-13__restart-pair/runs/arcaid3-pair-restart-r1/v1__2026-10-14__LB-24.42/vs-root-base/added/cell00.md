# ARCAID3: stuck-level restart on Franzen's Milestone 2 notebook

**Base:** `dfranzen/arc-agi-3-milestone-2-solution` version 1 (27.89). Every cell of it is here, in order. Two of its cells are edited, at anchors checked by `kaggle/restart-dfranzen/build.py`:
- **The setup cell** (environment and paths) applies one more patch after Franzen's (`restart.patch`) and sets `STUCK_RESTART_TOKENS`.
- **The customisation cell:** the save run plays all 25 public games at once, each with the leaderboard's GPU share (7,254 s), priority scheduling on. The submission branch asserts the competition settings.

Three cells are added: this note, the restart patch (`%%writefile`), and a summary of restart events at the end.

**The change (restart.patch v2):** when one level's conversation has used `STUCK_RESTART_TOKENS` generated tokens (100,000) without completing the level, the harness clears that level's messages once and opens a fresh turn on the current board. This also happens while the model is deliberating without acting.
- **Kept:** the system prompt, the retained functions and the board.
- **Scheduling is unchanged:** the level keeps its token count, so the priority gate treats the game as it would with the flag off.
- `STUCK_RESTART_TOKENS = 0` gives Franzen v1's behaviour.

**Evidence so far:** none that it helps. Counted the same way in both arms, attempts past 100K tokens completed 5 of 21 times with restart v1 and 9 of 46 without (p = 0.46). The v1 submission scored 25.76, at the mean of unchanged copies.

**Test:** `kaggle/restart-dfranzen/DECISION_RULE_PAIR.md`.

Licence: Franzen's notebook and patch are his; the restart patch is MIT-0.
