"""Stage 4 of ANALYSIS-PLAN.md: exploratory mechanism analyses M1-M6. Labelled exploratory; nothing here is confirmatory.

  python3.12 -I stage4_exploratory.py DATA_DIR REPO_ROOT OUT_DIR

Joins: events link each replayed action (actions) to the model turn that executed it (turns); calls carry token usage.
Outcomes (board change, level completion, game over, board state) come from the engine replay.
Intervals are 95% bootstrap intervals over games (2,000 resamples, seed 0).
"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

data, repo, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
A = pd.read_csv(data / "actions.csv.gz", dtype={"board_hash": str})
E = pd.read_csv(data / "events.csv.gz")
T = pd.read_csv(data / "turns.csv.gz")
C = pd.read_csv(data / "calls.csv.gz")
L = pd.read_csv(data / "levels.csv.gz")
K = ["run_id", "game_run", "pass"]
rng = np.random.default_rng(0)


def generation(run_id, trial=None):
    if run_id.startswith("arcaid3-lt-"):
        return "level trials (Oct)"
    if run_id.startswith("arcaid3"):
        return "Franzen-based whole games (Oct)"
    return "Duck/TAAF whole games (Sept)"


def boot(df, stat, by="game", n=2000):
    games = df[by].unique(); groups = {g: d for g, d in df.groupby(by)}
    vals = []
    for _ in range(n):
        pick = rng.choice(games, len(games))
        vals.append(stat(pd.concat([groups[g] for g in pick])))
    vals = [v for v in vals if v == v]
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))) if vals else (float("nan"),) * 2


# ---- per-action features: revisits of a board state already seen on the same level
A = A.sort_values(K + ["action_index"])
A["revisit"] = A.duplicated(subset=K + ["level", "board_hash"]).astype(int)
A["game"] = A.game_run.str.split("@").str[0]

# ---- turns with their actions
EA = E.merge(A, left_on=K + ["action_num"], right_on=K + ["action_index"], how="left")
per_turn = EA.groupby(K + ["analysis_step"]).agg(n_actions=("action_index", "size"), changed=("board_changed", "sum"),
                                                  lvl_done=("level_completed", "max"), over=("game_over", "max"),
                                                  first_level=("level", "first")).reset_index()
TT = T.merge(per_turn, on=K + ["analysis_step"], how="left").fillna({"n_actions": 0, "changed": 0, "lvl_done": 0, "over": 0})
lvl_lookup = A.set_index(K + ["action_index"])["level"]
def turn_level(r):
    if r.first_level == r.first_level:
        return r.first_level
    key = (r.run_id, r.game_run, r["pass"], r.first_action_num)
    if key in lvl_lookup.index:
        return lvl_lookup.loc[key]
    sub = A[(A.run_id == r.run_id) & (A.game_run == r.game_run) & (A["pass"] == r["pass"])]
    return sub.level.iloc[-1] if len(sub) else 0
TT["level"] = [turn_level(r) for _, r in TT.iterrows()]
TT["game"] = TT.game_run.str.split("@").str[0]
TT["generation"] = TT.run_id.map(generation)
# completion within the next 10 actions from the turn's start
lc = A.set_index(K + ["action_index"])["level_completed"]
idx = {k: g.set_index("action_index")["level_completed"] for k, g in A.groupby(K)}
TT["lvl_within_10"] = [int(idx.get((r.run_id, r.game_run, r["pass"]), pd.Series(dtype=int)).loc[r.first_action_num:r.first_action_num + 9].max() > 0)
                       if (r.run_id, r.game_run, r["pass"]) in idx else 0 for _, r in TT.iterrows()]

res = {}

# ---- M1 reading vs acting
LEX = TT[TT.run_id.str.contains("lexicon-view|rep-v|lb-lex|lt-lex|dprime")].copy()
LEX["read"] = ((LEX.reads_code + LEX.reads_rules) > 0).astype(int)
LEX["acts"] = (LEX.n_actions > 0).astype(int)
LEX["share_changed"] = np.where(LEX.n_actions > 0, LEX.changed / LEX.n_actions.clip(lower=1), np.nan)
outcomes = ["acts", "share_changed", "lvl_done", "lvl_within_10", "over"]
def stratified_diff(df, col):
    s = df.dropna(subset=[col]).groupby(K + ["level"])
    num = den = 0.0
    for _, g in s:
        r, nr = g[g.read == 1][col], g[g.read == 0][col]
        if len(r) and len(nr):
            w = len(r) * len(nr) / (len(r) + len(nr)); num += w * (r.mean() - nr.mean()); den += w
    return num / den if den else float("nan")
m1 = {"turns": int(len(LEX)), "turns_with_read": int(LEX.read.sum()), "outcomes": {}}
for col in outcomes:
    d = stratified_diff(LEX, col)
    m1["outcomes"][col] = {"rate_read": float(LEX[LEX.read == 1][col].mean()), "rate_no_read": float(LEX[LEX.read == 0][col].mean()),
                           "stratified_difference": d, "ci": boot(LEX, lambda x: stratified_diff(x, col))}
OFF = TT[TT.run_id.isin(["arcaid3-lt-off-r3@v1", "arcaid3-lb-off-r1@v1", "arcaid3-lb-off-r2@v1"])].copy()
OFF["acts"] = (OFF.n_actions > 0).astype(int)
OFF["share_changed"] = np.where(OFF.n_actions > 0, OFF.changed / OFF.n_actions.clip(lower=1), np.nan)
m1["off_arm_reference"] = {col: float(OFF[col].mean()) for col in outcomes}
res["M1"] = m1

# ---- M2 spending, in the paired level-trial designs
arms = {"A3 lexicon on (r3)": "arcaid3-lt-lex-r3@v1", "A3 lexicon off (r3)": "arcaid3-lt-off-r3@v1",
        "probe-first on (r1)": "arcaid3-lt-pf-on-r1@v1", "probe-first off (r1)": "arcaid3-lt-pf-off-r1@v1",
        "probe-first on (r2)": "arcaid3-lt-pf-on-r2@v1", "probe-first off (r2)": "arcaid3-lt-pf-off-r2@v1"}
m2 = {}
for name, run in arms.items():
    c = C[C.run_id == run].copy()
    na = na_tok = 0
    for _, g in c.groupby(K, sort=False):
        prev = 0
        for a_, ct in zip(g.action_num.fillna(0), g.completion_tokens.fillna(0)):
            if a_ <= prev:
                na += 1; na_tok += ct
            prev = a_
    lv = L[L.run_id == run]
    tok_per_trial = c.groupby("game_run").completion_tokens.sum()
    before_first = c[c.action_num.fillna(0) <= 1].groupby("game_run").completion_tokens.sum().reindex(lv.game_run).fillna(0)
    t = TT[TT.run_id == run]
    m2[name] = {"trials": int(len(lv)), "cleared": int(lv.cleared.sum()), "responses": int(len(c)),
                "completion_tokens": int(c.completion_tokens.sum()), "reasoning_tokens": int(c.reasoning_tokens.fillna(0).sum()),
                "completion_tokens_per_cleared_level": float(c.completion_tokens.sum() / max(1, lv.cleared.sum())),
                "median_tokens_per_trial": float(tok_per_trial.median()),
                "no_action_response_share": na / max(1, len(c)), "no_action_token_share": na_tok / max(1, c.completion_tokens.sum()),
                "median_tokens_before_first_action": float(before_first.median()),
                "turns_without_action_share": float((t.n_actions == 0).mean()),
                "truncated_responses": int((c.finish_reason == "length").sum())}
res["M2"] = m2

# ---- M3 stuck levels: levels played but not cleared, against cleared levels
lvl_feats = A.groupby(K + ["level"]).agg(n=("action_index", "size"), revisit=("revisit", "mean"), unchanged=("board_changed", lambda s: 1 - s.mean()),
                                         over=("game_over", "sum"), tok=("generated_tokens", "sum")).reset_index()
LL = L.merge(lvl_feats, on=K + ["level"], how="left")
LL["generation"] = LL.run_id.map(generation)
LL["tok_per_action"] = LL.tok / LL.n.clip(lower=1)
LL["over_per_100"] = 100 * LL.over / LL.n.clip(lower=1)
m3 = {}
for gen, g in LL.groupby("generation"):
    m3[gen] = {}
    for cl, h in g.groupby("cleared"):
        m3[gen]["cleared" if cl else "not cleared"] = {"levels": int(len(h)), "median_actions": float(h.n.median()),
            "median_revisit_share": float(h.revisit.median()), "median_unchanged_share": float(h.unchanged.median()),
            "game_overs_per_100_actions": float(100 * h.over.sum() / max(1, h.n.sum())),
            "median_tokens_per_action": float(h.tok_per_action.median())}
res["M3"] = m3

# ---- M4 efficiency on cleared levels
m4 = {}
cl = LL[LL.cleared == 1].copy()
for gen, g in cl.groupby("generation"):
    r = g.actions_over_human.astype(float)
    m4[gen] = {"cleared_levels": int(len(g)), "median_actions_over_human": float(r.median()),
               "iqr": [float(r.quantile(0.25)), float(r.quantile(0.75))], "share_at_or_below_human": float((r <= 1).mean()),
               "ci_median": boot(g, lambda x: x.actions_over_human.astype(float).median())}
for name, run in arms.items():
    g = cl[cl.run_id == run]; r = g.actions_over_human.astype(float)
    m4[name] = {"cleared_levels": int(len(g)), "median_actions_over_human": float(r.median()),
                "iqr": [float(r.quantile(0.25)), float(r.quantile(0.75))], "share_at_or_below_human": float((r <= 1).mean())}
res["M4"] = m4

# ---- M5 generalisation across harness generations
m5 = {}
for gen, g in TT.groupby("generation"):
    a = A[A.run_id.map(generation) == gen]
    m5[gen] = {"turns": int(len(g)), "actions": int(len(a)), "turns_without_action_share": float((g.n_actions == 0).mean()),
               "median_reasoning_chars_per_turn": float(g.reasoning_chars.median()),
               "unchanged_board_share": float(1 - a.board_changed.mean()), "revisit_share": float(a.revisit.mean()),
               "game_overs_per_100_actions": float(100 * a.game_over.mean()),
               "mean_generated_tokens_per_action": float(a.generated_tokens.mean())}
res["M5"] = m5

# ---- M6 ARC-AGI-2 description
S2 = pd.read_csv(repo / "Submissions/ARC-AGI-2/submissions.csv")
m6 = {"versions": [], "submissions": S2[["submitted_utc", "public_score", "status", "after_deadline"]].fillna("").to_dict("records")}
for rj in sorted((repo / "Submissions/ARC-AGI-2").glob("*/v*/run.json")):
    r = json.loads(rj.read_text())
    m6["versions"].append({"version": r["version"], "start": r["run"]["start"], "minutes": round((r["run"]["duration_s"] or 0) / 60, 1),
                           "exception": r["run"]["exception"], "folder": rj.parent.name})
res["M6"] = m6

json.dump(res, open(out / "stage4_exploratory.json", "w"), indent=1, default=float)

pc = lambda x: f"{100 * x:.1f}%"
md = ["# Stage 4: exploratory mechanism analyses", "",
      "**Exploratory.** Specified in [`../ANALYSIS-PLAN.md`](../ANALYSIS-PLAN.md) §4. Nothing here is confirmed; patterns are reported "
      "with counts and 95% bootstrap intervals over games (2,000 resamples, seed 0). Script: `analysis/stage4_exploratory.py`; all numbers: "
      "`stage4_exploratory.json`.", "",
      "## M1. Reading vs acting (lexicon-on runs)", "",
      f"Turns in lexicon-on runs: {m1['turns']:,}; turns whose tool code read `current_frame.code` or `.rules`: {m1['turns_with_read']:,}. "
      "The stratified difference compares turns with and without a read within the same run, game and level.", "",
      "| Outcome of the turn | With a read | Without | Stratified difference (95% CI) | Lexicon-off runs, for reference |", "|---|---|---|---|---|"]
names = {"acts": "executes at least one action", "share_changed": "share of its actions that change the board",
         "lvl_done": "completes a level", "lvl_within_10": "a level completes within 10 actions of the turn's start", "over": "ends in a game over"}
for col in outcomes:
    o = m1["outcomes"][col]
    md.append(f"| {names[col]} | {pc(o['rate_read'])} | {pc(o['rate_no_read'])} | {o['stratified_difference']*100:+.1f} pts "
              f"({o['ci'][0]*100:+.1f} to {o['ci'][1]*100:+.1f}) | {pc(m1['off_arm_reference'][col])} |")
md += ["", "## M2. Spending in the paired level trials", "",
       "| Arm | Trials | Cleared | Completion tokens per cleared level | Median tokens per trial | No-action response share | No-action token share | Median tokens before the first action | Turns without an action | Truncated responses |",
       "|---|---|---|---|---|---|---|---|---|---|"]
for name, v in m2.items():
    md.append(f"| {name} | {v['trials']} | {v['cleared']} | {v['completion_tokens_per_cleared_level']:,.0f} | {v['median_tokens_per_trial']:,.0f} | "
              f"{pc(v['no_action_response_share'])} | {pc(v['no_action_token_share'])} | {v['median_tokens_before_first_action']:,.0f} | "
              f"{pc(v['turns_without_action_share'])} | {v['truncated_responses']} |")
md += ["", "No-action shares follow the definition in `Ablations/ARC-AGI-3/2026-10-24__level-trials-probe-first/analysis/lt_analysis.py` "
       "(a response after which the action count did not advance).", "",
       "## M3. Stuck levels against cleared levels", "",
       "| Generation | Levels | Cleared? | Median actions | Median share of actions revisiting a seen board | Median unchanged-board share | Game-overs per 100 actions | Median generated tokens per action |",
       "|---|---|---|---|---|---|---|---|"]
for gen, d in m3.items():
    for k_, v in d.items():
        md.append(f"| {gen} | {v['levels']} | {k_} | {v['median_actions']:.0f} | {pc(v['median_revisit_share'])} | {pc(v['median_unchanged_share'])} | "
                  f"{v['game_overs_per_100_actions']:.2f} | {v['median_tokens_per_action']:,.0f} |")
md += ["", "## M4. Efficiency on cleared levels (our actions / human baseline)", "",
       "| Group | Cleared levels | Median (95% CI) | IQR | At or below the human count |", "|---|---|---|---|---|"]
for k_, v in m4.items():
    ci = f" ({v['ci_median'][0]:.2f}–{v['ci_median'][1]:.2f})" if "ci_median" in v else ""
    md.append(f"| {k_} | {v['cleared_levels']} | {v['median_actions_over_human']:.2f}{ci} | {v['iqr'][0]:.2f}–{v['iqr'][1]:.2f} | {pc(v['share_at_or_below_human'])} |")
md += ["", "## M5. Across harness generations", "",
       "| Generation | Turns | Actions | Turns without an action | Median reasoning characters per turn | Unchanged-board actions | Revisits of a seen board | Game-overs per 100 actions | Mean generated tokens per action |",
       "|---|---|---|---|---|---|---|---|---|"]
for gen, v in m5.items():
    md.append(f"| {gen} | {v['turns']:,} | {v['actions']:,} | {pc(v['turns_without_action_share'])} | {v['median_reasoning_chars_per_turn']:,.0f} | "
              f"{pc(v['unchanged_board_share'])} | {pc(v['revisit_share'])} | {v['game_overs_per_100_actions']:.2f} | {v['mean_generated_tokens_per_action']:,.0f} |")
md += ["", "The generations differ in setup (time per game, number of games, harness), which is stated rather than adjusted away.", "",
       "## M6. ARC-AGI-2 transfer (description only)", "",
       "| Version | Run started | Minutes | Exception |", "|---|---|---|---|"]
for v in m6["versions"]:
    md.append(f"| v{v['version']} | {v['start'] or '—'} | {v['minutes']} | {v['exception'] or 'none'} |")
md += ["", "| Submitted (UTC) | Public score | Status | Late, not counted |", "|---|---|---|---|"]
for s in m6["submissions"]:
    md.append(f"| {s['submitted_utc'][:16]} | {s['public_score']} | {s['status']} | {s['after_deadline']} |")
md += ["", "The ARC-AGI-2 save runs are install checks with a 3-task smoke test; no agent transcripts were saved, so no behavioural analysis is possible."]
(out / "stage4_exploratory.md").write_text("\n".join(md) + "\n")
print("\n".join(md[:24]))
