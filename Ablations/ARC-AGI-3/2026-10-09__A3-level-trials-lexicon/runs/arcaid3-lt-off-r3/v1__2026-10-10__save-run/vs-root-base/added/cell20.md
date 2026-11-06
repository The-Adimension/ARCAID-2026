## ARCAID3 lexicon view (the one added code cell)

The next cell adds `current_frame.code`, `.objects`, `.native`, `.rules` and `.changes_since(...)` to the Python sandbox, lists them in the harness's prompt lines, adds "when to look" lines and a first-turn / new-level cue. It tests itself through the real sandbox and rolls back if anything fails. Version 2 adds a per-level scale lock and version 3 adds rules learned from the level's steps; each has its own sandbox self-test. Port notes and checks: `kaggle/lexicon-dfranzen/` in the ARCAID3 repo.
