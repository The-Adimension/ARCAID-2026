# Surprise signal on wall levels: test result

**Script:** `inputs/surprise_walls.py` (CPU only, no GPU).

**Cases:**
- The 36 wall runs from `consult/walls_2026-09-21.md`: `1345/` depthrun1, stallrun2 and resetrun2–4, i.e. 6 games × 6 runs.
- The same test repeated on all 186 unique saved runs.

## Signals

Both signals are computed from observations only, without the model:

- **`s_frame`**, at level entry: the share of the level's first-frame foreground pixels (HUD border masked) drawn in colours never seen in earlier levels of the run.
- **`s_eff`**, over the level's first 10 actions: the share of actions whose effect signature was never seen in an earlier level. The signature is the action plus the set of (old colour → new colour) pairs among the changed cells.

## Results

| | 36 wall runs | All 186 runs |
|---|---|---|
| Levels ≥ 2 entered (stuck / cleared) | 134 (36 / 98) | 316 (118 / 198) |
| **Q1** AUC `s_frame`, stuck vs cleared | **0.65** | **0.64** |
| **Q1** AUC `s_eff`, stuck vs cleared | 0.53 | 0.46 |
| **Q2** `s_frame`, failing vs winning run on the same level | equal in 50 of 50 pairs | equal in 587 of 587 pairs |
| **Q2** `s_eff`, failing vs winning run on the same level | fail higher 16, equal 18, lower 16 | fail higher 122, equal 236, lower 229 |
| **Q3** share of stuck-level actions taken after action 10 | 96.3% | 94.6% |

Wall levels solved in some runs and failed in others show large action gaps. Median actions for winners vs losers:

| Level | Winners | Losers |
|---|---|---|
| sb26 L2 | 28 | 171 |
| ar25 L3 | 55 | 526 |
| re86 L4 | 144 | 348 |
| ft09 L4 | 33 | 357 |

## Reading

1. **Screen surprise weakly flags hard levels.** An AUC of 0.65 means new colours at level entry go with getting stuck more often than chance, but far from reliably.
2. **Effect surprise carries no signal** (AUC 0.46–0.53).
3. **Neither signal separates a run that will misread the goal from one that won't.**
   - `s_frame` is identical by construction: the game is deterministic, so the same level shows the same screen.
   - `s_eff` splits evenly between winners and losers.
   - This matches the walls study: winners and losers perceive the level identically. The difference is inside the model's reading of the goal.
4. **There is room to intervene.** About 95% of the actions on stuck levels come after the tenth.

## Verdict

- Surprise can be used only as a cheap "this level is new" flag.
- Anything it triggers (for example, the walls study's fix B: "list what is new; treat the previous level's rule as a hypothesis") would fire for winners and losers alike.
- Its value therefore depends on the model's response, which can't be measured offline. It needs live runs, judged against a multi-run baseline, not the 6-game probe.
- A model-free System 1 cannot tell a misreading run from a good one on this data.
