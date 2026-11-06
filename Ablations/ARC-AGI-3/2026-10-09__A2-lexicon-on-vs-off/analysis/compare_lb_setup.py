"""Lexicon on against off in the leaderboard-like setup (lb_setup.py): all 25 public games at once, 121 min each.

  python3 kaggle/lexicon-dfranzen/compare_lb_setup.py [--fetch] [round ...]

With --fetch, first downloads each arm's benchmark.json, summary, logs and request logs (read-only; the raw
request logs stay out of the repo), using compare_replicates.fetch.

Per arm: levels, 25-game mean score, levels-over-time area (below), tokens, cache reuse, view and `.rules` use.
Per game: both arms side by side, and a paired sign-flip test over games on the score and on the area.

Levels-over-time area, per game: the share of the game's levels already completed, averaged over its time
budget (0 to 100). A level completed at time t of a budget T adds (T - t) / T / levels. It credits clearing
levels sooner, and it moves less from run to run than the final score, whose late levels weigh most.
Caution: the games of one run share a GPU, so they are not independent; with one run per arm the per-game
test is a guide, not a verdict.
"""
import json
import pathlib
import random
import re
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import compare_replicates as cr  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXP = ROOT / "experiments/2026-10-09__lb-setup-lexicon-vs-off"
BUDGET_S = 532 * 60 * 25 // 110


def area(g, budget=BUDGET_S):
    h, apl, n = g["history"], g["actions_per_level"], g["number_of_levels"]
    total, done = 0.0, 0
    for k in range(g["levels_completed"]):
        done += apl[k]
        t = h[done - 1]["wallclock_seconds"] if done else 0.0
        total += max(0.0, budget - t) / budget
    return 100 * total / n


def run(folder):
    bj = json.load(open(folder / "outputs/benchmark.json"))
    games = {g["game_id"][:4]: {"levels": g["levels_completed"], "score": g["final_score"], "area": area(g),
                                "n": g["number_of_levels"], "actions": len(g["history"])} for g in bj["game_runs"]}
    base = cr.run(folder) if (folder / "request_usage.csv").exists() else {"reuse": float("nan"), "view": "-", "rules": "-"}
    log = (folder / "log.txt").read_text() if (folder / "log.txt").exists() else ""
    final = next((l for l in log.splitlines() if l.startswith("ARCAID3_LEXICON_FINAL")), "")
    off = "ARCAID3_LEXICON_OFF" in log
    return {"games": games, "levels": sum(v["levels"] for v in games.values()),
            "mean": statistics.mean(v["score"] for v in games.values()),
            "area": statistics.mean(v["area"] for v in games.values()),
            "reuse": base["reuse"], "view": base["view"], "rules": base["rules"], "off": off,
            "errors": (re.search(r"'errors': (\d+)", final) or [None, "-"])[1]}


def sign_flip(diffs, n=200_000, seed=0):
    """Two-sided p for a mean difference of zero, by random sign flips (paired by game)."""
    obs = abs(statistics.mean(diffs))
    rng = random.Random(seed)
    hits = sum(abs(sum(d if rng.random() < 0.5 else -d for d in diffs)) / len(diffs) >= obs - 1e-12 for _ in range(n))
    return (hits + 1) / (n + 1)


def pooled(rounds):
    """All rounds together, and the decision rule fixed before round 2 (DECISION_RULE.md)."""
    runs = {arm: [run(EXP / f"arcaid3-lb-{arm}-r{r}") for r in rounds] for arm in ("lex", "off")}
    per_round = [a["mean"] - b["mean"] for a, b in zip(runs["lex"], runs["off"])]
    primary = statistics.mean(per_round)
    gs = sorted(runs["lex"][0]["games"])
    per_game = [statistics.mean(a["games"][g]["score"] - b["games"][g]["score"] for a, b in zip(runs["lex"], runs["off"]))
                for g in gs]
    p = sign_flip(per_game)
    area = statistics.mean(a["area"] - b["area"] for a, b in zip(runs["lex"], runs["off"]))
    levels = statistics.mean(a["levels"] - b["levels"] for a, b in zip(runs["lex"], runs["off"]))
    on_means = ", ".join(f"{x['mean']:.2f}" for x in runs["lex"])
    off_means = ", ".join(f"{x['mean']:.2f}" for x in runs["off"])
    lines = [f"pooled over rounds {', '.join(map(str, rounds))}:",
             f"  round means: lexicon on {on_means}; off {off_means}",
             f"  run-to-run spread (SD over rounds): on {statistics.stdev([x['mean'] for x in runs['lex']]):.2f}, "
             f"off {statistics.stdev([x['mean'] for x in runs['off']]):.2f}",
             f"  on - off per round: {', '.join(f'{d:+.2f}' for d in per_round)}",
             f"  primary (mean over rounds): {primary:+.2f}; per-game sign-flip p = {p:.3f}; "
             f"levels {levels:+.1f}; area {area:+.2f}"]
    if primary >= 5.0 and all(d > 0 for d in per_round) and p < 0.10:
        verdict = "RECOMMEND SUBMITTING v5 (primary >= +5.0, positive in every round, p < 0.10)"
    elif primary < 2.0 or per_round[-1] <= 0:
        verdict = "NO MEASURABLE EFFECT (primary < +2.0, or the latest round's difference is not positive)"
    elif len(rounds) >= 3:
        verdict = "STILL INCONCLUSIVE AFTER THREE ROUNDS: treat as no measurable effect"
    else:
        verdict = "INCONCLUSIVE: run one more round under the same rule"
    return lines + [f"  decision (rule fixed before round 2): {verdict}", ""]


def main():
    rounds = [int(a) for a in sys.argv[1:] if a.isdigit()] or [1]
    if "--fetch" in sys.argv:
        for r in rounds:
            for arm in ("lex", "off"):
                folder = EXP / f"arcaid3-lb-{arm}-r{r}"
                cr.fetch(folder.name, folder)
    lines = []
    for r in rounds:
        lex, off = run(EXP / f"arcaid3-lb-lex-r{r}"), run(EXP / f"arcaid3-lb-off-r{r}")
        assert off["off"] and not lex["off"], "the control arm must log ARCAID3_LEXICON_OFF, the lexicon arm must not"
        lines += [f"round {r}: 25 public games at once, {BUDGET_S} s per game",
                  "arm   levels   mean score   levels-over-time area   cache   view   .rules   errors"]
        for name, x in (("lex", lex), ("off", off)):
            lines.append(f"{name:5s} {x['levels']:6d} {x['mean']:12.2f} {x['area']:23.2f} {x['reuse']:6.1f}% {x['view']:>6s} "
                         f"{x['rules']:>6s} {x['errors']:>8s}")
        gs = sorted(lex["games"])
        ds = [lex["games"][g]["score"] - off["games"][g]["score"] for g in gs]
        da = [lex["games"][g]["area"] - off["games"][g]["area"] for g in gs]
        dl = [lex["games"][g]["levels"] - off["games"][g]["levels"] for g in gs]
        lines += ["",
                  f"lex - off, paired by game: score {statistics.mean(ds):+.2f} (sign-flip p = {sign_flip(ds):.2f}); "
                  f"area {statistics.mean(da):+.2f} (p = {sign_flip(da):.2f}); levels {sum(dl):+d} "
                  f"(games better / worse / same: {sum(d > 0 for d in dl)} / {sum(d < 0 for d in dl)} / {sum(d == 0 for d in dl)})",
                  "", f"{'game':5s} {'levels lex/off':>15s} {'score lex':>10s} {'score off':>10s} {'area lex':>9s} {'area off':>9s}"]
        for g in gs:
            a, b = lex["games"][g], off["games"][g]
            lines.append(f"{g:5s} {a['levels']:>7d}/{b['levels']:<2d} of {a['n']:<2d} {a['score']:10.1f} {b['score']:10.1f} "
                         f"{a['area']:9.1f} {b['area']:9.1f}")
        lines.append("")
    if len(rounds) > 1:
        lines += pooled(rounds)
    out = "\n".join(lines)
    EXP.mkdir(parents=True, exist_ok=True)
    (EXP / "compare_lb_setup.out").write_text(out + "\n")
    print(out)


if __name__ == "__main__":
    main()
