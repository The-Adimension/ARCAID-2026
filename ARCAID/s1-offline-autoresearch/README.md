# arc3-autoresearch

An autoresearch loop for the ARC Prize 2026 ARC-AGI-3 Kaggle competition, where
the thing being improved is an **offline game-playing program**, and the thing
improving it is an AI agent that first **plays the games itself**.

It combines two earlier loops:

- [karpathy/autoresearch](https://github.com/karpathy/autoresearch), via
  [habanwer/autoresearch-MIL](https://github.com/habanwer/autoresearch-MIL): a
  human-owned `program.md` and `ground.json`, one agent-owned file, an append-only
  results log, memory that persists between runs, and git keep-or-revert.
- [The-Adimension/Agent-ProSAT](https://github.com/The-Adimension): one mutable
  solver, a locked assessor with a **twin-blind** check, and directives that forbid
  the solver from seeing the answer.

## Why

A frontier model playing through a plain text interface finishes ARC-AGI-3
levels at human pace (vc33: 3 levels in 5, 7 and 23 actions, human 7, 18 and 44).
It cannot run inside the Kaggle notebook: no internet, and the open models that
fit on a Kaggle GPU cannot yet use the same interface (see `memory/MEMORY.md`).

So the agent does the understanding, and the program does the playing:

```
        +-------------------- a round --------------------+
        |                                                 |
  teach |  agent plays a dev game via play.py             |
        |        (stable object ids, board image,         |
        |         the competition score per level)        |
        v                                                 |
reflect |  agent writes why it won: memory/games, principles.md
        v                                                 |
distill |  agent turns ONE general principle into code    |
        |        in policy.py (no game ids, no copied moves)
        v                                                 |
 assess |  assess.py: all 25 games, real score, twin blind |
        v                                                 |
   keep |  hold score held, dev score or teacher parity up? |
        |        yes: keep and log    no: git reset       |
        v                                                 |
   gate |  submit.py: gates pass -> ask the human -> push  |
        +--------------------------------------------------+
```

The measure of success is **teacher parity**: the program finishing, on its own,
the levels the agent finished while teaching. Hold games, never taught, check that
what was distilled transfers.

## Files

| File | Owner | What it is |
|---|---|---|
| `program.md` | human | The agent's instructions: the round, the keep rule, the gates |
| `directives.md` | human | Rules for editing `policy.py` (isolation, no copied answers, budgets) |
| `ground.json` | human | Paths, the fixed dev/hold split, budgets, submission gates |
| `prepare.py` | human | Offline game access and the competition scoring formula; `python prepare.py` is the preflight |
| `play.py` | human | The teacher's interface: stateless, replayable, scored |
| `perception.py` | human | Frozen perception for `play.py`, so the teacher's view never drifts |
| `assess.py` | human | The locked judge: real score, teacher parity, twin blind, static scan |
| `submit.py` | human | Builds the notebook from `policy.py`; pushes only through the gates |
| `policy.py` | **agent** | The offline player. The only code the agent edits |
| `memory/` | agent | Principles, per-game notes, and the logs of every round and push |
| `results.tsv` | agent | Append-only log of every change to `policy.py` |

## Quick start

Requires the sibling [ARC-AGI-3-Kaggle-Starter](../ARC-AGI-3-Kaggle-Starter)
install (its `.venv`, vendored framework and `environment_files`); paths are in
`ground.json`.

```bash
PY=../ARC-AGI-3-Kaggle-Starter/.venv/Scripts/python.exe
$PY prepare.py              # preflight: must end with "preflight OK"
$PY assess.py --quick       # a fast read of the current policy
$PY assess.py               # the full judge (~3 min)
$PY play.py vc33 --player me --round r001   # teach: shows decision 1
$PY submit.py               # build the notebook and check the gates (never pushes)
```

## Running the agent

Open Claude Code (or any coding agent) in this folder and say:

```
Read program.md, then run round r001.
```

It will play, write memory, change `policy.py`, measure, keep or revert, and stop
to ask you before anything is pushed to Kaggle.

## Honest limits

- Teaching needs a capable agent: in our tests, small local models did not reach
  useful play through this interface.
- 25 public games are a small, biased sample of the 110 hidden ones. The hold
  split is necessary and not sufficient.
- The score counts the agent's RESET actions; the official scorer may differ by
  about one action per life.

## License

MIT
