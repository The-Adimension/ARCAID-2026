# System-1 replay (design 1): what an online state graph could have answered

**Script:** `inputs/replay_system1.py`. It uses the pinned engine (arc-agi 0.9.8, arcengine 0.9.3), runs on CPU in 26 s, and needs no GPU.

**Corpus:** every saved `benchmark.json` in `submissions/`, `experiments/` and `inputs/arc3-collections/1345/`.
- 186 unique runs (40 duplicates removed) and 28,159 actions, all chosen by the model.
- All 25 public games appear, but 97% of the actions come from ar25, re86, vc33, sb26, ft09 and lp85.

## Result

The table uses the HUD-masked screen (2-cell border masked), which gives the upper bound.

| | Cleared levels | Stuck levels | All |
|---|---|---|---|
| Actions | 10,021 | 18,138 | 28,159 |
| Known no-op: the same (screen, action) already did nothing | 4.0% | 13.2% | 9.9% |
| Known result: the same (screen, action) already tried, and it changed something | 4.2% | 8.7% | 7.1% |
| First-time no-op: a lookup can't know it; a learned effect model could | 7.0% | 10.7% | 9.4% |
| New: a first try that changed something | 84.9% | 67.3% | 73.6% |
| **Removable** (walks through known territory, minus the shortest known path) | **5.7%** | **17.9%** | **13.6%** |

- **Model calls:** 347 of 4,762 (7.3%) consisted only of known moves. They account for 3.8% of generated tokens.
- **Score on these runs:** 12.14 → 12.28 (+1.2%) once the removable actions are cut from cleared levels.
  - Cleared levels are already close to human pace, so there is little to gain there.
  - On stuck levels, the removable actions are wall-clock time, not score.

**Lower bound (exact screens, no mask):** removable 4.9%, all-known calls 2.0%, tokens 0.9%, score +0.1%.

## Validity checks

1. **Replay is exact.** Level counts match on all 186 runs. The score reproduces `benchmark.json` on all 333 runs checked, with a maximum difference of 0.0.
2. **Model-call boundaries are right.** A call starts at `generated_tokens > 0`. On the v3 probe this gives 4.63 actions per call, the same as the `ANALYSIS-2026-09-26.md` figure.
3. **"Same screen, same outcome" mostly holds.**
   - On the agent's own play: 14 of about 4,800 known pairs (0.3%) gave a different outcome from the first time.
   - Under random play (25 games × 300 actions): 92 of 2,346 (3.9%), concentrated in bp35 (35), g50t (21), ar25 (14) and sk48 (10). These games carry state that the masked screen doesn't show, so a harness must verify a "known" outcome before trusting it.
4. **The HUD mask matters.** Without it, most repeats look new: removable actions fall from 13.6% to 4.9%. The true value sits between the two bounds.

## Verdict: no-go as a score lever

- **Most actions are new.** 74% are first tries that changed the screen. A lookup can't remove them.
- **What a lookup can remove is small.** 13.6% of actions at most, 3.8% of tokens and +1.2% of score, and it's concentrated in two games (vc33 30.5%, ar25 21.6%).
- **The ceiling for a learned no-op predictor (the step-3 JEPA target) is also small:** the 9.4% first-time no-ops.
- **The loss comes from what the new actions try.** The data points to wrong goal hypotheses rather than repeated moves, which matches `inputs/arc3-collections/0393/consult/walls_2026-09-21.md`.
- **A System-1 model is worth building only if it targets that.** One option is detecting surprise at wall entries and prompting a different reading of the goal. Waste removal alone won't pay for it.
