# RubiQ and AGI: what it can and cannot enable, 2026-10-11

**Question:** how can RubiQ (`RubiQ_20260427.zip.zip`, sha256 `df1a48b3…`) enable a new track or approach to AGI?

**Method:** read the code, recomputed its group, and ran three probes on the 25 public ARC-AGI-3 games with the pinned engine. Scripts, outputs and their limits are in `analysis/2026-10-11-rubiq/`.

## Answer

- **As uploaded, RubiQ cannot enable an AGI track.**
  - It is a federated-learning image classifier for CIFAR.
  - Its central claim is that choosing modules by a Rubik's-cube group beats choosing them at random. Its own reported results do not show that: 0.2144 vs 0.2144 at α = 0.1 and 0.2807 vs 0.2813 at α = 0.5, on 3 seeds.
  - Its comparison could not show it either way, because the random control differs from RubiQ in module types, parameter count and warmup (§2).
  - It measures none of the four capabilities ARC-AGI-3 tests: exploration, modelling, goal-setting, planning.
- **Of its three ideas, two can be tested on ARC-AGI-3. I tested both.**
  1. **Sharing learned code across clients (the federated idea).** Across games there is almost nothing to share.
     - The model's helper-function definitions are 2.96% of all generated tokens.
     - Definitions that recur in another game are 0.14%.
     - At the measured value of tokens, that is worth about 0.004 demo points.
  2. **Treating actions as group elements (the permutation algebra).** This structure exists, but only in part.
     - In 14 of 25 games, some action is cyclic on some level: repeating it returns the board. In 3 games every live action is.
     - 15 of the 40 stuck-but-solvable level attempts in Franzen's run start on such a level.
     - Plain search with the game's true dynamics solved none of 16 stuck levels with cyclic actions within 4,000 expanded states. Nine hit the budget with thousands of distinct states seen; seven exhausted the move set I gave it, so for those the result is a lower bound. Human solutions run to 26–424 actions.
     - The structure helps only if a planner decomposes it. Nothing here shows that would beat the LLM agent.
- **The one defensible track is a research track, not a lever before 2026-11-02:** inducing an algebraic model of the actions from the agent's own history, then planning over it (§6).
  - It reuses RubiQ's permutation code, and needs none of the federated or network parts.
  - It has a pre-registered falsifier.
  - For the competition, the 2026-10-10 memo stands.

## 1. What RubiQ is (read from the code)

- **Model and data.**
  - A small CNN feature extractor feeds 27 residual MLP modules on a 3×3×3 lattice, then a linear classifier.
  - Module width depends on position: corner 96, edge 64, face centre 48, core 32 (`harness.py` 158–165, 258–271).
  - Ten clients get CIFAR-10/100 split by a Dirichlet draw; 30 rounds, 5 of them warmup.
- **Which modules train each round** (lines 191–197, 237–250, 513–521):
  - Each client trains 8 of the 27 modules.
  - The 8 come from a permutation that composes a public "server" element with a per-client element.
  - Each element is a word of exactly 15 (client) or 10 (server) moves, chosen by HMAC-SHA256 bytes, over 18 generators: quarter turns of the 9 layers in either direction.
  - The permutation is applied to a fixed 8-position "canonical path".
- **Inside the lattice:** modules in the same x-layer are averaged, and the layers are applied in order (lines 282–289).
- **Aggregation:** each module is averaged over the clients that trained it. The non-lattice weights are averaged over all clients.
- **Methods compared:** `rubiq`; `random_csi` (8 modules chosen at random); FedAvg, FedProx, SCAFFOLD and FedAvgM on a parameter-matched MLP.

## 2. Does its evidence support its claim? No, and the test cannot

Group facts below come from `rubiq_group.py`; the rest is read from the code.

| Finding | Evidence |
|---|---|
| The parity filter never rejects a client | All 18 generators are even permutations (two 4-cycles each), so every product is even (lines 213–226, 517–519). |
| The core module never trains after warmup | Every generator fixes position 13, (1,1,1), and the canonical path does not contain it. 0 activations in 100,000 client-rounds. |
| Every RubiQ set has the same composition | The group's orbits are exactly the position types: 8 corners, 12 edges, 6 centres, 1 core. Group order 231,760,134,144,000. Every active set is 3 corners + 4 edges + 1 centre, so RubiQ always trains 201,280 lattice parameters. There are 75,335 distinct sets over 100,000 client-rounds, and per-module frequency ranges from 16,430 to 37,836. |
| The random control is not matched | `random_csi` includes the core 29.6% of the time. Only 7.5% of its sets have RubiQ's type mix. Its trained parameters range 119,808–247,552 (mean 184,789), so RubiQ trains about 9% more per round. |
| Warmup is not symmetric | In warmup RubiQ trains all 27 modules, while `random_csi` stays at 8 (lines 513–516 ignore `full`). The docstring claims symmetric warmup. |
| Training and testing differ | Both lattice methods train 8 modules but are evaluated with all 27 (`LatticeModel.forward` default; `_evaluate` calls `model(imgs)`). |
| Nothing is secret | The HMAC keys are the strings `client_k` and `rubiq_public_seed_v1`, so the selection schedule is public. |
| Statistics | `aggregate.py` promises a per-class win count it never computes. With 3 seeds, a one-sided bootstrap p of 0.0000 means only that all 3 differences share a sign. CIFAR-100 is normalised with the CIFAR-10 mean (line 352). |
| Results in hand | The uploaded zip contains no result files. The only results are the earlier record's 36-run CIFAR-10 sweep: RubiQ = random to within 0.0006. They were not re-run here (no torch or GPU in this session). |
| The baseline is fair on size | FairBaseline hidden width 671 gives 623,487 MLP parameters against 623,744 for the lattice (formula at lines 326–333). |

The group machinery in RubiQ itself is correct. The claim it is meant to support has not been tested, because the control changes several other things at once (§7 lists the fixes).

## 3. Mapping RubiQ's parts to AGI and ARC-AGI-3

| RubiQ part | Closest established idea | ARC-AGI-3 capability | Tested here | Result |
|---|---|---|---|---|
| Permutation algebra: compose, invert, words over generators | Planning over a puzzle's move graph; solving the Rubik's cube by search ([arXiv 1805.07470](https://arxiv.org/abs/1805.07470)) | Modelling, planning | Yes (§4, §6) | Structure present in part; plain search does not solve the stuck levels |
| Group-indexed choice of modules | Equivariant networks ([arXiv 1602.07576](https://arxiv.org/abs/1602.07576)); mixture-of-experts sparse activation | None directly (a network design choice) | Indirectly: its own CIFAR test | No effect over random selection |
| Federated averaging of sparse module updates | Sharing skills across tasks at test time | Skill-acquisition efficiency (Chollet, [arXiv 1911.01547](https://arxiv.org/abs/1911.01547)) | Yes (§5) | Almost nothing reusable across games |
| HMAC-keyed schedule | Pseudorandom scheduling | None | n/a | Keys are public; no property for AGI |

A related outside observation: ARC reports that GPT-6 Astra wrote "compact algebraic notation" for game state and controls ([arcprize.org/blog/astra](https://arcprize.org/blog/astra)). Representing mechanics algebraically is something strong agents do. RubiQ's permutation code is one concrete form of that idea.

## 4. Probe 1: do ARC-AGI-3 actions behave like group elements?

`action_algebra.py` probed 143 level-start states: every level start that Franzen's best run of each game reached.
- **Per action:** no-op or not, colour histogram preserved or not, order up to 12, inverses among the available actions, and whether pairs commute.
- **Two comparisons:** the exact grid, and the interior with a 4-cell border removed. In tr87 and ft09 the only cells that differ after a cycle completes are 3–4 cells of the bottom row, a step counter.

| Reading | Result |
|---|---|
| Exact grid | No game is group-like. In 1 game (re86) one action has an inverse once. Every return to a start state is spoiled by the step counter. |
| Interior grid | 14 of 25 games have a cyclic live action on some level. |
| Fully cyclic games | tr87 (24/24 live actions; orders mostly 7), ft09 (38/38 clicks), tn36 (6/6 clicks). |
| Partly cyclic games | lp85 21/37; cn04 18/56; dc22 10/25; ar25 7/37; re86 7/40; m0r0 6/27; sc25 5/29; ka59 2/25; ls20 2/14; s5i5 1/30; sb26 1/1 |
| Never cyclic in this probe | 11 games: bp35, cd82, g50t, lf52, r11l, sk48, sp80, su15, tu93, vc33, wa30 |
| UNDO (ACTION7) restores the interior | ar25 17/24, sk48 3/3, bp35 0/4, lf52 0/8 |
| Stuck-but-solvable attempts on a cyclic level | 15 of 40 (interior); 0 of 40 (exact) |
| Never-solved attempts on a cyclic level | 9 of 27 (interior); 5 of 27 (exact) |

So the structure RubiQ manipulates does exist in a minority of mechanics: toggles, rotations and cyclic recolourings. It is neither universal nor dominant.

## 5. Probe 2: is there anything to share across games?

`helper_reuse.py` read 100 transcripts of Franzen's run: 9,271 Python tool calls and 6,086 function definitions.
- **Helper definitions overall:** 530,696 tokens (characters/4), 2.96% of the 17.95M generated tokens.
- **Re-defined within the same run:** 1,215 definitions, 0.29% of tokens. Franzen's harness already keeps functions for the rest of the game.
- **Recurring in another game:**
  - exact matches: 83 of 4,871 unique definitions, 0.01% of tokens;
  - near-duplicates (bigram Jaccard ≥ 0.8): 656, 13.5% of definitions but 0.14% of tokens.
- **Most common helper names:** crop 89, bfs 83, ok 68, run 48, solve 45. They are generic, but they are short.
- **Value:** the 2026-10-10 analysis measured +0.26 demo points per +10% tokens. On that scale, removing every duplicated helper is worth about 0.004 demo points, and removing all helper writing about 0.08.

Conclusion: there is no meaningful federated or skill-sharing gain to collect across games at this level.

## 6. Probe 3: ceiling for planning over the action structure

`oracle_bfs.py` searched breadth-first with the true engine. It is an oracle that no competition agent has; it measures the best case for "know the actions exactly, then search". It covered the 16 stuck levels that have cyclic actions (the 11 levels behind the 15 recoverable attempts, plus 5 never-solved levels), with up to 4,000 expansions and 240 s per level.

| Level | Result | Distinct states seen | Human baseline (actions) |
|---|---|---|---|
| ar25 L6 | budget | 3,550 | 159 |
| cn04 L2 | budget | 16,715 | 54 |
| cn04 L5 | budget | 16,550 | 208 |
| dc22 L4 | move set exhausted | 48 | 98 |
| dc22 L5 | move set exhausted | 240 | 324 |
| ft09 L5 | move set exhausted | 128 | 65 |
| ka59 L6 | budget | 4,557 | 132 |
| ls20 L5 | budget | 1,820 | 96 |
| m0r0 L6 | budget | 1,866 | 237 |
| re86 L7 | budget | 10,423 | 424 |
| re86 L8 | budget | 7,207 | 241 |
| sc25 L4 | move set exhausted | 1,356 | 83 |
| sc25 L5 | move set exhausted | 128 | 143 |
| tn36 L2 | move set exhausted | 2 | 72 |
| tn36 L3 | move set exhausted | 2 | 26 |
| tr87 L6 | budget | 7,677 | 146 |

None was solved:
- **Nine ran out of budget** with 1,820–16,715 distinct states.
- **The "move set exhausted" rows are a limit of my probe,** not proof that the level is unsolvable: their key clicks are not at component centres.
- **Even with perfect knowledge of the dynamics, brute-force search over these move graphs does not reach the goal within thousands of states.** A group-based planner would need to decompose the state into independent cyclic parts, which is the useful content of group theory here. Nothing in this repo or in published ARC-AGI-3 work shows such a planner beating the LLM agent.

## 7. What a real track would look like

**Algebraic world-model induction.** A research track for ARC-AGI-3-style agents, after the competition.

- **Mechanism, passive and free in actions:**
  - Hash the interior grid at every observed state.
  - From the agent's own history, detect when a state recurs. From the action words that close those loops, infer each action's order, its inverses, and which actions commute.
  - Represent the mechanics as generators acting on cells: RubiQ's `compose`/`invert`/word evaluation, generalised from 27 lattice positions to board cells.
  - Plan by factoring the state into independent cyclic components (for example per-cell toggles of order k), solving each, and checking the plan against the observed history before acting.
- **Why it is AGI-relevant:**
  - It targets ARC's "modelling" and "planning", and skill-acquisition efficiency: inferring structure from a few interactions and reusing it.
  - It is general rather than game-specific.
  - It is the same move Astra makes in notation.
- **Pre-registered test** on the 25 public games, then any held-out games:
  - Fed only states observed in Franzen's 100 recorded trajectories, the inducer must predict the order and inverse of each cyclic action with at least 90% accuracy, scored against `results/algebra.json`.
  - On the 15 stuck attempts that start on cyclic levels, an LLM agent given the induced model as a tool must complete at least 5 within the tokens those attempts spent.
  - Either failing ends the track.
- **Cost and timing:**
  - About 1–2 weeks to build the inducer and the decomposition planner, and to wire them into the Duck harness as a tool.
  - Not feasible to validate before 2026-11-02, given the noise floor in the 2026-10-10 memo and one submission a day.
  - Treat it as post-competition research.
- **What it does not need from RubiQ:** the federated training, the lattice network, the HMAC schedule and the CIFAR benchmark.

## 8. Fixes RubiQ needs before its own claim can be tested

1. **Match the control on what it activates.** Draw random sets with RubiQ's type mix (3 corners, 4 edges, 1 centre) so the trained parameters are equal. Also run RubiQ with a position-type-preserving random permutation, which isolates "group order" from "type mix".
2. **Make warmup symmetric:** honour `full` for `random_csi`.
3. **Fix the core:** let it be selected, or document that it never trains after warmup. It is still used at evaluation.
4. **Evaluate the way you train:** evaluate with sparse active sets, or report both full and sparse evaluation.
5. **Use enough seeds:** at least 10 per cell, and report the paired difference with a t-interval as well as the bootstrap. 3 seeds cannot support a p-value.
6. **Clean up the claims:** remove the unused parity filter, or use a group that contains odd permutations; implement or delete the per-class win count; use the CIFAR-100 mean; drop any privacy claim, since the keys are public.

## 9. Sources

- **RubiQ code:** `RubiQ/bench/harness.py`, `aggregate.py`, `run_sweep.py`, `README.md` from the upload, cited by line.
- **Earlier record of this repo:** `corpus/AGI-RUBIQ-CORPUS-2026-10-01.md` (CIFAR results), `corpus/OFFICIAL-SOURCES-VS-CODE-2026-10-01.md` §2.2.
- **ARC-AGI-3 engine and games:** arc-agi 0.9.8, arcengine 0.9.3; `inputs/official-input-arc-prize-2026-arc-agi-3/environment_files`.
- **Trajectories:** Franzen's 4×25 run, `analysis/2026-10-10/data/dfranzen-m2-v3/benchmark.json`, and the transcripts in the output of `kaggle.com/code/dfranzen/arc-agi-3-milestone-2-solution`.
- **Papers** (arXiv IDs checked against the arXiv API on 2026-10-11):
  - Cohen & Welling 2016, *Group Equivariant Convolutional Networks*, 1602.07576;
  - McAleer et al. 2018, *Solving the Rubik's Cube Without Human Knowledge*, 1805.07470;
  - Chollet 2019, *On the Measure of Intelligence*, 1911.01547.
- **ARC Prize:** [arcprize.org/blog/astra](https://arcprize.org/blog/astra) (algebraic notation); [arcprize.org/competitions/2026/arc-agi-3](https://arcprize.org/competitions/2026/arc-agi-3) (the four capabilities).
