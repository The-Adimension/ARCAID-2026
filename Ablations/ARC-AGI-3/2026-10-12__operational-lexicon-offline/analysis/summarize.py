"""Read replay_probe.py output and apply DECISION_RULE.md.

  python experiments/2026-10-12__lexicon-proposals-offline/summarize.py <probe.jsonl>

Stdlib only. Intervals are 95% bootstrap intervals over attempts (2,000 resamples, fixed seed).
"""
from __future__ import annotations

import collections
import gzip
import json
import random
import sys

MIN_STEP = 10            # steps before an attempt's 10th action are not graded
WINDOW = 30              # loop score window (actions)
CHECKPOINTS = (40_000, 60_000)
RNG = random.Random(20261012)


def load(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    runs = [json.loads(l) for l in opener(path, "rt")]
    bad = [(r["game"], r["pas"], r["stored_levels"], r["replay_levels"]) for r in runs if r["stored_levels"] != r["replay_levels"]]
    atts = []
    for r in runs:
        for a in r["attempts"]:
            atts.append(dict(a, game=r["game"], pas=r["pas"], run=r["run"]))
    return runs, atts, bad


def graded(a, subset=None):
    rows = [x for x in a["rows"] if x["a"] != "RESET" and x["i"] >= MIN_STEP]
    if subset == "new":
        rows = [x for x in rows if x["new"]]
    return rows


def classify(x):
    """(informative-right, misleading, lenient-right, lenient-misleading, unknown) flags for one step."""
    ans, good = x["ans"], x["good"]
    if ans == "unknown":
        return 0, 0, 0, 0, 1
    if ans == "noop":
        return int(good), int(not good), int(good), int(not good), 0
    lenient_ok = x["right"] == x["npred"]
    return int(good), int(not good), int(lenient_ok), int(not lenient_ok), 0


def rates(atts, subset=None):
    tot = collections.Counter()
    for a in atts:
        for x in graded(a, subset):
            i, m, li, lm, u = classify(x)
            tot["n"] += 1
            tot["I"] += i
            tot["M"] += m
            tot["LI"] += li
            tot["LM"] += lm
            tot["U"] += u
            tot["unexpl"] += x["unexpl"] > 0
            tot["confident"] += x["ans"] == "confident"
            tot["noop"] += x["ans"] == "noop"
    return tot


def boot(atts, fn, n=2000):
    vals = []
    for _ in range(n):
        s = [atts[RNG.randrange(len(atts))] for _ in atts]
        v = fn(s)
        if v is not None:
            vals.append(v)
    vals.sort()
    return vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]


def share(key, subset=None):
    def f(atts):
        t = rates(atts, subset)
        return t[key] / t["n"] if t["n"] else None
    return f


def pct(x):
    return f"{100 * x:5.1f}%"


def auc(pos, neg):
    """P(score of a positive > score of a negative), ties count half."""
    if not pos or not neg:
        return None
    w = 0.0
    for p in pos:
        for q in neg:
            w += 1.0 if p > q else 0.5 if p == q else 0.0
    return w / (len(pos) * len(neg))


def features_at(a, budget):
    rows = [x for x in a["rows"] if x["tok"] <= budget]
    if not rows:
        return None
    last = rows[-WINDOW:]
    g = [x for x in rows if x["a"] != "RESET" and x["ans"] != "unknown"]
    return {
        "loop30": sum(x["loop"] for x in last) / len(last),
        "loop_all": sum(x["loop"] for x in rows) / len(rows),
        "rules_exact": (sum(bool(x["good"]) for x in g) / len(g)) if g else 0.0,
        "actions": len(rows),
        "resets": sum(x["a"] == "RESET" for x in rows),
        "unexpl_share": sum(x.get("unexpl", 0) > 0 for x in rows if x["a"] != "RESET") / max(1, sum(x["a"] != "RESET" for x in rows)),
    }


def detector(atts, budget):
    alive = [a for a in atts if a["tokens"] > budget]
    pts = []
    for a in alive:
        f = features_at(a, budget)
        if f is not None:
            pts.append((not a["done"], f, a))
    return pts


def auc_of(pts, key):
    pos = [f[key] for stuck, f, _ in pts if stuck]
    neg = [f[key] for stuck, f, _ in pts if not stuck]
    return auc(pos, neg)


def main():
    runs, atts, bad = load(sys.argv[1])
    out = []
    p = out.append
    stuck = [a for a in atts if not a["done"]]
    done = [a for a in atts if a["done"]]
    p(f"runs {len(runs)}; replay levels differ from stored on {len(bad)} runs {bad[:5]}")
    p(f"attempts {len(atts)}: completed {len(done)}, unfinished {len(stuck)}; "
      f"graded steps (non-RESET, action >= {MIN_STEP}): completed {rates(done)['n']}, unfinished {rates(stuck)['n']}")
    p("")
    p("== Test A: predict(action)  [kill if, on unfinished attempts, I < 30% or M >= I]")
    p(f"{'':28s} {'n':>6s} {'I (inform.+right)':>18s} {'M (misleading)':>15s} {'unknown':>8s} {'lenient I':>10s} {'lenient M':>10s}")
    for name, group in (("unfinished (stuck)", stuck), ("completed", done)):
        for subset in (None, "new"):
            t = rates(group, subset)
            if not t["n"]:
                continue
            label = name + (", new actions" if subset else "")
            p(f"{label:28s} {t['n']:6d} {pct(t['I'] / t['n']):>18s} {pct(t['M'] / t['n']):>15s} {pct(t['U'] / t['n']):>8s} "
              f"{pct(t['LI'] / t['n']):>10s} {pct(t['LM'] / t['n']):>10s}")
    tI = rates(stuck)
    lo, hi = boot(stuck, share("I"))
    mlo, mhi = boot(stuck, share("M"))
    I, M = tI["I"] / tI["n"], tI["M"] / tI["n"]
    p(f"unfinished: I = {pct(I)} (95% CI {pct(lo)}-{pct(hi)}), M = {pct(M)} (95% CI {pct(mlo)}-{pct(mhi)})")
    killA = I < 0.30 or M >= I
    p(f"decision A: {'KILL' if killA else 'PASS'} (I < 30%: {I < 0.30}; M >= I: {M >= I})")
    # attempt-weighted, so long attempts do not dominate
    per = [rates([a]) for a in stuck if rates([a])["n"]]
    p(f"unfinished, mean of per-attempt rates ({len(per)} attempts): I {pct(sum(t['I'] / t['n'] for t in per) / len(per))}, "
      f"M {pct(sum(t['M'] / t['n'] for t in per) / len(per))}")
    by_game = collections.defaultdict(list)
    for a in stuck:
        by_game[a["game"]].append(a)
    p("unfinished, by game (I / M / unknown, graded steps):")
    for g in sorted(by_game):
        t = rates(by_game[g])
        if t["n"]:
            p(f"  {g}: {pct(t['I'] / t['n'])} / {pct(t['M'] / t['n'])} / {pct(t['U'] / t['n'])}  ({t['n']})")
    p("")
    p("== Test B: unexplained_recent()  [kill if > 50% of unfinished-attempt steps carry an unexplained change]")
    for name, group in (("unfinished (stuck)", stuck), ("completed", done)):
        t = rates(group)
        p(f"{name:28s} steps with >=1 unexplained change: {pct(t['unexpl'] / t['n'])} of {t['n']}")
    tB = rates(stuck)
    B = tB["unexpl"] / tB["n"]
    blo, bhi = boot(stuck, share("unexpl"))
    p(f"unfinished: {pct(B)} (95% CI {pct(blo)}-{pct(bhi)}); decision B: {'KILL' if B > 0.5 else 'PASS'}")
    p("")
    p("== Test C: stuck detector  [wire into restart trigger if loop30 AUC at 40K >= 0.70]")
    for budget in CHECKPOINTS:
        pts = detector(atts, budget)
        n_stuck = sum(s for s, _, _ in pts)
        p(f"alive at {budget // 1000}K tokens on the level: {len(pts)} attempts, {n_stuck} never finish, {len(pts) - n_stuck} finish later")
        for key in ("loop30", "loop_all", "rules_exact", "unexpl_share", "actions", "resets"):
            a = auc_of(pts, key)
            if a is None:
                continue
            lo, hi = boot(pts, lambda s, k=key: auc_of(s, k))
            ms = sum(f[key] for s, f, _ in pts if s) / max(1, n_stuck)
            mf = sum(f[key] for s, f, _ in pts if not s) / max(1, len(pts) - n_stuck)
            p(f"  {key:12s} AUC {a:.3f} (95% CI {lo:.3f}-{hi:.3f}); mean never-finish {ms:.3f} vs finish-later {mf:.3f}")
        if budget == CHECKPOINTS[0]:
            a40 = auc_of(pts, "loop30")
            p(f"decision C: {'WIRE IN' if a40 is not None and a40 >= 0.70 else 'DO NOT WIRE IN'} (loop30 AUC {a40:.3f})")
    print("\n".join(out))


if __name__ == "__main__":
    main()
