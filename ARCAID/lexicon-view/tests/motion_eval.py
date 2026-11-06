"""Motion view: grade the lexicon's "what moved" reading against the engine, and
build the per-game data dictionary (symbol -> what actions do to it) from plays.

Plays replayed on the official public games (pinned engine):
  agent   the 25 game histories of the 4.17 notebook's save run
          (submissions/2026-09-30__taaf-flashnext-sheetu12b-0922__v1__score-4.17/outputs/benchmark.json)
  local   inputs/local_play/*/full_actions.json (the real records; the fake summary.json WINs are not used)
  recordings  inputs/local_play/recordings/**/*.jsonl with more than 2 lines (2-line files are the
          refuted fake WINs)

At every action, from the screens alone, `lexicon.diff` reports moved objects.
The engine's sprite positions (evaluation only) say which sprites really moved.
  precision  reported moves that land on a sprite which really moved by that amount
  recall     visible sprites that really moved and were reported as a move

The dictionary (written to results/dictionary_<game>.md) is built from the
screens only: for each symbol, how often each action moved it and by how much.

Usage (Python 3.12, arc-agi==0.9.8, arcengine==0.9.3), from the repo root:
  python arcaid3/part2/motion_eval.py
"""
from __future__ import annotations

import collections
import json
import os
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import groundtruth as gt  # noqa: E402
import lexicon as lx  # noqa: E402

REPO = gt.REPO
OUT = HERE / "results"
AGENT_RUN = REPO / "submissions/2026-09-30__taaf-flashnext-sheetu12b-0922__v1__score-4.17/outputs/benchmark.json"
LOCAL = REPO / "inputs/local_play"
SAMPLE_GAMES = ("ft09", "sb26", "ls20", "vc33", "cd82", "tu93")


def plays():
    bench = json.load(open(AGENT_RUN))
    for run in bench["game_runs"]:
        acts = [(h["action"]["id"], h["action"].get("data") or None) for h in (run.get("history") or [])]
        if acts:
            yield "agent", run["game_id"][:4], acts
    for g in sorted(os.listdir(LOCAL)):
        p = LOCAL / g / "full_actions.json"
        if p.exists():
            acts = [(a["id"] if isinstance(a["id"], str) else f"ACTION{a['id']}",
                     {"x": a["x"], "y": a["y"]} if "x" in a else None) for a in json.load(open(p))]
            yield "local", g, acts
    # official-format recordings; the 2-line files are the refuted fake WINs and are skipped
    for path in sorted((LOCAL / "recordings").rglob("*.jsonl")):
        lines = [json.loads(x) for x in open(path)]
        if len(lines) <= 2:
            continue
        acts = [(e["data"]["action_input"]["id"], e["data"]["action_input"].get("data") or None)
                for e in lines[1:]]
        yield "recordings", lines[0]["data"]["game_id"][:4], acts


def sprite_state(game):
    return {id(s): (s.x, s.y, bool(s.is_visible)) for s in game.current_level.get_sprites()}


def run_play(arc, gid, acts, stats, roles):
    from arcengine import GameAction
    env = arc.make(gid, seed=0)
    f = env.reset()
    game = env._game
    lex = lx.Lexicon()
    prev_code = lx.encode(np.array(f.frame[-1]).tolist(), lex)
    prev_state, prev_level = sprite_state(game), game.level_index
    for name, data in acts:
        ga = GameAction.from_name(name) if hasattr(GameAction, "from_name") else GameAction[name]
        f = env.step(ga, data=data)
        frame = np.array(f.frame[-1], dtype=np.int16)
        code = lx.encode(frame.tolist(), lex)
        state, level = sprite_state(game), game.level_index
        stats["steps"] += 1
        om = gt.owner_map(game)
        comparable = (level == prev_level and name != "RESET" and (om["colours"] == frame).all()
                      and code["scale"] == om["camera_scale"] == prev_code["scale"]
                      and code["offset"] == prev_code["offset"])
        d = lx.diff(prev_code, code)
        for sym, (r0, c0), (r1, c1) in d["moved"]:
            roles[sym][name][(r1 - r0, c1 - c0)] += 1
        for s0, s1, _ in d["became"]:
            roles[s0][name][f"became {s1}"] += 1
        if not d["moved"] and not d["became"] and not d["appeared"] and not d["disappeared"]:
            roles["_screen"][name]["no object change"] += 1
        if comparable:
            stats["comparable_steps"] += 1
            sprites = list(game.current_level.get_sprites())
            moved_gt = {}
            for sid, (x, y, vis) in state.items():
                if sid in prev_state and vis and prev_state[sid][2] and (x, y) != prev_state[sid][:2]:
                    moved_gt[sid] = (y - prev_state[sid][1], x - prev_state[sid][0])
            k, (oy, ox) = code["scale"], code["offset"]
            owners = om["owners"]
            bg_display = code["background"]
            # visible moved sprites (recall denominator)
            visible_moved = set()
            for i, s in enumerate(sprites):
                if id(s) in moved_gt and ((owners == i) & (frame != bg_display)).any():
                    visible_moved.add(id(s))
            stats["gt_moved_visible"] += len(visible_moved)
            hit = set()
            at_cells = {p["at"]: p for p in code["placed"]}
            for sym, (r0, c0), (r1, c1) in d["moved"]:
                stats["reported_moves"] += 1
                p = at_cells.get((r1, c1))
                if p is None:
                    continue
                own = collections.Counter()
                for r, c in p["cells"]:
                    o = owners[oy + r * k: oy + (r + 1) * k, ox + c * k: ox + (c + 1) * k].ravel()
                    own.update(int(v) for v in o if v >= 0)
                if not own:
                    continue
                s = sprites[own.most_common(1)[0][0]]
                if moved_gt.get(id(s)) == (r1 - r0, c1 - c0):
                    stats["correct_moves"] += 1
                    hit.add(id(s))
            stats["gt_moved_hit"] += len(hit & visible_moved)
        prev_code, prev_state, prev_level = code, state, level
        if str(f.state).endswith("WIN"):
            break


def dictionary_text(game, roles, lex_sizes):
    lines = [f"# Data dictionary for {game} (built from screens only)", "",
             "Each row: a lexicon symbol, then what each action did to it during the replayed plays.",
             "Moves are (rows, cols) in native cells; counts in brackets.", ""]
    screen = roles.pop("_screen", {})
    for sym in sorted(roles, key=lambda s: -sum(sum(c.values()) for c in roles[s].values()))[:25]:
        parts = []
        for act, moves in sorted(roles[sym].items()):
            top = ", ".join(f"{m}[{n}]" for m, n in moves.most_common(3))
            parts.append(f"{act}: {top}")
        reading = lx.read_roles(roles[sym])
        lines.append(f"- **{sym}**: " + "; ".join(parts)
                     + (f"  \n  reading: {'; '.join(reading)}" if reading else ""))
    if screen:
        lines += ["", "Actions after which no object changed: " +
                  ", ".join(f"{a} x{c['no object change']}" for a, c in sorted(screen.items()))]
    lines += ["", f"Symbols in this game's lexicon: {lex_sizes}"]
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    arc = gt.arcade()
    ids = gt.game_ids(arc)
    by_source = collections.defaultdict(collections.Counter)
    by_game = collections.defaultdict(collections.Counter)
    for source, g, acts in plays():
        stats = collections.Counter()
        roles = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
        run_play(arc, ids[g], acts, stats, roles)
        by_source[source].update(stats)
        by_game[f"{source}:{g}"].update(stats)
        if g in SAMPLE_GAMES and source == ("local" if g in ("ft09", "cd82", "tu93", "vc33") else "agent"):
            (OUT / f"dictionary_{g}.md").write_text(dictionary_text(g, roles, len(roles)))
        print(source, g, dict(stats), flush=True)

    def rates(c):
        return {
            "steps": c["steps"], "comparable_steps": c["comparable_steps"],
            "reported_moves": c["reported_moves"], "correct_moves": c["correct_moves"],
            "precision": round(c["correct_moves"] / max(1, c["reported_moves"]), 4),
            "gt_moved_visible": c["gt_moved_visible"], "gt_moved_hit": c["gt_moved_hit"],
            "recall": round(c["gt_moved_hit"] / max(1, c["gt_moved_visible"]), 4),
        }

    total = collections.Counter()
    for c in by_source.values():
        total.update(c)
    report = {"all": rates(total), "by_source": {k: rates(v) for k, v in by_source.items()},
              "by_play": {k: rates(v) for k, v in sorted(by_game.items())}}
    (OUT / "motion_eval.json").write_text(json.dumps(report, indent=1, sort_keys=True))
    print(json.dumps({"all": report["all"], "by_source": report["by_source"]}, indent=1))


if __name__ == "__main__":
    main()
