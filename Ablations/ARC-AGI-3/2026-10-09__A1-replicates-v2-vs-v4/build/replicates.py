"""Replicate save runs of lexicon v2 and v4: the same notebooks, byte for byte, under new kernel names.

One run per version cannot separate a change from noise (the SD of a difference between two single
10-game runs is about 10 points). Replicates can. Each replicate is the notebook exactly as it was
pushed for that version (taken from git), in its own private kernel, so a v2 and a v4 replicate
can run side by side (Kaggle allows 2 GPU sessions; one kernel runs one version at a time).
Running them in pairs (one v2, one v4 per round) puts both arms on the same day and conditions.

  python kaggle/lexicon-dfranzen/replicates.py            # writes notebooks/replicates/<slug>/
  kaggle kernels push -p notebooks/replicates/<slug>      # one per replicate
"""
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = "notebooks/2026-10-05__dfranzen-M2-LB27.89__plus-lexicon-view__kaggle-habanwer-arcaid3-lexicon-view-dfranzen-m2"
VERSIONS = {"v2": "c46578a4", "v4": "9b87fd2e"}          # the commits that were pushed as Kaggle versions 2 and 4
ROUNDS = (1, 2)
OUT = ROOT / "notebooks/replicates"


def at(commit, path):
    return subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:{path}"], check=True,
                          capture_output=True, text=True).stdout


def main():
    meta0 = json.loads(at(VERSIONS["v4"], f"{SRC}/kernel-metadata.json"))
    for r in ROUNDS:
        for v, commit in VERSIONS.items():
            slug = f"arcaid3-rep-{v}-r{r}"
            nb = at(commit, f"{SRC}/arcaid3-lexicon-view-dfranzen-m2.ipynb")
            meta = dict(meta0, id=f"habanwer/{slug}", title=slug, code_file=f"{slug}.ipynb")
            d = OUT / slug
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{slug}.ipynb").write_text(nb)
            (d / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
            print(f"{slug}: notebook from {commit} ({len(nb)} bytes)")


if __name__ == "__main__":
    main()
