"""Which stuck level attempts in Franzen's 4x25 run fall on levels whose start state has a cyclic action?

Usage: python crossref_stuck.py BENCHMARK_JSON ALGEBRA_JSON [interior|exact]
'stuck-recoverable' = unfinished attempt on a (game, level) completed in another pass;
'never' = (game, level) never completed in any pass.
"""
import collections, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "2026-10-10"))
from attempts import attempts  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from summarize_algebra import summarise  # noqa: E402

bench, alg = json.load(open(sys.argv[1]))["game_runs"], json.load(open(sys.argv[2]))
mode = sys.argv[3] if len(sys.argv) > 3 else "interior"
cyc = {g: set(r["cyclic_levels"]) for g, r in summarise(alg, mode).items()}
probed = {g[:4]: {s["levels_completed"] + 1 for s in st} for g, st in alg.items()}
by = collections.defaultdict(list)
for r in bench:
    for a in attempts(r):
        by[(r["game_id"][:4], a["level"])].append(a)
rec, never = [], []
for (g, lv), v in by.items():
    for a in v:
        if not a["done"]:
            (rec if any(x["done"] for x in v) else never).append((g, lv))
for name, lst in (("stuck-recoverable", rec), ("never-completed", never)):
    tested = [x for x in lst if x[1] in probed.get(x[0], set())]
    hit = [x for x in tested if x[1] in cyc.get(x[0], set())]
    print(f"[{mode}] {name}: attempts={len(lst)} level-start probed={len(tested)} with a cyclic action={len(hit)} {sorted(collections.Counter(hit).items())}")
