"""Build our copy of the top public Duck notebook's SERVING stack (item 5).

Source: wuliao0/duck-qwen3-8-anim-base (249 votes, byte-identical to
keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp). Its own "About this fork" states the Duck
prompts, tool-use loop, game policy and scorer are UNCHANGED from the Milestone-1 winner;
the only changes are model serving: RadixArk/Qwen3.8-Flash-Next-NVFP4 weights, BF16
compute, chunked prefill, three-token NEXTN speculative decoding, 8 vLLM sequences, CUDA
graphs, prefix caching off, plus a pinned offline vLLM runtime and a server watchdog.

That is the published ladder: 1.21 (Qwen3.6-27B) -> ~9 -> the current top band, from
serving alone. Our own harness work (arc3_tricks) is deliberately NOT installed here, so
this run measures the serving change and nothing else.

The competition path is kept byte-identical to theirs. The ONLY edit is the save run:
theirs plays all 25 public games at the full 7920 s cap (~2.5 h of RTX Pro 6000), ours
caps a save run at SMOKE_CAP_S so the first end-to-end test is affordable. The 25-game
audit and the frozen scorer still run, so the save run yields a public-25 score.
"""
import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SMOKE_CAP_S = 900.0     # save-run per-game cap; the rerun keeps their 7920
KERNEL_ID = "habanwer/arc3-duck-fp4-serving"


def main() -> None:
    src_dir = HERE / "top"
    nb = copy.deepcopy(json.loads((src_dir / "duck-qwen3-8-anim-base.ipynb").read_text(encoding="utf-8")))
    meta = json.loads((src_dir / "kernel-metadata.json").read_text(encoding="utf-8"))

    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            cell["outputs"] = []
            cell["execution_count"] = None

    nb["cells"][0]["source"] = (
        "## Our copy: Duck harness on the NVFP4 serving stack\n\n"
        "Forked from [wuliao0/duck-qwen3-8-anim-base](https://www.kaggle.com/code/wuliao0/duck-qwen3-8-anim-base), "
        "itself based on [Tufa Labs' Duck harness](https://www.kaggle.com/code/jeroencottaar/"
        "tufa-labs-duck-harness-june-30-milestone-winner) (Milestone-1 winner). Full credit to Jeroen Cottaar, "
        "Tufa Labs, and to ktyser/wuliao_0 for the NVFP4 serving work.\n\n"
        "The Duck prompts, tool-use loop, game policy and scorer are unchanged, and so is the serving profile "
        "(`kv5-bf16-mtp3-c8-cg32`: NVFP4 weights, BF16 compute, chunked prefill, 3-token NEXTN MTP, 8 vLLM "
        "sequences, CUDA graphs, prefix caching off).\n\n"
        f"**Our only change:** a save run caps each game at {SMOKE_CAP_S:.0f} s instead of 7920 s, so the first "
        "end-to-end test of this stack costs ~40 min of GPU instead of ~2.5 h. The competition rerun path is "
        "untouched and keeps the full 7920 s budget. The 25-game audit and the frozen scorer still run, so the "
        "save run ends with a public-25 `score.json` we can compare against our FP8 baseline.\n")

    # Cell 13 sets the solver budget for BOTH paths; make only the save run cheap.
    cell = "".join(nb["cells"][13]["source"])
    old = "bm.solver.max_runtime_s_per_game = 7920.0"
    assert cell.count(old) == 1, "settings cell changed upstream"
    cell = cell.replace(
        old,
        "# arc3: the rerun keeps their measured 7920 s; a save run is capped so our first\n"
        "# end-to-end test of this serving stack is affordable.\n"
        f"bm.solver.max_runtime_s_per_game = 7920.0 if TRUE_SUBMISSION else {SMOKE_CAP_S}")
    nb["cells"][13]["source"] = cell

    out = HERE / "fp4nb"
    out.mkdir(exist_ok=True)
    (out / "arc3-duck-fp4-serving.ipynb").write_text(json.dumps(nb, indent=1), encoding="utf-8")
    meta.update({"id": KERNEL_ID, "title": "arc3-duck-fp4-serving",
                 "code_file": "arc3-duck-fp4-serving.ipynb", "is_private": True, "keywords": []})
    meta.pop("id_no", None)
    (out / "kernel-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(json.dumps({k: meta[k] for k in ("id", "model_sources", "dataset_sources", "machine_shape")}, indent=1))
    for i, c in enumerate(nb["cells"]):
        if c["cell_type"] == "code":
            compile("".join(c["source"]).replace("await bm.run(", "bm.run("), f"cell{i}", "exec")
    print(f"{len(nb['cells'])} cells, all code compiles")


if __name__ == "__main__":
    main()
