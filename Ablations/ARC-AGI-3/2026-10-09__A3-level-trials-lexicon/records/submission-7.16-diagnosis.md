# Why the 2026-10-11 submission scored 7.16

**Submission:** public kernel `habanwer/arcaid3-lt-lex-r3`, version 1 (scriptVersionId 357014947), submitted 2026-10-11 14:39 UTC. Public LB 7.16; the previous best was 27.05 (`arcaid3-lexicon-view-dfranzen-m2` v4).

## Finding

- **The notebook is the "level trials" evaluation build:** Franzen M2 v1, plus the lexicon view (v5 naming tweaks), plus a mode that plays every level of every public game as its own 20-minute trial.
- **It sets `USE_PRIORITY_SCHEDULING = False`** (line 10200 of the flattened source). Franzen v1 and the 27.05 notebook set it to `True`. With the flag off, the competition rerun loses three things:
  - **The rerun overrides never apply.** They are written as `if TRUE_SUBMISSION: if USE_PRIORITY_SCHEDULING: concurrency = 120; max_runtime_s_per_game = 532*60` (config cell).
  - **The priority-gate environment variables are not set** (`ARC3_MAX_ACTIVE_STREAMS=10`, `ARC3_PRIORITY_*`).
  - **So the hidden games ran with the trial defaults:** 10 at a time, a hard 20-minute cap each, and no reallocation of time from stuck games to progressing ones. With 110 games that is about 11 waves × 20 min, roughly 220 of the 540 available minutes.
- **The save run itself was healthy:**
  - The lexicon installed and passed its self-tests.
  - 7,370 tool calls, 1,408 of them using the view, 0 errors.
  - No traceback in the log.

## Expected score under that configuration

`estimate.py` runs on the notebook's own save run and on Franzen's 4×25 demo run.

| Estimate | Demo mean | Share of the full system (46.49) | LB-equivalent (× 25.77) |
|---|---|---|---|
| (a) The save run's 25 `@L0` entries: whole games under the same 20-minute cap, 10 at a time, no gate | 19.79 | 0.426 | 10.97 |
| (b) Franzen's runs, counting only levels finished within the 76,014 generated tokens a 20-minute entry got | 19.14 | 0.412 | 10.61 |

Observed: 7.16. The configuration accounts for most of the drop from about 26. The rest is consistent with draw noise, and with hidden games being harder than the demo set, so a tight per-game cap may cost more there. Neither of those can be separated with one draw.

Run: `python3 estimate.py data/lt-lex-r3-benchmark.json ../2026-10-10/data/dfranzen-m2-v3/benchmark.json`

## Data

- `data/lt-lex-r3-benchmark.json` and `data/lt-lex-r3-summary.txt`: the kernel's saved output (Save & Run of 2026-10-10, 183 level-trial entries, offline on the 25 public games), fetched via `GET /api/v1/kernels/output`.
- Kaggle never returns the hidden rerun's play, so the rerun configuration above is read from the code, not observed.

## Independent verification (2026-10-12, three checkers, each told to refute)

All three confirmed the diagnosis from the code lines and recomputed the numbers.

- **Code path:**
  - The flag changes only cell 5. It removes the competition overrides and the priority gate; `ARC3_MAX_ACTIVE_STREAMS` unset means the gate is off.
  - Each game's 20-minute clock starts when it gets one of the 10 slots, so all 110 hidden games are played, in about 11 rounds.
  - The run finishes in about 4 of its 9 hours.
  - The level-trials patch is a no-op on competition games (no `@L<k>` in their ids).
  - The harness patch and all of Franzen's cells match the 27.05 notebook.
  - The rerun log is not available, so the rerun itself is inferred from code plus save-run timing.
- **Numbers:** 19.79 and 19.14 reproduce, so the prediction for the configuration is about 10.7–11.1. Against the full system's mean, 7.16 is z = −4.7, so it is not plain noise. The remaining 3.5–4 points are not explained. Candidates, none verified:
  - draw noise, which is larger at small budgets (Franzen's per-pass means under the same cap range 15.65–20.39);
  - harder hidden games losing more under a tight cap: a "hidden levels cost 2× tokens" model gives 8.2;
  - gateway latency per action, which counts against a wall-clock cap;
  - the lexicon v5 naming changes, a confound.
- **Restart design:** the restart A/B needs whole games, not this instrument.
  - A 100k-token stuck-level trigger can never fire in a 20-minute level trial: 0 of 183 entries reached 100k generated tokens (max 94,770).
  - Cold-start level trials are much harder than chained play from the second level onward: 22% vs 80% of levels cleared within 75k tokens.
  - A fair restart A/B uses whole games under Franzen's budget with priority on. It should be read per event: of attempts that reach 100k tokens, what share then finish? The control's rate is 3 of 35 (14.6% by 140k).

## What to do with this

- **Next submission:** set `USE_PRIORITY_SCHEDULING = True`, or resubmit the 27.05 notebook / Franzen v1.
- **Keep evaluation builds and submission builds separate.** In a submission build, assert the competition settings in the `TRUE_SUBMISSION` branch, e.g. `assert bm.solver.concurrency == 120 and bm.solver.max_runtime_s_per_game == 532*60`, so a mis-set flag fails loudly instead of scoring 7.
- **Final selection:** do not select this submission. If no selection is made, Kaggle auto-selects by public score, which would pick the 27.05 and 24.95 draws.
