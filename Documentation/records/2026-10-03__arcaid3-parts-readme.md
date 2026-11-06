# ARCAID3: from a Kaggle ARC-AGI-3 record to a way of teaching machines how to look

*2026-10-03. Three parts. Each makes claims only as far as files in this repository support them, and each comes with the script that recomputes its numbers.*

| Part | Question | Read | Recompute |
|---|---|---|---|
| **I. Record** | What do our submissions, experiments and logs actually show, and how do they compare with other teams'? | [`part1/PART-I-FINDINGS.md`](part1/PART-I-FINDINGS.md) | `python3 arcaid3/part1/part1_facts.py` |
| **II. ARCAID3** | Can the same material be turned into graded "ways of looking" at any game? | [`part2/PART-II-ARCAID3.md`](part2/PART-II-ARCAID3.md) | `python arcaid3/part2/evaluate_views.py`, `motion_eval.py`, `derive_rows.py` |
| **III. Submission** | What can be submitted now that shows Part II, and how should it be judged? | [`part3/PART-III-SUBMISSION.md`](part3/PART-III-SUBMISSION.md) | `python3 arcaid3/part3/build.py`, `python arcaid3/part3/test_cell.py` |

## The three findings that carry the argument

1. **Our agent lost on understanding, not on clumsiness.**
   - On the 433 levels it cleared, it used a median of 0.71× the human's moves.
   - 62% of all its moves went into the one level per run it never cleared.
   - Separately, the teams that reached 20–28 did so mostly by giving the same kind of agent far more working memory (7–34×) and sharing time between games by a scheduler. (Part I)
2. **A screen can be read back into something close to the code that drew it, and that reading can be graded.**
   - The true world size is recovered on 93% of screens.
   - Where an object is isolated, 96% of the lexicon's names correspond to exactly one of the designer's sprite names.
   - From recorded play, a game's control scheme falls out as one line, e.g. "G moves (−5, 0) on ACTION1".
   - The limits are measured too: about 23% of objects can't be separated in any still picture, and 3 games are drawn mostly by their own interface code. (Part II)
3. **The reading fits into the strongest public lineage we have, as one optional view.**
   - It is one cell on Scott Le Grand's notebook, tested against the real Duck sandbox.
   - It comes with a mechanism check and falsifiers, so a single lucky or unlucky draw cannot be mistaken for a result. (Part III)

## Names, used correctly

- **ARC-AGI-3** is the benchmark. **ARC Prize 2026** is the competition, run on Kaggle. Its score is **RHAE**: per level `min((human actions / agent actions)², 1.15)`, weighted by level number, averaged over games.
- **Tufa Labs** wrote the **Duck** solver and harness (Milestone 1 winner). **TAAF** is the framework name on the bundle that packages Duck for Kaggle; the bundle does not expand the acronym.
- **Scott Le Grand** wrote `taaf-flashnext-sheetu12b-0922`: a Duck fork with Flash-Next serving and "agentfix" repairs, including F13/F19 animation frames.
- **Our lineage:**
  - our **3.59** is a fork of keithtyser's Flash-Next port of Duck;
  - our **3.90** is Scott Le Grand's notebook plus our Change A;
  - our **4.17** is Scott Le Grand's notebook unchanged.

  None of them is a direct edit of Tufa Labs' own notebook.
- **Public LB draw** means one scored run on the hidden games. **Save run** means a run on the 25 public games. Every log in this repository is from save runs.

## What is new in this folder (relative to the repo before 2026-10-03)

- `part1/part1_facts.py` and its JSON: one deterministic pass over every submission, save run, serving log and external notebook.
- `part2/lexicon.py`: a screen-to-code transcoder (standard library only).
- `part2/groundtruth.py`, `evaluate_views.py`, `motion_eval.py`: grading against the engine's own sprites, on public games only.
- `part2/results/`: measurements, code samples and per-game data dictionaries.
- `corpus/rows-2026-10-03-arcaid3-views.jsonl`: the measurements as corpus rows. Append-only; no earlier corpus file was changed.
- `part3/`: the submittable notebook, the paste-in cells, the build script and the tests.

## Environment for the engine-based scripts

```
python3.12 -m venv .venv && . .venv/bin/activate
pip install arc-agi==0.9.8 arcengine==0.9.3 numpy      # the competition-pinned versions
```

Part I and `derive_rows.py` need only plain Python 3.
