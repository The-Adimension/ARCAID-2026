# Probe-first governor (PF)

Paste-in cell for Daniel Franzen's Milestone 2 notebook (`dfranzen/arc-agi-3-milestone-2-solution`, v1) and for
any notebook that carries his harness patch (our `arcaid3-lexicon-view-dfranzen-m2` lineage). One cell, standard
library only, kill switch `PF=0`.

## Why (measured on Franzen's own published Save & Run, 10 public games, 531 model responses)

| Fact | Value |
|---|---|
| Model responses that executed no action | 52% |
| Generated tokens spent in those responses | 61% |
| Median inspect-only exchanges before an action (p90) | 2 (4) |
| Generated tokens before the first action of a level, median (p90) | 3.5k (10.8k) |
| Agent actions / human actions on cleared levels, median (60 runs, 115 levels) | 0.69 |
| RESET entries (deaths + initial) in 1,327 actions | 6 |

A level scores `min(1.15, (h/a)^2)`, so anything below `a = 0.93 h` scores the same. The agent sits at `0.69 h`:
actions are not the scarce resource, generated tokens are (the competition run is wall-clock bound). The cell makes
the model spend actions to test rules instead of tokens to plan inside unverified ones.

## What it does

1. **Ledger** per game: actions spent on the current level and consecutive exchanges with no executed action,
   both read from the harness's own step summary (`action_num`, `level`).
2. **Nudge**: from the 3rd consecutive no-action exchange the opener gets one paragraph stating the ledger and the
   scoring economics. Wording switches to "every further action costs score" once the level is far above a typical
   human count (prior from public per-depth medians; the hidden baselines are unknown).
3. **Cap**: from the 5th consecutive no-action exchange, requests go out with `max_tokens=4096` until an action
   executes. Explicit `max_tokens` set by the harness is never overridden.

It never issues, blocks or re-counts an action. `valid_actions` still come from the harness; a game-over auto-RESET
keeps the level so the ledger persists; a level completion starts a fresh ledger.

## Install

Paste `probe_first_cell.py` as one code cell after "4. Import the bundled source" and before "9. Run the benchmark".
Check the log for `ARC3_PF_READY installed ... self_test=ok`. Stats print every 100 openers (`ARC3_PF_STATS`).

Knobs (env, set before the cell): `PF_NUDGE_AT=3`, `PF_CAP_AT=5`, `PF_CAP_TOKENS=4096`.

## Verify before submitting

Paired level trials (the A3 design, 183 (game, level) trials per arm, 20 min each), PF on vs off, two rounds.
Primary: levels cleared. Secondary: generated tokens per cleared level, share of tokens in no-action exchanges,
median agent/human action ratio on cleared levels (must stay below 0.9), deaths per level. Gate: +15% levels cleared
and McNemar p < 0.05 across the two rounds.
