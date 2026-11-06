# ARC Prize 2026 · ARC-AGI-3 (Kaggle): memo, 2026-09-26

Live numbers were fetched on 2026-09-26 at 07:20 UTC unless marked otherwise. The Kaggle leaderboard is not gated and was read live. Target: a public-LB score above 6.

## 1. What the benchmark is

- The tasks are interactive, turn-based games, not static puzzles. The agent receives frames (a grid up to 64×64, 16 colours) and sends `RESET`, `ACTION1–5`, `ACTION6(x,y)` or `ACTION7` (undo, per the docs). Goals and action meanings are never stated. Every game has several levels. — https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/data · https://docs.arcprize.org/actions
- It tests exploration, world-modelling, goal inference and planning. Agents are scored on how many levels they complete and on how efficiently they act compared with first-time humans. — https://arcprize.org/competitions/2026/arc-agi-3
- **Official score (RHAE)**, as computed by the shipped scorer:
  - `level = min((human_actions / agent_actions)², 1.15)` for a completed level, and 0 for an uncompleted one.
  - `game = Σ(i·level_i) / Σ i` over all levels, with weight = the 1-indexed level number. The game score is also capped at the weight share of the levels completed (clearing 4 of 6 levels caps the game at 10/21 = 47.6).
  - `total = mean(game)` over all games.
  - Sources: https://docs.arcprize.org/methodology · https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/728299
- Sources disagree on the per-level cap. The docs and the shipped `scorecard.py` cap it at 1.15. The Kaggle Evaluation and Data pages say 1.0. Either way, being more efficient than humans adds at most 15%.
- Every environment action counts, including a dead click that changes nothing and an in-level `RESET`. The host confirmed on 2026-07-08 that the scored server matches the toolkit on this. — https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/718638
- The human baseline is the upper-median first-time player on each level, drawn from about 500 people tested. — https://docs.arcprize.org/methodology · https://arcprize.org/blog/astra
- **Hidden set:** 110 private games. Every submission plays all 110. 55 feed the public LB and 55 the private LB. Private scores are computed at run time and never re-run. — https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/729985
- According to the host, the public LB uses the "semi-private" set. The 25 public demo games (183 levels, about 7.3 per game) were made deliberately easier. — https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/703990 · https://developer.nvidia.com/blog/nvidia-avo-reaches-100-on-arc-agi-3-demonstrating-a-frontier-level-general-purpose-architecture-for-long-horizon-autonomous-agents/

## 2. Kaggle constraints

- Submissions are notebooks only. Internet is off, runtime is capped at 9 h (540 min, CPU or GPU), and the gateway writes `submission.parquet` automatically. — https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview/code-requirements
- **Hardware:** one RTX Pro 6000 (96 GB VRAM, `g4-standard-48`), reserved for this competition. It replaced the H100 on 2026-05-07 after a stockout. In practice this means models of about 125B parameters or fewer, quantized to 4 bits. Qwen3.8-Flash-Next (125B MoE) fits as NVFP4, but fine-tuning it on this card is not feasible. — https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/697720 · https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/742835
- **Competition mode:**
  - One `make` per game: a single play, with no parallel copies of a game.
  - A game reset becomes a level reset.
  - The scorecard can't be read during play.
  - The game source files are not present in the rerun.
  - Sources: https://docs.arcprize.org/toolkit/competition_mode · https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/707925
- Kaggle has no 5×-baseline action cap; that cap applies only to the verified leaderboard. Wall-clock time is the only limit. — https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/713921
- **Submissions and deadlines:**
  - 1 submission per day. The limit was restored on 2026-06-08 after a 5-per-day error.
  - 2 final submissions may be selected, and teams can have at most 8 members.
  - Entry and team-merger deadline: 2026-10-26. Final deadline: 2026-11-02 23:59 UTC. Winners announced 2026-12-04.
  - Sources: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview/timeline · https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/705405
- **Prize eligibility:**
  - Winners license their solution under CC-BY 4.0.
  - The system, model and weights must all be open, per the OSI Open Source AI checklist.
  - Winners must deliver training and inference code, and identity verification is required.
  - External data and models must be public and pass a cost "reasonableness" test.
  - Source: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/rules
- **Milestone eligibility:** the notebook must be public under an open-source licence by 23:59 UTC on the milestone date, and ranking uses the public LB. The Duck harness is MIT (code dataset) and Apache 2.0 (notebook), so forks can qualify. Check the licence of any model checkpoint you ship. — https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/713634 · https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/717133
- **Operational risk:** RTX queues of 8–12 h were reported on 2026-09-20/21 and cleared on 2026-09-22. — https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/742148

## 3. Live standings (dated)

Kaggle public LB at 2026-09-26 07:20 UTC: 3,337 teams on the board, 15,222 joined users, 38,698 submissions. — https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/leaderboard

| # | Team | Score | Subs |
|---|---|---|---|
| 1 | Tong Hui Kang | 20.53 | 84 |
| 2 | Lord Han Solo | 19.45 | 74 |
| 3 | Tufa Labs | 18.81 | 146 |
| 4 | Yi-Chia Chen | 18.80 | 12 |
| 5 | Daniel Franzen | 16.68 | 83 |
| 6 | NVARC3 | 16.07 | 20 |
| 7 | the last dance 🕺 | 13.70 | 63 |
| 8 | Matija L & Zhongwei W & Fususu | 11.64 | 175 |
| 9 | Third Intelligence | 9.76 | 57 |
| 10 | Ebi | 9.26 | 26 |
| 11 | yktori | 7.87 | 8 |
| 12 | Skyfall AI | 7.67 | 36 |
| 13 | Tanaka Ai24 | 7.55 | 51 |
| 14 | mostik.ai | 7.51 | 47 |
| 15 | UNK | 7.37 | 73 |

- **Cut-points** (2026-09-26 07:20 UTC):
  - Top-50 cutoff: **5.02**.
  - #10 = 9.26; #28 = 6.04 (the last team at or above 6); #100 = 4.32; #200 = 3.92; #500 = 3.23; #1000 = 1.42.
- **Team counts** (same timestamp): ≥15: 6 · ≥10: 8 · ≥6: **28** · ≥5: 50 · ≥4: 172 · ≥3: 614 · exactly 0: 158.
- **Best public notebook:** 4.50 ("Duck Qwen3.8 (Tuned)", run 2026-09-04). Every public notebook at or above 3 is a fork of the Duck harness running Qwen3.8. No public notebook scores above 4.50. — https://www.kaggle.com/code/chiakazirim/duck-qwen3-8-tuned
- **Volatility at the top:** #1 said they were 8th on 2026-09-24 and 1st by 2026-09-26. — https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/742935
- **Milestone 2:**
  - Deadline 2026-09-30 23:59 UTC, ranked on the public LB at that moment, with the notebook public and open-source by then.
  - Prizes $25,000 / $7,500 / $5,000 per the Kaggle Prizes page and Rules. arcprize.org lists $25K / $10K / $2.5K. Both total $37.5K, and the Kaggle Rules govern.
  - Sources: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview/prizes · https://arcprize.org/competitions/2026/arc-agi-3
- **Stated publication plans** (2026-09-23 to 09-26):
  - Tufa (#3): will not publish.
  - NVARC3 (#6): probably will not publish.
  - #1 and #2: will publish only if they are top-3 among teams willing to share.
  - A participant says the prize passes down to the highest-ranked open-sourced notebooks. The host has not confirmed this.
  - Sources: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/742801 · https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/742935
- **Milestone 1 reference (2026-06-30):** Tufa 1.21 (a 1.30 was retracted), Reki 0.86, forge 0.86. — https://arcprize.org/blog/arc-prize-2026-milestone-1

## 4. Score bands and what they mean

- **What a level is worth.** In a 7-level game (weights sum to 28), clearing levels at human efficiency earns:

  | Levels cleared | Game points (human efficiency) | Game points (2× human actions) |
  |---|---|---|
  | L1 | 3.6 | 0.9 |
  | L1–L2 | 10.7 | 2.7 |
  | L1–L3 | 21.4 | 5.4 |
  | L1–L4 | 35.7 | 8.9 |

  Using twice the human action count quarters these values.
- **What each band requires.** An LB score multiplied by 55 gives the total game points needed on the public half:

  | LB score | Game points | Rough equivalent (cleared levels at ~human efficiency) |
  |---|---|---|
  | 3 (rank ~614) | 165 | L1–L2 in 15 games, or L1–L3 in 8 |
  | **6 (rank ~28)** | **330** | **L1–L2 in 31 games, or L1–L3 in 15** |
  | 9.26 (#10) | 509 | L1–L3 in 24 games |
  | 16.68 (#5) | 917 | L1–L3 in 43 games, or L1–L4 in 26 |
  | 20.53 (#1) | 1,129 | L1–L3 in ~all 55, or L1–L4 in 32 |

- **Gaps:**
  - #1 to #5 is −3.85 points (−19%).
  - #1 over a score of ~5 (rank 50) is 4.1×. #1 over a score of ~3 (rank ~614) is 6.8×.
  - Going from 3 to 6 means doubling the weighted levels cleared. Going from 6 to 20 is another 3.4×.
- **Implications, from the formula:**
  - A score above ~10.7 requires clearing L3 or beyond in some games, because L1–L2 in all 55 games caps out at 10.7. The top 8 teams (≥11.64) must be reaching L3+ in most games.
  - Efficiency cannot close a coverage gap. Beating human efficiency adds at most +15%, and the weight cap limits each game to the levels completed. Efficiency only multiplies levels you already clear: 1.4× the human action count yields 0.51 of a level's value, and 2× yields 0.25.
  - Once a Duck-type agent cracks a level, it reportedly plays it at about human efficiency (level score of about 90–100). This is a single source, but the Astra analysis reports the same "binary" pattern for frontier models. — https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/743060 · https://arcprize.org/blog/astra
  - So the lever is coverage: how many games get cracked and how deep they go. Coverage is bounded by wall-clock time, because every Duck run hits its per-game time cap. Tokens per second and tokens per action are effectively score. — https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/734369
- **Noise from identical code:**
  - 11 official submissions of one harness scored 0.55–1.29 (mean 0.90, coefficient of variation 0.26). — https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/738762
  - Anim forks of Flash-Next scored 1.96–4.33, and a member of the #8 team reports "2.5–5.5 same code". A single pass over the 25 public games has σ of about 0.8–0.9. — https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/732854 · https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/743060
- **The 25 public games are a poor proxy for the LB.** Examples: local 22.3 gave LB 5.37, and local 17.3 gave LB 6.91 (same participant). Local 10.2 gave 3.05, while local 7.7 gave 4.42. — https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/732854
- **Odds of a best public score above 6.** Log-normal model with a coefficient of variation of 0.25–0.30; the public LB shows your best draw.

  | True mean | Chance >6, one draw | Chance >6, best of 5 draws |
  |---|---|---|
  | 4.0 | 4–6% | 18–28% |
  | 4.5 | 10–13% | 40–50% |
  | 5.0 | 19–22% | 66–71% |
  | 5.5 | 32–33% | 85–86% |

  A reliable score above 6 needs a true mean of at least 5.5 across every remaining daily draw, or about 6.5 or more for a single draw. A lucky public draw says nothing about the private half: the private score of the same submission is an independent draw on different games.

## 5. Approach map (legal vs illegal on Kaggle)

**Kaggle-legal** (offline, one RTX Pro 6000, 9 h, open weights). Scores are on the Kaggle public LB unless marked.

| Approach | Best measured | Board / date | Source |
|---|---|---|---|
| Random / "just explore" / Stochastic Goose samples | 0.18 / 0.19 / 0.25 | Kaggle public, Mar | https://www.kaggle.com/code/inversion/arc3-sample-submission-stochastic-goose |
| Classical search, no LLM (BFS, MCTS, graph exploration, BFS+CNN) | 0.29–0.46 | Kaggle public, Apr–Jun | https://www.kaggle.com/code/nihilisticneuralnet/0-46-arc-agi-3-persistent-memory-bfs-arc-solver |
| Vision model as policy returning JSON actions (Gemma-4-31B, reflection memory) | 0.86 | Kaggle public, 06-30 (M1 #2 and #3) | https://arcprize.org/blog/arc-prize-2026-milestone-1 |
| Gemma-4-31B + JEPA-style dynamics model | 0.79 | Kaggle public, 06-30 | https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/716711 |
| REPL coding agent "Duck" + Qwen3.6-27B FP8 | 1.21 (range 0.77–1.30); 25 public games 1.60 ± 0.45 | Kaggle public, 06-30 | https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/717133 |
| Duck + STaR LoRA on its own winning trajectories (Qwen3.6) | 1.25 → 1.94 | Kaggle public, ~Aug | https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/739047 |
| Duck + Qwen3.8-27B FP8 | 2.13–2.23 | Kaggle public, 08-17/18 | https://www.kaggle.com/code/foysalemonshanto/lb-9-arc3-duck-v12-with-qwen-3-8-27b |
| Duck + click-candidate hints + scoring/time prompt (Qwen3.8-27B) | 1.12 → 1.43 (single draws) | Kaggle public, Sep | https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/743060 |
| Duck + Qwen3.8-Flash-Next NVFP4 + MTP (serving change only) | 3.38 → 4.50 (best fork) | Kaggle public, 09-01 to 09-04 | https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp |
| The same + animation-frame access ("Anim") | 4.09–4.33 (best forks); A/B on the 25 public games +1.4%, p = 0.92 | Kaggle public, Sep | https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/734369 |
| Undisclosed private systems (Tufa, NVARC3, #1, #2, …) | 6.04–20.53 | Kaggle public, 09-26 | LB |

- **What moved the Kaggle score, in measured order:**
  - First, the base model plus serving throughput: 1.2 → 2.2 → 3.4–4.5.
  - Then undisclosed private work: 6 → 20.5.
  - Every prompt or tool tweak measured so far sits inside the noise. Tufa: gains came from "better base models and multi-modality"; hand-built tools hurt.
- **Dead ends, with numbers:**
  - 64K context: throughput fell from 283 to 195 tok/s, and the score from 1.43 to 1.20.
  - Temperature 0.3: 0.95, with fewer games making progress.
  - An archetype playbook in the prompt: 1.54 on the 25 public games, below its pre-set 3.5 threshold.
  - Gemma-4-31B is weaker at code and logic. DeepSeek-V4-Flash is slow on the RTX and has no vision.
  - Multi-role LLM loops need 5× the calls and don't fit in 9 h.
  - SFT on human play of the public games gave no gain.
  - Down-weighting reasoning tokens in SFT caused a "no tool call" collapse.
  - Giving more time to games at L2+ helped on the 25 public games (7.6 → ~13) but slightly hurt the LB.
  - Sources: 743060 · 739938 · 742788 · 743319 · 740812 (all https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/<id>)
- **Inference only, no published evidence:** the top teams' levers. The forum guesses fine-tuning, possibly on off-Kaggle H200-class compute, plus synthetic "harder than public" games. The NVIDIA team says self-generated data was not treated as external data when they won ARC-AGI-2. — https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/742940

**Not transferable to Kaggle** (network or frontier-API systems, or public-demo-only results):

| System | Score | Board | Cost | Source |
|---|---|---|---|---|
| GPT-6 Astra (high) | 99.9% | ARC semi-private, Provider Adapter harness | $18.8K | https://arcprize.org/blog/astra |
| GPT-6 Astra (max) | 62.7% | ARC semi-private, Standard harness | $26.1K | https://arcprize.org/leaderboard |
| Gemini 3.8 Flash (high) | 35.0% / 10.4% | ARC semi-private, Provider Adapter / Standard | $4.5K / $4.4K | https://arcprize.org/leaderboard |
| Claude Opus 5 (high) | 30.2% | ARC semi-private, Standard | $20.7K | https://arcprize.org/leaderboard |
| GPT-5.6 Sol (max) | 7.8% | ARC semi-private, Standard | $25.1K | https://arcprize.org/leaderboard |
| NVIDIA AVO (on Claude Opus 5) | 100.00; 183/183 levels, 6,624 actions | ARC public demo (25 games) | n/a | NVIDIA blog, 2026-08-21 |
| VISTA (vision-only, 512 px frames) | ~100% (Claude / Sol) | ARC public demo | n/a | NVIDIA blog; 734369 comment |
| Symbolica ARCgentica | 36% | ARC public demo, day after release | n/a | Tufa write-up (717133) |

- **Why none of these transfer:**
  - No internet, and 96 GB of VRAM caps model size.
  - 9 h for 110 games.
  - The frontier runs cost $17K–$50K.
  - The distance between the Kaggle #1 (20.53) and Astra (99.9%) is the offline-versus-API gap.
  - A 100% on the public demo is not a Kaggle result.
- **Illegal or useless on Kaggle:**
  - Loading game source into a private simulator. The files are absent in the rerun, and the host has seen no evidence it works on private games.
  - Playing the same game in parallel.
  - Resetting repeatedly to get "fresh" draws. Resets count as actions, and a game reset becomes a level reset.

## 6. Bets, ranked

- **Bottom line:** nothing published reliably scores above 6.
  - The best public notebook's best draw is 4.50, and its forks spread roughly 2–4.5. The ~440 teams scoring 3–4 are mostly those forks, so a stock fork's true mean is about 3.5.
  - Closest public evidence of a fork-based route past 6: a heavily modified Flash-Next fork reports "stable 4.0+" and a best of 6.23 after 51 submissions (now #27). Harness fixes alone got another participant to 5.19 after 61 submissions (#42). — https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/732854 · https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/742801
  - To clear 6 by 2026-09-30 you need to raise the fork's mean from about 3.5 to 5 or more (+40%) and use every remaining daily submission.
  - You have at most 5 draws (Sep 26–30). Each run takes about 9 h plus queue time, and a run must finish scoring before 23:59 UTC on 09-30.

Ranked by expected hidden-set lift per unit of work:

| Rank | Bet | Estimated band if it works | Work | Kaggle-legal |
|---|---|---|---|---|
| 1 | Throughput-tuned fork of the Flash-Next Duck | mean ~3.5–4.5 (draws 3–5.5) | ½ day | Yes |
| 2 | Waste-cutting harness fixes, stacked on 1 | +0 to +1.0 | 1 day | Yes |
| 3 | STaR LoRA on your own winning trajectories | +0.5 to +2, often negative | 3–5 days + rented GPU | Yes, if weights and code are published |

**Bet 1: start from the strongest public base and spend effort on throughput, not prompts.**
- **Claim:** fork the best Flash-Next NVFP4 + MTP Duck notebook unchanged. Then tune serving so more tokens, and so more actions and hypotheses, fit inside each game's 7,920 s cap:
  - raise the number of concurrent vLLM sequences from 8 towards 16;
  - keep 32K context, 3-token MTP and 28-way game concurrency;
  - keep reasoning at xhigh.
- **Evidence:**
  - Only model and serving changes have moved the LB materially (1.21 → 2.2 → 3.4–4.5).
  - Runs are wall-clock bound: +17% tokens per action cost actions in every game, and 64K context lost both throughput and score.
  - One participant reports the stock NVFP4 Duck at 16 sequences reaching "the brink of top 10%" (about 3.6 at today's cut); another found no gain beyond 16. This sets the baseline; it is not yet evidence of a lift. The xhigh reasoning setting beat low both locally and on the LB, per one participant.
  - Sources: https://www.kaggle.com/code/chiakazirim/duck-qwen3-8-tuned · 734369 · 732854 · 739938 · 735243
- **Falsified if:** a run on the 25 public games shows actions per game and decode tok/s up less than 15% versus 8 sequences, or 2 LB draws both land below 3.5.
- **Kaggle-legal:** yes.
- **Band:** mean about 3.5–4.5. Alone, this gives roughly 10–40% odds of at least one draw above 6 in 5 draws (see the odds table in §4).

**Bet 2: cheap harness fixes aimed at the two known waste modes, dead actions and empty turns (stack on Bet 1).**
- **Claim:**
  - (a) Label `ACTION7` as UNDO, as the docs define it.
  - (b) Put the true scoring rule and a remaining-time line into the prompt.
  - (c) Block exact repeats of a (state, action) pair that has already been a no-op.
  - (d) Tell the model explicitly when its last turn produced no tool call.
  - (e) For click games, supply deterministic click candidates from connected components.
- **Evidence:**
  - (b)+(e) together: 1.12 → 1.43 (+28%, single draws).
  - (a): one participant got their best score with the UNDO label.
  - (c): 12–20% fewer actions, though the gain is unclear under a time cap.
  - (d): in one failure mode, 1,474 of 4,767 turns produced no action.
  - Sources: 743060 · 742477 · 734369 · 743319
- **Falsified if:** turn logs from the 25 public games show no drop in no-op actions or empty turns, or LB draws don't beat the Bet 1 draws.
- **Kaggle-legal:** yes.
- **Band:** +0 to +1.0 on top of Bet 1 (a mean of about 4–5.5 combined). You need Bets 1 and 2 together to reach the mean of about 5 that gives better-than-even odds above 6.

**Bet 3: STaR / rejection-sampling LoRA on your own winning trajectories. Only worth it if you already have transcripts and a training box.**
- **Claim:** SFT on the agent's own level-completing transcripts (the process, not the answers) raises the number of games cracked.
- **Evidence for:**
  - 1.25 → 1.94 on Qwen3.6-27B (Kaggle public, one comparison).
  - Local 11.0 → 13.0 using same-model traces (another participant).
- **Evidence against:**
  - "LoRA backfired" for another participant.
  - Adding more data with the same recipe made things worse.
  - Down-weighting reasoning tokens caused a no-action collapse.
  - Flash-Next cannot be trained on the RTX Pro 6000; it needs a rented H200 node. A 27B LoRA would have to roughly double to match base Flash-Next.
- **Sources:** 739047 · 732854 · 742835 · 743319
- **Falsified if:** the tuned model fails to beat its base on 2 or more LB draws, or the no-tool-call rate rises.
- **Kaggle-legal:** yes, if the weights and training code are published (required for the milestone). Rented compute is subject to the cost "reasonableness" test.
- **Band:** 27B LoRA 2.5–4. Flash-Next LoRA 5–7 if it works. Unlikely to land before 09-30.

**Submission policy (execution rule, not a bet):**
- Freeze the best config and submit it every remaining day, rather than spending draws on A/B tests on the LB.
- If a draw lands above 6, publish that notebook under an open-source licence before 2026-09-30 23:59 UTC. The top teams are not publishing, so if the prize passes down the ladder, an open notebook above 6 could place in Milestone 2.
- Ask the host now to confirm the ladder rule.
- This policy raises your public best by about +1 to +1.5 over your mean. It adds nothing to your private score.

**Skip this week:**
- Swapping to Gemma-4-31B, DeepSeek-V4-Flash or GPT-OSS-120B.
- Multi-role LLM loops, prompt playbooks, lower temperature, or longer context.
- Tuning to scores on the 25 public games.

**After 09-30, for the 11-02 final:** the highest-probability route above 6 is to fork any top notebook released for Milestone 2 (#1 and #2 said they may publish). The Milestone 1 precedent: Tufa's 1.21 release became the base of every high-scoring public notebook. Expect thousands of copies and noisy ranks.

## 7. Sources

- Kaggle overview, rules, prizes, timeline, code requirements, data: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3
- Kaggle leaderboard, live 2026-09-26 07:20 UTC: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/leaderboard
- Kaggle discussion, index: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion. Threads cited, with IDs appended to `/discussion/`:
  - Host rulings: 703990, 707925, 713634, 713921, 718638, 729985
  - Milestone publication plans: 742801, 742935
  - Write-ups: 717133 (Tufa Duck), 734369 (TAAF Anim), 743060 (perception-augmented Duck)
  - Fine-tuning: 739047 (STaR LoRA), 742835, 743319
  - Variance and proxy validity: 732854, 736578, 737617, 738762, 739801, 740812
  - Operations: 697720, 705405, 742148
  - Approaches and rules questions: 739938, 742477, 742788, 742940
- ARC docs, scoring: https://docs.arcprize.org/methodology
- ARC docs, competition mode: https://docs.arcprize.org/toolkit/competition_mode
- ARC Prize 2026 · ARC-AGI-3 page: https://arcprize.org/competitions/2026/arc-agi-3
- Milestone 1 results: https://arcprize.org/blog/arc-prize-2026-milestone-1
- GPT-6 Astra analysis (Standard vs Provider Adapter): https://arcprize.org/blog/astra
- ARC verified leaderboard (data: https://arcprize.org/media/data/leaderboard/v3.json): https://arcprize.org/leaderboard
- NVIDIA AVO (public demo only): https://developer.nvidia.com/blog/nvidia-avo-reaches-100-on-arc-agi-3-demonstrating-a-frontier-level-general-purpose-architecture-for-long-horizon-autonomous-agents/
- Top public notebooks:
  - https://www.kaggle.com/code/chiakazirim/duck-qwen3-8-tuned
  - https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp
  - https://www.kaggle.com/code/wuliao0/duck-qwen3-8-anim-base
  - https://www.kaggle.com/code/jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner
