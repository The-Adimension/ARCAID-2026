"""Per-level attempts: generated tokens and actions spent on each level of a run.

A level attempt runs from the first token after the previous level's completing action
to the action that completes the level. The first level the run did not complete is an
unfinished (right-censored) attempt that ends at the run's last generated token.
"""
from __future__ import annotations

from rhae import cumulative_tokens, run_tokens


def attempts(r: dict) -> list[dict]:
    cum = cumulative_tokens(r)
    total = run_tokens(r)
    apl = r["actions_per_level"]
    base = r["base_actions_per_level"]
    lc = r["levels_completed"]
    out = []
    start_idx, start_tok = 0, 0
    for k in range(len(apl)):
        if k < lc:
            end_idx = start_idx + apl[k]
            end_tok = cum[end_idx - 1]
            out.append(dict(level=k + 1, done=True, tokens=end_tok - start_tok,
                            actions=apl[k], base=base[k]))
            start_idx, start_tok = end_idx, end_tok
        else:
            out.append(dict(level=k + 1, done=False, tokens=total - start_tok,
                            actions=apl[k], base=base[k]))
            break
    return out


def km_completed_by(atts: list[dict], grid: list[int]) -> dict[int, float]:
    """Kaplan-Meier estimate of P(level completed within t tokens), unfinished = censored."""
    events = sorted((a["tokens"], a["done"]) for a in atts)
    at_risk = len(events)
    surv = 1.0
    out: dict[int, float] = {}
    gi = 0
    for tok, done in events:
        while gi < len(grid) and grid[gi] < tok:
            out[grid[gi]] = 1 - surv
            gi += 1
        if done:
            surv *= 1 - 1 / at_risk
        at_risk -= 1
    while gi < len(grid):
        out[grid[gi]] = 1 - surv
        gi += 1
    return out
