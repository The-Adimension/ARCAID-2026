"""Leave-one-pass-out estimates of 'restart a stuck level with a fresh context' policies.

Each pass of a multi-pass run is an independent play of the same game. For a level attempt
that used more than R tokens, the policy cuts it at R and starts a fresh attempt. The fresh
attempt's outcome is drawn from the OTHER passes' attempts on the same (game, level):
P(success within X tokens) = #{other attempts completed within X} / #{other attempts}.

Charged and not charged:
  * actions already spent before the cut stay on the level (pro-rated by tokens), plus the
    median actions of the other passes' successful attempts;
  * a slow attempt that would have completed after R is cut and loses its completion unless
    the fresh attempt succeeds;
  * `fresh_budget=None`: the fresh attempt only gets what the cut attempt had left (T - R);
  * `fresh_budget=F`: it gets F tokens; the net extra tokens F - (T - R) are charged at the
    measured marginal value of tokens on budget-limited runs (`marginal_points_per_token`);
  * `with_continuation=True`: a rescued level is also credited with the mean later-level score
    of the other passes that solved it, and their later-level tokens are charged at the same rate.
All deltas are in mean-score points over all runs (the unit of the run's mean score).
These are model estimates from one multi-pass run, not measurements of the policy.
"""
from __future__ import annotations

import collections
import statistics as st

from attempts import attempts
from rhae import level_score, run_tokens, truncated


def marginal_points_per_token(runs: list[dict]) -> float:
    """Mean-score points lost per token removed from the last 10% of budget-limited runs."""
    gave_up = [r for r in runs if r["state"] != "won"]
    full = st.mean(r["final_score"] for r in runs)
    cut = st.mean([r["final_score"] for r in runs if r["state"] == "won"]
                  + [truncated(r, 0.9)[1] for r in gave_up])
    return (full - cut) / (0.1 * sum(run_tokens(r) for r in gave_up))


def restart_estimate(runs: list[dict], R: int, fresh_budget: int | None = None,
                     with_continuation: bool = False) -> dict:
    cpt = marginal_points_per_token(runs)
    att = {i: attempts(r) for i, r in enumerate(runs)}
    by = collections.defaultdict(list)
    for i, r in enumerate(runs):
        for a in att[i]:
            by[(r["game_id"], a["level"])].append((i, a))

    def weight(r):
        n = len(r["base_actions_per_level"])
        return n * (n + 1) / 2

    def later(i, k):
        r = runs[i]
        W = weight(r)
        pts = sum(level_score(a["base"], a["actions"]) * a["level"] / W * 100
                  for a in att[i] if a["done"] and a["level"] > k)
        tok = sum(a["tokens"] for a in att[i] if a["level"] > k)
        return pts, tok

    gain = extra_tokens = 0.0
    fired = cut_successes = 0
    rescued = 0.0
    for i, r in enumerate(runs):
        W = weight(r)
        for a in att[i]:
            if a["tokens"] <= R:
                continue
            others = [(j, x) for j, x in by[(r["game_id"], a["level"])] if j != i]
            if not others:
                continue
            fired += 1
            budget = fresh_budget if fresh_budget is not None else a["tokens"] - R
            p = sum(1 for _, x in others if x["done"] and x["tokens"] <= budget) / len(others)
            succ = [(j, x) for j, x in others if x["done"]]
            spent = a["actions"] * R / a["tokens"]
            new = (level_score(a["base"], spent + st.median(x["actions"] for _, x in succ))
                   * a["level"] / W * 100) if succ else 0.0
            old = level_score(a["base"], a["actions"]) * a["level"] / W * 100 if a["done"] else 0.0
            cont = cont_tok = old_cont = 0.0
            if with_continuation and succ:
                cont = st.mean(later(j, a["level"])[0] for j, _ in succ)
                cont_tok = st.mean(later(j, a["level"])[1] for j, _ in succ)
                old_cont = later(i, a["level"])[0] if a["done"] else 0.0
            gain += (p * (new + cont) - (old + old_cont)) / len(runs)
            if fresh_budget is not None:
                extra_tokens += fresh_budget - (a["tokens"] - R) + p * cont_tok
            cut_successes += a["done"]
            rescued += 0.0 if a["done"] else p
    cost = extra_tokens * cpt
    return dict(R=R, fresh_budget=fresh_budget, continuation=with_continuation, fired=fired,
                slow_successes_cut=cut_successes, expected_rescues=rescued,
                level_gain=gain, token_cost=cost, net=gain - cost)
