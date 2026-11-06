## Duck + NVFP4 + batch + stall warn + dead-signature ban

The policy cell installs two patches:

- `arc3_batch`: predict-then-commit. Patches both `prompts.PYTHON_ADDENDUM` and `tool_agent.PYTHON_ADDENDUM`. The built system prompt must contain `PREDICT-THEN-COMMIT`.
- `arc3_stall`: loop and grind detector with `MODE = "warn"`, plus a dead-signature ban. A stuck level adds `stuck_warning` to the action result. A signature that has already repeated until this level stopped advancing is dropped from later batches on this level. If every action left in the batch is banned, the original batch is returned unchanged. The batch is not replaced with RESET. This file does not issue RESET.

Parent public 25-game score of the warn behavior this file starts from: **3.37** (2026-09-20). This file has **no new 25-game score**. The stall print from that run was `resets_issued` 0, `resets_suppressed_invalid` 91, `warnings_shown` 91. The source string said `MODE=reset`; the valid-action gate suppressed every RESET, so the run was warn. This file says `MODE=warn`, does not issue RESET, and adds only the dead-signature ban.

Not RESET. Not ledger.

Serving stays `kv5-bf16-mtp3-c8-cg32` (prefix cache off, KV auto, 5368709120 bytes, MTP 3, max_seqs 8). `ONLY_RESET_LEVELS=true` stays. It does nothing while this policy never sends RESET.

Offline runs still integrity-check the 25 public ids, then play the 6-game depth probe (1 pass, 3600 s, concurrency 6). A 6-game mean is not a keep. A competition rerun still plays the live gateway (7920 s, concurrency 28).

The diagnostic cell still shows the 2026-09-20 probe print (`ARC3_RESET_RESULT`, mode reset, 0 RESET issued). That print is the record of that run.

### 2026-09-25 changes (v4: safety fixes only, play unchanged)

- System prompt unchanged from the 2026-09-23 version (asserted in the policy cell). A scoring/time/click-hint prompt (v3) was tested on 2026-09-25 and dropped: actions per decision 6.92 to 4.63, tokens per action 277 to 662.
- Budget: competition per-game budget 7920 s to 7750 s, then re-fitted before `bm.run` so all 4 waves (110 games at concurrency 28) finish before the soft end (setup has taken 570-935 s). Concurrency stays 28.
- Stall: ban behaviour unchanged. Adds observe-only counters `calls_single_action` and `calls_fully_banned_passthrough` (v3 run: 1242 of 1262 calls were single-action; 325 banned calls passed through).
- Teardown: a teardown command that hangs past its 30 s timeout no longer raises.
- Serving profile unchanged (`kv5-bf16-mtp3-c8-cg32`).
