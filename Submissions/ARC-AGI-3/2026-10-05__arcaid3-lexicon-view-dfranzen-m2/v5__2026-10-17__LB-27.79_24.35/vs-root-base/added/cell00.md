# ARCAID3 lexicon view on Daniel Franzen's Milestone 2 solution

**What this is.** [Daniel Franzen's Milestone 2 notebook](https://www.kaggle.com/code/dfranzen/arc-agi-3-milestone-2-solution), version 1 (public LB 27.89), built on [Tufa Labs' Duck harness](https://www.kaggle.com/code/jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner). Every original cell is kept, unchanged and in order: model, SGLang serving, 128K context, scheduler, harness patch and competition settings are his.

**The one change.** One cell before *Run the benchmark* adds an optional way for the model to read the board in the Python sandbox:

| New in the sandbox | What it gives the model |
|---|---|
| `current_frame.code` | The board as objects: the true cell size, a legend of symbols (small multi-colour pictures with stable names), and where each symbol sits |
| `current_frame.changes_since(previous_frame)` | Which objects moved, appeared, disappeared or turned into another symbol |
| `current_frame.objects` | The same objects as data, with a screen row/col to click |
| `current_frame.native` | The board at its true resolution |
| `current_frame.rules` (version 3) | Rules learned from this level's recent steps, `when <action> [if/unless <relation>] then <change>`, each with how often it was right and wrong, and the last step's changes that no rule explains |

The cell also lists these members in the three prompt lines that say a frame exposes "only" five fields, adds a "when to look" line next to the "most recent change" line, and adds a first-turn / new-level cue to the user message. Each edit applies only if its exact anchor is found; the `ARCAID3_LEXICON_READY` line reports which applied. Before the run the cell tests itself through the real sandbox and rolls back to the stock sandbox if anything fails.

**Why port it here.** On the old sheetu base (16K context, prefix caching off) the view was used in 22% of tool calls but cannot be judged there: that stack scores about 3 to 6, against about 26 for this one. On a 128K context its output no longer crowds out the model's own history.

**Save run.** Franzen's own v1 demo settings: 10 public games, 25 minutes each, 10 streams, 1 pass. That matches the saved outputs of his v1 run, so the two compare directly (levels, tokens, cache reuse, view usage). Like every single run, it cannot settle a score difference.

**Version 2: per-level scale lock.** The lexicon used to detect the grid size afresh on every frame, so a sparse frame could flip to a coarser grid and rename every object. Now every frame of a level is read at one block size, agreed across that level's frames in `history`; a block size that fails on any frame of the level stays rejected. On 4,662 replayed steps of 45 recorded plays (official engine), it halves scale flips (0.26% → 0.13%) and changes only vc33, which improves on every measure; no game gets worse. It is per level because the camera scale changes between levels in 4 of the 25 public games.

**Version 3: `current_frame.rules`.** In the sandbox, a rule grammar learns rules from the level's recent steps in `history`: one rule shape, `when <action> [if/unless <relation>] then <verb>(<who>, <how>)`. Objects are picked by relation (the clicked one, whatever touches X, a colour, or a picture). Conditions are contact, something in the way, or what the click targeted. The verbs are the engine's sprite operations (move, recolor, turn, resize, reshape, vanish, appear). It has no game-specific code and no hand-named rule kinds. Offline, against the version-2 prototype's nine rule kinds, it predicted the next screen better on 55 recorded public plays (changes fully predicted: 9.3% → 16.5%) and on 20 generated games with mechanics the kinds were not built from (18.3% → 33.6%). Whether it helps the model score is what this run starts to test; one run cannot settle it.

**Version 4: `.rules` cue & object permanence.** Adds a cue for `current_frame.rules` when it has something to say (after actions that changed nothing inside the board, or at 6/15/30/60/120 actions on a level), cuts merged objects back apart using earlier frames (object permanence), and rejects coarse grids that a finer grid reads cleanly.

**Version 5: 4-hex-digit picture names & `.rules` time budget.** Expands stable picture names from 3 hex digits to 4 (`0xFFFF:04x`, eliminating collisions seen on 34 of 161 public levels) with a content-derived fallback suffix, and skips older steps rather than the newest step when `.rules` hits its time budget so `LAST STEP` always describes the action just taken.

**Version 6: multi-step contact permanence, read-only cue fix, death-reset filter & long-horizon scale lock.** (1) `.code`, `.objects`, and `.changes_since(...)` now chain distinct predecessor grids across the level (and cache per `FrameView`), so objects that stay in contact across multiple steps (bumping or sliding along a wall) remain separated and `previous_frame` matches `current_frame` instead of reporting false `became` mutations; (2) `ARCAID3_RULES_CUE_STILL` requires `executed_count > 0` so read-only inspection turns (`stale=True`) no longer trigger false no-op cues; (3) `.rules` filters out mid-level death/auto-reset snaps back to the initial board so they do not poison learned rules; (4) `scale_lock` deduplicates consecutive identical grids and retains the level's initial distinct frames beyond 256 steps; (5) adds a `TRUE_SUBMISSION` contest config guard.

**Kill switches:** `ARCAID3_LEXICON=0` (whole view), `ARCAID3_SCALE_LOCK=0` (lock only), `ARCAID3_RULES=0` (rules only). **Log lines:** `ARCAID3_LEXICON_READY`, `ARCAID3_LEXICON_STATS` every 200 tool calls, `ARCAID3_LEXICON_FINAL` at the end.

Credits: Daniel Franzen (Milestone 2 solution, Apache-2.0 per his notebook), Tufa Labs (Duck), and the model, serving and checkpoint authors he credits below. Third-party code and weights keep their licences.
