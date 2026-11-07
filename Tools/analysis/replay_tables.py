"""Replay every recorded ARC-AGI-3 action history on the official engine; write the verified level and action tables.

  python3.12 -I replay_tables.py REPO_ROOT ENV_DIR OUT_DIR

REPO_ROOT  this repository: every `outputs/benchmark.json` (the harness's own record of a save run) with the
           `run.json` beside its folder
ENV_DIR    the official ARC-AGI-3 public game files (`environment_files/` of the competition's data page;
           they are not redistributed here)
Needs Python 3.12 with the competition-pinned packages: pip install arc-agi==0.9.8 arcengine==0.9.3 numpy

Whole-game runs start at level 0. A run that plays a game more than once lists it once per pass; `pass` numbers them
in order (0, 1, ...), as the harness's `_p<N>` file names do. Level trials (game ids "<game>@L<k>") are positioned exactly as the trial
cell did it: set_level(k), then RESET, with ONLY_RESET_LEVELS=true (the harness's own setting). The engine's levels_completed
counter does not count the k skipped levels, so a trial's level index is k plus the levels cleared since its start.

Writes to OUT_DIR:
  replay.csv       one row per game-run: what the harness recorded and what the engine reproduces, with a
                   match flag for levels, actions per level and score
  levels.csv.gz    one row per (run, game-run, level played): human baseline, our actions, cleared,
                   game-overs, actions that left the board unchanged, generated tokens
  actions.csv.gz   one row per action: level, action and its data, board changed (last frame against the last
                   frame before), any frame changed (any frame the action returned differs), level completed,
                   game over, a 12-hex hash of the board after the action (for detecting repeated states),
                   generated tokens and wall-clock seconds as the harness logged them
Every outcome in these tables comes from the engine, not from the harness's own bookkeeping; the harness
fields (tokens, wall-clock) are carried along for joins.
"""
import csv, gzip, hashlib, json, logging, os, re, sys
from pathlib import Path

os.environ["ONLY_RESET_LEVELS"] = "true"
logging.disable(logging.CRITICAL)
import numpy as np
import arc_agi
from arcengine import GameAction, GameState

repo, env_dir, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)
arc = arc_agi.Arcade(operation_mode=arc_agi.OperationMode.OFFLINE, environments_dir=env_dir)


def rhae(apl, base, done):
    n = len(base); w = n * (n + 1) / 2
    s = sum((i + 1) * min((base[i] / apl[i]) ** 2 * 100, 115) for i in range(done) if apl[i]) / w
    return min(s, sum(range(1, done + 1)) / w * 100)


def last(f):
    return np.asarray(f.frame[-1]) if f.frame else None


rep_rows, lvl_rows = [], []
act_f = gzip.open(out / "actions.csv.gz", "wt", newline="")
act_w = csv.writer(act_f)
act_w.writerow(["run_id", "game_run", "pass", "action_index", "level", "action", "x", "y", "board_changed",
                "any_frame_changed", "level_completed", "game_over", "board_hash", "generated_tokens", "wallclock_seconds"])
for bpath in sorted(repo.glob("**/outputs/benchmark.json")):
    vdir = bpath.parent.parent
    run = json.loads((vdir / "run.json").read_text())
    run_id = f"{run['kernel'].split('/')[-1]}@v{run['version']}"
    folder = vdir.relative_to(repo).as_posix()
    place = run.get("placement") or {}
    seen = {}
    for r in json.loads(bpath.read_text())["game_runs"]:
        gid = r["game_id"]; m = re.search(r"@L(\d+)$", gid); k = int(m.group(1)) if m else 0
        trial = m is not None                        # "@L0" is a trial too
        pss = seen.get(gid, 0); seen[gid] = pss + 1  # runs with several passes list a game once per pass
        env = arc.make(gid.split("@")[0], seed=0); f = env.reset()
        if k:
            env._game.set_level(k); f = env.step(GameAction.RESET)
        start = f.levels_completed
        base = r["base_actions_per_level"]; n = len(base)
        apl, deaths, noop, tok = [0] * n, [0] * n, [0] * n, [0] * n
        prev = last(f)
        for i, h in enumerate(r["history"]):
            cur = min(k + f.levels_completed - start, n - 1)   # the engine's counter does not include set_level(k)
            a = h["action"]; data = a.get("data") or None
            f = env.step(GameAction[a["id"]], data=data)
            now = last(f)
            changed = not (prev is not None and now is not None and prev.shape == now.shape and np.array_equal(prev, now))
            any_changed = any(not (prev is not None and np.asarray(fr).shape == prev.shape and np.array_equal(prev, np.asarray(fr)))
                              for fr in (f.frame or []))
            lvl_done = k + f.levels_completed - start > cur
            over = f.state == GameState.GAME_OVER
            apl[cur] += 1; deaths[cur] += over; noop[cur] += (not changed); tok[cur] += h.get("generated_tokens") or 0
            act_w.writerow([run_id, gid, pss, i + 1, cur, a["id"], (data or {}).get("x", ""), (data or {}).get("y", ""),
                            int(changed), int(any_changed), int(lvl_done), int(over),
                            hashlib.sha1(now.tobytes()).hexdigest()[:12] if now is not None else "", h.get("generated_tokens", ""),
                            round(h["wallclock_seconds"], 3) if h.get("wallclock_seconds") is not None else ""])
            prev = now
        done = f.levels_completed
        rec_apl = r.get("actions_per_level") or []
        rep_rows.append({
            "run_id": run_id, "folder": folder, "track": run["track"], "place": place.get("place", ""),
            "group": place.get("group", ""), "arm": place.get("arm", ""), "game_run": gid, "pass": pss, "start_level": k, "trial": int(trial),
            "actions": len(r["history"]), "recorded_levels_completed": r["levels_completed"],
            "replay_levels_completed": done, "replay_cleared_from_start": done - start,
            "levels_match": int(r["levels_completed"] in (done, done - start)),
            "actions_per_level_match": int(rec_apl == apl) if not trial else "",
            "recorded_score": round(r["final_score"], 4),
            "replay_score": round(rhae(apl, base, done), 4) if not trial else "",
            "score_match": int(abs(r["final_score"] - rhae(apl, base, done)) < 1e-6) if not trial else "",
            "replay_state": str(f.state).split(".")[-1]})
        played = [k] if trial else [i for i in range(n) if apl[i] or i <= min(done, n - 1)]
        for i in played:
            cleared = (done - start >= 1) if trial else (i < done)
            lvl_rows.append({"run_id": run_id, "track": run["track"], "place": place.get("place", ""),
                             "group": place.get("group", ""), "arm": place.get("arm", ""), "game_run": gid, "pass": pss,
                             "game": gid.split("@")[0], "level": i, "trial": int(trial), "human_actions": base[i],
                             "our_actions": apl[i], "cleared": int(cleared),
                             "actions_over_human": round(apl[i] / base[i], 4) if cleared and base[i] else "",
                             "game_overs": deaths[i], "unchanged_board_actions": noop[i], "generated_tokens": tok[i]})
act_f.close()
for name, rows in (("replay.csv", rep_rows), ("levels.csv.gz", lvl_rows)):
    op = gzip.open if name.endswith(".gz") else open
    with op(out / name, "wt", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
bad = [r for r in rep_rows if not r["levels_match"] or r["score_match"] == 0 or r["actions_per_level_match"] == 0]
print(f"{len(rep_rows)} game-runs replayed; {len(lvl_rows)} level rows; mismatches: {len(bad)}")
