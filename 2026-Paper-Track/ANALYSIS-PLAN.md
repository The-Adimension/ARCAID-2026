# Analysis plan for the Paper Track

**Written:** 2026-11-07, before any analysis in Stages 2–4 was run. The commit that adds this file is the timestamp.

**Purpose:** the paper is to be written from the data in [`data/`](data/), not from earlier write-ups. This plan fixes in advance:
- what will be tested;
- how it will be tested;
- what counts as confirmatory;
- how deviations are reported.

## 0. What has already been seen

Honest disclosure of what was computed before this plan was written:

- **Stage 1 verification (done).** Every recorded ARC-AGI-3 action history was replayed on the official engine (`arc-agi` 0.9.8, `arcengine` 0.9.3, the official public game files):
  - 2,489 game-runs and 191,674 actions;
  - levels, actions per level and scores reproduce for all 659 whole-game runs;
  - the cleared/not-cleared outcome reproduces for all 1,830 level trials;
  - the human baselines match the official game metadata for all 2,489 game-runs.
- **Recomputed from replayed outcomes**, shown to the author in chat on 2026-11-07, and matching the records of October 2026:
  - A3 round 3: on 58, off 67; discordant pairs 8 vs 17; exact McNemar p = 0.108.
  - Probe-first round 1: p = 0.043. Round 2: p = 0.281. Both rounds pooled: discordant pairs 37 vs 19, p = 0.022.
- **Earlier analyses on record.** The decision rules and results of October 2026 are in `../Ablations/ARC-AGI-3/`, with commit times in `PREREGISTRATION.csv`. The analyses below are **re-analyses of data already collected**, with the plan fixed now. They are not new pre-registered experiments, and the paper will say so.

## 1. Data

| Table | Unit | Built by | Source |
|---|---|---|---|
| `data/replay.csv` | game-run | `Tools/analysis/replay_tables.py` | `benchmark.json` histories, replayed on the engine |
| `data/levels.csv.gz` | (run, game-run, level) | same | engine replay |
| `data/actions.csv.gz` | action | same | engine replay, plus the harness's tokens and wall-clock per action |
| `data/turns.csv.gz` | model turn (`analysis_step`) | `Tools/analysis/extract_zip_tables.py` | `transcripts/` in the run-output zips |
| `data/calls.csv.gz` | model response | same | `*_requests.jsonl` (October runs onward) |
| `data/events.csv.gz` | logged action | same | `artifacts/*_events.jsonl` |

**Rules for using the tables:**
- **Outcomes** (cleared, actions, game-overs, board change) come only from the engine replay.
- **Behaviour** (tokens, reasoning, tool calls) comes from the logs.
- **Joining:** events link actions to turns through `run_id`, `game_run`, `pass` and `action_num` = `action_index`.
- **Schemas** are in `data/datapackage.json`.

## 2. Confirmatory analyses

Two hypotheses, one per datafication layer. Each is tested where the design isolates it: paired cold-start level trials, in which every level of the 25 public games is played from its own start under both arms.

| | H1: perception | H2: economics |
|---|---|---|
| Change | Lexicon view on vs off (`ARCAID3_LEXICON`) | Probe-first governor on vs off (`PF`) |
| Design | `Ablations/ARC-AGI-3/2026-10-09__A3-level-trials-lexicon` | `Ablations/ARC-AGI-3/2026-10-24__level-trials-probe-first` |
| Primary data | Round 3, 183 paired levels. Rounds 1–2 failed their own validity checks, written before the result. | Rounds 1 and 2, 2 × 183 paired levels |
| Primary endpoint | Level cleared within the trial (`levels.csv.gz`, `trial = 1`, `cleared`) | Same |
| Primary test | Exact McNemar, two-sided | Exact test on discordant pairs, stratified by round (exact conditional, equivalent to McNemar summed over strata), two-sided |
| Effect size | Difference in clear rate with a Newcombe interval for paired proportions; conditional odds ratio (discordant ratio) with an exact 95% interval | Same, per round and pooled |
| Multiplicity | Holm across H1 and H2, family-wise α = 0.05 | Same |

**Pre-set sensitivity analyses.** They are reported whatever they show.
1. H1 including rounds 1–2, stratified by round, labelled as including invalid rounds.
2. Each hypothesis by level depth: level 1, levels 2–3, levels 4 and above.
3. Leave-one-game-out: the range of the effect estimate and p-value.
4. Conditional logistic regression with game as a random effect, as a robustness check of the primary test.

**Interpretation rule:**
- A hypothesis is called **supported** only if its Holm-adjusted p < 0.05 **and** the sign is the same in every round that was run.
- Otherwise the result is reported as **not detected at this size**, with the interval. It is not reported as "no effect".

## 3. Secondary analyses (descriptive; no significance gate)

| | Question | Data | Method |
|---|---|---|---|
| S1 | How noisy is one whole-game run? | A1 replicates (3 runs per arm); A2 rounds; the two save runs of each selected notebook | Per-game and per-run spread; game-level bootstrap intervals for mean RHAE |
| S2 | Whole-game designs as recorded | A1 (v2 vs v4), A2 (on vs off), restart v1 and pair | Re-run of each recorded test on replayed outcomes. Report agreement with the record. |
| S3 | Where do the selected leaderboard draws sit against the noise? | S1; the scores of copies of the base notebook (Son Pham, Kaggle discussion 745062; third-party) | Descriptive only. Hidden-set reruns cannot be replayed. |

## 4. Mechanism analyses (exploratory; labelled as such)

| | Question | Data | Method |
|---|---|---|---|
| M1 | **Reading vs acting.** After the model reads the lexicon (`reads_code`, `reads_rules`), does what it does next change? | `turns`, `events`, `actions` (lexicon-on runs, and A3 trials of both arms) | Per turn: share of actions that change the board; level completion within the turn and within the next K = 10 actions; game-overs. Turns with and without reads, matched on game and level. The off arm on the same levels is the reference. |
| M2 | **Spending.** Where do tokens and actions go? | `calls`, `turns`, `levels` | Tokens per cleared level; share of turns executing no action; tokens before the first action of a level; probe-first arms compared. The gate quantity that failed ("no-action token share") is recomputed from its definition in `lt_analysis.py`. |
| M3 | **Stuck levels.** What happens on levels played but not cleared? | `actions` (`board_hash`), `levels`, `calls` | Repeated board states (loops), unchanged-board actions, game-overs, tokens spent; compared with cleared levels of the same game. |
| M4 | **Efficiency.** How do our actions compare with the human baseline on cleared levels? | `levels` (`actions_over_human`) | Distributions by arm and by harness generation; the share of levels at or below the human count (where the RHAE cap of 1.15 applies) |
| M5 | **Generalisation across generations.** Do M2–M4 patterns hold in the September Duck runs, the October Franzen-based runs and the level trials? | All tables | Same metrics per generation. Differences in setup (time per game, number of games) are stated, not adjusted away. |
| M6 | **ARC-AGI-2 transfer.** What the entry ran and how it was served | Run folders and their logs | Description only: install checks, serving, the 3-task smoke run, the leaderboard record. No behavioural data exists. |

**Rules for M1–M6:**
- No mechanism result is called confirmed.
- Patterns are reported with counts, intervals and the analyses tried, so they can be followed up.

## 5. Handling rules

- **Validity:** a run or round that failed a validity check written before its result stays excluded from primary analyses and is shown in sensitivity analyses.
- **Units:** whole-game results are compared within one setup only (10 games × 25 min; 25 games × 121 min; 183 levels × 20 min).
- **Missing data:** September runs have no per-call token records. Their per-action generated tokens (from `benchmark.json`) are used instead and labelled.
- **Randomness:** sampling runs at the notebooks' own temperatures; no seed was fixed. Every run counts as one draw.
- **Software:** Python 3.12; `arc-agi` 0.9.8 and `arcengine` 0.9.3 for replays. Analysis scripts are committed in `Tools/analysis/` before their results.

## 6. Reporting

- Every number in the paper comes from a committed script reading `data/`. A `claims.csv` maps each claim to its script and value.
- Confirmatory, secondary and exploratory results are kept in separate sections.
- Null and negative results are reported as fully as positive ones.
- The leaderboard scores are reported as single hidden-set draws. Public-game results are never presented as hidden-set results.

## 7. Deviations

Any change to this plan after its commit is listed here, with its date and reason.

| Date | Change | Reason |
|---|---|---|
| | | |
