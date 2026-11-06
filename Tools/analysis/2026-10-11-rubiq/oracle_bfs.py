"""Ceiling check: are the stuck levels with cyclic actions small, exactly plannable puzzles?

ORACLE, NOT AN AGENT: breadth-first search over real engine snapshots (copy.deepcopy), so it
uses the game's true dynamics, which no competition agent has. It answers one question: if an
agent had induced an exact model of the actions (the premise of a group/Cayley-graph planner),
would search find the level's goal, and how long is the shortest plan vs the human baseline?

Moves: every available non-click action, plus ACTION6 at the centres of up to MAX_CLICKS
same-colour components (non-dominant colour) of each state. States are deduplicated on the
interior grid (4-cell border excluded: step counters live there). Search stops at the first
state whose levels_completed increases, after MAX_STATES expansions, or after MAX_SECONDS.

Usage: python oracle_bfs.py BENCHMARK_JSON ENV_DIR OUT_JSON game:level [game:level ...]
"""
from __future__ import annotations

import collections
import copy
import json
import logging
import sys
import time

import numpy as np

logging.disable(logging.CRITICAL)
import arc_agi  # noqa: E402
from arcengine import GameAction, GameState  # noqa: E402

sys.path.insert(0, __import__("os").path.dirname(__file__))
from action_algebra import click_targets, level_start_states  # noqa: E402

MAX_STATES = 4000
MAX_SECONDS = 240
MAX_CLICKS = 12
BORDER = 4


def key(f):
    g = np.array(f.frame[-1])
    return g[BORDER:-BORDER, BORDER:-BORDER].tobytes()


def moves(f):
    out = [(f"ACTION{a}", None) for a in f.available_actions if a not in (0, 6, 7)]
    if 6 in f.available_actions:
        out += [("ACTION6", d) for d in click_targets(np.array(f.frame[-1]))[:MAX_CLICKS]]
    return out


def bfs(env0, f0):
    lv0 = f0.levels_completed
    seen = {key(f0)}
    q = collections.deque([(env0, f0, 0)])
    expanded = 0
    t0 = time.time()
    while q:
        if expanded >= MAX_STATES or time.time() - t0 > MAX_SECONDS:
            return dict(solved=False, reason="budget", expanded=expanded, seen=len(seen))
        env, f, d = q.popleft()
        expanded += 1
        for name, data in moves(f):
            e = copy.deepcopy(env)
            g = e.step(GameAction[name], data=data)
            if g.levels_completed > lv0 or g.state == GameState.WIN:
                return dict(solved=True, length=d + 1, expanded=expanded, seen=len(seen))
            if g.state == GameState.GAME_OVER:
                continue
            k = key(g)
            if k in seen:
                continue
            seen.add(k)
            q.append((e, g, d + 1))
    return dict(solved=False, reason="exhausted", expanded=expanded, seen=len(seen))


def main(bench, env_dir, out, targets):
    runs = json.load(open(bench))["game_runs"]
    best = {}
    for r in runs:
        g = r["game_id"][:4]
        if g not in best or r["levels_completed"] > best[g]["levels_completed"]:
            best[g] = r
    arc = arc_agi.Arcade(operation_mode=arc_agi.OperationMode.OFFLINE, environments_dir=env_dir)
    res = {}
    for t in targets:
        g, lv = t.split(":")
        lv = int(lv)
        r = best[g]
        states, _ = level_start_states(arc, r)
        env, f = states[lv - 1]
        assert f.levels_completed == lv - 1, (t, f.levels_completed)
        out_r = bfs(env, f)
        out_r["human_baseline"] = r["base_actions_per_level"][lv - 1]
        res[t] = out_r
        print(t, json.dumps(out_r), flush=True)
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])
