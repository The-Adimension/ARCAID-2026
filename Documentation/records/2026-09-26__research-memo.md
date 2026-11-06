# ARC Prize 2026 · ARC-AGI-3 (Kaggle): research memo

*Written 2026-09-26. My environment's network policy blocked kaggle.com, arcprize.org, docs.arcprize.org, arxiv.org and github.com, so I couldn't open any page directly. Every figure below is taken from search-engine extracts of the cited URL. "Undated" means the source gave no date; I retrieved all of them on 2026-09-26.*

## 1. What the benchmark is

- **What it measures:** how efficiently an agent learns to play a new, turn-based grid game. Frames are up to 64×64 cells with 16 colours. There are no instructions, so the agent has to work out the rules and the goal by acting. Score is action efficiency relative to first-time human players. [Tech report](https://arcprize.org/media/ARC_AGI_3_Technical_Report.pdf)
- **Sets (two sources disagree, both kept):**
  - Tech report: 135 environments, split into 25 public demo, 55 semi-private (used to verify frontier APIs) and 55 fully private (reserved for Kaggle). [arXiv 2603.24621](https://arxiv.org/html/2603.24621v1)
  - Kaggle data page: 110 hidden games, half scored on the public LB and half on the private LB. [Kaggle data](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/data)
- **Human bar:** every environment was solved by at least 2 of roughly 10 first-time players. [Human dataset post](https://arcprize.org/blog/arc-agi-3-human-dataset)
- **Official formula (RHAE)** [Methodology](https://docs.arcprize.org/methodology):
  - Level: `s_i = min((h_i / a_i)², 1.15)`. `h_i` is the human baseline action count for level i; `a_i` is the agent's actions on that level, RESETs included.
  - Cutoff: if `a_i > 5·h_i`, the agent is stopped and the level scores 0. Later levels can't be reached, so their contribution is lost too.
  - Game: `Σ i·s_i / Σ i`, summed over **all** levels of the game with weights 1, 2, 3, …. The game score is capped at the weighted fraction of levels completed.
  - Total: the mean of game scores across all games.
- **Versions:** the 2026-04-14 changelog raised the level cap from 1.0 to 1.15 and switched the baseline from "second-best human" to the median human. Some pages still say "upper-median". Either way the squared ratio is what drives the score. [Methodology](https://docs.arcprize.org/methodology)
- **What counts as an action:** only commands that change the environment. Reasoning, tool calls and code execution are free. A game-over triggers a RESET, and that RESET uses up the level's action budget. [Methodology](https://docs.arcprize.org/methodology)
- **Public vs hidden difficulty:** the official line is that the public set is "materially easier" and public-set scores are never reported on the official board. [Tech report](https://arcprize.org/media/ARC_AGI_3_Technical_Report.pdf)
  - One leaderboard page says the opposite. The measured pair below supports "public easier": GPT-5.6 Sol scored 13.3% on public with the official harness (2026-07-30) and 7.78% on semi-private (ARC-verified, July). [OpenAI](https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores/), [Schema](https://schema-harness.github.io/)

## 2. Kaggle constraints

- **Submission format:** a code competition. You submit a notebook, and Kaggle reruns it against the hidden games through its gateway. The local `arc-agi` package runs the same engine. [ARC docs 2026](https://docs.arcprize.org/arc-prize-2026)
- **No internet while scoring.** Hosted APIs (GPT, Claude, Gemini) can't be used, and RTX sessions must have internet disabled. [Kaggle rules](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/rules)
- **Hardware:** one GPU. Options are CPU, T4, P100 or RTX PRO 6000 (96 GB). The RTX is reserved for ARC-AGI-3. [Kaggle discussion](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion)
- **Wall clock:** 9 h for the scored rerun.
  - The Duck/TAAF payload is configured for 32,400 s, with a soft stop 30 min earlier, 7,920 s per game and 28 games in parallel. [JustAdev742 repo](https://github.com/JustAdev742/Arc-Agi-3-Kaggle-comp)
  - "<12 h" also appears, but that is the ARC site's "Kaggle Systems" listing rule. Plan for 9 h. [ARC leaderboard](https://arcprize.org/leaderboard)
- **5 submissions per day.** [ARC docs 2026](https://docs.arcprize.org/arc-prize-2026)
- **Models and data:** external data and pretrained weights are allowed if they are freely and publicly available. [arcprize.org 2026](https://arcprize.org/competitions/2026)
- **Licence:**
  - Code you write must be released as CC0 or MIT-0.
  - Third-party code must carry an open-source licence that allows public sharing (for example Apache-2.0 or GPLv3).
  - Prize-eligible teams must open-source before they receive private scores, or they are removed. [arcprize.org 2026](https://arcprize.org/competitions/2026)
- **Milestone eligibility:** your notebook must be public under an open-source licence by the milestone date. [Kaggle overview](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview)
- **Licence risk:** as of issue #6 (undated), the Tufa `duck-harness` repo and its framework repos had no LICENSE file. If you build on it, confirm its licence before 2026-09-30. [Issue #6](https://github.com/Tufalabs/duck-harness/issues/6)
- **Dates (all 23:59 UTC):**
  - Milestone 2: 2026-09-30.
  - Final submissions: 2026-11-02.
  - Results: 2026-12-04. [Kaggle overview](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview)

## 3. Live standings (dated)

- **I couldn't get the leaderboard.** kaggle.com is blocked from here, and the LB page is JavaScript-rendered, so no search index holds its rows. **I found no top-15 table and I don't give one.** No source I found gives the top-50 cutoff either.
- **Dated score points (Kaggle public LB unless noted):**
  - 2026-05-22: the best public template scored 0.68, "which is why so many people have this score". Tufa Labs went from 0.68 to 1.17. [Kamradt on X](https://x.com/GregKamradt/status/2057897180955025593)
  - 2026-06-30, Milestone 1 winners: 1. Tufa Labs "Duck", 2. Reki, 3. Md Boktiar Mahbub Murad ("forge"). [ARC M1 post](https://arcprize.org/blog/arc-prize-2026-milestone-1)
    - Tufa reported 1.21% on 2026-07-01. [Tufa on X](https://x.com/tufalabs/status/2072336849465417747)
    - One search extract gives 1.03 for Duck on Kaggle, without saying which board. I couldn't isolate the source page.
    - I found no score for 2nd or 3rd place.
  - Undated: "Kaggle leaderboard leader scores 1.86%", from a competitor's GitHub README. I couldn't isolate which one.
  - 2026-08-25: one competitor reached LB 2.56, their peak across 21 submissions made between 2026-07-31 and 2026-09-01. [Shih-Yu-Yeh journal](https://github.com/Shih-Yu-Yeh/arc3-dev-agi-journal)
  - Undated: another competitor reports LB 2.37. The same repo reports 5.27 locally on the 25 public games (31 of 183 levels). [anandsingh8687 repo](https://github.com/anandsingh8687/arc-prize-2026-arc-agi-3-agent)
  - Undated, Kaggle Models page ("best public score" per model): Qwen3.8-27B FP8 Repacked **3.11**; Gemma-4-31B **0.86**. [Kaggle models](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/models)
    - 3.11 is the highest Kaggle number I found. It is a lower bound on the current #1.
- **Names with ranks but no scores (undated):** Tufa Labs #1, Sanjay Dutt #12, Yusaku Muroya #13, CreateAMind #18, StochasticGoose_v7_final #30, Junhua Yang #42. [Medium LB summary](https://medium.com/@ccro8990/the-official-live-leaderboard-for-the-arc-agi-3-machine-learning-competition-hosted-on-kaggle-part-06dbe491c8dc)
- **Field size (undated):** 731 teams, 771 participants, 4,645 entrants. [Competehub](https://www.competehub.dev/en/competitions/kagglearc-prize-2026-arc-agi-3)
- **Milestone 2:**
  - Deadline 2026-09-30.
  - Prizes: $25K / $10K / $2.5K per the ARC competition page. One secondary source says $25K / $7.5K / $5K. [ARC-AGI-3 comp](https://arcprize.org/competitions/2026/arc-agi-3), [BIG-FISH issue](https://github.com/burbanodev-lab/pantrypilot-mcp/issues/13)
  - Rule: top 3 at the deadline, with the notebook public under an open-source licence.
  - **Not confirmed:** whether the public or private board decides the milestone.
- **Final prizes:**
  - Top-score prizes of $40K / $15K / $10K / $5K / $5K come from a secondary source only. [BIG-FISH issue](https://github.com/burbanodev-lab/pantrypilot-mcp/issues/13)
  - A $700K grand prize unlocks at a 100% score. [Kaggle overview](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview)

## 4. Score bands and what they mean

These use the official formula on a 55-game board with a typical 7-level game (weights sum to 28; the public set averages 183 levels over 25 games, about 7.3). One game is worth at most 1.82 LB points. `r` is agent actions divided by human actions.

| What gets cleared | r = 1 | r = 1.5 | r = 2 | r = 3 | r = 5 |
|---|---|---|---|---|---|
| Level 1 of one game | 0.065 | 0.029 | 0.016 | 0.007 | 0.003 |
| Level 3 of one game | 0.195 | 0.087 | 0.049 | 0.022 | 0.008 |
| A full 7-level game | 1.82 | 0.81 | 0.45 | 0.20 | 0.07 |

- **Converting a gap into play:** 0.5 LB points is roughly any of these:
  - about 8 extra level-1 clears at human parity;
  - about 31 extra level-1 clears at 2× human;
  - about 1 extra full game at 2× human.
- **Efficiency multiplies what you already clear.** Going from 3× to 2× human raises a level's score 2.25×; going from 2× to 1.5× raises it 1.78×. Beating humans pays almost nothing, because the cap is 1.15.
- **Coverage is weighted by depth, but you can't skip ahead.** Level 3 is worth 3× level 1 at the same efficiency. You only reach it by clearing levels 1 and 2 within the 5× cutoff, and one cutoff ends the rest of the game.
- **What a score of about 3 means:** about 1.65 "full-game equivalents" out of 55. That is shallow coverage (levels 1–2 in many games), inefficient clears, or both.
- **Noise:**
  - Four identical 25-game passes varied by σ ≈ 21% of the mean. A top-five competitor is quoted with the same figure (about 20% across seeds).
  - One "jackpot" game (sb26) took the coefficient of variation from 6% to 24%.
  - At an LB of 2.5–3, σ is about 0.5–0.6 points. [sonpham PR #41](https://github.com/sonpham-org/arc-3/pull/41)
- **Gap from #1 to #5 and #3:** I can't name it because I don't have the rows. The known open-weight results span 2.37–3.11 (undated), about 0.7 points, which is roughly one σ.
  - Ranks inside that band can't be told apart with a single run.
  - The private board uses a different 55 games, so expect reshuffling.

## 5. Approach map (legal vs illegal on Kaggle)

**Kaggle-legal (offline, one GPU, open weights)**

- **LLM coding agent in a REPL (Tufa "Duck" / TAAF).**
  - Setup: Qwen3.6-27B FP8. It sees the grid as an image plus ASCII and has a segmentation tool. Old messages are dropped to stay within context (64k cap, evicting down to 32k).
  - Scores: Kaggle LB 1.17 (2026-05-22), then 1.21% (2026-07-01). On the 25 public games: 1.60 ± 0.45 over 20 tries.
  - Tufa's own claim is that the gains came from multimodality and better base models, not hand-built tools. [Tufa writeup](https://tufalabs.ai/research/duck-harness/)
- **Duck forks on Qwen3.8-27B-FP8.**
  - One competitor went from LB 0.87 to 2.56 between 2026-07-31 and 2026-08-25. The peak came from raising image upscaling from 4 to 8 (256 px to 512 px).
  - Every module added after that scored lower (their V25 to V35). [Shih-Yu-Yeh journal](https://github.com/Shih-Yu-Yeh/arc3-dev-agi-journal)
  - Best public score for this model: 3.11 (undated). [Kaggle models](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/models)
- **Vision-LLM as policy (Reki; forge).**
  - Reki: Gemma-4-31B looks at labelled frames and returns JSON with 1–4 actions. forge adds candidate generation and an arbiter that picks between them.
  - Placed 2nd and 3rd at Milestone 1; no scores published. Best public score for Gemma-4-31B is 0.86 (undated). [ARC M1 post](https://arcprize.org/blog/arc-prize-2026-milestone-1), [Kaggle models](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/models)
- **Programmatic, no LLM (learned transition model, state hashing, BFS).**
  - LB 0.26–0.27. The author calls this the ceiling for that track. [BDR-Pro repo](https://github.com/BDR-Pro/arc-prize-2026-arc-agi-3)
- **CNN that predicts which actions change the frame, plus RL (StochasticGoose).**
  - 12.58% on the 2025 preview games, then 0.25% on the full benchmark at launch. [ARC preview learnings](https://arcprize.org/blog/arc-agi-3-preview-30-day-learnings), [Tech report](https://arxiv.org/html/2603.24621v2)
- **Tiny-model epistemic agent (AERA, Qwen2.5-0.5B).**
  - RHAE 0.21 on the **public 25 only**.
  - The same paper shows every public game can be beaten with non-intelligent strategies, and 18 games can be bypassed with a null-coordinate bug. This is no evidence for the hidden set. [arXiv 2605.25931](https://arxiv.org/abs/2605.25931)
- **LoRA fine-tuning on replay traces.**
  - Round 3 on held-out public games: 7 levels cleared fell to 2 (score 20.4 → 0.7 in local units, 2026-09). Round 4 showed no gain. [sonpham PR #59](https://github.com/sonpham-org/arc-3/pull/59), [PR #65](https://github.com/sonpham-org/arc-3/pull/65)
  - RL LoRA on Qwen3.8 (2× H100): no score published. [qwen38-arc3-rl](https://github.com/U4AR/qwen38-arc3-rl)
- **Harness knobs with measured effect (local, public games):**
  - Qwen3.8-Flash-Next-NVFP4 (a mixture-of-experts model with ~6B active parameters) beat the 27B model on 6 of 7 hard games at the same median clock, using the same or fewer actions. [sonpham PR #40](https://github.com/sonpham-org/arc-3/pull/40)
  - Letting the model press RESET, behind a rate limit: 1.54 vs 0.995, with the same 16 levels cleared. Most of the gap came from two passes, so it's weak evidence. [sonpham PR #27](https://github.com/sonpham-org/arc-3/pull/27)

**Not Kaggle-legal (network or frontier models); most results are on the public demo**

- **ARC-verified, semi-private:**
  - GPT-6 Astra: 62.7% on the standard harness ($26K) and 99.9% with a provider adapter ($19K), 2026-09-03. [ARC Astra post](https://arcprize.org/blog/astra)
  - Claude Opus 5: 30.2%, 2026-07-24. [ARC result](https://arcprize.org/results/anthropic-claude-opus-5)
  - GPT-5.6 Sol: 7.78%, July. [Schema](https://schema-harness.github.io/)
  - Grok 4.6: 2.11%, 2026-08-11. [ARC results](https://arcprize.org/results)
- **Self-reported, public 25 only:**
  - Symbolica Agentica 36.08% (113/182 levels), launch day. [Symbolica](https://www.symbolica.ai/blog/arc-agi-3)
  - Executable World Models, GPT-5.5: 58.12%. [arXiv 2605.05138](https://arxiv.org/abs/2605.05138)
  - Schema: about 99%. [Schema](https://schema-harness.github.io/)
  - OPINE-World: 160 of 183 levels. [arXiv 2607.01531](https://arxiv.org/abs/2607.01531)
  - Twin: 93.3. [arXiv 2608.14490](https://arxiv.org/abs/2608.14490)
  - Tycho: 88.49 mean; 100 with top models. [arXiv 2607.28287](https://arxiv.org/abs/2607.28287)
  - NVIDIA AVO: 100. [NVIDIA](https://developer.nvidia.com/blog/nvidia-avo-reaches-100-on-arc-agi-3-demonstrating-a-frontier-level-general-purpose-architecture-for-long-horizon-autonomous-agents/)
  - Prime Agent: 30 → 95.5. [arXiv 2608.23552](https://arxiv.org/abs/2608.23552)
- **Memory handling is the transferable finding:**
  - GPT-5.6 Sol on public went from 13.3% to 38.3% with retained reasoning and compaction (2026-07-30). [OpenAI](https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores/)
  - ARC says Astra's 62.7 vs 99.9 is "caused entirely by memory handling". [ARC Astra post](https://arcprize.org/blog/astra)
  - Gemini 3.8 Flash: the harness that keeps the model's reasoning was ahead or level on 21 of 21 game/effort pairs. [sonpham PR #73](https://github.com/sonpham-org/arc-3/pull/73)
  - None of these systems transfers to Kaggle. Only the ideas do.

## 6. Bets, ranked

Budget to 2026-09-30 is at most about 20 submissions. One LB reading has σ ≈ 20%, so judge each change on local multi-seed means over the 25 public games, not on a single LB number.

1. **Run Qwen3.8-27B-FP8 in an unmodified Duck-class REPL harness with upscale = 8.**
   - **Evidence:** LB 0.87 → 2.56 (2026-08-25). Best public score for this model is 3.11 (undated). Tufa attributes its gains to the base model and multimodality. Modules added on top regressed.
   - **Falsifier:** two LB runs no better than your current best, or a 3-seed local mean that doesn't beat Duck on Qwen3.6.
   - **Kaggle-legal:** yes. Check the harness licence first.
   - **Band if it works:** about 2.4–3.1 on the public LB. This is the measured range; the private board may differ.
2. **Swap in Qwen3.8-Flash-Next-NVFP4 behind the same harness.**
   - **Evidence:** beat the 27B on 6 of 7 hard games at the same clock with no more actions (2026-09). It runs at 81–88 tok/s single-stream and 341 tok/s with 6 concurrent streams on one RTX PRO 6000, so more turns fit into 9 h. [NVIDIA forum](https://forums.developer.nvidia.com/t/optimized-qwen3-8-flash-next-on-1x-rtx-pro-6000-171-tok-s-524k-and-hicache-nixl-persistence/381722)
   - **Falsifier:** the 25-game, 3-seed mean isn't above bet 1's, or it runs out of memory or time on Kaggle.
   - **Kaggle-legal:** yes; the weights are on Kaggle. [Kaggle model](https://www.kaggle.com/models/keithtyser/qwen3-8-flash-next-nvfp4)
   - **Band:** my estimate is at or above bet 1. I found no LB data point.
3. **Audit coverage against the clock.**
   - **Evidence:** a game that doesn't start, or hits the 7,920 s per-game cap, scores 0. There are 110 games, 9 h and 28 in parallel.
   - **Method:** Kaggle hides scored-run logs, so time local runs at Kaggle concurrency and extrapolate to 110 games.
   - **Falsifier:** projected 95th-percentile total time is under 8.5 h and no game hits its per-game cap.
   - **Kaggle-legal:** yes.
   - **Band:** recovers your mean score × the fraction of games dropped. Zero if none are dropped. Cheapest bet here.
4. **Keep the model's reasoning, or a compact memory of it, instead of dropping old messages.**
   - **Evidence:** 13.3 → 38.3 (OpenAI, 2026-07-30); 62.7 → 99.9, ARC-verified (2026-09-03); 21 of 21 pairs ahead or level (Gemini 3.8 Flash). All of this is frontier models. There's no open-weight measurement, and a "compact reasoning" A/B lift came entirely from one jackpot game (+23.4; −2.9 without it). [sonpham PR #41](https://github.com/sonpham-org/arc-3/pull/41)
   - **Falsifier:** no lift in a 3-seed local A/B once sb26 is excluded, or longer contexts push games past the clock.
   - **Kaggle-legal:** yes.
   - **Band:** my estimate is +0 to +1 point over bet 1. Highest variance of the five.
5. **Cut wasted actions:** skip actions predicted to leave the frame unchanged, skip revisits of states already seen, and don't act until a hypothesis predicts the result.
   - **Evidence:** the formula (3× → 2× human is worth ×2.25 on every level you already clear). Frontier world-model planners beat human efficiency on 158 of 179 levels (Twin). As a standalone policy, action-effect prediction fell to 0.25% at launch.
   - **Falsifier:** logs show under 10% of actions are no-ops or revisits.
   - **Kaggle-legal:** yes.
   - **Band:** my estimate is +0–30% relative on the current score.

**Don't spend this week on:**
- LoRA fine-tuning on public or human traces (held-out 7 → 2 levels).
- Stacking modules onto a working fork (V25–V35 regressed).
- A programmatic-only agent (0.27 ceiling).
- Any public-set 90–100% result used as evidence for Kaggle.
- Resubmitting for LB spikes. That samples σ, adds nothing on the hidden set, and only matters if Milestone 2 is decided on the public board.

## 7. Sources

- Kaggle competition overview (dates, prizes, milestone rule): https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview
- Kaggle rules (internet, licences, external models): https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/rules
- Kaggle data (110 hidden games, 50/50 public/private split): https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/data
- Kaggle models tab (best public score per model): https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/models
- Kaggle leaderboard (couldn't access from this environment): https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/leaderboard
- ARC scoring methodology: https://docs.arcprize.org/methodology
- ARC Prize 2026 Kaggle docs: https://docs.arcprize.org/arc-prize-2026
- ARC-AGI-3 competition page: https://arcprize.org/competitions/2026/arc-agi-3
- ARC Prize 2026 rules summary: https://arcprize.org/competitions/2026
- Milestone 1 post: https://arcprize.org/blog/arc-prize-2026-milestone-1
- ARC leaderboard: https://arcprize.org/leaderboard
- GPT-6 Astra analysis: https://arcprize.org/blog/astra
- ARC-AGI-3 tech report: https://arcprize.org/media/ARC_AGI_3_Technical_Report.pdf
- Kamradt, 0.68 → 1.17 (2026-05-22): https://x.com/GregKamradt/status/2057897180955025593
- Tufa Duck writeup: https://tufalabs.ai/research/duck-harness/
- Duck repo licence issue: https://github.com/Tufalabs/duck-harness/issues/6
- LB 0.87 → 2.56 journal: https://github.com/Shih-Yu-Yeh/arc3-dev-agi-journal
- Duck-fork lab (variance, LoRA, model and RESET studies): https://github.com/sonpham-org/arc-3
- Programmatic agent (LB 0.27): https://github.com/BDR-Pro/arc-prize-2026-arc-agi-3
- OpenAI, retained reasoning and compaction: https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores/
- AERA / public-set exploits: https://arxiv.org/abs/2605.25931
- Executable World Models: https://arxiv.org/abs/2605.05138
- Schema: https://schema-harness.github.io/
- Twin: https://arxiv.org/abs/2608.14490
- Tycho: https://arxiv.org/abs/2607.28287
- Symbolica: https://www.symbolica.ai/blog/arc-agi-3
- Competehub (team count): https://www.competehub.dev/en/competitions/kagglearc-prize-2026-arc-agi-3
- Medium LB summary (ranks and names): https://medium.com/@ccro8990/the-official-live-leaderboard-for-the-arc-agi-3-machine-learning-competition-hosted-on-kaggle-part-06dbe491c8dc
