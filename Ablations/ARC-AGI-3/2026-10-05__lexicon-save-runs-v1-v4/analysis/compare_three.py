"""Three save runs on the same 10 public games, 25 min each, 10 streams: dfranzen v1, lexicon v1, lexicon v2 (scale lock).

  python3 kaggle/lexicon-dfranzen/compare_three.py
Reads each run's benchmark.json and per-request usage (raw request logs for dfranzen v1, the derived
request_usage.csv for the lexicon runs) and the lexicon runs' log counters. One run per arm: a mechanics
comparison, not a score verdict.
"""
import csv, glob, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
RUNS = {
    "dfranzen v1": ROOT / "external_submission/2026-09-30__dfranzen__arc-agi-3-milestone-2-solution__v1__teambest-27.89/outputs",
    "lexicon v1": ROOT / "experiments/2026-10-05__arcaid3-lexicon-view-dfranzen-m2__v1__unsubmitted__offline10-41.13/outputs",
    "lexicon v2 (lock)": ROOT / "experiments/2026-10-07__arcaid3-lexicon-view-dfranzen-m2__v2__unsubmitted__offline10-42.61/outputs",
}


def games(folder):
    out = {}
    for g in json.load(open(folder / "benchmark.json"))["game_runs"]:
        tok = int(re.search(r"tokens=(\d+)", g["solver_note"] or "tokens=0").group(1))
        out[g["game_id"][:4]] = dict(lv=g["levels_completed"], score=g["final_score"], tok=tok, wall=g["final_wallclock_seconds"])
    return out


def usage(folder):
    pt = ct = gen = n = 0
    table = folder.parent / "request_usage.csv"
    if table.exists():
        rows = list(csv.DictReader(open(table)))
        for r in rows:
            pt += int(r["prompt_tokens"]); ct += int(r["cached_tokens"]); gen += int(r["completion_tokens"]); n += 1
    else:
        for f in glob.glob(str(folder / "*_p0_requests.jsonl")):
            for line in open(f):
                if '"usage"' not in line:
                    continue
                u = json.loads(line).get("usage") or {}
                if u.get("prompt_tokens"):
                    pt += u["prompt_tokens"]; ct += (u.get("prompt_tokens_details") or {}).get("cached_tokens") or 0
                    gen += u.get("completion_tokens", 0); n += 1
    return dict(requests=n, reuse=100 * ct / max(1, pt))


def counters(folder):
    log = folder.parent / "log.txt"
    if not log.exists():
        return None
    for line in log.read_text().splitlines():
        if line.startswith("ARCAID3_LEXICON_FINAL"):
            m = re.search(r"'tool_calls': (\d+), 'calls_using_view': (\d+)", line)
            return f"{m.group(2)} of {m.group(1)} tool calls ({100 * int(m.group(2)) / int(m.group(1)):.1f}%)"


data = {name: games(f) for name, f in RUNS.items()}
common = sorted(set.intersection(*(set(d) for d in data.values())))
print(f"{'game':5s}" + "".join(f" | {n:>18s}" for n in RUNS))
for g in common:
    print(f"{g:5s}" + "".join(f" | {data[n][g]['lv']:3d} lv {data[n][g]['score']:6.1f}   " for n in RUNS))
print()
for name, folder in RUNS.items():
    d = data[name]
    lv = sum(d[g]["lv"] for g in common); sc = sum(d[g]["score"] for g in common) / len(common)
    tok = sum(d[g]["tok"] for g in common); wall = max(d[g]["wall"] for g in common)
    u = usage(folder); c = counters(folder)
    print(f"{name:18s} levels {lv:2d}  mean {sc:5.2f}  tokens {tok:7d}  tok/s {tok / wall:4.0f}  requests {u['requests']}  "
          f"cache reuse {u['reuse']:.1f}%" + (f"  view read in {c}" if c else ""))
