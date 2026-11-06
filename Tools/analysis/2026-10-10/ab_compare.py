"""Paired A/B comparison of two multi-pass TAAF/Duck demo runs, by game.

Why: one leaderboard draw of identical code spans roughly 21-34, so a single draw cannot
separate variants. This compares arms on the same public games, pairs them by game, and
reports a bootstrap interval over games, plus two lower-variance readings: levels completed
per million generated tokens, and the Kaplan-Meier chance of finishing a level within 60k tokens.

Usage:
    python3 ab_compare.py A/benchmark.json B/benchmark.json
    python3 ab_compare.py RUN/benchmark.json --split 0,1:2,3     # A/A check within one run
Reads files only.
"""
from __future__ import annotations

import argparse
import collections
import random
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from attempts import attempts, km_completed_by  # noqa: E402
from rhae import check_scorer, load_runs, pass_index, run_tokens  # noqa: E402


def game_means(runs):
    g = collections.defaultdict(list)
    for r in runs:
        g[r["game_id"][:4]].append(r["final_score"])
    return {k: st.mean(v) for k, v in g.items()}


def summary(runs):
    lv = sum(r["levels_completed"] for r in runs)
    tok = sum(run_tokens(r) for r in runs)
    atts = [a for r in runs for a in attempts(r)]
    return dict(runs=len(runs), mean=st.mean(r["final_score"] for r in runs),
                levels_per_M_tokens=lv / tok * 1e6,
                p_level_within_60k=km_completed_by(atts, [60000])[60000])


def compare(a_runs, b_runs, n_boot=10000, seed=0):
    for name, runs in (("A", a_runs), ("B", b_runs)):
        bad = check_scorer(runs)
        if bad:
            raise SystemExit(f"arm {name}: scorer mismatches={bad}; stop")
    ga, gb = game_means(a_runs), game_means(b_runs)
    common = sorted(set(ga) & set(gb))
    if not common:
        raise SystemExit("no common games")
    d = [gb[g] - ga[g] for g in common]
    rng = random.Random(seed)
    boots = sorted(st.mean(rng.choice(d) for _ in d) for _ in range(n_boot))
    lo, hi = boots[int(0.025 * n_boot)], boots[int(0.975 * n_boot)]
    return dict(games=len(common), A=summary(a_runs), B=summary(b_runs),
                paired_diff=st.mean(d), ci95=(lo, hi))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b", nargs="?")
    ap.add_argument("--split", help="A/A within one file: passes for A and B, e.g. 0,1:2,3")
    args = ap.parse_args()
    if args.split:
        pa, pb = ([int(x) for x in s.split(",")] for s in args.split.split(":"))
        runs = load_runs(args.a)
        a_runs = [r for r in runs if pass_index(r) in pa]
        b_runs = [r for r in runs if pass_index(r) in pb]
    else:
        if not args.b:
            ap.error("give two files, or one file with --split")
        a_runs, b_runs = load_runs(args.a), load_runs(args.b)
    res = compare(a_runs, b_runs)
    for arm in ("A", "B"):
        s = res[arm]
        print(f"{arm}: runs={s['runs']} mean={s['mean']:.2f} levels/M tokens={s['levels_per_M_tokens']:.1f} "
              f"P(level within 60k tokens)={s['p_level_within_60k']:.3f}")
    lo, hi = res["ci95"]
    print(f"paired by game (n={res['games']}): B - A = {res['paired_diff']:+.2f}, 95% bootstrap CI [{lo:+.2f}, {hi:+.2f}]")
    print("verdict:", "B better" if lo > 0 else "A better" if hi < 0 else "no detectable difference")


if __name__ == "__main__":
    main()
