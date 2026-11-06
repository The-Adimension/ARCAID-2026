# Data map for a Jev-style System One decision model (2026-09-27)

A Jev-style model reads a structured state and answers pre-declared typed questions:
- **Noul:** a yes/no probability;
- **Choice:** one of several options;
- **Score:** a number.

It answers them all in one forward pass, with calibrated probabilities, trained on (question, probability, ground truth). This note maps which ARC-AGI-3 data can supply those triples, and what each question is worth, measured where possible.

Jev itself is API-only (TypeSafe AI publishes no weights), so it cannot run in the offline Kaggle rerun. Only the concept transfers. The one open reconstruction, `kyegomez/open-jev` (Apache-2.0), is untrained.

## 1. Data in this repo

**Decision turns.** `inputs/jev/extract_turns.py` turns the 339 Duck transcripts into one record per model turn. Removing 149 duplicate copies leaves:
- 190 unique runs and **7,357 turns** across 25 games, with 6 games dominating;
- per turn: level, actions just executed, carried world model (goal, plan, open questions), reasoning, code, whether an action ran, and whether the level was later cleared;
- **503 run-levels** (316 cleared, 187 stuck);
- 30 game-levels that were cleared in some runs and failed in others.

**Replayable actions.** 28,159 unique actions replay to full frames on the pinned engine (`inputs/replay_system1.py`).

**Game sources.** `environment_files/` holds the 25 public games, which can generate unlimited transitions.

**Teacher rounds.** `arc3-collections/0393/rounds`, `memory/principles.md` and the per-game notes: Claude Opus teacher play over 13 rounds of about 15 decisions each. High quality, but small.

## 2. Public external data (checked 2026-09-27)

| Source | What | Size | Licence |
|---|---|---|---|
| **ARA Labs** (`AgentNativeResearchLab/arc-agi3-*`, 81 repos) | 17 harness/model setups (Opus 4.8, Fable 5, GPT-5.5, GPT-5.6 Sol, Gemini 3.1 Pro, Kimi K2.7, GLM 5.2, Grok 4.5, …) on 11 public games (ar25, ft09, g50t, ka59, lf52, ls20, r11l, s5i5, su15, tr87, wa30). See the ledger breakdown below the table. | 81 repos | **CC-BY-4.0**; training allowed with attribution |
| `fredericowieser/arc-agi-3-wm-traces` | (state, action, next_state, level_done) transitions. Includes human play (`hhazard`, 14.8K), `prior_games` (2.2K) and generated rollouts. | 14.6M rows | "other": check before use |
| `cveinnt/kepler-arc-agi-3-traces` | 50 runs that encode each game as a certified, executable `world_model.py` | 50 runs | MIT |
| `schema-harness/arc-agi-3-schema-traces` | 50 frontier-model trajectories (GPT-5.6 Sol, Claude Opus/Fable) | 50 | not stated on the card |
| `guanning/arc-agi-3-schema-traces-*` | Schema traces (Opus 4.8, GPT-5.6) | n/a | gated (manual approval) |

ARA Labs repos contain:
- a **prediction ledger** of 1,355 goal/mechanic hypotheses with stated confidence and a falsifiable condition, plus 1,305 later verdicts (580 refuted, 396 confirmed, the rest partial);
- 582 per-level "why"-traces (one line per action);
- 503 winning replay scripts.

## 3. Candidate typed questions, with measured value

| # | Typed question | Labels | Measured so far |
|---|---|---|---|
| Q1 | Noul: "will this action change the board?" | Exact and abundant (replays, 14.6M transitions, game sources) | Low ceiling: only 9.4% of actions are first-time no-ops, and a lookup saves 3.8% of tokens (`SYSTEM1-REPLAY`) |
| Q2 | Noul: "is this level going to be a wall?" (screen only) | Replays | AUC 0.65. Cannot separate a winning run from a losing run on the same level: identical in 587 of 587 pairs (`SURPRISE-WALLS`) |
| Q3 | Noul: "will this run clear this level?" (from the model's own text) | 7,357 turns | Early-turn AUC 0.71 within the same level, but **confounded by run config**: within the same config and level it is 0.52 (1,185 pairs). Too few same-config pairs to train on. "reading order" is a top "stuck" term, matching the walls study. |
| Q4 | Noul: "is the current goal hypothesis right?" and Choice: "which alternative reading next?" | **ARA ledger: 1,171 prediction/verdict pairs**, plus the carried world models in our turns | Frontier confidence is only partly calibrated: confirmed rate 0.29 (low), 0.38 (medium), 0.87 (high). About 60% of hypotheses end refuted. **Untested as a learned critic.** This is the only question aimed at the measured failure (wrong goal reading at walls). |
| Q5 | Noul: "act now, or keep thinking?" | 7,357 turns | 35% of turns execute nothing and they produce 43% of generated text. But 94% of those end on the 60 s turn-time slice while inspecting, not on errors, so the value is unmeasured. |

## 4. Kaggle-legal ways to run it

- **Prefill-only readout on the served Flash-Next model.** Ask the typed question, then read the answer-option logits from a single prefill, with no decoding.
  - Prefill is about 7.5% of GPU time and decode about 92.5%, so the extra cost is small.
  - Calibrate offline, for example with Platt scaling on the ledger and turns.
- **A small encoder on CPU.** The GPU has no spare memory (v3 logs show 42 MB free).
- **Data rules.** The data must be public: CC-BY-4.0 is fine with credit, and the "other" licence needs checking.
  - Every trace is from **public games**. The hidden 110 are different, so evaluate leave-one-game-out and treat hidden-set transfer as unproven.
  - Public-trained *policies* have not transferred before. A critic of hypothesis quality is a different target, but is equally unproven.

## 5. Next measurement (CPU only, about 2 h)

Build the Q4 dataset from the ARA ledger (hypothesis text, stated confidence, verdict) plus the goal/plan lines from our 7,357 turns. Then test leave-one-game-out whether a critic predicts "refuted" better than the model's own stated confidence.
- **If it does:** the critic is the Jev-style component worth wiring into a Duck variant.
- **If it doesn't:** this data can't support the idea.
