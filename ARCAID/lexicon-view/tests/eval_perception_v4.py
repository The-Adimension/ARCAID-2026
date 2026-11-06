"""Grade the three v4 perception fixes on real play, against the engine (evaluation only).

Replays the 45 recorded agent plays used to grade the v2 scale lock (eval_scale_lock.py) on the
official games and reads every screen twice:
  v3   the lexicon as shipped in notebook v3: scale lock without the finer-grid check, diff that
       pairs look-alikes into moves before checking places, no carving
  v4   lock with the finer-grid check; diff checks identity by place first; pieces that merged
       objects seen apart on the previous frame are carved back (object permanence)

Per step, for each reading (steps that stay on one level, are not RESET, and pass the engine's
render check):
  changes right   reported changes whose object belongs to an engine sprite that really changed
                  (moved, appeared, vanished, or changed pixels, rotation, mirroring or scale);
                  changes on cells no sprite owns (the interface layer: bars, counters) are
                  counted apart and not graded
  moves right     reported moves that land on a sprite which really moved by that amount
  move recall     visible sprites that really moved and were reported as moved
  flips           (block size, offset) changed from the previous frame of the same level
  camera match    block size equals the engine camera's scale

Needs Python 3.12 with arc-agi==0.9.8, arcengine==0.9.3 and numpy. From the repo root:
  python kaggle/lexicon-dfranzen/eval_perception_v4.py [workers]   # writes eval_perception_v4.json
"""
from __future__ import annotations

import collections
import json
import logging
import pathlib
import sys
from multiprocessing import Pool

import numpy as np

logging.disable(logging.CRITICAL)
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
_argv, sys.argv = sys.argv, sys.argv[:1]
import eval_scale_lock as base  # noqa: E402  (reads argv at import)
sys.argv = _argv
ARMS = ("v3", "v4")
import os  # noqa: E402
# identity-by-place mode for the v4 arm: "all", "shared" (pictures with several copies only) or "off"
PLACE = {"all": True, "shared": "shared", "off": False}[os.environ.get("ARCAID3_PLACE", "shared")]


def sprite_state(s):
    return (s.x, s.y, bool(s.is_visible), getattr(s, "_rotation", 0), s.mirror_ud, s.mirror_lr, s.scale, s.pixels.tobytes())


def owners_of(code, cells, owners):
    k, (oy, ox) = code["scale"], code["offset"]
    out = set()
    for r, c in cells:
        block = owners[oy + r * k: oy + (r + 1) * k, ox + c * k: ox + (c + 1) * k].ravel()
        out.update(int(v) for v in block if v >= 0)
    return out


def run_play(args):
    run, gid, acts = args
    import arc_agi
    from arcengine import GameAction
    lx = base.load_lexicon()
    arc = arc_agi.Arcade(operation_mode=arc_agi.OperationMode.OFFLINE, environments_dir=str(base.ENV_DIR))
    env = arc.make(gid, seed=0)
    f = env.reset()
    game = env._game
    lex = {a: lx.Lexicon(naming="stable") for a in ARMS}
    stats = {a: collections.Counter() for a in ARMS}

    def read(arm, frames, prev):
        lock = lx.scale_lock(frames, finer_check=(arm == "v4"))
        return lx.encode(frames[-1], lex[arm], lock=lock, prev=prev if arm == "v4" else None)

    frame = np.array(f.frame[-1], dtype=np.int16)
    level, frames = game.level_index, [frame.tolist()]
    prev = {a: read(a, frames, None) for a in ARMS}
    prev_owners, _, _, prev_sprites = base.owners_and_camera(game, frame)
    prev_state = {id(s): sprite_state(s) for s in game.current_level.get_sprites()}
    for name, data in acts:
        f = env.step(GameAction[name], data=data)
        frame = np.array(f.frame[-1], dtype=np.int16)
        if game.level_index != level:
            level, frames = game.level_index, []
            frames.append(frame.tolist())
            prev = {a: read(a, frames, None) for a in ARMS}
            prev_owners, _, _, prev_sprites = base.owners_and_camera(game, frame)
            prev_state = {id(s): sprite_state(s) for s in game.current_level.get_sprites()}
            continue
        frames.append(frame.tolist())
        owners, cam_scale, render_ok, sprites = base.owners_and_camera(game, frame)
        state = {id(s): sprite_state(s) for s in game.current_level.get_sprites()}
        changed = {sid for sid in state if state[sid] != prev_state.get(sid)} | (set(prev_state) - set(state))
        moved_px = {sid: ((st[1] - prev_state[sid][1]) * cam_scale, (st[0] - prev_state[sid][0]) * cam_scale)
                    for sid, st in state.items() if sid in prev_state and st[2] and prev_state[sid][2]
                    and st[:2] != prev_state[sid][:2]}
        gradable = name != "RESET" and render_ok
        for arm in ARMS:
            cur = read(arm, frames, prev[arm])
            p, st = prev[arm], stats[arm]
            st["steps"] += 1
            st["camera_match"] += cur["scale"] == cam_scale
            st["flips"] += (cur["scale"], cur["offset"]) != (p["scale"], p["offset"])
            if gradable and (cur["scale"], cur["offset"]) == (p["scale"], p["offset"]):
                st["graded_steps"] += 1
                d = lx.diff(p, cur, place_first=(PLACE if arm == "v4" else False))
                cells0 = {(q["sym"], q["at"]): q["cells"] for q in p["placed"]}
                cells1 = {(q["sym"], q["at"]): q["cells"] for q in cur["placed"]}

                def real(cells_before=(), cells_after=()):
                    ids = {id(prev_sprites[i]) for i in owners_of(p, cells_before, prev_owners) if i < len(prev_sprites)}
                    ids |= {id(sprites[i]) for i in owners_of(cur, cells_after, owners) if i < len(sprites)}
                    return bool(ids & changed) if ids else None          # None: interface cells only
                checks = ([real(cells0[(s, l)], cells1[(s, r)]) for s, l, r in d["moved"]]
                          + [real(cells0[(s0, at)], cells1[(s1, at)]) for s0, s1, at in d["became"]]
                          + [real(cells_after=cells1[(s, r)]) for s, r in d["appeared"]]
                          + [real(cells_before=cells0[(s, l)]) for s, l in d["disappeared"]])
                st["interface_changes"] += sum(c is None for c in checks)
                st["changes"] += sum(c is not None for c in checks)
                st["changes_right"] += sum(c is True for c in checks)
                k, (oy, ox) = cur["scale"], cur["offset"]
                visible = {id(sprites[i]) for i in range(len(sprites))
                           if id(sprites[i]) in moved_px and ((owners == i) & (frame != cur["background"])).any()}
                st["moved_visible"] += len(visible)
                at = {q["at"]: q for q in cur["placed"]}
                hit = set()
                for s, (r0, c0), (r1, c1) in d["moved"]:
                    st["moves"] += 1
                    q = at.get((r1, c1))
                    if q is None:
                        continue
                    own = collections.Counter(i for i in owners_of(cur, q["cells"], owners))
                    if own:
                        sp = sprites[own.most_common(1)[0][0]]
                        if moved_px.get(id(sp)) == ((r1 - r0) * k, (c1 - c0) * k):
                            st["moves_right"] += 1
                            hit.add(id(sp))
                st["moved_hit"] += len(hit & visible)
            prev[arm] = cur
        prev_owners, prev_sprites, prev_state = owners, sprites, state
        if str(f.state).endswith("WIN"):
            break
    return run, gid[:4], {a: dict(s) for a, s in stats.items()}


def summary(c):
    def r(a, b):
        return round(a / b, 4) if b else None
    return {"steps": c.get("steps", 0), "graded_steps": c.get("graded_steps", 0),
            "changes": c.get("changes", 0), "changes_right": r(c.get("changes_right", 0), c.get("changes", 0)),
            "interface_changes": c.get("interface_changes", 0),
            "moves": c.get("moves", 0), "moves_right": r(c.get("moves_right", 0), c.get("moves", 0)),
            "move_recall": r(c.get("moved_hit", 0), c.get("moved_visible", 0)),
            "flip_rate": r(c.get("flips", 0), c.get("steps", 0)), "camera_match": r(c.get("camera_match", 0), c.get("steps", 0))}


def main():
    jobs = list(base.plays())
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 3) as pool:
        results = pool.map(run_play, jobs, chunksize=1)
    total = {a: collections.Counter() for a in ARMS}
    by_game = collections.defaultdict(lambda: {a: collections.Counter() for a in ARMS})
    for run, g, st in results:
        for a in ARMS:
            total[a].update(st[a])
            by_game[g][a].update(st[a])
    report = {"plays": len(results), "all": {a: summary(total[a]) for a in ARMS},
              "by_game": {g: {a: summary(v[a]) for a in ARMS} for g, v in sorted(by_game.items())}}
    (HERE / f"eval_perception_v4_{os.environ.get('ARCAID3_PLACE', 'shared')}.json").write_text(json.dumps(report, indent=1))
    lines = [f"plays {len(results)}", f"{'':6s} {'changes right':>22s} {'moves right':>20s} {'move recall':>12s} {'flips':>7s} {'camera':>7s}"]
    for a in ARMS:
        s = report["all"][a]
        lines.append(f"{a:6s} {s['changes_right']:>8} of {s['changes']:<10d} {s['moves_right']:>8} of {s['moves']:<8d} "
                     f"{s['move_recall']:>12} {s['flip_rate']:>7} {s['camera_match']:>7}")
    lines.append("")
    lines.append(f"{'game':5s} {'changes right v3 -> v4':>26s} {'moves right v3 -> v4':>24s} {'move recall v3 -> v4':>24s} {'camera v3 -> v4':>18s}")
    for g, v in report["by_game"].items():
        a, b = v["v3"], v["v4"]
        lines.append(f"{g:5s} {str(a['changes_right']):>11s} -> {str(b['changes_right']):<10s} {str(a['moves_right']):>10s} -> {str(b['moves_right']):<10s} "
                     f"{str(a['move_recall']):>10s} -> {str(b['move_recall']):<10s} {str(a['camera_match']):>7s} -> {str(b['camera_match']):<7s}")
    out = "\n".join(lines)
    (HERE / f"eval_perception_v4_{os.environ.get('ARCAID3_PLACE', 'shared')}.out").write_text(out + "\n")
    print(out)


if __name__ == "__main__":
    main()
