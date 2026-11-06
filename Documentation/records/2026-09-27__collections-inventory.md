# `inputs/arc3-collections`: verified inventory (2026-09-27)

This replaces the first, shallower version of this file. Two independent read-only audits traversed every directory and opened every file:
- **Audit 1:** `1345`, 118 directories and 1,348 files. All 18 pickles were loaded with class stand-ins, so no bundled code ran.
- **Audit 2:** `0393`, `5643`, `2345`, `3244` and `3245`, with `inputs/local_play` for comparison. All 2,184 files were SHA-256 hashed.

Neither audit found a file it could not open. The findings below were checked against the audit scripts and data in the session scratchpad. The divergence between the game-file copies and the official files was re-verified independently.

## 1. What is unique, and what is a copy

| Folder | Verdict |
|---|---|
| `1345` | **Every run directory is a byte-for-byte copy** of a folder in `submissions/*/outputs` or `experiments/*/outputs`. `abrun1`, `resetrun1` and `stallrun1` crashed and have no game data. Unique content: `taaf/` (141 files, framework source), `fp4src/` (28 files, the Kaggle Duck bundle; `serving_teardown.py` is missing), `abtest/` (17 builder and test scripts), the `stallnb`, `lb9` and `top` notebooks, and **3,090 animation in-between frames** in `intermediate_states.pkl` (run1, abrun2, abrun3; up to 118 per step). No other file stores those frames. |
| `0393` | The most complete autoresearch snapshot: `consult/`, `handover.md`, `build/`, 183 teacher frame PNGs, and the full `MEMORY.md` (866 lines). |
| `5643` | An earlier snapshot of `0393`. 89 files are identical and 22 differ only in line endings. Its only unique files are `sessions/probe-p5k.{json,log}`, a 5,000-action program run. |
| `3244` | Its 3 files are prefixes of `3245`'s. Nothing unique. |
| `3245` | `local_play/` is identical to `inputs/local_play` (807 of 807 files). `environment_files/` equals `2345`'s. Unique content: its `program.md`, `results.tsv` and memory notes. |
| `2345` | Starter kit. `agent/my_agent.py` is **byte-identical to `0393/perception.py`**. |
| Game-file copies (`2345`, `3245`) | **They differ from the official `environment_files` in all 25 games, even ignoring line endings.** They add a licence header, and 23 of 25 games also differ by 4–46 lines of code; the official files have extra methods such as `_get_valid_actions` and `_get_hidden_state`. Replay only against the official files in `inputs/official-input-arc-prize-2026-arc-agi-3/`. |

## 2. Unique play data, verified by replay

| Source | Content | Verified outcome |
|---|---|---|
| Duck runs (`submissions/`, `experiments/`; copies in `1345`) | 148 passes in `1345` alone and 190 unique transcripts overall. Per action: the board as a 64×64 grid, the flags `board_changed`, `level_completed`, `game_over` and `done`, batch position, and tokens on the first action of each call. Per turn: prompt, carried world model, full reasoning (18.7M characters in `1345`), and tool code. | Replay matches on all runs (see `SYSTEM1-REPLAY`). In `1345`: 176 of 1,071 levels cleared and 1 full win (sb26, 8/8 in 135 actions). The win's last level shows only `done`/`WIN`, not `level_completed`. |
| Teacher rounds (`0393/rounds`) | 14 rounds and 206 decisions by claude-opus-5, over **12 games**. Each has a note of about 23 words plus commands (`CLICK id`, `UP n`, `GOTO id`, `SPACE`, `UNDO`), which expand to 511 engine actions. 16 levels were cleared. There is no human play. | **All 13 traces replay exactly**, using the command mapping in `play.py` and a stand-in agent loop. The engine-level actions are in the audit's `round_replays.json`. The r011/sc25 round has no trace, and 5 r001 folders were never answered. |
| `local_play` recordings | 62 recordings, machine-paced (no human). | 31 match frame for frame and 4 match on state and levels. **Real clears: 36 levels on 11 games**: sb26 8/8 (124 actions), ft09 6/6 (90), cd82 6/6 (70), sc25 6/6 (127), tu93 3, vc33 2, and 1 each on lp85, sp80, lf52, r11l and su15. One tn36 recording differs by 28 cells on 7 steps, cause unknown. |
| **Fake records** | 25 `summary.json`, 25 `win_actions.json` and 25 two-line recordings claim WIN on every level, but their frames are the unplayed start boards. All were created on 2026-09-23 at 10:55. | **Replay refutes all 25.** Counted naively they would add 185 levels. Exclude them. |
| Program evaluations (`sessions/`) | 21 runs of the programmatic agent: scores and actions per level. | Action sequences are not stored, only a trace hash per game. |
| Notes | `principles.md` (**19 rules**, P1–P19, with evidence); 13 per-game mechanics notes (0393); `MEMORY.md` research log; `rounds.tsv`, `submissions.tsv`, `results.tsv`. Scores in `sessions` are percentages, while `trace.json` stores fractions. | Text; no replay needed |

## 3. Turning images and video into evidence (tested)

| Media | What it shows | Method | Measured accuracy | New information? |
|---|---|---|---|---|
| Teacher `frame_NNN.png` (183) | The board at 8 px per cell, with anti-aliased object-id labels | Cell = width / 64; exact RGB match to the `PALETTE` in `play.py`; majority colour per cell | 99.995% of cells, 164 of 183 frames exact. All errors sit under labels. Sampling only the centre pixel scores worse (99.28%). | None: the frames equal the replayed boards, and object ids regenerate exactly. |
| `local_play` PNG and GIF (1,025 frames) | Clean board renders at 8×, 6× or 4×. GIFs drop repeated frames and show the final animation layer only. | Same method | **1,025 of 1,025** equal a recorded or replayed board | None |
| `1345/movies/*.mp4` (58) | 128×128 H.264 at 8 fps, one frame per step | Average each 2×2 block, then nearest palette colour with luminance weighted 2× (needs `av`/`imageio`; the system has no ffmpeg) | 96.9% of frames exact, about 99.999% of cells. Residual errors: sky blue read as light grey (compression). | None: frame order and count equal `events.jsonl` in 58 of 58 |
| `diagnostics.html` and `.per_game_cards.pkl` thumbnails (177, base64) | 84×84 cards; the board sits 10 px in at 1 px per cell | Crop, then nearest palette colour | Inner 62×62 cells: 177 of 177 exact. The outer ring is covered by the chart frame. | None |
| Charts in `diagnostics.html` | Plots | Would need digitising | n/a | None: `benchmark.json` holds the source numbers |

**Conclusion on media:** every image and video in the collection decodes reliably back to 64×64 colour grids, but none contains a board the engine replay or the JSON logs don't already provide. They are useful for cross-checking data, not as new evidence. The one frame-level source with unique content is the 3,090 animation frames in the `1345` pickles, which store mid-action motion that the per-action logs keep only as the final board.

## 4. Corrections to the earlier shallow pass

| Earlier claim | Correction |
|---|---|
| "206 teacher decisions across 13 games" | 206 decisions across **12** games, and **all replay exactly** |
| "20 principles" | **19** (P1–P19); the 20th heading is a status note |
| "Large files are re-renders of the same 190 runs" | Confirmed, plus a correction: **all of `1345`'s runs already exist byte-for-byte in `submissions/` and `experiments/`** |
| `local_play` has "3 fully solved games" | **4 full wins** (sb26, ft09, cd82, sc25) and **36 real levels on 11 games** |
| Not previously noticed | 25 fake WIN records in `local_play` (refuted by replay); **bundled game copies diverge from the official files**; a model-name conflict (saved settings name Qwen3.6-27B-FP8, transcripts show Qwen3.8-27B-FP8 served); `uncached_input_tokens` is always 0 |
