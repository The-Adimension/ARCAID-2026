## ARCAID3 lexicon view (the one added code cell)

The next cell adds `current_frame.code`, `.objects`, `.native` and `.changes_since(...)` to the Python sandbox and
one sentence to the system prompt. It tests itself through the real sandbox before the run and rolls back to the
stock sandbox if anything fails. Source: `arcaid3/part2/lexicon.py` (standard library only).
