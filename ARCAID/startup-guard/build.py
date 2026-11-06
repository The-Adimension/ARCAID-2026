"""Build startup-guard (SG) versions of the notebooks that scored 0.00 on Oct 21-25.

Usage (from the repo root):  python kaggle/startup_guard/build.py
Pulls each base notebook from the Kaggle API at the exact scriptVersionId that was submitted, then
adds three cells and changes one number; every other cell is kept unchanged and in order:
  - a markdown note and the startup-guard cell, just above "## 9. Run the benchmark";
  - a counter cell at the very end;
  - in "9. Run the benchmark": the Kaggle-gateway wait goes from 600 s to 1800 s.
"""
import copy, hashlib, json, pathlib, re
from kaggle.api.kaggle_api_extended import KaggleApi
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest, ApiDownloadKernelOutputRequest
from requests.exceptions import HTTPError

HERE = pathlib.Path(__file__).parent; ROOT = HERE.parents[1]
OWNER = 'habanwer'
CELL = (HERE / 'startup_guard_cell.py').read_text()
STATS = ("# Startup guard: final counters (released_by, ready_after_s, keepalive_resets; never raises)\n"
         "print('ARC3_SG_FINAL', globals().get('SG_STATS'), flush=True)\n")
NOTE = ("## ARCAID3 startup guard (one added code cell)\n\n"
        "Base: **{base}**, all original cells unchanged and in order, except the Kaggle-gateway wait in "
        "*9. Run the benchmark* (600 s -> 1800 s).\n"
        "- **Why:** since Oct 20 the model load on Kaggle takes 35-65 min instead of ~10. The stock notebook gives up on "
        "the server at ~27 min and the scorecard closes after 15 min with no action, so the rerun ends COMPLETE with 0.00 "
        "(Kaggle discussion 751598).\n"
        "- **The added cell:** each game waits for the model server's `/health` before its first analyzer call; while games "
        "wait, one of them sends a RESET every 7 min (one per game, fewest first) so the scorecard stays open. The hold ends "
        "when the server is healthy, when it exits, or 2 h after notebook start.\n"
        "- **Kill switch:** `SG=0`. Knobs: `SG_KEEPALIVE_S` (420), `SG_HOLD_MAX_S` (7200).\n\n"
        "Source: `kaggle/startup_guard/` in the HabAnwer ARCAID3 repository.\n")
GATEWAY_OLD = 'def _wait_for_gateway(base_url: str, timeout_s: float = 600.0) -> None:'
GATEWAY_NEW = 'def _wait_for_gateway(base_url: str, timeout_s: float = 1800.0) -> None:'

TARGETS = [  # (kernel slug, submitted scriptVersionId, why)
    ('arcaid3-probe-first-dfranzen-m2', 361509356, 'COMPLETE 0.00 on 2026-10-25 (57619917)'),
    ('arcaid3-lexicon-dprime-dfranzen-m2', 360147562,
     'byte-identical version scored 21.18 on 2026-10-19, then COMPLETE 0.00 on 10-21 and 10-22 (57483523, 57510463)'),
]


def code(src): return {'cell_type': 'code', 'execution_count': None, 'metadata': {}, 'outputs': [], 'source': src.splitlines(True)}
def md(src): return {'cell_type': 'markdown', 'metadata': {}, 'source': src.splitlines(True)}
def text(cell): return ''.join(cell['source'])


def pull(c, slug, sid):
    """The notebook (and its version number) that Kaggle ran for scriptVersionId `sid`."""
    r = ApiGetKernelRequest(); r.user_name, r.kernel_slug = OWNER, slug
    meta = c.get_kernel(r).metadata
    for v in range(meta.current_version_number, 0, -1):
        q = ApiDownloadKernelOutputRequest()
        q.owner_slug, q.kernel_slug, q.version_number, q.file_path = OWNER, slug, v, '__notebook__.ipynb'
        try:
            res = c.download_kernel_output(q)
        except HTTPError:
            continue
        if int(re.search(r'/kf/(\d+)/', res.url).group(1)) == sid:
            return json.loads(res.content), v, meta
    raise SystemExit(f'{slug}: no saved version has scriptVersionId {sid}')


def build(nb, slug, v, meta, why):
    base = f'{OWNER}/{slug} version {v} (scriptVersionId {sid_of[slug]}; {why})'
    nb = copy.deepcopy(nb); cells = nb['cells']; n0 = len(cells)
    run_md = [i for i, c in enumerate(cells) if c['cell_type'] == 'markdown' and text(c).startswith('## 9. Run the benchmark')]
    assert len(run_md) == 1, f'{slug}: expected one "## 9. Run the benchmark" cell'
    run_code = [i for i, c in enumerate(cells) if c['cell_type'] == 'code' and GATEWAY_OLD in text(c)]
    assert len(run_code) == 1, f'{slug}: expected one gateway-wait cell'
    cells[run_code[0]]['source'] = text(cells[run_code[0]]).replace(GATEWAY_OLD, GATEWAY_NEW).splitlines(True)
    at = run_md[0]
    cells[at:at] = [md(NOTE.format(base=base)), code(CELL)]
    cells.append(code(STATS))
    assert len(cells) == n0 + 3

    new_slug = f'{slug}-sg'
    out = ROOT / 'notebooks' / f'2026-10-25__{slug}-v{v}__plus-startup-guard__kaggle-{OWNER}-{new_slug}'
    out.mkdir(parents=True, exist_ok=True)
    km = {'id': f'{OWNER}/{new_slug}', 'title': new_slug, 'code_file': f'{new_slug}.ipynb', 'language': 'python',
          'kernel_type': 'notebook', 'is_private': True, 'enable_gpu': True, 'enable_tpu': False, 'enable_internet': False,
          'keywords': ['gpu'], 'dataset_sources': ['dfranzen/pennyroyal-v253', 'dfranzen/taaf-kaggle-source-bundle-copy'],
          'kernel_sources': [], 'competition_sources': ['arc-prize-2026-arc-agi-3'],
          'model_sources': ['dfranzen/albucino-qwen3-8-flash-next-drafter/Transformers/default/1',
                            'dfranzen/intel-qwen3.8-flash-next-w4a16-autoround/Transformers/default/1'],
          'docker_image': 'gcr.io/kaggle-private-byod/python@sha256:57e612b484cf3df5026ee4dcc3cb176974b22b2bc0937fb1e16132a8be4cb13c',
          'machine_shape': 'NvidiaRtxPro6000'}
    json.dump(nb, open(out / km['code_file'], 'w'), indent=1)
    json.dump(km, open(out / 'kernel-metadata.json', 'w'), indent=2)
    h = hashlib.sha256((out / km['code_file']).read_bytes()).hexdigest()[:12]
    print(f'{out.name}: {len(cells)} cells (guard at {at}-{at + 1}, stats at end), sha256 {h}')


sid_of = {slug: sid for slug, sid, _ in TARGETS}
api = KaggleApi(); api.authenticate()
with api.build_kaggle_client() as k:
    c = k.kernels.kernels_api_client
    for slug, sid, why in TARGETS:
        nb, v, meta = pull(c, slug, sid)
        build(nb, slug, v, meta, why)
