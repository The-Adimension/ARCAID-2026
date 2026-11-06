# RubiQ vs ARC-AGI-3: analysis of 2026-10-11

Reproduces every number in `memo-2026-10-11-rubiq.md`. Read-only on the uploaded RubiQ code (not imported, not executed); the probes run the pinned ARC-AGI-3 engine on the 25 public games.

## Environment

```
python3 -m venv venv && venv/bin/pip install arc-agi==0.9.8 arcengine==0.9.3 numpy sympy
```

Python 3.13 with these wheels reproduces Franzen's 100 demo runs exactly (`inputs/replay_benchmark.py` → mean 46.49).

## Run

```
cd analysis/2026-10-11-rubiq
B=../2026-10-10/data/dfranzen-m2-v3/benchmark.json
E=../../inputs/official-input-arc-prize-2026-arc-agi-3/environment_files
venv/bin/python rubiq_group.py                                 # RubiQ's group and module selection
venv/bin/python action_algebra.py $B $E algebra.json           # ~80 s: action orders, inverses, commutation on 143 level starts
python3 summarize_algebra.py algebra.json interior             # per-game summary (also: exact)
python3 crossref_stuck.py $B algebra.json interior             # stuck level attempts on levels with cyclic actions
python3 helper_reuse.py TRANSCRIPT_DIR $B                      # cross-game reuse of model-written helpers (needs the 100 transcripts)
venv/bin/python oracle_bfs.py $B $E bfs.json ar25:6 cn04:2 ...   # oracle search ceiling (4 levels per process, ~16 min)
```

`TRANSCRIPT_DIR`: the 100 `transcripts/*.txt` files from the output of public kernel `dfranzen/arc-agi-3-milestone-2-solution` v3 (`GET /api/v1/kernels/output`; 211 MB, not committed).

## Files

| File | Measures |
|---|---|
| `rubiq_group.py` | Generator parities, fixed points, orbits, group order (sympy), type mix and parameter count of every RubiQ active set, the same for `random_csi`. A torch-free copy of harness.py lines 138-250 and 258-271, 513-521. |
| `action_algebra.py` | For each level start that Franzen's best run reached: each action's no-op status, colour-histogram preservation, order (<= 12), inverses among available actions, pairwise commutation; exact grid and interior grid (4-cell border excluded). |
| `summarize_algebra.py` | Per-game classes and the share of live actions with finite order ("cyclic"). |
| `crossref_stuck.py` | How many of the stuck level attempts in the 4x25 run start on a level that has a cyclic action. |
| `helper_reuse.py` | Python functions the model defined in 9,271 tool calls; within-run redefinitions; exact and near-duplicate (bigram Jaccard >= 0.8) definitions across games; their token share. |
| `oracle_bfs.py` | Breadth-first search with the true engine (an oracle, not an agent) on the 16 stuck levels that have cyclic actions: is the goal reachable within 4,000 expansions, and how many distinct states appear. |
| `results/` | The outputs these scripts produced on 2026-10-11. |

## Bugs found and fixed before the numbers were used

- `summarize_algebra.py` first tested `"ACTION7" in available` against integer action ids, so UNDO always read "n/a". Fixed to `7 in available`.
- `helper_reuse.py` first built its item list with a leftover loop variable as the game label, so every definition looked like it came from the same game and no cross-game match could be found (0). It also cut candidates to the top 50 by shared bigrams, which can hide true matches. Both fixed (exact pre-filter |A∩B| >= 0.8|A| replaces the top-N cut); result 656 near-duplicates.

## Validity limits

- Public demo games only (easier than the hidden set and not representative of its mechanics, per ARC).
- Interior comparison excludes a 4-cell border. Checked: after a cycle completes in tr87 and ft09, the only differing cells are 3-4 cells of the bottom row (a step counter). Results on the exact grid are reported alongside.
- Click targets are centres of same-colour components (up to 8 in the probe, 12 in the oracle). A game whose key clicks are elsewhere is under-counted; seven oracle searches ended "exhausted" for this reason and are lower bounds.
- Token costs of helper definitions use characters/4.
