# Directives: editing `policy.py`

`policy.py` is the only code you change, and it is exactly what the Kaggle
notebook runs on 110 games nobody has seen. Every rule below exists because
something that looked like progress on the 25 public games would score nothing
there.

## What policy.py is

- One file, standard-library Python, defining `MyAgent(Agent)` with
  `choose_action` and `is_done`. `submit.py` pastes it into the notebook verbatim.
- `python policy.py` runs `_self_check()`. It must pass after every edit.
- It sees only what the framework hands it: frames, available actions, level
  count, state. Nothing else.

## Identity isolation (the twin-blind check)

`assess.py` plays every game twice: once under its real id, once under a
scrambled one. The two games must produce **identical action traces**. If they
differ anywhere, the run scores `twin_blind=FAIL` and must be reverted.

So: never read, branch on, seed on, or hash the game id, the game title, or
anything derived from them. A policy that recognises a game cannot recognise a
game it has never seen.

## No transcribed answers

Teaching rounds show you exactly how a level was won. Do **not** copy that into
the code:
- no stored action sequences or click coordinates from your play;
- no board fingerprints (hashes, digests or pixel templates of a specific
  board) used to trigger special behaviour;
- no constants that only make sense for one game (a colour number, a
  position, a step count found by playing it).

Encode the **mechanism** instead: how to recognise the situation from the frame,
and what to do about it in general. The hold games are the check. A
principle that raises `dev_score` but not `hold_score` has probably memorised
something.

## Static scan

`assess.py` refuses a policy whose executable code (comments and docstrings
excluded) mentions a game id, the game files, file or network access, or
dynamic imports. The list is in `ground.json` under `assess.forbidden_in_policy`.

## Budgets

- Kaggle gives one 9-hour run for about 110 games at up to 1200 actions each:
  roughly 0.2 s per action, shared with the game engine. Keep a decision well
  under 50 ms on average. Watch `seconds` in the assess report.
- Local model calls, network, GPUs: not available inside the notebook. Anything
  you teach has to become plain code.

## How to change it

1. One focused change per iteration, tied to one principle in
   `memory/principles.md`.
2. Prefer changes that add a capability the program lacks (recognising a
   goal, a new kind of control, a smarter order of trying things) over tuning
   numbers: tuned numbers are what failed to transfer before.
3. If two versions score the same, keep the shorter one.
4. Leave a comment at the change naming the principle and the run_id that
   measured it, the way the existing code cites its lab results.
