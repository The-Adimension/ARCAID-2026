"""Paired level-trial analysis for the probe-first gate.

Usage: python lt_analysis.py <off_dir> <on_dir> [<off_dir2> <on_dir2>]
Each dir holds a Kaggle kernel output: benchmark.json (+ *_requests.jsonl for secondary metrics).
Primary: levels cleared per (game, level) entry, paired, exact McNemar (two-sided binomial on discordant pairs).
Secondary: no-action token share, median a/h on cleared entries, deaths per entry, truncations.
"""
import collections, glob, json, math, os, statistics as st, sys


def load(d):
    b = json.load(open(os.path.join(d, "benchmark.json")))
    out = {}
    for g in b["game_runs"]:
        gid = g["game_id"]                      # "<game>@L<k>"
        k = int(gid.rsplit("@L", 1)[1]) if "@L" in gid else 0
        apl, base = g["actions_per_level"], g["base_actions_per_level"]
        cleared = int(g["levels_completed"]) >= 1
        resets = sum(1 for h in g.get("history") or []
                     if isinstance(h.get("action"), dict) and str(h["action"].get("id")).startswith("RESET"))
        out[gid] = {"cleared": cleared, "ratio": (apl[0] / base[k]) if cleared and k < len(base) and base[k] else None,
                    "deaths": max(0, resets - 1), "state": g.get("state")}
    return out


def requests_metrics(d):
    resp = comp = noact_tok = noact = trunc = 0
    for f in glob.glob(os.path.join(d, "*_requests.jsonl")):
        prev = 0
        for line in open(f):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("event") != "response":
                continue
            u = r.get("usage") or {}; a = r.get("action") or 0; ct = u.get("completion_tokens", 0)
            resp += 1; comp += ct
            if r.get("finish_reason") == "length": trunc += 1
            if a <= prev: noact += 1; noact_tok += ct
            prev = a
    return {"responses": resp, "no_action_share": noact / resp if resp else None,
            "no_action_token_share": noact_tok / comp if comp else None, "truncations": trunc}


def mcnemar_exact(b, c):
    """Two-sided exact p for discordant counts b (on-only) and c (off-only)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def main(argv):
    pairs = [(argv[i], argv[i + 1]) for i in range(0, len(argv), 2)]
    B = C = both = neither = 0; off_clear = on_clear = n = 0
    ratios = {"off": [], "on": []}; deaths = {"off": 0, "on": 0}; req = {"off": [], "on": []}
    for off_d, on_d in pairs:
        off, on = load(off_d), load(on_d)
        for gid in sorted(set(off) & set(on)):
            n += 1; o, p = off[gid]["cleared"], on[gid]["cleared"]
            off_clear += o; on_clear += p
            if p and not o: B += 1
            elif o and not p: C += 1
            elif o and p: both += 1
            else: neither += 1
            for arm, src in (("off", off), ("on", on)):
                if src[gid]["ratio"] is not None: ratios[arm].append(src[gid]["ratio"])
                deaths[arm] += src[gid]["deaths"]
        for arm, d in (("off", off_d), ("on", on_d)):
            req[arm].append(requests_metrics(d))
    p = mcnemar_exact(B, C)
    lift = (on_clear - off_clear) / off_clear if off_clear else float("nan")
    print(f"paired entries {n} | cleared off {off_clear} on {on_clear} | lift {lift:+.1%} | on-only {B} off-only {C} both {both} neither {neither} | exact McNemar p = {p:.4f}")
    for arm in ("off", "on"):
        rs = ratios[arm]; r = req[arm]
        tok = [x["no_action_token_share"] for x in r if x["no_action_token_share"] is not None]
        print(f"  {arm}: median a/h on cleared {st.median(rs):.2f} (n={len(rs)}) | deaths/entry {deaths[arm]/max(1,n):.3f} | "
              f"no-action token share {sum(tok)/len(tok) if tok else float('nan'):.0%} | truncations {sum(x['truncations'] for x in r)}")
    base_deaths = deaths["off"] / max(1, n); on_deaths = deaths["on"] / max(1, n)
    on_tok = [x["no_action_token_share"] for x in req["on"] if x["no_action_token_share"] is not None]
    gate = {
        "lift >= +15%": lift >= 0.15,
        "McNemar p < 0.05": p < 0.05,
        "median a/h (on) < 0.90": (st.median(ratios["on"]) if ratios["on"] else 9) < 0.90,
        "deaths (on) <= 1.5x off": on_deaths <= 1.5 * max(base_deaths, 1e-9) or on_deaths == 0,
        "no-action token share (on) <= 45%": bool(on_tok) and sum(on_tok) / len(on_tok) <= 0.45,
    }
    for k, v in gate.items():
        print(f"  gate {k}: {'PASS' if v else 'FAIL'}")
    print("VERDICT:", "PROCEED to a scored submission" if all(gate.values()) else "DO NOT submit")


if __name__ == "__main__":
    main(sys.argv[1:])
