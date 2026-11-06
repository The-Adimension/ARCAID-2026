"""Same-day pair: restart v2 on (100K) against restart off (flag 0). Applies DECISION_RULE_PAIR.md.

  python kaggle/restart-dfranzen/compare_pair.py [--fetch]

Arms: habanwer/arcaid3-pair-restart-r1 and habanwer/arcaid3-pair-flag0-r1b (identical cells except the flag and the
head note), run side by side. Outputs go to experiments/2026-10-13__restart-pair/<slug>/.
Earlier runs in the same setup are read for the pooled (secondary) mechanism test:
  restart on : experiments/2026-10-12__restart-dfranzen/arcaid3-restart-dfranzen-m2{,-r2}/benchmark.json (restart v1)
  restart off: arcaid3-lb-off-r1/-r2 and arcaid3-lb-lex-r1/-r2 (Franzen code; lexicon measured as no effect), from
               origin/claude/gracious-thompson-6is9pp:experiments/2026-10-09__lb-setup-lexicon-vs-off/<slug>/outputs/
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import random
import re
import subprocess
import sys
from math import comb

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "experiments/2026-10-13__restart-pair"
ON, OFF = "arcaid3-pair-restart-r1", "arcaid3-pair-flag0-r1b"
R = 100_000
EARLIER_ON = [ROOT / f"experiments/2026-10-12__restart-dfranzen/{s}/benchmark.json"
              for s in ("arcaid3-restart-dfranzen-m2", "arcaid3-restart-dfranzen-m2-r2")]
EARLIER_OFF = ["arcaid3-lb-off-r1", "arcaid3-lb-off-r2", "arcaid3-lb-lex-r1", "arcaid3-lb-lex-r2"]
EARLIER_OFF_REF = "origin/claude/gracious-thompson-6is9pp"


def _compare_restart():
    spec = importlib.util.spec_from_file_location("compare_restart", HERE / "compare_restart.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.OUT = OUT
    return mod


def run_tokens(r):
    m = re.search(r"tokens=(\d+)", r.get("solver_note") or "")
    return int(m.group(1)) if m else sum(h["generated_tokens"] for h in r["history"])


def attempts(r):
    """(level 1-based, completed, generated tokens on the level) per level attempt, as analysis/2026-10-10/attempts.py."""
    cum, t = [], 0
    for h in r["history"]:
        t += h["generated_tokens"]
        cum.append(t)
    out, start_idx, start_tok = [], 0, 0
    for k, n in enumerate(r["actions_per_level"]):
        if k < r["levels_completed"]:
            end_idx = start_idx + n
            end_tok = cum[end_idx - 1] if end_idx > 0 else start_tok
            out.append((k + 1, True, end_tok - start_tok))
            start_idx, start_tok = end_idx, end_tok
        else:
            out.append((k + 1, False, run_tokens(r) - start_tok))
            break
    return out


def past_r(runs):
    """Attempts whose level used >= R generated tokens: (n, of which completed)."""
    a = [x for r in runs for x in attempts(r) if x[2] >= R]
    return len(a), sum(x[1] for x in a)


def past_r_keyed(runs):
    """[(game_id, level, completed)] for attempts whose level used >= R generated tokens."""
    return [(r["game_id"], lvl, done) for r in runs for (lvl, done, tok) in attempts(r) if tok >= R]


def stratified_perm(on, off, reps=100_000, seed=20261014):
    """One-sided p for 'restart on completes more', permuting arm labels within each (game, level) stratum.

    Repeated game-levels across runs are not independent trials; this keeps each stratum's arm sizes and
    completions fixed. Strata seen in only one arm carry no information and drop out.
    """
    strata = {}
    for arm, rows in ((1, on), (0, off)):
        for g, lvl, done in rows:
            strata.setdefault((g, lvl), []).append((arm, int(done)))
    informative = [v for v in strata.values() if len({a for a, _ in v}) == 2]
    obs = sum(d for v in informative for a, d in v if a == 1)
    rng = random.Random(seed)
    hits = 0
    for _ in range(reps):
        tot = 0
        for v in informative:
            outcomes = [d for _, d in v]
            n_on = sum(a for a, _ in v)
            rng.shuffle(outcomes)
            tot += sum(outcomes[:n_on])
        hits += tot >= obs
    return hits / reps, len(informative), sum(len(v) for v in informative)


def fisher_greater(a, n1, b, n2):
    """One-sided Fisher exact p for rate a/n1 > b/n2."""
    k, n = a + b, n1 + n2
    return sum(comb(k, i) * comb(n - k, n1 - i) / comb(n, n1) for i in range(a, min(k, n1) + 1))


def sign_flip(diffs, reps=200_000, seed=20261013):
    rng = random.Random(seed)
    obs = abs(sum(diffs))
    hits = sum(abs(sum(d if rng.random() < 0.5 else -d for d in diffs)) >= obs - 1e-12 for _ in range(reps))
    return hits / reps


def boot_ci(diffs, reps=20_000, seed=7):
    rng = random.Random(seed)
    ms = sorted(sum(rng.choice(diffs) for _ in diffs) / len(diffs) for _ in range(reps))
    return ms[int(0.025 * reps)], ms[int(0.975 * reps) - 1]


def earlier_off_runs():
    runs = []
    for s in EARLIER_OFF:
        path = f"experiments/2026-10-09__lb-setup-lexicon-vs-off/{s}/outputs/benchmark.json"
        txt = subprocess.run(["git", "show", f"{EARLIER_OFF_REF}:{path}"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        runs.append(json.loads(txt)["game_runs"])
    return runs


def main():
    cr = _compare_restart()
    if "--fetch" in sys.argv:
        for s in (ON, OFF):
            cr.fetch(s)
    data = {}
    for s, tok in ((ON, "100000"), (OFF, "0")):
        b, log, events = cr.read(s)
        runs = b["game_runs"]
        ready = re.search(r"ARCAID3_RESTART_READY \{'tokens': (\d+)", log)
        health = {"ready_tokens_" + tok: bool(ready and ready.group(1) == tok),
                  "no_traceback": "Traceback (most recent call last)" not in log,
                  "games_25": len(runs) == 25 and all(r.get("history") for r in runs),
                  # a crashed game is caught by the solver without a traceback; a killed run leaves end_time unset
                  "states_won_or_gave_up": all(r.get("state") in ("won", "gave_up") for r in runs),
                  "no_failed_notes": not any(str(r.get("solver_note") or "").startswith(("error:", "analyzer failed")) for r in runs),
                  "run_finished": b.get("end_time") is not None,
                  "summary_cell_ran": "ARCAID3_RESTART_FINAL" in log}
        if s == OFF:
            health["no_restart_events"] = not [e for e in events if e.get("event") == "restart"]
        data[s] = dict(runs=runs, events=events, health=health)
        print(f"{s}: health {health}")
    valid = all(all(d["health"].values()) for d in data.values())
    if not valid:
        print("decision: INVALID PAIR (health rule); nothing is judged")
        return

    on, off = data[ON]["runs"], data[OFF]["runs"]
    by_on = {r["game_id"]: r for r in on}
    fired = [e for e in data[ON]["events"] if e["event"] == "restart"]
    conv = []
    for e in fired:
        m = cr.STATE.search(e["state_path"])
        r = by_on.get(m.group(1)) if m else None
        conv.append(bool(r and r["levels_completed"] >= e["level"]))
    n_on, k_on = past_r(on)
    n_off, k_off = past_r(off)
    covered = len({(cr.STATE.search(e["state_path"]).group(1), e["level"]) for e in fired if cr.STATE.search(e["state_path"])})
    print(f"\nsame day, restart arm: {len(fired)} restarts ({sum(e.get('resumed_turn', False) for e in fired)} on a no-action "
          f"resumption), {sum(conv)} of them completed their level afterwards; restarts reached {covered} of its {n_on} "
          f"attempts past {R // 1000}K tokens")
    p_same = fisher_greater(k_on, n_on, k_off, n_off)
    print(f"PRIMARY, same day, attempts past {R // 1000}K tokens that completed later: restart on {k_on}/{n_on} "
          f"({k_on / max(1, n_on):.1%}), restart off {k_off}/{n_off} ({k_off / max(1, n_off):.1%}); one-sided Fisher p = {p_same:.3f}")

    # secondary: pooled over every run in this setup (restart v1 on 10-12, v2 here; controls 10-09 and here)
    e_on = [json.loads(p.read_text())["game_runs"] for p in EARLIER_ON]
    e_off = earlier_off_runs()
    pn_on, pk_on = map(sum, zip(*[past_r(x) for x in [on, *e_on]]))
    pn_off, pk_off = map(sum, zip(*[past_r(x) for x in [off, *e_off]]))
    p_naive = fisher_greater(pk_on, pn_on, pk_off, pn_off)
    p_mech, n_strata, n_strat_att = stratified_perm(
        [x for runs in [on, *e_on] for x in past_r_keyed(runs)],
        [x for runs in [off, *e_off] for x in past_r_keyed(runs)])
    print(f"SECONDARY, pooled (3 runs on: v1 x2 + v2; 5 runs off): restart on {pk_on}/{pn_on} = {pk_on / max(1, pn_on):.1%}, "
          f"restart off {pk_off}/{pn_off} = {pk_off / max(1, pn_off):.1%}; stratified by game-level p = {p_mech:.3f} "
          f"({n_strata} strata seen in both arms, {n_strat_att} attempts); naive Fisher p = {p_naive:.3f} (anti-conservative)")

    # same-day score, paired by game
    by_off = {r["game_id"]: r for r in off}
    games = sorted(set(by_on) & set(by_off))
    diffs = [by_on[g]["final_score"] - by_off[g]["final_score"] for g in games]
    lv = [by_on[g]["levels_completed"] - by_off[g]["levels_completed"] for g in games]
    s_on = sum(by_on[g]["final_score"] for g in games) / len(games)
    s_off = sum(by_off[g]["final_score"] for g in games) / len(games)
    lo, hi = boot_ci(diffs)
    print(f"\nsame-day score: restart on {s_on:.2f}, restart off {s_off:.2f}; difference {s_on - s_off:+.2f} "
          f"(per-game bootstrap 95% CI {lo:+.2f} to {hi:+.2f}; sign-flip p = {sign_flip(diffs):.3f}); levels {sum(lv):+d}")
    print("  (a same-day difference must exceed about +/-13-17 points to reach p < 0.05; the plausible effect of the "
          "mechanism is about +1 point, so a large difference either way is noise)")
    long_on = {g for g, _, _ in past_r_keyed(on)}
    long_off = {g for g, _, _ in past_r_keyed(off)}
    print("  per game (score, levels); markers: a = restart arm had an attempt past 100K, b = control had one, "
          "R = a restart fired (selection-biased, shown for reference only)")
    rest = {cr.STATE.search(e['state_path']).group(1) for e in fired if cr.STATE.search(e['state_path'])}
    for g in games:
        tag = ("a" if g in long_on else " ") + ("b" if g in long_off else " ") + ("R" if g in rest else " ")
        print(f"  {tag} {g[:4]}  on {by_on[g]['final_score']:6.1f} ({by_on[g]['levels_completed']})  "
              f"off {by_off[g]['final_score']:6.1f} ({by_off[g]['levels_completed']})")
    prior = [43.77, 47.57, 51.20, 40.08]
    print(f"  day check: control today {s_off:.2f} against the 10-09 controls {prior} (mean {sum(prior) / 4:.2f}); "
          f"restart v1 on 10-12: 37.60, 37.99")

    mech = p_mech < 0.05 and k_on / max(1, n_on) > k_off / max(1, n_off)
    print(f"\nmechanism (same-day rate higher and pooled stratified p < 0.05): {'CONFIRMED' if mech else 'NOT CONFIRMED'}")
    if mech and s_on - s_off >= 0:
        verdict = "RESTART BECOMES THE DEFAULT for remaining submissions and final selection"
    else:
        verdict = "NO CHANGE: restart stays an equivalent draw; the base configuration remains the default"
    print(f"decision: {verdict}")


if __name__ == "__main__":
    main()
