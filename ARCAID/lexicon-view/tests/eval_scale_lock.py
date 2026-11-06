"""Grade the per-level scale lock on real play, against the engine (evaluation only).

Replays the recorded actions of agent save runs on the official public games with the pinned engine,
and reads every screen twice with kaggle/lexicon-dfranzen/lexicon.py:
  per-frame  each screen's own block-size detection (the lexicon as shipped until now)
  locked     scale_lock over all frames of the current level seen so far, current one included
             -- what the sandbox can compute from `history`

Per step, for each reading:
  flips          the reading's (block size, offset) changed from the previous frame of the same level
  camera match   block size equals the engine camera's scale
  residue        screen pixels the reading does not reproduce
  moves          lexicon.diff "moved" reports, graded in screen pixels against the engine's sprites:
                 precision = reported moves that land on a sprite which really moved by that amount
                 recall    = visible sprites that really moved and were reported
Steps are graded when they stay on one level, are not RESET, and the engine's render check passes.

Needs Python 3.12 with arc-agi==0.9.8, arcengine==0.9.3 and numpy. From the repo root:
  python kaggle/lexicon-dfranzen/eval_scale_lock.py [workers] [tolerance]   # writes eval_scale_lock*.json here
"""
from __future__ import annotations

import collections
import importlib.util
import json
import logging
import pathlib
import sys
from multiprocessing import Pool

import numpy as np

logging.disable(logging.CRITICAL)
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ENV_DIR = ROOT / "inputs/official-input-arc-prize-2026-arc-agi-3/environment_files"
RUNS = {
    "sheetu-4.17": ROOT / "submissions/2026-09-30__taaf-flashnext-sheetu12b-0922__v1__score-4.17/outputs/benchmark.json",
    "dfranzen-v1": ROOT / "external_submission/2026-09-30__dfranzen__arc-agi-3-milestone-2-solution__v1__teambest-27.89/outputs/benchmark.json",
    "lexicon-dfranzen-v1": ROOT / "experiments/2026-10-05__arcaid3-lexicon-view-dfranzen-m2__v1__unsubmitted__offline10-41.13/outputs/benchmark.json",
}
TOLERANCE = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0   # share of a level's frames allowed to fail the lock


def load_lexicon():
    spec = importlib.util.spec_from_file_location("lexicon", HERE / "lexicon.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def plays():
    for run, path in RUNS.items():
        for g in json.load(open(path))["game_runs"]:
            acts = [(h["action"]["id"], h["action"].get("data") or None) for h in (g.get("history") or [])]
            if acts:
                yield run, g["game_id"], acts


def owners_and_camera(game, frame):
    """Which sprite owns each screen pixel, plus the camera's scale and offset (engine internals)."""
    cam = game.camera
    sprites = list(game.current_level.get_sprites())
    h, w = cam._height, cam._width
    colours = np.full((h, w), cam._background, dtype=np.int16)
    owners = np.full((h, w), -1, dtype=np.int32)
    for i in sorted((i for i, s in enumerate(sprites) if s.is_visible), key=lambda i: sprites[i].layer):
        s = sprites[i]
        px = s.render()
        sh, sw = px.shape
        rx, ry = s.x - cam._x, s.y - cam._y
        x0, x1, y0, y1 = max(0, rx), min(w, rx + sw), max(0, ry), min(h, ry + sh)
        if x1 <= x0 or y1 <= y0:
            continue
        reg = px[y0 - ry:y1 - ry, x0 - rx:x1 - rx]
        m = reg >= 0
        colours[y0:y1, x0:x1][m] = reg[m]
        owners[y0:y1, x0:x1][m] = i
    scale, xo, yo = cam._calculate_scale_and_offset()
    if scale > 1:
        colours = np.repeat(np.repeat(colours, scale, 0), scale, 1)
        owners = np.repeat(np.repeat(owners, scale, 0), scale, 1)
    out_c = np.full((64, 64), cam._letter_box, dtype=np.int16)
    out_o = np.full((64, 64), -3, dtype=np.int32)
    out_c[yo:yo + colours.shape[0], xo:xo + colours.shape[1]] = colours
    out_o[yo:yo + owners.shape[0], xo:xo + owners.shape[1]] = owners
    final = cam.render(sprites).astype(np.int16)
    out_o[final != out_c] = -2
    return out_o, scale, bool((final == frame).all()), sprites


def run_play(args):
    run, gid, acts = args
    import arc_agi
    from arcengine import GameAction
    lx = load_lexicon()
    arc = arc_agi.Arcade(operation_mode=arc_agi.OperationMode.OFFLINE, environments_dir=str(ENV_DIR))
    env = arc.make(gid, seed=0)
    f = env.reset()
    game = env._game
    arms = {"per-frame": {"lex": lx.Lexicon(naming="stable")}, "locked": {"lex": lx.Lexicon(naming="stable")}}
    stats = {a: collections.Counter() for a in arms}
    level_frames, level = [], None

    def read(frame_list, lvl_frames):
        out = {}
        out["per-frame"] = lx.encode(frame_list, arms["per-frame"]["lex"])
        lock = lx.scale_lock(lvl_frames, tolerance=TOLERANCE)
        out["locked"] = lx.encode(frame_list, arms["locked"]["lex"], lock=lock)
        return out

    frame = np.array(f.frame[-1], dtype=np.int16)
    level = game.level_index
    level_frames = [frame.tolist()]
    prev = read(level_frames[-1], level_frames)
    prev_state = {id(s): (s.x, s.y, bool(s.is_visible)) for s in game.current_level.get_sprites()}
    for name, data in acts:
        ga = GameAction.from_name(name) if hasattr(GameAction, "from_name") else GameAction[name]
        f = env.step(ga, data=data)
        frame = np.array(f.frame[-1], dtype=np.int16)
        new_level = game.level_index
        if new_level != level:
            level, level_frames = new_level, []
        level_frames.append(frame.tolist())
        cur = read(level_frames[-1], level_frames)
        state = {id(s): (s.x, s.y, bool(s.is_visible)) for s in game.current_level.get_sprites()}
        owners, cam_scale, render_ok, sprites = owners_and_camera(game, frame)
        same_level = len(level_frames) > 1
        gradable = same_level and name != "RESET" and render_ok
        moved_px = {}
        if gradable:
            for sid, (x, y, vis) in state.items():
                if sid in prev_state and vis and prev_state[sid][2] and (x, y) != prev_state[sid][:2]:
                    moved_px[sid] = ((y - prev_state[sid][1]) * cam_scale, (x - prev_state[sid][0]) * cam_scale)
        for arm in arms:
            c, p = cur[arm], prev[arm]
            st = stats[arm]
            st["steps"] += 1
            st["camera_match"] += c["scale"] == cam_scale
            st["residue"] += c["residue"]
            if same_level:
                st["same_level_steps"] += 1
                st["flips"] += (c["scale"], c["offset"]) != (p["scale"], p["offset"])
            d = lx.diff(p, c)
            st["diff_lines"] += len(d["moved"]) + len(d["became"]) + len(d["appeared"]) + len(d["disappeared"])
            if not gradable:
                continue
            st["graded_steps"] += 1
            k, (oy, ox) = c["scale"], c["offset"]
            bg = c["background"]
            visible = {id(sprites[i]) for i in range(len(sprites))
                       if id(sprites[i]) in moved_px and ((owners == i) & (frame != bg)).any()}
            st["gt_moved_visible"] += len(visible)
            at = {pl["at"]: pl for pl in c["placed"]}
            hit = set()
            same_grid = (p["scale"], p["offset"]) == (c["scale"], c["offset"])
            for sym, (r0, c0), (r1, c1) in d["moved"]:
                st["reported_moves"] += 1
                pl = at.get((r1, c1))
                if pl is None or not same_grid:
                    continue
                own = collections.Counter()
                for r, cc in pl["cells"]:
                    o = owners[oy + r * k: oy + (r + 1) * k, ox + cc * k: ox + (cc + 1) * k].ravel()
                    own.update(int(v) for v in o if v >= 0)
                if not own:
                    continue
                s = sprites[own.most_common(1)[0][0]]
                if moved_px.get(id(s)) == ((r1 - r0) * k, (c1 - c0) * k):
                    st["correct_moves"] += 1
                    hit.add(id(s))
            st["gt_moved_hit"] += len(hit & visible)
        prev, prev_state = cur, state
        if str(f.state).endswith("WIN"):
            break
    for arm in arms:
        stats[arm]["symbols"] = len(arms[arm]["lex"].entries)
    return run, gid[:4], {a: dict(s) for a, s in stats.items()}


def summary(c):
    return {
        "steps": c["steps"], "graded_steps": c["graded_steps"],
        "flip_rate": round(c["flips"] / max(1, c["same_level_steps"]), 4),
        "camera_match": round(c["camera_match"] / max(1, c["steps"]), 4),
        "residue_px_per_frame": round(c["residue"] / max(1, c["steps"]), 2),
        "diff_lines_per_step": round(c["diff_lines"] / max(1, c["steps"]), 3),
        "symbols": c["symbols"],
        "precision": round(c["correct_moves"] / max(1, c["reported_moves"]), 4),
        "recall": round(c["gt_moved_hit"] / max(1, c["gt_moved_visible"]), 4),
        "reported_moves": c["reported_moves"], "correct_moves": c["correct_moves"],
        "gt_moved_visible": c["gt_moved_visible"], "gt_moved_hit": c["gt_moved_hit"],
    }


def main():
    jobs = list(plays())
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 4) as pool:
        results = pool.map(run_play, jobs, chunksize=1)
    total = {a: collections.Counter() for a in ("per-frame", "locked")}
    by_game = collections.defaultdict(lambda: {a: collections.Counter() for a in ("per-frame", "locked")})
    for run, g, st in results:
        for a in total:
            total[a].update(st[a])
            by_game[g][a].update(st[a])
    report = {"plays": len(results), "runs": {k: str(v.relative_to(ROOT)) for k, v in RUNS.items()},
              "all": {a: summary(total[a]) for a in total},
              "by_game": {g: {a: summary(v[a]) for a in v} for g, v in sorted(by_game.items())}}
    report["tolerance"] = TOLERANCE
    (HERE / ("eval_scale_lock.json" if TOLERANCE == 0 else f"eval_scale_lock_tol{TOLERANCE:g}.json")).write_text(json.dumps(report, indent=1))
    print(json.dumps({"plays": report["plays"], "all": report["all"]}, indent=1))
    changed = {g: v for g, v in report["by_game"].items() if v["per-frame"]["flip_rate"] != v["locked"]["flip_rate"]}
    print("games where the lock changes the flip rate:")
    for g, v in changed.items():
        print(f"  {g}: flips {v['per-frame']['flip_rate']:.3f} -> {v['locked']['flip_rate']:.3f}, "
              f"recall {v['per-frame']['recall']:.3f} -> {v['locked']['recall']:.3f}, "
              f"precision {v['per-frame']['precision']:.3f} -> {v['locked']['precision']:.3f}, "
              f"symbols {v['per-frame']['symbols']} -> {v['locked']['symbols']}")


if __name__ == "__main__":
    main()
