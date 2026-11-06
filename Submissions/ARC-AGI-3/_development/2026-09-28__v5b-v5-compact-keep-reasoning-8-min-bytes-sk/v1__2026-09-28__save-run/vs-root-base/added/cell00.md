## v5b = v5 compact + KEEP_REASONING=8 + min-bytes skip

Live knobs: `KEEP_REASONING=8` (self-test still runs at 2), `STRIP_INSTRUCTIONS=True`, `MIN_COMPACT_BYTES=40000`. Prefix cache stays off. Submit gates require `ar25>=27.78`, preemptions<40, oom==0, history>=0.9*v3.

## v5 = v3 + arc3_compact (one change: smaller requests, same history)

Base: v3, LB 3.59 (2026-09-25, version 3 of habanwer/duck-nvfp4-batch-stall-warn-dead-sign). Everything in v3 is kept: arc3_batch, arc3_stall (warn), arc3_score prompt lines, budget re-fit, teardown guard, serving profile `kv5-bf16-mtp3-c8-cg32`, context window 32768.

**The one change.** `arc3_compact` rewrites each chat request to the local vLLM server just before it is sent (urllib3, in this process, where `bm.run` plays every game):
1. The reasoning of assistant messages older than the current turn and the newest 2 assistant messages is dropped. Their content, tool calls and tool results stay.
2. The 14 fixed instruction lines are dropped from every USER message except the newest. Executed actions, state lines, the carried world model and the grid image stay.

**Why.** Throughput is bound by the 5 GiB KV pool (105,202 tokens). This model's chat template keeps every earlier turn's reasoning (`preserve_thinking` defaults to true), and every USER turn repeats the same instructions. Rendering v3's six prompt snapshots with the model's own template and tokenizer gives 21.4K tokens on average (vLLM measured 21.5K). With arc3_compact they render to 13.2K (0.62x), with the same messages. v4A reached a similar size (15.6K) only by trimming history (23.9 -> 17.8 messages), and its score fell from 25.08 to 13.41 because the model repeated moves. v5 keeps the history depth unchanged.

**Save run = same 6-game probe as v3/v4/v4A** (sb26, vc33, ft09, lp85, re86, ar25; 1 pass; 3600 s; concurrency 6). The last cells print `ARC3_EVAL`, `ARC3_COMPACT` and `ARC3_VERDICT` against v3/v4/v4A. If the rewrite never fired, the save run raises at the end: do not submit that version.

**Competition rerun** is v3's: live gateway, 110 games, concurrency 28, per-game budget re-fit, plus the compaction.

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
- 
