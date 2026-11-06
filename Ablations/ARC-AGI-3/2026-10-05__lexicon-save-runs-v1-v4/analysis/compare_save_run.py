"""Compare the lexicon-on-dfranzen save run with dfranzen's own v1 save run (same 10 games, 25 min, 10 streams).

  python kaggle/lexicon-dfranzen/compare_save_run.py [OUT_DIR]

Downloads the finished kernel's benchmark.json, log and per-game request logs through the Kaggle API
(read-only), then prints per game: levels, score and generated tokens for both runs, plus cache reuse,
prompt size, aggregate throughput and the ARCAID3 usage counters. One run per arm: a mechanics check
(did the view get used, did tokens or cache reuse move), not a score verdict.
"""
import glob
import json
import pathlib
import re
import sys

import numpy as np
import requests

ROOT = pathlib.Path(__file__).resolve().parents[2]
KERNEL = ("habanwer", "arcaid3-lexicon-view-dfranzen-m2")
BASE = ROOT / "external_submission/2026-09-30__dfranzen__arc-agi-3-milestone-2-solution__v1__teambest-27.89/outputs"
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "experiments/2026-10-05__arcaid3-lexicon-view-dfranzen-m2__v1__unsubmitted__offline10-41.13/outputs"


def fetch():
    OUT.mkdir(parents=True, exist_ok=True)
    url = f"https://www.kaggle.com/api/v1/kernels/output?userName={KERNEL[0]}&kernelSlug={KERNEL[1]}"
    files, token = [], None
    while True:
        d = requests.get(url + (f"&pageToken={token}" if token else ""), timeout=120).json()
        files += d.get("files", [])
        if d.get("log"):
            log = d["log"]
            try:
                log = "\n".join(e.get("data", "") for e in json.loads(log))
            except (ValueError, AttributeError):
                pass
            (OUT.parent / "log.txt").write_text(log)
        token = d.get("nextPageToken")
        if not token:
            break
    for f in files:
        name = f["fileName"]
        if name == "benchmark.json" or name.endswith("_p0_requests.jsonl") or name in ("summary.txt", "serve.log"):
            target = OUT / name
            if name.endswith("_p0_requests.jsonl") and (OUT.parent / "request_usage.csv").exists():
                continue
            if not target.exists():
                target.write_bytes(requests.get(f["url"], timeout=600).content)
    return files


def games(folder):
    b = json.load(open(folder / "benchmark.json"))
    out = {}
    for g in b["game_runs"]:
        tok = int(re.search(r"tokens=(\d+)", g["solver_note"] or "tokens=0").group(1))
        out[g["game_id"][:4]] = dict(lv=g["levels_completed"], score=g["final_score"], tok=tok,
                                     wall=g["final_wallclock_seconds"])
    return out


def usage(folder):
    pt, ct, comp = [], [], []
    table = folder.parent / "request_usage.csv"          # derived table kept in the repo instead of the raw logs
    if not glob.glob(str(folder / "*_p0_requests.jsonl")) and table.exists():
        import csv
        for row in csv.DictReader(open(table)):
            pt.append(int(row["prompt_tokens"]))
            ct.append(int(row["cached_tokens"]))
            comp.append(int(row["completion_tokens"]))
    for f in glob.glob(str(folder / "*_p0_requests.jsonl")):
        for line in open(f):
            if '"usage"' not in line:
                continue
            try:
                u = json.loads(line).get("usage") or {}
            except json.JSONDecodeError:
                continue
            if u.get("prompt_tokens"):
                pt.append(u["prompt_tokens"])
                comp.append(u.get("completion_tokens", 0))
                ct.append((u.get("prompt_tokens_details") or {}).get("cached_tokens") or 0)
    if not pt:
        return None
    pt, ct, comp = map(np.array, (pt, ct, comp))
    return dict(requests=len(pt), p50=float(np.median(pt)), p90=float(np.percentile(pt, 90)),
                reuse=100 * ct.sum() / pt.sum(), gen=int(comp.sum()))


def main():
    fetch()
    a, b = games(BASE), games(OUT)
    print(f"{'game':5s} | {'dfranzen v1 lv':>14s} {'score':>6s} {'tok':>7s} | {'+lexicon lv':>11s} {'score':>6s} {'tok':>7s}")
    for k in sorted(a):
        x, y = a[k], b.get(k)
        if y is None:
            print(f"{k:5s} | missing in lexicon run")
            continue
        print(f"{k:5s} | {x['lv']:14d} {x['score']:6.1f} {x['tok']:7d} | {y['lv']:11d} {y['score']:6.1f} {y['tok']:7d}")
    for name, g in (("dfranzen v1", a), ("+lexicon", b)):
        common = [k for k in a if k in b]
        wall = max(g[k]["wall"] for k in common)
        print(f"{name:12s} levels {sum(g[k]['lv'] for k in common)}, mean score {np.mean([g[k]['score'] for k in common]):.2f}, "
              f"tokens {sum(g[k]['tok'] for k in common)}, aggregate tok/s {sum(g[k]['tok'] for k in common) / wall:.0f}")
    for name, folder in (("dfranzen v1", BASE), ("+lexicon", OUT)):
        u = usage(folder)
        if u:
            print(f"{name:12s} requests {u['requests']}, prompt p50 {u['p50']:.0f} p90 {u['p90']:.0f}, cache reuse {u['reuse']:.1f}%")
    log = (OUT.parent / "log.txt")
    if log.exists():
        for line in log.read_text().splitlines():
            if line.startswith(("ARCAID3_LEXICON_READY", "ARCAID3_LEXICON_OFF", "ARCAID3_LEXICON_FINAL")):
                print(line[:600])


if __name__ == "__main__":
    main()
