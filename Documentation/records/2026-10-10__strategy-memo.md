# ARC Prize 2026 · ARC-AGI-3 (Kaggle): what can still move the private score, 2026-10-10

Live data was read on 2026-10-10 between 17:10 and 18:00 UTC through the Kaggle API, rendered Kaggle pages, arcprize.org, docs.arcprize.org, arXiv and Hugging Face. Every derived number below is reproduced by `analysis/2026-10-10/` (scripts, inputs with checksums, and the source pages as fetched). 23 days remain: final submission deadline 2026-11-02 23:59 UTC; entry and team-merger deadline 2026-10-26.

## Answer

- **No approach is guaranteed, and none of the public ones is even likely to win.** The top 5 score 41–63. The best public base averages about 26 per draw. No public notebook, write-up, paper, model or fine-tune report explains that 15–37 point gap.
- **The field has converged on one system.** All three Milestone 2 winners run Tufa's Duck harness with Qwen3.8-Flash-Next. So do 40 of the 41 public notebooks scoring 20 or more: they attach Flash-Next weights and a TAAF/Duck source bundle. The 41st now attaches only a handbook dataset, though its card says it was copied from Franzen's notebook. What lifted the winners above earlier forks was inference engineering: longer retained context, an FP8 KV cache, speculative decoding and prefix-cache reuse. None of them won on a new agent idea.
- **Your 27.05 is an ordinary draw of that system, not a measure of rank 855.** Single draws that can be traced to unchanged Franzen code score 21.01–27.89. The 25–36 band on the public board fits "best of 2–3 draws of identical code". The private board will compress that band.
- **New measurement, from Franzen's own 4-pass run on the 25 demo games:**
  - **Tokens are close to saturated.** +10% tokens is worth about +0.26 demo points out of 46.49.
  - **Completed levels are already played better than humans,** at a median 0.64× the human action count.
  - **Score is lost on stuck levels.** 40 of the 67 stuck attempts were on levels the same system solved in another pass, typically with half the tokens.
  - **The model's first idea is the variance.** Taking each game's best of the 4 passes would score 61.89 instead of 46.49.
- **One change has data behind it: restart a stuck level with a fresh context and a fresh token budget.**
  - Estimated value: +0.8 to +4.9 demo points.
  - It comes with a cheap mechanism test that can falsify it.
  - Implement it on unchanged Franzen v1, test it on demo games, and submit it only if the test passes.
- **For the final selection, choose two independent, healthy draws of the best-evidence configuration.** Kaggle's standard rule counts the better of your selected private scores, so two independent draws are worth about +2.2 points over one.

## 1. Live standings (Kaggle public LB, CSV of 2026-10-10 17:12:56 UTC)

| # | Team | Score | Subs |
|---|---|---|---|
| 1 | Yi-Chia Chen | 62.96 | 26 |
| 2 | Tufa Labs | 56.52 | 159 |
| 3 | mtg | 44.32 | 64 |
| 4 | Majkel1337 | 42.66 | 13 |
| 5 | NVARC3 | 40.97 | 33 |
| 6 | the last dance 🕺 | 39.30 | 77 |
| 7 | dreach.ai | 39.11 | 34 |
| 8 | Nhan Duc Nguyen | 38.84 | 15 |
| 9 | artificialagencylab.com | 38.62 | 49 |
| 10 | fshindo | 38.20 | 10 |
| 11 | 復活の混テキスト | 38.15 | 80 |
| 12 | SparseTech | 37.98 | 34 |
| 13 | keithtyser | 37.22 | 104 |
| 14 | _hans | 37.07 | 7 |
| 15 | Lord Han Solo | 36.61 | 88 |

- **Size:** 4,099 teams on the board. The Overview page shows 4,097 teams, 47,494 submissions and 16,896 entrants.
- **Cut-points:**
  - #10 = 38.20; #20 = 35.45; #50 = 33.24; #100 = 32.09; #200 = 31.11; #353 = 30.03; #500 = 29.12; #1000 = 25.67.
  - Teams at or above: 50 → 2; 40 → 5; 30 → 358; 25 → 1,066; 20 → 1,214.
- **Medal lines** (Kaggle medal table for 1000+ teams):
  - Gold: top 10 + 0.2% = 18.
  - Silver: top 5% = 204.
  - Bronze: top 10% = 409.
  - These counts use today's team count; entries close 10-26.
  - Medals come from the private board. The Rules say "potential winner(s) are determined solely by the leaderboard ranking on the Private Leaderboard".
- **You:** rank 855, 27.05, 24 submissions. Since 10-01:
  - 10-03: error (lexicon-view v1).
  - 10-05: 4.56 (lexicon v2 on sheetu).
  - 10-06: 24.95, and 10-08: 27.05 (lexicon view on Franzen M2).
- **Milestone 2 authors now:**
  - Daniel Franzen: 27.89, rank 711, 91 submissions. No higher draw in 3 submissions since his M2 run.
  - Lord Han Solo: 36.61, #15.
  - rellik13: 24.31, rank 1,110.
  - AFF AI CLUB, author of the D′ scheduler fork: 33.92, #29.
- **Official M2 announcement:** none on arcprize.org; its newest blog post is still the Astra post of 09-03. The board numbers above are Kaggle's.

## 2. What the three Milestone 2 winners published

| | Franzen (27.89, #1) | Lord Han Solo (23.84, #2) | rellik13 / sirikilohit (22.53, #3) |
|---|---|---|---|
| Model | Intel W4A16 AutoRound + Albucino INT4 MTP draft | primitive-ai mixed NVFP4-FP8 | Intel W4A16 AutoRound + RadixArk NVFP4 MTP |
| Server | SGLang Pennyroyal v2.5.3 + 5 patches | vLLM e975732 + patches | SGLang Pennyroyal v2.5.0 |
| Context | 128K; trim at ~118K down to ~59K | ~127K; trim to 81.5K | 70K; trim 57K → 45K |
| KV cache | FP8 | FP8 | FP8 |
| Scheduling | 10 slots; priority by level, actions, tokens; tail fade | 14 streams; 3,918 s per game | 16 streams; 2,400 s time slices |
| What they say moved the score | Better models; animation frames; 10× images, diff images, game-over frame; UNDO; retained Python functions; larger context; prefix-cache patch; scheduler. Turning the structured world model off worked best. Removing retained reasoning "leads to a large regression". | "The score closely followed the number of turns per game." He cannot confirm that any harness change helped. | FP8 KV + longer history: 14.49 → 22.53, with no prompt change. Adding prompt text hurt: 6.42 → 4.16 and 13.40 → 9.98. Fresh-context restart of a stuck level "bought nothing". Temperature 1.0, pruning experts (REAP) and Swift 1.5 were no better. |

Sources: [Franzen write-up](https://github.com/da-fr/arc-agi-3-solution/blob/main/WRITEUP.md) · [Lord Han Solo write-up](https://www.kaggle.com/writeups/lordhansolo/arc-agi-3-milestone-2) · [rellik13 write-up](https://github.com/LohitSiriki/arc-agi-3-milestone2-solution/blob/main/WRITEUP.md) · [comparison thread 744792](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/744792)

## 3. The noise floor: identical code on the public board

- **Single draws of unchanged Franzen v1 code:**
  - 27.89 (Franzen);
  - 27.62 (shiiin9, unchanged resubmission);
  - 27.80, then 21.01 on the next rerun of the same immutable version (skarin);
  - 27.83 (prvsiyan v16);
  - "4 times … 27–28" (xz, [746010](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/746010)).
- **First-day copies (Son Pham, [745062](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/745062)):** mean 25.77, SD 3.93, median 26.19.
- **Code-tab scores are best-of-version, not single draws.** Each is the best of all submissions of that notebook version:
  - Two notebooks byte-identical to Franzen v1 (sha256 `7b76c194…`) show 32.6 and 30.75.
  - A third, identical on the competition path, shows 31.76.
  - Franzen's page shows 34.3, a figure participants dispute in thread 746010.
- **Forks that change something score inside the same band.** These are Code-tab scores: the notebook's best submission, possibly from an earlier version than the current one.
  - D′ scheduler: 31.54 / 30.82 / 29.15.
  - "Multi-tier" prompt stack: 31.93.
  - World-model simulator DF-WM: 29.3.
  - Kinetic catalog: 29.68.
  - Your lexicon view: 24.95 / 27.05.
  - Diffs against v1 are in `analysis/2026-10-10/sources/fork-diffs-vs-dfranzen-v1.csv`.
- **The board's 25–36 band is what best-of-k draws of identical code produce.** Model: 1,213 teams that submitted on or after 10-01 and score ≥20, each team's best = max of k draws from N(25.77, 3.93).

  | | ≥30 | ≥33 | ≥36 |
  |---|---|---|---|
  | Observed | 358 | 66 | 18 |
  | k = 2 | 318 | 79 | 11 |
  | k = 3 | 444 | 116 | 17 |

  (`lb_model.py`)
- **What the private board can look like.** This is a model, not data. Assume 30 teams with real gains above a mass of copy-teams, each scored as the best of 2 selected draws.

  | Your true mean vs a copy | P(bronze, line ≈ 29.4) | P(silver, line ≈ 31.4) |
  |---|---|---|
  | +0 | 0.32 | 0.15 |
  | +2 | 0.56 | 0.33 |
  | +4 | 0.78 | 0.56 |

  Small real gains in the mean move medal odds a lot. Public-board luck does not.

## 4. New measurements: Franzen's 4 × 25 demo run

Input: output of `dfranzen/arc-agi-3-milestone-2-solution` v3, `benchmark.json` (sha256 `ea186291…`). It covers 100 game runs from one 8 h 11 m job on 2026-10-03, with each game's budget scaled to the competition's time per game. The competition path is identical to v1. The toolkit's scorer form reproduces 100 of 100 stored game scores. Script: `analysis/2026-10-10/report.py`.

- **Level and variance:**
  - Demo mean 46.49 (the same code averages about 26 on the hidden public board).
  - Pass means 45.80 / 45.59 / 47.46 / 47.12.
  - Within-game variance implies an SD of 3.06 for a 55-game score. The measured LB SD of copies is 3.93.
- **Throughput is near saturation at this budget:**
  - Cut the 67 budget-limited runs to 90% or 80% of their tokens and the mean falls only to 46.20 or 45.87.
  - That is about +0.26 demo points per +10% tokens.
  - Budget-limited runs complete 68 / 61 / 31 / 18 / 5 levels per token quintile.
- **Efficiency is not the gap.** Completed levels used a median 0.64× the human action count (quartiles 0.46 / 0.94), and 80% used ≤1×.
- **Stuck attempts eat the tokens:**
  - 36.2% of all generated tokens went into level attempts that never completed.
  - Chance of completing a level within 20K / 60K / 100K / 140K tokens: 0.42 / 0.78 / 0.88 / 0.89.
  - An attempt still open at 100K tokens finishes by 140K only 14.6% of the time.
- **Most stuck attempts are bad luck, not hard levels:**
  - 40 of the 67 unfinished attempts were on a level the same system completed in another pass.
  - The stuck attempt had already used a median 1.95× the tokens the successful passes needed.
  - 14 levels were never completed in any pass.
  - Taking each game's best pass would give 61.89 vs 46.49. That is the most this system could gain from removing attempt-level luck.
- **Restart estimates.** Leave-one-pass-out: a fresh attempt is drawn from the other passes on the same level. Actions already spent stay charged.

  | Policy | Net demo points |
  |---|---|
  | Restart with only the remaining budget (R = 100K / 120K) | −0.04 / +0.12 |
  | Restart at R = 100K with a fresh 80K budget, cost of extra tokens charged | +0.79 |
  | The same, also crediting later levels the rescue unlocks | +4.90 |
  | Restart earlier (R = 60K, fresh 80K): without / with later levels | −1.40 / +2.82; it cuts 41 slow successes |

  Model estimates; assumptions are listed in `policies.py`.
- **What a demo A/B can detect** (`ab_compare.py`, A/A test on the same run): 2 passes against 2 passes on 25 games gives 95% intervals of about ±6 to ±12 points; 1 pass against 1 gives about ±12 to ±16. A mechanism-level count, such as the share of fired restarts that complete their level, is the only reading sharp enough for this month.

## 5. What ARC's publications and the papers say about an "AGI-first", task-agnostic agent

- **The official methodology is unchanged since 2026-04-14:**
  - Level score `min((h/a)², 1.15)`, with h = human actions and a = agent actions.
  - Levels weighted by index, game score capped at the completed share, total = mean over games.
  - In competition mode, game resets become level resets and each environment can be made once. [methodology](https://docs.arcprize.org/methodology) · [changelog](https://docs.arcprize.org/changelog) · [competition mode](https://docs.arcprize.org/toolkit/competition_mode)
- **GPT-6 Astra** ([arcprize.org/blog/astra](https://arcprize.org/blog/astra), 09-03):
  - 62.7% on the Standard harness, 99.9% with the Provider Adapter harness. The adapter harness lets the model keep its reasoning state between requests and use compaction; ARC reports it was also about 3.66× faster and used 49% fewer tokens on the game-reasoning pairs both harnesses solved.
  - "Once frontier AI 'understands' the mechanics, it generally executes within the range of human efficiency."
  - Astra builds compact symbolic notes. Section 4 shows the same binary pattern in Flash-Next: completed levels at 0.64× human actions.
- **Model capability beats harness design.** [arXiv 2607.15439](https://arxiv.org/abs/2607.15439): gains from model capability and reasoning effort "often exceed variant differences". Replay verification ranks first but costs more.
- **Memory design matters for frontier models.** [PRO-LONG, 2607.20064](https://arxiv.org/abs/2607.20064) (programmatic memory over a full interaction log): +18.0 points over a base coding agent across frontier models, with 4.2–5.8× fewer tokens.
- **Executable world models** ([2605.05138](https://arxiv.org/abs/2605.05138)): 58.12% on the public 25 with GPT-5.5. Held-out performance is untested.
- **What this means on Kaggle:**
  - The task-agnostic recipe is already in the field's base: one code tool, retained reasoning, retained functions, frames and animations as data, and no game-specific logic.
  - Extra world-model or memory machinery on that base has not moved scores: Franzen turned his off; DF-WM, the kinetic catalog and the lexicon view score inside the noise band.
  - Capability per GPU-second is fixed by the model, and no stronger open model fits. As of 10-10 on Hugging Face:
    - DeepSeek-V4.1-Flash: 763B parameters.
    - GLM-5.3-Flash: 321B.
    - Qwen3.8-Flash-Next: 180B. It already needs its 95 GB per-layer embedding (PLE) table offloaded to host RAM.
  - What remains measurable and agnostic is the variance of the model's first hypothesis on a level (section 4).
- **Fine-tuning has no positive public evidence for Flash-Next** ([742835](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/742835)):
  - SFT on H200s with several teachers and recipes, on Flash-Next and on the 27B: no permutation made a meaningful improvement.
  - An RL pipeline on a full H200 node: no gain.
  - Same-model cloning on Qwen3.6-27B: +2 on public games, "didn't translate" to the hidden set.
  - The author of that RL pipeline says the RTX PRO 6000 cannot train a ~100B model, even with CPU offload and quantization.

## 6. Bets, ranked by expected private-score lift per unit of work

| # | Bet | Evidence | Falsifier | Kaggle-legal | Band if it works |
|---|---|---|---|---|---|
| 1 | **Final selection = two independent, healthy draws of the best-evidence configuration.** | Rules: "up to two (2) Final Submissions". Kaggle counts the better private score (standard behaviour; the rules text read here doesn't say so in words). Best of 2 independent draws = μ + σ/√π ≈ μ + 2.2. | None; this is arithmetic. It fails if both picks come from broken runs. | Yes | +2.2 over selecting one draw |
| 2 | **Stuck-level fresh restart on unchanged Franzen v1, behind an on/off flag.** | Section 4: 40 of 67 stuck attempts were solved in another pass; net estimate +0.8 (conservative) to +4.9 (with later levels) demo points. Counter-evidence: rellik13 reports a fresh restart "bought nothing" (few runs, different base). | In a 1–2-pass demo run, fewer than 25% of fired restarts complete their level (the model predicts about 60%), or restarts fire on more than 15% of level attempts (the model predicts 7%). Either way, drop it. | Yes | Hidden board +0.4 to +2.7, if demo gains scale proportionally (unverified) |
| 3 | **Team merger before 10-26** with a team holding a better-measured private configuration. | Rules allow mergers until 10-26. It is the only fast way to a different true mean. | No partner with replicated evidence. | Yes | Their mean |

**How to build bet 2 (map of Franzen's harness, `ARC3-Inference/inference/agent/tool_agent.py` in his patch):**

1. **Where to hook in.**
   - Each request first passes through `_trim_messages_for_context(...)`, then `_maybe_handover()`.
   - `_maybe_handover()` prices the game with `tokens = _session_generated_tokens − _tokens_at_level_start` and hands the slot back at a trim.
   - A trim already invalidates the prefix cache, so a restart at that point costs no extra prefill.
2. **What the restart does.** At a trim, if tokens on the level ≥ R = 100,000 and this level has not been restarted yet:
   - Drop every message since the level started, not just the oldest block.
   - Keep the system prompt, the retained functions and the current frame.
   - Add one line stating that the previous attempt on this level was cleared.
   - Set `_tokens_at_level_start` to the current session total, so the priority formula prices it as a fresh attempt.
   - Restart at most once per level.
3. **What not to add.** No new advice text: added prompt text measured negative twice (rellik13).
4. **Logging.** Log each restart with the level, tokens and actions at the cut, and whether the level then completed. The falsifier above reads those log lines.

**Don't spend the remaining 23 days on these** (evidence in sections 3–5):
- more throughput engineering: +0.26 demo points per +10% tokens;
- scheduler formula variants: D′ forks sit inside the copy band;
- prompt or world-model add-ons: Franzen's own ablations, rellik13's measured losses, and DF-WM, kinetic and lexicon all inside the band;
- fine-tuning Flash-Next: no positive report, and it needs an H200 node plus re-quantization;
- switching base model: nothing newer fits;
- chasing a public best-of-k: it does not carry over to the private board.

## 7. Calendar to 2026-11-02

1. **10-11 to 10-13:**
   - Build bet 2 on a copy of Franzen v1, without the lexicon cell, so changes are not stacked.
   - With the flag off, the code must behave byte-for-byte like v1.
   - Quick-save on 1–2 demo games to prove it boots.
2. **10-13 to 10-15:** run one 2-pass × 25-game demo run with the flag on (Franzen's 4-pass run took 8 h 11 m), then:
   - read the restart log against the falsifier;
   - run `ab_compare.py` against `data/dfranzen-m2-v3/benchmark.json`.
3. **Every daily slot until 10-31:** submit flag-on if it passed, otherwise unchanged v1. Judge nothing by a single LB draw.
4. **10-26:** entry and merger deadline.
5. **By 10-31:** make the last submission.
   - Queues of 6–17 h were reported between 10-05 and 10-08 ([745951](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/745951)), and the run itself takes up to 9 h.
   - The pages read here don't say whether a scored run must finish before the deadline, so plan as if it must.
6. **11-02:** select the finals.
   - Bet 2 passed and its paired demo interval excludes 0: two flag-on draws.
   - It passed but the interval includes 0: one flag-on and one base draw.
   - Otherwise: two base draws.
   - Whichever applies, skip a draw far below the configuration's mean (such as a 21-type draw). A broken run (outage, truncation) depresses both halves of the board.

## 8. Risks

- **Prize eligibility of Qwen3.8-Flash-Next (Qwen Community License, not OSI-approved).**
  - The Rules' Winner License section requires "open source system, open source model, and open source weights/parameters", but exempts "pretrained models with an incompatible license".
  - Two threads asking the host to rule are unanswered as of 10-10 ([745079](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/745079), [745837](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/745837)).
  - This affects the cash prizes, not medals.
- **Runs that ended early.** Runs that completed in 2–4 h instead of 9 h were reported on 10-01/02 ([744995](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/744995)). A participant links them to an outage Kaggle confirmed in another competition.
- **Dataset mount failures** on save were reported on 10-08 ([747438](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/747438)). Your notebook depends on Franzen's datasets and models: verify the mounts on every save.
- **Docker image for the rerun.** Per a participant, the default image has been Python 3.13 since 10-01. Your notebook and Franzen's pin the private image `sha256:57e612b4…`. Whether a rerun uses the pinned image has no host answer ([745654](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/745654)); one non-host reply says it does. Your 10-06 and 10-08 runs scored, so the current pin worked then.

## 9. What would change this memo

- **A host statement on the Qwen licence or on the rerun image:** update the risks.
- **A top-5 team publishing before 11-02:** fork it unchanged. Hundreds of teams copied Franzen's M2 notebook within 24 h ([745062](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/745062)), and Tufa's M1 release became the base of the high-scoring public notebooks.
- **A newer open model that fits 96 GB VRAM plus about 180 GB host RAM:** Franzen and rellik13 each report every model switch so far as a substantial improvement.
- **Bet 2 mechanism test:** conversion of fired restarts below 25% → drop bet 2; above 50% together with a non-negative paired demo delta → make it the default.

## 10. Sources

All were fetched on 2026-10-10; copies are in `analysis/2026-10-10/sources/`.

- **Kaggle:**
  - [leaderboard](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/leaderboard) (CSV via API, 17:12:56 UTC)
  - [rules](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/rules)
  - [timeline](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview/timeline)
  - [code requirements](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview/code-requirements)
  - [models tab](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/models)
  - [code tab by score](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/code?sortBy=scoreDescending)
  - [medal table](https://www.kaggle.com/progression/competitions)
- **Kaggle discussion** (append the ID to `https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/`):
  - 744792: comparison of the three M2 winners
  - 745062: variance of copies
  - 746010: Franzen's displayed score and xz's 4 runs
  - 744995: runs ending at 2–4 h
  - 747438: dataset mount error
  - 745951: queues
  - 745079, 745837: Qwen licence
  - 745654: Docker image
  - 742801: Tufa's reasons for not sharing
  - 742835: fine-tuning reports
  - 742940: self-generated data
  - 740812, 744365, 744545: top-team discussion
  - 746295: your lexicon-view post
- **Write-ups:**
  - [Franzen](https://github.com/da-fr/arc-agi-3-solution/blob/main/WRITEUP.md)
  - [Lord Han Solo](https://www.kaggle.com/writeups/lordhansolo/arc-agi-3-milestone-2)
  - [rellik13](https://github.com/LohitSiriki/arc-agi-3-milestone2-solution/blob/main/WRITEUP.md)
- **Notebooks:**
  - [Franzen M2](https://www.kaggle.com/code/dfranzen/arc-agi-3-milestone-2-solution) (v3 output used in section 4), plus the 14 notebooks listed in `sources/fork-diffs-vs-dfranzen-v1.csv`.
  - Data sources of all 41 public notebooks scoring ≥20: `sources/public-notebooks-score20plus-sources.json`.
  - [skarin 100-trajectory audit](https://www.kaggle.com/code/skarin/arc-agi-3-27-80-lb-100-trajectory-audit) (27.80 / 21.01)
  - [shiiin9 D′](https://www.kaggle.com/code/shiiin9/affectify-arc-31-54-in-a-single-sub)
- **ARC Prize:**
  - [competition page](https://arcprize.org/competitions/2026/arc-agi-3)
  - [blog index](https://arcprize.org/blog)
  - [Astra](https://arcprize.org/blog/astra)
  - [methodology](https://docs.arcprize.org/methodology)
  - [changelog](https://docs.arcprize.org/changelog)
  - [competition mode](https://docs.arcprize.org/toolkit/competition_mode)
- **Papers:** [2607.15439](https://arxiv.org/abs/2607.15439) · [2607.20064](https://arxiv.org/abs/2607.20064) · [2605.05138](https://arxiv.org/abs/2605.05138)
- **Models (Hugging Face API, parameter counts):**
  - [Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next)
  - [DeepSeek-V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash)
  - [GLM-5.3-Flash](https://huggingface.co/zai-org/GLM-5.3-Flash)
