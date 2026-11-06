"""Level trials: lexicon on against off, paired by (game, level). See level_trials.py.

  python3 kaggle/lexicon-dfranzen/compare_level_trials.py [--fetch] [round ...]

Per trial (one game started cold at one level, 60 min): cleared or not, and when. Per arm: levels cleared
out of 183, a time-weighted score, usage counters. Paired over the trials: an exact McNemar test on
cleared/not cleared, a sign-flip test on the time-weighted score, by game and by level depth. The decision
rule in DECISION_RULE.md (fixed before the first run) is applied at the end.
"""
import json
import math
import pathlib
import random
import re
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import compare_replicates as cr  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXP = ROOT / "experiments/2026-10-09__level-trials-lexicon-vs-off"
BUDGET_S = {1: 60 * 60, 2: 60 * 60}   # per-trial clock by round; later rounds: 20 min
BUDGET_DEFAULT = 20 * 60
ID = re.compile(r"^(?P<game>[^@]+)@L(?P<level>\d+)$")


def trials(folder):
    """{(game4, level): {"cleared": bool, "t": seconds or None, "actions": n}}"""
    out = {}
    for g in json.load(open(folder / "outputs/benchmark.json"))["game_runs"]:
        m = ID.match(g["game_id"])
        if not m:
            continue
        h, apl = g["history"], g["actions_per_level"]
        cleared = g["levels_completed"] >= 1
        # history clocks run from the benchmark's start, not the trial's: time a clear from the trial's first action
        t = h[apl[0] - 1]["wallclock_seconds"] - h[0]["wallclock_seconds"] if cleared and apl[0] else None
        out[(m["game"][:4], int(m["level"]))] = {"cleared": cleared, "t": t, "actions": apl[0] if cleared else len(h)}
    return out


def weighted(x, budget):
    return max(0.0, budget - x["t"]) / budget if x["cleared"] and x["t"] is not None else 0.0


def usage(folder):
    log = (folder / "log.txt").read_text() if (folder / "log.txt").exists() else ""
    final = next((l for l in log.splitlines() if l.startswith("ARCAID3_LEXICON_FINAL")), "")
    calls = re.search(r"'tool_calls': (\d+), 'calls_using_view': (\d+)", final)
    rules = re.search(r"'rules': (\d+)", final)
    n = re.search(r"ARCAID3_LEVEL_TRIALS (\d+) entries", log)
    return {"view": f"{100 * int(calls[2]) / max(1, int(calls[1])):.1f}%" if calls and int(calls[1]) else "-",
            "rules": rules[1] if rules else "-", "entries": int(n[1]) if n else None,
            "off": "ARCAID3_LEXICON_OFF" in log, "errors": (re.search(r"'errors': (\d+)", final) or [None, "-"])[1]}


def mcnemar(b, c):
    """Exact two-sided McNemar p from the discordant counts."""
    n, k = b + c, min(b, c)
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def sign_flip(diffs, n=200_000, seed=0):
    obs = abs(sum(diffs))
    rng = random.Random(seed)
    hits = sum(abs(sum(d if rng.random() < 0.5 else -d for d in diffs)) >= obs - 1e-12 for _ in range(n))
    return (hits + 1) / (n + 1)


def main():
    rounds = [int(a) for a in sys.argv[1:] if a.isdigit()] or [1]
    if "--fetch" in sys.argv:
        for r in rounds:
            for arm in ("lex", "off"):
                folder = EXP / f"arcaid3-lt-{arm}-r{r}"
                cr.fetch(folder.name, folder)
    lines, pairs = [], []
    for r in rounds:
        on_f, off_f = EXP / f"arcaid3-lt-lex-r{r}", EXP / f"arcaid3-lt-off-r{r}"
        on, off = trials(on_f), trials(off_f)
        budget = BUDGET_S.get(r, BUDGET_DEFAULT)
        for x in (on, off):
            for v in x.values():
                v["w"] = weighted(v, budget)
        uon, uoff = usage(on_f), usage(off_f)
        assert uoff["off"] and not uon["off"], "the control arm must log ARCAID3_LEXICON_OFF, the lexicon arm must not"
        keys = sorted(set(on) & set(off))
        idle = {name: sum(x[k]["actions"] == 0 and not x[k]["cleared"] for k in keys) for name, x in (("on", on), ("off", off))}
        lines += [f"round {r}: {len(keys)} paired trials (on {len(on)}, off {len(off)}; logged entries {uon['entries']} / {uoff['entries']}), "
                  f"{budget // 60} min each",
                  f"  validity: trials that never acted: on {idle['on']}, off {idle['off']}"
                  + ("  ** more than 5% of trials never played: not a valid round **"
                     if max(idle.values()) > 0.05 * len(keys) else "  (ok)"),
                  "arm   cleared   time-weighted   view   .rules   errors"]
        for name, x, u in (("lex", on, uon), ("off", off, uoff)):
            lines.append(f"{name:5s} {sum(x[k]['cleared'] for k in keys):7d} {statistics.mean(x[k]['w'] for k in keys):15.3f} "
                         f"{u['view']:>6s} {u['rules']:>8s} {u['errors']:>8s}")
        pairs += [(on[k], off[k], k) for k in keys]
        lines.append("")
    b = sum(a["cleared"] and not z["cleared"] for a, z, _ in pairs)
    c = sum(z["cleared"] and not a["cleared"] for a, z, _ in pairs)
    n = len(pairs)
    d = (b - c) / n
    se = math.sqrt(max(0.0, b + c - (b - c) ** 2 / n)) / n
    p = mcnemar(b, c)
    wd = [a["w"] - z["w"] for a, z, _ in pairs]
    lines += [f"all rounds, {n} paired trials:",
              f"  cleared by lexicon only {b}, by control only {c}, by both {sum(a['cleared'] and z['cleared'] for a, z, _ in pairs)}, "
              f"by neither {sum(not a['cleared'] and not z['cleared'] for a, z, _ in pairs)}",
              f"  clear-rate difference on - off: {100 * d:+.1f} points (95% CI {100 * (d - 1.96 * se):+.1f} to {100 * (d + 1.96 * se):+.1f}); "
              f"exact McNemar p = {p:.3f}",
              f"  time-weighted difference: {statistics.mean(wd):+.3f} (sign-flip p = {sign_flip(wd):.3f})"]
    if d > 0 and p < 0.05:
        verdict = "LEXICON HELPS (on - off > 0, McNemar p < 0.05)"
    elif d < 0 and p < 0.05:
        verdict = "LEXICON HURTS (on - off < 0, McNemar p < 0.05)"
    else:
        verdict = "NO DETECTABLE DIFFERENCE at this size (McNemar p >= 0.05); see the interval"
    lines += [f"  decision (rule fixed before the first run): {verdict}", "",
              "by level depth (cleared on / off):"]
    for lo, hi in ((0, 0), (1, 2), (3, 5), (6, 99)):
        sub = [(a, z) for a, z, k in pairs if lo <= k[1] <= hi]
        if sub:
            lines.append(f"  levels {lo}-{hi}: {sum(a['cleared'] for a, _ in sub)} / {sum(z['cleared'] for _, z in sub)} of {len(sub)}")
    lines += ["", "by game (cleared on / off, of trials):"]
    for g in sorted({k[0] for _, _, k in pairs}):
        sub = [(a, z) for a, z, k in pairs if k[0] == g]
        lines.append(f"  {g}: {sum(a['cleared'] for a, _ in sub)} / {sum(z['cleared'] for _, z in sub)} of {len(sub)}")
    out = "\n".join(lines)
    EXP.mkdir(parents=True, exist_ok=True)
    (EXP / "compare_level_trials.out").write_text(out + "\n")
    print(out)


if __name__ == "__main__":
    main()
