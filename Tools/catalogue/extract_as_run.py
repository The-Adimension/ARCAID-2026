"""Copy the exact text of each ARCAID component, as it ran on Kaggle, into ARCAID/<component>/as-run/.

  python -I extract_as_run.py REPO_ROOT

Looks at every added or changed cell (the `added/` folders that build_catalogue.py wrote, against the
parent and against the root base) and assigns it to a component by a marker string. Identical cell
texts are stored once, named by their first notebook version; as-run/INDEX.csv lists every notebook
version that ran each text (by sha256).
"""
import csv, hashlib, json, sys
from collections import defaultdict
from pathlib import Path

MARKERS = [  # (component, marker); the first match wins
    ("startup-guard", "Startup guard (SG)"),
    ("probe-first", "Probe-first governor (PF)"),
    ("stuck-level-restart", "ARC3_STUCK_RESTART_TOKENS"),
    ("lexicon-view", "ARCAID3 lexicon view: one extra"),
    ("lexicon-arc-agi-2", "%%writefile /kaggle/working/agent/"),
    ("duck-taaf-addons-2026-09", "arc3_batch"),
    ("duck-taaf-addons-2026-09", "arc3_stall"),
    ("duck-taaf-addons-2026-09", "arc3_ledger"),
    ("duck-taaf-addons-2026-09", "ARC3_COMPACT"),
    ("duck-taaf-addons-2026-09", "WMREASON"),
    ("duck-taaf-addons-2026-09", "arc3_tricks"),
]

root = Path(sys.argv[1])
seen = defaultdict(list)          # (component, sha) -> [(kernel, version, cell, path)]
for rj in sorted(root.glob("**/run.json")):
    run = json.loads(rj.read_text())
    if run["track"] == "ARC-AGI-2":
        comps = ["lexicon-arc-agi-2"]
    else:
        comps = None
    cells = []
    if comps and (rj.parent / "notebook.ipynb").exists():      # ARC-AGI-2: every agent file of every version
        nb = json.loads((rj.parent / "notebook.ipynb").read_text(encoding="utf-8"))
        for i, c in enumerate(nb["cells"]):
            if c["cell_type"] == "code":
                cells.append((f"cell{i:02d}", c["source"] if isinstance(c["source"], str) else "".join(c["source"])))
    for added in [rj.parent / "added", rj.parent / "vs-root-base" / "added"]:
        if added.is_dir():
            cells += [(p.stem, p.read_text(encoding="utf-8")) for p in sorted(added.glob("cell*.py"))]
    for stem, text in cells:
        comp = next((c for c, m in MARKERS if m in text and (comps is None or c in comps)), None)
        if not comp:
            continue
        sha = hashlib.sha256(text.encode()).hexdigest()
        seen[(comp, sha)].append((run["kernel"].split("/")[-1], run["version"], stem, text))

by_comp = defaultdict(list)
for (comp, sha), uses in seen.items():
    uses = sorted({(k, v, c): t for k, v, c, t in uses}.items())
    (k, v, c), text = uses[0]
    by_comp[comp].append((sha, k, v, c, text, [f"{k}@v{v}:{c}" for (k, v, c), _ in uses]))
for comp, items in by_comp.items():
    d = root / "ARCAID" / comp / "as-run"
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("*.py"):
        old.unlink()
    with open(d / "INDEX.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["file", "sha256", "lines", "ran_in"])
        for sha, k, v, c, text, ran in sorted(items, key=lambda x: (x[1], x[2], x[3])):
            name = f"{k}__v{v}__{c}.py"
            (d / name).write_text(text, encoding="utf-8")
            w.writerow([name, sha, len(text.splitlines()), " ".join(sorted(set(ran)))])
    print(comp, len(items), "distinct cell texts")
