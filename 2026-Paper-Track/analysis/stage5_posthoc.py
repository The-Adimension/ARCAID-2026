"""Stage 5 of ANALYSIS-PLAN.md (section 8): post hoc analyses P1-P6, added after the Stage 2-4 results were seen.
Post hoc: these results suggest; they do not confirm, and no Stage 2-4 verdict changes because of them.

  python3.12 -I stage5_posthoc.py DATA_DIR REPO_ROOT OUT_DIR

Reads the tables in DATA_DIR. For setup checks it also reads, in REPO_ROOT, the run.json, log.txt and notebook.ipynb
of the runs (folders as listed in replay.csv), and OUT_DIR/stage4_exploratory.json to check that P6 starts from
the same turns and numbers as Stage 4 M1. Seeds are fixed per section; Monte Carlo sizes are stated with each result.
"""
import json, re, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import optimize, special, stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

data, repo, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
K = ["run_id", "game_run", "pass"]
L = pd.read_csv(data / "levels.csv.gz")
R = pd.read_csv(data / "replay.csv")
A = pd.read_csv(data / "actions.csv.gz", dtype={"board_hash": str})
C = pd.read_csv(data / "calls.csv.gz")
E = pd.read_csv(data / "events.csv.gz")
T = pd.read_csv(data / "turns.csv.gz")
res = {"checks": {}}

# The six runs of the paired level-trial designs (183 cold-start levels each, 20 minutes per level)
RUNS = {"C1": "arcaid3-lt-off-r3@v1", "C2": "arcaid3-lt-pf-off-r1@v1", "C3": "arcaid3-lt-pf-off-r2@v1",
        "PF1": "arcaid3-lt-pf-on-r1@v1", "PF2": "arcaid3-lt-pf-on-r2@v1", "LEX": "arcaid3-lt-lex-r3@v1"}
ROLE = {"C1": "control, lexicon design round 3", "C2": "control, probe-first round 1", "C3": "control, probe-first round 2",
        "PF1": "probe-first on, round 1", "PF2": "probe-first on, round 2", "LEX": "lexicon on, round 3"}
CTRL = ["C1", "C2", "C3"]
PAIRS_AB = [("PF1", "C2"), ("PF2", "C3"), ("LEX", "C1")]      # same-day add-on vs control (the Stage 2 pairs)
PAIRS_AA = [("C1", "C2"), ("C1", "C3"), ("C2", "C3")]         # unchanged agent against itself
folder = R.drop_duplicates("run_id").set_index("run_id").folder
runjson = {rid: json.loads((repo / f / "run.json").read_text()) for rid, f in folder.items()}
root = {rid: (j.get("root_base") or "") for rid, j in runjson.items()}
start = {k: runjson[v]["run"].get("start") for k, v in RUNS.items()}
pc = lambda x: f"{100 * x:.1f}%"
pts = lambda x: f"{100 * x:+.1f}"
esc = lambda s: s.replace("|", "\\|")

# ------------------------------------------------------------------ setup checks: what the control arms ran
def addon_lines(run_id):
    log = (repo / folder[run_id] / "log.txt").read_text(errors="replace").splitlines()
    return [ln.split("| ", 1)[-1].strip()[:400] for ln in log if re.search(r"ARC3_PF_(ARM|READY|FINAL)|ARCAID3_LEXICON_(READY|FINAL)", ln)]


def nb_cells(run_id):
    nb = json.loads((repo / folder[run_id] / "notebook.ipynb").read_text())
    return [("".join(c["source"]) if isinstance(c["source"], list) else c["source"], c["cell_type"]) for c in nb["cells"]]


setup = {"start_utc": start, "addon_log_lines": {k: addon_lines(v) for k, v in RUNS.items()}, "notebooks": {}}
cells = {k: nb_cells(v) for k, v in RUNS.items()}
for group, names in (("three controls", CTRL), ("round 1 arms", ["PF1", "C2"]), ("round 2 arms", ["PF2", "C3"]), ("lexicon round 3 arms", ["LEX", "C1"])):
    n = {len(cells[x]) for x in names}
    diff = []
    if len(n) == 1:
        for i in range(n.pop()):
            if len({cells[x][i][0] for x in names}) > 1:
                diff.append({"cell": i, "type": cells[names[0]][i][1],
                             "first_lines": {x: cells[x][i][0].strip().splitlines()[0][:120] if cells[x][i][0].strip() else "" for x in names}})
    setup["notebooks"][group] = {"runs": names, "cells": sorted({len(cells[x]) for x in names}), "differing_cells": diff,
                                 "identical_cells": (len(cells[names[0]]) - len(diff)) if len({len(cells[x]) for x in names}) == 1 else None}
installed = {}
for k in RUNS:
    txt = " ".join(setup["addon_log_lines"][k])
    installed[k] = bool(re.search(r"ARC3_PF_READY installed|'installed': True", txt))
setup["addon_installed"] = installed
res["checks"]["controls_install_nothing"] = all(not installed[k] for k in CTRL) and all(installed[k] for k in ("PF1", "PF2", "LEX"))
res["setup"] = setup

# ------------------------------------------------------------------ the level-by-run matrix
TR = L[(L.trial == 1) & L.run_id.isin(RUNS.values())]
assert TR.groupby(K).size().max() == 1, "a level trial has more than one row"
M = pd.DataFrame({k: TR[TR.run_id == v].set_index("game_run").cleared for k, v in RUNS.items()})
assert len(M) == 183 and not M.isna().any().any()
M = M.astype(int)


def mcnemar(a, b):
    on, off = int(((a == 1) & (b == 0)).sum()), int(((a == 0) & (b == 1)).sum())
    n = on + off
    return on, off, (1.0 if n == 0 else min(1.0, 2 * stats.binom.cdf(min(on, off), n, 0.5)))


def kappa(a, b):
    po = (a == b).mean(); pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    return float((po - pe) / (1 - pe))


# ------------------------------------------------------------------ P1. A/A: the unchanged agent against itself
p1 = {"cleared": {k: int(v) for k, v in M.sum().items()}, "pairs": {}}
for x, y in PAIRS_AA + [("PF1", "PF2")] + PAIRS_AB:
    b, c, p = mcnemar(M[x], M[y])
    p1["pairs"][f"{x} vs {y}"] = {"kind": "A/A" if (x, y) in PAIRS_AA or (x, y) == ("PF1", "PF2") else "add-on vs same-day control",
                                  "cleared": [int(M[x].sum()), int(M[y].sum())], "only_first": b, "only_second": c,
                                  "disagreeing_levels": b + c, "exact_p": p, "kappa": kappa(M[x], M[y])}
Cm = M[CTRL].values; n_l, r_ = Cm.shape; gm = Cm.mean()
msb = r_ * ((Cm.mean(1) - gm) ** 2).sum() / (n_l - 1); msw = ((Cm - Cm.mean(1, keepdims=True)) ** 2).sum() / (n_l * (r_ - 1))
p1["icc1_controls"] = float((msb - msw) / (msb + (r_ - 1) * msw))
p1["levels_by_runs_clearing_of_6"] = {int(k): int(v) for k, v in M.sum(axis=1).value_counts().sort_index().items()}
p1["levels_by_controls_clearing_of_3"] = {int(k): int(v) for k, v in M[CTRL].sum(axis=1).value_counts().sort_index().items()}
res["P1"] = p1

# ------------------------------------------------------------------ P2. Power and overstatement, calibrated to the A/A
def fit_bb(k, n):
    def nll(t):
        a, b = np.exp(t)
        return -np.sum(special.gammaln(n + 1) - special.gammaln(k + 1) - special.gammaln(n - k + 1)
                       + special.betaln(k + a, n - k + b) - special.betaln(a, b))
    r = optimize.minimize(nll, [0.0, 0.0], method="Nelder-Mead", options={"xatol": 1e-8, "fatol": 1e-10, "maxiter": 4000})
    return [float(x) for x in np.exp(r.x)]


def shifted(p, g):
    """Per simulated run of levels (rows of p): add the same log-odds shift to every level, chosen so that the mean gain is g."""
    if g == 0:
        return p
    lp = np.log(np.clip(p, 1e-12, 1 - 1e-12) / np.clip(1 - p, 1e-12, 1))
    lo = np.full(len(p), -30.0); hi = np.full(len(p), 30.0)
    target = p.mean(1) + g
    for _ in range(80):
        mid = (lo + hi) / 2
        f = special.expit(lp + mid[:, None]).mean(1) - target
        lo = np.where(f < 0, mid, lo); hi = np.where(f >= 0, mid, hi)
    return special.expit(lp + ((lo + hi) / 2)[:, None])


def simulate(k, n, a, b, g, rounds, sims, rng):
    p = rng.beta(a + k, b + n - k, size=(sims, len(k)))
    pt = shifted(p, g)
    x = rng.random((sims, rounds, len(k))) < p[:, None, :]
    t = rng.random((sims, rounds, len(k))) < pt[:, None, :]
    on = (t & ~x).sum((1, 2)); off = (x & ~t).sum((1, 2)); nn = on + off
    pval = np.where(nn > 0, np.minimum(1.0, 2 * stats.binom.cdf(np.minimum(on, off), nn, 0.5)), 1.0)
    detected = (pval < 0.05) & ((on > off) if g >= 0 else (off > on))
    return detected, (on - off) / (rounds * len(k)), nn / rounds


rng = np.random.default_rng(5)
obs_aa = [p1["pairs"][f"{x} vs {y}"]["disagreeing_levels"] for x, y in PAIRS_AA]
kc = M[CTRL].sum(axis=1).values
p_first = (kc + 0.5) / 4.0                               # the first, scratch model (replaced; see ANALYSIS-PLAN.md section 8)
p2 = {"observed_aa_disagreeing_levels": obs_aa, "first_pass_model_expected_disagreeing_levels": float(np.sum(2 * p_first * (1 - p_first))),
      "models": {}}
for label, cols, sims in (("fitted to the 3 controls (primary)", CTRL, 4000), ("fitted to all 6 runs (sensitivity)", list(RUNS), 2000)):
    k = M[cols].sum(axis=1).values; n = len(cols); a, b = fit_bb(k, n)
    _, _, dis = simulate(k, n, a, b, 0.0, 1, 20000, rng)
    band = [float(np.percentile(dis, 5)), float(np.percentile(dis, 95))]
    mdl = {"alpha": a, "beta": b, "simulated_aa_disagreeing_levels": {"mean": float(dis.mean()), "p5": band[0], "p95": band[1]},
           "calibration_ok": bool(all(band[0] <= o <= band[1] for o in obs_aa)), "power": {}, "overstatement": {}}
    for g in (0.03, 0.05, 0.08, 0.10):
        for rounds in (1, 2, 4):
            det, _, _ = simulate(k, n, a, b, g, rounds, sims, rng)
            mdl["power"][f"gain {g * 100:.0f} pts, {rounds} round(s)"] = float(det.mean())
    for g in (-0.05, -0.08):
        det, _, _ = simulate(k, n, a, b, g, 1, sims, rng)
        mdl["power"][f"harm {abs(g) * 100:.0f} pts, 1 round"] = float(det.mean())
    for g in (0.033, 0.049):
        det, est, _ = simulate(k, n, a, b, g, 2, 20000, rng)
        mdl["overstatement"][f"true gain {g * 100:.1f} pts, 2 rounds"] = {"power": float(det.mean()), "mean_significant_estimate": float(est[det].mean()),
                                                                          "ratio": float(est[det].mean() / g), "simulations": 20000}
    mdl["simulations_per_power_cell"] = sims
    p2["models"][label] = mdl
res["checks"]["power_model_matches_aa"] = all(m_["calibration_ok"] for m_ in p2["models"].values())
res["P2"] = p2

# ------------------------------------------------------------------ P3. Each add-on against all three controls (exact permutation)
def perm_exact(treat, ctrl):
    X = M[treat + ctrl].values; nt, nc = len(treat), len(ctrl); N = nt + nc
    m = X.sum(1)
    obs = float((X[:, :nt].mean(1) - X[:, nt:].mean(1)).mean())
    pmf = np.array([1.0])
    for mi in m:
        v = stats.hypergeom.pmf(np.arange(nt + 1), N, mi, nt)
        pmf = np.convolve(pmf, v)
    H = np.arange(len(pmf))
    S = ((1 / nt + 1 / nc) * H - m.sum() / nc) / len(m)
    return obs, float(pmf[np.abs(S) >= abs(obs) - 1e-12].sum())


p3 = {}
for name, cols in (("probe-first (PF1, PF2) vs C1-C3", ["PF1", "PF2"]), ("lexicon (LEX) vs C1-C3", ["LEX"])):
    d, p = perm_exact(cols, CTRL)
    p3[name] = {"clear_rate_add_on": float(M[cols].values.mean()), "clear_rate_controls": float(M[CTRL].values.mean()),
                "difference": d, "exact_permutation_p_two_sided": p}
res["P3"] = p3

# ------------------------------------------------------------------ per-trial effort table (P4, P5)
Atr = A[A.run_id.isin(RUNS.values())].sort_values(K + ["action_index"])
Ctr = C[C.run_id.isin(RUNS.values())]
inv = {v: k for k, v in RUNS.items()}
rows = []
agroups = {key: g for key, g in Atr.groupby(K)}; cgroups = {key: g for key, g in Ctr.groupby(K, sort=False)}
for _, lv in TR.iterrows():
    key = (lv.run_id, lv.game_run, lv["pass"]); kk = int(lv.level)
    g = agroups.get(key, Atr.iloc[0:0]); cc = cgroups.get(key, Ctr.iloc[0:0])
    st_ = g[g.level == kk]; clr = st_[st_.level_completed == 1]
    ci = int(clr.action_index.iloc[0]) if len(clr) else None
    an = cc.action_num.fillna(0)
    rows.append({"arm": inv[lv.run_id], "game_run": lv.game_run, "game": lv.game, "k": kk, "human": int(lv.human_actions), "cleared": int(lv.cleared),
                 "total_tokens": int(cc.completion_tokens.sum()), "responses": int(len(cc)), "actions_total": int(len(g)),
                 "tokens_to_clear": int(cc[an <= ci].completion_tokens.sum()) if ci else np.nan,
                 "responses_to_clear": int((an <= ci).sum()) if ci else np.nan, "actions_to_clear": ci if ci else np.nan,
                 "start_level_actions": int(len(st_)), "start_level_distinct_boards": int(st_.board_hash.nunique()),
                 "tokens_before_first_action": int(cc[an <= 1].completion_tokens.sum())})
TE = pd.DataFrame(rows)
TE["budget_fraction_at_clear"] = TE.tokens_to_clear / TE.total_tokens
assert (TE.groupby("arm").size() == 183).all()
res["checks"]["trial_clears_match_replayed_actions"] = bool((TE.cleared == TE.actions_to_clear.notna().astype(int)).all())

# ------------------------------------------------------------------ P4. Did probe-first change what it targets?
def streaks(run_id):
    c = C[C.run_id == run_id]
    mono = []; lens = []; tok_all = 0; tok_long = 0
    for _, g in c.groupby(K, sort=False):
        mono.append(bool((np.diff(g.analysis_step.values) >= 0).all()))
        prev = 0; s = 0; stoks = []
        for a_, ct in zip(g.action_num.fillna(0), g.completion_tokens.fillna(0)):
            tok_all += ct
            if a_ <= prev:
                s += 1; stoks.append(ct)
            else:
                if s:
                    lens.append(s)
                    tok_long += sum(stoks) if s >= 5 else 0
                s = 0; stoks = []
            prev = a_
        if s:
            lens.append(s); tok_long += sum(stoks) if s >= 5 else 0
    x = np.array(lens)
    return {"streaks": int(len(x)), "median": float(np.median(x)), "p90": float(np.percentile(x, 90)), "max": int(x.max()),
            "share_5_or_more": float((x >= 5).mean()), "share_10_or_more": float((x >= 10).mean()),
            "token_share_in_streaks_5_or_more": float(tok_long / tok_all), "calls_in_time_order": float(np.mean(mono))}


def pf_final(k):
    for ln in setup["addon_log_lines"][k]:
        if ln.startswith("ARC3_PF_FINAL"):
            return ln[len("ARC3_PF_FINAL"):].strip()
    return None


p4 = {"governor_counters": {k: pf_final(k) for k in ("PF1", "PF2", "C2", "C3")}, "streaks": {k: streaks(v) for k, v in RUNS.items()},
      "moves_per_trial": {}, "effort_on_levels_both_cleared": {}, "budget": {}}
for x, y in PAIRS_AB + PAIRS_AA:
    a_ = TE[TE.arm == x].set_index("game_run").actions_total; b_ = TE[TE.arm == y].set_index("game_run").actions_total.reindex(a_.index)
    w = stats.wilcoxon(a_, b_)
    p4["moves_per_trial"][f"{x} vs {y}"] = {"n": int(len(a_)), "median": [float(a_.median()), float(b_.median())],
                                            "mean_difference": float((a_ - b_).mean()), "median_difference": float((a_ - b_).median()), "wilcoxon_p": float(w.pvalue)}
    ta = TE[TE.arm == x].set_index("game_run"); tb = TE[TE.arm == y].set_index("game_run")
    both = ta.index[ta.cleared == 1].intersection(tb.index[tb.cleared == 1])
    e = {"levels": int(len(both))}
    for col in ("tokens_to_clear", "responses_to_clear", "actions_to_clear"):
        u, v = ta.loc[both, col].astype(float), tb.loc[both, col].astype(float)
        w = stats.wilcoxon(np.log(u + 1), np.log(v + 1))
        e[col] = {"median": [float(u.median()), float(v.median())], "median_ratio": float(np.exp(np.median(np.log((u + 1) / (v + 1))))),
                  "first_lower": int((u < v).sum()), "wilcoxon_p": float(w.pvalue)}
    p4["effort_on_levels_both_cleared"][f"{x} vs {y}"] = e
for k in RUNS:
    t = TE[TE.arm == k]
    p4["budget"][k] = {"median_tokens_per_trial": float(t.total_tokens.median()), "total_tokens": int(t.total_tokens.sum()), "cleared": int(t.cleared.sum()),
                       "tokens_per_cleared_level": float(t.total_tokens.sum() / max(1, t.cleared.sum())),
                       "median_tokens_before_first_action": float(t.tokens_before_first_action.median())}
for x, y in PAIRS_AB:
    p4["budget"][f"{x} / {y}"] = {"total_tokens_ratio": p4["budget"][x]["total_tokens"] / p4["budget"][y]["total_tokens"],
                                  "cleared_ratio": p4["budget"][x]["cleared"] / p4["budget"][y]["cleared"]}
res["P4"] = p4

# ------------------------------------------------------------------ P5. What limits the score?
p5 = {}
# (a) score anatomy of whole-game runs, grouped by the root base recorded in run.json
W = R[R.trial == 0].copy()
W["base_group"] = np.where(W.run_id.map(root).str.startswith("dfranzen/"), "Franzen-based", "Duck/TAAF-based")
LW = {key: g.sort_values("level") for key, g in L[L.trial == 0].groupby(K)}
# A game's levels and their human baselines: every level of each public game was a level-trial start. (levels.csv.gz lists only
# the levels a whole-game run reached.) See ANALYSIS-PLAN.md section 7, deviation of 2026-11-07.
TRALL = L[L.trial == 1].assign(gid=lambda d: d.game_run.str.split("@").str[0])
cnt = TRALL.groupby(["run_id", "gid"])["level"].agg(["count", "max"])
res["checks"]["trial_starts_cover_every_level"] = bool((cnt["count"] == cnt["max"] + 1).all() and (cnt["count"].unstack("run_id").nunique(axis=1) == 1).all())
BASE = {g: d.sort_values("level").human_actions.values.astype(float) for g, d in TRALL.drop_duplicates(["gid", "level"]).groupby("gid")}
res["checks"]["public_games_and_levels"] = [len(BASE), int(sum(len(b) for b in BASE.values()))]
an_rows = []; rhae_dev = []; order_bad = 0; base_bad = 0
for _, r in W.iterrows():
    lv = LW[(r.run_id, r.game_run, r["pass"])].set_index("level")
    base = BASE[r.game_run]; n = len(base); w = n * (n + 1) / 2
    base_bad += int((lv.human_actions.values != base[lv.index.values]).any())
    apl = lv.our_actions.reindex(range(n)).fillna(0).values.astype(float)
    clr = lv.cleared.reindex(range(n)).fillna(0).values.astype(int)
    done = int(r.replay_levels_completed)
    order_bad += int(not (clr[:done].all() and not clr[done:].any()))
    cap = sum(range(1, done + 1)) / w * 100
    s = sum((i + 1) * min((base[i] / apl[i]) ** 2, 1.15) for i in range(done) if apl[i] > 0) / w * 100
    rhae_dev.append(abs(min(s, cap) - r.replay_score))
    s5 = 0.0; done5 = 0
    for i in range(done):
        if apl[i] > 5 * base[i]:
            break
        s5 += (i + 1) * min((base[i] / apl[i]) ** 2, 1.15) if apl[i] else 0; done5 = i + 1
    s5 = min(s5 / w * 100, sum(range(1, done5 + 1)) / w * 100)
    nxt = (done + 1) / w * 100 if done < n else 0.0
    an_rows.append({"group": r.base_group, "score": r.replay_score, "ceiling": cap, "lost_uncleared": 100 - cap, "lost_inefficiency": cap - r.replay_score,
                    "levels_over_5x": int(((clr == 1) & (apl > 5 * base)).sum()), "score_5x_rule": s5,
                    "next_level_ceiling_raise": nxt, "next_level_max_gain": min(1.15 * nxt, (cap - r.replay_score) + nxt) if done < n else 0.0})
AN = pd.DataFrame(an_rows)
res["checks"]["rhae_formula_reproduces_engine_scores_max_abs_diff"] = float(max(rhae_dev))
res["checks"]["whole_game_levels_cleared_in_order"] = order_bad == 0
res["checks"]["whole_game_baselines_match_trial_starts"] = base_bad == 0
p5["score_anatomy"] = {}
for gname, g in AN.groupby("group"):
    p5["score_anatomy"][gname] = {"runs": sorted(W[W.base_group == gname].run_id.unique().tolist()), "game_runs": int(len(g)),
        "mean_score": float(g.score.mean()), "mean_ceiling": float(g.ceiling.mean()), "mean_lost_uncleared": float(g.lost_uncleared.mean()),
        "mean_lost_inefficiency": float(g.lost_inefficiency.mean()),
        "inefficiency_share_of_lost_score": float(g.lost_inefficiency.sum() / (g.lost_inefficiency.sum() + g.lost_uncleared.sum())),
        "cleared_levels_over_5x_human": int(g.levels_over_5x.sum()), "game_runs_with_a_level_over_5x": int((g.levels_over_5x > 0).sum()),
        "mean_score_with_5x_rule": float(g.score_5x_rule.mean()), "mean_next_level_ceiling_raise": float(g.next_level_ceiling_raise.mean()),
        "mean_next_level_max_gain": float(g.next_level_max_gain.mean())}
# (b) difficulty: what predicts a clear for the unchanged agent (3 controls x 183 levels)
CT = TR[TR.run_id.isin([RUNS[k] for k in CTRL])].copy()
CT["log_h"] = np.log(CT.human_actions); CT["depth"] = CT.level + 1
lvc = CT.groupby(["game_run", "game", "depth", "human_actions"]).cleared.mean().reset_index()
q = lvc.human_actions.quantile([0.25, 0.5, 0.75]).tolist()
hb = pd.cut(lvc.human_actions, [0, q[0], q[1], q[2], np.inf])
db = pd.cut(lvc.depth, [0, 1, 3, 6, 10])
glm = smf.glm("cleared ~ log_h + depth", CT, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(CT.game)[0]})
pg = lvc.groupby("game").cleared.mean()
p5["difficulty"] = {"levels": int(len(lvc)), "human_actions_quartiles": q,
                    "spearman_clear_rate_vs_human_actions": [float(x) for x in stats.spearmanr(lvc.cleared, lvc.human_actions)],
                    "spearman_clear_rate_vs_depth": [float(x) for x in stats.spearmanr(lvc.cleared, lvc.depth)],
                    "clear_rate_by_human_actions": {str(k): [int(v["size"]), float(v["mean"])] for k, v in lvc.groupby(hb, observed=True).cleared.agg(["size", "mean"]).iterrows()},
                    "clear_rate_by_depth": {str(k): [int(v["size"]), float(v["mean"])] for k, v in lvc.groupby(db, observed=True).cleared.agg(["size", "mean"]).iterrows()},
                    "logistic_clustered_by_game": {t: {"coef": float(glm.params[t]), "se": float(glm.bse[t]), "p": float(glm.pvalues[t]),
                                                       "ci": [float(x) for x in glm.conf_int().loc[t]]} for t in glm.params.index},
                    "trials_in_model": int(len(CT)), "games": int(CT.game.nunique()),
                    "per_game_clear_rate": {"min": float(pg.min()), "median": float(pg.median()), "max": float(pg.max()), "games_never_cleared": int((pg == 0).sum())}}
# (c) the time budget: when clears happen within each trial
cks = [2500, 5000, 10000, 20000, 40000, 80000]
p5["budget"] = {}
for k in RUNS:
    t = TE[TE.arm == k]; cl = t[t.cleared == 1]
    p5["budget"][k] = {"clears": int(len(cl)), "median_budget_fraction_at_clear": float(cl.budget_fraction_at_clear.median()),
                       "share_of_clears_in_last_quarter": float((cl.budget_fraction_at_clear > 0.75).mean()),
                       "cumulative_share_of_183_cleared_by_tokens": {str(x): float((t.tokens_to_clear <= x).sum() / 183) for x in cks}}
# (d) levels cleared by one run of a pair vs by both: where in the trial
p5["timing_one_vs_both"] = {}
for x, y in PAIRS_AB + PAIRS_AA:
    fx = TE[TE.arm == x].set_index("game_run").budget_fraction_at_clear; fy = TE[TE.arm == y].set_index("game_run").budget_fraction_at_clear
    ox = M.index[(M[x] == 1) & (M[y] == 0)]; oy = M.index[(M[x] == 0) & (M[y] == 1)]; bo = M.index[(M[x] == 1) & (M[y] == 1)]
    one = pd.concat([fx.loc[ox], fy.loc[oy]]); both = pd.concat([fx.loc[bo], fy.loc[bo]])
    p5["timing_one_vs_both"][f"{x} vs {y}"] = {"kind": "A/A" if (x, y) in PAIRS_AA else "add-on vs same-day control",
                                                "one_run_only": {"n": int(len(one)), "median": float(one.median())},
                                                "both": {"n": int(len(both)), "median": float(both.median())},
                                                "mann_whitney_p": float(stats.mannwhitneyu(one, both).pvalue)}
# (e) failed trials: moves made against the human count and against the moves clears needed
TE["moves_over_human"] = TE.start_level_actions / TE.human
cl_ = TE[TE.cleared == 1]; fl = TE[TE.cleared == 0]
p10 = float(cl_.moves_over_human.quantile(0.10))
p5["failed_trials"] = {"failed": int(len(fl)), "cleared": int(len(cl_)),
                       "cleared_moves_over_human": {"median": float(cl_.moves_over_human.median()), "p10": p10, "p05": float(cl_.moves_over_human.quantile(0.05))},
                       "failed_moves_over_human_median": float(fl.moves_over_human.median()),
                       "failed_share_below_human_count": float((fl.moves_over_human < 1).mean()),
                       "failed_share_below_p10_of_clears": float((fl.moves_over_human < p10).mean()),
                       "failed_median_moves": float(fl.start_level_actions.median()), "cleared_median_moves_to_clear": float(cl_.actions_to_clear.median()),
                       "by_human_actions": {}}
for lo, hi in ((0, q[0]), (q[0], q[1]), (q[1], q[2]), (q[2], np.inf)):
    f_ = fl[(fl.human > lo) & (fl.human <= hi)]; c_ = cl_[(cl_.human > lo) & (cl_.human <= hi)]
    qq = float(c_.moves_over_human.quantile(0.10)) if len(c_) >= 5 else float("nan")
    p5["failed_trials"]["by_human_actions"][f"({lo:g}, {hi:g}]"] = {
        "failed": int(len(f_)), "failed_median_moves": float(f_.start_level_actions.median()), "human_median": float(f_.human.median()),
        "failed_median_moves_over_human": float(f_.moves_over_human.median()), "failed_share_below_human_count": float((f_.moves_over_human < 1).mean()),
        "clears": int(len(c_)), "clears_p10_moves_over_human": qq, "failed_share_below_that": float((f_.moves_over_human < qq).mean())}
# (f) exploration on failed trials, and (g) the frontier of levels ever cleared
nov = fl[fl.start_level_actions > 0].assign(novelty=lambda d: 100 * d.start_level_distinct_boards / d.start_level_actions)
p5["failed_trial_new_boards_per_100_moves"] = {k: float(v) for k, v in nov.groupby("arm").novelty.median().items()}
U3 = M[CTRL].sum(axis=1) > 0
p5["frontier"] = {"levels_cleared_by_any_control": int(U3.sum()), "levels_cleared_by_any_run": int((M.sum(axis=1) > 0).sum()),
                  "levels_cleared_by_every_run": int((M.sum(axis=1) == 6).sum()),
                  "new_beyond_the_3_controls": {k: int(((M[k] == 1) & ~U3).sum()) for k in ("PF1", "PF2", "LEX")},
                  "new_beyond_the_3_controls_PF1_or_PF2": int((((M.PF1 + M.PF2) > 0) & ~U3).sum()),
                  "reference_one_control_beyond_the_other_two": {c: int(((M[c] == 1) & ~(M[[x for x in CTRL if x != c]].sum(axis=1) > 0)).sum()) for c in CTRL}}
res["P5"] = p5

# ------------------------------------------------------------------ P6. Reading the lexicon, matched on situation
# Same turns and outcomes as Stage 4 M1 (construction copied from stage4_exploratory.py), restricted to lexicon-on runs.
LEXRE = "lexicon-view|rep-v|lb-lex|lt-lex|dprime"
lexruns = set(T.run_id[T.run_id.str.contains(LEXRE)])
A6 = A[A.run_id.isin(lexruns)].sort_values(K + ["action_index"]).copy()
A6["revisit"] = A6.duplicated(subset=K + ["level", "board_hash"]).astype(int)
E6 = E[E.run_id.isin(lexruns)]; T6 = T[T.run_id.isin(lexruns)]
EA = E6[K + ["action_num", "analysis_step"]].merge(A6, left_on=K + ["action_num"], right_on=K + ["action_index"], how="left")
per_turn = EA.groupby(K + ["analysis_step"]).agg(n_actions=("action_index", "size"), changed=("board_changed", "sum"),
                                                  lvl_done=("level_completed", "max"), over=("game_over", "max"), first_level=("level", "first")).reset_index()
TT = T6.merge(per_turn, on=K + ["analysis_step"], how="left").fillna({"n_actions": 0, "changed": 0, "lvl_done": 0, "over": 0})
nxt_ = A6[K + ["action_index", "level"]].rename(columns={"action_index": "first_action_num", "level": "next_level"})
TT = TT.merge(nxt_, on=K + ["first_action_num"], how="left")
TT = TT.merge(A6.groupby(K)["level"].last().rename("last_level").reset_index(), on=K, how="left")
TT["level"] = TT.first_level.fillna(TT.next_level).fillna(TT.last_level).fillna(0).astype(int)
TT["game"] = TT.game_run.str.split("@").str[0]
w10 = np.zeros(len(TT), dtype=int); pos = np.zeros(len(TT), dtype=int); unch5 = np.zeros(len(TT), dtype=int); rev10 = np.zeros(len(TT), dtype=int)
tidx = {key: idx for key, idx in TT.groupby(K).indices.items()}
for key, g in A6.groupby(K):
    if key not in tidx:
        continue
    ii = tidx[key]; n = len(g)
    cs = np.concatenate([[0], np.cumsum(g.level_completed.values)])
    s = TT.first_action_num.values[ii].clip(1, max(n, 1)).astype(int)
    w10[ii] = ((cs[np.minimum(s + 9, n)] - cs[s - 1]) > 0).astype(int) if n else 0
    ai = g.action_index.values; al = g.level.values; un = 1 - g.board_changed.values; rv = g.revisit.values
    bylvl = {lv_: (ai[al == lv_], un[al == lv_], rv[al == lv_]) for lv_ in np.unique(al)}
    for j, st0, L0 in zip(ii, TT.first_action_num.values[ii].astype(int), TT.level.values[ii]):
        if L0 not in bylvl:
            continue
        idx_, u_, r_ = bylvl[L0]
        pos[j] = int(np.searchsorted(idx_, st0))
        unch5[j] = int(u_[(idx_ >= st0 - 5) & (idx_ <= st0 - 1)].sum())
        rev10[j] = int(r_[(idx_ >= st0 - 10) & (idx_ <= st0 - 1)].sum())
TT["lvl_within_10"] = w10; TT["pos_in_level"] = pos
TT["stuck"] = ((unch5 > 0) | (rev10 > 0)).astype(int)
TT["posbin"] = pd.cut(TT.pos_in_level, [-1, 0, 5, 15, 40, 10 ** 9], labels=["level start", "1-5", "6-15", "16-40", ">40"]).astype(str)
TT["read"] = ((TT.reads_code + TT.reads_rules) > 0).astype(int)
TT["cue"] = (TT.lexicon_cue > 0).astype(int)
rng6 = np.random.default_rng(6)


def strata_table(df, col, extra):
    g = df.groupby(K + ["level"] + extra + ["read"])[col].agg(["size", "sum"]).unstack("read", fill_value=0)
    g.columns = [f"{a}_{b}" for a, b in g.columns]
    g = g[(g.get("size_1", 0) > 0) & (g.get("size_0", 0) > 0)].reset_index()
    g["game"] = g.game_run.str.split("@").str[0]
    g["w"] = g.size_1 * g.size_0 / (g.size_1 + g.size_0); g["d"] = g.sum_1 / g.size_1 - g.sum_0 / g.size_0
    return g


def est(g, mult=None):
    w = g.w.values * (1 if mult is None else mult)
    return float((w * g.d.values).sum() / w.sum()) if w.sum() else float("nan")


def boot(g, n=2000):
    games = g.game.unique(); gi = pd.Categorical(g.game, categories=games).codes; v = []
    for _ in range(n):
        v.append(est(g, np.bincount(rng6.integers(0, len(games), len(games)), minlength=len(games))[gi]))
    v = [x for x in v if x == x]
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]


p6 = {"turns": int(len(TT)), "turns_with_read": int(TT.read.sum()), "turns_with_cue": int(TT.cue.sum()),
      "read_rate": {"by_position": {k: [int(v["size"]), float(v["mean"])] for k, v in TT.groupby("posbin").read.agg(["size", "mean"]).iterrows()},
                    "by_cue": {str(k): [int(v["size"]), float(v["mean"])] for k, v in TT.groupby("cue").read.agg(["size", "mean"]).iterrows()},
                    "by_stuck": {str(k): [int(v["size"]), float(v["mean"])] for k, v in TT.groupby("stuck").read.agg(["size", "mean"]).iterrows()}},
      "outcomes": {}}
s4 = json.loads((out / "stage4_exploratory.json").read_text())["M1"]
repro = []
for col in ("lvl_done", "lvl_within_10"):
    o = {}
    for label, sub, extra in (("as Stage 4 M1: same run, game and level", TT, []),
                              ("matched: also position in level and stuck status", TT, ["posbin", "stuck"]),
                              ("matched, turns without a cue (unprompted reads)", TT[TT.cue == 0], ["posbin", "stuck"]),
                              ("matched, turns with a cue (prompted reads)", TT[TT.cue == 1], ["posbin", "stuck"])):
        g = strata_table(sub, col, extra)
        o[label] = {"difference": est(g), "ci": boot(g), "strata": int(len(g)), "turns": int(len(sub)), "reads": int(sub.read.sum())}
    p6["outcomes"][col] = o
    repro.append(abs(o["as Stage 4 M1: same run, game and level"]["difference"] - s4["outcomes"][col]["stratified_difference"]) < 1e-9)
res["checks"]["p6_reproduces_stage4_m1"] = bool(all(repro) and p6["turns"] == s4["turns"] and p6["turns_with_read"] == s4["turns_with_read"])
res["P6"] = p6

json.dump(res, open(out / "stage5_posthoc.json", "w"), indent=1, default=float)

# ------------------------------------------------------------------ report
ck = res["checks"]
md = ["# Stage 5: post hoc analyses", "",
      "**Post hoc.** Added after the Stage 2–4 results were seen ([`../ANALYSIS-PLAN.md`](../ANALYSIS-PLAN.md) §8). These results suggest; they do not confirm, "
      "and no Stage 2–4 verdict changes because of them. Script: `analysis/stage5_posthoc.py`; all numbers: `stage5_posthoc.json`.", "",
      "The six runs are the paired level-trial runs: every level of the 25 public games played from its own start, 20 minutes each, 183 levels per run.", "",
      "| Label | Run | Role | Started (UTC) | Cleared |", "|---|---|---|---|---|"]
for k, v in RUNS.items():
    md.append(f"| {k} | `{v}` | {ROLE[k]} | {(start[k] or '')[:16]} | {p1['cleared'][k]} |")
md += ["", "## Checks", "",
       f"- **The controls installed no add-on:** {'yes' if ck['controls_install_nothing'] else 'NO'}. Each log's add-on lines are in the JSON (`setup.addon_log_lines`).",
       f"- **Notebook cells:** the three controls differ in {len(setup['notebooks']['three controls']['differing_cells'])} of "
       f"{setup['notebooks']['three controls']['cells'][0]} cells (each carries its own add-on cell, switched off); listed below.",
       f"- **The power model reproduces the real A/A disagreement:** {'yes' if ck['power_model_matches_aa'] else 'NO'} (P2).",
       f"- **The scoring formula reproduces the engine scores** of all whole-game runs: largest difference {ck['rhae_formula_reproduces_engine_scores_max_abs_diff']:.2g} points; "
       f"levels cleared in order: {'yes' if ck['whole_game_levels_cleared_in_order'] else 'NO'}. Each game's level count and human baselines come from the "
       f"level-trial starts ({ck['public_games_and_levels'][0]} games, {ck['public_games_and_levels'][1]} levels; consistent across trial runs: "
       f"{'yes' if ck['trial_starts_cover_every_level'] else 'NO'}; whole-game rows agree: {'yes' if ck['whole_game_baselines_match_trial_starts'] else 'NO'}).",
       f"- **P6 starts from Stage 4 M1:** {'yes' if ck['p6_reproduces_stage4_m1'] else 'NO'} (same turns, same estimates).",
       f"- **Trial clears match the replayed actions** (a clear has a clearing action, a failure has none): {'yes' if ck['trial_clears_match_replayed_actions'] else 'NO'}.", "",
       "| Cell | Type | " + " | ".join(CTRL) + " |", "|---|---|" + "---|" * len(CTRL)]
for d in setup["notebooks"]["three controls"]["differing_cells"]:
    md.append(f"| {d['cell']} | {d['type']} | " + " | ".join(f"`{esc(d['first_lines'][x][:70])}`" for x in CTRL) + " |")
md += ["", "## P1. The unchanged agent against itself (A/A)", "",
       "| Pair | Kind | Cleared | Only first | Only second | Exact McNemar p | Cohen's κ |", "|---|---|---|---|---|---|---|"]
for name, v in p1["pairs"].items():
    md.append(f"| {name} | {v['kind']} | {v['cleared'][0]} vs {v['cleared'][1]} | {v['only_first']} | {v['only_second']} | {v['exact_p']:.3f} | {v['kappa']:.2f} |")
md += ["", f"ICC(1) of the clear outcome across the three controls: {p1['icc1_controls']:.2f} (the share of outcome variation that belongs to the level). "
       f"Levels by how many of the six runs cleared them: {p1['levels_by_runs_clearing_of_6']}; by how many of the three controls: {p1['levels_by_controls_clearing_of_3']}.", "",
       "## P2. What the level-trial design can detect", "",
       f"Observed disagreeing levels in the three A/A pairs: {obs_aa}. The first, scratch model implied {p2['first_pass_model_expected_disagreeing_levels']:.1f} per pair and was replaced.", ""]
for label, mdl in p2["models"].items():
    sa = mdl["simulated_aa_disagreeing_levels"]
    md += [f"**Model {label}:** beta-binomial α = {mdl['alpha']:.3f}, β = {mdl['beta']:.3f}. Simulated A/A disagreement: mean {sa['mean']:.1f} "
           f"(5–95%: {sa['p5']:.0f}–{sa['p95']:.0f}); covers the observed: {'yes' if mdl['calibration_ok'] else 'NO'}. "
           f"Simulations per power cell: {mdl['simulations_per_power_cell']:,}.", "",
           "| Effect | Power |", "|---|---|"]
    md += [f"| {k} | {v:.2f} |" for k, v in mdl["power"].items()]
    md += ["", "| If the true gain is | Power | Significant results average | Ratio |", "|---|---|---|---|"]
    md += [f"| {k} | {v['power']:.2f} | {v['mean_significant_estimate'] * 100:.1f} pts | ×{v['ratio']:.1f} |" for k, v in mdl["overstatement"].items()]
    md.append("")
md += ["A run's levels get their clear chances from the fitted model; the add-on adds the same log-odds shift to every level, so levels "
       "no run can clear stay unclearable. Detection: exact McNemar p < 0.05 (pooled over rounds) in the direction of the effect.", "",
       "## P3. Each add-on against all three controls", "",
       "| Comparison | Add-on clear rate | Controls | Difference | Exact permutation p (two-sided) |", "|---|---|---|---|---|"]
for name, v in p3.items():
    md.append(f"| {name} | {pc(v['clear_rate_add_on'])} | {pc(v['clear_rate_controls'])} | {pts(v['difference'])} pts | {v['exact_permutation_p_two_sided']:.3f} |")
md += ["", "Run labels are permuted within each level; the null distribution is exact (convolution over levels). This assumes runs on different days are exchangeable, "
       "which the same-day pairing of Stage 2 does not need.", "",
       "## P4. Did probe-first change what it targets?", "",
       f"Governor counters at the end of each run: PF1 `{p4['governor_counters']['PF1']}`; PF2 `{p4['governor_counters']['PF2']}`; "
       f"C2 `{p4['governor_counters']['C2']}`; C3 `{p4['governor_counters']['C3']}`.", "",
       "No-action streaks (consecutive responses after which the action count did not advance, as in `lt_analysis.py`):", "",
       "| Run | Streaks | Median | 90th pct | Max | 5 or more | 10 or more | Tokens in streaks of 5+ |", "|---|---|---|---|---|---|---|---|"]
for k, v in p4["streaks"].items():
    md.append(f"| {k} | {v['streaks']:,} | {v['median']:.0f} | {v['p90']:.0f} | {v['max']} | {pc(v['share_5_or_more'])} | {pc(v['share_10_or_more'])} | {pc(v['token_share_in_streaks_5_or_more'])} |")
md += ["", "| Pair | Moves per trial, median | Mean difference | Median difference | Wilcoxon p | Levels both cleared | Tokens to clear, median ratio (p) | Actions to clear, median ratio (p) |",
       "|---|---|---|---|---|---|---|---|"]
for name, v in p4["moves_per_trial"].items():
    e = p4["effort_on_levels_both_cleared"][name]
    md.append(f"| {name} | {v['median'][0]:.0f} vs {v['median'][1]:.0f} | {v['mean_difference']:+.1f} | {v['median_difference']:+.0f} | {v['wilcoxon_p']:.3f} | {e['levels']} | "
              f"{e['tokens_to_clear']['median_ratio']:.2f} ({e['tokens_to_clear']['wilcoxon_p']:.3f}) | {e['actions_to_clear']['median_ratio']:.2f} ({e['actions_to_clear']['wilcoxon_p']:.3f}) |")
md += ["", "| Run | Median tokens per trial | Total tokens | Cleared | Tokens per cleared level |", "|---|---|---|---|---|"]
for k in RUNS:
    v = p4["budget"][k]
    md.append(f"| {k} | {v['median_tokens_per_trial']:,.0f} | {v['total_tokens']:,} | {v['cleared']} | {v['tokens_per_cleared_level']:,.0f} |")
md += [""] + [f"- {x} / {y}: total tokens ×{p4['budget'][f'{x} / {y}']['total_tokens_ratio']:.2f}, levels cleared ×{p4['budget'][f'{x} / {y}']['cleared_ratio']:.2f}." for x, y in PAIRS_AB]
md += ["", "## P5. What limits the score?", "", "### Score anatomy of whole-game runs (grouped by the root base in `run.json`)", "",
       "| Base | Game-runs | Mean score | Ceiling from levels cleared | Lost to uncleared levels | Lost to inefficiency | Inefficiency share of the loss | Cleared levels over 5× human | Mean score with the 5× rule | Next level raises the ceiling by | Next level, largest possible gain |",
       "|---|---|---|---|---|---|---|---|---|---|---|"]
for gname, v in p5["score_anatomy"].items():
    md.append(f"| {gname} | {v['game_runs']} | {v['mean_score']:.2f} | {v['mean_ceiling']:.2f} | {v['mean_lost_uncleared']:.2f} | {v['mean_lost_inefficiency']:.2f} | "
              f"{pc(v['inefficiency_share_of_lost_score'])} | {v['cleared_levels_over_5x_human']} | {v['mean_score_with_5x_rule']:.2f} | {v['mean_next_level_ceiling_raise']:.1f} | {v['mean_next_level_max_gain']:.1f} |")
md += ["", "Points out of 100 per game-run. A game's score is capped at the level-weighted share of levels cleared (the ceiling); per level the score is "
       "min((human/ours)², 1.15). The 5× rule is the action budget of the official evaluation (\"the agent is terminated after 5n actions\", ARC-AGI-3 report §4.3): "
       "a cleared level that took more than 5× the human count scores 0 and ends that game. The next-level columns are what clearing one more level could add to "
       "that game's score. Runs in each group are listed in the JSON.", "",
       "### Difficulty: what predicts a clear for the unchanged agent (3 controls)", "",
       "| Human actions for the level | Levels | Clear rate |", "|---|---|---|"]
md += [f"| {k} | {v[0]} | {pc(v[1])} |" for k, v in p5["difficulty"]["clear_rate_by_human_actions"].items()]
md += ["", "| Level depth | Levels | Clear rate |", "|---|---|---|"]
md += [f"| {k} | {v[0]} | {pc(v[1])} |" for k, v in p5["difficulty"]["clear_rate_by_depth"].items()]
lg = p5["difficulty"]["logistic_clustered_by_game"]
md += ["", f"Logistic regression on {p5['difficulty']['trials_in_model']} trials, standard errors clustered by game ({p5['difficulty']['games']} games): "
       f"log human actions {lg['log_h']['coef']:.2f} (95% CI {lg['log_h']['ci'][0]:.2f} to {lg['log_h']['ci'][1]:.2f}, p = {lg['log_h']['p']:.1e}); "
       f"depth {lg['depth']['coef']:.2f} per level ({lg['depth']['ci'][0]:.2f} to {lg['depth']['ci'][1]:.2f}, p = {lg['depth']['p']:.1e}). "
       f"Per-game clear rate: {p5['difficulty']['per_game_clear_rate']}.", "",
       "### When in the trial clears happen (share of the trial's generated tokens spent at the clear)", "",
       "| Run | Clears | Median point of the trial | Clears in the last quarter | Cleared by 10k tokens | by 20k | by 40k | by 80k |", "|---|---|---|---|---|---|---|---|"]
for k, v in p5["budget"].items():
    c_ = v["cumulative_share_of_183_cleared_by_tokens"]
    md.append(f"| {k} | {v['clears']} | {v['median_budget_fraction_at_clear']:.2f} | {pc(v['share_of_clears_in_last_quarter'])} | {pc(c_['10000'])} | {pc(c_['20000'])} | {pc(c_['40000'])} | {pc(c_['80000'])} |")
md += ["", "| Pair | Kind | Cleared by one run only: n, median point | Cleared by both: n, median point | Mann–Whitney p |", "|---|---|---|---|---|"]
for name, v in p5["timing_one_vs_both"].items():
    md.append(f"| {name} | {v['kind']} | {v['one_run_only']['n']}, {v['one_run_only']['median']:.2f} | {v['both']['n']}, {v['both']['median']:.2f} | {v['mann_whitney_p']:.1e} |")
ft = p5["failed_trials"]
md += ["", "### Failed trials: moves made against the human count and against what clears needed", "",
       f"Cleared trials needed a median {ft['cleared_moves_over_human']['median']:.2f}× the human count (10th percentile {ft['cleared_moves_over_human']['p10']:.2f}×). "
       f"Failed trials made a median {ft['failed_moves_over_human_median']:.2f}× the human count; {pc(ft['failed_share_below_human_count'])} made fewer moves than the human count, "
       f"but only {pc(ft['failed_share_below_p10_of_clears'])} stopped below the 10th percentile of what clears needed. "
       f"Median moves: failed trials {ft['failed_median_moves']:.0f}; cleared trials, to the clear {ft['cleared_median_moves_to_clear']:.0f}.", "",
       "| Human actions for the level | Failed trials | Their median moves (human median) | Moves / human, median | Below the human count | Clears | 10th pct of clears | Failed below that |",
       "|---|---|---|---|---|---|---|---|"]
for k, v in ft["by_human_actions"].items():
    md.append(f"| {k} | {v['failed']} | {v['failed_median_moves']:.0f} ({v['human_median']:.0f}) | {v['failed_median_moves_over_human']:.2f} | {pc(v['failed_share_below_human_count'])} | "
              f"{v['clears']} | {v['clears_p10_moves_over_human']:.2f} | {pc(v['failed_share_below_that'])} |")
fr = p5["frontier"]
md += ["", f"New board states per 100 moves on failed trials (median): {', '.join(f'{k} {v:.1f}' for k, v in p5['failed_trial_new_boards_per_100_moves'].items())}.", "",
       f"Frontier: {fr['levels_cleared_by_any_run']} levels cleared by at least one of the six runs, {fr['levels_cleared_by_every_run']} by all six, {fr['levels_cleared_by_any_control']} by at least one control. "
       f"Levels no control cleared: PF1 {fr['new_beyond_the_3_controls']['PF1']}, PF2 {fr['new_beyond_the_3_controls']['PF2']} (either: {fr['new_beyond_the_3_controls_PF1_or_PF2']}), "
       f"LEX {fr['new_beyond_the_3_controls']['LEX']}. For reference, each control clears {', '.join(f'{c} {n_}' for c, n_ in fr['reference_one_control_beyond_the_other_two'].items())} levels the other two controls never cleared.", "",
       "## P6. Reading the lexicon, matched on situation", "",
       f"Turns in lexicon-on runs: {p6['turns']:,} (as Stage 4 M1); with a read of `.code` or `.rules`: {p6['turns_with_read']:,}; with a lexicon cue in the prompt: {p6['turns_with_cue']:,}.", "",
       "| Position in the level (actions already taken) | Turns | Read rate |", "|---|---|---|"]
md += [f"| {k} | {v[0]:,} | {pc(v[1])} |" for k, v in p6["read_rate"]["by_position"].items()]
md += ["", f"Read rate with a cue {pc(p6['read_rate']['by_cue']['1'][1])}, without {pc(p6['read_rate']['by_cue']['0'][1])}; "
       f"when stuck {pc(p6['read_rate']['by_stuck']['1'][1])}, otherwise {pc(p6['read_rate']['by_stuck']['0'][1])} "
       "(stuck: an unchanged-board action in the last 5 actions, or a revisit in the last 10, on that level).", "",
       "| Outcome | Comparison | Difference, read minus no read (95% CI) | Strata | Turns | Reads |", "|---|---|---|---|---|---|"]
onames = {"lvl_done": "completes a level", "lvl_within_10": "a level completes within 10 actions of the turn's start"}
for col, o in p6["outcomes"].items():
    for label, v in o.items():
        md.append(f"| {onames[col]} | {label} | {pts(v['difference'])} pts ({pts(v['ci'][0])} to {pts(v['ci'][1])}) | {v['strata']:,} | {v['turns']:,} | {v['reads']:,} |")
md += ["", "Stratified differences weight each stratum by n₁n₀/(n₁+n₀); intervals are 2,000 bootstrap resamples of games (seed 6)."]
(out / "stage5_posthoc.md").write_text("\n".join(md) + "\n")
print("\n".join(md[:40]))
print("checks:", res["checks"])
