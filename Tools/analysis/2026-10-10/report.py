"""Print every number the 2026-10-10 memo derives from a multi-pass TAAF/Duck benchmark.json.

Usage (from this folder):
    python3 report.py data/dfranzen-m2-v3/benchmark.json
Reads the file only. Exits non-zero if the scorer does not reproduce the stored scores.
"""
from __future__ import annotations

import collections
import math
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from attempts import attempts, km_completed_by
from policies import restart_estimate
from rhae import check_scorer, load_runs, pass_index, run_tokens, truncated


def quantiles(xs, ps):
    xs = sorted(xs)
    return [xs[int(p * (len(xs) - 1))] for p in ps]


def main(path: str) -> None:
    runs = load_runs(path)
    bad = check_scorer(runs)
    print(f"[scorer] runs={len(runs)} mismatches={bad}")
    if bad:
        sys.exit("scorer does not reproduce stored final_score; stop")

    # 1. replicate structure
    by_pass = collections.defaultdict(list)
    by_game = collections.defaultdict(list)
    for r in runs:
        by_pass[pass_index(r)].append(r)
        by_game[r["game_id"]].append(r["final_score"])
    means = [st.mean(x["final_score"] for x in by_pass[p]) for p in sorted(by_pass)]
    print(f"[passes] n={len(means)} means={[round(m, 2) for m in means]} "
          f"overall={st.mean(r['final_score'] for r in runs):.2f} sd_of_pass_means={st.stdev(means):.2f}")
    var_within = st.mean(st.variance(v) for v in by_game.values())
    print(f"[variance] mean within-game variance={var_within:.1f}; implied SD of a 25-game mean="
          f"{math.sqrt(var_within / 25):.2f}, of a 55-game mean={math.sqrt(var_within / 55):.2f}")
    best = st.mean(max(v) for v in by_game.values())
    print(f"[ceiling] per-game best-of-{len(means)} mean={best:.2f} vs mean={st.mean(st.mean(v) for v in by_game.values()):.2f}")

    # 2. value of tokens
    won = [r for r in runs if r["state"] == "won"]
    gave_up = [r for r in runs if r["state"] != "won"]
    print(f"[runs] won={len(won)} budget-limited={len(gave_up)} "
          f"median tokens won={st.median(run_tokens(r) for r in won):.0f} "
          f"budget-limited={st.median(run_tokens(r) for r in gave_up):.0f}")
    res = {}
    for f in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        res[f] = st.mean([r["final_score"] for r in won] + [truncated(r, f)[1] for r in gave_up])
        print(f"[tokens] budget-limited runs cut to {f:.0%} of their tokens -> mean score {res[f]:.2f}")
    for a in (0.8, 0.9):
        per10 = (res[1.0] - res[a]) / math.log(1 / a) * math.log(1.1)
        print(f"[tokens] last {1 - a:.0%} adds {res[1.0] - res[a]:.2f}; log-linear per +10% tokens ~ {per10:.2f}")
    quint = [0] * 5
    for r in gave_up:
        tot = run_tokens(r)
        for a_, cum_end in _completion_points(r):
            quint[min(int(cum_end / tot * 5), 4)] += 1
    print(f"[tokens] budget-limited runs: level completions per token quintile = {quint}")

    # 3. level attempts
    atts = [a for r in runs for a in attempts(r)]
    done = [a for a in atts if a["done"]]
    und = [a for a in atts if not a["done"]]
    tot = sum(a["tokens"] for a in atts)
    print(f"[attempts] total={len(atts)} completed={len(done)} unfinished={len(und)}")
    print(f"[attempts] tokens to complete a level, q25/50/75/90/95 = {quantiles([a['tokens'] for a in done], (.25, .5, .75, .9, .95))}")
    print(f"[attempts] share of generated tokens on attempts that never completed = {sum(a['tokens'] for a in und) / tot:.3f}")
    ratio = [a["actions"] / a["base"] for a in done]
    print(f"[efficiency] completed levels actions/human q25/50/75/90 = "
          f"{[round(x, 2) for x in quantiles(ratio, (.25, .5, .75, .9))]}; share <= 1x = {sum(x <= 1 for x in ratio) / len(ratio):.2f}")
    grid = [20000, 40000, 60000, 100000, 140000, 200000]
    km = km_completed_by(atts, grid)
    print(f"[hazard] KM P(level done within t tokens) = { {g: round(v, 3) for g, v in km.items()} }")
    for t0, t1 in ((20000, 60000), (60000, 100000), (100000, 140000)):
        s0, s1 = 1 - km[t0], 1 - km[t1]
        print(f"[hazard] P(done by {t1} | not done at {t0}) = {(s0 - s1) / s0:.3f}")

    # 4. stuck attempts: attempt-specific or level-specific?
    by_level = collections.defaultdict(list)
    for r in runs:
        for a in attempts(r):
            by_level[(r["game_id"], a["level"])].append(a)
    rec = [(k, a) for k, v in by_level.items() for a in v if not a["done"] and any(x["done"] for x in v)]
    never = sorted({k[0][:4] + f" L{k[1]}" for k, v in by_level.items()
                    if not any(x["done"] for x in v)})
    rr = [a["tokens"] / st.median(x["tokens"] for x in by_level[k] if x["done"]) for k, a in rec]
    print(f"[stuck] unfinished attempts={len(und)}; same level completed in another pass={len(rec)}; "
          f"stuck/median-solving tokens q25/50/75 = {[round(x, 2) for x in quantiles(rr, (.25, .5, .75))]}")
    print(f"[stuck] levels never completed in any pass ({len(never)}): {never}")

    # 5. restart-policy estimates
    for R, F, c in ((100000, None, False), (120000, None, False),
                    (100000, 60000, False), (100000, 80000, False),
                    (100000, 60000, True), (100000, 80000, True),
                    (60000, 80000, False), (60000, 80000, True)):
        e = restart_estimate(runs, R, F, c)
        print(f"[restart] R={R} fresh={F} continuation={c}: fired={e['fired']} slow_successes_cut="
              f"{e['slow_successes_cut']} rescues~{e['expected_rescues']:.1f} gain={e['level_gain']:+.2f} "
              f"token_cost={e['token_cost']:+.2f} net={e['net']:+.2f}")


def _completion_points(r):
    from rhae import cumulative_tokens
    cum = cumulative_tokens(r)
    end = 0
    for k in range(r["levels_completed"]):
        end += r["actions_per_level"][k]
        yield k + 1, cum[end - 1]


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/dfranzen-m2-v3/benchmark.json")
