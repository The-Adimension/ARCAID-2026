## Our copy: Duck harness on the NVFP4 serving stack

Forked from [wuliao0/duck-qwen3-8-anim-base](https://www.kaggle.com/code/wuliao0/duck-qwen3-8-anim-base), itself based on [Tufa Labs' Duck harness](https://www.kaggle.com/code/jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner) (Milestone-1 winner). Full credit to Jeroen Cottaar, Tufa Labs, and to ktyser/wuliao_0 for the NVFP4 serving work.

The Duck prompts, tool-use loop, game policy and scorer are unchanged, and so is the serving profile (`kv5-bf16-mtp3-c8-cg32`: NVFP4 weights, BF16 compute, chunked prefill, 3-token NEXTN MTP, 8 vLLM sequences, CUDA graphs, prefix caching off).

**Our only change:** a save run caps each game at 900 s instead of 7920 s, so the first end-to-end test of this stack costs ~40 min of GPU instead of ~2.5 h. The competition rerun path is untouched and keeps the full 7920 s budget. The 25-game audit and the frozen scorer still run, so the save run ends with a public-25 `score.json` we can compare against our FP8 baseline.
