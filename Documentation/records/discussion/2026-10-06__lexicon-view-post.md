# Reading the screen back into code: a "lexicon view" for the Duck sandbox (with an honest null result)

Hi all. This post shares one idea, what it cost to run, and what it scored. The short version: the model uses the view and it costs nothing to serve, but there is no measurable score effect yet.

## The idea

ARC-AGI-3 games are small programs. They place named multi-colour sprites on a small grid (often 16×16 or 32×32) and scale it up to 64×64. The **lexicon** works backwards from the screen alone:

- it finds the true cell size;
- it cuts the world into objects, including multi-colour ones;
- it gives each distinct picture a short name that stays stable for the whole game, and links rotated or mirrored copies;
- it prints the board as a legend plus placements, and reports changes between frames at the object level.

In the Duck Python sandbox it appears as `current_frame.code`, `current_frame.changes_since(previous_frame)`, `.objects` and `.native`. It is one notebook cell, standard library only. The cell tests itself through the real sandbox and rolls back to stock if anything fails.

```
SCREEN 64x64 = world 32x32 cells, each cell 2x2 px ...
OBJECTS 41 in 11 kinds:
  A x20 @ (1,2) (1,10) (1,19) ...
  C x1 @ (5,6)
LEGEND:
  C 3x3 [W,g,R]: gWg/WRg/gWW
  F 3x3 [g]: ggg/g../g..
  G 3x3 [g] = F mirror: ggg/..g/..g
```

*[Figure 1: upload `figures/arcaid3-lexicon/lexicon-figure.gif` (animated) or `lexicon-figure-final.png` (still) here. Caption: the real level-1 screen of ft09, read into a true grid, 41 objects, 11 names and the code the model sees.]*

## Why I tried it

Our own runs lost on *understanding* levels, not on clumsy play. On levels it cleared, the agent used a median of 0.71× the human's moves. Yet 62% of all its moves went into the one level per run it never understood.

In this lineage, the one change reported to move the hidden board was also about perception: Scott Le Grand's animation frames, offered in the sandbox.

*[Figure 2: upload `figures/arcaid3-lexicon/pipeline.png` here. Caption: the four steps run on the screen alone in the Duck sandbox; steps 1–3 were graded against the engine's own sprites on the 25 public games.]*

## How well it reads the screen

I graded it against the engine's own sprites on the 25 public games:

- **True world size:** recovered on 93% of screens.
- **Objects broken into pieces:** roughly halved compared with single-colour segmentation (31% → 16%).
- **Names:** where an object is isolated, 96% of the lexicon's names map to exactly one of the designer's sprite names.
- **Length:** about 3.4× shorter than the ASCII board.
- **Limits:**
  - About 23% of objects touch a same-colour neighbour, and no still picture can separate them.
  - A few games (bp35, lf52, m0r0) are drawn mostly by interface code.

## Lesson: offering a view is not enough

In version 1 the model read the view in **0 of 1,130** tool calls. The harness prompt says three times that a frame exposes "only" five fields, and that segmentation is "the primary view".

Version 2 does three things:
- corrects those lines;
- adds a "when to look" line;
- adds a cue on a new board.

With those changes, usage was **22%** of calls on the sheetu base and **12%** on dfranzen's base. On dfranzen's base, his `frame_diff()` already covers object changes.

## Results

| Base | + lexicon view | Same base, unchanged |
|---|---|---|
| Scott Le Grand's sheetu12b | **4.56** | about 4.2–6.1 |
| Daniel Franzen's Milestone 2 | **24.95** | about 21–29 (mean ≈ 26) |

A matched save run on dfranzen's base (10 public games, 25 min, against his own v1 run) gave:
- levels: 42 vs 40;
- prompt tokens served from cache: 94.3% vs 94.2%;
- throughput: 602 vs 616 tok/s.

So the model reads the view and it costs nothing to serve, but **no score effect is visible**. A single submission can't detect an effect below about 30%, and copies of identical code already span 21–29 (see Son Pham's thread on the variance of Franzen copies). The 25-point level comes from dfranzen's serving and memory work, not from this view. Tong Hui Kang's comparison of the Milestone 2 winners explains that work well.

## Notebooks

- [Lexicon view on dfranzen's Milestone 2 notebook (LB 24.95)](https://www.kaggle.com/code/habanwer/arcaid3-lexicon-view-dfranzen-m2)
- [Lexicon view v2 on sheetu12b (LB 4.56), the minimal version](https://www.kaggle.com/code/habanwer/arcaid3-lexicon-view-v2)

## Built on

- [Daniel Franzen's Milestone 2 solution](https://www.kaggle.com/code/dfranzen/arc-agi-3-milestone-2-solution)
- [Scott Le Grand's sheetu12b](https://www.kaggle.com/code/scottlegrand/taaf-flashnext-sheetu12b-0922)
- [keithtyser's Flash-Next serving](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp)
- [Tufa Labs' Duck harness](https://www.kaggle.com/code/jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner)

Context threads: [Comparing the Milestone 2 winning solutions](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/744792) and [Franzen copies, variance analysis](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/745062).

## Next

- Split merged objects when only part of them moves.
- Add a view of the interface layer.
- Run several replicates at matched tokens, so a 10% effect could show up.

Feedback is very welcome, especially from anyone who has tried structured board views with a stronger model or with more replicates.
