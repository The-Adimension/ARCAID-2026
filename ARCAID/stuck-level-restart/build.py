"""Build the stuck-level restart notebook on Daniel Franzen's Milestone 2 notebook, plus Kaggle metadata.

  python kaggle/restart-dfranzen/build.py [--tokens N] [--slug SLUG] ...

  base     dfranzen/arc-agi-3-milestone-2-solution version 1, the version that scored 27.89
           (external_submission/2026-09-30__dfranzen__arc-agi-3-milestone-2-solution__v1__teambest-27.89/).
           All of its cells stay, unchanged except the three anchored edits below.
  change   restart.patch, applied after Franzen's own patch: a level whose conversation has used
           ARC3_STUCK_RESTART_TOKENS generated tokens gets its history cleared once (the board, system
           prompt and retained functions stay). 0 turns it off, which is Franzen v1's behaviour.

restart.patch is v2 (2026-10-14); restart_v1.patch is what notebooks/restart/ (submitted 2026-10-12, LB 25.76) embed:
  python kaggle/restart-dfranzen/build.py --patch kaggle/restart-dfranzen/restart_v1.patch --slug arcaid3-restart-dfranzen-m2
reproduces that notebook's cells except the head note.

Edits to Franzen's cells (each anchor must match exactly once):
  setup cell (his cell 4)          apply restart.patch after his patch; set the restart flag and its log file.
  customisation cell (his cell 16) save run = the leaderboard-like setup of the 2026-10-09 lexicon A/B (all 25 public games at once,
           each with the leaderboard's GPU share, 532*60*25//110 = 7,254 s, priority scheduling on), so the
           two Franzen-code control runs from that A/B (arcaid3-lb-off-r1/-r2) compare directly.
           Submission branch: assert the competition settings, so a mis-set flag fails loudly instead of
           scoring 7 (the 2026-10-11 arcaid3-lt-lex-r3 submission).
Added cells: a head note, the restart patch (%%writefile), and a summary of restart events at the end.
"""
import argparse
import copy
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE_DIR = ROOT / "external_submission/2026-09-30__dfranzen__arc-agi-3-milestone-2-solution__v1__teambest-27.89"
PATCH = HERE / "restart.patch"
META = {
    "language": "python", "kernel_type": "notebook", "is_private": True, "enable_gpu": True, "enable_tpu": False,
    "enable_internet": False, "keywords": ["gpu"],
    "dataset_sources": ["dfranzen/pennyroyal-v253", "dfranzen/taaf-kaggle-source-bundle-copy"],
    "kernel_sources": [], "competition_sources": ["arc-prize-2026-arc-agi-3"],
    "model_sources": ["dfranzen/albucino-qwen3-8-flash-next-drafter/Transformers/default/1",
                      "dfranzen/intel-qwen3.8-flash-next-w4a16-autoround/Transformers/default/1"],
    # Franzen's Python 3.12 image; the default image is 3.13 since 10-01 and his cp312 wheels do not install there
    "docker_image": "gcr.io/kaggle-private-byod/python@sha256:57e612b484cf3df5026ee4dcc3cb176974b22b2bc0937fb1e16132a8be4cb13c",
    "machine_shape": "NvidiaRtxPro6000",
}

HEAD = """# ARCAID3: stuck-level restart on Franzen's Milestone 2 notebook

**Base:** `dfranzen/arc-agi-3-milestone-2-solution` version 1 (27.89). Every cell of it is here, in order. Two of its cells are edited, at anchors checked by `kaggle/restart-dfranzen/build.py`:
- **The setup cell** (environment and paths) applies one more patch after Franzen's (`restart.patch`) and sets `STUCK_RESTART_TOKENS`.
- **The customisation cell:** the save run plays all 25 public games at once, each with the leaderboard's GPU share (7,254 s), priority scheduling on. The submission branch asserts the competition settings.

Three cells are added: this note, the restart patch (`%%writefile`), and a summary of restart events at the end.

**The change (restart.patch v2):** when one level's conversation has used `STUCK_RESTART_TOKENS` generated tokens (100,000) without completing the level, the harness clears that level's messages once and opens a fresh turn on the current board. This also happens while the model is deliberating without acting.
- **Kept:** the system prompt, the retained functions and the board.
- **Scheduling is unchanged:** the level keeps its token count, so the priority gate treats the game as it would with the flag off.
- `STUCK_RESTART_TOKENS = 0` gives Franzen v1's behaviour.

**Evidence so far:** none that it helps. Counted the same way in both arms, attempts past 100K tokens completed 5 of 21 times with restart v1 and 9 of 46 without (p = 0.46). The v1 submission scored 25.76, at the mean of unchanged copies.

**Test:** `kaggle/restart-dfranzen/DECISION_RULE_PAIR.md`.

Licence: Franzen's notebook and patch are his; the restart patch is MIT-0.
"""


def code(src):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": src.splitlines(keepends=True)}


def md(src):
    return {"cell_type": "markdown", "metadata": {}, "source": src.splitlines(keepends=True)}


def edit(cell, old, new):
    src = "".join(cell["source"])
    assert src.count(old) == 1, f"anchor found {src.count(old)} times: {old[:70]!r}"
    cell["source"] = src.replace(old, new).splitlines(keepends=True)


def summary_cell():
    return code('''# ARCAID3: restart events of this run (never raises; the run's result does not depend on it).
import json, os
from pathlib import Path
try:
    path = Path(os.environ.get("ARC3_STUCK_RESTART_LOG", "/kaggle/working/stuck_restarts.jsonl"))
    events = [json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []
    fired = [e for e in events if e.get("event") == "restart"]
    done = [e for e in events if e.get("event") == "completed_after_restart"]
    print("ARCAID3_RESTART_FINAL", json.dumps({
        "threshold_tokens": int(os.environ.get("ARC3_STUCK_RESTART_TOKENS", "0") or 0),
        "restarts": len(fired), "completed_after_restart": len(done),
        "levels_restarted": sorted({(e["state_path"], e["level"]) for e in fired}),
    }, default=str))
    for e in events:
        print(" ", json.dumps(e, default=str))
except Exception as exc:
    print("ARCAID3_RESTART_FINAL unavailable:", repr(exc))
''')


def build(tokens, slug, out_dir, patch_path=PATCH):
    nb = json.loads((BASE_DIR / "__notebook__.ipynb").read_text())
    nb = copy.deepcopy(nb)
    cells = nb["cells"]
    assert "".join(cells[2]["source"]).startswith("%%writefile /kaggle/harness-changes.patch"), "cell 2 is not Franzen's patch"
    c4, c16 = cells[4], cells[16]

    edit(c4, "print('harness patch applied successfully')\n",
         "print('harness patch applied successfully')\n"
         "# ARCAID3: stuck-level restart, applied after Franzen's patch (kaggle/restart-dfranzen/restart.patch)\n"
         "subprocess.run([\"git\", \"apply\", \"--include=ARC3-Inference/*\", \"-v\", \"/kaggle/restart.patch\"], "
         "cwd=f\"{BUNDLE_DIR}/src\", check=True)\n"
         "_restart_src = Path(f\"{BUNDLE_DIR}/src/ARC3-Inference/inference/agent/tool_agent.py\").read_text()\n"
         "assert \"def _maybe_restart_stuck_level\" in _restart_src and \"restart_note = self._maybe_restart_stuck_level\" in _restart_src\n"
         "print('restart patch applied successfully')\n")
    edit(c4, "USE_PRIORITY_SCHEDULING = True\n",
         "USE_PRIORITY_SCHEDULING = True\n"
         f"STUCK_RESTART_TOKENS = {int(tokens)}  # ARCAID3: 0 = Franzen v1 behaviour\n")
    edit(c4, "os.environ.update({k: str(v) for k,v in setup_env.items()})",
         "os.environ.update({k: str(v) for k,v in setup_env.items()})\n"
         "# ARCAID3: stuck-level restart flag and its event log\n"
         "os.environ['ARC3_STUCK_RESTART_TOKENS'] = str(STUCK_RESTART_TOKENS)\n"
         "os.environ['ARC3_STUCK_RESTART_LOG'] = str(WORKING_DIR / 'stuck_restarts.jsonl')\n"
         "print('ARCAID3_RESTART_READY', {'tokens': STUCK_RESTART_TOKENS, 'priority': USE_PRIORITY_SCHEDULING, "
         "'true_submission': TRUE_SUBMISSION})")

    edit(c16, "demo_excluded_games = [] if TRUE_SUBMISSION else ['bp35', 'cd82', 'cn04', 'dc22', 'g50t', 'ka59', 'lf52', "
              "'ls20', 'm0r0', 's5i5', 'sk48', 'sp80', 'su15', 'tn36', 'wa30']",
         "demo_excluded_games = []  # ARCAID3 leaderboard-like save run: all 25 public games at once")
    edit(c16, "        bm.solver.max_runtime_s_per_game = 532*60\n",
         "        bm.solver.max_runtime_s_per_game = 532*60\n"
         "    # ARCAID3: fail loudly rather than score a mis-set configuration (cf. 7.16 on 2026-10-11)\n"
         "    assert USE_PRIORITY_SCHEDULING, 'submission build must run the priority scheduler'\n"
         "    assert bm.solver.concurrency == 120 and bm.solver.max_runtime_s_per_game == 532*60, "
         "(bm.solver.concurrency, bm.solver.max_runtime_s_per_game)\n"
         "    assert os.environ.get('ARC3_MAX_ACTIVE_STREAMS') == '10', os.environ.get('ARC3_MAX_ACTIVE_STREAMS')\n")
    edit(c16, "        bm.solver.max_runtime_s_per_game = 25*60 #532*60 * bm.solver.concurrency // 110",
         "        bm.solver.max_runtime_s_per_game = 532*60 * bm.solver.concurrency // 110  # ARCAID3: the leaderboard's GPU share per game")

    patch = pathlib.Path(patch_path).read_text()
    assert patch.endswith("\n")
    cells.insert(3, code("%%writefile /kaggle/restart.patch\n" + patch))
    head = HEAD.replace("100,000", f"{int(tokens):,}")
    if int(tokens) == 0:
        i, j = head.index("**The change"), head.index("**Evidence so far")
        head = head[:i] +("**This is the control arm:** `STUCK_RESTART_TOKENS = 0`. The restart code is installed but returns at its "
                           "first check, so the harness behaves as Franzen v1. It differs from the restart arm only in that flag "
                           "and this note.\n\n") + head[j:]
        head = head.replace("# ARCAID3: stuck-level restart on Franzen's Milestone 2 notebook\n",
                            "# ARCAID3: stuck-level restart on Franzen's Milestone 2 notebook (control arm: restart off)\n", 1)
    cells.insert(0, md(head))
    cells.append(summary_cell())

    meta = dict(META, id=f"habanwer/{slug}", title=slug, code_file=f"{slug}.ipynb")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / meta["code_file"]).write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
    (out_dir / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    return nb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokens", type=int, default=100_000)
    ap.add_argument("--slug", action="append", required=True)
    ap.add_argument("--patch", default=str(PATCH))
    a = ap.parse_args()
    for slug in a.slug:
        out = ROOT / "notebooks" / ("restart-pair" if slug.startswith("arcaid3-pair-") else "restart") / slug
        nb = build(a.tokens, slug, out, a.patch)
        print(f"{slug}: {len(nb['cells'])} cells -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
