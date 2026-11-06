# Analysis of `submissions/` (code and logs trusted over notebook text)

Scope: `submissions.csv`, v1 (1.37) and v3 (3.59). The team has 17 submissions on Kaggle; only these two are in the folder. LB: rank 330, score 3.59 (snapshot 2026-09-26 07:20 UTC).

## What v3 actually runs (from the code, `vllm-server-identity.json` and `taaf_setup_env.json`)

| Item | Value |
|---|---|
| Harness / model | Duck bundle `keithtyser/duck-qwen38-nvfp4-mtp-vllm-smoke-v1` + Qwen3.8-Flash-Next NVFP4 |
| Decoding | Thinking on, T=0.6, top-p 0.95, top-k 20, 32K context, image upscale **4** |
| vLLM | `--kv-cache-memory-bytes 5 GiB` (bf16 KV), `--max-num-seqs 8`, MTP 3, prefix caching **off**, 8K batched tokens |
| Competition run | 28 concurrent games, 7,750 s per game re-fitted to the time left, `analyzer_timeout` 900 |
| Save run (probe) | 6 public games, 1 pass, 3,600 s each, **concurrency 6** |
| Patches | `arc3_batch` (predict-then-commit prompt); `arc3_stall` (warn + dead-signature ban); `arc3_score` (scoring, time and click prompt lines); observe-only counters |

## What each patch did in the v3 probe (logs)

- **`arc3_batch` works mechanically.** It produced 4.63 actions per model decision (the docstring's earlier run: 2.33) at 662 generated tokens per action.
- **`arc3_stall` is effectively inert:**
  - 35 warnings were generated, but the warning text (`STUCK: …`) appears **0 times** in all 6 transcripts. It is written into `last_action_result['stuck_warning']`, which the model only sees if it prints that key. It printed the key a few times, and the value was `None` each time.
  - The ban armed 28 times but dropped only **4** actions. 1,242 of 1,262 `action()` calls were single-action calls (the predict-then-commit loop sends `action([a])`), so 325 fully-banned calls passed straight through.
  - The prompt line about `stuck_warning` did reach the model. In lp85 the model reasons about the threshold it expects ("The stuck_warning threshold is approaching").
  - Implication: any earlier A/B attributed to "warn" (for example, sb26 going 1→7 in stallrun2) was probably noise, if the warning was undelivered there too.
- **`arc3_score` click-target line contradicts the harness prompt.** The harness says the raw grid is not exposed (`current_frame` offers `.ascii` and `.segmentation`), but the line tells the model to iterate `enumerate(current_frame)`. The model never used that code; it read `.ascii` instead. The scoring and time lines are present.

## Discrepancies: notebook text and diagnostics vs code

- **The diagnostic cell's "RHAE" is completion-only:** `100·Σ(1..levels)/Σ(1..N)`, which ignores efficiency. The frozen scorer (`score.json`) gives a **25.08** mean, not 26.13. For vc33 it gives **15.15**, not 21.43. The hard-coded baselines (`DEPTH1`, `STALL2`) use the same completion-only metric, so the "WITHOUT sb26 … THE VERDICT" line does not compare RHAE.
- **The diagnostic cell header says "RESET branch"**, but the file runs in warn mode and never issues RESET.
- **The budget comment assumes about 725 s of setup;** this save run needed **935 s** before vLLM was ready. The run-time re-fit absorbs this.
- **Several vLLM settings are not what forum forks advertise:** upscale is 4, not 8, and the KV budget is 5 GiB.

## The binding constraint: compute per game on the hidden run

- **The KV cache is the cap:** 5 GiB = **105,202 tokens**, a "maximum concurrency 3.21×" at 32K. With only 6 games, vLLM ran **3–5 requests, 1–3 waiting, KV usage 75–100%**, and 17 preemptions.
- **Probe totals:**
  - 632 requests, averaging 21.5K prompt and 1.39K generated tokens each.
  - Aggregate generation **244 tok/s**.
  - MTP acceptance 61% (2.83 tokens per step).
  - Average queue time 15 s and end-to-end 33 s per request.
- **The competition run has 28 games** contending for the same ~3–5 slots. That leaves an estimated **~68K generated tokens per game** (244 × 7,750 / 28), against **~147K per game** in the probe. This is an estimate; the competition run's logs are not returned.
- **Probe score versus tokens per game.** Replaying the probe at the ~68K-token point:

  | Game | Levels cleared by ~68K tokens |
  |---|---|
  | sb26 | L1 |
  | vc33 | L1 |
  | ft09 | L3 |
  | lp85 | L3 |
  | re86 | L3 |
  | ar25 | ~L3 |

  That is a 6-game mean of roughly **14**, against **25.08** at full probe compute. On these games, doubling tokens per game roughly doubled the score. The public games are easier, so the hidden set may return less per token.
- **Cleared levels are efficient in v3.** Most cleared levels used fewer actions than the human baseline and hit the 1.15 cap. The losses come from levels never cleared, not from wasted actions.
- **That efficiency depends on v3's scoring and time prompt lines.** v4 removed them and cleared the same 19 levels at 1.41× human actions, scoring 16.23 against v3's 25.08. See `presubmissions/EVAL-v4-2026-09-26.md`.

## Candidate changes, ranked by expected lift per unit of work

1. **Raise concurrent sequences on the GPU.** The targeted checks below revised this.
   - Setting `TAAF_VLLM_KV_CACHE_DTYPE=fp8` alone fails on this build.
   - Raising `KV_CACHE_MEMORY_BYTES` has no headroom.
   - What remains:
     - (a) Lower `LOCAL_ANALYZER_CONTEXT_WINDOW`. This needs no patch but is untested.
     - (b) Backport vLLM PR #55557 into the offline runtime to get fp8 KV (1.77× pool).
   - Validate either one with a save run at **concurrency 28** (not 6) on the 25 public games, capped at 30–40 min. Pass if aggregate generation tok/s and running requests go up, with no OOM and no crash.
2. **Either deliver the stall warning or delete it.**
   - Delivering means getting the text into the model's view, since today it never lands.
   - With no delivered evidence either way, deleting the module and its prompt line is the safe simplification.
3. **Drop the click-target line.** It contradicts the harness, and the model never used it.
4. **Replace the diagnostic "RHAE"** with `score.json` numbers so decisions rest on the real metric.
5. **Keep `arc3_batch`.** It has a real mechanism effect on actions per decision.

## Targeted checks (2026-09-26, 08:46–09:30 UTC)

**1. KV cache headroom and fp8 KV for this build**
- **fp8 KV is blocked on the Kaggle build.** Its vLLM (`0.1.dev20073+g8e685d198`) rejects fp8 KV on the model's sparse-attention (QSA) path with `NotImplementedError: Qwen3.8-Flash-Next QSA requires a BF16 main KV cache`. — https://github.com/vllm-project/vllm/issues/54426
- **Upstream fixed it on 2026-09-16** (merged PR https://github.com/vllm-project/vllm/pull/55557). Results on an RTX PRO 6000:
  - KV pool 434,886 → 771,704 tokens (1.77×).
  - Prefill and decode unchanged; accuracy within bf16 noise.
  - With MTP, draft acceptance fell by about 0.1 and decode by 7–11% (measured on a different GPU, SM121).
- **Using it means backporting that PR's Triton and backend changes into the offline runtime.** No public Kaggle dataset ships a patched runtime.
- **No public notebook uses fp8 KV or a larger KV cache.** All ~40 public Flash-Next notebooks, including the 4.50 one, run the identical `kv5-bf16-mtp3-c8-cg32` profile.
- **A larger bf16 KV cache won't fit.** The v3 log shows CUDA OOM warnings at 5 GiB KV: 42 MB free during MoE autotune, and 233 MB free at 10:41. One public notebook set 46 GiB of KV and has no score.
- **Hybrid-model caveat:** fp8 KV gains shrink at short contexts, because the bf16 GDN/Mamba state pins the page size (1.00× at 1K tokens, 1.84× at 32K). — https://github.com/vllm-project/vllm/issues/55196
- **The only knob left that needs no patch:** `LOCAL_ANALYZER_CONTEXT_WINDOW` (32768). Average prompts are ~21.5K tokens. Cutting that to ~16K would fit ~6.5 concurrent requests instead of ~4.9 in the fixed 105K-token pool. Nobody has tested this publicly, and it trades away history.

**2. Hugging Face: no drop-in replacement for Flash-Next**
- **No Qwen4 release.**
- **Recent trending models don't fit this setup:**
  - Too large: MiMo-V2.6-Flash-RL (311B), DeepSeek-V4.1-Flash (763B).
  - Text-only: Xing4.0-29B-A4B (Apache 2.0; benchmarks level with Qwen3.6-35B-A3B).
  - Base-only: AliceAI-80B-A3B-Base.
  - Small: ZDTaichu5.0-9B.
- **The Flash-Next NVFP4 model card** says the checkpoint was validated on SGLang, not vLLM. It carries no KV-scale metadata, and "long agentic generations tend to run longer than BF16". — https://hf.co/RadixArk/Qwen3.8-Flash-Next-NVFP4
- **ARC-AGI-3 trace datasets now exist on the Hub** (for example `guanning/arc-agi-3-schema-traces-gpt56-xhigh` and `AgentNativeResearchLab/arc-agi3-*`). They could feed SFT for the Nov 2 final, not for Sep 30.

**3. Kaggle since the 07:20 UTC snapshot (checked 08:46 UTC)**
- The top 30 are unchanged, and the best public notebook is still 4.50.
- No Milestone 2 notebooks are published, and there are no new discussion threads.
- Movers:
  - Md Boktiar Mahbub Murad (Milestone 1 3rd place) went 3.66 → 5.05 (#51).
  - Samuel Sundararaman went 4.17 → 5.60 (#33).
- This team is now #333 at 3.59.
