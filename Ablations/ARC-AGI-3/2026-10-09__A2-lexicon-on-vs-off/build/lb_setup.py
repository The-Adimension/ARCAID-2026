"""Evaluation notebooks in a leaderboard-like setup: the lexicon notebook against itself with the lexicon off.

Why. The save runs so far (10 of the 25 public games, 10 at a time, 25 min each) differ from the leaderboard
run, where the notebook's submission branch plays about 110 games at once, each for up to 532 min, under its
priority scheduler. The save-run branch already carries the scaling that keeps a game's share of the GPU
equal to the leaderboard's (`532*60 * concurrency // 110`), commented out in favour of 25 min. Here it is
switched on, with all 25 public games at once: 7,254 s (121 min) per game, priority scheduling on.

Two arms, run side by side in the two GPU sessions, so they share the day and conditions:
  arcaid3-lb-lex-r<N>   the current lexicon notebook (as built by build.py), unchanged except the setup
  arcaid3-lb-off-r<N>   the same notebook with ARCAID3_LEXICON=0: nothing installed, dfranzen's stock harness

  python kaggle/lexicon-dfranzen/lb_setup.py [round ...]     # writes notebooks/lb-setup/<slug>/
  kaggle kernels push -p notebooks/lb-setup/<slug>
"""
import copy
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / "notebooks/2026-10-05__dfranzen-M2-LB27.89__plus-lexicon-view__kaggle-habanwer-arcaid3-lexicon-view-dfranzen-m2"
OUT = ROOT / "notebooks/lb-setup"
SETUP_EDITS = [
    ("demo_excluded_games = [] if TRUE_SUBMISSION else ['bp35', 'cd82', 'cn04', 'dc22', 'g50t', 'ka59', 'lf52', "
     "'ls20', 'm0r0', 's5i5', 'sk48', 'sp80', 'su15', 'tn36', 'wa30']",
     "demo_excluded_games = []  # ARCAID3 leaderboard-like evaluation: all 25 public games at once"),
    ("        bm.solver.max_runtime_s_per_game = 25*60 #532*60 * bm.solver.concurrency // 110",
     "        bm.solver.max_runtime_s_per_game = 532*60 * bm.solver.concurrency // 110  # ARCAID3: the leaderboard's GPU share per game"),
]
OFF_CELL = ("# ARCAID3 evaluation control arm: the lexicon view is switched off, so the next cells install nothing\n"
            "# and the harness runs as dfranzen's notebook does.\n"
            "import os\n"
            "os.environ['ARCAID3_LEXICON'] = '0'\n")


def code(src):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": src.splitlines(keepends=True)}


def main():
    rounds = [int(a) for a in sys.argv[1:]] or [1]
    meta0 = json.loads((SRC / "kernel-metadata.json").read_text())
    nb0 = json.loads((SRC / meta0["code_file"]).read_text())
    for r in rounds:
        for arm in ("lex", "off"):
            nb = copy.deepcopy(nb0)
            cells = nb["cells"]
            for old, new in SETUP_EDITS:
                hits = [c for c in cells if c["cell_type"] == "code" and old in "".join(c["source"])]
                assert len(hits) == 1, f"setup anchor found {len(hits)} times: {old[:60]}"
                hits[0]["source"] = "".join(hits[0]["source"]).replace(old, new).splitlines(keepends=True)
            if arm == "off":
                at = next(i for i, c in enumerate(cells)
                          if c["cell_type"] == "code" and "def install_arcaid3_lexicon" in "".join(c["source"]))
                cells.insert(at, code(OFF_CELL))
            slug = f"arcaid3-lb-{arm}-r{r}"
            meta = dict(meta0, id=f"habanwer/{slug}", title=slug, code_file=f"{slug}.ipynb")
            d = OUT / slug
            d.mkdir(parents=True, exist_ok=True)
            (d / meta["code_file"]).write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
            (d / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
            print(f"{slug}: {len(cells)} cells")


if __name__ == "__main__":
    main()
