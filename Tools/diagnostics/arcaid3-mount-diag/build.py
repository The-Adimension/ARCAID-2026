"""Build arcaid3-mount-diag.ipynb (v4) and kernel-metadata.json."""
import json, pathlib

HERE = pathlib.Path(__file__).parent

MD = """# arcaid3-mount-diag v4: parallel-read and copy-to-local test

v3 (2026-10-22) measured a flat ~46 MiB/s single-stream read of the 168.8 GiB
Flash Next weights (~63 min), versus ~600 MiB/s implied by the old 4-5 min loads.
v4 checks whether that is a per-stream cap: it compares 1 stream with N parallel
streams (separate files, and ranged reads inside one file), times the gcsfuse
dataset mount, then copies the full model to local disk with the best N to see
whether "copy first, then start vLLM" brings loading back to minutes.
Results are written to `/kaggle/working/read_bench_v4.json`."""

CELL_MOUNT = r'''import os, time, subprocess
t0 = time.time()
P = "/kaggle/input/datasets/dfranzen/taaf-kaggle-source-bundle-copy"
for i in range(61):
    ok = os.path.isdir(P)
    print(f"t={time.time()-t0:5.0f}s exists={ok} input={sorted(os.listdir('/kaggle/input')) if os.path.isdir('/kaggle/input') else None}", flush=True)
    if ok:
        print(sorted(os.listdir(P)))
        break
    time.sleep(10)
for root, dirs, files in os.walk("/kaggle/input"):
    depth = root[len("/kaggle/input"):].count(os.sep)
    if depth <= 2: print(root, sorted(dirs)[:10], len(files))
    if depth >= 2: dirs[:] = []
print(subprocess.run(["bash","-lc","mount | grep kaggle/input; nvidia-smi -L; df -h /kaggle/working /tmp"], capture_output=True, text=True).stdout)'''

CELL_BENCH = (HERE / 'v4_bench.py').read_text()


def cell(kind, src):
    c = {"cell_type": kind, "metadata": {}, "source": src.splitlines(keepends=True)}
    if kind == "code":
        c.update(execution_count=None, outputs=[])
    return c


nb = {
    "cells": [cell("markdown", MD), cell("code", CELL_MOUNT), cell("code", CELL_BENCH)],
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                 "language_info": {"name": "python"}},
    "nbformat": 4, "nbformat_minor": 4,
}
(HERE / "arcaid3-mount-diag.ipynb").write_text(json.dumps(nb, indent=1))

meta = {
    "id": "habanwer/arcaid3-mount-diag",
    "title": "arcaid3-mount-diag",
    "code_file": "arcaid3-mount-diag.ipynb",
    "language": "python",
    "kernel_type": "notebook",
    "is_private": False,
    "enable_gpu": True,
    "enable_internet": False,
    "machine_shape": "NvidiaRtxPro6000",
    "dataset_sources": ["dfranzen/pennyroyal-v253", "dfranzen/taaf-kaggle-source-bundle-copy"],
    "competition_sources": ["arc-prize-2026-arc-agi-3"],
    "kernel_sources": [],
    "model_sources": ["dfranzen/albucino-qwen3-8-flash-next-drafter/Transformers/default/1",
                      "dfranzen/intel-qwen3.8-flash-next-w4a16-autoround/Transformers/default/1"],
}
(HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
