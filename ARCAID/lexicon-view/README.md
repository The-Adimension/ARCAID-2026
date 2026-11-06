# Lexicon view (ARC-AGI-3)

**Layer:** perception. **Kill switches:** `ARCAID3_LEXICON=0` (all of it), `ARCAID3_SCALE_LOCK=0`, `ARCAID3_RULES=0`.

One code cell, standard library only, pasted into a Duck-harness notebook. It reads each 64×64 frame back into the objects that drew it and offers that reading to the model inside the Python sandbox:

| Member | Content | Since |
|---|---|---|
| `current_frame.code` | The board as objects: true cell size, a legend of multi-colour pictures with stable names (mirrored and rotated copies linked), and where each sits | v1 |
| `current_frame.objects` | The same as a list of dicts, with a screen row/col to click | v1 |
| `current_frame.native` | The board at its true resolution | v1 |
| `current_frame.changes_since(prev)` | Objects that moved, appeared, disappeared or turned into another picture | v1 |
| per-level scale lock | One block size per level, agreed across the level's frames | v2 |
| `current_frame.rules` | Rules induced from the level's recent steps: `when <action> [if/unless <relation>] then <change>`, with right and wrong counts, and the last step's unexplained changes | v3 |
| `.rules` cue; object permanence | A cue in the user message when `.rules` can answer; merged pieces cut back into objects seen apart | v4 |

The cell also edits the harness's prompt lines that say a frame exposes "only" five fields, adds a "when to look" line and a first-turn/new-level cue. Each edit applies only if its anchor is found once, and the `ARCAID3_LEXICON_READY` log line reports which applied. The cell self-tests through the real sandbox and rolls back on failure. Counters are printed as `ARCAID3_LEXICON_STATS` and `ARCAID3_LEXICON_FINAL`.

## Versions and where they ran

The cell's own header numbers its versions. Two different changes are both called "Version 2". The table gives each by date. The Kaggle version numbers of the notebooks are a separate count.

| Cell header | Change | Lines | Kaggle notebook versions that ran it |
|---|---|---|---|
| v1 (2026-10-03) | The view and one sentence | 712 | `arcaid3-lexicon-view` v1, `arcaid3-lexicon-view-py312` v1 (sheetu base) |
| "Version 2" (2026-10-04) | The three "only" prompt lines, a "when" trigger, a first-turn cue | 805–811 | `arcaid3-lexicon-view-v2` v1 (sheetu base); `arcaid3-lexicon-view-dfranzen-m2` v1 (first port to Franzen M2 v1) |
| "Version 2" (2026-10-07) | Per-level scale lock | 965 | `arcaid3-lexicon-view-dfranzen-m2` v2; `arcaid3-rep-v2-r1`, `-r2` |
| Version 3 (2026-10-08) | `current_frame.rules` | 1,777 | `arcaid3-lexicon-view-dfranzen-m2` v3 |
| Version 4 (2026-10-08) | `.rules` cue; object permanence; finer-grid scale check | 2,018 | `arcaid3-lexicon-view-dfranzen-m2` **v4 (selected)**; `arcaid3-rep-v4-r1`, `-r2` |
| Version 5 (2026-10-09) | Picture names carry 4 hex digits (3 gave two pictures one name on 34 of 161 levels); `.rules` drops older steps first when out of time | 2,026 | `arcaid3-lb-lex-r1`, `-r2`; `arcaid3-lt-lex-r1`–`r3` |
| Version 6 (2026-10-17) | Multi-step object permanence; `.rules` cue only after turns that executed actions; death/reset snaps excluded from `.rules`; scale lock keeps a level's first frames on long levels; contest-configuration guard (`TRUE_SUBMISSION`) | 2,103 | `arcaid3-lexicon-view-dfranzen-m2` v5, v6; `arcaid3-lexicon-dprime-dfranzen-m2`; `arcaid3-lexicon-dprime-dfranzen-m2-sg` |

Read from the cell headers of the collected notebooks. `as-run/INDEX.csv` lists every notebook version that ran each exact text, by sha256.

## Files

- `source/lexicon.py`: the screen-to-code transcoder.
- `source/rule_grammar.py`: the rule grammar behind `.rules`.
- `source/rules_view.py`: the sandbox side of `.rules`.
- `build/`: the generators of the notebook cell. `build.py` and `lexicon_cell_dfranzen.py` target Franzen's notebook; the `*_sheetu*` files target the earlier sheetu base.
- `tests/`: the port verification, perception and scale-lock evaluations against the engine on recorded plays, and the rule-grammar comparison. Their saved outputs are kept as `*.out`.
- `docs/`: design notes and analyses written at the time.
