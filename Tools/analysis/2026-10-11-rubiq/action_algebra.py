"""Do ARC-AGI-3 actions behave like group elements? Probe on the 25 public games.

RubiQ's machinery (compose and invert permutations, words over generators, parity) only
helps an ARC-AGI-3 agent if some games' actions act on game states like elements of a group:
each action has a finite order (repeating it returns to the start), has an inverse among
the available actions, and pairs commute or not in a structured way.

States probed: the start of every level that Franzen's best run of each game reached
(replaying its recorded history), snapshotted with copy.deepcopy (checked to be independent).
For each state s and each available action a (RESET excluded; ACTION6 at up to 8 click
targets = centres of same-colour components that are not the dominant colour):
  noop      a(s) == s
  hist      colour histogram of a(s) equals that of s
  order     smallest k <= 12 with a^k(s) == s (stop early on GAME_OVER / level change)
  inverse   some available non-click b (or ACTION7) with b(a(s)) == s
  commute   for non-click pairs, a(b(s)) == b(a(s))
Every comparison is done twice: on the full 64x64 grid ("exact") and on the interior
excluding a 4-cell border ("interior"), because several games draw a step bar on the edge.

Usage: python action_algebra.py BENCHMARK_JSON ENV_DIR OUT_JSON
Needs arc-agi==0.9.8, arcengine==0.9.3.
"""
from __future__ import annotations

import collections
import copy
import json
import logging
import sys

import numpy as np

logging.disable(logging.CRITICAL)
import arc_agi  # noqa: E402
from arcengine import GameAction, GameState  # noqa: E402

MAX_ORDER = 12
MAX_CLICKS = 8
BORDER = 4


def grid(f):
    return np.array(f.frame[-1]) if f.frame else None


def same(a, b, interior):
    if a is None or b is None or a.shape != b.shape:
        return False
    if interior:
        return np.array_equal(a[BORDER:-BORDER, BORDER:-BORDER], b[BORDER:-BORDER, BORDER:-BORDER])
    return np.array_equal(a, b)


def click_targets(g):
    vals, counts = np.unique(g, return_counts=True)
    bg = vals[np.argmax(counts)]
    seen = np.zeros(g.shape, bool)
    comps = []
    H, W = g.shape
    for y in range(H):
        for x in range(W):
            if seen[y, x] or g[y, x] == bg:
                continue
            col, stack, cells = g[y, x], [(y, x)], []
            seen[y, x] = True
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny, nx] and g[ny, nx] == col:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            cy = int(round(np.mean([c[0] for c in cells])))
            cx = int(round(np.mean([c[1] for c in cells])))
            if g[cy, cx] != col:          # non-convex blob: use a member cell
                cy, cx = cells[len(cells) // 2]
            comps.append((len(cells), cx, cy))
    comps.sort(reverse=True)
    return [{"x": cx, "y": cy} for _, cx, cy in comps[:MAX_CLICKS]]


def step(env, name, data=None):
    return env.step(GameAction[name], data=data)


def terminal(f, lv0):
    return f.state == GameState.GAME_OVER or f.levels_completed != lv0 or f.state == GameState.WIN


def probe_state(env, f0):
    s = grid(f0)
    lv0 = f0.levels_completed
    avail = [a for a in f0.available_actions if a != 0]
    nonclick = [f"ACTION{a}" for a in avail if a != 6]
    acts = [(n, None) for n in nonclick]
    if 6 in avail:
        acts += [("ACTION6", d) for d in click_targets(s)]
    out = []
    after = {}
    for name, data in acts:
        e = copy.deepcopy(env)
        f = step(e, name, data)
        g1 = grid(f)
        rec = dict(action=name, data=data, terminal_first=terminal(f, lv0),
                   noop_exact=same(g1, s, False), noop_interior=same(g1, s, True),
                   hist=bool(g1 is not None and np.array_equal(np.bincount(g1.ravel(), minlength=16),
                                                                np.bincount(s.ravel(), minlength=16))))
        after[(name, json.dumps(data))] = (e, f)
        for mode in ("exact", "interior"):
            interior = mode == "interior"
            order = None
            if not rec["terminal_first"] and not same(g1, s, interior):
                e2, fk = copy.deepcopy(e), f
                for k in range(2, MAX_ORDER + 1):
                    fk = step(e2, name, data)
                    if terminal(fk, lv0):
                        break
                    if same(grid(fk), s, interior):
                        order = k
                        break
            rec[f"order_{mode}"] = order
        out.append(rec)
    # inverses and commutation for non-click actions (plus ACTION7 as an inverse candidate)
    inv_cands = nonclick + (["ACTION7"] if 7 in avail and "ACTION7" not in nonclick else [])
    for rec in out:
        if rec["action"] == "ACTION6" or rec["terminal_first"] or rec["noop_exact"]:
            continue
        e, f = after[(rec["action"], json.dumps(rec["data"]))]
        for mode in ("exact", "interior"):
            interior = mode == "interior"
            inv = []
            for b in inv_cands:
                e2 = copy.deepcopy(e)
                fb = step(e2, b)
                if not terminal(fb, lv0) and same(grid(fb), s, interior):
                    inv.append(b)
            rec[f"inverses_{mode}"] = inv
    comm = []
    for i, a in enumerate(nonclick):
        for b in nonclick[i + 1:]:
            ea = copy.deepcopy(after[(a, "null")][0]); fab = step(ea, b)
            eb = copy.deepcopy(after[(b, "null")][0]); fba = step(eb, a)
            comm.append(dict(a=a, b=b, exact=same(grid(fab), grid(fba), False),
                             interior=same(grid(fab), grid(fba), True)))
    return dict(levels_completed=lv0, available=avail, actions=out, commute=comm)


def level_start_states(arc, run):
    """(env snapshot, frame) at reset and right after each level-completing action of `run`."""
    env = arc.make(run["game_id"], seed=0)
    f = env.reset()
    states = [(copy.deepcopy(env), f)]
    lv = f.levels_completed
    for h in run["history"]:
        a = h["action"]
        f = env.step(GameAction[a["id"]], data=a.get("data") or None)
        if f.levels_completed > lv and f.state != GameState.WIN:
            states.append((copy.deepcopy(env), f))
        lv = f.levels_completed
    return states, lv


def main(bench_path, env_dir, out_path):
    runs = json.load(open(bench_path))["game_runs"]
    best = {}
    for r in runs:
        g = r["game_id"]
        if g not in best or r["levels_completed"] > best[g]["levels_completed"]:
            best[g] = r
    arc = arc_agi.Arcade(operation_mode=arc_agi.OperationMode.OFFLINE, environments_dir=env_dir)
    results = {}
    for gid in sorted(best):
        r = best[gid]
        states, reached = level_start_states(arc, r)
        assert reached == r["levels_completed"], (gid, reached, r["levels_completed"])
        results[gid] = [probe_state(env, f) for env, f in states]
        print(gid, "levels probed", len(states), flush=True)
    json.dump(results, open(out_path, "w"), indent=1, default=str)


if __name__ == "__main__":
    main(*sys.argv[1:4])
