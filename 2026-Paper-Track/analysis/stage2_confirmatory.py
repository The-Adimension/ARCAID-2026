"""Stage 2 of ANALYSIS-PLAN.md: confirmatory tests of H1 (lexicon) and H2 (probe-first) on paired level trials.

  python3.12 -I stage2_confirmatory.py DATA_DIR OUT_DIR

Reads data/levels.csv.gz (outcomes from the engine replay). Writes OUT_DIR/stage2_confirmatory.md and .json.
Everything here is specified in ANALYSIS-PLAN.md §2 (committed before this script was run).
"""
import json, math, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

data, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
L = pd.read_csv(data / "levels.csv.gz")
T = L[L.trial == 1].copy()
T["key"] = T.game_run

DESIGNS = {  # hypothesis -> list of rounds (on run, off run); primary rounds per the plan
    "H1": {"primary": [("arcaid3-lt-lex-r3@v1", "arcaid3-lt-off-r3@v1")],
           "all": [("arcaid3-lt-lex-r1@v1", "arcaid3-lt-off-r1@v1"), ("arcaid3-lt-lex-r2@v1", "arcaid3-lt-off-r2@v1"),
                   ("arcaid3-lt-lex-r3@v1", "arcaid3-lt-off-r3@v1")]},
    "H2": {"primary": [("arcaid3-lt-pf-on-r1@v1", "arcaid3-lt-pf-off-r1@v1"), ("arcaid3-lt-pf-on-r2@v1", "arcaid3-lt-pf-off-r2@v1")]},
}


def pairs(on, off):
    a = T[T.run_id == on].set_index("key")["cleared"]; b = T[T.run_id == off].set_index("key")["cleared"]
    k = a.index.intersection(b.index)
    return pd.DataFrame({"on": a[k].astype(int), "off": b[k].astype(int), "game": [x.split("@")[0] for x in k],
                         "level": [int(x.split("@L")[1]) for x in k]}, index=k)


def counts(df):
    return dict(both=int(((df.on == 1) & (df.off == 1)).sum()), on_only=int(((df.on == 1) & (df.off == 0)).sum()),
                off_only=int(((df.on == 0) & (df.off == 1)).sum()), neither=int(((df.on == 0) & (df.off == 0)).sum()), n=len(df))


def exact_p(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * stats.binom.cdf(min(b, c), n, 0.5))


def wilson(x, n, z=1.959964):
    if n == 0:
        return (0.0, 1.0)
    p = x / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def newcombe_paired(c):  # Newcombe (1998) method 10, with the continuity-corrected phi
    A, B, C, D, n = c["both"], c["on_only"], c["off_only"], c["neither"], c["n"]
    p1, p2 = (A + B) / n, (A + C) / n; l1, u1 = wilson(A + B, n); l2, u2 = wilson(A + C, n)
    den = math.sqrt((A + B) * (C + D) * (A + C) * (B + D))
    num = A * D - B * C
    num = max(num - n / 2, 0) if num > 0 else num
    phi = num / den if den else 0.0
    d = p1 - p2
    lo = d - math.sqrt(max((p1 - l1) ** 2 - 2 * phi * (p1 - l1) * (u2 - p2) + (u2 - p2) ** 2, 0))
    hi = d + math.sqrt(max((u1 - p1) ** 2 - 2 * phi * (u1 - p1) * (p2 - l2) + (p2 - l2) ** 2, 0))
    return d, lo, hi


def cond_or(b, c):
    if b + c == 0:
        return (float("nan"),) * 3
    lo = stats.beta.ppf(0.025, b, c + 1) if b > 0 else 0.0
    hi = stats.beta.ppf(0.975, b + 1, c) if c > 0 else 1.0
    f = lambda p: p / (1 - p) if p < 1 else float("inf")
    return (b / c if c else float("inf"), f(lo), f(hi))


def summarise(rounds):
    per, frames = [], []
    for on, off in rounds:
        df = pairs(on, off); c = counts(df); d, lo, hi = newcombe_paired(c)
        per.append({"on": on, "off": off, **c, "clear_on": (c["both"] + c["on_only"]) / c["n"],
                    "clear_off": (c["both"] + c["off_only"]) / c["n"], "risk_difference": d, "rd_ci": [lo, hi],
                    "exact_p": exact_p(c["on_only"], c["off_only"]), "odds_ratio": cond_or(c["on_only"], c["off_only"])})
        df = df.assign(round=on); frames.append(df)
    allp = pd.concat(frames)
    b = sum(r["on_only"] for r in per); cc = sum(r["off_only"] for r in per)
    pooled_counts = counts(allp); d, lo, hi = newcombe_paired(pooled_counts)
    return per, {"on_only": b, "off_only": cc, "n": len(allp), "exact_p": exact_p(b, cc), "odds_ratio": cond_or(b, cc),
                 "risk_difference": d, "rd_ci": [lo, hi], "same_sign_every_round": len({np.sign(r["on_only"] - r["off_only"]) for r in per}) == 1,
                 "sign": int(np.sign(b - cc))}, allp


res = {}
for h in ("H1", "H2"):
    per, pooled, allp = summarise(DESIGNS[h]["primary"])
    res[h] = {"rounds": per, "pooled": pooled, "_pairs": allp}

# Holm across H1 and H2 (family-wise alpha 0.05)
ps = sorted(((res[h]["pooled"]["exact_p"], h) for h in res))
m = len(ps); running = 0.0
for i, (p, h) in enumerate(ps):
    running = max(running, min(1.0, (m - i) * p)); res[h]["pooled"]["holm_p"] = running
for h in res:
    pl = res[h]["pooled"]
    pl["supported"] = bool(pl["holm_p"] < 0.05 and pl["same_sign_every_round"])

# Sensitivity 1: H1 with the invalid rounds 1-2 included
s1_per, s1_pool, _ = summarise(DESIGNS["H1"]["all"])

# Sensitivity 2: by level depth
def depth(k):
    return "level 1" if k == 0 else ("levels 2-3" if k <= 2 else "levels 4+")
s2 = {}
for h in res:
    allp = res[h]["_pairs"]
    for dname, g in allp.groupby(allp.level.map(depth)):
        c = counts(g); d, lo, hi = newcombe_paired(c)
        s2.setdefault(h, {})[dname] = {**c, "risk_difference": d, "rd_ci": [lo, hi], "exact_p": exact_p(c["on_only"], c["off_only"])}

# Sensitivity 3: leave one game out
s3 = {}
for h in res:
    allp = res[h]["_pairs"]; rows = []
    for g in sorted(allp.game.unique()):
        sub = allp[allp.game != g]; c = counts(sub)
        rows.append({"left_out": g, "risk_difference": newcombe_paired(c)[0], "exact_p": exact_p(c["on_only"], c["off_only"])})
    rd = [r["risk_difference"] for r in rows]; pv = [r["exact_p"] for r in rows]
    s3[h] = {"rd_min": min(rd), "rd_max": max(rd), "p_min": min(pv), "p_max": max(pv),
             "games_whose_removal_crosses_0.05": [r["left_out"] for r in rows if (r["exact_p"] < 0.05) != (res[h]["pooled"]["exact_p"] < 0.05)]}

# Sensitivity 4: logistic models (conditional logit by pair; mixed logit with game and pair effects)
import statsmodels.api as sm
from statsmodels.discrete.conditional_models import ConditionalLogit
from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
s4 = {}
for h in res:
    allp = res[h]["_pairs"].reset_index().rename(columns={"index": "key"})
    allp["pair"] = allp["round"].astype(str) + "|" + allp["key"]
    long = pd.concat([allp.assign(arm=1, y=allp.on), allp.assign(arm=0, y=allp.off)])
    cl = ConditionalLogit(long["y"].values, long[["arm"]].values, groups=long["pair"].values).fit(disp=0)
    beta, se = float(cl.params[0]), float(cl.bse[0])
    long = long.assign(intercept=1.0)
    vc = {"game": "0 + C(game)", "pair": "0 + C(pair)"}
    mm = BinomialBayesMixedGLM.from_formula("y ~ arm", vc, long).fit_vb()
    i = list(mm.model.exog_names).index("arm")
    s4[h] = {"conditional_logit": {"log_or": beta, "se": se, "or": math.exp(beta),
                                   "or_ci": [math.exp(beta - 1.96 * se), math.exp(beta + 1.96 * se)],
                                   "p": float(2 * stats.norm.sf(abs(beta / se)))},
             "mixed_logit_vb": {"log_or_mean": float(mm.fe_mean[i]), "log_or_sd": float(mm.fe_sd[i]),
                                "or": math.exp(float(mm.fe_mean[i])),
                                "or_interval_95": [math.exp(float(mm.fe_mean[i]) - 1.96 * float(mm.fe_sd[i])),
                                                   math.exp(float(mm.fe_mean[i]) + 1.96 * float(mm.fe_sd[i]))]}}

for h in res:
    res[h].pop("_pairs")
json.dump({"confirmatory": res, "sensitivity_1_H1_all_rounds": {"rounds": s1_per, "pooled": s1_pool},
           "sensitivity_2_depth": s2, "sensitivity_3_leave_one_game_out": s3, "sensitivity_4_models": s4},
          open(out / "stage2_confirmatory.json", "w"), indent=1, default=float)

f = lambda x: f"{x:.3f}"; pc = lambda x: f"{100 * x:.1f}%"
md = ["# Stage 2: confirmatory tests", "",
      "Specified in [`../ANALYSIS-PLAN.md`](../ANALYSIS-PLAN.md) §2, committed before this analysis was run. "
      "Outcomes are from the engine replay (`data/levels.csv.gz`). Script: `analysis/stage2_confirmatory.py`. "
      "All numbers: `stage2_confirmatory.json`.", "",
      "## Primary results", "",
      "| | Design | Paired levels | Cleared: on / off | On only / off only | Clear-rate difference (95% CI) | Conditional OR (95% CI) | Exact p | Holm p | Same sign every round | Verdict by the plan's rule |",
      "|---|---|---|---|---|---|---|---|---|---|---|"]
for h, label in (("H1", "Lexicon on vs off, A3 round 3"), ("H2", "Probe-first on vs off, rounds 1+2")):
    pl = res[h]["pooled"]; on = sum(r["both"] + r["on_only"] for r in res[h]["rounds"]); off = sum(r["both"] + r["off_only"] for r in res[h]["rounds"])
    orr = pl["odds_ratio"]
    md.append(f"| **{h}** | {label} | {pl['n']} | {on} / {off} | {pl['on_only']} / {pl['off_only']} | "
              f"{pl['risk_difference']*100:+.1f} pts ({pl['rd_ci'][0]*100:+.1f} to {pl['rd_ci'][1]*100:+.1f}) | "
              f"{orr[0]:.2f} ({orr[1]:.2f}–{orr[2]:.2f}) | {f(pl['exact_p'])} | {f(pl['holm_p'])} | {'yes' if pl['same_sign_every_round'] else 'no'} | "
              f"**{'supported' if pl['supported'] else 'not detected at this size'}** |")
md += ["", "Per round:", "", "| | Round | Paired | Clear on | Clear off | On only / off only | Difference (95% CI) | Exact p |", "|---|---|---|---|---|---|---|---|"]
for h in res:
    for r in res[h]["rounds"]:
        md.append(f"| {h} | `{r['on'].split('@')[0]}` vs `{r['off'].split('@')[0]}` | {r['n']} | {pc(r['clear_on'])} | {pc(r['clear_off'])} | "
                  f"{r['on_only']} / {r['off_only']} | {r['risk_difference']*100:+.1f} pts ({r['rd_ci'][0]*100:+.1f} to {r['rd_ci'][1]*100:+.1f}) | {f(r['exact_p'])} |")
md += ["", "**Rule** (plan §2): supported only if the Holm-adjusted p < 0.05 and the sign is the same in every round run; "
       "otherwise *not detected at this size*, with the interval — not \"no effect\".", "",
       "## Sensitivity analyses (pre-set; reported whatever they show)", "",
       "**1. H1 including the two rounds that failed their validity checks** (labelled as such):", "",
       "| Round | Paired | On only / off only | Difference | Exact p |", "|---|---|---|---|---|"]
for r in s1_per:
    md.append(f"| `{r['on'].split('@')[0]}` | {r['n']} | {r['on_only']} / {r['off_only']} | {r['risk_difference']*100:+.1f} pts | {f(r['exact_p'])} |")
md.append(f"| pooled, stratified | {s1_pool['n']} | {s1_pool['on_only']} / {s1_pool['off_only']} | {s1_pool['risk_difference']*100:+.1f} pts "
          f"({s1_pool['rd_ci'][0]*100:+.1f} to {s1_pool['rd_ci'][1]*100:+.1f}) | {f(s1_pool['exact_p'])} |")
md += ["", "**2. By level depth:**", "", "| | Depth | Paired | On only / off only | Difference (95% CI) | Exact p |", "|---|---|---|---|---|---|"]
for h in s2:
    for dname in ("level 1", "levels 2-3", "levels 4+"):
        if dname in s2[h]:
            r = s2[h][dname]
            md.append(f"| {h} | {dname} | {r['n']} | {r['on_only']} / {r['off_only']} | {r['risk_difference']*100:+.1f} pts "
                      f"({r['rd_ci'][0]*100:+.1f} to {r['rd_ci'][1]*100:+.1f}) | {f(r['exact_p'])} |")
md += ["", "**3. Leave one game out** (25 games):", "", "| | Difference range | Exact p range | Games whose removal moves p across 0.05 |", "|---|---|---|---|"]
for h in s3:
    r = s3[h]
    md.append(f"| {h} | {r['rd_min']*100:+.1f} to {r['rd_max']*100:+.1f} pts | {f(r['p_min'])} to {f(r['p_max'])} | "
              f"{', '.join(r['games_whose_removal_crosses_0.05']) or 'none'} |")
md += ["", "**4. Logistic models** (robustness of the primary test):", "",
       "| | Conditional logit by level pair: OR (95% CI), p | Mixed logit with game and pair effects (variational Bayes): OR (95% interval) |", "|---|---|---|"]
for h in s4:
    a, b = s4[h]["conditional_logit"], s4[h]["mixed_logit_vb"]
    md.append(f"| {h} | {a['or']:.2f} ({a['or_ci'][0]:.2f}–{a['or_ci'][1]:.2f}), p = {f(a['p'])} | {b['or']:.2f} ({b['or_interval_95'][0]:.2f}–{b['or_interval_95'][1]:.2f}) |")
md += ["", "The mixed model is fitted by variational Bayes (statsmodels `BinomialBayesMixedGLM`); its interval is the approximate "
       "posterior mean ± 1.96 SD of the log odds ratio."]
(out / "stage2_confirmatory.md").write_text("\n".join(md) + "\n")
print("\n".join(md[:14]))
