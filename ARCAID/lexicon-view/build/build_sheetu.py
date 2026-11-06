"""Build the Part III notebook: the 4.17 notebook, unchanged, plus the ARCAID3 lexicon view.

Base: submissions/2026-09-30__taaf-flashnext-sheetu12b-0922__v1__score-4.17/__notebook__.ipynb
      (byte-identical in code to scottlegrand/taaf-flashnext-sheetu12b-0922 v1, Apache-2.0).
Adds four cells and changes nothing else (checked below):
  0             plain-language head cell (markdown)
  after hook    a markdown note + the lexicon-view code cell, right after the "Customization hook"
                code cell (all harness modules and agentfix are installed by then; no sandbox has run)
  end           a counter cell

Writes (version 2; version 1 stays as committed in arcaid3/part3/notebook/, and as run in
experiments/2026-10-04__arcaid3-lexicon-view-py312__v1__unsubmitted__save-run/):
  arcaid3/part3/lexicon_view_cell.py               the generated code cell (lexicon embedded)
  arcaid3/part3/notebook-v2/arcaid3-lexicon-view-v2.ipynb
  arcaid3/part3/notebook-v2/kernel-metadata.json   for `kaggle kernels push -p arcaid3/part3/notebook-v2`

Run from the repo root:  python3 arcaid3/part3/build.py
"""
from __future__ import annotations

import copy
import csv
import hashlib
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / "submissions/2026-09-30__taaf-flashnext-sheetu12b-0922__v1__score-4.17/__notebook__.ipynb"
KAGGLE_SETTINGS_FROM = ROOT / "submissions/2026-09-25__duck-nvfp4-batch-stall-warn-dead-sign__v3__score-3.59/__notebook__.ipynb"
OUT = HERE / "notebook-v2"
NAME = "arcaid3-lexicon-view-v2.ipynb"

HEAD = """# ARCAID3 lexicon view v2 on Scott Le Grand's sheetu12b (public LB 4.17 for our unchanged copy)

**What this is.** Scott Le Grand's public notebook `taaf-flashnext-sheetu12b-0922` (Apache-2.0), itself built on
Tufa Labs' Duck harness (CC0) and keithtyser's Flash-Next serving. Every original cell is kept, unchanged and in order.

**The one change.** The model already reads the board through Python (`current_frame.ascii`, `.segmentation`,
and F13's in-between animation frames). This adds one more optional way to read it:

| New in the sandbox | What it gives the model |
|---|---|
| `current_frame.code` | The board as objects: the true cell size (many games draw a 16x16 or 32x32 world scaled up to 64x64), a legend of symbols (small multi-colour pictures with stable names), and where each symbol sits |
| `current_frame.changes_since(previous_frame)` | Which objects moved (and by how much), appeared, disappeared or turned into another symbol |
| `current_frame.objects` | The same objects as data, with a screen row/col to click |
| `current_frame.native` | The board at its true resolution |

**What v2 changes in the prompt, and why.** In version 1 the model never used the view: 0 of 1,130 tool calls.
The harness's own prompt said, three times per request, that a frame exposes "only" `.ascii`, `.step`, `.level`,
`.shape` and `.segmentation`, and our one sentence gave no reason to look
(`arcaid3/part3/WHY-THE-VIEW-WAS-NOT-USED.md`). v2 therefore:
1. adds the new members to those three "only" lines (tool description and two system-prompt lines);
2. adds a "when" line next to the harness's "most recent change" line: on a new level, or when the last action's
   effect is unclear, print `current_frame.code` and `current_frame.changes_since(previous_frame)`;
3. on a game's first turn and after a level change, adds one line to the user message: start with
   `print(current_frame.code)`.

Nothing else changes: same model, serving, images, schedule. Every prompt edit is applied only if its exact anchor
text is found, and the `ARCAID3_LEXICON_READY` line reports which edits applied.

**Why this change and not another.** In this lineage the only change ever reported to move the hidden leaderboard
(F13, 3.20 -> 3.71 in the author's notes) was a perception change of this kind: more of the board, offered in the
sandbox, read only when the model asks. Our own runs lost their score on levels the model never understood, not on
clumsy play (see `arcaid3/part1/PART-I-FINDINGS.md`).

**Honest expectation.** One leaderboard draw cannot show whether this helps: identical code has scored 5.68, 4.09 and
2.30 for another team. Judge it on several draws against several draws of the unchanged base.

**Environment:** Kaggle image `sha256:37c64f7d…fade02bfa8bf3fc647d461` (Python 3.12), set as "Pin to original environment".
keithtyser's vLLM runtime stops on Python 3.13 with `The pinned vLLM runtime requires CPython 3.12`.

**Kill switch:** `ARCAID3_LEXICON=0`. **Log lines:** `ARCAID3_LEXICON_READY` near the start, `ARCAID3_LEXICON_STATS`
every 200 tool calls, `ARCAID3_LEXICON_FINAL` at the end. Success test for this save run: `calls_using_view` above
5% of `tool_calls`.

Credits: Tufa Labs (Duck), keithtyser (Flash-Next serving), Scott Le Grand (sheetu12b, agentfix, F13/F19).
"""

NOTE = """## ARCAID3 lexicon view v2 (the one added code cell)

The next cell adds `current_frame.code`, `.objects`, `.native` and `.changes_since(...)` to the Python sandbox,
corrects the harness's prompt lines that said a frame exposes "only" five fields, adds a "when to look" line, and
adds a first-turn / new-level cue to the user message. It tests itself through the real sandbox before the run and rolls back to the
stock sandbox if anything fails. Source: `arcaid3/part2/lexicon.py` (standard library only).
"""

STATS = ("# ARCAID3 lexicon view: final counters (how often the model's Python read the new view)\n"
         "print('ARCAID3_LEXICON_FINAL', globals().get('ARCAID3_STATS'), globals().get('ARCAID3_REPORT'), flush=True)\n")


def code(src, cid):
    return {"cell_type": "code", "execution_count": None, "id": cid, "metadata": {}, "outputs": [],
            "source": src.splitlines(True)}


def md(src, cid):
    return {"cell_type": "markdown", "id": cid, "metadata": {}, "source": src.splitlines(True)}


# The notebook-level Kaggle settings, as Kaggle's editor writes them. Each value was checked on 2026-10-04:
#  - competition 133468 = arc-prize-2026-arc-agi-3 (competitions API);
#  - datasetVersion 19306148 / 19333078 and modelInstanceVersion 977939 = the keithtyser inputs: the same three
#    ids appear in the saved settings of 4 other teams' notebooks with exactly these inputs, and neither dataset
#    has a version newer than 2026-08-31;
#  - dockerImageVersionId 31401 = the Python 3.12 image sha256:37c64f7d...fade02bfa8bf3fc647d461 (our v3 kernel
#    and an external notebook pair the two).
KAGGLE_BLOCK = {
    "accelerator": "nvidiaRtxPro6000",
    "dataSources": [
        {"sourceId": 133468, "sourceType": "competition"},
        {"sourceId": 19306148, "sourceType": "datasetVersion"},
        {"sourceId": 19333078, "sourceType": "datasetVersion"},
        {"sourceId": 977939, "sourceType": "modelInstanceVersion"},
    ],
    "dockerImageVersionId": 31401,
    "isGpuEnabled": False,
    "isInternetEnabled": False,
    "language": "python",
    "sourceType": "notebook",
}


def source_literal(text: str) -> str:
    """The lexicon source as a parenthesised run of one string literal per line (readable in a notebook)."""
    lines = text.splitlines(True)
    return "(\n" + "".join(f"    {line!r}\n" for line in lines) + ")"


def build_cell() -> str:
    template = (HERE / "lexicon_view_template.py").read_text()
    lexicon = (ROOT / "arcaid3/part2/lexicon.py").read_text()
    assert "\nimport " not in lexicon and "\nfrom " not in lexicon, "lexicon.py must not import anything"
    cell = template.replace("__LEXICON_SOURCE__", source_literal(lexicon), 1)
    compile(cell, "lexicon_view_cell.py", "exec")
    (HERE / "lexicon_view_cell.py").write_text(cell)
    return cell


def main() -> None:
    cell = build_cell()
    base = json.load(open(BASE))
    nb = copy.deepcopy(base)
    cells = nb["cells"]
    hook_md = next(i for i, c in enumerate(cells)
                   if c["cell_type"] == "markdown" and "".join(c["source"]).startswith("## 6. Customization hook"))
    hook_code = next(i for i in range(hook_md + 1, len(cells)) if cells[i]["cell_type"] == "code")
    cells.insert(hook_code + 1, code(cell, "arcaid3-lexicon-view"))
    cells.insert(hook_code + 1, md(NOTE, "arcaid3-note"))
    cells.insert(0, md(HEAD, "arcaid3-head"))
    cells.append(code(STATS, "arcaid3-final-counters"))

    # every original cell is still there, with unchanged source, in order
    added = {0, hook_code + 2, hook_code + 3, len(cells) - 1}
    assert "".join(cells[hook_code + 3]["source"]) == cell and "".join(cells[hook_code + 2]["source"]) == NOTE
    kept = [c for i, c in enumerate(cells) if i not in added]
    assert [(c["cell_type"], "".join(c["source"])) for c in kept] == \
        [(c["cell_type"], "".join(c["source"])) for c in base["cells"]]
    for c in cells:
        if c["cell_type"] == "code":                  # a new version starts without the base run's outputs
            c["outputs"], c["execution_count"] = [], None
        c["metadata"] = {}                            # and without the 4.17 run's papermill timings
    ids = [c.get("id") for c in cells]                # nbformat 4.5: every cell has a unique id
    assert all(ids) and len(set(ids)) == len(ids) and all(re.fullmatch(r"[A-Za-z0-9_-]{1,64}", i) for i in ids), ids

    assert json.load(open(KAGGLE_SETTINGS_FROM))["metadata"]["kaggle"] == KAGGLE_BLOCK, "settings block drifted"
    nb["nbformat"], nb["nbformat_minor"] = 4, 5
    nb["metadata"] = {"kaggle": KAGGLE_BLOCK,
                      "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                      "language_info": base["metadata"].get("language_info", {"name": "python"})}
    idx = {r["kernel"]: r for r in csv.DictReader(open(ROOT / "external_submission/index.csv"))}
    scott = idx["scottlegrand/taaf-flashnext-sheetu12b-0922"]
    # Environment: the pinned vLLM runtime needs CPython 3.12. Every working run (our 4.17, 3.90, Change A,
    # scottlegrand's original) used the image below. Naming the image alone did not pin it: v1 of
    # habanwer/arcaid3-lexicon-view was put on Kaggle's latest image (Python 3.13) and failed at vLLM setup
    # (experiments/2026-10-03__arcaid3-lexicon-view__v1__unsubmitted__error-python313). So the push also sets
    # docker_image_pinning_type, under a new slug whose "original" environment is the one named here.
    # (That worked for v1 as habanwer/arcaid3-lexicon-view-py312; v2 gets its own new slug the same way.)
    meta = {
        "id": "habanwer/arcaid3-lexicon-view-v2",
        "title": "arcaid3-lexicon-view-v2",
        "code_file": NAME,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": False,
        "keywords": ["gpu"],
        "dataset_sources": json.loads(scott["datasets"]),
        "kernel_sources": [],
        "competition_sources": ["arc-prize-2026-arc-agi-3"],
        "model_sources": json.loads(scott["models"]),
        "docker_image": scott["docker_image"],
        "docker_image_pinning_type": "original",
        "machine_shape": "NvidiaRtxPro6000",
    }
    assert meta["docker_image"].endswith("fade02bfa8bf3fc647d461"), "not the Python 3.12 image the working runs used"
    OUT.mkdir(exist_ok=True)
    # paste-in route: the four added cells as files, for Kaggle "Copy & Edit" of the original notebook
    add = OUT / "cells_to_add"
    add.mkdir(exist_ok=True)
    for old in add.glob("*"):
        old.unlink()
    anchor = "".join(base["cells"][hook_code + 1]["source"]).splitlines()[0].strip()
    (add / "1_markdown__insert_at_the_very_TOP.md").write_text(HEAD)
    (add / "2_markdown__insert_right_BELOW_the_code_cell_under_6_Customization_hook.md").write_text(NOTE)
    (add / "3_code__insert_right_BELOW_cell_2.py").write_text(cell)
    (add / "4_code__append_at_the_very_END.py").write_text(STATS)
    (add / "HOW_TO.md").write_text(
        "# Adding the ARCAID3 lexicon view by hand\n\n"
        "1. On Kaggle, open `scottlegrand/taaf-flashnext-sheetu12b-0922` and click *Copy & Edit* "
        "(this keeps its GPU, internet-off setting, datasets and model).\n"
        "2. Check the right-hand panel: accelerator RTX Pro 6000, internet off, inputs = the competition, "
        "`keithtyser/duck-qwen38-nvfp4-mtp-vllm-smoke-v1`, `keithtyser/qwen38-flash-next-vllm-nvfp4-runtime-v1`, "
        "model `keithtyser/qwen3-8-flash-next-nvfp4`. Under *Environment*, keep **Pin to original environment**: "
        "the vLLM runtime needs Python 3.12, and Kaggle's latest environment is Python 3.13.\n"
        "3. Add the four cells as their file names say. Cells 2 and 3 go after the code cell under "
        f"*6. Customization hook* and before the markdown cell headed `{anchor}`.\n"
        "4. Change nothing else. *Save Version* -> *Save & Run All*.\n"
        "5. In the log, look for `ARCAID3_LEXICON_READY` near the start and `ARCAID3_LEXICON_FINAL` at the end.\n"
        "6. If the run stops within about 3 minutes with `The pinned vLLM runtime requires CPython 3.12, found cpython "
        "3.13`, the environment is the latest one, not the original. Stop, fix the Environment setting, run again.\n")
    json.dump(nb, open(OUT / NAME, "w"), indent=1)
    json.dump(meta, open(OUT / "kernel-metadata.json", "w"), indent=2)
    h = hashlib.sha256((OUT / NAME).read_bytes()).hexdigest()[:12]
    print(f"{NAME}: {len(cells)} cells ({len(base['cells'])} original + 4), "
          f"cell inserted at {hook_code + 2}, sha256 {h}; cell {len(cell)} chars")


if __name__ == "__main__":
    main()
