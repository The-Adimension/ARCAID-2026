# Rule grammar: one rule shape instead of rule kinds

*2026-10-08. Follow-up to `../2026-10-07__lexicon-code/`. The aim is AGI-first and game-agnostic: the 25 public games are examples of a vast space, not the rulebook.*

## What changed, and why

The first prototype had nine rule kinds: steer, toggle, solid, remote, tick and others. Their names came from patterns seen in the 25 public games, which makes them a small rulebook. This folder replaces them with one rule shape that composes:

```
when <trigger> [if | unless <relation>] then <verb>(<who>, <how>)
```

| Part | Allowed values | Where it comes from |
|---|---|---|
| trigger | an action (ACTION1 … ACTION7; ACTION6 carries its click), or `any` | the benchmark interface |
| who | `clicked`, `all`, `same_as_clicked`, `touching_clicked`, `colour:c`, `touching:S`, `pic:S` | Core Knowledge relations; `pic:S` names one picture and costs more, so a relation wins a tie |
| relation | `touch:c` (contact), `path:c` (something in the way), `click:c` (what the action targeted); `c` may be `edge` | contact and solidity (Core Knowledge), and the action's own argument |
| verb / how | `move(d)`, `recolor(map)`, `turn(transform)`, `resize(delta)`, `reshape(to S)`, `vanish`, `appear(S, where)` | the engine's sprite operations, as the screen shows them |

One rule may range over several actions: one selector and one verb, with a parameter per action. It pools the evidence of those actions. This holds for any verb, so it is part of the grammar rather than a steering kind.

**Learning (`rule_grammar.Learner`):**
1. Every observed change proposes the rules that would have produced it, under every selector that picks its object.
2. Each candidate is scored on every step of the level: hits, false predictions, and changes explained.
3. A greedy minimum-description choice keeps a rule only if the changes it explains outweigh its false predictions plus its own length.
4. A rule with false predictions may buy one condition, found by searching the relations above.
5. Changes that no kept rule explains form the **residual**: where to look next, and what a language model can be asked to explain.

**Prediction is closed-world:** when no rule fires, nothing is predicted to change.

Nothing in `rule_grammar.py` refers to a game, a picture or a colour.

## How it was tested

Both learners read the same lexicon screens (with the per-level cell-size lock). Before every step, each is re-learned from the level's earlier steps only, predicts the step, and is then judged on it.

- **Changes explained:** a change counts only if a correct prediction specifies it fully: where the object moves, which colours it takes, which picture it becomes, where something appears.
  - Under this rule, "X moves" or "the clicked object changes" is right when it happens, but doesn't predict the next screen.
  - That looser count is reported as *any*.
  - Several old rules make only such predictions: tick, remote, effect, and the click rules.
- **Steps exact:** every prediction came true, and every change was explained.

**The two test beds:**

| Test bed | What it is |
|---|---|
| **public** | The 25 public games: 55 recorded agent plays from four save runs, replayed on the official engine (5,948 steps). |
| **worlds** | 20 games generated with the official engine (`worlds.py`), 2 layouts each, 150 actions per layout (6,000 steps). Actions come from a game-agnostic explorer: a random available action, with clicks on a random object it sees (70%) or a random pixel (30%). |

**The world mechanics** were picked to fall outside the old kinds:
- gravity, pushing, a chaser, conveyors, ice, a painting trail, teleport pads, a mirrored twin, a timer bar;
- lights-out, click-to-spawn with gravity, a global colour swap, rotation on ACTION5, scrambled controls.

Three controls are ones the old kinds do cover: walls, colour cycling and click-to-remove.

The worlds were written by the same person as the learner, which is a bias. Their specs were fixed before any world result, and every result is reported.

## Results (`run_compare.out`)

| | Predictions right | **Changes explained** | **Steps exact** | Changes, any |
|---|---|---|---|---|
| **Worlds**: old kinds | 65.7% | 18.3% (1755/9606) | 31.9% (1912/6000) | 29.5% |
| **Worlds**: grammar | 81.7% | **33.6%** (3227/9606) | **46.9%** (2815/6000) | 40.5% |
| **Public**: old kinds | 83.9% | 9.3% (3187/34279) | 4.0% (239/5948) | 17.6% |
| **Public**: grammar | 74.7% | **16.5%** (5654/34279) | **9.2%** (548/5948) | 21.9% |

- **Does the grammar find the old rules?** On the public games it explains 2,868 of the 3,187 changes the old kinds explained (90%), plus 2,786 the old kinds did not.
  - It misses 319 of theirs: 310 steering moves (it needs a few more presses to confirm a family than the old kind did) and 9 from `remote`.
  - On the worlds it misses 162 of the old kinds' changes and adds 1,634.
- **Rules that name no picture:** 44% of the final rules on the public games and 11% on the worlds. Within a game, naming a picture is a binding, which is allowed. It wins on the worlds mostly because a colour selector also picks objects that the lexicon merged on contact (see Limits).

**Per world** (changes explained, old → grammar; grammar's exact-step rate):

| World | Mechanic | Old | Grammar | Exact |
|---|---|---|---|---|
| w01 | walls (control) | 24.9% | 23.9% | 35% |
| w02 | scrambled controls | 31.1% | 30.5% | 51% |
| w03 | gravity on rocks | 24.1% | 21.5% | 32% |
| w04 | pushable boxes | 29.6% | 26.6% | 42% |
| w05 | collect coins | 60.6% | 58.3% | 70% |
| w06 | key opens door | 32.1% | 30.2% | 44% |
| w07 | teleport pad | 14.7% | 16.8% | 24% |
| w08 | mirrored twin | 19.8% | 33.1% | 20% |
| w09 | chaser | 18.8% | 41.3% | 42% |
| w10 | conveyor drifters | 12.0% | 37.2% | 8% |
| w11 | ice | 88.6% | 81.4% | 90% |
| w12 | painting trail | 34.7% | 35.8% | 13% |
| w13 | coins + timer bar | 23.1% | 24.1% | 0% |
| w14 | ACTION5 rotates the avatar | 9.5% | 33.1% | 42% |
| w15 | click cycles 3 colours (control) | 0.0% | 95.5% | 96% |
| w16 | lights-out on a lattice | 0.0% | 3.4% | 24% |
| w17 | click a switch rotates a shape | 0.0% | 86.0% | 98% |
| w18 | click spawns falling blocks | 0.0% | 59.6% | 56% |
| w19 | click removes (control) + ACTION5 swaps colours | 0.0% | 17.6% | 81% |
| w20 | push + gravity + coins, scrambled controls | 2.6% | 55.8% | 69% |

**What the grammar wrote, from the screen alone** (layout 0):

```
w17  when any if click:c12 then turn(colour:9, rot90)                       # 17 right, 0 wrong
w18  when any unless path:c8 then move(colour:6, (+4,+0))                   # 160 right, 26 wrong   (gravity, in pixels)
     when any if click:none then appear(M28a, somewhere)                    # 23 right, 16 wrong
w10  when any unless path:c8 then move(pic:G36e, (+0,+1))                   # 86 right, 32 wrong    (the conveyor)
w02  when ACTION1|ACTION2|ACTION3|ACTION4 then move(pic:bbef, by action:
       A1 unless path:c8 (+1,+0) | A2 unless path:c8 (+0,+1) | A3 unless path:c8 (-1,+0) | A4 unless path:c8 (+0,-1))
                                                                            # scrambled controls, learned; walls as conditions
ft09 when any then recolor(clicked, {9:8})          (replay level 2: when any unless click:c2 then recolor(clicked, {9:12, 12:9}))
ls20 when ACTION1|ACTION2|ACTION3|ACTION4 then move(colour:12, by action: A1 if path:c3 (-5,+0) | A2 (+5,+0) | ...)   # 59 right, 0 wrong
```

The toggle, the wall, the switch and gravity are all sentences in the same grammar. None needed its own code.

## What it does not express yet (measured, by world)

- **Perception is now the main limit, not the rule language.**
  - The lexicon merges differently coloured objects that touch. An avatar against a wall becomes one new picture, which produces spurious `resize`/`reshape` changes and false `colour:` selections (w01–w07, w13).
  - The lexicon also gives identity by picture. When same-looking tiles change colour, it reads the change as tiles moving between places (w16 lights-out, w19 colour swap).
  - Both are fixable in the lexicon by Core Knowledge cohesion: what moves together is one object, and what stays in place keeps its identity.
- **Relations missing from the grammar:**
  - "toward X" for a chaser (w09 learns only its commonest step);
  - "until blocked" for ice (w11);
  - "the next tile in the lattice" for lights-out (w16);
  - "move to where Y is" for teleports (w07);
  - "any pose of this picture" for a rotating avatar (w14: one rule per pose).
  - These are general relations (direction to, until, nearest, location of, same family). Adding them is the next grammar step. Each needs a reason from Core Knowledge or the engine, never because one world needs it.
- **Cohesion in rules:** the ls20 player is still read as two pieces, giving two rules where the old code folded them into one.

## Changes made during the work

1. **Click-target condition (`click:c`).** Added before any world result, for parity with the old `remote` rule ("clicking X changes Y").
2. **Rules that range over actions.** Added after the first world (w01) showed each direction needed its own three confirmations.
3. **Strict judging.** Adopted after the first public breakdown. Under the lenient count, the old kinds explained 6,041 changes on the public games, but 2,854 of those were predicted only vaguely ("X moves", "the clicked object changes"). Under lenient judging the grammar still led: 21.9% vs 17.6% explained on the public games, and 40.5% vs 29.5% on the worlds.
4. **World fixes before measurement.** Objects get a clear surrounding cell (as designed games place them), and the spawn world gained a ground row so the first screen isn't blank.

## Update: perception fixes (2026-10-08, notebook v4)

Two of the three perception limits named above are now fixed in `kaggle/lexicon-dfranzen/lexicon.py`; the third is not:
- **Objects that merge on contact** are cut back into the objects seen apart on the previous frame (object permanence).
- **The scale lock** rejects a coarse grid that a smaller one reads cleanly.
- **Identity by place** (look-alike tiles that change colour) was tried and graded against the engine. On the public games it read real moves as recolours far more often than it fixed recolours, so it is **off by default**. A single frame pair cannot tell the two apart; the evidence has to come from several steps (next).

Same comparison as above, re-run with the new perception (`run_compare.out`; the earlier one is `run_compare_v3perception.out`):

| | Changes explained, old → grammar | Steps exact, grammar |
|---|---|---|
| Worlds, v3 perception | 18.3% → 33.6% | 46.9% |
| Worlds, v4 perception | 35.6% → **59.6%** | **68.3%** |
| Public, v3 perception | 9.3% → 16.5% | 9.2% |
| Public, v4 perception | 9.4% → 16.6% | 9.3% |

Every avatar-and-walls world gains (for example, w08's exact steps go from 20% to 77%). Lights-out (w16) stays at 24%.

## Reproduce

```
python design/2026-10-07__rule-grammar/run_compare.py 3 all      # Python 3.12, arc-agi 0.9.8, arcengine 0.9.3; ~4 min on 3 workers
```

| File | What it is |
|---|---|
| `rule_grammar.py` | the grammar, learner, prediction and residual (stdlib; reads screens with `kaggle/lexicon-dfranzen/lexicon.py`) |
| `worlds.py` | the 20 generated games (official engine) |
| `run_compare.py` → `run_compare.out`, `run_compare.json` | the comparison on both test beds |

## Next

1. **Perception:** split merged objects when only part of them moves, and keep identity by place when a still object changes colour.
2. **Grammar:** add the five missing relations, then re-measure on these worlds and on a new batch written before the change.
3. **Goals in the same grammar:** relations that become true at a level change.
4. **Kaggle:** expose `rules`, the residual and `simulate(action)` in the sandbox, after the offline numbers move.
