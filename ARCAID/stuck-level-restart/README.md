# Stuck-level restart (ARC-AGI-3)

**Layer:** memory. **Switch:** `ARC3_STUCK_RESTART_TOKENS` (0 = off, which is the base notebook's behaviour). Events are logged to `ARC3_STUCK_RESTART_LOG` (JSON lines).

A patch to the Duck harness's `tool_agent.py`, applied after Daniel Franzen's own patch. When a level's conversation has used the set number of generated tokens (100,000 in our runs) without clearing the level, its history is cleared once. The board, the system prompt and retained functions stay. The level keeps its token count, so the scheduler prices the game as it would without the patch.

| File | What |
|---|---|
| `restart_v1.patch` | Version 1, embedded in `arcaid3-restart-dfranzen-m2` and `-r2` (2026-10-12) |
| `restart.patch` | Version 2 (2026-10-14): fires on resumptions with no action, adds a fresh opener after such a restart, never carries the note across a level. Embedded in `arcaid3-pair-restart-r1`. |
| `build.py` | Builds the notebook from Franzen's v1 with three anchored edits, and asserts the contest settings on the submission branch |
| `test_restart.py`, `sim_restart.py`, `verify_notebook.py` | Unit test, offline simulation, and a notebook-versus-base check |

**Tests:** `../../Ablations/ARC-AGI-3/2026-10-12__restart-v1/` and `../../Ablations/ARC-AGI-3/2026-10-13__restart-pair/`.
