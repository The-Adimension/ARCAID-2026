"""Leaderboard structure vs a 'best of k identical-code draws' model, and what two final
selections are worth. This is a model with the assumptions printed below, not a measurement.

Usage:
    python3 lb_model.py data/leaderboard/publicleaderboard-2026-10-10T17-12-56.csv
"""
from __future__ import annotations

import csv
import math
import sys

# Single-draw distribution of unchanged Franzen M2 copies on the public LB:
# Son Pham, discussion 745062 (first-day single submissions of copies).
MU, SD = 25.77, 3.93


def phi(z: float) -> float:
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def p_best_at_least(x: float, k: int, mu: float = MU, sd: float = SD) -> float:
    return 1 - phi((x - mu) / sd) ** k


def main(path: str) -> None:
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    for r in rows:
        r["score"] = float(r["Score"])
    print(f"teams on board: {len(rows)}")
    post = [r for r in rows if r["LastSubmissionDate"] >= "2026-10-01" and r["score"] >= 20]
    print(f"teams with a submission on/after 2026-10-01 and best >= 20: {len(post)}")
    for lo, hi in ((20, 25), (25, 28), (28, 30), (30, 33), (33, 36), (36, 40), (40, 101)):
        print(f"  [{lo},{hi}): {sum(lo <= r['score'] < hi for r in post)}")
    obs = {x: sum(r["score"] >= x for r in post) for x in (30, 33, 36)}
    print(f"observed among them: >=30 {obs[30]}, >=33 {obs[33]}, >=36 {obs[36]}")
    print(f"model: every such team = best of k draws ~ Normal({MU}, {SD})")
    for k in (1, 2, 3, 4):
        e = {x: p_best_at_least(x, k) * len(post) for x in (30, 33, 36)}
        print(f"  k={k}: expected >=30 {e[30]:.0f}, >=33 {e[33]:.0f}, >=36 {e[36]:.1f}")

    print(f"\nexpected private score of a copy: one selected draw = {MU:.2f}; "
          f"best of two independent selected draws = {MU + SD / math.sqrt(math.pi):.2f}")
    # Medal-line scenario: assumes ~30 teams with real gains sit above a copy mass of len(post)-30
    # teams whose private score is the best of two independent draws.
    n_teams = len(rows)
    real = 30
    mass = len(post) - real
    for name, rank in (("bronze (top 10%)", int(0.10 * n_teams)), ("silver (top 5%)", int(0.05 * n_teams))):
        q = (rank - real) / mass                   # share of the copy mass that must be beaten from above
        lo_z, hi_z = -5.0, 5.0
        for _ in range(100):                       # solve 1 - phi(z)^2 = q
            mid = (lo_z + hi_z) / 2
            if 1 - phi(mid) ** 2 > q:
                lo_z = mid
            else:
                hi_z = mid
        z = (lo_z + hi_z) / 2
        line = MU + z * SD
        print(f"scenario {name}: rank <= {rank} -> private line ~ {line:.1f}")
        for gain in (0, 2, 4, 6):
            p = 1 - phi((line - (MU + gain)) / SD) ** 2
            print(f"   true mean +{gain}: P(best of 2 selected draws >= line) = {p:.2f}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/leaderboard/publicleaderboard-2026-10-10T17-12-56.csv")
