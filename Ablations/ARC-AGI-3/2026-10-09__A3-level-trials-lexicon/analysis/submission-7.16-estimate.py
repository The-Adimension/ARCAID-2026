"""What does the configuration of the 7.16 submission (habanwer/arcaid3-lt-lex-r3 v1) cost?

The notebook sets USE_PRIORITY_SCHEDULING = False, so on the hidden rerun Franzen's competition
overrides never apply: 10 games at a time, 20 minutes (1200 s) each, no priority gate.
Two estimates of the effect on the 25 public games:
  (a) the notebook's own Save & Run: its '@L0' entries are whole games from level 1 under exactly
      those settings (20 minutes, concurrency 10, no gate);
  (b) Franzen's 4x25 run with his competition-scaled budget, counting only levels completed within
      the generated-token budget a 20-minute entry actually got.
Usage: python estimate.py LT_BENCHMARK_JSON FRANZEN_BENCHMARK_JSON
"""
from __future__ import annotations

import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "2026-10-10"))
from rhae import check_scorer, cumulative_tokens, game_score, load_runs, run_tokens  # noqa: E402


def capped(r, cap):
    cum = cumulative_tokens(r)
    done = end = 0
    for k in range(r["levels_completed"]):
        end += r["actions_per_level"][k]
        if cum[end - 1] > cap:
            break
        done = k + 1
    return game_score(r["base_actions_per_level"], r["actions_per_level"], done)


def main(lt_path, fr_path):
    lt, fr = load_runs(lt_path), load_runs(fr_path)
    assert check_scorer(lt) == 0 and check_scorer(fr) == 0
    l0 = [r for r in lt if r["game_id"].endswith("@L0")]
    cap = st.median(run_tokens(r) for r in lt)
    full = st.mean(r["final_score"] for r in fr)
    a = st.mean(r["final_score"] for r in l0)
    b = st.mean(capped(r, cap) for r in fr)
    print(f"lt-lex-r3 save run: {len(lt)} entries; median generated tokens per 20-min entry = {cap:,.0f}")
    print(f"Franzen full configuration: mean {full:.2f}; median tokens per game "
          f"{st.median(run_tokens(r) for r in fr):,.0f}")
    print(f"(a) lt-lex-r3 '@L0' whole games, 20-min cap: mean {a:.2f} = {a / full:.3f} of full")
    print(f"(b) Franzen runs capped at {cap:,.0f} tokens:  mean {b:.2f} = {b / full:.3f} of full")
    for name, x in (("a", a), ("b", b)):
        print(f"    LB-equivalent of ({name}) at the copy mean 25.77: {25.77 * x / full:.2f}")
    print("per game, Franzen full mean -> capped mean -> lt @L0:")
    fg = {}
    for r in fr:
        fg.setdefault(r["game_id"][:4], []).append(r)
    l0g = {r["game_id"][:4]: r["final_score"] for r in l0}
    for g in sorted(fg):
        print(f"  {g}: {st.mean(x['final_score'] for x in fg[g]):6.2f} -> "
              f"{st.mean(capped(x, cap) for x in fg[g]):6.2f} -> {l0g.get(g, float('nan')):6.2f}")
    print(f"rerun wall time if 110 games run 10 at a time for 20 min each: about "
          f"{-(-110 // 10) * 20} min of the 540-min limit (plus model start-up)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
