## ARCAID3 lexicon view v2 (the one added code cell)

The next cell adds `current_frame.code`, `.objects`, `.native` and `.changes_since(...)` to the Python sandbox,
corrects the harness's prompt lines that said a frame exposes "only" five fields, adds a "when to look" line, and
adds a first-turn / new-level cue to the user message. It tests itself through the real sandbox before the run and rolls back to the
stock sandbox if anything fails. Source: `arcaid3/part2/lexicon.py` (standard library only).
