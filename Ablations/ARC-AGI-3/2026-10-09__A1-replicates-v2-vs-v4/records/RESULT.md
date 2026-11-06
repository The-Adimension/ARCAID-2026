# Replicates: lexicon v2 against v4, three save runs each (2026-10-09)

**Question:** v4 scored 55.36 against v2's 42.61 in one save run each, on the same 10 public games (+12.75 points). Is the gain real?

**Answer: no.** Over three runs each, the two versions are indistinguishable:

| | Mean of the three 10-game means | Levels cleared |
|---|---|---|
| v2 | 48.15 (SD 5.91) | 46.3 |
| v4 | 47.81 (SD 6.54) | 46.3 |

- **Difference (v4 − v2):** −0.33 points.
- **Exact permutation test:** p = 0.55.
- **v4's 55.36 was the luck of one draw.** One v2 replicate scored 54.37.

## Design

**Notebooks.** Each replicate is the notebook exactly as pushed for that version, taken from git and byte for byte the same.
- v2 is commit `c46578a4` and v4 is commit `9b87fd2e`.
- Each copy runs in its own private kernel: `arcaid3-rep-{v2,v4}-r{1,2}`, written by `kaggle/lexicon-dfranzen/replicates.py`.

**Pairing.** The replicates ran in pairs, one v2 and one v4 at the same time: round 1 from 09:18 UTC, round 2 from 09:56 UTC. That puts both arms under the same conditions on the same day.

**Settings.** The same 10 demo games and settings as every earlier save run: 25 min per game, 10 streams, 1 pass.

**What each arm contains.**
- Two replicates.
- The original save run: Kaggle version 2 (2026-10-07) for v2, and version 4 (2026-10-08) for v4.

**Reproduce:** `python3 kaggle/lexicon-dfranzen/compare_replicates.py` (output in `compare_replicates.out`; add `--fetch` to download again).

## Six runs

| Run | Levels | 10-game mean | Prompt from cache | Tool calls reading the view | `.rules` reads |
|---|---|---|---|---|---|
| v2, original (version 2) | 43 | 42.61 | 94.7% | 11.1% | — |
| v2, replicate 1 | 45 | 47.46 | 95.0% | 7.8% | — |
| v2, replicate 2 | 51 | 54.37 | 94.8% | 10.6% | — |
| v4, original (version 4) | 50 | 55.36 | 93.9% | 17.0% | 40 |
| v4, replicate 1 | 44 | 43.70 | 94.1% | 16.5% | 39 |
| v4, replicate 2 | 45 | 44.38 | 91.5% | 16.8% | 24 |

**All six installed with every self-test ok** (`ARCAID3_LEXICON_READY`). The final counters report 0 errors.

**The logs are alike across runs.** Each has the same handful of "timed out at action N; yielding" lines. These are model requests cut off when a game's 25-minute budget ends, not tool failures. The original runs show the same lines.

## Statistics

- **Exact permutation test.** All 20 ways of splitting the six runs into two groups of three were tried.
  - On the means, p = 11/20 = 0.55.
  - On levels, p = 12/20 = 0.60.
- **Noise of a single run.** The SD of one 10-game mean is **6.2 points** (pooled within arms). This matches the earlier estimate of about 7.
- **95% interval for v4 − v2:** −14.5 to +13.8 points (t with 4 degrees of freedom).
  - So the replicates rule out an effect as large as v4's first run suggested.
  - They cannot detect a small effect.
- **Runs needed to detect a gain.** With an SD of 6.2 per run, at 80% power and 5% two-sided:

  | Runs per arm | Smallest detectable gain |
  |---|---|
  | 3 | about 19 points |
  | 5 | about 11 points |
  | 10 | about 8 points |
  | 20 | about 5.5 points |

## Per game (mean score over the three runs; levels per run in brackets)

| Game | v2 | v4 |
|---|---|---|
| ar25 | 42.6 (5/4/6) | 47.2 (5/6/5) |
| ft09 | 100.0 (6/6/6) | 74.1 (6/6/3) |
| lp85 | 38.9 (4/3/7) | 47.2 (6/5/5) |
| r11l | 11.1 (1/2/2) | 30.2 (2/3/4) |
| re86 | 37.0 (5/4/5) | 32.4 (5/4/4) |
| sb26 | 100.0 (8/8/8) | 91.3 (8/7/8) |
| sc25 | 38.9 (4/4/3) | 29.3 (3/2/4) |
| tr87 | 52.7 (4/5/4) | 73.0 (6/4/5) |
| tu93 | 34.2 (3/5/7) | 22.5 (5/4/3) |
| vc33 | 26.0 (3/4/3) | 31.0 (4/3/4) |

- **No game separates the two arms beyond its own spread.**
  - In v4's first run, tr87 cleared 6 levels; its replicates cleared 4 and 5.
  - In v2's second replicate, tu93 cleared 7 levels.
- **r11l favours v4 in all three runs** (2–4 levels against 1–2). With 10 games and 3 runs, one such game is expected by chance, so it is a lead to check, not a finding.

## What changed and what didn't

- **Behaviour changed, reproducibly.** v4 reads the view in 16.5–17.0% of tool calls, against 7.8–11.1% for v2. It reads `.rules` 24–40 times per run. So the cue does what it was built to do.
- **The score did not change.** More structured looking, as delivered by v4, does not turn into more levels on these games.
- **The submission agrees.** v4 scored 27.05 on the public leaderboard, inside the 21–29 band of unchanged dfranzen copies.

## What this means for earlier readings

- **Single-run gaps of 5–13 points between versions were noise.** That covers:
  - lexicon v1 against dfranzen v1 (+4.6);
  - v2 against v1 (+1.5);
  - v4 against v2 (+12.75).
  - Each was already flagged as within noise. Now the noise is measured.
- **Lexicon versus no lexicon is not tested here.** Both arms carry the lexicon, and dfranzen v1 has one run (36.56). If that comparison matters, it needs its own replicates.

## Next

1. **Judge changes offline first.** The engine-graded measures have no run-to-run noise: perception (`eval_perception_v4.py`) and rule prediction (`design/2026-10-07__rule-grammar/run_compare.py`). A save run then only checks that nothing breaks.
2. **When a score claim is needed, plan the runs up front.** Detecting a 10-point gain takes about 5–6 runs per arm, in pairs. Each pair uses both GPU slots for about 40 minutes.
3. **Make the view change what the agent does.** The model now looks more often but plays no better. The next lever is the content, not the cue: rules that predict sooner, and a way to test an action before taking it (`simulate`).
