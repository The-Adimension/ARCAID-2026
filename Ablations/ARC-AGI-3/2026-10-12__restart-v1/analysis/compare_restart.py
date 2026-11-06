"""Fetch the restart runs' outputs and apply DECISION_RULE.md.

  python kaggle/restart-dfranzen/compare_restart.py [--fetch] [slug ...]

Default slugs: arcaid3-restart-dfranzen-m2 and -r2. With --fetch, benchmark.json, stuck_restarts.jsonl and the
log are downloaded into experiments/2026-10-12__restart-dfranzen/<slug>/ (Kaggle API; credentials come from
the environment). Without it, the files already there are read.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import time
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "experiments/2026-10-12__restart-dfranzen"
SLUGS = ["arcaid3-restart-dfranzen-m2", "arcaid3-restart-dfranzen-m2-r2"]
KEEP = ("benchmark.json", "stuck_restarts.jsonl", "summary.txt")
CONTROL = {"pooled_reach_100k": 46, "pooled_completed_later": 9, "lb_off_scores": (43.77, 47.57)}
STATE = re.compile(r"([a-z0-9]{4}-[0-9a-f]{8})_p(\d+)_tool_runtime_state")


def get(url, binary=False):
    for wait in (0, 30, 60, 120, 240):
        time.sleep(wait)
        try:
            with urllib.request.urlopen(url, timeout=600) as r:
                data = r.read()
                return data if binary else json.loads(data)
        except urllib.error.HTTPError as exc:
            if exc.code != 429:
                raise
    raise RuntimeError(f"rate limited: {url}")


def fetch(slug):
    d = OUT / slug
    d.mkdir(parents=True, exist_ok=True)
    url = f"https://www.kaggle.com/api/v1/kernels/output?userName=habanwer&kernelSlug={slug}"
    token, files, log = None, [], None
    while True:
        page = get(url + (f"&pageToken={token}" if token else ""))
        files += page.get("files") or []
        log = log or page.get("log")
        token = page.get("nextPageToken")
        if not token:
            break
    for f in files:
        name = f.get("fileName", "")
        if name.split("/")[-1] in KEEP:
            (d / name.split("/")[-1]).write_bytes(get(f["url"], binary=True))
    if log:
        try:
            lines = json.loads(log)
            text = "".join(x.get("data", "") for x in lines)
        except (ValueError, TypeError, AttributeError):
            text = str(log)
        (d / "log.txt").write_text(text)
    print(f"{slug}: {len(files)} output files; kept {sorted(p.name for p in d.iterdir())}")


def read(slug):
    d = OUT / slug
    b = json.loads((d / "benchmark.json").read_text())
    log = (d / "log.txt").read_text() if (d / "log.txt").exists() else ""
    ev_path = d / "stuck_restarts.jsonl"
    events = [json.loads(l) for l in ev_path.read_text().splitlines()] if ev_path.exists() else []
    return b, log, events


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    slugs = args or SLUGS
    if "--fetch" in sys.argv:
        for s in slugs:
            fetch(s)
    pooled = {"fired": 0, "converted": 0, "attempts": 0}
    for s in slugs:
        b, log, events = read(s)
        runs = b["game_runs"]
        ready = re.search(r"ARCAID3_RESTART_READY \{'tokens': (\d+)", log)
        health = {
            "ready_tokens_100000": bool(ready and ready.group(1) == "100000"),
            "no_traceback": "Traceback (most recent call last)" not in log,
            "games_25": len(runs) == 25 and all(r.get("history") for r in runs),
        }
        by_game = {r["game_id"]: r for r in runs}
        fired = [e for e in events if e["event"] == "restart"]
        conv = []
        for e in fired:
            m = STATE.search(e["state_path"])
            r = by_game.get(m.group(1)) if m else None
            ok = r is not None and r["levels_completed"] >= e["level"]
            conv.append(ok)
            print(f"  {s[-2:] if s.endswith('r2') else 'r1'} {m.group(1)[:4] if m else '?':4s} level {e['level']}: "
                  f"restart at {e['tokens_before']:,} tokens / {e['actions_before']} actions -> "
                  f"{'COMPLETED' if ok else 'not completed'}")
        attempts = sum(r["levels_completed"] + (r["levels_completed"] < r["number_of_levels"]) for r in runs)
        score = sum(r["final_score"] for r in runs) / len(runs)
        levels = sum(r["levels_completed"] for r in runs)
        print(f"{s}: health {health}; score {score:.2f}, levels {levels}; restarts {len(fired)} on {attempts} attempts "
              f"({len(fired) / max(1, attempts):.1%}); completed after restart {sum(conv)}")
        if all(health.values()):
            pooled["fired"] += len(fired)
            pooled["converted"] += sum(conv)
            pooled["attempts"] += attempts
        else:
            print(f"  {s} is INVALID under the health rule and is not judged")
    f, c, a = pooled["fired"], pooled["converted"], pooled["attempts"]
    rate = c / f if f else 0.0
    fire = f / a if a else 0.0
    ctrl = CONTROL["pooled_completed_later"] / CONTROL["pooled_reach_100k"]
    print(f"pooled: {c} of {f} restarts completed their level ({rate:.1%}; control {ctrl:.1%}); fired on {fire:.1%} of {a} attempts")
    if not f:
        verdict = "INCONCLUSIVE (no restarts fired)"
    elif rate >= 0.40 and fire <= 0.15:
        verdict = "PASS"
    elif rate < 0.25 or fire > 0.15:
        verdict = "FAIL"
    else:
        verdict = "INCONCLUSIVE (one more pair of runs, same rule)"
    print(f"decision: {verdict}")


if __name__ == "__main__":
    main()
