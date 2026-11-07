# Analysis plan for the Paper Track

**Written:** 2026-11-07, before any analysis in Stages 2–4 was run. The commit that adds this file is the timestamp. Section 8 (post hoc, Stage 5) was added later that day, after the Stage 2–4 results had been seen.

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
| 2026-11-07 | Tables gained a `pass` column; the join of events to actions uses `run_id`, `game_run`, `pass` and `action_num`. | Four runs play some games more than once. Without the pass number their actions were mis-joined. A data-structure correction made before any Stage 2–4 analysis; no test or endpoint changed. |
| 2026-11-07 | `actions.board_changed` is defined from the replay: the last frame after the action against the last frame before it. `any_frame_changed` was added alongside. | The harness's own flag is constant (always 1) in games `lf52` and `bp35` (`data/CHECKS.md` §2). Outcome definitions come from the engine (§1), as planned. |
| 2026-11-07 | `stage3_secondary.py` S3: notebooks are selected by their recorded root base (Franzen's notebook) instead of by score, and the 7.16 trial build is excluded by name. | Bug in the committed script: its score filter let in a sheetu-base notebook (4.56) and the 7.16 build, contrary to the plan's S3 scope. Found on the first run; corrected before the result was used. |
| 2026-11-07 | `replay_tables.py`: in level trials, an action's level is the start level plus the levels cleared since the start. | Bug: the engine's `levels_completed` does not count the levels skipped by `set_level(k)`, so trial actions had been filed under level 0. Trial outcomes (cleared or not, relative to the start) were unaffected, so H1 and H2 were unaffected; per-level actions, ratios, game-overs and tokens of trials were wrong. Found from an impossible value in M4 (cleared with 0 actions); all tables and Stage 2–4 results rebuilt. |
| 2026-11-07 | `stage4_exploratory.py`: whole-game runs are grouped by the root base recorded in each run's `run.json`, not by run name. The September group is relabelled "Duck/TAAF-based whole games (Sept to 4 Oct)". | Bug: two runs of 4 October on Scott Le Grand's sheetu base (`arcaid3-lexicon-view-py312@v1`, `arcaid3-lexicon-view-v2@v1`; 50 game-runs) were grouped with the Franzen-based runs because their names start with `arcaid3`. Affects M3–M5 only; M1, M2, M6 and Stages 2–3 are unaffected. Found while writing Stage 5; Stage 4 re-run. |
| 2026-11-07 | The analysis scripts are in `2026-Paper-Track/analysis/`, not in `Tools/analysis/` as §5 says. | Placement only. Each script was committed before its results, as §5 requires. |
| 2026-11-07 | §8 added: post hoc analyses (Stage 5). | Questions raised by the Stage 2–4 results; labelled post hoc. See §8. |

## 8. Post hoc analyses (Stage 5)

**Added:** 2026-11-07, after the Stage 2–4 results (commit `e944464`, 08:22 UTC) had been seen. Nothing in this section was fixed in advance.

**Status:** post hoc. The results suggest; they do not confirm. No Stage 2–4 verdict changes because of them, and in the paper each one is labelled post hoc.

**How they arose.** The Stage 2–4 results raised "why" questions. They were first explored the same morning in scratch scripts outside this repo, and the results were seen and shown to the author. Re-running them found errors in that first pass (listed below). `analysis/stage5_posthoc.py` redoes every analysis from `data/` with those errors fixed. It is committed before its first run, and its output is the only version used.

| | Question | Why it was asked | Data | Method |
|---|---|---|---|---|
| P1 | How different are two runs of the unchanged agent (A/A)? | H1's split (8 vs 17) needs a reference for chance. | `levels`: the three control arms (lexicon round 3 on 10 Oct; probe-first rounds 1 and 2 on 24 Oct). Setup checks: each control's log and notebook. | Exact McNemar for each pair of controls and for the two probe-first runs; Cohen's κ; ICC(1) across the controls. |
| P2 | What effect size can the level-trial design detect, and how much do significant results overstate? | To read H1's "not detected" and H2's +4.9 points. | `levels` (the controls; all six runs as a sensitivity) | Simulation. Each level's clear chance comes from a beta-binomial fitted by maximum likelihood to the clear counts. An add-on shifts every level's log-odds by one constant, chosen to give the stated mean gain. Built-in check: the simulated A/A disagreement must cover the observed. Power for gains of 3, 5, 8 and 10 points with 1, 2 and 4 rounds, and for harms of 5 and 8 points with 1 round. The mean significant estimate when the true gain is 3.3 or 4.9 points (2 rounds). |
| P3 | Each add-on against all three controls | A second estimate that uses every control run | `levels` | Difference in clear rate; exact permutation of run labels within each level. Assumes runs on different days are exchangeable. |
| P4 | Did probe-first change what it targets? | H2 was supported, but its mechanism is unknown, and Stage 4 M2 shows fewer tokens per cleared level. | `calls`, `actions`, `levels`; the governor's counters in the logs | No-action streaks (the `lt_analysis.py` definition); moves per trial; tokens, responses and actions to clear levels that both same-day arms cleared (Wilcoxon signed-rank). The A/A pairs are the reference. |
| P5 | What limits the score? | Stage 4 M4 shows little inefficiency on cleared levels. | `replay`, `levels`, `calls`, `actions` | Score anatomy of whole-game runs by root base: lost to uncleared levels vs to inefficiency, the 5× action budget, the value of the next level. Clear rate by human solution length and depth (logistic regression clustered by game). When clears happen within a trial. Levels cleared by one run of a pair vs by both (Mann–Whitney). Moves in failed trials against the human count and against the moves clears needed. New board states per move; the frontier of levels ever cleared. |
| P6 | Is M1's reading association explained by when reads happen? | M1's negative associations could reflect timing. | The turns of M1 | M1's stratified difference, with strata refined by position in the level (0, 1–5, 6–15, 16–40, more than 40 actions taken) and stuck status (an unchanged-board action among the last 5 actions, or a revisit among the last 10, on that level). Both completion outcomes of M1; turns with and without a lexicon cue separately; bootstrap over games. |

**Errors found in the first pass, and fixed in the script:**
1. **Power model.** Each level's clear chance was set to (k + 0.5)/4 from three runs, so levels no run had cleared got 12.5%. That implied 50 disagreeing levels per A/A pair, against 25–29 observed, and power figures that were too low. Replaced by the fitted model above, with the A/A check built in.
2. **Failed trials.** "72% of failed trials made fewer moves than the human count" was read as "they ran out of moves". Clears often take fewer moves than the human count, so failed trials are now also compared with the moves that clears needed.
3. **Reading.** The matched reading result was compared with the wrong M1 outcome. Both M1 completion outcomes are now matched.
4. **Grouping.** Two October whole-game runs on the sheetu base were grouped with the Franzen-based runs by their names. The same bug was in Stage 4 (§7). Runs are now grouped by the root base in `run.json`.
5. **Definitions.** Late-clear timing and the frontier now use one stated definition each.

**Rules:** as for §4. Results go to `results/stage5_posthoc.md` and `.json`.
