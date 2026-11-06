"""Summarise action_algebra.py output per game.

A non-click action is 'group-like' on a state if it is not a no-op, does not end the attempt,
has a finite order <= 12, and some available non-click action (or ACTION7) inverts it.
A game is 'group-like' if at least one non-click action is group-like on >= half of the
probed states; 'partial' if any action is group-like on any state; otherwise 'not'.
'cyclic_share' counts every live (not no-op, not terminal) action, clicks included, with a finite
order <= 12: such an action is invertible on its orbit (its inverse is itself repeated k-1 times).
'cyclic_levels' lists the 1-indexed levels whose start state has at least one such action.
Usage: python summarize_algebra.py ALGEBRA_JSON [interior|exact]
"""
from __future__ import annotations

import collections
import json
import statistics as st
import sys


def summarise(res, mode):
    rows = {}
    for gid, states in res.items():
        per_action = collections.defaultdict(lambda: [0, 0])  # action -> [group-like count, states seen]
        orders, n_click, click_order, click_hist, undo_ok, undo_seen = [], 0, 0, 0, 0, 0
        noop, total_nc, hist_nc, comm_t, comm_n = 0, 0, 0, 0, 0
        for s in states:
            for a in s["actions"]:
                if a["action"] == "ACTION6":
                    n_click += 1
                    click_order += a[f"order_{mode}"] is not None
                    click_hist += a["hist"]
                    continue
                total_nc += 1
                noop += a[f"noop_{mode}"]
                hist_nc += a["hist"]
                inv = a.get(f"inverses_{mode}", [])
                gl = (not a["terminal_first"] and not a[f"noop_{mode}"]
                      and a[f"order_{mode}"] is not None and bool(inv))
                per_action[a["action"]][0] += gl
                per_action[a["action"]][1] += 1
                if a[f"order_{mode}"] is not None:
                    orders.append(a[f"order_{mode}"])
                if 7 in s["available"] and a["action"] != "ACTION7" and not a[f"noop_{mode}"] and not a["terminal_first"]:
                    undo_seen += 1
                    undo_ok += "ACTION7" in inv
            for c in s["commute"]:
                comm_n += 1
                comm_t += c[mode]
        live = [a for s in states for a in s["actions"] if not a["terminal_first"] and not a[f"noop_{mode}"]]
        cyc = [a for a in live if a[f"order_{mode}"] is not None]
        cyclic_levels = [s["levels_completed"] + 1 for s in states
                         if any(a[f"order_{mode}"] is not None and not a["terminal_first"] and not a[f"noop_{mode}"]
                                for a in s["actions"])]
        n_states = len(states)
        best = max((v[0] / v[1] for v in per_action.values() if v[1]), default=0.0)
        anyg = any(v[0] for v in per_action.values())
        cls = "group-like" if best >= 0.5 else "partial" if anyg else "not"
        rows[gid[:4]] = dict(
            states=n_states, avail=sorted({x for s in states for x in s["available"]}),
            nonclick_actions=total_nc, noop=noop, hist_preserved=hist_nc,
            finite_order=len(orders), orders=dict(collections.Counter(orders)),
            group_like_by_action={k: f"{v[0]}/{v[1]}" for k, v in sorted(per_action.items())},
            clicks=n_click, clicks_finite_order=click_order, clicks_hist_preserved=click_hist,
            undo_restores=f"{undo_ok}/{undo_seen}" if undo_seen else "n/a",
            commuting_pairs=f"{comm_t}/{comm_n}" if comm_n else "n/a", cls=cls,
            cyclic_share=f"{len(cyc)}/{len(live)}", cyclic_levels=cyclic_levels)
    return rows


if __name__ == "__main__":
    res = json.load(open(sys.argv[1]))
    mode = sys.argv[2] if len(sys.argv) > 2 else "interior"
    rows = summarise(res, mode)
    for g, r in rows.items():
        print(g, json.dumps(r))
    c = collections.Counter(r["cls"] for r in rows.values())
    print(f"[{mode}] classes:", dict(c))
    print(f"[{mode}] states probed:", sum(r["states"] for r in rows.values()))
