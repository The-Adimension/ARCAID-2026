"""Reproduce the numbers in report-2026-10-05.md.

Reads files only (the leaderboard snapshot in this folder, and two save-run
output folders already in the repo). No network, no engine.

Run from the repo root:  python report-2026-10-05/luck_test.py
"""
import csv
import glob
import json
import re
from pathlib import Path

import numpy as np
from scipy.stats import norm

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LB = HERE / "publicleaderboard-2026-10-05T10-16-27.csv"
DFR = ROOT / "external_submission/2026-09-30__dfranzen__arc-agi-3-milestone-2-solution__v1__teambest-27.89/outputs"
SHEETU = ROOT / "submissions/2026-09-30__taaf-flashnext-sheetu12b-0922__v1__score-4.17/outputs"

# Public scores of notebooks whose competition path is byte-identical to
# dfranzen/arc-agi-3-milestone-2-solution (diffs touch only markdown or the
# non-submission save-run branch). Sources in report section 3.
IDENTICAL_PATH_DRAWS = {
    "dfranzen (author, team LB)": 27.89,
    "shiiin9 unchanged resubmission": 27.62,
    "skarin v1, submitted 10-02": 27.80,
    "skarin v1, submitted 10-03": 21.01,
    "juliancamilovilla/arc-agi3-franzen-m2": 25.17,
    "svegio/arc-agi-3-milestone-2-solution": 22.24,
    "manwithacat/digital-mouse-qwen-genome-baseline": 26.23,
    "bang1850/arc-prize-2026-sovereign-agent": 29.08,
}
D_PRIME_DRAWS = [31.54, 26.98, 25.33]  # shiiin9, amatlas, matterhorn3838


def leaderboard():
    rows = list(csv.DictReader(open(LB, encoding="utf-8-sig")))
    for r in rows:
        r["s"] = float(r["Score"])
        r["n"] = int(r["SubmissionCount"])
        r["d"] = r["LastSubmissionDate"][:10]
    return rows


def describe(x):
    x = np.asarray(x, dtype=float)
    return (f"n={len(x)} mean={x.mean():.2f} sd={x.std(ddof=1):.2f} "
            f"p10={np.percentile(x, 10):.2f} p50={np.median(x):.2f} "
            f"p90={np.percentile(x, 90):.2f} min={x.min():.2f} max={x.max():.2f}")


def section_leaderboard(rows):
    print("== Leaderboard 2026-10-05T10:16:27 ==")
    print("teams:", len(rows))
    sc = np.array([r["s"] for r in rows])
    for t in (50, 40, 35, 32, 30, 25, 20, 10, 6):
        print(f"  teams >= {t}: {int((sc >= t).sum())}")
    print("  rank 353 score:", rows[352]["s"])
    one = [r["s"] for r in rows if r["n"] == 1 and r["s"] >= 15]
    gap = [r["s"] for r in rows if r["n"] == 1 and 5 <= r["s"] < 15]
    print("  teams with exactly 1 submission and score >= 15:", describe(one))
    print("  teams with exactly 1 submission and 5 <= score < 15:", gap)


def section_noise():
    print("\n== Same-code noise ==")
    print("  identical-path draws:", describe(list(IDENTICAL_PATH_DRAWS.values())))
    print(f"  D' scheduler draws: mean {np.mean(D_PRIME_DRAWS):.2f} (n={len(D_PRIME_DRAWS)})")
    ours = [3.04, 3.37, 2.84, 2.57, 3.01, 3.39, 3.59, 2.78]  # submissions/index.csv, 09-19..09-26
    rellik = [5.02, 5.50, 6.42]  # rellik13 write-up, same notebook x3
    for name, x in (("ours (Flash-Next v3 family)", ours), ("rellik13 triple", rellik),
                    ("dfranzen identical-path", list(IDENTICAL_PATH_DRAWS.values()))):
        x = np.asarray(x)
        print(f"  CV {name}: {x.std(ddof=1) / x.mean():.2f}")


def section_envelope(rows):
    print("\n== Luck envelope: expected vs observed counts ==")
    print("  pool: teams with last submission >= 2026-10-01 and score >= 15;")
    print("  draws per team = min(SubmissionCount, 25) (upper bound: 5/day since 09-30)")
    pool = [r for r in rows if r["d"] >= "2026-10-01" and r["s"] >= 15]
    print("  pool size:", len(pool))
    nulls = {"wide N(25.8, 3.93) [Son Pham, thread 745062]": (25.8, 3.93),
             "narrow N(25.8, 2.91) [single-submission teams]": (25.8, 2.91)}
    for name, (mu, sd) in nulls.items():
        print("  --", name)
        for thr in (30, 32, 34, 35, 36, 38):
            exp = sum(1 - norm.cdf((thr - mu) / sd) ** min(r["n"], 25) for r in pool)
            obs = sum(1 for r in pool if r["s"] >= thr)
            print(f"     >= {thr}: expected by luck {exp:6.1f}   observed {obs:4d}")
    print("\n  per-team P(best of k draws >= score) under each null, top 16:")
    for r in rows[:16]:
        k = min(r["n"], 25)
        pw = 1 - norm.cdf((r["s"] - 25.8) / 3.93) ** k
        pn = 1 - norm.cdf((r["s"] - 25.8) / 2.91) ** k
        print(f"   {r['Rank']:>3} {r['TeamName'][:24]:24s} {r['s']:6.2f} subs={r['n']:4d}  "
              f"wide={pw:8.1e}  narrow={pn:8.1e}")


def runs(folder):
    b = json.load(open(folder / "benchmark.json"))
    out = {}
    for g in b["game_runs"]:
        tok = int(re.search(r"tokens=(\d+)", g["solver_note"] or "tokens=0").group(1))
        out[g["game_id"][:4]] = dict(lv=g["levels_completed"], score=g["final_score"],
                                     tok=tok, wall=g["final_wallclock_seconds"])
    return out


def section_mechanics():
    print("\n== Save-run mechanics: dfranzen v1 (10 games, 25 min, 10 streams) vs our sheetu run (25 games, 120 min) ==")
    d, s = runs(DFR), runs(SHEETU)
    wall_d = max(v["wall"] for v in d.values())
    print(f"  aggregate generated tok/s: dfranzen {sum(v['tok'] for v in d.values()) / wall_d:.0f}, "
          f"sheetu {sum(v['tok'] for v in s.values()) / 7200:.0f}")
    common = list(d)
    for name, x in (("dfranzen", d), ("sheetu", s)):
        lv = sum(x[g]["lv"] for g in common)
        sc = np.mean([x[g]["score"] for g in common])
        ex = np.mean([x[g]["score"] for g in common if g != "sb26"])
        tk = sum(x[g]["tok"] for g in common)
        print(f"  {name:8s} same 10 games: levels {lv}, mean score {sc:.2f} (ex-sb26 {ex:.2f}), tokens {tk}")
    pt, ct, comp = [], [], []
    for f in glob.glob(str(DFR / "*_p0_requests.jsonl")):
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
    pt, ct, comp = map(np.array, (pt, ct, comp))
    print(f"  dfranzen requests {len(pt)}: prompt p50 {np.median(pt):.0f}, p90 {np.percentile(pt, 90):.0f}; "
          f"cache reuse {100 * ct.sum() / pt.sum():.1f}%; uncached prompt / generated = "
          f"{(pt - ct).sum() / comp.sum():.1f}")
    prom = (SHEETU / "vllm-metrics-final.prom").read_text()
    get = lambda k: float(re.search(rf"^vllm:{k}\{{.*\}} (\S+)$", prom, re.M).group(1))
    print(f"  sheetu vLLM: prefix-cache queries {get('prefix_cache_queries_total'):.0f}; "
          f"prompt tokens {get('prompt_tokens_total') / 1e6:.2f}M; generated {get('generation_tokens_total') / 1e6:.2f}M; "
          f"prompt / generated = {get('prompt_tokens_total') / get('generation_tokens_total'):.1f}")


if __name__ == "__main__":
    lb = leaderboard()
    section_leaderboard(lb)
    section_noise()
    section_envelope(lb)
    section_mechanics()
