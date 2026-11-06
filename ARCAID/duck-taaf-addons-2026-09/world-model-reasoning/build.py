"""Build the two Change-A notebooks + Kaggle metadata from their exact bases.

  v3 base   : submissions/2026-09-25__...__v3__score-3.59/__notebook__.ipynb (the submitted v3, LB 3.59)
  5.19 base : scottlegrand/taaf-flashnext-sheetu12b-0922 version 1 (public, Apache-2.0), pulled via the Kaggle API
Each gets a plain-language head cell (cell 0), a markdown note + the Change A code cell after the last patch
cell, and a stats cell at the end; nothing else in the notebook is changed.
"""
import copy, hashlib, json, pathlib, re, sys
HERE = pathlib.Path(__file__).parent; ROOT = HERE.parents[1]
CELL = (HERE / 'wmreason_cell.py').read_text()
STATS = ("# Change A: final counters (printed after the run; compare visible_labels vs reasoning_applied)\n"
         "print('ARC3_WMREASON_FINAL', globals().get('WMR_STATS'), flush=True)\n")
def code(src): return {'cell_type': 'code', 'execution_count': None, 'metadata': {}, 'outputs': [], 'source': src.splitlines(True)}
def md(src): return {'cell_type': 'markdown', 'metadata': {}, 'source': src.splitlines(True)}
NOTE = ("## Change A: world-model lines from the model's reasoning\n\n"
        "This notebook is **{base}** with four added cells: the plain-language head cell, this note, the Change A code cell below, and a counter cell at the end. Nothing else changed.\n"
        "- **The added cell:** after every model response, if the visible reply has no world-model labels, the harness's own parser reads the "
        "model's reasoning and writes those fields (capped at 400 characters each) into the carried world model.\n"
        "- **The last cell:** prints the counters.\n"
        "- **Kill switch:** `WMREASON=0`.\n\n"
        "Details and verification: `kaggle/changeA/README.md` in the ARC3 repo.\n")

def build(base_nb, insert_after, out_dir, meta, base_name, head, origin):
    nb = json.load(open(base_nb)); nb = copy.deepcopy(nb)
    cells = nb['cells']
    cells.insert(0, md(head))
    insert_after += 1
    cells.insert(insert_after + 1, code(CELL))
    cells.insert(insert_after + 1, md(NOTE.format(base=base_name)))
    cells.append(code(STATS))
    # Notebook-level Kaggle settings: exactly the block Kaggle saved for the working v3 run
    # (RTX Pro 6000, internet off, competition + both datasets + model, docker image). The API-pulled
    # 5.19 notebook has no such block, which made uploads fall back to no GPU / no inputs.
    nb['metadata'] = {'kaggle': copy.deepcopy(KAGGLE_BLOCK), 'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
                      'language_info': nb['metadata'].get('language_info', {'name': 'python'})}
    out_dir.mkdir(parents=True, exist_ok=True)
    # Paste-in route: the added cells as separate files, for Kaggle "Copy & Edit" of the original kernel.
    add = out_dir / 'cells_to_add'; add.mkdir(exist_ok=True)
    for old in add.glob('*'): old.unlink()
    (add / '1_TOP_markdown_cell.md').write_text(head)
    anchor = ''.join(nb['cells'][insert_after + 3]['source']).splitlines()[0].strip()   # the original cell right after the two inserted cells
    (add / '2_markdown_cell__insert_just_ABOVE_the_original_cell_headed_' .__add__(re.sub(r'[^A-Za-z0-9]+', '_', anchor).strip('_')) .__add__('.md')).write_text(NOTE.format(base=base_name))
    (add / '3_code_cell__insert_right_BELOW_cell_2.py').write_text(CELL)
    (add / '4_code_cell__append_at_the_very_END.py').write_text(STATS)
    (add / 'HOW_TO.md').write_text(HOWTO.format(kernel=origin, anchor=anchor))
    name = meta['code_file']
    json.dump(nb, open(out_dir / name, 'w'), indent=1)
    json.dump(meta, open(out_dir / 'kernel-metadata.json', 'w'), indent=2)
    h = hashlib.sha256(open(out_dir / name, 'rb').read()).hexdigest()[:12]
    print(f'{out_dir.name}: {len(cells)} cells (inserted at {insert_after + 1}-{insert_after + 2}, stats at end), sha256 {h}')

HEAD_V3 = """# Duck v3 + Change A: what differs, in plain words

| | Tufa Labs Duck (original, June) | Our v3 (public LB 3.59): the base of this notebook | **This notebook** |
|---|---|---|---|
| AI model | Qwen3.6-27B (older, slower) | Qwen3.8-Flash-Next, compressed to run much faster (NVFP4) | same as v3 |
| Games at once / memory | standard | 8 model conversations at once, long memory (32K) | same as v3 |
| How the AI moves | one or two moves, then thinks again | plans several moves and makes them in one go, checking each result | same as v3 |
| Extra instructions | none | explains scoring, time left and click aiming; warns when stuck; skips repeated moves that did nothing | same as v3 |
| Working notes | notes are wiped when it loses a life; sloppy labels are ignored | same as the original | same as v3 |
| **Change A** | none | none | **also keeps the notes the AI writes while thinking silently, not only what it says out loud** (capped at 400 characters each) |

**What was changed:** three cells were added: this one, a note plus the Change A code before *7. Run the benchmark*, and a counter printout at the end. Every other cell is exactly the submitted v3 (kernel `habanwer/duck-nvfp4-batch-stall-warn-dead-sign`, version 3).

**What to check in the log:**
- `ARC3_WMREASON_READY ... self_test=ok` near the start;
- `ARC3_WMREASON_FINAL` at the end, with `reasoning_applied > 0` and `errors == 0`.

**Status:** Change A has no measured score yet.
"""
HEAD_S = """# Sheetu12b + Change A: what differs, in plain words

| | Tufa Labs Duck (original, June) | Scott Le Grand's `taaf-flashnext-sheetu12b-0922` v1 (public LB 5.19): the base of this notebook | **This notebook** |
|---|---|---|---|
| AI model | Qwen3.6-27B (older, slower) | Qwen3.8-Flash-Next, compressed to run much faster (NVFP4) | same as the base |
| Games at once / memory | standard | 16 model conversations at once, shorter memory (16K) | same as the base |
| How the AI moves | one or two moves, then thinks again | same as the original | same as the base |
| What the AI sees | a picture of the board | a larger picture (12x), plus the in-between frames when something animates; old board pictures dropped to save memory | same as the base |
| Working notes | notes are wiped when it loses a life; sloppy labels are ignored | notes survive losing a life; looser labels accepted | same as the base |
| **Change A** | none | none | **also keeps the notes the AI writes while thinking silently, not only what it says out loud** (capped at 400 characters each) |

**Note on the base's header below:** "About this fork" says "32K context ... eight vLLM sequences", but the base's own code (cell *1. Environment and submission mode*) sets **16** sequences and a **16K** context. The table above follows the code.

**What was changed:** three cells were added: this one, a note plus the Change A code after the base's agentfix cell, and a counter printout at the end. Every other cell is exactly the base, version 1.

**Credit and licence:** Apache-2.0. Credit to Scott Le Grand, and to Tufa Labs for the Duck harness.

**What to check in the log:**
- `ARC3_WMREASON_READY ... self_test=ok` near the start;
- `ARC3_WMREASON_FINAL` at the end, with `reasoning_applied > 0` and `errors == 0`.

**Status:** Change A has no measured score yet.
"""
V3_NB = ROOT / 'submissions/2026-09-25__duck-nvfp4-batch-stall-warn-dead-sign__v3__score-3.59/__notebook__.ipynb'
KAGGLE_BLOCK = json.load(open(V3_NB))['metadata']['kaggle']
HOWTO = """# How to add Change A without changing the notebook's Kaggle setup

Recommended: start from the original on Kaggle, which keeps the GPU, internet-off, datasets and model exactly as they are.

1. **Open the original:** {kernel}.
   - For v3: open **your** kernel, go to *Edit* and make a new version; it opens with the code of your latest version. Check that the code matches the submitted **version 3**; if not, use the file menu to revert to version 3 first.
   - For the 5.19 notebook: click *Copy & Edit*.
2. **Before editing, check the right-hand panel:**
   - Accelerator: GPU RTX Pro 6000.
   - Internet: off.
   - Inputs: the competition, `keithtyser/duck-qwen38-nvfp4-mtp-vllm-smoke-v1`, `keithtyser/qwen38-flash-next-vllm-nvfp4-runtime-v1`, and the model `keithtyser/qwen3-8-flash-next-nvfp4` (PyTorch, radixark-modelopt-fp4, v1).
3. **Add four cells.** The file names say where each one goes:
   - `1_TOP_markdown_cell.md`: a new markdown cell at the very top.
   - `2_markdown_cell__...md`: a new markdown cell just **above** the original cell headed `{anchor}`.
   - `3_code_cell__...py`: a new code cell right **below** cell 2, still above `{anchor}`.
   - `4_code_cell__append_at_the_very_END.py`: a new code cell at the very end.
4. **Change nothing else**, then *Save Version*, then *Save & Run All*.
5. **Check the log:**
   - near the start: `ARC3_WMREASON_READY cap=400 self_test=ok`;
   - at the end: `ARC3_WMREASON_FINAL {{...}}`.

**Alternative:** import the whole `.ipynb` from the folder above. Its settings block is copied from Kaggle's own record of the working v3 run. Kaggle's import may still not attach inputs, so re-check step 2 after importing.
"""
COMMON = {'language': 'python', 'kernel_type': 'notebook', 'is_private': True, 'enable_gpu': True, 'enable_tpu': False,
          'enable_internet': False, 'keywords': ['gpu'],
          'dataset_sources': ['keithtyser/duck-qwen38-nvfp4-mtp-vllm-smoke-v1', 'keithtyser/qwen38-flash-next-vllm-nvfp4-runtime-v1'],
          'kernel_sources': [], 'competition_sources': ['arc-prize-2026-arc-agi-3'],
          'model_sources': ['keithtyser/qwen3-8-flash-next-nvfp4/PyTorch/radixark-modelopt-fp4/1'],
          'docker_image': 'gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461',
          'machine_shape': 'NvidiaRtxPro6000'}
v3 = ROOT / 'submissions/2026-09-25__duck-nvfp4-batch-stall-warn-dead-sign__v3__score-3.59/__notebook__.ipynb'
build(v3, 14, ROOT / 'notebooks/2026-09-27__v3-LB3.59__plus-changeA-wmreason__kaggle-habanwer-duck-v3-wmreason',
      {'id': 'habanwer/duck-v3-wmreason', 'title': 'duck-v3-wmreason', 'code_file': 'duck-v3-wmreason.ipynb', **COMMON},
      'our submitted v3 (Duck + NVFP4 + batch + stall warn + dead-sign, public LB 3.59, kernel habanwer/duck-nvfp4-batch-stall-warn-dead-sign v3)', HEAD_V3, 'your kernel `habanwer/duck-nvfp4-batch-stall-warn-dead-sign`, version 3 (the one submitted for LB 3.59)')
sheetu = pathlib.Path(sys.argv[1])
build(sheetu, 10, ROOT / 'notebooks/2026-09-27__sheetu12b-LB5.19__plus-changeA-wmreason__kaggle-habanwer-sheetu12b-wmreason',
      {'id': 'habanwer/sheetu12b-wmreason', 'title': 'sheetu12b-wmreason', 'code_file': 'sheetu12b-wmreason.ipynb', **COMMON},
      'scottlegrand/taaf-flashnext-sheetu12b-0922 version 1 (public LB 5.19, Apache-2.0 licence, all credit to Scott Le Grand and to Tufa Labs for the Duck harness)', HEAD_S, '`scottlegrand/taaf-flashnext-sheetu12b-0922` (https://www.kaggle.com/code/scottlegrand/taaf-flashnext-sheetu12b-0922)')
