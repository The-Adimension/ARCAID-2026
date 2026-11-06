"""Re-runnable derivations behind the derived rows of AGI-RUBIQ-CORPUS-2026-10-01.

Reads files only. Replays nothing, loads no pickle, starts no engine.
Run from the repo root:  python corpus/derive_2026-10-01.py > /tmp/derived.json
"""

from __future__ import annotations

import csv
import difflib
import glob
import hashlib
import json
import os
import re
import statistics as st

RUN_GLOBS = ("submissions/2026-*", "experiments/2026-*")


def code_lines(nb_path: str) -> list[str]:
    nb = json.load(open(nb_path))
    cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
    return "\n".join(cells).splitlines()


def code_hash(nb_path: str) -> str:
    nb = json.load(open(nb_path))
    cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
    return hashlib.sha256("\n#--\n".join(cells).encode()).hexdigest()[:16]


def pearson(x, y) -> float:
    mx, my = st.mean(x), st.mean(y)
    sx = sum((a - mx) ** 2 for a in x) ** 0.5
    sy = sum((b - my) ** 2 for b in y) ** 0.5
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def ranks(v):
    s = sorted(v)
    return [s.index(a) + 1 for a in v]


def add_only_diff(base_nb: str, arm_nb: str) -> dict:
    d = [l for l in difflib.unified_diff(code_lines(base_nb), code_lines(arm_nb), lineterm="", n=0)
         if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    return {
        "added": sum(l[0] == "+" for l in d),
        "removed": sum(l[0] == "-" for l in d),
        "change_a_header": any("Change A (wmreason)" in l for l in d),
    }


def main() -> None:
    out: dict = {"runs": {}}
    for d in sorted(sum((glob.glob(g) for g in RUN_GLOBS), [])):
        if not os.path.isdir(d):
            continue
        nb = f"{d}/__notebook__.ipynb"
        log = f"{d}/__output__.json"
        txt = open(log, errors="ignore").read() if os.path.exists(log) else ""
        games = None
        sj = sorted(glob.glob(f"{d}/outputs/**/score.json", recursive=True))
        if sj:
            g = json.load(open(sj[0])).get("games", {})
            if g:
                games = {"n_games": len(g), "mean": round(st.mean(v["score"] for v in g.values()), 2)}
        bj = sorted(glob.glob(f"{d}/outputs/**/benchmark.json", recursive=True))
        bench = None
        if bj:
            b = json.load(open(bj[0]))
            runs = b.get("game_runs") or []
            bench = {"n_passes": b.get("n_passes"), "game_runs": len(runs),
                     "actions": sum(len(r.get("history") or []) for r in runs)}
        out["runs"][d] = {
            "code_hash": code_hash(nb) if os.path.exists(nb) else None,
            "benchmark_json": bench,
            "score_json": games,
            "prints_public25_runs_25": "PUBLIC25_AUDIT runs=25" in txt,
            "true_submission_flags": sorted(set(re.findall(r"TRUE_SUBMISSION=\w+", txt))),
        }

    rows = list(csv.DictReader(open("submissions/index.csv")))
    out["index_csv"] = {
        "rows": len(rows),
        "private_score_nonempty": sum(1 for r in rows if r["private_score"].strip()),
        "contains_4_19": any(r["public_score"].strip() == "4.19" for r in rows),
    }

    # 6-game probe (score.json) vs public LB (index.csv); pairs named in report-2026-09-27.
    p5 = [(41.37, 3.39), (34.93, 2.78), (32.50, 2.84), (28.92, 3.37), (25.08, 3.59)]
    p6 = p5 + [(28.24, 3.03)]  # wmreason, after the report
    for name, p in (("n5", p5), ("n6", p6)):
        x, y = zip(*p)
        out[f"probe_vs_lb_{name}"] = {"pearson": round(pearson(x, y), 3),
                                      "spearman": round(pearson(ranks(x), ranks(y)), 3)}

    duck8 = [3.04, 3.37, 2.84, 2.57, 3.01, 3.39, 3.59, 2.78]  # 09-19 .. 09-26
    duck9 = duck8 + [3.03]  # + 09-27 wmreason
    out["duck_flashnext_draws"] = {
        "n8": {"mean": round(st.mean(duck8), 3), "sd": round(st.stdev(duck8), 3)},
        "n9": {"mean": round(st.mean(duck9), 3), "sd": round(st.stdev(duck9), 3)},
    }

    S = "submissions/"
    out["change_a_pairs"] = {
        "duck_v3": add_only_diff(
            S + "2026-09-25__duck-nvfp4-batch-stall-warn-dead-sign__v3__score-3.59/__notebook__.ipynb",
            S + "2026-09-27__duck-v3-wmreason__v1__score-3.03/__notebook__.ipynb"),
        "sheetu_0922": add_only_diff(
            S + "2026-09-30__taaf-flashnext-sheetu12b-0922__v1__score-4.17/__notebook__.ipynb",
            S + "2026-09-28__taaf-flashnext-sheetu12b-reasoning-notes__v3__score-3.90/__notebook__.ipynb"),
    }

    levels = 0
    metas = sorted(glob.glob("inputs/official-input-arc-prize-2026-arc-agi-3/environment_files/*/*/metadata.json"))
    for m in metas:
        levels += len(json.load(open(m))["baseline_actions"])
    out["official_env"] = {"games": len(metas), "levels": levels}

    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
