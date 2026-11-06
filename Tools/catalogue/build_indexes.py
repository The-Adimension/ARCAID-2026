"""Write the index pages from the run.json files that build_catalogue.py produced.

  python -I build_indexes.py REPO_ROOT

Writes:
  Submissions/<track>/README.md   every submission, oldest first, linked to its version folder
  Documentation/LINKS.md          every notebook version: Kaggle URL and its folder here
  ARCAID/LINEAGE.md               every version's inferred parent and root base, as a tree per root
Nothing here is typed by hand: re-run after build_catalogue.py.
"""
import csv, json, sys
from collections import defaultdict
from pathlib import Path

root = Path(sys.argv[1])
runs = []
for p in sorted(root.glob("**/run.json")):
    r = json.loads(p.read_text())
    r["_dir"] = p.parent.relative_to(root).as_posix()
    runs.append(r)
by_sid = {str(r["script_version_id"]): r for r in runs if r.get("script_version_id")}


def link(r, frm):
    rel = Path(r["_dir"]).relative_to(frm) if r["_dir"].startswith(frm) else Path("../" * len(Path(frm).parts)) / r["_dir"]
    return rel.as_posix() + "/"


# 1. Track indexes
for track in ("ARC-AGI-3", "ARC-AGI-2"):
    frm = f"Submissions/{track}"
    rows = list(csv.DictReader(open(root / frm / "submissions.csv")))
    out = [f"# {track} submissions", "",
           f"All {len(rows)} submissions to the Kaggle competition, oldest first, from the Kaggle API (`submissions.csv`). "
           "`selected` marks the submissions chosen for final scoring (`selected.csv`; the API does not expose this). "
           "Private scores are published on 2026-12-04.", "",
           "Each row links to the folder of the notebook version that was submitted. "
           "Notebook versions that were run but never submitted, and were not part of a controlled test, are in [`_development/`](_development/). "
           "Controlled tests are in [`../../Ablations/" + track + "/`](../../Ablations/" + track + "/).", "",
           "| # | Submitted (UTC) | Notebook, version | Public score | Status | Selected | Folder |", "|---|---|---|---|---|---|---|"]
    for i, s in enumerate(rows, 1):
        r = by_sid.get(s["script_version_id"] or "")
        nb = f"`{(s['kernel'] or '').split('/')[-1]}` v{r['version']}" if r else f"`{(s['kernel'] or '').split('/')[-1]}`"
        flag = (" (late, not counted)" if s["after_deadline"] == "yes" else "")
        out.append(f"| {i} | {s['submitted_utc'][:16].replace('T', ' ')}{flag} | {nb} | {s['public_score'] or '—'} | "
                   f"{s['status'].lower()} | {'**yes**' if s['selected'] == 'yes' else ''} | "
                   f"{('[folder](' + link(r, frm) + ')') if r else 'not collected'} |")
    (root / frm / "README.md").write_text("\n".join(out) + "\n")

# 2. Links registry
out = ["# Links", "",
       "Every notebook version of ours that used an ARC Prize 2026 competition, with its address on Kaggle and its folder in this repository. "
       "Run outputs that are too large for git will be hosted as a Kaggle Dataset and on Hugging Face after the release checks; each folder's "
       "`outputs-manifest.csv` lists them with sha256.", "",
       "| Notebook | Version | Track | Placement | Kaggle (version) | Folder here |", "|---|---|---|---|---|---|"]
for r in sorted(runs, key=lambda r: (r["kernel"], r["version"])):
    pl = r.get("placement", {})
    where = pl.get("place", "") + (f" / {pl['group']}" if pl.get("group") else "")
    out.append(f"| `{r['kernel'].split('/')[-1]}` | v{r['version']} | {r['track']} | {where} | "
               f"[Kaggle]({r['url']}) | [`{r['_dir']}`](../{r['_dir']}/) |")
(root / "Documentation" / "LINKS.md").write_text("\n".join(out) + "\n")

# 3. Lineage
nodes = {f"{r['kernel']}@v{r['version']}": r for r in runs}
children = defaultdict(list)
roots = set()
for nid, r in nodes.items():
    par = (r.get("inferred_parent") or {}).get("notebook")
    if par in nodes:
        children[par].append(nid)
    else:
        children[par or "Our own code (no earlier notebook shares 30% of its lines)"].append(nid)
        roots.add(par or "Our own code (no earlier notebook shares 30% of its lines)")


def start(nid):
    return (nodes.get(nid, {}).get("run") or {}).get("start") or ""


def walk(nid, depth, lines):
    r = nodes.get(nid)
    if r:
        subs = ", ".join((s["public_score"] or s["status"].lower()) + (" (late)" if s.get("after_deadline") == "yes" else "")
                         for s in r.get("submissions", []))
        d = (r.get("inferred_parent") or {}).get("distance_lines")
        lines.append(f"{'  ' * depth}- [`{nid.split('/')[-1]}`](../{r['_dir']}/)"
                     f"{' · ' + str(d) + ' lines from parent' if d is not None else ''}"
                     f"{' · LB ' + subs if subs else ''}{' · ' + r['placement'].get('place', '') if r.get('placement') else ''}")
    for c in sorted(children.get(nid, []), key=start):
        walk(c, depth + 1, lines)


out = ["# Lineage", "",
       "How each of our notebook versions descends from earlier notebooks, ours and others'. The tree is **inferred from code**, not typed by hand:",
       "",
       "- **Parent:** for every version, the notebook that started running earlier and has the fewest differing code lines "
       "(`Tools/lineage/infer_parents.py`).",
       "- **Ties:** go to the earliest original, so an unchanged copy is never credited over its source.",
       "- **Diffs:** every version folder holds a cell diff against this parent (`DIFF.md`) and, where the parent is ours, "
       "against the third-party notebook at the root of its chain (`vs-root-base/DIFF.md`).",
       "",
       "**Third-party roots** are notebooks by other authors. They are cited in [`../Documentation/REFERENCES.md`](../Documentation/REFERENCES.md).", ""]
for rt in sorted(roots, key=lambda x: (x.startswith("("), x)):
    out.append(f"## {rt}")
    out.append("")
    lines = []
    for c in sorted(children[rt], key=start):
        walk(c, 0, lines)
    out += lines + [""]
(root / "ARCAID" / "LINEAGE.md").write_text("\n".join(out) + "\n")
print(len(runs), "runs indexed")
