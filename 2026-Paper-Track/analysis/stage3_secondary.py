"""Stage 3 of ANALYSIS-PLAN.md: secondary, descriptive analyses (no significance gate).

  python3.12 -I stage3_secondary.py DATA_DIR REPO_ROOT OUT_DIR

S1  run-to-run noise of whole-game save runs (identical code), with game-level bootstrap intervals
S2  the recorded whole-game tests (A1 replicates, A2 on/off) recomputed on replayed scores
S3  where the leaderboard draws of the Franzen-based notebooks sit against third-party copy variance
Outcomes come from data/replay.csv (engine replay). Leaderboard scores come from Submissions/ARC-AGI-3/submissions.csv.
"""
import itertools, json, statistics as st, sys
from pathlib import Path
import numpy as np
import pandas as pd

data, repo, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
R = pd.read_csv(data / "replay.csv"); R = R[R.trial == 0]
rng = np.random.default_rng(0)


def run_scores(run_id):
    g = R[R.run_id == run_id]
    return g.groupby(g.game_run.str[:4])["replay_score"].mean(), int(g.replay_levels_completed.sum())


def boot_ci(v, n=10000):
    v = np.asarray(v); idx = rng.integers(0, len(v), (n, len(v)))
    m = v[idx].mean(axis=1); return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


GROUPS = {  # identical code within each arm (byte-identical copies or flag-identical notebooks)
    "A1 lexicon v2 (10 games x 25 min)": ["arcaid3-lexicon-view-dfranzen-m2@v2", "arcaid3-rep-v2-r1@v1", "arcaid3-rep-v2-r2@v1"],
    "A1 lexicon v4, the selected code (10 games x 25 min)": ["arcaid3-lexicon-view-dfranzen-m2@v4", "arcaid3-rep-v4-r1@v1", "arcaid3-rep-v4-r2@v1"],
    "A2 lexicon v5 on (25 games x 121 min)": ["arcaid3-lb-lex-r1@v1", "arcaid3-lb-lex-r2@v1"],
    "A2 lexicon off (25 games x 121 min)": ["arcaid3-lb-off-r1@v1", "arcaid3-lb-off-r2@v1"],
}
s1 = {}
for name, runs in GROUPS.items():
    rows = []
    for r in runs:
        sc, lv = run_scores(r)
        lo, hi = boot_ci(sc.values)
        rows.append({"run": r, "games": len(sc), "mean": float(sc.mean()), "levels": lv, "bootstrap_ci": [lo, hi]})
    means = [x["mean"] for x in rows]
    s1[name] = {"runs": rows, "mean_of_means": st.mean(means), "sd_between_runs": st.stdev(means), "range": [min(means), max(means)]}

# S2 A1: exact one-sided permutation over the 20 splits of 6 runs (as recorded)
v2 = [x["mean"] for x in s1["A1 lexicon v2 (10 games x 25 min)"]["runs"]]
v4 = [x["mean"] for x in s1["A1 lexicon v4, the selected code (10 games x 25 min)"]["runs"]]
l2 = [x["levels"] for x in s1["A1 lexicon v2 (10 games x 25 min)"]["runs"]]
l4 = [x["levels"] for x in s1["A1 lexicon v4, the selected code (10 games x 25 min)"]["runs"]]
def perm(a, b):
    diff = st.mean(b) - st.mean(a); pool = a + b
    k = sum(1 for s in itertools.combinations(range(6), 3)
            if st.mean([pool[i] for i in s]) - st.mean([pool[i] for i in range(6) if i not in s]) >= diff - 1e-9)
    return diff, k
d_sc, k_sc = perm(v2, v4); d_lv, k_lv = perm(l2, l4)
a1 = {"v4_minus_v2_points": d_sc, "p_one_sided": k_sc / 20, "levels_v4_minus_v2": d_lv, "p_levels": k_lv / 20,
      "recorded": {"v4_minus_v2_points": -0.33, "p": 0.55, "levels": 0.0, "p_levels": 0.60}}

# S2 A2: per round on-off, primary = mean over rounds, per-game sign-flip test (200,000 flips, seed 0, as recorded)
on = [run_scores(r)[0] for r in GROUPS["A2 lexicon v5 on (25 games x 121 min)"]]
off = [run_scores(r)[0] for r in GROUPS["A2 lexicon off (25 games x 121 min)"]]
per_round = [float(a.mean() - b.mean()) for a, b in zip(on, off)]
games = sorted(set(on[0].index) & set(off[0].index))
per_game = np.array([np.mean([a[g] - b[g] for a, b in zip(on, off)]) for g in games])
flips = np.random.default_rng(0).choice([-1, 1], size=(200000, len(per_game)))
p_flip = float((np.abs((flips * per_game).mean(axis=1)) >= abs(per_game.mean()) - 1e-12).mean())
a2 = {"per_round_on_minus_off": per_round, "primary_mean_over_rounds": st.mean(per_round), "sign_flip_p_two_sided": p_flip,
      "recorded": {"per_round": [7.42, -7.49], "primary": -0.03, "p": 0.995},
      "rule_outcome": "no measurable effect" if (st.mean(per_round) < 2.0 or per_round[-1] <= 0) else
                      ("recommend" if st.mean(per_round) >= 5 and all(x > 0 for x in per_round) and p_flip < 0.10 else "inconclusive")}

# S3 leaderboard draws of the Franzen-based notebooks
S = pd.read_csv(repo / "Submissions/ARC-AGI-3/submissions.csv")
S = S[S.kernel.fillna("").str.contains("arcaid3") & (S.status == "COMPLETE")]
S = S[pd.to_numeric(S.public_score, errors="coerce") > 1]          # exclude the 0.00 infrastructure failures and the 7.16 misconfigured trial build
ref_mean, ref_sd = 25.77, 3.93                                      # third party: Son Pham, Kaggle discussion 745062
draws = [{"kernel": k.split("/")[-1], "script_version_id": int(v), "score": float(s), "selected": bool(sel == "yes"),
          "z_vs_copies": (float(s) - ref_mean) / ref_sd}
         for k, v, s, sel in zip(S.kernel, S.script_version_id, S.public_score, S.selected.fillna(""))]
s3 = {"reference_copies": {"mean": ref_mean, "sd": ref_sd, "source": "Son Pham, Kaggle discussion 745062 (third party)"},
      "draws": draws, "our_mean": st.mean(d["score"] for d in draws), "our_sd": st.stdev(d["score"] for d in draws), "n": len(draws),
      "excluded": "0.00 scores (slow model loads, 21-25 October; Kaggle discussion 751598) and 7.16 (a level-trial build submitted with trial settings)"}

json.dump({"S1_noise": s1, "S2_A1": a1, "S2_A2": a2, "S3_leaderboard": s3}, open(out / "stage3_secondary.json", "w"), indent=1)

md = ["# Stage 3: secondary analyses (descriptive)", "",
      "Specified in [`../ANALYSIS-PLAN.md`](../ANALYSIS-PLAN.md) §3. Scores are RHAE on the public games, re-derived by the engine "
      "replay (`data/replay.csv`). Script: `analysis/stage3_secondary.py`; all numbers: `stage3_secondary.json`.", "",
      "## S1. Run-to-run noise of identical code", "",
      "| Arm (setup) | Run | Mean score | Levels | Game-bootstrap 95% CI |", "|---|---|---|---|---|"]
for name, g in s1.items():
    for r in g["runs"]:
        md.append(f"| {name} | `{r['run']}` | {r['mean']:.2f} | {r['levels']} | {r['bootstrap_ci'][0]:.1f}–{r['bootstrap_ci'][1]:.1f} |")
    md.append(f"| | **between runs** | **{g['mean_of_means']:.2f}** (SD {g['sd_between_runs']:.2f}, range {g['range'][0]:.2f}–{g['range'][1]:.2f}) | | |")
md += ["", "## S2. Recorded whole-game tests, recomputed on replayed scores", "",
       "| Test | Recomputed | Recorded in October | Agree |", "|---|---|---|---|",
       f"| A1: v4 − v2, mean of 3 runs each | {a1['v4_minus_v2_points']:+.2f} points, one-sided permutation p = {a1['p_one_sided']:.2f} | −0.33, p = 0.55 | "
       f"{'yes' if abs(a1['v4_minus_v2_points'] + 0.33) < 0.006 and abs(a1['p_one_sided'] - 0.55) < 1e-9 else 'no'} |",
       f"| A1: levels v4 − v2 | {a1['levels_v4_minus_v2']:+.1f}, p = {a1['p_levels']:.2f} | +0.0, p = 0.60 | "
       f"{'yes' if abs(a1['levels_v4_minus_v2']) < 1e-9 and abs(a1['p_levels'] - 0.60) < 1e-9 else 'no'} |",
       f"| A2: on − off per round | {', '.join(f'{x:+.2f}' for x in a2['per_round_on_minus_off'])} | +7.42, −7.49 | "
       f"{'yes' if all(abs(x - y) < 0.006 for x, y in zip(a2['per_round_on_minus_off'], [7.42, -7.49])) else 'no'} |",
       f"| A2: primary (mean over rounds), sign-flip p | {a2['primary_mean_over_rounds']:+.2f}, p = {a2['sign_flip_p_two_sided']:.3f} | −0.03, p = 0.995 | "
       f"{'yes' if abs(a2['primary_mean_over_rounds'] + 0.03) < 0.006 else 'no'} |",
       f"| A2: outcome under its own rule | {a2['rule_outcome']} | no measurable effect | {'yes' if a2['rule_outcome'] == 'no measurable effect' else 'no'} |",
       "", "The restart tests (`Ablations/ARC-AGI-3/2026-10-12__restart-v1`, `2026-10-13__restart-pair`) are defined on restart events "
       "(`stuck_restarts.jsonl`), not on replayable outcomes; they are not recomputed here and remain as recorded.", "",
       "## S3. Leaderboard draws of the Franzen-based notebooks", "",
       f"Reference: unchanged copies of Franzen's notebook scored {ref_mean} ± {ref_sd} (third party: Son Pham, Kaggle discussion 745062). "
       f"Excluded: {s3['excluded']}.", "",
       "| Notebook | Public score | Selected | Distance from the copies' mean, in their SD |", "|---|---|---|---|"]
for d in sorted(draws, key=lambda x: -x["score"]):
    md.append(f"| `{d['kernel']}` | {d['score']:.2f} | {'yes' if d['selected'] else ''} | {d['z_vs_copies']:+.2f} |")
md += ["", f"Our {s3['n']} draws: mean {s3['our_mean']:.2f}, SD {s3['our_sd']:.2f}. Each public score is one run on half of the hidden games; "
       "hidden-set runs cannot be replayed, so this comparison is descriptive only."]
(out / "stage3_secondary.md").write_text("\n".join(md) + "\n")
print("\n".join(md[:30]))
