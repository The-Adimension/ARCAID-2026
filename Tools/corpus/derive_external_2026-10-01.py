"""public_demo kernel rows for external_submission/ (other teams' public Kaggle kernels).

One row per external_submission/*/__notebook__.ipynb. Reads the notebook and the
names of the files under outputs/. Opens no other file, replays nothing, and
does not touch the existing rows-*.jsonl files.

- row_role: "replayer_test" if outputs/ holds a trace, else "notebook".
  A trace is a per-game step file matched by name (TRACE_GLOBS). One sample of
  each pattern was opened and holds per-step frames/actions; the rest are
  matched by name only.
- public_score: only where the notebook text states a public leaderboard score
  for that notebook (STATED_SCORES, read by hand from the notebook cells and
  checked here against the cell text). The teambest-{score} part of the folder
  name is the team's best score, not this notebook's, and is never used.
- heldout_evidence and training_target are always False.

Run from the repo root:
    python corpus/derive_external_2026-10-01.py
writes corpus/rows-2026-10-01-external.jsonl and prints a summary as JSON.
"""

from __future__ import annotations

import glob
import json
import os
import re

ROOT = "external_submission"
OUT = "corpus/rows-2026-10-01-external.jsonl"
FOLDER = re.compile(r"^\d{4}-\d{2}-\d{2}__(?P<owner>[^/]+?)__(?P<slug>[^/]+?)__v(?P<version>\d+)__teambest-[0-9.]+$")
TRACE_GLOBS = ("**/*_events.jsonl", "**/*.recording.jsonl", "**/games/*/log.jsonl")

# folder -> (public_score, cell index, exact substring of that cell). A folder
# whose statement is text copied from another notebook names that folder.
STATED_SCORES = {
    "2026-06-30__mbmmurad__arc-agi-3-lb-0-86-3rd-place-candidate-milestone__v56__teambest-6.25": (
        0.86, 0, "This is the notebook I used as my ARC-AGI-3 milestone candidate. It reached 0.86 on the public leaderboard", None),
    "2026-08-01__sushanthtiruvaipati__arc3-duck-lb117-fork__v5__teambest-4.23": (
        0.86, 0, "This is the notebook I used as my ARC-AGI-3 milestone candidate. It reached 0.86 on the public leaderboard",
        "2026-06-30__mbmmurad__arc-agi-3-lb-0-86-3rd-place-candidate-milestone__v56__teambest-6.25"),
    "2026-08-09__tanakaai24__arc3-qwen3-6-duck-lb117-safety-v1__v1__teambest-26.11": (
        1.17, 0, "The public LB-1.17 AGI-8/AGI-9 rerun is preserved.", None),
    "2026-08-13__sushanthtiruvaipati__arc3-taaf-qwen3-v2-no-patches__v8__teambest-4.23": (
        1.17, 0, "The public LB-1.17 AGI-8/AGI-9 rerun is preserved.",
        "2026-08-09__tanakaai24__arc3-qwen3-6-duck-lb117-safety-v1__v1__teambest-26.11"),
}


def cell_text(nb: dict, i: int) -> str:
    return "".join(nb["cells"][i]["source"])


def main() -> None:
    rows = []
    for nb_path in sorted(glob.glob(f"{ROOT}/*/__notebook__.ipynb")):
        folder = nb_path.split("/")[1]
        m = FOLDER.match(folder)
        if not m:
            raise SystemExit(f"unparsed folder name: {folder}")
        owner, slug, version = m["owner"], m["slug"], m["version"]
        nb = json.load(open(nb_path))
        out_dir = os.path.join(ROOT, folder, "outputs")
        trace = sorted({p for g in TRACE_GLOBS for p in glob.glob(os.path.join(out_dir, g), recursive=True)})
        role = "replayer_test" if trace else "notebook"

        score, quote, copied_from = None, None, None
        if folder in STATED_SCORES:
            score, cell, quote, copied_from = STATED_SCORES[folder]
            if quote not in cell_text(nb, cell):
                raise SystemExit(f"stated-score quote not found in {nb_path} cell {cell}")
            if copied_from:
                src = json.load(open(f"{ROOT}/{copied_from}/__notebook__.ipynb"))
                if quote not in cell_text(src, cell):
                    raise SystemExit(f"copied quote not found in {copied_from}")
            quote = {"cell": cell, "text": quote}

        n = len(rows) + 1
        assertion = (
            f"External public kernel {owner}/{slug} v{version} stored at {nb_path}. "
            + (f"Has a trace in outputs/ ({len(trace)} files): replayer test." if trace
               else "No trace in outputs/: notebook row.")
            + (f" The file states public score {score} (cell {quote['cell']})." if score is not None
               else " The file states no public score for this notebook.")
            + (f" That text is copied from {copied_from}." if copied_from else "")
            + " Not held-out evidence, not a training target."
        )
        rows.append({
            "id": f"PD-E{n:03d}",
            "family": "external_kernel",
            "kind": "public_demo",
            "source": "repo_file",
            "path": nb_path,
            "assertion": assertion,
            "split": "public_demo",
            "links": [],
            "revoke_if": None,
            "kernel_ref": f"{owner}/{slug}",
            "kernel_version": int(version),
            "metadata_path": os.path.join(ROOT, folder, "submission.json"),
            "row_role": role,
            "trace_paths": trace,
            "public_score": score,
            "public_score_quote": quote,
            "public_score_copied_from": copied_from,
            "heldout_evidence": False,
            "training_target": False,
        })

    missing = set(STATED_SCORES) - {r["path"].split("/")[1] for r in rows}
    if missing:
        raise SystemExit(f"STATED_SCORES folders not found: {missing}")
    with open(OUT, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps({
        "rows": len(rows),
        "replayer_test": sum(r["row_role"] == "replayer_test" for r in rows),
        "notebook": sum(r["row_role"] == "notebook" for r in rows),
        "trace_files": sum(len(r["trace_paths"]) for r in rows),
        "public_score_stated": sum(r["public_score"] is not None for r in rows),
    }, indent=1))


if __name__ == "__main__":
    main()
