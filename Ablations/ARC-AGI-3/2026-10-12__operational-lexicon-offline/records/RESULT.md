# Do the "operational lexicon" proposals target where score is lost? No (2026-10-12)

**Question:** before spending GPU on `predict(action)`, `unexplained_recent()`, a richer rule grammar, better tracking or loop-based exploration hints, does the lexicon know anything useful on the level attempts where score is lost?

**Answer: no, on all three pre-registered tests** (`DECISION_RULE.md`, committed before the run as `6ebf3049`).

| Test | What it measures | Rule | Result | Decision |
|---|---|---|---|---|
| A. `predict(action)` | Informative and right (I) vs misleading (M), steps of stuck attempts | kill if I < 30% or M ≥ I | **I = 5.7%** (95% CI 2.8–9.8%), **M = 69.7%** | **kill** |
| B. `unexplained_recent()` | Steps with ≥1 change no rule explains, stuck attempts | kill if > 50% | **90.3%** (95% CI 85.9–93.9%) | **kill** |
| C. loop score as a stuck detector | AUC for "never finishes", attempts alive at 40K tokens | wire in if ≥ 0.70 | **0.491** (95% CI 0.400–0.581) | **do not wire in** |

## Data and method

- **Plays:** Franzen M2 v3, 4 passes × 25 public games = 100 runs and 21,245 actions. Replayed on the official engine; replay matched the stored level counts on 100 of 100 runs.
- **Attempts:** 484 level attempts: 417 completed and 67 unfinished. Graded steps (non-RESET, from an attempt's 10th action): 11,604 completed and 4,883 unfinished.
- **Lexicon and grammar:** exactly as shipped in lexicon v5 (`src/`).
- **The learner reads every earlier step of the attempt,** not the shipped 60-step window, so the test favours the proposal.

## Test A in detail

| Steps | n | I | M | unknown | lenient I | lenient M |
|---|---|---|---|---|---|---|
| Stuck attempts | 4,883 | 5.7% | 69.7% | 24.6% | 49.3% | 26.1% |
| Stuck, new actions (key used ≤ 2 times before) | 664 | 2.7% | 38.9% | 58.4% | 26.1% | 15.5% |
| Completed attempts | 11,604 | 5.3% | 68.3% | 26.4% | 52.7% | 20.9% |

- **Strict vs lenient grading.**
  - *Strict*, the pre-registered grade and the one the rule-grammar work uses: every prediction came true and every change on screen was predicted.
  - *Lenient*: every prediction came true, even if other things also changed. Timers and counters (ls20, wa30, su15) make nearly every step inexact under strict grading, so the lenient column is the fair upper bound. **It does not rescue the proposal:**
    - **Where a prediction would be news,** on actions the agent has barely tried, the tool is right 26% of the time and says "unknown" 58% of the time.
    - **Where it is right,** it is repeating what the agent has already seen many times.
- **Same level, stuck vs completed** (29 levels with both): lenient-right share 51.1% on the stuck attempt vs 49.4% on the completed one. The stuck attempt is higher on 13 of 29. **What the rule engine can model does not separate failure from success.**
- **ft09 shows it plainly.** The rules predict 97.3% of its stuck steps exactly, and the agent is stuck anyway. Stuck is a goal and plan problem, not a mechanics problem.

## Test C in detail

| Feature (at 40K tokens on the level; 160 attempts, 64 never finish) | AUC | 95% CI |
|---|---|---|
| loop30 (primary): share of the last 30 actions landing on a seen interior screen | 0.491 | 0.400–0.581 |
| loop over the whole attempt | 0.495 | 0.401–0.584 |
| rule exact rate so far | 0.522 | 0.459–0.583 |
| unexplained share | 0.483 | 0.395–0.570 |
| actions so far | 0.575 | 0.484–0.667 |

- **At 60K** the loop score is 0.439. No lexicon feature tells a stuck attempt from a slow one.
- **Tokens alone already do the selecting:** 60% of attempts alive at 40K finish later, 40% at 60K, and 8.6% (3 of 35) at 100K.
- So a restart, if any, should trigger on tokens. A lexicon gate adds nothing.

## What it means for the seven proposals

- **1. Queryable prediction + unexplained (the top-ranked one):** killed by A and B. The query would mostly answer "unknown" or be wrong, and the counterexample signal fires on 9 of 10 steps.
- **2. Richer grammar / induction and 3. Tracking:**
  - They pay off only by raising A's I on stuck attempts, from 5.7% (strict) or 26% (lenient, new actions).
  - The grammar's own record says the public-game gap is perception and long-tail mechanics. Moving v3 → v4 perception took public "changes explained" from 16.5% to 16.6%.
  - There is no evidence a 3-week push reaches the 30% bar, and even then the model has to use it. The passive view's GPU A/Bs measured −4.9 points of clear rate (CI −10.2 to +0.4), −0.03 and −0.33.
- **4. Exploration hints / loop detection:** killed by C. The "suggest a deliberate reset when stuck" part survives, but triggered on tokens; that is the restart (`kaggle/restart-dfranzen/`).
- **5. Token efficiency:** tokens are near saturation (+0.26 demo points per +10% tokens, 2026-10-10 memo), so compact views buy almost nothing.
- **6. Evaluation:** already in place: replicates, LB-like A/B and level trials on `origin/claude/gracious-thompson-6is9pp`. This folder adds the cheap decision-level offline test that the independent review asked for.
- **7. Click by object id, probe actions, auto-verification:**
  - These save actions or LLM calls on levels the agent already completes.
  - Those levels already run at a median 0.64× the human action count, and 80% are at the 1.15 cap. Worth 0–2 points at most.

## Reproduce

```
git show origin/claude/vibrant-keller-ksqha6:analysis/2026-10-10/data/dfranzen-m2-v3/benchmark.json > /tmp/dfranzen-v3.json
python experiments/2026-10-12__lexicon-proposals-offline/replay_probe.py /tmp/dfranzen-v3.json /tmp/probe.jsonl 4   # Python 3.12, arc-agi 0.9.8, arcengine 0.9.3; ~25 min on 4 cores
python experiments/2026-10-12__lexicon-proposals-offline/summarize.py probe.jsonl.gz                               # the committed output; ~1 min
```

| File | What it is |
|---|---|
| `DECISION_RULE.md` | the rule, committed before the run |
| `replay_probe.py` | replay and per-step grading |
| `summarize.py` → `summarize.out` | the three tests |
| `probe.jsonl.gz` | per-step output of the run (sha256 `3f32bcf3…`) |
| `src/` | lexicon v5 and the rule grammar, copied from `92e8ac6d` |
