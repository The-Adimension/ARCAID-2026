"""Build Submissions/ and Ablations/ from collected Kaggle runs.

  python -I build_catalogue.py RAW_DIR PARENTS_CSV BASES_DIR REPO_ROOT

RAW_DIR      written by Tools/kaggle/collect_runs.py (<slug>/v<N>/...)
PARENTS_CSV  written by Tools/lineage/infer_parents.py
BASES_DIR    written by Tools/kaggle/pull_bases.py (third-party notebooks, for the diffs)
REPO_ROOT    this repository; reads Tools/catalogue/placement.csv and Submissions/<track>/submissions.csv

For every notebook version it writes one folder:
  notebook.ipynb         the notebook as it ran, with cell outputs removed (the outputs are in log.txt
                         and in the outputs manifest); the sha256 of the original is in run.json
  log.txt                the Save & Run log: seconds since start, stream, text
  run.json               Kaggle ids and URL, inputs, run start/end and exception, submissions of this
                         version, inferred parent, sha256 of the original notebook and log
  outputs-manifest.csv   every output file: path, bytes, sha256 (the files themselves are hosted
                         outside git; see Documentation/LINKS.md)
  outputs/               the small summary outputs (summary.txt, benchmark.json, submission files)
  DIFF.md, added/, changed/   cell diff against the inferred parent (Tools/lineage/notebook_diff.py)
  vs-root-base/          the same diff against the third-party notebook at the root of its lineage
                         (the parent chain followed until a notebook by another author)
and a README.md per notebook and per track. Re-running rebuilds these folders from RAW_DIR.
"""
import csv, hashlib, json, shutil, subprocess, sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIFF = HERE.parent / "lineage" / "notebook_diff.py"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def render_log(src, dst):
    try:
        recs = json.loads(Path(src).read_text(encoding="utf-8"))
    except Exception:
        return False
    with open(dst, "w", encoding="utf-8") as f:
        for r in recs:
            t, s = r.get("time", 0.0), (r.get("stream_name") or "")[3:6]
            for line in (r.get("data") or "").splitlines():
                f.write(f"{t:9.1f} {s} | {line}\n")
    return True


def strip(src, dst):
    nb = json.loads(Path(src).read_text(encoding="utf-8"))
    for c in nb.get("cells", []):
        if c.get("cell_type") == "code":
            c["outputs"], c["execution_count"] = [], None
        c.get("metadata", {}).pop("papermill", None)
        c.get("metadata", {}).pop("execution", None)
    Path(dst).write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return nb.get("metadata", {})


def root_base(node, parents, owner="habanwer"):
    """Follow inferred parents until a notebook by another author; None if the chain ends in ours."""
    seen = set()
    while node and node not in seen:
        seen.add(node)
        if not node.startswith(owner + "/"):
            return node
        node = (parents.get(node) or {}).get("nearest_earlier")
    return None


def main():
    raw, parents_csv, bases, root = map(Path, sys.argv[1:5])
    place = {r["kernel"]: r for r in csv.DictReader(open(root / "Tools/catalogue/placement.csv"))}
    parents = {r["notebook"]: r for r in csv.DictReader(open(parents_csv))}
    subs = defaultdict(list)
    for track in ("ARC-AGI-3", "ARC-AGI-2"):
        for r in csv.DictReader(open(root / "Submissions" / track / "submissions.csv")):
            if r["kernel"] and r["script_version_id"]:
                subs[(r["kernel"].split("/")[1], r["script_version_id"])].append(r)

    versions = defaultdict(list)
    for d in sorted(raw.glob("*/v*")):
        if (d / "meta.json").exists():
            versions[d.parent.name].append(d)

    index = defaultdict(list)
    for slug, vdirs in versions.items():
        p = place.get(slug)
        if not p or p["place"] == "none":
            print("no placement:", slug); continue
        track = p["track"]
        rows = []
        for d in sorted(vdirs, key=lambda x: int(x.name[1:])):
            meta = json.loads((d / "meta.json").read_text())
            v, sid = meta["version"], meta["script_version_id"]
            pm, nbmeta = {}, {}
            if (d / "__notebook__.ipynb").exists():
                nbmeta = json.loads((d / "__notebook__.ipynb").read_text(encoding="utf-8")).get("metadata", {})
                pm = nbmeta.get("papermill") or {}
            start = (pm.get("start_time") or "")[:10]
            my_subs = subs.get((slug, str(sid)), [])
            if my_subs:
                scores = [("late-" if s["after_deadline"] == "yes" else "") + (s["public_score"] or s["status"].lower())
                          for s in my_subs]
                label = "LB-" + "_".join(scores)
                if any(s["selected"] == "yes" for s in my_subs):
                    label += "__SELECTED"
            elif not (d / "__notebook__.ipynb").exists():
                label = "no-saved-run"
            elif pm.get("exception"):
                label = "save-run-error"
            else:
                label = "save-run"
            rows.append((v, start, label, d, meta, pm, nbmeta, my_subs))
        first = min([r[1] for r in rows if r[1]] or [min((s["submitted_utc"][:10] for r in rows for s in r[7]), default="")])
        kfolder = f"{first}__{slug}"
        if p["place"] == "submissions":
            kdir = root / "Submissions" / track / kfolder
        elif p["place"] == "development":
            kdir = root / "Submissions" / track / "_development" / kfolder
        elif p["place"] == "ablations":
            kdir = root / "Ablations" / track / p["group"] / "runs" / slug
        else:
            kdir = root / "Tools" / p["group"] / slug / "runs"
        if kdir.exists():
            shutil.rmtree(kdir)
        kdir.mkdir(parents=True)
        table = []
        for v, start, label, d, meta, pm, nbmeta, my_subs in rows:
            vdir = kdir / f"v{v}__{start or 'not-run'}__{label}"
            vdir.mkdir()
            run = {"kernel": f"{meta['owner']}/{slug}", "title": meta["title"], "version": v,
                   "script_version_id": meta["script_version_id"], "url": meta["url"], "track": track,
                   "private_on_kaggle_at_collection": meta.get("private_now"),
                   "placement": {k: p[k] for k in ("place", "group", "arm", "note") if p.get(k)},
                   "inputs_now": {k: meta[k] for k in ("competition_sources", "dataset_sources", "model_sources", "kernel_sources")},
                   "inputs_as_run": (nbmeta.get("kaggle") or {}).get("dataSources"),
                   "accelerator": (nbmeta.get("kaggle") or {}).get("accelerator"),
                   "run": {"start": pm.get("start_time"), "end": pm.get("end_time"),
                           "duration_s": pm.get("duration"), "exception": pm.get("exception")},
                   "submissions": [{k: s[k] for k in ("submission_ref", "submitted_utc", "status", "public_score",
                                                        "private_score", "selected", "after_deadline")} for s in my_subs],
                   "files": meta["files"], "collected_at": meta["collected_at"]}
            if (d / "__notebook__.ipynb").exists():
                strip(d / "__notebook__.ipynb", vdir / "notebook.ipynb")
                run["notebook_sha256_original"] = sha(d / "__notebook__.ipynb")
            if (d / "__output__.json").exists() and render_log(d / "__output__.json", vdir / "log.txt"):
                run["log_sha256_original"] = sha(d / "__output__.json")
            if (d / "outputs-manifest.csv").exists():
                shutil.copy(d / "outputs-manifest.csv", vdir / "outputs-manifest.csv")
            if (d / "keep").is_dir():
                shutil.copytree(d / "keep", vdir / "outputs")
            me = f"{meta['owner']}/{slug}@v{v}"
            par = parents.get(me)
            if par and par["nearest_earlier"]:
                run["inferred_parent"] = {"notebook": par["nearest_earlier"], "distance_lines": int(par["distance"]),
                                          "runner_up": par["runner_up"],
                                          "runner_up_distance": int(par["runner_up_distance"] or -1),
                                          "method": "Tools/lineage/infer_parents.py"}
                pref, pv = par["nearest_earlier"].split("@v")
                owner, pslug = pref.split("/")
                base = (raw / pslug / f"v{pv}" / "__notebook__.ipynb") if owner == meta["owner"] \
                    else (bases / f"{owner}__{pslug}" / f"v{pv}.ipynb")
                if base.exists() and (d / "__notebook__.ipynb").exists():
                    subprocess.run([sys.executable, "-I", str(DIFF), str(base), str(d / "__notebook__.ipynb"), str(vdir),
                                    "--label", f"{meta['owner']}/{slug} v{v} against {par['nearest_earlier']}"],
                                   check=True, capture_output=True)
            rb = root_base(me, parents)
            if rb and rb != (par or {}).get("nearest_earlier") and (d / "__notebook__.ipynb").exists():
                owner, rest = rb.split("/"); pslug, pv = rest.split("@v")
                base = bases / f"{owner}__{pslug}" / f"v{pv}.ipynb"
                if base.exists():
                    subprocess.run([sys.executable, "-I", str(DIFF), str(base), str(d / "__notebook__.ipynb"),
                                    str(vdir / "vs-root-base"), "--label", f"{me} against its root base {rb}"],
                                   check=True, capture_output=True)
            if rb:
                run["root_base"] = rb
            (vdir / "run.json").write_text(json.dumps(run, indent=1, ensure_ascii=False) + "\n")
            dur = pm.get("duration")
            table.append(f"| [v{v}]({vdir.name}/) | {start or '—'} | {round(dur/60) if dur else '—'} | "
                         f"{', '.join((s['public_score'] or s['status'].lower()) + (' (selected)' if s['selected'] == 'yes' else '') + (' (late, not counted)' if s['after_deadline'] == 'yes' else '') for s in my_subs) or '—'} | "
                         f"{(run.get('inferred_parent') or {}).get('notebook', '—')} | "
                         f"[Kaggle]({meta['url']}) |")
            index[(track, p["place"], p.get("group", ""))].append((slug, v, vdir, my_subs, label))
        readme = [f"# {meta['title']}", "",
                  f"Kaggle: https://www.kaggle.com/code/{meta['owner']}/{slug} · Track: {track}"
                  + (f" · {p['note']}" if p.get("note") else ""), "",
                  "| Version | Run started | Minutes | Public score(s) | Nearest earlier notebook (inferred) | Link |",
                  "|---|---|---|---|---|---|"] + table + ["",
                  "Each version folder holds the notebook without outputs, the Save & Run log, `run.json` and the outputs manifest. "
                  "`DIFF.md` compares the version with its nearest earlier notebook, found by `Tools/lineage/infer_parents.py`."]
        (kdir / "README.md").write_text("\n".join(readme) + "\n")
        print(slug, len(rows), "->", kdir.relative_to(root))
    json.dump({f"{k[0]}|{k[1]}|{k[2]}": [[s, v, str(vd.relative_to(root)), l] for s, v, vd, _, l in val]
               for k, val in index.items()}, open(HERE / "catalogue_index.json", "w"), indent=1)


if __name__ == "__main__":
    main()
