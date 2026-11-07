# Literature search for the Novelty criterion

**Searched:** 2026-11-07, two days before the Paper Track deadline.

**Why:** the rubric asks *"How novel is the Submission relative to existing public research?"*. This page records:
- what was searched and read;
- the closest public work to each part of our submission and analysis;
- what the paper can and cannot claim.

**Scope and limits:**
- This is a targeted search, not a systematic review.
- Most ARC-AGI-3 papers are 2026 arXiv preprints with self-reported, public-set scores.
- Other teams' Paper Track writeups are not public until the track closes.
- Kaggle discussion pages are rendered by JavaScript, and the one we tried could not be read.

## How it was done

- **Web searches** on six topics:
  - ARC-AGI-3 agents, harnesses and evaluation (2026);
  - object-centric perception and programmatic world models;
  - overthinking and budget control in LLM agents;
  - run-to-run variance and statistical testing in agent evaluations;
  - selection effects on leaderboards;
  - the term "datafication".
- **Reading:** the closest papers were fetched and read in their arXiv HTML versions (status column below). For long papers, the first 40,000–80,000 characters were read verbatim and the rest only as a model-written summary. Numbers that came only from such summaries are marked *(to verify)* and must be checked before the paper cites them.

## Our elements against the closest public work

| Our element | Closest public work | What is the same | What is different | What we can claim |
|---|---|---|---|---|
| **Lexicon view** (perception): the board as named multi-colour symbols at its true scale, objects, frame differences (`current_frame.code`, `.objects`, `.native`, `.changes_since`) | Object-based representations nearly doubled GPT-4 on ARC-AGI-1 tasks, 13 → 23 of 50 [W1]. SARBLOH gives an object inventory with tracking, a geometric briefing and an annotated map [A4]. OPINE-World builds object records [A7]. | Objects with identity across frames; change lists | Ours is an optional view inside the Duck sandbox. We tested it against the unchanged agent in paired level trials. | **Not a new idea.** New: a controlled ARC-AGI-3 test found no detectable effect on levels cleared (H1), and the gap equals the gap between identical runs on different days (Stage 5, P1). |
| **The view went unused** until the harness's prompt lines saying a frame exposes "only" five fields were edited: 0 of 1,130 tool calls, then 247 of 1,111 | Documentation drives tool use [W4] | Models use what the prompt says exists. | An ARC-AGI-3 harness's own prompt suppressed a new affordance. | We found no ARC-AGI-3 report of this. Descriptive, from one run each. |
| **Learned rules** (`current_frame.rules`): `when <action> [if/unless <relation>] then <change>`, learned from a level's recent steps | Programmatic world models written as code [W2, W3, A7, A8, A9]. Tycho: world model on vs off, +9.42 RHAE, one run per configuration [A8]. OPINE-World: belief layer removed, −20.24 [A7]. | Rules inferred from observed transitions | Ours is a fixed, game-agnostic grammar, never tested apart from the lexicon. | **Not new.** Do not claim. |
| **Probe-first governor** (economics) | See the three points below the table. | Making the budget visible each turn; trading thinking for acting | ARC-AGI-3 scores actions, not tokens, so the governor nudges toward cheap probes only while few actions have been spent, and caps tokens during streaks without a move. | **Not a new idea.** New: in a controlled ARC-AGI-3 test it gave a small supported gain (+4.9 points of levels cleared, Holm p = 0.044), but the behaviour it targets did not change measurably (post hoc, P4). We found no ARC-AGI-3 report that checks a governor's mechanism. |
| **Startup guard** (for zero scores caused by a slow model load) | A public repo on the same base sends RESET every 4 minutes until the model server is ready, and reports no 0.00 run since [K1]. | The same failure and a similar fix | Implementation details | **Not new.** Credit the parallel fix. |
| **Paired cold-start level trials:** each of the 183 public levels started from its own start, both arms in the same session, exact McNemar stratified by round | See the two points below the table. | Paired comparison on the same items | The unit is a single level started cold, with a binary outcome. This removes level difficulty, which is two-thirds of outcome variation (ICC 0.67, P1). | **The statistics are standard.** We found no ARC-AGI-3 study that pairs outcomes level by level with cold starts. |
| **A/A noise floor and calibrated power** (post hoc) | See the two points below the table. | Repeating identical configurations; power by simulation; ICC | A/A at level resolution, same day vs different days. The power model is calibrated to the observed A/A disagreement, and a first, uncalibrated model failed that check. | **Incremental.** We found no ARC-AGI-3 work that measures the noise floor of an add-on comparison, or the overstatement of a significant result. |
| **Engine replay of every recorded action:** 2,489 game-runs, 191,674 actions, all matching | Competition replay of traces for scorecards [A8]; replay checks of programmatic models [A7, A8] | Re-executing recorded traces | We use it to audit the analysis data. | Good practice, **not a novelty.** |
| **Score anatomy:** Franzen-based whole games lose about 98% of the lost score to uncleared levels; the 5× cutoff never binds (P5) | SARBLOH splits its lost points into unreached levels, attempted levels and action overhead *(to verify)* [A4]. The ARC-AGI-3 report argues for per-level visibility but gives no empirical split [A1]. | Splitting lost score into coverage and efficiency | Our runs clear far fewer levels than SARBLOH's best runs, and efficiency is only 1–2% of our loss. | Contemporaneous, **not new as an idea.** The share lost to inefficiency appears to depend on capability. |
| **Outcome disagreements fall at the time limit:** levels cleared by only one of two runs are cleared late in the trial, in A/A pairs as well (P5) | Trajectories diverge early in their tokens [S6] | — | We locate where outcomes disagree, not where trajectories diverge. | Possibly new; **post hoc and descriptive.** |
| **Selecting the best draws:** our two selected submissions are our highest leaderboard draws | Best-of-N selection inflates scores [S8]. Kaggle holdouts show little overfitting overall [S9]. Development gains overstate held-out gains [A6]. Community repos on the same base report single-draw SDs of 3.2–3.9 points [K1, K2]. | Selection from noisy draws | — | **Not new.** We disclose it (Stage 3, S3). |
| **Datafication framing** (DEITY): perception, economics and evaluation as three layers | The term [D1]; a critical view [D2]; the DEITY framework [D3] | — | Applied to agent design on ARC | A lens, not a result. **Claim modestly.** |

**Probe-first: the closest prior work.**
- Overthinking in agentic tasks: analysis paralysis, rogue actions, premature disengagement [E1].
- Scaling interaction steps rather than per-step reasoning [E2].
- The Budget Tracker, which appends a budget status block after each tool response; its budgets cap tool calls, not tokens [E3].
- Forcing or limiting reasoning length [E4].

**Paired level trials: the closest prior work.**
- ARC-AGI-3 studies mostly compare one whole-game run per configuration:
  - Rodionov: "a single playthrough per game cannot estimate run-to-run variability" [A5];
  - Tycho [A8] and NOOA [A9] also use one run per configuration.
- OPINE-World uses paired tests over games and several runs per condition in some experiments [A7].
- Lehmann & Vahdati use a sign test and bootstrap over lineages [A6].
- In general, McNemar is the standard test for paired binary comparisons [S1, S2]; paired differences are recommended for model comparisons [S3]; and McNemar is recommended for agent comparisons [S7].

**A/A noise and power: the closest prior work.**
- 10 runs per configuration on SWE-bench Verified: single-run pass@1 varies by 2.2–6.0 points, with a power table for the number of runs [S6].
- ICC(1,1) of 0.30–0.77 for agents on GAIA and FRAMES [S7].
- Ten evaluations of one ARC-AGI-3 harness: SD 3.99 RHAE [A6].
- Simulation-based power analysis [S4]; Type M error, the exaggeration ratio [S5].

## How the ARC-AGI-3 studies we read measured their effects

| Study | Configurations compared | Runs per configuration | Statistics | Noise measured? |
|---|---|---|---|---|
| SARBLOH [A4] | Perception formats (rubric scoring); one pair of full runs (briefing and map off: 143 levels; on, with other changes: 138) | 1 | None. Its Section 3 diagnostics are single trials. The paper itself says the two runs are "not a measured effect of perception". | No |
| Rodionov [A5] | Four nested harness variants × four model-effort settings | 1 playthrough per game | None | No; stated as a limitation |
| Lehmann & Vahdati [A6] | Harness H0 vs revisions, 27 lineages | 1, plus a post hoc 10-run check of one harness | Sign test (15 vs 12, p = 0.70); bootstrap over lineages; held-out gain +2.80 (−1.44 to 7.35) against +8.42 on development games | One harness: SD 3.99 |
| OPINE-World [A7] | Full system vs components removed | Up to 5 in some experiments | Wilcoxon signed-rank over games, sign-flip tests, paired bootstrap *(to verify)* | Not reported separately |
| Tycho [A8] | World model on vs off, and other policies | 1 | Per-game bootstrap intervals, which "reflect benchmark composition, not run-to-run variability" *(to verify)* | No |
| NOOA [A9] | Memory and skill ablations | 1 per game | None | No |
| **This work** | Lexicon on vs off; probe-first on vs off | 1 (lexicon) and 2 (probe-first) rounds of 183 paired level trials; 3 A/A controls | Exact McNemar, Holm, Newcombe interval, exact conditional odds ratio; pre-set sensitivity analyses; post hoc A/A, calibrated power, exact permutation | Yes: same day 13/13; different days 17/8 |

## What the paper can claim

**Not novel, and the paper must say so:**
- the lexicon view, the learned rules, probe-first and the startup guard as techniques;
- any of the statistical methods;
- priority for the score decomposition;
- anything about the hidden set beyond single leaderboard draws.

**What appears new, relative to the public work we found by 2026-11-07:**
1. **The design.** Add-ons tested on ARC-AGI-3 with paired cold-start trials of every public level, against a measured A/A noise floor and a power model calibrated to it.
2. **A controlled null for perception.** An object and symbol view showed no detectable effect on levels cleared, using the same open-weight model family as SARBLOH (Qwen3.8-Flash-Next). SARBLOH argues that perception governs ARC-AGI-3 on single-trial and single-run evidence [A4], and object views helped GPT-4 on ARC-AGI-1 [W1]. The view also went unused until the harness's own prompt stopped saying a frame has "only" five fields.
3. **A supported gain without its mechanism.** The budget governor gave a small gain that passed the pre-set test, while the behaviour it was built to change did not change measurably. This is a caution about attributing gains to mechanisms.
4. **Where the score is lost, and where comparisons are decided.** At this capability level nearly all lost score is uncleared levels. The levels that decide a comparison are cleared near the time limit, in A/A pairs too.

**Wording rule:** say "we found no prior ARC-AGI-3 study that …", not "the first".

**A possible Novelty sentence for the writeup:**

> Neither add-on is a new idea: object-centric views and learned rules (Xu et al.; OPINE-World; Tycho; SARBLOH) and budget-aware acting (Cuadron et al.; Shen et al.; Liu et al.) have clear precedents. What we add is measurement: in the ARC-AGI-3 work we found, no study tests add-ons with paired cold-start trials of every public level against a measured noise floor. Under that design, an object and symbol view had no detectable effect, and a budget governor gave a small gain without changing the behaviour it targets.

## Check before citing

- **SARBLOH:** its lost-points split and its Sections 4–6 were read only as a summary.
- **OPINE-World:** its Table 1 values and test details were read only as a summary.
- **Tycho:** its matched-study numbers other than the abstract's were read only as a summary.
- **Lehmann & Vahdati:** Tables 4 and 10–12 were read only as a summary.
- **NOOA:** its scores were read only as a summary.
- **The ARC-AGI-3 report's scoring.** Version 1 of the report gives a per-level cap of 1.0 and the second-best human as baseline. The scorer used here (`arc-agi` 0.9.8) and the methodology page use a cap of 1.15 and the median human (ARC Prize changelog, 2026-04-14), as recorded in `Documentation/records/2026-10-01__official-sources-vs-code.md`. Version 2 of the report (2026-04-17) was not read.
- **Mayer-Schönberger & Cukier [D1]:** the wording of their definition of datafication was not checked.
- **Tufa Labs' Duck write-up (Kaggle discussion 717133)** could not be read. A search snippet says it steered the model away from naming classical game sprites and reports large variance between repeated submissions. Unverified.

## References

**Status key:**
- **read:** the arXiv HTML or the page itself was read, partly verbatim, as described above;
- **abstract:** abstract or search results only;
- **known:** standard reference, not re-checked in this search.

### ARC-AGI-3 (2025–2026)

| # | Reference | Status |
|---|---|---|
| A1 | ARC Prize Foundation. *ARC-AGI-3: A New Challenge for Frontier Agentic Intelligence.* arXiv:2603.24621 (v1 2026-03-24). https://arxiv.org/abs/2603.24621 (= C4 in `Documentation/REFERENCES.md`) | read (v1) |
| A2 | ARC Prize Foundation. *ARC-AGI-3 Preview Agent Competition* results, 2025: StochasticGoose (Tufa Labs) first, 12.58%, 18 levels. https://arcprize.org/competitions/arc-agi-3-preview-agents | abstract; also A1 §6.1 |
| A3 | ARC Prize Foundation. *ARC Prize 2026: ARC-AGI-3 Milestone Prize #1.* https://arcprize.org/blog/arc-prize-2026-milestone-1 | abstract |
| A4 | Banwait HS. *Transforming Integer Grids to Spatial Intuition: Perception, Not Planning, Governs ARC-AGI-3* (SARBLOH). arXiv:2611.06793 (2026-11-04). https://arxiv.org/abs/2611.06793 | read |
| A5 | Rodionov S. *Do Coding Agents Need Executable World Models, Simplification, and Verification to Solve ARC-AGI-3?* arXiv:2607.15439 (v2 2026-08-27). https://arxiv.org/abs/2607.15439 | read |
| A6 | Lehmann J, Vahdati S. *Can LLMs Improve Their Own Harness? A Controlled Study on ARC-AGI-3.* arXiv:2610.30499 (2026-10). https://arxiv.org/abs/2610.30499 | read |
| A7 | Courtis D, Li W, Sanner S. *OPINE-World: Programmatic World Modeling with Ontology-error-Prioritized Interactive Exploration for ARC-AGI-3.* arXiv:2607.01531 (v3 2026-09-26). https://arxiv.org/abs/2607.01531 | read |
| A8 | Lehmann J, Aioanei A, Vahdati S. *Tycho: Active Abstraction with Programmatic World Models for ARC-AGI-3.* arXiv:2607.28287 (2026-07-30). https://arxiv.org/abs/2607.28287 | read |
| A9 | Furgale P, Klingler S, Nolan J, et al. (NVIDIA). *NVIDIA-labs OO Agents: Native Python Object-Oriented Agents.* arXiv:2607.20709 (2026-07-22). https://arxiv.org/abs/2607.20709 | read |
| A10 | Found but not read: *Prime Agent* (arXiv:2608.23552); *DiG-bench* (arXiv:2608.12593); *Algebraic World Model* (arXiv:2610.40503); *How Humans Learn Unfamiliar Worlds: A Think-Aloud Dataset on ARC-AGI-3* (arXiv:2610.34523); *The ARC of Progress towards AGI: A Living Survey* (arXiv:2603.13372); *ARC Prize 2025: Technical Report* (arXiv:2601.10904); VISTA (https://vista-research.github.io/); Paper Track repos *Identifying, Not Choosing, Goals* (https://github.com/hralm/arc-agi-3-paper-track-2026) and *What should an agent carry from one level to the next?* (rodriguescarson) | not read |

### Community work in the same competition, on the same base

| # | Reference | Status |
|---|---|---|
| K1 | hammadfarooq-ai. *arc-prize-2026-arc-agi-3* (README): keepalive at startup, think-close guard; single-draw SD ≈ 3.9; best public LB 31.47. https://github.com/hammadfarooq-ai/arc-prize-2026-arc-agi-3 | read |
| K2 | Rodrigues C. *arc-agi-3* (README): level memory on the Duck/Franzen harness; 13 public-LB draws, mean 26.35 (SD 3.18). https://github.com/rodriguescarson/arc-agi-3 | read |
| K3 | Son Pham. Franzen copies' variance, Kaggle discussion 745062 (= K2 in `Documentation/REFERENCES.md`) | cited earlier |

### Perception and world models

| # | Reference | Status |
|---|---|---|
| W1 | Xu Y, Li W, Vaezipoor P, Sanner S, Khalil EB. *LLMs and the Abstraction and Reasoning Corpus: Successes, Failures, and the Importance of Object-based Representations.* TMLR 2024; arXiv:2305.18354. | abstract |
| W2 | Tang H, Key D, Ellis K. *WorldCoder, a Model-Based LLM Agent: Building World Models by Writing Code and Interacting with the Environment.* NeurIPS 2024; arXiv:2402.12275. | abstract |
| W3 | Piriyakulkij WT, Liang Y, Tang H, Weller A, Kryven M, Ellis K. *PoE-World: Compositional World Modeling with Products of Programmatic Experts.* NeurIPS 2025. | abstract |
| W4 | Hsieh C-Y, et al. *Tool Documentation Enables Zero-Shot Tool-Usage with Large Language Models.* arXiv:2308.00675 (2023). | abstract |

### Thinking, acting and budgets

| # | Reference | Status |
|---|---|---|
| E1 | Cuadron A, et al. *The Danger of Overthinking: Examining the Reasoning-Action Dilemma in Agentic Tasks.* arXiv:2502.08235 (2025). | abstract |
| E2 | Shen J, Bai H, Zhang L, Zhou Y, Setlur A, Tong S, Caples D, Jiang N, Zhang T, Talwalkar A, Kumar A. *Thinking vs. Doing: Agents that Reason by Scaling Test-Time Interaction.* arXiv:2506.07976; NeurIPS 2025. | abstract read |
| E3 | Liu T, Wang Z, Miao J, et al. *Budget-Aware Tool-Use Enables Effective Agent Scaling.* arXiv:2511.17006 (v1 2025-11-21; v2 2026-08-17, COLM 2026). | read |
| E4 | Muennighoff N, et al. *s1: Simple test-time scaling.* arXiv:2501.19393 (2025). | known |

### Evaluation and statistics

| # | Reference | Status |
|---|---|---|
| S1 | McNemar Q. Note on the sampling error of the difference between correlated proportions or percentages. *Psychometrika* 1947;12:153–157. | known |
| S2 | Dietterich TG. Approximate statistical tests for comparing supervised classification learning algorithms. *Neural Computation* 1998;10(7):1895–1923. | known |
| S3 | Miller E. *Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations.* arXiv:2411.00640 (2024). | abstract |
| S4 | Card D, Henderson P, Khandelwal U, Jia R, Mahowald K, Jurafsky D. *With Little Power Comes Great Responsibility.* EMNLP 2020; arXiv:2010.06595. | abstract |
| S5 | Gelman A, Carlin J. Beyond power calculations: assessing Type S (sign) and Type M (magnitude) errors. *Perspectives on Psychological Science* 2014;9(6):641–651. | abstract |
| S6 | Bjarnason BH, Silva A, Monperrus M. *On Randomness in Agentic Evals.* arXiv:2602.07150 (v2 2026-03-23). | read |
| S7 | Mustahsan Z, Lim A, Anand M, Jain S, McCann B. *Stochasticity in Agentic Evaluations: Quantifying Inconsistency with Intraclass Correlation.* arXiv:2512.06710 (2025-12-07). | read |
| S8 | Singh S, et al. *The Leaderboard Illusion.* arXiv:2504.20879 (2025); NeurIPS 2025. | abstract |
| S9 | Roelofs R, Shankar V, Recht B, Fridovich-Keil S, Hardt M, Miller J, Schmidt L. *A Meta-Analysis of Overfitting in Machine Learning.* NeurIPS 2019. | abstract |
| S10 | Shrout PE, Fleiss JL. Intraclass correlations: uses in assessing rater reliability. *Psychological Bulletin* 1979;86(2):420–428. | known |

### Datafication

| # | Reference | Status |
|---|---|---|
| D1 | Mayer-Schönberger V, Cukier K. *Big Data: A Revolution That Will Transform How We Live, Work, and Think.* Houghton Mifflin Harcourt, 2013. | known; wording not checked |
| D2 | van Dijck J. Datafication, dataism and dataveillance: Big Data between scientific paradigm and ideology. *Surveillance & Society* 2014;12(2):197–208. https://doi.org/10.24908/ss.v12i2.4776 | abstract |
| D3 | Anwer S. The Adimension: the DEITY principles framework. *EHJ – Imaging Methods and Practice* 2026;4(1):qyaf038 (= F1 in `Documentation/REFERENCES.md`) | own work |
