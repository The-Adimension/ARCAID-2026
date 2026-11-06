## v4A = v3 + harness context window 32768 -> 24576 (one change)

Base: v3, LB 3.59 (2026-09-25, version 3 of habanwer/duck-nvfp4-batch-stall-warn-dead-sign). Everything in v3 is kept: arc3_batch, arc3_stall (warn), arc3_score prompt lines, budget re-fit, teardown guard, serving profile `kv5-bf16-mtp3-c8-cg32`.

**The one change.** `LOCAL_ANALYZER_CONTEXT_WINDOW` 32768 -> 24576, set right after solver setup and before the benchmark is unpickled (the first import of the harness). The harness budget is window - 1024 (v3 prompt logs: `context_budget_tokens: 31744`), so it becomes 23552. The vLLM server is untouched (`--max-model-len 32768`).

**Why.** Throughput is bound by the 5 GiB KV pool (105,202 tokens). In the v3 save run, prompts averaged 21.5K tokens, only 3.07 requests ran at a time and 2.65 waited. Shorter prompts fit more requests in the same pool, so each game gets more generated tokens inside its time budget.

**Risk.** Less history per turn can make the model repeat failed actions. v4 showed how much efficiency matters: same 19 levels as v3, but 1.41x human actions instead of 0.72x, and 16.23 instead of 25.08.

**Save run = same 6-game probe as v3/v4** (sb26, vc33, ft09, lp85, re86, ar25; 1 pass; 3600 s; concurrency 6), so the result is like-for-like. The last cells print `ARC3_EVAL` (frozen-scorer score, efficiency, vLLM running/waiting, generated tokens, against v3 and v4) and `ARC3_CTX_CHECK`. If the new window did not reach the harness, the save run raises at the end and this version should not be submitted.

**Competition rerun** is v3's: live gateway, 110 games, concurrency 28, per-game budget re-fit, plus the context change.

**Inputs to attach:** competition data; datasets `keithtyser/qwen38-flash-next-vllm-nvfp4-runtime-v1` and `keithtyser/duck-qwen38-nvfp4-mtp-vllm-smoke-v1`; model `keithtyser/qwen3-8-flash-next-nvfp4` (radixark-modelopt-fp4, v1). Accelerator RTX Pro 6000, internet off.

## Duck + NVFP4 + batch + stall warn + dead-signature ban

The policy cell installs two patches:

- `arc3_batch`: predict-then-commit. Patches both `prompts.PYTHON_ADDENDUM` and `tool_agent.PYTHON_ADDENDUM`. The built system prompt must contain `PREDICT-THEN-COMMIT`.
- `arc3_stall`: loop and grind detector with `MODE = "warn"`, plus a dead-signature ban. A stuck level adds `stuck_warning` to the action result. A signature that has already repeated until this level stopped advancing is dropped from later batches on this level. If every action left in the batch is banned, the original batch is returned unchanged. The batch is not replaced with RESET. This file does not issue RESET.

Parent public 25-game score of the warn behavior this file starts from: **3.37** (2026-09-20). This file has **no new 25-game score**. The stall print from that run was `resets_issued` 0, `resets_suppressed_invalid` 91, `warnings_shown` 91. The source string said `MODE=reset`; the valid-action gate suppressed every RESET, so the run was warn. This file says `MODE=warn`, does not issue RESET, and adds only the dead-signature ban.

Not RESET. Not ledger.

Serving stays `kv5-bf16-mtp3-c8-cg32` (prefix cache off, KV auto, 5368709120 bytes, MTP 3, max_seqs 8). `ONLY_RESET_LEVELS=true` stays. It does nothing while this policy never sends RESET.

Offline runs still integrity-check the 25 public ids, then play the 6-game depth probe (1 pass, 3600 s, concurrency 6). A 6-game mean is not a keep. A competition rerun still plays the live gateway (7920 s, concurrency 28).

The diagnostic cell still shows the 2026-09-20 probe print (`ARC3_RESET_RESULT`, mode reset, 0 RESET issued). That print is the record of that run.

### 2026-09-25 changes (score + budget fit)

- Prompt: adds the RHAE scoring rule (level score `(h/a)^2`, level weight = level index, uncleared = 0, RESET counts), a time line (points at `time_remaining_seconds` if the harness reports it, otherwise states the per-game budget), and a grid click-target line (only if the harness uses `current_frame` and `row`/`col`). Marker: `SCORING (how this run is graded)`.
- Budget: competition per-game budget 7920 s to 7750 s, then re-fitted before `bm.run` so all 4 waves (110 games at concurrency 28) finish before the soft end. Concurrency stays 28.
- Stall: ban behaviour unchanged. Adds observe-only counters `calls_single_action` and `calls_fully_banned_passthrough` to explain `actions_dropped` 0.
- Teardown: a teardown command that hangs past its 30 s timeout no longer raises.
- Serving profile unchanged (`kv5-bf16-mtp3-c8-cg32`).
