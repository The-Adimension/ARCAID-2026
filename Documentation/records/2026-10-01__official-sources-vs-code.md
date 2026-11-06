# Official ARC-AGI-3 sources vs the code in hand (2026-10-01)

This record states three things:
- what the code does (RubiQ, `rubiq_lineage`, the official toolkit, engine and repos);
- what the official ARC-AGI-3 sources require;
- the gaps between them.

Where a page and the code disagree, both sides are kept. Nothing here adopts a component, reports a playthrough, or states a private score. Rows: `corpus/rows-2026-10-01-official.jsonl`.

## Sources read

| Source | Identifier read |
|---|---|
| Docs index and pages | `docs.arcprize.org/llms.txt`; 59 of 60 linked pages as raw markdown. `api-reference/openapi.json` returns 404. |
| Docs source repo | `arcprize/docs` @ `6956cde` (2026-08-25). Matches the live pages (token similarity 0.97–0.99; only front-matter titles differ). |
| Technical report | arXiv:2603.24621 v2 (17 Apr 2026; v1 24 Mar 2026), "ARC-AGI-3: A New Challenge for Frontier Agentic Intelligence". The `arcprize.org/media/ARC_AGI_3_Technical_Report.pdf` copy has the same content. |
| arcprize.org | `/arc-agi/3`, `/competitions/2026/arc-agi-3`. The leaderboard pages render client-side. `media/data/leaderboard/v3.json` (generatedAt 2026-09-30T13:12Z) is served by arcprize.org; its URL came from `memo-2026-09-26.md`, not from the page's static code. |
| Toolkit | `arcprize/arc-agi` @ `f12822c` (0.9.9). The competition-pinned PyPI wheel `arc_agi-0.9.8` is byte-identical in `scorecard.py`, `api.py`, `base.py`, `local_wrapper.py`, `wrapper.py`, `models.py` and `server.py`. |
| Engine | `arcprize/arcengine` @ `b495c6a`. Equals the PyPI wheel `arcengine-0.9.3` in `base_game.py`, `enums.py` and `level.py`. |
| Agents | `arcprize/arc-agi-3-agents` @ `4743e7d`. The Kaggle-bundled copy in `inputs/official-input-…/ARC-AGI-3-Agents` differs in 12 entries. |
| Kaggle starter | `arcprize/arc-agi-3-kaggle-starter` @ `eeb1535` |
| Benchmarking | `arcprize/arc-agi-3-benchmarking` @ `09a307b` (2026-09-30) |
| Community leaderboard | `arcprize/arc-agi-community-leaderboard` @ `f0ea936` |
| Kaggle | Competition metadata via `GET /api/v1/competitions/list`. The rules and Evaluation pages are JavaScript-only and were **not readable**. |
| Related work | arXiv abstracts only: 2605.05138, 2607.15439, 2607.01531, 2609.39140 |
| In hand | `rubiq20260427.zip`, `RubiQ-benchmark.ipynb` outputs, `rubiq_lineage` package, corpus rows at `4a00984` |

The official repos were found by collecting every `github.com/arcprize/…` link in the pages, report and repos above. The GitHub org listing is not reachable from this session.

## 1. What the official sources require

### 1.1 Environment and interaction

- **Frame:** "a 64x64 grid" of 16 colours (report §2.3.1). The game schema says "Maximum 64x64", with values 0–15 and (0,0) at top-left. A turn may return a frame *sequence* (animation; report §2.3; schema). The engine renders every frame until an action resolves, capped at `MAX_FRAME_PER_ACTION = 1000`.
- **Actions:** `RESET` and `ACTION1`–`ACTION7`.
  - `ACTION6` takes x,y in 0–63; `ACTION7` "will always be an undo action" (actions page; API reference).
  - Each frame lists `available_actions`. After a game over only `RESET` is valid; the API returns 400.
  - The LLM-agents page says agents return `RESET`/`ACTION1`–`ACTION6`, and its parse regex is `ACTION[1-6]`. **Kept as a page-vs-page disagreement.**
- **What counts as an action:** turns that affect the environment. Tool calls, reasoning and retries do not count (methodology; report §2.3.2).
- **States:** `NOT_PLAYED`, `NOT_FINISHED`, `WIN`, `GAME_OVER`.
- **IDs:** game IDs are `<4-char name>-<version>`. Levels: "at least six levels per environment" (report §3.4).
- **Recording schema (docs, Recordings):** JSONL `{timestamp, data:{game_id, state, levels_completed, win_levels, action_input:{id, data, reasoning}, guid, full_reset, available_actions, frame}}`.

### 1.2 Scoring (RHAE)

| Item | Official statement | Where |
|---|---|---|
| Level score | `(h/a)²`; a level "can receive at most 1.15" | Methodology page |
| Level score | Eq. (1): `S = min(1.15, h/a)²`, which allows up to 1.3225 | Report §4.1 |
| Level score | "between 0% … and 115%" | Report §4.1, prose next to Eq. (1) |
| Level score | `min((b/a)² × 100, 115)` | Toolkit `scorecard.py` (pinned 0.9.8 = 0.9.9) |
| Cap history | per-level cap "increased from 1.0x to 1.15x" on 2026-04-14 | Changelog |
| Environment score | Level-index-weighted mean, capped at the weighted share of completed levels | Methodology; report Eq. (2); toolkit |
| Total | Mean over all environments. In competition mode, environments never played are created at close and score 0. | Methodology; report Eq. (3); toolkit `api.py` |
| Human baseline | "upper median human (by fewest actions)" per level, first-time players | Methodology; report §4.2, §5.3.2 |
| Human baseline | "now uses the median human per level (previously 2nd best human)" | Changelog 2026-04-14 |
| Testers | "Exactly 10 members of the public are tested on each environment" (§4.2). An environment is included only if fully solved by "at least two" testers (§5). | Report |
| Action budget | "five times the human-baseline median … the agent is terminated after 5n actions", for official-leaderboard evaluation | Report §4.3 |

**The report disagrees with itself.** Eq. (1) caps the ratio before squaring; its prose, the methodology page and the scorer code cap the score at 1.15. Recomputing every stored game run in this repo reproduces the scorer's form on 269 of 269 runs; the Eq. (1) form fails on 40 (row DV-06).

### 1.3 Datasets and leaderboards (report §3.6, §4.3)

- **Datasets (Table 1):**
  - Public Demo: 25, intentionally easier, and they "do not comprehensively represent the mechanics found in the private set".
  - Semi-Private: 55, for testing frontier models behind an API.
  - Fully Private: 55, "used for the competition".
- **Official leaderboard:**
  - it "will never report public set scores";
  - it "will not use a harness to report official scores", and runs one system prompt with no tools;
  - it discounts task-specific and domain-specific overfitting, including training on "synthetically generated ARC-AGI-3 lookalike environments".
- **Community leaderboard:** self-reported and unverified. Its repo collects a `scorecard_url` for ARC-AGI-3 but displays no self-reported scores.
- **Human-replay harness:** ARC Prize says it is "releasing an open-source 'harness' which scores 100% on all public environments, using human replay".

### 1.4 Competition mode and Kaggle

- **Competition mode (docs; toolkit `api.py`):**
  - environments are reached through the API;
  - game resets become level resets;
  - each environment can be `make`d once, under one scorecard;
  - `get_scorecard` is refused while the run is in flight;
  - scoring covers all environments.
- **Two runs per submission (docs, ARC Prize 2026):** "Phase A: Save & Run All", then "Phase B: Competition Rerun … Your agent plays the hidden game set". The `arc-agi` PyPI package "hosts the same game engine the Kaggle gateway runs".
- **Rerun mechanics (starter `build_notebook.py`):**
  - the notebook waits for `http://gateway:8001` and runs the agent with `OPERATION_MODE=online`;
  - recordings go to `RECORDINGS_DIR=/kaggle/working/server_recording`;
  - "The gateway records every action and emits submission.parquet".
  - Outside the rerun it writes a dummy parquet `[row_id, game_id, end_of_game, score]`. All 31 `submission.parquet` files in this repo are that one placeholder (one hash).
- **Pinned toolkit:** arc-agi 0.9.8 and arcengine 0.9.3, CPython 3.12 (`list_of_wheels.md`).
- **Kaggle metadata (API):**
  - reward $850,000;
  - deadline 2026-11-02 23:59 UTC;
  - merger and new-entrant deadlines on 2026-10-26;
  - 1 submission per day, teams of up to 8, kernel-only submissions;
  - metric "ARC-AGI-3 Metric" (custom, defined on the Evaluation tab, not readable here);
  - `awardsPoints: true`.
- **arcprize.org competition page:**
  - prizes: $850K total, Grand $700K, Top Score $75K, Milestones $75K;
  - "No internet access during evaluation";
  - open source required for prizes;
  - "Hardware and compute limits will be announced with the competition launch". The page itself states none.
- **The four tests are named officially** on the arcprize.org competition page: Exploration, Modeling, Goal-setting, Planning and Execution. **No official source defines a separate metric for each; RHAE is one scalar.**

## 2. What the code does

### 2.1 Official toolkit and engine

- **Engine `handle_reset`:** a `RESET` with zero actions on the current level, or after `WIN`, is a full reset to level 1 with score 0. Otherwise it's a level reset. So two `RESET`s in a row reset the whole game.
- **Scorecard counting:**
  - a level reset adds 1 to actions;
  - a full reset opens a new play;
  - `WIN` counts all remaining levels as completed;
  - an environment's score is the **max** over its plays. The docstring says "average".
- **Not exposed to agents:** `_get_valid_actions` and `_get_hidden_state` are "internal use only, … never exposed via the API or to Users/Agents". The report uses hidden state for graph-based validation (§3.5.2).
- **Scorecard lifetime:** 15-minute idle auto-close, matching the docs. The maximum open time defaults to 4,320 minutes (72 h), while the changelog says "capped at 24 hours".
- **Precedence:** `OPERATION_MODE=COMPETITION` from the environment overrides the constructor argument. The Arcade docs say constructor arguments take precedence.
- **Caps:** no action cap anywhere in the toolkit or engine.
- **Agent-side caps** in `arc-agi-3-agents`: base `MAX_ACTIONS = 80` "to avoid looping forever", 20–400 in templates. The loop runs while `action_counter <= MAX_ACTIONS`.
- **Benchmarking budget:** per-level budget `ceil(baseline × MAX_ACTIONS_BASELINE_MULTIPLIER)`. The code default is **2.0**; all 16 shipped model configs set **5**.

### 2.2 RubiQ bench (`harness.py`, `aggregate.py`, `run_sweep.py`, `live_monitor.py`)

This is a federated CIFAR-10/100 classifier benchmark with six methods. Checked by reading the code and by executing the pure-Python lattice functions; no training was run.

- **The parity filter never fires.** All 18 generators are even permutations; 0 of 300 client-rounds are dropped.
- **Site 13, the core at (1,1,1), is never active after warmup.** Every generator fixes it. Each sparse set is always 3 corners, 4 edges and 1 face centre, which is why `rubiq`'s `bw` is constant.
- **`random_csi` stays sparse during warmup** (it ignores `full`), while `rubiq` uses all 27 sites. This contradicts the docstring's "symmetric warmup". The group-vs-random control is therefore not matched.
- **Evaluation always runs all 27 sites** (`active_ids=None`).
- **No `check_integrity` override** exists in the harness or the notebook. The guidance note's claim is unsupported by the code in hand.
- **`bw` counts parameter elements, not bytes.**
- **CIFAR-100 normalisation reuses the CIFAR-10 mean.**
- **Determinism is `warn_only=True`.**
- **CLI and `Config` defaults disagree:** batch size 64 vs 128, workers 2 vs 4.
- **The sweep cache key** omits `lr`, `batch_size` and the other `extra` fields.
- **In `aggregate.py`:**
  - the docstring's per-class win count is not computed;
  - the grouping key differs from the docstring;
  - with n = 3 seeds, a one-sided bootstrap p of 0.0000 only means all three seed differences share a sign.
- **The only run in hand** is the 36-run CIFAR-10 sweep (`sweep.json`). Mean post-warmup accuracy was 0.2144 vs 0.2144 at α = 0.1, and 0.2807 vs 0.2813 at α = 0.5.

### 2.3 `rubiq_lineage`

- **`TRAIN_READABLE = {public_demo, generated}`.** Training may read public-demo episodes, while LINEAGE.md says replayer-only.
- **The contamination audit compares IDs and filenames, not content.** In the demo, `hold-0001` and `pub-0001` hold identical frames and the audit reports clean.
- **Raw frames live only in memory;** `reproduce()` can't survive a restart.
- **The demo's `revocations` is read from a fresh `GoalBook()`**, so it is always 0. Revocation is never exercised.
- **`rhae_level` implements report Eq. (1)**, not the scorer.
- **`StepRecord` has no `guid`, `win_levels`, `levels_completed`, `full_reset`, `action_input.reasoning` or frame sequence** fields from the official recording schema.
- **`random_active` reseeds per round,** unlike the harness's per-client RNG stream.

## 3. Gaps between code and official requirements

| # | Gap | Official side | Code / note side |
|---|---|---|---|
| G1 | Level-score cap | Methodology and the scorer: at most 1.15. Report Eq. (1): up to 1.3225. | `rubiq_lineage.metrics.rhae_level` follows Eq. (1); differs on 40 of 269 stored runs |
| G2 | Human baseline definition | "Upper median" (methodology, report) vs "median" (changelog) | The repo's official `metadata.json` files carry post-14-April versions but `date_downloaded` 2026-04-08. Which rule their `baseline_actions` follow is unknown. |
| G3 | 5× action budget | Report §4.3: official-leaderboard evaluation only. Benchmarking configs: 5. Toolkit: none. Methodology page: silent. Kaggle: no read source states one. | Guidance and LINEAGE present 5× as part of RHAE in general ("later levels unreachable") |
| G4 | Four-component measurement | Four capabilities named; one scalar published | `component_vector` and its five metrics are the note's own construction. RubiQ code measures none of the four. |
| G5 | Interaction record | Official JSONL recording schema; multi-frame responses; `full_reset` | `StepRecord` can't ingest an official recording without a mapping; it holds one frame per step |
| G6 | Public set use | "Strictly … a demonstration", never a valid progress measure; lookalike synthetic training counts as domain-specific overfitting | `rubiq_lineage` lets training read `public_demo` and `generated` |
| G7 | Contamination | Task- and domain-specific overfitting concerns | ID/filename-only audit; no content hashes |
| G8 | Rerun observability | The gateway records actions; rerun recordings stay in `server_recording` | Nothing in the repo or the API returns rerun actions (consistent with corpus O-01) |
| G9 | Episode boundaries | `RESET` after zero level actions is a full reset; `WIN` completes the last level | Corpus replay rows must count `WIN` as level completion (INVENTORY saw `done`/`WIN` without `level_completed`) |
| G10 | Dataset mapping | Report: Fully Private 55 "for the competition" | AS-15 relays the memo's "110 hidden, 55/55 public/private board" (forum). No read official source maps Kaggle's two boards to sets. |
| G11 | Harness on the official leaderboard | Report v2: "will not use a harness" | `v3.json` (2026-09-30) lists provider-adapter configurations as separate entries |
| G12 | Page vs page and page vs code | Actions page: `ACTION7` = undo | LLM-agents page: `ACTION1`–`ACTION6`; `openapi.json` 404; scorecard 24 h (changelog) vs 72 h (code); "average" docstring vs `max` |
| G13 | RubiQ group control | n/a (not an ARC component) | The warmup asymmetry, fixed orbit mix and never-active core mean RubiQ vs `random_csi` is not a clean group test |
| G14 | Related-work figures | Abstracts: Rodionov 15/25, 58.12%; Schema 58.7% → 99.2%; OPINE 1.5% → 78.40%; the ablation's verification "ranks first throughout" | Guidance's OPINE "20/25" and "neural latent solved none" are not in the abstract. Its ablation reading omits that verification ranked first. |

## 4. Corrections to this corpus

- **LB-03** says medals come from the final private board and uses a top-10% band. Neither came from a read source; Kaggle metadata only says `awardsPoints: true`. The clause is unsourced.
- **AS-15** relays "110 hidden games, 55/55" from the memo. The report says the competition uses the Fully Private 55. Both are kept (G10).
- **D-09 / O-06:** the cap disagreement now has an official origin. Report Eq. (1) vs report prose, methodology and the pinned scorer code. The local scorer side stands (DV-06). Whether Kaggle's gateway scores with this exact code isn't published; the docs say it "runs the same game engine" and serves via `listen_and_serve` in competition mode.

## 5. Not established by any source read

- The Kaggle rules and Evaluation tab text (JavaScript-only pages).
- Hardware, time or action limits for the Kaggle rerun.
- Which hidden set each Kaggle board uses.
- The gateway's scoring code.
- Any private score.
- Whether Change A or any agent code ran as written during a rerun.
