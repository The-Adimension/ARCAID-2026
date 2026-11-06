# AGI-RubiQ Corpus: record of 2026-10-01

Built from `habanwer/ARC3` as it stands at commit `6569701` (Kaggle sync through 2026-09-30, pushed 2026-10-01). Nothing was replayed, no engine was started, and no pickle was loaded. The replays already ran, and their verdicts are the assessments listed below.

- **Rows:** `corpus/rows-2026-10-01.jsonl` (167 rows).
- **Derivations:** `corpus/derive_2026-10-01.py` (sha256 prefix `c4b91cc583c9837e`). It reads files only. Every `derived` row names it.

**Row sources.** A confirmation is always a separate row that links back to what it confirms. An `operator_intake` row is never upgraded.

| source | rows | meaning |
|---|---|---|
| `operator_intake` | 44 | The sealed `<intake>` and `<what_the_mass_already_measured>` assertions |
| `operator_rule` | 6 | The read rules stated in the brief |
| `file_confirmed` | 20 | A named path was opened and the claim checked |
| `derived` | 68 | Computed this session from opened files by the derivation script |
| `assessment_states` | 21 | A named assessment states it; the assessment was read, the underlying data was not |
| `attachment` | 8 | RubiQ zip, RubiQ notebook, `rubiq_lineage`, LINEAGE.md, guidance note |

## 1. Families (never averaged across)

| Family | Holds | Split | Status |
|---|---|---|---|
| **Starter save runs** | 9 folders (scored v1–v9, unsubmitted v5). None has `benchmark.json` or `score.json`. | `no_episode` | derived. Starter v5 has the same code as scored v6 (`3709f9d3…`). |
| **Duck/TAAF save runs** | 29 folders: 16 in `experiments/`, plus the save outputs of 13 scored folders. 22 hold play. The `benchmark.json` files list 269 game runs (some empty) and 34,942 actions. 7 hold none (ab-tricks v1 has 16 empty runs; reset v1 and stall v1 hit import errors; kvfp8 and dead-sign v5 failed vLLM setup; the TAAF quick-saves v1 and v2 hold none). | `public_demo` | derived per folder (`RUN-*` rows). 190 unique transcripts per the operator (INVENTORY: 18.7M reasoning characters in `1345`). |
| **Scored notebooks** | 21 public draws; `private_score` is empty on all 21; no actions. Sub-groups: starter (8 draws, 0.02–0.13), Duck Qwen3.8-27B (1 draw, 1.37), Duck FP4/NVFP4, from serving onward (10 draws, 2.49–3.59; the report's 8 Flash-Next draws are 09-19 to 09-26), TAAF sheetu (2 draws, 3.90 and 4.17). | `score_only` | file_confirmed against `submissions/index.csv`, 21 of 21. |
| **Teacher rounds** | `0393`: 14 rounds, 206 claude-opus-5 decisions, 12 games, 511 engine actions, 13 of 13 traces replay. No human play. | `public_demo` | operator_intake + assessment_states. Not opened. |
| **local_play real** | 62 machine recordings, 4 full wins (sb26, ft09, cd82, sc25), 36 real levels on 11 games | `public_demo` | operator_intake + assessment_states. Not opened. |
| **local_play fake** | 25 `summary.json` + 25 `win_actions.json` + 25 two-line recordings claiming WIN. Replay refuted all of them. They also exist in `3245/local_play`, which is a byte copy. | `excluded` | operator_intake + assessment_states |
| **Official games** | `inputs/official-input-arc-prize-2026-arc-agi-3/environment_files/`: 25 games, 183 levels in `baseline_actions` | `environment` | file_confirmed |
| **Assessments** | The 8 named files, dated 09-26 and 09-27 | `adjudication` | All 8 read. Immutable. |
| **RubiQ CIFAR** (attached) | 36 runs: 6 methods × CIFAR-10 × α ∈ {0.1, 0.5} × 3 seeds | `rubiq_fl` | attachment |

Within-family statistics only:

- **Duck Flash-Next draws, 09-19 to 09-26 (n = 8):** mean 3.074, SD 0.349. This reproduces the report. Adding 09-27 wmreason (n = 9): mean 3.069, SD 0.327.
- **6-game probe vs LB (n = 5):** Pearson −0.318, Spearman −0.40. Adding wmreason (n = 6): −0.235 and −0.371.
- **25-game save runs also run inverse.** Duck: 0.89 and 0.79 offline against 2.49 and 3.04 on the LB. TAAF: 8.68 and 7.80 offline against 3.90 and 4.17.

## 2. Links

### Which assessment judges which run

| Assessment | Judges | Does not judge |
|---|---|---|
| `experiments/SUBMISSIONS-EXPERIMENTS-AUDIT-2026-09-27.md` | All 18 scored folders and 14 save runs present at `8f26b44` | Scored 3.03, 3.90, 4.17; save runs TAAF quick-save v1 and v2, v5b |
| `experiments/ARC3-COLLECTIONS-INVENTORY-2026-09-27.md` | `arc3-collections/*`, `local_play`, teacher rounds, game copies. Source of the real/fake split. | No scored run |
| `experiments/SYSTEM1-REPLAY-2026-09-27.md` | 186 unique Duck save-run histories, as a test of waste removal (verdict: no-go) | No scored run |
| `experiments/SURPRISE-WALLS-2026-09-27.md` | 36 wall runs and the same 186 runs, as a test of a model-free surprise signal (verdict: a flag only) | No scored run |
| `experiments/JEV-DATA-MAP-2026-09-27.md` | Data supply for a typed-question critic | No run |
| `submissions/ANALYSIS-2026-09-26.md` | Baseline v1 (1.37), dead-sign v3 (3.59) and its probe; v4 (16.23) via EVAL-v4 | The other 15 draws |
| `report-2026-09-27.md` | The 8 Flash-Next draws, the 5 probe/LB pairs, compact (HOLD, 2.78). Its recommendation produced the 4.17 row. | The 4.17 row itself |
| `memo-2026-09-26.md` | Approaches and scoring, from external sources | No run in this repo |

**No assessment judges the current scored trace (4.17).** The same holds for the other two post-09-27 draws and for 6,779 actions in 62 game runs.

### Same code under different names (derived from notebook code hashes)

- **dead-sign v5 ≡ `notebook7c0bf2022d`** (`bd3071f6…`). Under the same code, one run failed at vLLM setup and the other completed at 13.41 offline. This confirms the operator assertion.
- **Starter v5 (no score) ≡ starter v6 (0.13).**
- **TAAF reasoning-notes v1 and v2 (quick-save) ≡ v3 (3.90).**
- **Change A (`wmreason`) is the only verified single-change pair.** Each arm adds exactly 81 lines and removes 0.
  - Dead-sign v3 → +A: 3.59 → 3.03 (Δ −0.56).
  - sheetu-0922 → +A: 4.17 → 3.90 (Δ −0.27).
  - One draw per arm. The +A arm on the sheetu base was submitted two days before the base.

### Disagreements: both sides kept, each named

| Row | Where | Side A | Side B |
|---|---|---|---|
| D-01 | dead-sign v2 | Markdown: 1 pass, 3,600 s, concurrency 6 | Code and `benchmark.json`: 2 passes, 7,920 s, concurrency 28. The code also prints `passes=1 cap_s=3600`. The 19.68 tag is a 2-pass mean. |
| D-02 | ab-tricks v3 | Markdown: 3 passes per arm | `n_passes=4`, alternating, so 2 per arm (24 runs over 6 games). The competition branch sets 1. |
| D-03 | Submission count | `submissions.csv`: 2 rows; ANALYSIS scoped to those 2 | `index.csv`: 18 at the 09-27 commits, 21 now. AUDIT says 18; the operator lists 21. The count depends on the date; the content does not conflict. |
| D-04 | `PUBLIC25_AUDIT runs=25` | Printed in 17 kernel logs | In 13 of those, `score.json` holds 6 games (11 runs) or 1 game (ledger, prompts). Only serving, batch and the two TAAF runs scored 25. |
| D-05 | Unique runs | 186 (SYSTEM1, excludes empty histories) · 190 (INVENTORY, JEV, operator) | 195 signatures (AUDIT, includes empty histories) |
| D-06 | Teacher rounds | 14 rounds, 12 games, 13 traces (INVENTORY, operator) | "13 rounds of about 15 decisions" (JEV-DATA-MAP) |
| D-07 | "v5" | The report's "compact v5" is the scored compact v1 (2.78; probe 34.93; code `5161ad04`) | `experiments/…dead-sign__v5` is Kaggle version 5 (code `bd3071f6`). `v5b` is a third run (29.09). |
| D-08 | Single-change steps | AUDIT (09-27): two exist (starter v7→v8, reset v3→v4) | Two later add-only steps exist (Change A). The v7→v8 and v3→v4 diffs were not re-checked here. |
| D-09 | RHAE form | memo: `min((h/a)², 1.15)` | `rubiq_lineage/metrics.py`: `min(1.15, h/a)²` (maximum 1.3225). The cap value is also 1.15 in the docs and 1.0 on the Kaggle pages. |
| D-10 | LINEAGE.md | Says the repo returned 404, 20 submissions, "4.19 Milestone-2 bronze" | The repo is private, not missing. `index.csv` has 21 rows. 4.19 appears in no named file. |
| D-11 | RubiQ cell label | LINEAGE.md: Δ 0.0000, p 0.2695 is a CIFAR-100 cell | The notebook ran CIFAR-10 only; that row is α = 0.1. **The CIFAR-100 attribution is revoked; the deltas stand.** |
| D-12–D-14 | Stale records | `presubmissions/` paths; reset v2 "23.33 vs 28.81" (raw 19.83 vs 28.30); `cap_s=3600` printed on a 1,200 s budget; completion-only "RHAE" 26.13 (frozen scorer 25.08); Qwen3.6 named in settings | Per AUDIT, ANALYSIS and INVENTORY. Kept as stated. |
| D-15 | Coverage | The 190 / 186 / 195 counts | These are 09-27 counts. 28,163 folder actions predate 09-27, within 4 of SYSTEM1's 28,159. The other 6,779 actions are uncounted. |

## 3. What a later agent may read

1. **public_demo wins are replayer tests only.** This covers the local_play full wins and 36 real levels, the `1345` sb26 8/8, and the 13 teacher traces. They are not training labels for a policy and not a held-out score.
2. **The fake WIN records are excluded** from every read, in both `local_play` copies. Counting them adds 185 phantom levels.
3. **The environment is the official game files:** `inputs/official-input-arc-prize-2026-arc-agi-3/environment_files/`. The `2345` and `3245` copies are not the environment.
4. **Reasoning text is the model's own assessment of a turn, not a label.** Within one config it predicts clearing at AUC 0.52 (JEV-DATA-MAP).
5. **The current scored trace is the 4.17 notebook:** `submissions/2026-09-30__taaf-flashnext-sheetu12b-0922__v1__score-4.17/__notebook__.ipynb`, public score 4.17. Its `outputs/` folder is a public-game save run (`TRUE_SUBMISSION=False`, 25 games, 7.80 offline), not the scored play.
6. **4.19 stays unverified** until a row in `index.csv` shows it.
7. **Scored rows are score-only.** No folder's `score.json` is hidden-set play.
8. **Offline scales do not mix.** The 6-game probes, the 25-game runs, the 1-game runs and the 2-pass means are different quantities.
9. **Media are checks, not episodes.** The 3,090 animation frames in `intermediate_states.pkl` are the one unique frame store. Inspect them with class stand-ins only.
10. **The assessments are immutable episodes.** A new judgement goes in a new file.
11. **This corpus has no `heldout_public`, `generated` or `private_lab` row.** The Duck runs have played all 25 public games, so nothing here can be promoted to an eval split.
12. **RubiQ CIFAR is federated-classification evidence only.** On mean post-warmup accuracy:
    - α = 0.1: rubiq 0.2144, random_csi 0.2144.
    - α = 0.5: rubiq 0.2807, random_csi 0.2813 (p 0.0000, n_paired = 3).
    - The FL baselines are an MLP, and SCAFFOLD sat at chance (0.1000) on α = 0.1. The group did not beat random sparsity.
    - The docstring of `aggregate.py` promises a per-class win count that its function body never computes.

## 4. Open remainder (not confirmable from this mass)

- **O-01: What the hidden rerun did.** No rerun log exists, and every saved log is `TRUE_SUBMISSION=False`.
- **O-02: Whether any single code change moved the score outside noise.**
  - The steps: starter v7→v8 (−0.06), reset v3→v4 (−0.53), Change A on Duck (−0.56), Change A on sheetu (−0.27).
  - Single-draw SD is about 0.33–0.35, measured on Duck only, so the difference of two draws has an SD of about 0.47–0.49.
  - No step exceeds about 1.2 of that, with one draw per arm. The TAAF base has no replicate, so its own noise is unmeasured.
- **O-03:** Whether 4.17 reflects the harness or one high draw. The report's falsifier, 3–4 sheetu draws at or below 3.6, never ran.
- **O-04:** Whether the 4.17 notebook is byte-identical to the public scottlegrand V1. That source is outside the named paths.
- **O-05:** Whether Change A actually fired in either +A run.
- **O-06:** Which RHAE form and cap the shipped scorer uses.
- **O-07:** Why the tn36 recording diverges by 28 cells on 7 steps.
- **O-08:** Whether the four `intermediate_states.pkl` files outside `1345` are the same bytes as the `1345` pickles.
- **O-09:** Whether reasoning text predicts correctness once config is controlled.
- **O-10:** Whether the unjudged post-09-27 rows carry record-keeping errors.
- **O-11:** Any private score.
- **O-12:** Whether the RubiQ lattice or group carries signal on any ARC-like target.

**Present but unopened (no row asserts their content):**
- `experiments/`: `index.csv`, `EVAL-v4*`, `PLAN-v5`, `hypothesis-test*`, `v5/`, `build_v4a.py`, `build_v5.py`
- `collect.py` (both copies)
- Root: `memo.md`, `research.md`, the two root `.ipynb` files
- `kaggle/`, including `kaggle/changeA/README.md`, which the Change A cell cites
- `notebooks/`
- The contents of `inputs/local_play`, `arc3-collections`, `jev` and `hypotheses`

**Open next, one file:** `submissions/2026-09-28__taaf-flashnext-sheetu12b-reasoning-notes__v3__score-3.90/__output__.json`. This session regex-scanned it for `PUBLIC25_AUDIT` and `TRUE_SUBMISSION` only; its `WMR_STATS` and vLLM identity lines are unread.

**The link it can revoke:** DV-03, which reads "3.90 = 4.17 code + Change A, a single-change pair inside measured noise". That link is revoked if the log shows any of:
- Change A installed nothing (`WMR_ON` false);
- Change A was applied to zero responses (`reasoning_applied = 0`);
- a served model or runtime that differs from the 4.17 log.

The pair would then be two draws of the 4.17 base. Its |Δ| of 0.27 would become the first replicate-noise measurement on that base.

---

## Addendum: Kaggle source and public leaderboard (2026-10-01, ~11:45 UTC)

This addendum is append-only. The sections above stay as written; corrections enter as adjudication rows.

- **Rows:** `corpus/rows-2026-10-01-addendum.jsonl` (21 rows; sources `kaggle_api`, `leaderboard_snapshot`, `derived`).
- **Checks:** `corpus/verify_addendum_2026-10-01.py` (sha256 prefix `380a51783490b364`). It uses GET requests to the Kaggle API and reads repo files. It submits nothing and replays nothing.
- **Leaderboard snapshot:** `arc-prize-2026-arc-agi-3-publicleaderboard-2026-10-01T11:43:58.csv` (sha256 prefix `8f64b13baf0dd1ba`), attached by the operator. It is not committed.

### What the source confirms

| Row | Finding |
|---|---|
| KG-01 | Kaggle lists 21 submissions; all 21 match `index.csv`. Private score is empty on all 21. No 4.19. None after 2026-09-30 18:47 UTC. |
| LB-01 | Public LB at 11:43:58: rank 322 of 3,536, score 4.17, 21 submissions. The team's best draw is 4.17, not 4.19. |
| KG-02 | The 4.17 notebook's code is identical to public `scottlegrand/taaf-flashnext-sheetu12b-0922` V1, with 0 lines differing. It also matches on datasets, model, machine and Docker digest. |
| KG-03 | The Kaggle sources and logs are byte-identical to the repo copies for the 3.90, 4.17 and 3.03 kernels. |
| KG-04, KG-06 | Change A ran in both +A save runs. 3.90: `reasoning_applied=142` of 1,087 responses. 3.03: 47 of 577. Both have `errors=0`. |
| KG-05 | The 3.90 and 4.17 runs used the same runtime. Identity and setup files are identical outside process fields. 58 of 61 provenance content pins are identical; the other 3 are per-boot log hashes. |
| DV-06 | The save-run scorer is `min((h/a)², 1.15)` with the completion cap. It reproduces 269 of 269 stored game runs; `min(1.15, h/a)²` fails on 40 and a 1.0 cap on 62. `score.json` equals `final_score` on 168 of 168 games. |

### Adjudications (AJ-01 … AJ-07)

- **AS-01 to AS-16:** read `kind=confirm` as "cites". The assessment was read; the underlying data was not.
- **DV-03:** now a single-change pair for the save runs, because the gate is met. No effect is shown: one draw per arm, Δ −0.56 and −0.27, inside noise. The +A sheetu arm was submitted before its base, so the pair is not a before/after. Change A in the hidden rerun is unobserved.
- **NEXT:** closed. Its revoke observation did not occur.
- **O-04:** resolved for code.
- **O-05:** resolved for the save runs.
- **O-06:** narrowed to the server-side scorer.
- **D-09:** keeps both sides. The local side is settled for the memo form.
- **Section 1 table:** the "Holds" column states teacher rounds, local_play wins and the 190 transcripts as facts. Cite the row sources instead.
- **LINEAGE.md:** the copy held in this session still says "CIFAR-100 cell". D-11 stands.
- **"Milestone-2 bronze":** no row supports it. The snapshot is about 12 h after the cutoff. Rank 322 sits inside this snapshot's top-10% band (rank ≤ 353), but medals come from the final private board.

### Still open, and next

- **O-01, O-02, O-03, O-11:** unchanged.
- **O-13:** whether the 5.19 belongs to the sheetu notebook. The snapshot gives only team bests. If it does, two draws of identical code differ by 1.02.
- **O-14:** whether the scottlegrand run used the same dataset content.
- **Next read (NEXT-2):** `vllm-setup-provenance.json` from the output of public kernel `scottlegrand/taaf-flashnext-sheetu12b-0922`.
- **What would revoke KG-02's runtime reading for the 5.19 run:** any differing content pin (`runtime.index_digest`, `model.config_sha256`, the patch artifact hashes, `vllm_version`).
