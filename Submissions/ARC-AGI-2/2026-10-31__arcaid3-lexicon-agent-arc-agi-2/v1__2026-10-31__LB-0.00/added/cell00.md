# ARCAID3 lexicon agent for ARC-AGI-2

**What this is.** The REPL program-synthesis agent of [madarshbb/arc-qwen-3-8-27b-agent](https://www.kaggle.com/code/madarshbb/arc-qwen-3-8-27b-agent) (modelled on Tufa Labs' Duck harness: `python` to explore, `submit` to verify a `transform` on every example), carried over with the pieces of my ARC-AGI-3 work ([arcaid3-lexicon-view-dfranzen-m2](https://www.kaggle.com/code/habanwer/arcaid3-lexicon-view-dfranzen-m2), ARC-AGI-3 LB 31.90) that make sense on static grids. Model and serving are unchanged: Qwen3.8-27B FP8 on vLLM, tensor-parallel over the 4 L4s.

| From ARC-AGI-3 | Here |
|---|---|
| `current_frame.code` / `.objects` (objects with stable picture names, legend, rotation/mirror families) | `lexicon(g)`, `lex_objects(g)`: one name per picture across the whole task |
| `.changes_since(previous_frame)` | `changes(i)`: train[i] input -> output as objects that moved / became / appeared / disappeared, cell colour transitions, or how a resized output sits in its input |
| `.rules` | `rules()`: facts that hold on every train pair (size relation, geometry, colour map, which cells change, object bookkeeping, symmetry) |
| first-turn cue | the first prompt names the lexicon and carries `rules()` as measured by the harness |
| restart.patch (stuck level restarts at 100K tokens; 4/10 vs 19.6% control) | an unverified attempt restarts from a fresh context at half its token cap; its programs stay candidates |
| startup guard + precache (35-65 min model loads since Oct 20) | the model files are read into the page cache during the wheel install; the first server option set waits up to 1 h, the ladder gives up at 2 h |

Plus a **hybrid** budget: the REPL agent gets 75% of the time; the tasks it leaves unverified then get one direct answer at `reasoning_effort` xhigh. Per test input: verified programs first, then the direct answer, then the best unverified programs.

**Save run.** Only writes the fallback submission (each test input as both attempts); the agent runs in the competition rerun only, which does not bill GPU quota. `ARCAID3_LEXICON=0` turns the lexicon off.

**Not yet measured.** No scored run of this version exists. The lexicon was checked on all 120 evaluation tasks (no crash, about 15 ms a task, `rules()` under 600 characters) and the whole harness was run end to end on CPU against a scripted server; whether the model uses it well on ARC-AGI-2 is what the first submission tests.

Credits: madarshbb (agent, Apache-2.0), Tufa Labs (Duck harness), Daniel Franzen (ARC-AGI-3 Milestone 2 fork ideas), foysalemonshanto (FP8 repack), keithtyser / mirzamilanfarabi (serving wheels). Third-party code and weights keep their licences.

Config:
```
{
 "model_glob": "/kaggle/input/**/qwen3-8-27b-fp8-repacked-v1/**/config.json",
 "overlay": "/kaggle/input/**/taaf-duck-qwen38-serving-v1/serving_wheels/*.whl",
 "parsers": [
  "--tool-call-parser",
  "qwen3_coder",
  "--reasoning-parser",
  "qwen3"
 ],
 "server_ladder": [
  [
   "--reasoning-config",
   "{\"reasoning_start_str\": \"<think>\", \"reasoning_end_str\": \"</think>\"}",
   "--kv-cache-dtype",
   "fp8",
   "--language-model-only",
   "--speculative-config",
   "{\"method\": \"qwen3_5_mtp\", \"num_speculative_tokens\": 2}"
  ],
  [
   "--reasoning-config",
   "{\"reasoning_start_str\": \"<think>\", \"reasoning_end_str\": \"</think>\"}",
   "--kv-cache-dtype",
   "fp8",
   "--speculative-config",
   "{\"method\": \"qwen3_5_mtp\", \"num_speculative_tokens\": 2}"
  ],
  [
   "--reasoning-config",
   "{\"reasoning_start_str\": \"<think>\", \"reasoning_end_str\": \"</think>\"}",
   "--kv-cache-dtype",
   "fp8"
  ],
  [
   "--reasoning-config",
   "{\"reasoning_start_str\": \"<think>\", \"reasoning_end_str\": \"</think>\"}"
  ],
  []
 ],
 "max_model_len": 81920,
 "max_num_seqs": 16,
 "first_server_wait_s": 3600,
 "server_wait_s": 1500,
 "server_hold_max_s": 7200,
 "precache_threads": 4,
 "mode": "repl",
 "attempts": 1,
 "concurrency": 16,
 "max_turns": 40,
 "context_budget": 28000,
 "nudge_every": 6,
 "turn_max_tokens": 16384,
 "thinking_token_budget": 12288,
 "template_kwargs": {
  "reasoning_effort": "high"
 },
 "effort_ladder": [
  "medium",
  "low"
 ],
 "retain_functions": true,
 "trim_drain": 4000,
 "keep_recent": 6,
 "degenerate_guard": true,
 "timeout_as_cut": true,
 "lexicon_cue": true,
 "digest": true,
 "restart_frac": 0.5,
 "max_restarts": 1,
 "repl_share": 0.75,
 "direct_first": true,
 "direct_concurrency": 10,
 "direct_max_tokens": 32768,
 "direct_thinking_token_budget": 28672,
 "direct_template_kwargs": {
  "reasoning_effort": "xhigh"
 },
 "rescue_tokens": 8192,
 "min_start_s": 900,
 "temperature": 1.0,
 "top_p": 0.95,
 "top_k": 20,
 "max_tokens": 16384,
 "tok_per_s": 140,
 "min_cap": 15000,
 "max_cap": 60000
}
```
