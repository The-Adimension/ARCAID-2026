"""Old rule kinds (../2026-10-07__lexicon-code/effect_code.py) against the rule grammar (rule_grammar.py).

Two test beds, one procedure:
  public   the 25 public games: 55 recorded agent plays (4 save runs) replayed on the official engine
  worlds   20 generated games (worlds.py), 2 layouts each, 150 actions per layout chosen by a
           game-agnostic explorer: a uniformly random available action; a click lands on a random
           object the lexicon sees (70%) or on a random pixel (30%)

Both learners read the same lexicon screens (per-level scale lock). Before every step each is
re-learned from the level's earlier steps only, predicts the step, and is judged on it:
  right      predictions that came true / predictions made
  explained  changes on screen that a true prediction accounts for / changes
  exact      steps where every prediction came true and every change was predicted (closed world:
             no prediction = nothing changes)
The changes are the grammar's events (rule_grammar.observe); the old code's expectations are matched
against the same events. A change counts as explained only if the prediction specifies it fully
(where it moves, which colours it takes, which picture it becomes, where it appears). "X moves" or
"the clicked object changes" is right if it happens but does not explain the next screen; that
looser count is reported separately ("any").

Needs Python 3.12 with arc-agi==0.9.8, arcengine==0.9.3. From the repo root:
  python design/2026-10-07__rule-grammar/run_compare.py [workers] [public|worlds|all]
"""
from __future__ import annotations

import collections
import json
import logging
import pathlib
import random
import sys
from multiprocessing import Pool

logging.disable(logging.CRITICAL)
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "design/2026-10-07__lexicon-code"))
import effect_code as ec  # noqa: E402
import rule_grammar as G  # noqa: E402

LX = G.LX
ENV_DIR = ROOT / "inputs/official-input-arc-prize-2026-arc-agi-3/environment_files"
RUNS = {
    "sheetu-4.17": "submissions/2026-09-30__taaf-flashnext-sheetu12b-0922__v1__score-4.17/outputs/benchmark.json",
    "dfranzen-v1": "external_submission/2026-09-30__dfranzen__arc-agi-3-milestone-2-solution__v1__teambest-27.89/outputs/benchmark.json",
    "lexicon-dfranzen-v1": "experiments/2026-10-05__arcaid3-lexicon-view-dfranzen-m2__v1__unsubmitted__offline10-41.13/outputs/benchmark.json",
    "lexicon-dfranzen-v2": "experiments/2026-10-07__arcaid3-lexicon-view-dfranzen-m2__v2__unsubmitted__offline10-42.61/outputs/benchmark.json",
}
CHANGE = ("recolor", "reshape", "turn", "resize", "vanish")
SEEDS, STEPS = (0, 1), 150


def judge_new(preds, click, events):
    """(right, predictions, changes explained fully, changes accounted for at all)."""
    right, full, loose = 0, set(), set()
    for _, i, eff in preds:
        ks = {k for k, e in enumerate(events) if G.matches(eff, i, e, click)}
        right += bool(ks)
        loose |= ks
        if eff[0] != "resize" and not (eff[0] == "appear" and eff[2][0] == "somewhere"):
            full |= ks
    return right, len(preds), full, loose


def judge_old(expectations, events, clicked, by_kind=None):
    """The old code's expectations, matched against the grammar's events (same returns as judge_new)."""
    right, full, loose = 0, set(), set()
    for rule, exp in expectations:
        kind = exp[0]
        ks, ok = set(), False
        if kind == "move":
            ks = {k for k, e in enumerate(events) if e["verb"] == "move" and e["sym"] == exp[1] and e["d"] == exp[2]}
        elif kind == "stay":
            ok = not any(e["verb"] == "move" and e["sym"] == exp[1] for e in events)
        elif kind == "nothing":
            ok = not events
        elif kind == "clicked_changes":
            ks = {k for k, e in enumerate(events) if e.get("obj") == clicked and clicked is not None and e["verb"] in CHANGE}
        elif kind == "verb":
            ks = {k for k, e in enumerate(events) if e["verb"] == exp[1] and e["sym"] == exp[2]}
        elif kind == "scroll":
            ks = {k for k, e in enumerate(events) if e["verb"] == "move" and e["d"] == exp[1]}
        right += ok or bool(ks)
        loose |= ks
        if kind in ("move", "scroll") or (kind == "verb" and exp[1] == "vanish"):
            full |= ks
        if by_kind is not None:
            for k in ks:
                by_kind.setdefault(k, rule.kind)
    return right, len(expectations), full, loose


class Tracker:
    """Reads one play screen by screen and scores both learners online, level by level."""

    def __init__(self):
        self.lex = LX.Lexicon(naming="stable")
        self.level = None
        self.tot = {"old": collections.Counter(), "new": collections.Counter()}
        self.both = collections.Counter()
        self.levels = []

    def start(self, frame, level):
        self.close()
        self.level, self.frames = level, [frame]
        self.prev = G.State(LX.encode(frame, self.lex, lock=LX.scale_lock(self.frames)))
        self.new, self.old_hist, self.n_steps = G.Learner(), [], 0

    def step(self, action, data, frame, level):
        if level != self.level:
            self.start(frame, level)
            return
        self.frames.append(frame)
        lock = LX.scale_lock(self.frames)
        prev = self.prev
        cur = G.State(LX.encode(frame, self.lex, lock=lock, prev=prev.code))  # prev: cut merged objects apart
        if (prev.code["scale"], prev.code["offset"]) != (cur.code["scale"], cur.code["offset"]):
            prev = G.State(LX.encode(self.frames[-2], self.lex, lock=lock))     # same grid for both screens
            cur = G.State(LX.encode(frame, self.lex, lock=lock, prev=prev.code))
        if action != "RESET":
            click = (data["x"], data["y"]) if action == "ACTION6" and data else None
            events = G.observe(prev, cur)
            preds, crc = G.predict(self.new.rules(), prev, action, click)
            rn, nn, exn, lon = judge_new(preds, crc, events)
            ev_old, hit = ec.events(prev.code, cur.code, click)
            rules_old = ec.induce(self.old_hist)
            clicked = prev.object_at(prev.cell_of(*click)) if click else None
            kinds = {}
            ro, no, exo, loo = judge_old(ec.predict(rules_old, action, hit, code=prev.code), events, clicked, kinds)
            for arm, r, n, ex, lo in (("new", rn, nn, exn, lon), ("old", ro, no, exo, loo)):
                t = self.tot[arm]
                t["right"] += r
                t["pred"] += n
                t["explained"] += len(ex)
                t["any"] += len(lo)
                t["exact"] += r == n and len(ex) == len(events)
            self.tot["new"]["events"] += len(events)
            self.tot["old"]["events"] += len(events)
            self.tot["new"]["steps"] += 1
            self.tot["old"]["steps"] += 1
            self.both["both"] += len(exn & exo)
            self.both["old_only"] += len(exo - exn)
            self.both["new_only"] += len(exn - exo)
            for k in exo - exn:
                self.both[f"old_only:{kinds[k]}"] += 1
            for k in exo & exn:
                self.both[f"both:{kinds[k]}"] += 1
            for k in exn - exo:
                self.both[f"new_only:{events[k]['verb']}"] += 1
            self.new.observe(prev, action, click, events)
            self.old_hist.append((action, ev_old, hit, ec.contact(prev.code, rules_old, action, ev_old)))
            self.n_steps += 1
        self.prev = cur

    def close(self):
        if self.level is None or not self.n_steps:
            return
        rules = self.new.rules()
        self.levels.append({"level": self.level, "steps": self.n_steps,
                            "new": [r.line() for r in rules],
                            "new_named": sum(r.uses_names() for r in rules), "new_rules": len(rules),
                            "residual": len(self.new.residual()),
                            "events": sum(len(s.events) for s in self.new.steps),
                            "old": [r.line() for r in ec.induce(self.old_hist)]})

    def report(self, **meta):
        self.close()
        self.level = None
        return dict(meta, tot={k: dict(v) for k, v in self.tot.items()}, both=dict(self.both), levels=self.levels)


def frame_of(f):
    fr = f.frame[-1]
    return fr.tolist() if hasattr(fr, "tolist") else fr


def run_public(args):
    run, gid, acts = args
    import arc_agi
    from arcengine import GameAction
    arc = arc_agi.Arcade(operation_mode=arc_agi.OperationMode.OFFLINE, environments_dir=str(ENV_DIR))
    env = arc.make(gid, seed=0)
    f = env.reset()
    game = env._game
    T = Tracker()
    T.start(frame_of(f), game.level_index)
    for name, data in acts:
        f = env.step(GameAction[name], data=data)
        T.step(name, data, frame_of(f), game.level_index)
        if str(f.state).endswith("WIN"):
            break
    return T.report(bed="public", run=run, game=gid[:4])


def run_world(args):
    spec, seed = args
    import worlds
    from arcengine import ActionInput, GameAction, GameState
    g = worlds.make(spec, seed)
    rng = random.Random(f"explorer-{spec['id']}-{seed}")
    f = g.perform_action(ActionInput(id=GameAction.RESET))
    T = Tracker()
    T.start(frame_of(f), 0)
    t = 0
    while t < STEPS:
        if f.state in (GameState.GAME_OVER, GameState.WIN):
            f = g.perform_action(ActionInput(id=GameAction.RESET))
            T.step("RESET", None, frame_of(f), 0)
            continue
        a = rng.choice(g._available_actions)
        data = {}
        if a == 6:
            if T.prev.free and rng.random() < 0.7:
                p = T.prev.objs[rng.choice(T.prev.free)]
                r, c = rng.choice(p["cells"])
                x, y = LX.display_xy(T.prev.code, r, c)
            else:
                x, y = rng.randrange(64), rng.randrange(64)
            data = {"x": x, "y": y}
        f = g.perform_action(ActionInput(id=GameAction[f"ACTION{a}"], data=data))
        T.step(f"ACTION{a}", data, frame_of(f), 0)
        t += 1
    return T.report(bed="worlds", game=spec["id"], seed=seed, note=spec["note"])


def public_jobs():
    for run, path in RUNS.items():
        for g in json.load(open(ROOT / path))["game_runs"]:
            acts = [(h["action"]["id"], h["action"].get("data") or None) for h in (g.get("history") or [])]
            if acts:
                yield run, g["game_id"], acts


def pct(a, b):
    return f"{100 * a / b:5.1f}%" if b else "   - "


def summarise(results, title):
    lines = [f"== {title}"]
    tot = {"old": collections.Counter(), "new": collections.Counter()}
    both = collections.Counter()
    named = rules = 0
    for r in results:
        for arm in tot:
            tot[arm].update(r["tot"][arm])
        both.update(r["both"])
        named += sum(l["new_named"] for l in r["levels"])
        rules += sum(l["new_rules"] for l in r["levels"])
    lines.append(f"{'':10s} {'predictions right':>22s} {'changes explained':>22s} {'steps exact':>18s} {'changes, any':>16s}")
    for arm, label in (("old", "old kinds"), ("new", "grammar")):
        t = tot[arm]
        lines.append(f"{label:10s} {pct(t['right'], t['pred']):>8s} ({t['right']}/{t['pred']})".ljust(34)
                     + f"{pct(t['explained'], t['events']):>8s} ({t['explained']}/{t['events']})".ljust(24)
                     + f"{pct(t['exact'], t['steps']):>8s} ({t['exact']}/{t['steps']})".ljust(20)
                     + f"{pct(t['any'], t['events']):>8s}")
    lines.append(f"changes explained by both: {both['both']}; by the old kinds only: {both['old_only']}; "
                 f"by the grammar only: {both['new_only']}")
    kinds = sorted({k.split(":")[1] for k in both if k.startswith(("old_only:", "both:"))})
    lines.append("  by old rule kind (also explained by the grammar / old kinds only): " + "; ".join(
        f"{k} {both.get('both:' + k, 0)}/{both.get('old_only:' + k, 0)}" for k in kinds))
    verbs = sorted((k.split(":")[1] for k in both if k.startswith("new_only:")), key=lambda v: -both["new_only:" + v])
    lines.append("  grammar only, by verb: " + "; ".join(f"{v} {both['new_only:' + v]}" for v in verbs))
    lines.append(f"final grammar rules: {rules}, of which {rules - named} name no picture ({pct(rules - named, rules).strip()})")
    return lines, tot, both


def per_game(results):
    lines = ["", f"{'game':6s} {'note':44s} {'old: right / explained':>24s} {'grammar: right / explained / exact':>36s}"]
    by = collections.defaultdict(lambda: {"old": collections.Counter(), "new": collections.Counter()})
    notes = {}
    for r in results:
        for arm in ("old", "new"):
            by[r["game"]][arm].update(r["tot"][arm])
        notes[r["game"]] = r.get("note", "")
    for g in sorted(by):
        o, n = by[g]["old"], by[g]["new"]
        lines.append(f"{g:6s} {notes[g][:44]:44s} {pct(o['right'], o['pred']):>8s} / {pct(o['explained'], o['events']):>7s}      "
                     f"{pct(n['right'], n['pred']):>8s} / {pct(n['explained'], n['events']):>7s} / {pct(n['exact'], n['steps']):>7s}")
    return lines


def listings(results, max_levels=1):
    lines, seen = [], set()
    for r in sorted(results, key=lambda r: (r["game"], r.get("seed", 0), r.get("run", ""))):
        for lv in r["levels"][:max_levels]:
            key = (r["game"], lv["level"])
            if key in seen:
                continue
            seen.add(key)
            src = r.get("run") or f"layout {r.get('seed')}"
            lines.append(f"-- {r['game']} level {lv['level'] + 1} ({lv['steps']} steps, {src}); "
                         f"residual {lv['residual']} of {lv['events']} changes")
            lines += ["   grammar: " + l for l in lv["new"]] or ["   grammar: (no rule)"]
            lines += ["   old:     " + l for l in lv["old"]] or ["   old:     (no rule)"]
    return lines


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    which = sys.argv[2] if len(sys.argv) > 2 else "all"
    import worlds
    out, report = [], {}
    with Pool(workers) as pool:
        if which in ("worlds", "all"):
            res = pool.map(run_world, [(s, seed) for s in worlds.SPECS for seed in SEEDS], chunksize=1)
            lines, tot, both = summarise(res, f"generated worlds: {len(worlds.SPECS)} games x {len(SEEDS)} layouts x {STEPS} actions")
            out += lines + per_game(res) + ["", "rules at the end (layout 0):"] + listings([r for r in res if r["seed"] == 0])
            report["worlds"] = res
            out.append("")
        if which in ("public", "all"):
            res = pool.map(run_public, list(public_jobs()), chunksize=1)
            lines, tot, both = summarise(res, f"public games: {len(res)} recorded plays")
            out += lines + per_game(res) + ["", "rules at the end of level 1 (first play per game):"] + listings(res)
            report["public"] = res
    name = "run_compare" if which == "all" else f"run_compare_{which}"
    (HERE / f"{name}.out").write_text("\n".join(out) + "\n")
    (HERE / f"{name}.json").write_text(json.dumps(report, indent=1, default=str))
    print("\n".join(out[:80]))


if __name__ == "__main__":
    main()
