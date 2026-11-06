# Can Gemma 4 + EmbeddingGemma 2 make a winning ARC-AGI-3 entry? 2026-10-17

Live data was read on 2026-10-17 between 13:20 and 13:50 UTC through the Kaggle API, rendered Kaggle pages, arcprize.org and the Hugging Face Hub. Repo evidence comes from `main` and the unmerged branches `claude/gracious-thompson-6is9pp`, `claude/gifted-cray-01t97t`, `claude/vibrant-keller-ksqha6` and `claude/arc3-agi-analysis-8w8czd`. The one new measurement is reproduced by `analysis/2026-10-17-gemma/trim_regime.py` (output in `trim_regime.out`). Copies of the live sources are in `analysis/2026-10-17-gemma/sources/`. 16 days remain to the final deadline (2026-11-02 23:59 UTC); the Paper Prize closes 2026-11-08.

## Answer

- **Gemma 4 as the playing model is not a winning approach in this competition.**
  - The base model has been the dominant lever all year: every Qwen switch (3.6-27B → 3.8-27B → 3.8-Flash-Next) was "substantial" for Franzen, and 0.99 → 3.81 for rellik13.
  - Gemma 4 31B trails Qwen3.8-Flash-Next **and** Qwen3.8-27B on every benchmark both model cards report (table in §3).
  - The best Gemma-4 result on record is 0.86 (Milestone 1, JSON-action harnesses). Those entries used other harnesses, so this is weak evidence. **No one has measured Gemma 4 inside the Franzen harness.** My estimate there is 8–16 against about 26 for the Qwen base. That is an estimate, not a measurement.
- **EmbeddingGemma 2 has no measured lever yet.** It can be added on top of the Qwen base at almost no GPU cost: the text path is 270M parameters, about 0.54 GB in bf16, and runs on the CPU or in the GPU's spare 4%.
  - The only places it can act are where the score is measured to be lost: goal-finding on stuck levels, and the level history that context trims discard.
  - **New today:** 59 of 67 stuck level attempts in Franzen's 4 × 25 run went past 59,392 generated tokens on their level. Past that point the harness's post-trim context can no longer hold the level's early history. 89.7% of completed attempts finish before that point.
  - Every idea below has a cheap offline falsifier, and the repo's record says to expect most to fail.
- **Where the pair can realistically win:**
  1. **The Paper Prize** (deadline 11-08; $50K / $20K / $5K, plus a $375K pool for papers scoring above 4.5).
  2. **A licence hedge.** Gemma 4 and EmbeddingGemma 2 are Apache 2.0. Qwen3.8-Flash-Next is under the Qwen Community License 1.0, which is not OSI-approved. On 2026-10-15 Kaggle staff declined to rule on whether it is prize-eligible.
- **Your Lexicon line is a healthy draw of the Franzen base, not a separate system.**
  - Three draws of the identical v4 notebook: 27.05, 31.90, 26.83 (mean 28.6).
  - Four offline and paired tests found no effect.
  - Keep its draws as the final picks unless a bet below passes its test.

## 1. Where things stand (Kaggle public LB, CSV of 2026-10-17 13:32:52 UTC)

| # | Team | Score | Subs |
|---|---|---|---|
| 1 | Tufa Labs | 68.91 | 165 |
| 2 | Yi-Chia Chen | 67.49 | 33 |
| 3 | mtg | 50.37 | 71 |
| 4 | the last dance 🕺 | 49.85 | 84 |
| 5 | Son & Mark & Ronen | 48.92 | 81 |
| 10 | artificialagencylab.com | 41.74 | 55 |
| 23 | Lord Han Solo | 37.07 | 95 |
| 26 | Daniel Franzen | 36.86 | 97 |
| **215** | **Shehab Anwer** | **31.90** | **29** |

- **Size:** 4,411 teams.
- **Cut-points:** #20 = 37.27; #50 = 34.28; #100 = 33.21; #200 = 32.01; #500 = 30.34; #1000 = 28.11.
- **Medal lines at today's team count:**

  | Medal | Teams | Score line |
  |---|---|---|
  | Gold (top 10 + 0.2%) | 18 | 38.20 |
  | Silver (top 5%) | 220 | 31.85 |
  | Bronze (top 10%) | 441 | 30.61 |

  - Medals come from the private board, which compresses the best-of-k band of the public one (memo-2026-10-10 §3).
  - Your 31.90 sits on today's public silver line, but that is a best draw, not your mean.
- **The top two are unexplained.** No public notebook, write-up or paper accounts for 67–69. Everything public near the top is Franzen's M2 harness on Qwen3.8-Flash-Next. Franzen's own team is now at 36.86, which most likely comes from an unpublished version (`gifted-cray`: `experiments/2026-10-14__franzen-v3-check/NOTE.md`).
- **New operational rule:** "If you don't do any move for 15 minutes, the run will end with the score so far" (Jeroen Cottaar, #1, [750173](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/750173), 10-17).
  - He gives this as the cause of two 0.00 scores that a participant reported for Franzen-based builds since 10-16.
  - Any new serving stack must make its first move within 15 min of the gateway opening, or send keep-alive RESETs as he suggests.

## 2. What the Lexicon line measured (your submissions, Kaggle API)

| Date (UTC) | Build | Public LB |
|---|---|---|
| 10-05 | lexicon v2 on the old sheetu base | 4.56 |
| 10-06 | lexicon v1 on Franzen M2 | 24.95 |
| 10-08 | lexicon v4 (rules cue, perception fixes) | 27.05 |
| 10-11 | level-trials evaluation build (priority scheduling off) | 7.16 (misconfigured) |
| 10-12 | stuck-level restart v1, no lexicon | 25.76 |
| 10-14 | lexicon v4, same version as 10-08 | **31.90** |
| 10-15 | lexicon v4, same version again | 26.83 |
| 10-16 | restart pair, flag 0 (= Franzen v1 behaviour) | 26.22 |
| 10-17 | restart pair, restart on | pending |

- **The six healthy Franzen-base draws** (24.95, 27.05, 25.76, 31.90, 26.83, 26.22) have mean 27.12 and SD 2.46.
  - The three v4 draws have mean 28.59 and SD 2.87, about 1.2–1.7 standard errors above unchanged copies (25.77 ± 3.93 first-day copies; 25.88 ± 2.89 identical-path draws).
  - That gap is not separable from the base with n = 3.
- **What the Lexicon tests found, all on `gracious-thompson` and `gifted-cray`:**
  - **Level trials:** −4.9 points of clear rate (CI −10.2 to +0.4).
  - **Leaderboard-like A/B:** −0.03 over two rounds.
  - **Replicates v2 vs v4:** −0.33 (p = 0.55).
  - **Pre-registered test of the operational-lexicon proposals:** `predict(action)` was informative on only 5.7% of stuck steps. The loop-based stuck detector scored AUC 0.49.
  - **Mechanics are not the failure.** On ft09 the rules predict 97% of stuck steps exactly, and the agent is still stuck.
- **What that leaves.** The loss is in finding the goal on stuck levels. Anything Gemma-family has to work there or on memory, not on perception or mechanics.

## 3. Gemma 4 as the playing model

**What the family is** ([model card](https://huggingface.co/google/gemma-4-31B-it-assistant); [technical report arXiv 2607.02770](https://arxiv.org/abs/2607.02770)):
- **Sizes:** E2B, E4B, 12B, 26B-A4B (25.2B total, 3.8B active, MoE) and 31B dense (30.7B).
- **Context:** 128K (small models) and 256K (12B and up).
- **Features:** text and image input on all models; native function calling, system role and a thinking mode.
- **Licence:** Apache 2.0.
- **Speculative decoding:** "assistant" MTP drafters, claimed up to 3× faster.
- **Quantised checkpoints:** Google publishes QAT W4A16 compressed-tensors builds (`google/gemma-4-31B-it-qat-w4a16-ct`). It is also on Kaggle Models, and you already run it in `habanwer/gemma4-deva-*`, though that is the Gemma 4 Developer Agent competition, not ARC.

**Benchmarks both model cards report** (vendor numbers, different eval setups):

| | Gemma 4 31B | Gemma 4 26B-A4B | Qwen3.8-27B | Qwen3.8-Flash-Next |
|---|---|---|---|---|
| GPQA Diamond | 84.3 | 82.3 | 89.2 | 91.7 |
| LiveCodeBench v6 | 80.0 | 77.1 | 90.3 | 91.9 |
| HLE, no tools | 19.5 | 8.7 | 30.8 | 35.9 |
| MathVision (no code interpreter) | 85.6 | 82.4 | 90.0 | 90.6 |

Sources: [Gemma 4 model card](https://huggingface.co/google/gemma-4-31B-it-assistant) · [Qwen3.8-Flash-Next model card](https://huggingface.co/Qwen/Qwen3.8-Flash-Next).

- **In-competition evidence.** It doesn't isolate the model, because every Gemma entry used a different harness.
  - Milestone 1: Gemma-4-31B JSON-action policies (Reki, forge) scored 0.86 while Duck on Qwen3.6-27B scored 1.21.
  - Teams whose public Gemma-4 notebooks I checked score 0.08–0.80 on today's board: Scrattle 0.80, Chris Paul Walker 0.72, wakaka 0.45, xCalibrr 0.17, orangger 0.08. Whether those notebooks produced the team scores isn't visible.
  - `llkh0a/tufa-labs-duck-harness-but-gemma4` (07-05) has no attributable score.
- **Why I estimate 8–16 for 31B in the Franzen harness** (estimate):
  - Qwen3.8-27B already beats Gemma 4 31B on all four rows above.
  - On the old Duck base, 27B drew 2.13–2.23 where Flash-Next drew 3.38–4.50, about 0.5–0.65×.
  - Applying a similar ratio to the 26-point base gives roughly 10–16. I widened that to 8–16 for the porting risks below.
- **Where Gemma 4 is better** (from `config.json`):
  - **Memory:** the 31B's KV cache is small. Only 10 of its 60 layers are global, each with 4 KV heads of width 512 and shared K = V: about 20 KB per token at FP8, plus about 0.4 GB per stream for the 1,024-token sliding window.
  - **Weights:** about 18 GB at 4 bit.
  - **Headroom:** 10 streams at 128K need about 30 GB of KV, about 48 GB with the weights. The 96 GB card has room for more streams or longer context than Flash-Next, whose 4-bit weights (about 65 GB) fill most of it.
  - **The 26B-A4B:** about 5 KB per token, with 3.8B active parameters.
  - Throughput on the RTX PRO 6000 is unpublished. Tokens are near saturation on the Qwen base (+0.26 demo points per +10% tokens), so speed is unlikely to buy back the capability gap.
- **Porting work** (2–4 days, high risk with 16 days left):
  - a Gemma chat template that keeps its thinking output in history (removing retained reasoning "leads to a large regression": Franzen);
  - a tool-call parser;
  - an image-token estimate (Gemma uses 280 soft tokens per image by default, configurable 70–1,120) in place of Franzen's Qwen estimator;
  - a vLLM build for sm_120. `ko0kip/vllm-0230-offline` has run Gemma-4-31B on the RTX PRO 6000; its licence field reads "Unknown".
  - Pennyroyal SGLang is Flash-Next-specific.
  - Prefix caching with sliding-window layers must be verified on whichever server you use.
  - The 15-minute first-move rule applies.

## 4. EmbeddingGemma 2: where it can act

**What it is** ([model card](https://huggingface.co/google/embeddinggemma-2); [Kaggle Models](https://www.kaggle.com/models/google/embeddinggemma-2), Apache 2.0, released 2026-10-06):
- **Size:** 740M parameters. The 270M text path (130M transformer + 140M embedder) can be loaded alone; the vision (170M) and audio (300M) encoders are optional.
- **Output:** 768-d vectors, with Matryoshka truncation to 512, 256 or 128.
- **Inputs:** 8K context; images cost 280 tokens each by default.
- **Precision:** run in bf16 or fp32. In fp16 it returns NaNs or silently degraded vectors.

**Where it could run during the scored rerun:**
- **GPU:** SGLang's static memory fraction of 0.96 leaves about 3.8 GB. A text-only copy at about 0.54 GB fits there in principle; verify against Mamba-state and CUDA-graph headroom.
- **CPU:** the box has 48 vCPUs, but the Flash-Next PLE lookups also run on the CPU.
- **Either way, embed compact records only.** Embedding every turn of 110 games is on the order of 20M or more tokens. That is hours of CPU time, and the PLE lookups need the same CPUs.

**What the repo says about where the score is lost** (Franzen 4 × 25, `vibrant-keller`: `memo-2026-10-10.md` §4, plus today's script):
- **Efficiency is fine.** Completed levels run at a median 0.64× the human action count, and tokens are near saturation.
- **Stuck attempts take the tokens.** They take 34.6% of all generated tokens by today's count, against 36.2% in the 10-10 memo, which uses a different token total.
  - 40 of the 67 stuck attempts were on levels another pass solved.
  - Taking each game's best of the 4 passes would score 61.89 instead of 46.49.
- **New: the stuck regime is the trim regime.**
  - 59 of 67 unfinished attempts generated more than 59,392 tokens on their level, which is Franzen's retained context after a trim.
  - 89.7% of completed attempts finish below it.
  - Tokens spent past that point by unfinished attempts are 12.5% of all tokens.
  - Every game in Franzen's 10-game demo run trimmed 1–2 times in only 25 minutes, so at the leaderboard's ~7,250 s per game trims are routine.
  - Generated tokens understate context growth, so these counts are lower bounds.
- **Push text hurts; pull views are neutral.**
  - Added advice text measured negative twice (rellik13: 6.42 → 4.16 and 13.40 → 9.98).
  - The pull-style lexicon view was read in 17–19% of tool calls with no effect.
  - Anything EmbeddingGemma 2 adds should be a function the model calls, not text pushed into the prompt.
- **Counter-evidence for "lost history is the problem".** The same-day restart pair cleared all of a level's messages at 100K tokens, and conversion did not drop: 0 of 7 against 1 of 13; pooled 17.9% against 16.9%, p = 0.80. Power is low, but it does not favour memory-recovery ideas.

**Four uses, best first:**

| # | Use | Targets | Falsifier (pre-register before running) | Cost |
|---|---|---|---|---|
| E1 | **Goal-drift stuck detector → early restart.** Embed the goal statements in each turn's reasoning. Score how far the stated goal wanders across turns within a level attempt. Use the score to fire the fresh-context restart at about 40K tokens instead of 100K. | Goal-finding; the restart's measured flaw: it fired with 64–2,171 s left, and an early restart on tokens alone "cuts 41 slow successes" (10-10 memo) | AUC ≥ 0.70 for "never finishes" at 40K tokens. Same bar as test C, where the loop score got 0.49 and actions 0.575. Run a TF-IDF control too: if it matches, EmbeddingGemma adds nothing. Prior against: reasoning text predicted clearing at AUC 0.52 within one config (JEV-DATA-MAP). | 1 CPU day offline on your own 8 leaderboard-like runs' transcripts (`arcaid3-lb-*`, `-restart-*`, `-pair-*`). If it passes, 1 build day + 2 paired runs. |
| E2 | **Goal casebook.** On each level completion, store a card: the start-frame image, the lexicon's change events on the completing step (a mechanical "completion signature") and the model's last stated goal. On a stuck level, a pull function `similar_goals()` returns the 3 nearest cards from other games already completed in the same run. | Goal-finding, across the 110 hidden games played concurrently | Offline leave-one-game-out on the 4 × 25 replays (the `replay_probe.py` infrastructure exists). Top-3 hit rate on the completion signature of the 40 solvable stuck levels must beat the most-frequent-signature base rate by ≥ 10 points. Same BM25 text-only control. Prior against: the novelty rule (no two games share mechanics), and archetype or knowledge-pack prompts sat inside noise. | 2 CPU days |
| E3 | **`recall(query)` over the game's full log**, including trimmed turns | The 59 of 67 in the trim regime | Only a GPU test can show it: conversion of attempts past 59K tokens, paired. Power is low (the restart pair had 7 vs 13 events), and the restart result above points against it. | 1 build day + 2+ paired runs |
| E4 | **Relevance-selected retention at trim time:** keep the recent tail plus the top-k older blocks most similar to the current level | Same | Same as E3. Note: it costs no extra prefill, because every trim already invalidates the prefix. | Same |

## 5. The licence question

- **Rules 5.a.1.a and 5.a.3.**
  - 5.a.1.a requires an "open source system, open source model, and open source weights/parameters" per the OSI checklist.
  - 5.a.3 exempts "pretrained models with an incompatible license".
- **Kaggle staff on 2026-10-15** ([745079](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/745079)): "we cannot offer any guidance or provide interpretation on model licenses under the light of the competition rules". The ARC Prize hosts have not answered either; the companion thread is [745837](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/745837).
- **What a Gemma stack changes.** Gemma 4, EmbeddingGemma 2 and the Franzen harness code are all Apache 2.0 or compatible, so they pass the OSI checklist without the exemption. The vLLM wheel datasets still need a stated licence.
- **What the hedge is worth.**
  - Top-score cash prizes ($75K) go to the top private ranks, and a Gemma entry at an estimated 8–16 places there only if the hosts exclude nearly every team above it.
  - Kaggle medals follow the private board, not prize eligibility.
  - Selecting a Gemma draw as one of your two finals costs about 1.4–2.2 points of expected private best-of-2 (σ/√π, with σ = 2.5–3.9).

## 6. Bets, ranked by expected value per unit of work

| # | Bet | Evidence | Falsifier | Band if it works |
|---|---|---|---|---|
| 1 | **Keep the finals on the best-evidence Qwen build** (Lexicon v4 / Franzen v1 draws). Fill unused daily slots with healthy draws of it. | Six healthy draws, mean 27.1; no tested change beats it | None; it's the default | Private ≈ the copy band + best-of-2 |
| 2 | **E1: goal-drift detector → early restart** (EmbeddingGemma 2) | Targets the measured loss; the cheap test runs offline on data you own | AUC < 0.70 at 40K, or ≤ the TF-IDF control | Between the 10-10 policy model's +0.79 (restart at 100K) and +2.82 demo points (restart at 60K, crediting later levels); a selective trigger avoids most of the 41 slow successes the 60K rule cuts. Roughly +0.4 to +1.5 hidden, if demo gains scale. |
| 3 | **Paper Prize** on the Lexicon, the rule grammar and the pre-registered negative results, with E1/E2 as the EmbeddingGemma 2 component, whichever way they come out | Rubric (accuracy, universality, progress, theory, completeness, novelty); a linked Kaggle submission at any score is enough | n/a | $5K–$50K, or the pool |
| 4 | **Gemma lane: measure before believing.** G0: a Save run checking first move < 15 min, tok/s at 10 and 20 streams, and prefix reuse. G1: one leaderboard-like 25-game run beside a same-day Qwen control. G2: one submission. | None yet; it converts the 8–16 estimate into data, and gives the licence hedge and the paper an Apache-only result | G1 below 50% of the control: stop | Hidden 8–16 (estimate) |
| 5 | **E2: goal casebook** | Thin | §4 table | Unknown; prior low |

**Don't spend the remaining days on:**
- **Making Gemma 4 the final playing model:** see §3.
- **Fine-tuning Gemma 4 or Flash-Next:**
  - SFT on Qwen3.8-27B gave +2 RHAE on the public games ([748593](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/748593)).
  - Same-model cloning on Qwen3.6-27B "didn't translate" to the hidden set (742835).
  - Flash-Next SFT and RL produced nothing for two teams (748593), and no recipe meaningfully improved it in 742835.
- **Co-hosting a Gemma 4 LLM on the GPU next to Flash-Next.** Flash-Next's weights fill most of the 96 GB, and KV-pool pressure was the binding limit in rellik13's logs (91–97% full before their FP8 change).
- **Pushing retrieved text into prompts:** measured negative twice.
- **More lexicon perception or mechanics work:** see §2.

## 7. Calendar to 11-02 (and 11-08)

1. **10-18 (CPU):**
   - Pre-register E1.
   - Pull the transcripts of up to 8 leaderboard-like runs with `kaggle kernels output`: `arcaid3-lb-{lex,off}-r{1,2}`, `arcaid3-restart-dfranzen-m2{,-r2}`, `arcaid3-pair-flag0-r1b` and `arcaid3-pair-restart-r1`.
   - Extract per-turn goal statements, embed them with EmbeddingGemma 2 (bf16 or fp32), and read the AUC against the TF-IDF control.
   - In parallel, run G0 as a Save run (about 1 GPU hour).
2. **10-19:**
   - If E1 passes, build restart v3 on the 31.90 notebook: drift trigger at 40K or more, fresh context, functions and board kept, at most once per level, flag-gated. Assert the competition settings in the `TRUE_SUBMISSION` branch (the 7.16 lesson).
   - If it fails, close E1 and start E2 offline.
3. **10-20 to 10-23:**
   - E1: two same-day paired leaderboard-like runs (restart v3 vs flag 0).
   - G1: a Gemma leaderboard-like run.
   - G2: submit only if G1 ≥ 50% of the control.
4. **10-26:** entry and team-merger deadline. A merger is still the only fast route to a different true mean.
5. **10-27 to 11-01:** daily slots go to restart v3 if its paired runs pass, otherwise to the base. Queues of 6–17 h have been reported, so make the last submission by 11-01.
6. **11-02:** select the finals.
   - Default: two healthy Qwen draws (31.90 and 27.05).
   - Swap one for a Gemma draw only if the hosts rule against Qwen, or if G2 lands inside the copy band (≥ 22).
   - Never select the 7.16.
7. **11-03 to 11-08:** write the paper, linking the 31.90 notebook (or restart v3, if it was submitted).

## 8. What would change this memo

- **A Gemma 4 draw of 20 or more in the Franzen harness:** promote bet 4 and re-run the hedge arithmetic in §5.
- **E1 passes and its paired runs show a non-negative score delta:** make restart v3 the final default.
- **The hosts rule on the Qwen licence:**
  - If they rule against it, a Gemma lane becomes the only prize-eligible route for every Qwen team, including you.
  - If they rule for it, drop the hedge.
- **A top-5 team publishes:** fork it unchanged, as with Franzen's M2.

## Sources

- **Kaggle** (all read 2026-10-17):
  - leaderboard CSV, 13:32:52 UTC: `sources/arc-prize-2026-arc-agi-3-publicleaderboard-2026-10-17T13:32:52.csv`
  - your submissions via the API: `sources/own-submissions-2026-10-17.json`
  - kernel metadata via `kernels/pull` for `ko0kip/arc-agi-3-gemma-4-31b-reflection-agent`, `orangger/arc-agi-3-xcaliber-gemma-4-baseline`, `themightiestman/arc3-fox-gemma-driver`, `jingshuifu/arc3-m2-solution`, `yukailiu/arc-agi-3-champion-solution` and `leoprovorov/fable-astra-play-arc-3-handbook-harness`
  - Kaggle Models: [google/embeddinggemma-2](https://www.kaggle.com/models/google/embeddinggemma-2), [google/gemma-4](https://www.kaggle.com/models/google/gemma-4)
- **Kaggle discussion**, rendered: [745079](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/745079) (licence; staff reply 10-15), [750173](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/750173) (15-minute idle rule), [748593](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/748593) (fine-tuning Flash-Next vs 27B). Copies are in `sources/`.
- **Model cards:**
  - [Gemma 4 (MTP assistant card, full family table)](https://huggingface.co/google/gemma-4-31B-it-assistant)
  - [gemma-4-31B-it config](https://huggingface.co/google/gemma-4-31B-it/blob/main/config.json)
  - [gemma-4-26B-A4B-it config](https://huggingface.co/google/gemma-4-26B-A4B-it/blob/main/config.json)
  - [EmbeddingGemma 2](https://huggingface.co/google/embeddinggemma-2)
  - [Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next)
- **ARC Prize:** [Paper Prize](https://arcprize.org/competitions/2026/paper) (rubric, $450K, linked-submission rule) · [ARC-AGI-3 competition](https://arcprize.org/competitions/2026/arc-agi-3)
- **Papers** (public games and frontier models only; nothing here transfers to Kaggle):
  - [Memento 3, arXiv 2610.11794](https://arxiv.org/abs/2610.11794): rulebook memory, 100.0 on the public 25
  - [Kepler, arXiv 2610.00834](https://arxiv.org/abs/2610.00834): auditable world models, 100.00 with Claude Opus 5, $777.72
- **This repo:**
  - `analysis/2026-10-17-gemma/trim_regime.py` → `trim_regime.out`. Input: Franzen 4 × 25 `benchmark.json` (sha256 `ea186291…`) from `origin/claude/vibrant-keller-ksqha6:analysis/2026-10-10/data/dfranzen-m2-v3/`, plus the request logs in `external_submission/2026-09-30__dfranzen__…/outputs/`.
  - `origin/claude/gracious-thompson-6is9pp`: `kaggle/lexicon-dfranzen/README.md`, `report-2026-10-05.md`, the lexicon experiment `RESULT.md` files.
  - `origin/claude/gifted-cray-01t97t`: `memo-2026-10-12-lexicon-proposals.md`, `experiments/2026-10-12__lexicon-proposals-offline/RESULT.md`, the restart `RESULT.md` files.
  - `origin/claude/vibrant-keller-ksqha6`: `memo-2026-10-10.md`, `analysis/2026-10-12-sub-7.16/README.md`.
  - `main`: `memo-2026-09-26.md`, `report-2026-09-27.md`, `corpus/`.
