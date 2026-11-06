"""RHAE scorer and run helpers for TAAF/Duck `benchmark.json` files.

The scorer is the form the official toolkit ships (`scorecard.py`): per level
min((human / agent)^2, 1.15), level-index weights, game score capped at the weighted
share of completed levels. `check_scorer` confirms it reproduces every stored
`final_score` in a file before any number is derived from that file.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

LEVEL_CAP = 1.15


def load_runs(path: str | Path) -> list[dict]:
    return json.loads(Path(path).read_text())["game_runs"]


def level_score(base: float, actions: float, cap: float = LEVEL_CAP) -> float:
    return min((base / actions) ** 2, cap) if actions > 0 else 0.0


def game_score(base_per_level: list, actions_per_level: list, levels_completed: int,
               cap: float = LEVEL_CAP) -> float:
    n = len(base_per_level)
    weights = range(1, n + 1)
    total = sum(weights)
    num = sum((i + 1) * level_score(base_per_level[i], actions_per_level[i], cap)
              for i in range(levels_completed))
    share = sum(range(1, levels_completed + 1)) / total
    return 100 * min(num / total, share)


def check_scorer(runs: list[dict]) -> int:
    """Number of runs whose stored final_score the scorer does NOT reproduce (must be 0)."""
    return sum(
        abs(game_score(r["base_actions_per_level"], r["actions_per_level"], r["levels_completed"])
            - r["final_score"]) > 1e-6
        for r in runs)


def run_tokens(r: dict) -> int:
    """Generated tokens of a run: the solver's own total (includes tokens after the last action)."""
    m = re.search(r"tokens=(\d+)", r.get("solver_note") or "")
    return int(m.group(1)) if m else sum(h["generated_tokens"] for h in r["history"])


def cumulative_tokens(r: dict) -> list[int]:
    out, t = [], 0
    for h in r["history"]:
        t += h["generated_tokens"]
        out.append(t)
    return out


def pass_index(r: dict) -> int:
    """Pass number from the per-run analysis file name (`..._p<k>.html`)."""
    return int(re.search(r"_p(\d+)\.html", r["solver_analysis_html"]).group(1))


def truncated(r: dict, frac: float) -> tuple[int, float]:
    """(levels, score) had the run stopped after `frac` of its generated tokens.

    Level k counts only if the action that completed it was issued with cumulative
    generated tokens <= frac * total.
    """
    budget = frac * run_tokens(r)
    cum = cumulative_tokens(r)
    done, end = 0, 0
    for k in range(r["levels_completed"]):
        end += r["actions_per_level"][k]
        if cum[end - 1] <= budget:
            done = k + 1
        else:
            break
    return done, game_score(r["base_actions_per_level"], r["actions_per_level"], done)
