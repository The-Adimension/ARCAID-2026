"""Evaluation notebooks for level trials: every level of the 25 public games as its own paired trial.

Why. Whole-game runs vary by about 6 points per run (two setups, 13 runs), partly because levels form a
chain: a game stuck early scores nothing later. Starting each (game, level) cold at that level
(level_trials_cell.py) turns one run into 183 trials, and two arms can be compared level by level.

Setup: 183 entries, 10 at a time (about 6.1 h of play), 20 min each, without the notebook's priority gate. A trial
that clears its level keeps playing the next one until its time is up, so the GPU load does not depend on
the outcomes. Two arms side by side in the two GPU sessions:
  arcaid3-lt-lex-r<N>   the current lexicon notebook (build.py), with level trials
  arcaid3-lt-off-r<N>   the same with ARCAID3_LEXICON=0

  python kaggle/lexicon-dfranzen/level_trials.py [round ...]     # writes notebooks/level-trials/<slug>/
  kaggle kernels push -p notebooks/level-trials/<slug>
"""
import copy
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / "notebooks/2026-10-05__dfranzen-M2-LB27.89__plus-lexicon-view__kaggle-habanwer-arcaid3-lexicon-view-dfranzen-m2"
OUT = ROOT / "notebooks/level-trials"
# One GPU's model server runs 10 requests at a time (--max-running-requests 10); round 2 put 92 trials on it
# at once and the server shut down. A fair trial holds one of the 10 streams for its whole clock.
CONCURRENCY, MINUTES = 10, 20
SETUP_EDITS = [
    # The notebook's priority gate (ARC3_MAX_ACTIVE_STREAMS=10, on with USE_PRIORITY_SCHEDULING) lets only 10
    # games hold a model stream at a time and frees a slot only when a game's context is first trimmed. With
    # 92 trials and a 60-minute clock each, most trials never got a slot in round 1 (74 of 158 later-level
    # trials took no action). Level trials therefore run without the gate: every trial in a wave plays at
    # once, on its own clock.
    ("USE_PRIORITY_SCHEDULING = True\n",
     "USE_PRIORITY_SCHEDULING = False  # ARCAID3 level trials: no priority gate, every trial plays on its own clock\n"),
    ("bm.solver.max_runtime_s_per_game = 48*60 #7920.0\n",
     f"bm.solver.max_runtime_s_per_game = {MINUTES}*60  # ARCAID3 level trials: per (game, level) entry\n"),
    ("bm.solver.concurrency = 10\n",
     f"bm.solver.concurrency = {CONCURRENCY}  # ARCAID3 level trials: one model stream per trial (server runs 10)\n"),
    ("demo_excluded_games = [] if TRUE_SUBMISSION else ['bp35', 'cd82', 'cn04', 'dc22', 'g50t', 'ka59', 'lf52', "
     "'ls20', 'm0r0', 's5i5', 'sk48', 'sp80', 'su15', 'tn36', 'wa30']",
     "demo_excluded_games = []  # ARCAID3 level trials: all 25 public games"),
    ("    bm.games = _offline_games(competition_env_files)\n",
     "    bm.games = _offline_games(competition_env_files)\n"
     "    bm.games = arcaid3_level_trials(bm.games, competition_env_files)  # ARCAID3: one entry per (game, level)\n"),
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
    trials = (HERE / "level_trials_cell.py").read_text()
    for r in rounds:
        for arm in ("lex", "off"):
            nb = copy.deepcopy(nb0)
            cells = nb["cells"]
            for old, new in SETUP_EDITS:
                hits = [c for c in cells if c["cell_type"] == "code" and old in "".join(c["source"])]
                assert len(hits) == 1, f"setup anchor found {len(hits)} times: {old[:60]}"
                hits[0]["source"] = "".join(hits[0]["source"]).replace(old, new).splitlines(keepends=True)
            run_at = next(i for i, c in enumerate(cells)
                          if c["cell_type"] == "code" and "".join(c["source"]).startswith("print('Starting benchmark...')"))
            cells.insert(run_at, code(trials))
            if arm == "off":
                at = next(i for i, c in enumerate(cells)
                          if c["cell_type"] == "code" and "def install_arcaid3_lexicon" in "".join(c["source"]))
                cells.insert(at, code(OFF_CELL))
            slug = f"arcaid3-lt-{arm}-r{r}"
            meta = dict(meta0, id=f"habanwer/{slug}", title=slug, code_file=f"{slug}.ipynb")
            d = OUT / slug
            d.mkdir(parents=True, exist_ok=True)
            (d / meta["code_file"]).write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
            (d / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
            print(f"{slug}: {len(cells)} cells")


if __name__ == "__main__":
    main()
