# Plan 2026-10-23: raise RHAE on the Franzen base by trading tokens for actions

Full text of the plan is in the session reply; this file keeps the numbers that back it, all computed in this
repo from `external_submission/*/outputs` (Franzen, shiiin9, sirikilohit Save & Runs on the 25 public games).

## Where actions and tokens go

- 60 game runs, 438 levels: actions on cleared levels 3,007; on never-cleared levels 2,876 (49%).
- Median agent/human action ratio on cleared levels 0.69 (mean 0.81, n = 115). Only 1 of 438 levels exceeded 5x human.
- Franzen run, 531 responses: 52% executed no action and consumed 61% of generated tokens (avg 2,058 vs 1,358).
- 86% of generated tokens are reasoning. 697 generated tokens per action. Prompt cache hit 94.2%.
- Before the first action of a level: median 3.5k generated tokens, p90 10.8k.
- Inspect-only streaks before an action: median 2 exchanges, p90 4. Stuck tail on r11l: 11 exchanges, 15k tokens,
  all spent writing beam/A* planners inside a movement model that was never tested.
- RESET entries: 6 in 1,327 actions (Franzen), 18 in 25 games (shiiin9). Deaths are rare.

## Human baselines, 25 public games (183 levels)

min 6, p10 22, p25 32, median 60, p75 119. Per depth median: L1 30, L2 54, L3 51, L4 54, L5 96, L6 80, L7 86, L8 92.

## RHAE arithmetic used for targets

One extra cleared level at depth d on an N-level game adds d x 1.15 / (N(N+1)/2) to that game's score.
At d = 4, N = 7 that is 0.164 of a game, i.e. 0.30 leaderboard points when averaged over 55 games.
+20% levels cleared from ~3.5 per game is ~0.7 levels per game, ~+10 leaderboard points, above the 3.9-point
single-draw SD of identical Franzen copies (Son Pham, discussion 745062).

## Deliverable

`kaggle/probefirst/probe_first_cell.py` (+ README): paste-in cell, self-tested against a stub of
`inference.agent.tool_agent.ToolAgent`.
