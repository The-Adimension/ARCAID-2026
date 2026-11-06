# Decision rule: do the "operational lexicon" proposals target where score is lost? (fixed before any run, 2026-10-12)

## Why an offline test, and why on stuck attempts

- **Where score is lost** (`origin/claude/vibrant-keller-ksqha6:memo-2026-10-10.md` §4, Franzen's 4 × 25 demo run):
  - Completed levels already use a median 0.64× the human action count, and 80% of them hit the 1.15 cap. Saving actions on levels the agent completes is worth 0–2 points.
  - 36.2% of generated tokens go into level attempts that never complete. 40 of the 67 unfinished attempts were on levels the same system completed in another pass.
- **So a tool can only move the score by turning stuck attempts into completions.** Every test below is read on stuck (unfinished) attempts, with completed attempts as the comparison.
- **The passive view is already measured at zero:** level trials −4.9 points of clear rate (95% CI −10.2 to +0.4), leaderboard-like A/B −0.03, replicates −0.33 (`origin/claude/gracious-thompson-6is9pp`, `experiments/2026-10-09__*`). A new tool has to show, offline, that it knows something on stuck attempts before it earns a GPU A/B.

## Data

- Franzen M2 v3 output, `benchmark.json` (sha256 `ea186291…`): 100 game runs (4 passes × 25 public games), 21,245 actions, each with its generated tokens. Copied from `origin/claude/vibrant-keller-ksqha6:analysis/2026-10-10/data/dfranzen-m2-v3/benchmark.json`.
- Replayed on the official engine (arc-agi 0.9.8, arcengine 0.9.3, Python 3.12) with the public game files.
- Lexicon and rule grammar exactly as shipped in lexicon v5 (`src/`, copied from `origin/claude/gracious-thompson-6is9pp` at `92e8ac6d`).

## Units

- **Attempt:** one run's play of one level, from the first action on that level to the action that completes it. The level the run never completes is an **unfinished (stuck)** attempt.
- **Step:** one non-RESET action. Steps before an attempt's 10th action are excluded from the rates (no tool has data yet), but they are kept in the history the learner reads.

## Test A: `predict(action)` (proposal 1)

Before each step, the grammar's learner holds every earlier step of the same attempt (more data than the shipped 60-step window, so this favours the proposal). `predict(action, click)` answers in one of three ways:

| Answer | When |
|---|---|
| **confident** | at least one rule fires |
| **known no-op** | no rule fires, and the same action (for a click: the same clicked picture, or "no object") changed nothing every earlier time on this attempt |
| **unknown** | otherwise |

Graded against the replayed screen:
- **Informative and right (I):** confident and exact (every prediction came true and every change was predicted), or known no-op and nothing changed.
- **Misleading (M):** confident and not exact, or known no-op and something changed.

**Kill rule for proposal 1:** on steps of stuck attempts, **I < 30%, or M ≥ I.** Either means the query would mostly say "unknown" or would mislead where the score is lost.

Also reported, not decisive: the same rates on completed attempts, and on "new" steps (an action key used at most twice before in the attempt).

## Test B: `unexplained_recent()` (proposal 1, second half)

A surprise signal is useful only if it is rare enough to mean something.

**Kill rule:** on steps of stuck attempts, if **more than 50%** of steps have at least one change no learned rule explains, the signal is a constant alarm, not a surprise trigger.

## Test C: stuck detector (proposal 4)

- **Question:** at a fixed point in an attempt, can a loop signal tell the attempts that will never finish from the slow ones that will? A restart policy needs exactly this: the 2026-10-10 policy model gains +2.82 demo points restarting at 60K tokens if it does not also cut the 41 slow successes it currently cuts.
- **Population:** attempts still running at **40,000** generated tokens on the level (also reported at 60,000).
- **Primary feature, fixed now:** the loop score, the share of the last 30 actions that changed nothing or led to an interior screen (4-cell border removed) already seen in this attempt.
- **Secondary features** (reported, not decisive): the same over the whole attempt; distinct screens per action; the rule grammar's exact rate so far.
- **Outcome:** the attempt never completes.

**Decision rule for proposal 4:** if the primary feature's AUC at 40K is **≥ 0.70**, wire it into the restart trigger as a gate. Otherwise a lexicon loop signal adds nothing over a plain token trigger, and the restart (if built) stays token-only.

## What none of this tests

- Whether the model would *use* a right answer. A pass here only earns the tool a GPU A/B; a fail ends it without one.
- Proposals 2 (richer grammar) and 3 (tracking) are graded through A: they matter only if they raise I on stuck attempts. The existing offline numbers (16.6% of changes explained on public plays with v4 perception, `origin/claude/gracious-thompson-6is9pp:design/2026-10-07__rule-grammar/README.md`) are the baseline they must move.
