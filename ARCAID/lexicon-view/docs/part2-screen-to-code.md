# Part II: ARCAID3, a working prototype for turning ARC-AGI-3 material into "ways of looking"

*ARCAID3 = ARC-3 AGI-Intelligence Datafication. Written 2026-10-03. All numbers come from scripts in this folder, run on the official public game files and on recordings stored in this repo. Raw results: `results/`. Corpus rows: `corpus/rows-2026-10-03-arcaid3-views.jsonl`.*

## The idea in plain words

**What an AI agent is given today.** A 64×64 picture of coloured squares, and nothing else. Some agents (like Tufa Labs' Duck) also get a few tools to inspect that picture. Whatever the agent learns, it learns from the picture as it was handed over.

**How the games are actually made.** Not as pictures. Each ARC-AGI-3 game is a short program. A level is a small world (often 16×16 or 32×32 cells) built from named **sprites**: small multi-colour pictures with properties. The engine places them, then scales the world up to fill 64×64. The picture is the *output* of that code.

**What ARCAID3 does.** It works backwards, from the picture towards something like the code:

1. it finds the world's true size;
2. it cuts the world into objects and gives every distinct object a short name that stays the same across the whole game;
3. it writes the screen as a **legend plus a list of placements**;
4. from recorded play, it builds a **data dictionary** for each name: what each action does to it.

The agent can then reason about "the thing that moves up 5 when I press ACTION1" instead of 4,096 coloured cells.

**What makes it "AGI-first" rather than another tool.** Two things:

- **Several ways of looking, side by side.** The prototype does not decide for the model how to see. It offers several views of the same screen (pixels, true-size grid, single-colour pieces, layered objects, object changes).
- **Every view is graded.** On the public games the engine's own sprite list exists, so each view is scored against the truth before anyone relies on it.

What is learned and improved is **how to inspect the input**, not a label for a game. Because no view contains anything game-specific, the same views can be applied to any game, including the hidden ones. Whether they *help* there is a separate, open question (see Part III).

## Why this follows from Part I

- **The agent's losses were levels it never understood.** It cleared 433 levels at a median of 0.71× the human's moves. Yet 62% of all its moves went into the one level per run it never cleared (Part I, §4).
- **The repo's earlier studies point the same way.** Winning and losing runs saw identical screens; the difference was the model's reading of the goal (`SURPRISE-WALLS-2026-09-27.md`).
- **Perception is where this lineage has moved the score.** In Scott Le Grand's lineage, the only change ever reported to move the hidden leaderboard was a perception change (F13: in-between animation frames offered in the sandbox).
- **So the lever worth building is a better presentation of the screen,** measured, not guessed.

## Architecture

```
L0  SOURCES            official game files (25 public games: the only ground truth)
                       recorded play: 250 agent game runs / 34,942 actions (submissions/, experiments/),
                       local_play full_actions + 62 recordings (fake 2-line "WIN" files excluded)
                       logs and transcripts, harness code, 154 external kernels
        |
L1  VIEWS              pixels -> native grid -> objects (single-colour | flat | layered)
    (frames only;      -> lexicon code (legend + placements) -> object changes (moved / became /
     agent-legal)         appeared / disappeared) ; F13 animation frames are a further view
        |
L2  DICTIONARY         per game: symbol -> {action -> effects}, with a plain-language reading
    (from plays)       e.g. "moves (-5, 0) on ACTION1 (22 of 24 times)"
        |
L3  GRADING            engine sprite ownership (evaluation only) -> exact / merged / split per
    (public only)      view; motion precision and recall; dictionary-to-sprite-name alignment
        |
L4  ROWS               every measurement becomes a corpus row with its derivation hash,
                       split = public_demo, never held-out evidence, never a training label
        |
        +--> feeds back: a graded view is deployed in an agent (Part III); its save runs are new
             recorded play (L0); the loop runs again. This is the "self-nourishing" part.
```

The files that implement it:

| File | Layer | What it does | Runs where |
|---|---|---|---|
| `lexicon.py` | L1, L2 | Native grid, objects, layered objects, symbol table, code text, object diff, plain readings. Standard library only, no imports. | Anywhere, including the Duck sandbox |
| `groundtruth.py` | L3 | Renders each level with sprite indices instead of colours, so every screen pixel is attributed to the sprite (or HUD) that drew it. Evaluation only. | Python 3.12 + pinned `arc-agi 0.9.8` / `arcengine 0.9.3` |
| `evaluate_views.py` | L3 | Grades four object views on all 183 level-start screens | same |
| `motion_eval.py` | L2, L3 | Replays 2,910 recorded actions, grades the "what moved" view and writes the per-game dictionaries | same |
| `derive_rows.py` | L4 | Writes the measurements as corpus rows | plain Python |

## What a screen looks like as code

ft09, level 1, as the lexicon writes it. Six kinds of tile plus a board, where the raw screen was 4,096 cells:

```
SCREEN 64x64 = world 32x32 cells, each cell 2x2 px, first cell at px (row 0, col 0); background B (black); 64 px drawn outside the cell grid (HUD).
OBJECTS 41 in 11 kinds (symbol xcount @ (row, col) of top-left cell):
  A x20 @ (1,2) (1,10) (1,19) (1,27) (5,10) (9,2) (9,19) (9,27) (18,6) (18,10) (18,18) (18,22) ... +8
  B x12 @ (1,6) (1,23) (5,2) (5,19) (5,27) (9,6) (9,10) (9,23) (18,2) (22,2) (22,10) (26,10)
  C x1 @ (5,6)
  ...
LEGEND (. = not part of the object):
  A 3x3 [b]: bbb/bbb/bbb
  B 3x3 [R]: RRR/RRR/RRR
  C 3x3 [W,g,R]: gWg/WRg/gWW
  F 3x3 [g]: ggg/g../g..
  G 3x3 [g] = F mirror+rot0: ggg/..g/..g
  ...
```

Notice two things:
- **The true scale is found:** a 32×32 world drawn at 2×.
- **Rotated and mirrored copies are linked:** `G = F mirror`. A model reading this sees four corner pieces of one shape, not four unrelated blobs.

## What the recordings teach: a data dictionary

From 67 agent actions in ls20, using the screens alone (`results/dictionary_ls20.md`):

```
G: moves (-5, 0) on ACTION1 (22 of 24 times); moves (5, 0) on ACTION2 (12 of 12 times);
   moves (0, -5) on ACTION3 (14 of 14 times); moves (0, 5) on ACTION4 (11 of 11 times)
```

That one line is the game's control scheme: G is what you steer, ACTION1–4 are up, down, left and right, and one step is 5 cells. Nobody labelled it.

In the click game ft09, the dictionary instead records state changes: "B became O on ACTION6 (17 of 17 times)", and pairs of symbols that toggle into each other.

## Measured results

### A. Cutting a screen into the game's own objects

Graded on 154 level-start screens (3,718 true sprite instances). 29 screens were set aside because the game paints most of them with its own drawing code (an "interface") rather than sprites: bp35, lf52, m0r0, and three sp80 and one ls20 screens. There is no sprite-level truth for those.

| View | Exact | Merged with others | Split into pieces | Pieces per true object |
|---|---|---|---|---|
| **duck**: single-colour pieces (what Duck's `current_frame.segmentation` returns) | 50.3% | 18.3% | 31.4% | 1.96 |
| flat: multi-colour pieces | 24.1% | 73.1% | 2.8% | 1.08 |
| **layered**: floors peeled off (lexicon default) | **52.6%** | 31.0% | **16.4%** | **1.35** |
| layered, 4-neighbour variant | 53.7% | 27.7% | 18.6% | 1.59 |

**How to read this:**
- **Only 19.9% of the games' visible objects are multi-colour.** So Duck's single-colour view is already right about half the time.
- **The layered lexicon halves the shattering of objects into pieces** (31% → 16%) and is slightly more often exact. It does so by merging more.
- **Neither view wins everywhere.** The layered view is better in 12 of 22 gradable games (ft09: 141 vs 96 exact; tu93: 46 vs 9) and worse in 6 (vc33: 61 vs 93; sk48: 47 vs 87). That is the argument for offering views side by side rather than replacing one with another.
- **There is a hard ceiling for any still picture.** 22.9% of true objects touch another object of the same colour. No colour-based cut can separate those from one screen. Only motion can.

### B. The true size of the world

- **True scale found on 143 of 154 screens (93%).** On 134 the block size equals the camera's scale exactly; on 9 the detector found a coarser block size that is still lossless.
- **The text is about 3.4× shorter.** The code listing averages 1,215 characters per screen, against 4,160 for the 64×64 ASCII board.

### C. What moved (motion view, from recorded play)

| Plays replayed | Actions | Precision (reported move is real, right object, right distance) | Recall (real moves that were reported) |
|---|---|---|---|
| Agent save run of the 4.17 notebook (25 games) | 1,917 | 82.4% | 53.3% |
| local_play `full_actions.json` | 353 | 82.5% | 54.0% |
| local_play recordings (fake WINs excluded) | 640 | 59.9% | 55.3% |
| **All** | **2,910** | **78.2%** | **53.6%** |

### D. Does the dictionary match the designer's vocabulary?

- **Lexicon symbols mostly name one real sprite.** Of the 458 symbols that exactly matched a sprite, 438 (95.6%) always matched sprites of the same name.
- **Sprite names mostly get one symbol.** Of 343 sprite names matched, 275 (80%) map to exactly one symbol. The rest appear in several colours or poses.
- **So where the lexicon isolates an object, its names line up with the game's own names**, recovered from the screen alone.

## What is new here, and what is not

Checked against the 154 public notebooks in `external_submission/` (top-10% teams, collected 2026-10-01) and the official sources recorded in `corpus/OFFICIAL-SOURCES-VS-CODE-2026-10-01.md`.

**Already done by others (credited):**
- **Single-colour segmentation with a containment tree:** Tufa Labs' Duck (`segmentation.py`).
- **Rotation-matched shape fingerprints and object-level frame differences, on those single-colour pieces:** Daniel Franzen's Milestone 2 notebook (`frame_diff.py`, `_object_signature`), also used by rellik13.
- **A harness-measured ledger of what each action did:** Scott Le Grand's F7 (`AGENTFIX_LEDGER`), shipped switched **off** in the 4.17 notebook.
- **In-between animation frames:** Scott Le Grand's F13/F19.
- **"Legend"** in other notebooks means a colour key (W = white, …), not an object dictionary.
- **Writing a game's rules as an executable program** is the subject of research systems with frontier models: "Executable World Models" (arXiv 2605.05138) and the Kepler `world_model.py` traces, as recorded in this repo's `memo.md` and `experiments/JEV-DATA-MAP-2026-09-27.md`; we did not re-read them. Those *write the rules*; ARCAID3 *transcribes the screen*. It could feed such a system, but it is not one.

**Not found in any of the 154 notebooks:**
1. Recovering the world's true resolution from the screen.
2. A multi-colour symbol dictionary that keeps names across frames and links rotated or mirrored copies.
3. Peeling floors to find the objects that sit on them.
4. Grading any perception view against the engine's own sprite ownership, and publishing the shortfalls (interface-drawn games, colour-inseparable objects).
5. Building a per-symbol action dictionary with plain-language readings from recorded play, and grading its "what moved" claims against the engine.

The claim is scoped to that evidence: *new relative to the public code of the 46 top-10% teams we collected*, not to everything ever written.

## Terms used, matched to the official engine (`arcengine 0.9.3`)

| Our word | Engine term | Note |
|---|---|---|
| object (true) | `Sprite` | Pixel array plus name, tags, layer, rotation, mirror, scale, collidable/visible |
| world | `Level` grid viewed by the `Camera` | The camera scales its view up by a whole number to fit 64×64, with letterbox margins |
| HUD / interface | `RenderableUserDisplay` | Drawn *after* scaling, so it breaks the block pattern; in bp35, lf52 and m0r0 it draws most of the screen |
| symbol | none (ours) | A name for a distinct picture, from the screen alone |
| ground truth | `_get_hidden_state` is **not** used | We render the level's sprites with their indices. Agents never see this, and it does not exist for hidden games |

## Limits, stated plainly

- **This is perception, not intelligence.** It makes the screen easier to read. It does not decide what to do.
- **Graded on public games only, which are "intentionally easier".** Nothing here is evidence about the hidden set.
- **About half of true objects are still cut imperfectly by any still view.** Motion (recall 54%) recovers only some of the rest.
- **Interface-drawn games** (bp35, lf52, m0r0) need a separate view of the interface layer. Not built.
- **Hidden state** (timers, counters that are not drawn) is invisible to every view.
- **The dictionary only knows what was played.** Actions never tried have no entry.

## Next steps (CPU-only, in order of value)

1. **Co-motion splitting.** When part of a merged object moves and part stays, split it, and keep that split for the rest of the game. This attacks the 23% ceiling directly.
2. **Interface view** for bp35, lf52 and m0r0, then re-grade those 29 screens.
3. **The 3,090 animation frames** in the `1345` pickles: grade the object-change view on in-between frames (inspect with class stand-ins, as the corpus rules require).
4. **Close the loop.** Run the Part III notebook's save run, feed its new recordings through `motion_eval.py`, and add the rows.

## Reproduce

```
# Python 3.12 with the competition pins
pip install arc-agi==0.9.8 arcengine==0.9.3 numpy
python arcaid3/part2/evaluate_views.py     # A, B, D  -> results/views_eval.json, results/samples.md
python arcaid3/part2/motion_eval.py        # C        -> results/motion_eval.json, results/dictionary_*.md
python3 arcaid3/part2/derive_rows.py       # L4       -> corpus/rows-2026-10-03-arcaid3-views.jsonl
```
