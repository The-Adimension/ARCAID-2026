# Part I: What our ARC-AGI-3 record actually shows

*Written 2026-10-03. Every number below is recomputed by `arcaid3/part1/part1_facts.py` from files in this repository (output: `part1_facts.json`). The script reads files only: no network, no GPU, no game engine. Leaderboard figures for other teams come from the snapshot taken 2026-10-01 11:43:58 UTC that `external_submission/` was collected against.*

## The short version

1. **Our best public score is 4.17** (rank 322 of 3,536 on 2026-10-01). It was Scott Le Grand's public notebook, submitted unchanged. Our own edits never beat it.
2. **Much of the movement between our scores is luck.** The same code can score very differently from one run to the next. One public team reports the same code scoring 5.68, 4.09 and 2.30. None of our single changes moved the score by more than that noise.
3. **Our agent was efficient when it understood a level, and lost when it didn't.** On the 433 levels it cleared, it used a median of 0.71× the human's moves. Yet 62% of all its moves went into the one level per run that it never cleared.
4. **Offline practice scores did not predict the leaderboard.** If anything, they pointed the wrong way.
5. **The teams that jumped from ~5 to 20–28 mostly changed the plumbing, not the "brain".** They used the same harness family (Tufa Labs' Duck) and much the same model, but gave it 7–34× more working memory for thinking and shared thinking time between games according to what each game could still earn. Our own analysis of 09-26 had already named that memory as our bottleneck. We could not lift it on the software we used.

## Words used in this report

| Term | Meaning here |
|---|---|
| **ARC-AGI-3** | The ARC Prize 2026 benchmark: turn-based grid games with no instructions. The agent must work out the rules and the goal by playing. |
| **RHAE** | The official ARC-AGI-3 score. A cleared level scores `min((human moves / agent moves)², 1.15)`. Later levels weigh more (level *i* of *N* carries weight *i*). A game's score is the weighted mean over all its levels, and the total is the mean over games. Uncleared levels score 0. |
| **Public LB draw** | One scored run of a notebook on Kaggle's hidden games. The public leaderboard shows a team's best draw. |
| **Save run** | Kaggle's "Save & Run All": the notebook plays the 25 *public* demo games offline. Its logs are what this repo holds. Kaggle never returns logs of the hidden-game run. |
| **Duck** | The ARC-AGI-3 solver and harness by Tufa Labs (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit, Michal Tesnar, Stefano Viel). It won Milestone 1. A language model looks at the board, writes Python in a sandbox to inspect it, and sends actions. |
| **TAAF** | The name of the framework that packages Duck for Kaggle ("TAAF Kaggle Source Bundle"). The bundle never spells out the acronym, so neither do we. |
| **Flash-Next** | The model Qwen3.8-Flash-Next, a mixture-of-experts model, run in NVFP4 (4-bit) form on the RTX PRO 6000. |
| **vLLM / SGLang** | Two different programs that serve a model (run it and answer requests). |
| **KV cache** | The model's working memory while it reads and writes. Its size limits how many games can be "thought about" at the same time. |
| **sheetu12b** | Short name of Scott Le Grand's notebook `taaf-flashnext-sheetu12b-0922`: Duck plus Flash-Next plus his "agentfix" repairs, including F13 (in-between animation frames) and F19 (a contact sheet of those frames). |

## 1. What we tried, in order

Our submissions form four families. They are a lineage, not four unrelated attempts.

```
Programmatic starter (ours, no language model)  ............  8 draws, 0.02 – 0.13
Tufa Labs Duck harness (June 30 Milestone 1 winner)
 ├─ foysalemonshanto's Qwen3.8-27B fork, copied ...........  1 draw,  1.37
 └─ keithtyser's Flash-Next port
     ├─ our edits (batching, stall, reset, ledger, prompts, compact, Change A)
     │   ...................................................  10 draws, 2.49 – 3.59 (mean 3.01)
     └─ Scott Le Grand's sheetu12b (agentfix + F13/F19)
         ├─ + our Change A ("reasoning notes") .............  1 draw,  3.90
         └─ unchanged ......................................  1 draw,  4.17
```

- **The programmatic starter** explored the game, built a small rule model, checked it, and then planned. It never broke 0.13.
- **Moving to a language-model agent (Duck) was the one step that clearly paid:** 0.13 → 1.37, then 2.49–3.59 once the faster Flash-Next model was served.
- **The 4.17 notebook is Scott Le Grand's code, byte for byte.** Its code cells match the public `scottlegrand/taaf-flashnext-sheetu12b-0922` in `external_submission/` with 0 lines different. Our 3.59 notebook is keithtyser's notebook plus 367 added and 18 removed lines.
- **A note on names.** The 3.59 and 3.90 notebooks are both descendants of Tufa Labs' Duck. The 3.90 one is Scott Le Grand's notebook with our Change A, not a separate Tufa Labs fork.

## 2. How much of a score is luck

| Evidence | Numbers |
|---|---|
| Our 9 Flash-Next draws, 09-19 to 09-27 (different small edits, same base) | mean 3.07, spread (SD) 0.33, range 2.57–3.59 |
| One public team, **same code** three times (AFF AI CLUB, stated in their notebook) | 5.68, 4.09, 2.30: a range of 3.38 |
| Scott Le Grand's notebook, unchanged: his draw vs ours | 5.19 (his, per the Kaggle code tab on 09-27, recorded in `report-2026-09-27.md`) vs 4.17 (ours) |

**What this means:** one leaderboard draw cannot tell two versions apart unless they differ by more than about a point. Every single change we tested landed inside that band:

| Single change | Base → with change |
|---|---|
| Change A on our v3 (81 lines added, 0 removed) | 3.59 → 3.03 |
| Change A on sheetu12b (81 lines added, 0 removed) | 4.17 → 3.90 |
| RESET allowed vs not (v3 → v4) | 3.37 → 2.84 |

None of these is evidence that a change helped or hurt. They are single draws inside the noise.

## 3. Practice scores pointed the wrong way

- **Six-game offline probes vs the leaderboard (6 versions):** correlation −0.24 (Pearson) and −0.37 (rank order). The version with the lowest probe score (25.08) had our best Duck leaderboard score (3.59).
- **Full 25-game save runs disagree too.** 0.89 and 0.79 offline went with 2.49 and 3.04 on the leaderboard; 8.68 and 7.80 went with 3.90 and 4.17.
- **Why:** the 25 public games are "intentionally easier" (official technical report) and differ from the hidden ones. The probes also ran with far more thinking time per game than the hidden run allows (6 games at once instead of 28). Practice measured a different situation.

## 4. Where the agent's moves went

Across every saved run in this repo (250 game runs, 34,942 actions, all 25 public games):

- **On cleared levels the agent was efficient.** On 433 cleared levels, its median was 0.71× the human baseline's moves, and 76% were at or below human. Under RHAE a level is capped at 1.15, so better efficiency here was worth almost nothing.
- **Most moves went into the level it never cleared:** 21,769 of 34,942 actions (62%).
- **Three games were never cleared once in any run:** cd82, g50t and sk48.
- **What this says:** the score was lost to *not understanding a level*, not to clumsy play. The repo's own earlier studies say the same thing in other words:
  - `SYSTEM1-REPLAY`: 74% of moves were first tries that changed the screen. Removing repeats would have added only about 1%.
  - `SURPRISE-WALLS`: winning and losing runs saw identical screens. The difference was in how the model read the goal.

**This is the bridge to Part II.** If the bottleneck is reading the level correctly, then *how the level is presented to the model* is the lever worth studying.

## 5. What the 20+ teams did differently (comparison with `external_submission/`)

We collected 154 public notebooks from 46 teams in the top 10%. The only big jump visible in public code is between two groups:

| | Our runs; Scott Le Grand; keithtyser | Published Milestone 2 notebooks at 20+ |
|---|---|---|
| Harness | Tufa Labs Duck | Tufa Labs Duck (heavily patched) |
| Model | Qwen3.8-Flash-Next | Qwen3.8-Flash-Next (various quantisations) |
| **Working memory (KV cache), from their own logs** | **105,202 tokens** | **1,011,264** (Daniel Franzen, team best 27.89), **1,004,288** (rellik13, 22.53), **3,576,997** (face-of-agi, 20.00) |
| Serving program | vLLM | SGLang fork (Franzen, rellik13), or vLLM with 4-bit cache storage (face-of-agi) |
| Time between games | fixed slice per game | shared by a scheduler: games that can still earn points get more turns (Franzen, rellik13; AFF AI CLUB's "attention lottery") |
| Perception repairs | F13/F19 animation frames (Scott Le Grand) | animation frames, UNDO (ACTION7) made usable, object-level frame differences |

**Read with care:**
- **A team's best score is not necessarily this notebook's score.** Kaggle does not show other teams' per-notebook scores. The three notebooks above are each titled as that team's Milestone 2 submission, which makes the link likely but not proven.
- **AFF AI CLUB's published version** ran a memory size close to ours (125,898 tokens), and its own text says that version was "not yet scored". Their stated scores for earlier scheduler versions on a base like ours are 5.68 and 5.75.
- **Our own 09-26 analysis** (`submissions/ANALYSIS-2026-09-26.md`) found this exact bottleneck: 3–5 requests running for 28 games, and roughly half the thinking per game that the probes had. The fix it proposed (an 8-bit cache) was blocked on our vLLM build. The 20+ teams got past it by changing the serving software.

**So the deterministic lesson of Part I:**
- with this harness and model, scores were limited first by how much thinking fits into 9 hours;
- second, by how that thinking is shared between games;
- prompt and memory tweaks came a distant third, and their effects are invisible in single draws.

## 6. What this record cannot tell us

- **How our code behaved on the hidden games.** Kaggle returns no logs of the scored rerun. Every log here is from public games.
- **Whether any single change helped.** There is one draw per change and no replicates.
- **Private-leaderboard scores.** None is known for any of our 21 submissions.
- **Whether the 20+ teams' gains came from memory, scheduling or their many other patches.** No public ablation separates them.

## Reproduce

```
python3 arcaid3/part1/part1_facts.py      # writes arcaid3/part1/part1_facts.json
```
