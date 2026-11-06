# ARCAID3 lexicon view on Daniel Franzen's Milestone 2 solution

**What this is.** [Daniel Franzen's Milestone 2 notebook](https://www.kaggle.com/code/dfranzen/arc-agi-3-milestone-2-solution), version 1 (public LB 27.89), built on [Tufa Labs' Duck harness](https://www.kaggle.com/code/jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner). Every original cell is kept, unchanged and in order: model, SGLang serving, 128K context, scheduler, harness patch and competition settings are his.

**The one change.** One cell before *Run the benchmark* adds an optional way for the model to read the board in the Python sandbox:

| New in the sandbox | What it gives the model |
|---|---|
| `current_frame.code` | The board as objects: the true cell size, a legend of symbols (small multi-colour pictures with stable names), and where each symbol sits |
| `current_frame.changes_since(previous_frame)` | Which objects moved, appeared, disappeared or turned into another symbol |
| `current_frame.objects` | The same objects as data, with a screen row/col to click |
| `current_frame.native` | The board at its true resolution |

The cell also lists these members in the three prompt lines that say a frame exposes "only" five fields, adds a "when to look" line next to the "most recent change" line, and adds a first-turn / new-level cue to the user message. Each edit applies only if its exact anchor is found; the `ARCAID3_LEXICON_READY` line reports which applied. Before the run the cell tests itself through the real sandbox and rolls back to the stock sandbox if anything fails.

**Why port it here.** On the old sheetu base (16K context, prefix caching off) the view was used in 22% of tool calls but cannot be judged there: that stack scores about 3 to 6, against about 26 for this one. On a 128K context its output no longer crowds out the model's own history.

**Save run.** Franzen's own v1 demo settings: 10 public games, 25 minutes each, 10 streams, 1 pass. That matches the saved outputs of his v1 run, so the two compare directly (levels, tokens, cache reuse, view usage). Like every single run, it cannot settle a score difference.

**Kill switch:** `ARCAID3_LEXICON=0`. **Log lines:** `ARCAID3_LEXICON_READY`, `ARCAID3_LEXICON_STATS` every 200 tool calls, `ARCAID3_LEXICON_FINAL` at the end.

Credits: Daniel Franzen (Milestone 2 solution, Apache-2.0 per his notebook), Tufa Labs (Duck), and the model, serving and checkpoint authors he credits below. Third-party code and weights keep their licences.
