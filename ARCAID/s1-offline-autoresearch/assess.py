"""assess.py -- the locked judge. Human-owned: never edit.

Plays `policy.py` on every dev and hold game through the framework's own loop,
scores it with the competition formula (prepare.score_game), and checks it
against the best the teacher has done (memory/rounds.tsv).

Two integrity checks, in the spirit of Agent-ProSAT's twin-blind guard:

  twin blind   every game is played twice, once under its real id and once under
               a scrambled one. The policy must make exactly the same moves: a
               difference means it is steering by the game's identity, which
               cannot transfer to the 110 hidden games.
  static scan  policy.py may not mention a game id, the game files, or any way
               to reach outside the frames it is handed (ground.json lists them).

Usage:
    python assess.py                 # all 25 games, 1200 actions, twin blind (~3 min)
    python assess.py --quick         # 200 actions per game, for a fast read
    python assess.py --games vc33,tn36
Writes sessions/<run_id>.log and sessions/<run_id>.json, and ends with a
`---` block of key=value lines for results.tsv.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import multiprocessing as mp
import re
import subprocess
import sys
import time
from pathlib import Path

import prepare as P

ROOT = P.ROOT
POLICY = ROOT / "policy.py"
_CACHE: dict = {}


def _job(job: tuple) -> dict:
    """One (game, pass) run. Never raises."""
    game, budget, blind = job
    t0 = time.perf_counter()
    try:
        if "arc" not in _CACHE:
            _CACHE["arc"] = P.arcade()
        mod = P.load_module(POLICY, f"policy_{game}_{int(blind)}")
        env = _CACHE["arc"].make(game)
        gid = ("blind-" + hashlib.md5(game.encode()).hexdigest()[:6]) if blind else game
        agent = mod.MyAgent(card_id="assess", game_id=gid, agent_name=f"assess.{gid}",
                            ROOT_URL="http://localhost", record=False, arc_env=env, tags=["assess"])
        agent.MAX_ACTIONS = budget
        meter = {"n": 0, "levels": 0, "level_at": [], "trace": hashlib.sha256()}
        inner = agent.choose_action

        def watched(frames, latest):
            lv = int(getattr(latest, "levels_completed", 0) or 0)
            if lv > meter["levels"]:
                meter["level_at"] += [meter["n"]] * (lv - meter["levels"])
                meter["levels"] = lv
            act = inner(frames, latest)
            meter["n"] += 1
            meter["trace"].update(f"{int(act.value)}:{getattr(act, 'action_data', None)};".encode())
            return act

        agent.choose_action = watched
        agent.main()
        final = agent.frames[-1] if agent.frames else None
        lv = int(getattr(final, "levels_completed", 0) or 0)
        if lv > meter["levels"]:
            meter["level_at"] += [meter["n"]] * (lv - meter["levels"])
        return {"game": game, "blind": blind, "actions": meter["n"], "level_at": meter["level_at"],
                "trace": meter["trace"].hexdigest()[:16], "secs": round(time.perf_counter() - t0, 1)}
    except Exception as e:
        return {"game": game, "blind": blind, "error": f"{type(e).__name__}: {e}",
                "secs": round(time.perf_counter() - t0, 1)}


def static_scan() -> list[str]:
    """Scan executable code only: comments and docstrings may cite games freely."""
    import ast
    tree = ast.parse(POLICY.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if (isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                and body and isinstance(body[0], ast.Expr)
                and isinstance(getattr(body[0], "value", None), ast.Constant)
                and isinstance(body[0].value.value, str)):
            node.body = body[1:] or [ast.Pass()]
    code = ast.unparse(tree)
    hits = [tok for tok in P.GROUND["assess"]["forbidden_in_policy"] if tok in code]
    hits += [g for g in P.GAMES if re.search(rf"\b{g}\b", code)]
    return sorted(set(hits))


def teacher_best() -> dict[str, int]:
    """Most levels the teacher has ever finished on each game."""
    best: dict[str, int] = {}
    f = ROOT / "memory" / "rounds.tsv"
    if not f.exists():
        return best
    with f.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row.get("player", "").startswith("teacher"):
                try:
                    best[row["game"]] = max(best.get(row["game"], 0), int(row["levels"]))
                except (KeyError, ValueError):
                    pass
    return best


def run_id() -> str:
    """The last commit that changed policy.py: memory commits after it do not rename the run."""
    try:
        h = subprocess.run(["git", "log", "-n", "1", "--format=%h", "--", "policy.py"], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip() or "nogit"
        dirty = subprocess.run(["git", "status", "--porcelain", "policy.py"], cwd=ROOT,
                               capture_output=True, text=True).stdout.strip()
        return h + ("-dirty" if dirty else "")
    except Exception:
        return time.strftime("%Y%m%d-%H%M%S")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--games", default="")
    ap.add_argument("--no-twin", action="store_true")
    ap.add_argument("--run-id", default="")
    a = ap.parse_args()

    games = [g.strip() for g in a.games.split(",") if g.strip()] or P.GAMES
    budget = P.QUICK_BUDGET if a.quick else P.BUDGET
    twin = P.GROUND["assess"]["twin_blind"] and not a.no_twin
    rid = a.run_id or run_id()
    t0 = time.perf_counter()

    jobs = [(g, budget, False) for g in games] + ([(g, budget, True) for g in games] if twin else [])
    with mp.get_context("spawn").Pool(min(len(jobs), P.GROUND["assess"]["workers"])) as pool:
        rows = pool.map(_job, jobs)

    real = {r["game"]: r for r in rows if not r["blind"]}
    blind = {r["game"]: r for r in rows if r["blind"]}
    teacher = teacher_best()
    out = []
    lines = [f"assess {rid}  budget={budget}  games={len(games)}  twin_blind={'on' if twin else 'off'}", ""]
    lines.append(f"{'game':6} {'set':4} {'levels':>7} {'teacher':>7} {'score%':>7}  actions per level (human)")
    per_game = {}
    for g in games:
        r = real[g]
        human = P.baselines(g)
        split = "dev" if g in P.DEV else "hold"
        if "error" in r:
            lines.append(f"{g:6} {split:4}  ERROR {r['error']}")
            per_game[g] = {"split": split, "error": r["error"], "score": 0.0, "levels": 0}
            continue
        s = P.score_game(r["level_at"], human)
        pairs = " ".join(f"{u}({h})" for u, h in zip(s["level_actions"], human))
        t = teacher.get(g)
        lines.append(f"{g:6} {split:4} {s['levels']:>3}/{s['n_levels']:<3} {('-' if t is None else t):>7} "
                     f"{100 * s['score']:>7.3f}  {pairs or '-'}")
        per_game[g] = {"split": split, "score": s["score"], "levels": s["levels"],
                       "n_levels": s["n_levels"], "level_actions": s["level_actions"],
                       "teacher_levels": t, "trace": r["trace"], "actions": r["actions"]}

    def suite(split):
        gs = [v for v in per_game.values() if v["split"] == split]
        return P.score_suite([v["score"] for v in gs]), sum(v["levels"] for v in gs), len(gs)

    dev_score, dev_levels, n_dev = suite("dev")
    hold_score, hold_levels, n_hold = suite("hold")
    peeks = [g for g in games if twin and "trace" in real[g] and blind.get(g, {}).get("trace") != real[g]["trace"]]
    scan = static_scan()
    taught = [g for g, t in teacher.items() if g in per_game and t]
    parity = [g for g in taught if per_game[g]["levels"] >= teacher[g]]
    errors = [g for g in games if "error" in real[g]]
    policy_lines = len(POLICY.read_text(encoding="utf-8").splitlines())
    secs = time.perf_counter() - t0

    lines += ["", f"twin blind: {'PASS' if not peeks else 'FAIL on ' + ', '.join(peeks)}",
              f"static scan: {'clean' if not scan else 'VIOLATIONS: ' + ', '.join(scan)}",
              f"teacher parity: {len(parity)}/{len(taught)} taught games ({', '.join(parity) or 'none'})", "",
              "---",
              f"run_id={rid}", f"budget={budget}",
              f"dev_score={dev_score:.4f}", f"hold_score={hold_score:.4f}",
              f"dev_levels={dev_levels}", f"hold_levels={hold_levels}",
              f"teacher_parity={len(parity)}/{len(taught)}",
              f"twin_blind={'PASS' if not peeks else 'FAIL'}", f"peeking_violations={len(peeks)}",
              f"static_violations={len(scan)}", f"errors={len(errors)}",
              f"policy_lines={policy_lines}", f"seconds={secs:.0f}"]
    text = "\n".join(lines)
    print(text)
    (ROOT / "sessions").mkdir(exist_ok=True)
    (ROOT / "sessions" / f"{rid}.log").write_text(text + "\n", encoding="utf-8")
    (ROOT / "sessions" / f"{rid}.json").write_text(json.dumps({
        "run_id": rid, "budget": budget, "dev_score": dev_score, "hold_score": hold_score,
        "dev_levels": dev_levels, "hold_levels": hold_levels, "teacher_parity": parity,
        "twin_blind": not peeks, "peeking": peeks, "static_violations": scan, "errors": errors,
        "policy_lines": policy_lines, "games": per_game}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
