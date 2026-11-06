"""Infer which earlier notebook each of our notebook versions was built from, by code distance.

  python -I infer_parents.py RAW_DIR BASES_DIR OUT.csv

RAW_DIR   our versions, as written by Tools/kaggle/collect_runs.py (<slug>/v<N>/__notebook__.ipynb)
BASES_DIR third-party versions, as written by Tools/kaggle/pull_bases.py (<owner>__<slug>/v<N>.ipynb)

For each of our versions, every notebook that started running earlier (ours or third-party) is a
candidate. Distance = the number of code lines that are in one notebook and not the other (multiset
symmetric difference over code cells; markdown and outputs ignored). The nearest candidate is
reported as the inferred parent, with the runner-up, so a close call is visible. On a tie the
earliest-started candidate wins, so an unchanged copy is never credited over its original. Start times come
from the notebook's own papermill metadata. Distance 0 means the code is identical.
This is evidence, not a declaration: Documentation and ARCAID/LINEAGE.md state where an inferred
parent was checked against the author's own records.
"""
import csv, json, sys
from collections import Counter
from pathlib import Path


def load(p):
    nb = json.loads(Path(p).read_text(encoding="utf-8"))
    lines = Counter()
    for c in nb.get("cells", []):
        if c.get("cell_type") != "code":
            continue
        s = c["source"] if isinstance(c["source"], str) else "".join(c["source"])
        lines.update(l.rstrip() for l in s.splitlines() if l.strip())
    start = (nb.get("metadata", {}).get("papermill", {}) or {}).get("start_time")
    return lines, start


def dist(a, b):
    return sum(((a - b) + (b - a)).values())


def main():
    raw, bases, out = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    nodes = []
    for p in sorted(raw.glob("*/v*/__notebook__.ipynb")):
        lines, start = load(p)
        nodes.append({"id": f"habanwer/{p.parent.parent.name}@v{p.parent.name[1:]}", "lines": lines, "start": start, "ours": True})
    for p in sorted(bases.glob("*/v*.ipynb")):
        lines, start = load(p)
        owner, slug = p.parent.name.split("__", 1)
        nodes.append({"id": f"{owner}/{slug}@v{p.stem[1:]}", "lines": lines, "start": start, "ours": False})
    rows = []
    for n in nodes:
        if not n["ours"]:
            continue
        cands = [m for m in nodes if m is not n and m["start"] and n["start"] and m["start"] < n["start"]]
        scored = sorted((dist(n["lines"], m["lines"]), m["start"], m["id"]) for m in cands)  # ties: the earliest original wins
        best = (scored[0][0], scored[0][2]) if scored else (None, "")
        second = (scored[1][0], scored[1][2]) if len(scored) > 1 else (None, "")
        rows.append([n["id"], n["start"] or "", sum(n["lines"].values()), best[1], best[0], second[1], second[0]])
    rows.sort(key=lambda r: r[1])
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["notebook", "started", "code_lines", "nearest_earlier", "distance", "runner_up", "runner_up_distance"])
        w.writerows(rows)
    print(len(rows), "rows ->", out)


if __name__ == "__main__":
    main()
