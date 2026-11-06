# Lexicon code: a data dictionary that carries from game to game

*Follow-up: `../2026-10-07__rule-grammar/` replaces the nine rule kinds below with one rule grammar, and tests it on 20 generated games as well as the public ones.*

*2026-10-07. Question: how can the lexicon turn the changes it sees into a data-dictionary "code" that persists between games and stays agnostic to the game being played?*

## Short answer

- **Split each dictionary entry in two.** Today the lexicon's dictionary says `G moves (-5, 0) on ACTION1 (22 of 24 times)`. That line mixes two things:
  - a **rule** in a fixed wording: `on ACTION1-4: move(AVATAR, step)`;
  - a **binding** that belongs to this game only: `AVATAR = G; step 5`.
- **Keep the wording; drop the bindings.** At the end of a game, discard the bindings. Carry three things to the next game:
  - the rule vocabulary;
  - the order in which to test it;
  - how often, and how fast, each rule was confirmed.
- **Within one game,** carry rules and bindings from level to level, but re-check the bindings on every step.
- **Why the vocabulary can be fixed without knowing the game:**
  - Every ARC-AGI-3 game, public or private, is a Python program on the same engine (ARCEngine; technical report §3.3).
  - The engine can change a sprite in about a dozen ways (move, rotate, mirror, recolour, set pixels, scale, show/hide, add, remove). Those are the verbs.
  - The game sources share nothing else. Sprite tags are scrambled per game (ls20 uses names like `xfmluydglp`), and the only tag found in more than one game is the engine's own `sys_click`, in 13 of 25.
- **Evidence** (55 recorded agent plays, 5,940 steps, all 25 public games; details below):
  - **Fast:** the steer, tick and click rules are confirmed after a median of 3–6 actions into a level. Humans use 28–45 actions on the same levels.
  - **Reliable:** once confirmed, a rule predicts the next step correctly 80–93% of the time. The exception is `inert`, at 57%.
  - **Carries across levels:** on the next level, the wording beats the names:

    | Rule | Wording | Names |
    |---|---|---|
    | steer | 86% | 69% |
    | tick | 92% | 65% |
    | click change | 86% | 78% |

  - **Covers unseen games:** the vocabulary built on 24 games covers every rule found in the 25th, in 24 of 25 cases.
- **The replay you linked shows why this matters.** Gemini 3.1 Pro cleared ft09 level 1 in 12 actions.
  - On level 2 the mechanics did not change: every click still toggled the clicked block (the rule predicted 71 of 71 clicks once confirmed).
  - The model's explanation drifted from "match the pattern" to "pipes", "padlock" and "AND gate". It spent 95 actions, pressed RESET 4 times, then hit GAME_OVER.
  - The code would have told it: *mechanics unchanged since level 1 (wording), colours rebound 8↔9 → 9↔12; the open question is the goal.*

## What the benchmark allows the code to contain

These points are from the technical report ([arXiv 2603.24621](https://arxiv.org/abs/2603.24621)), the docs ([docs.arcprize.org](https://docs.arcprize.org/)) and the engine.

| Benchmark fact | What it means for the code |
|---|---|
| Games use **Core Knowledge priors only**: objectness, basic geometry and topology, basic physics, agentness. No language or cultural symbols. | Roles come from these priors: AVATAR (agentness), WALL (solidity), CLICKED, TRIGGER and TARGET (contact and causality), TICKER (something that changes on every action), pose (rotation and mirror). Pieces that always move together are one object (cohesion); this repairs sprites the lexicon cut in two, such as the ls20 player. Nothing else is assumed. |
| **Novelty test:** no single program may solve two environments while being ≥50% shorter than the two separate programs. | A game's mechanics will not repeat in another game. Store primitives and procedures, never mechanics. |
| The **private set is out of distribution** and shares few mechanics with the public 25. | The public-game frequencies below set the *order of tests*, not beliefs about private mechanics. |
| **Difficulty through composition:** later levels reuse concepts from earlier levels, and level 1 is a tutorial. | Persistence across levels is rewarded by design. Carry the rules and look for what they fail to explain: that is the new mechanic. |
| **Scoring:** RHAE counts actions only. Tool calls and reasoning are free. Each level scores (human ÷ AI actions)², weighted by level index. | Inducing and checking rules in the sandbox costs no actions. Every action spent re-learning a known mechanic costs score. |
| The docs: ACTION1–4 are "semantically mapped to up, down, left, right"; ACTION7 is undo; ACTION6 takes x and y. | The interface semantics are documented, so the code may use them. Here they choose which of several lockstep movers is the avatar: in tu93 a second object moves the opposite way. |

## The design: three layers

```
screen ──lexicon.py──▶ objects with picture names      (names: this game only)
       ──events()────▶ the engine's verbs per step      (verbs: every game)
       ──induce()────▶ rules over roles + bindings      (rules: every game; bindings: this game)
```

**Layer 2, the verbs.** Each verb is the screen trace of one engine operation:

| Verb | Engine operation | Core Knowledge prior | Seen on screen as |
|---|---|---|---|
| `move` | `Sprite.move`, `set_position` (all 25 games) | objectness, motion | the same picture at a new place |
| `turn` | `rotate`, `set_mirror_*` (18 and 2 games) | geometry | a rotated or mirrored copy of the same family |
| `recolor` | `color_remap` (14) | objectness (identity kept) | same shape, colours swapped |
| `reshape`, `resize` | `pixels`, `merge`, `set_scale` (16, 6) | objectness | a different picture or size in the same place |
| `appear`, `vanish` | `add_sprite`, `remove_sprite`, `set_visible` (15, 16, 10) | object permanence | an object that wasn't there before, or is gone |
| `scroll` | camera | — | most objects shift by one vector |
| `nothing` | — | — | the action changed nothing |

**Layer 3, the rules.** There are nine kinds, each a template with a role and a support count:

```
on ACTION1-4: move(AVATAR, step)         steer   one object moves a fixed step per directional action
on ACTION1-4: nothing if WALL ahead      solid   a colour in the path stops the avatar
on ACTION6(x,y): toggle(CLICKED)         toggle  the clicked object cycles between pictures
on ACTION6(x,y): change(CLICKED)         change  the clicked object changes (no cycle seen yet)
on ACTION6(x,y) at TRIGGER: v(TARGET)    remote  clicking one object changes another
on ACTION6(x,y): nothing if CLICKED is INERT     inert   clicking it changes nothing at all
every action: v(TICKER)                  tick    something changes whichever action is pressed
on ACTIONk: v(SUBJECT)                   effect  any other consistent effect (ACTION5, ACTION7 ...)
on ACTIONk: nothing                      noop    stop spending presses on it
```

Each rule is trusted only while it keeps predicting the next step. `predict()` and `holds()` check it before the step is seen. This is the same principle Twin and Executable World Models use: a rule must reproduce the observations.

**What persists, and for how long:**

| Scope | Kept | Dropped |
|---|---|---|
| within a level | rules, bindings, counts | — |
| level → next level | rules by wording; bindings re-checked and rebound when pictures change | counts restart |
| game → next game | the vocabulary; the test order (below); confirmation statistics; the procedure (predict, check, prune noop and inert) | every name, picture, colour, step size and binding |

**Test order for a new game** (first-contact prior from the public 25):
- If directional actions exist, a steer rule turned up in 15 of 17 games. Press each direction once and look for one object moving a fixed step.
- If ACTION6 exists, a click rule turned up in 14 of 17 games. Click one copy of each distinct picture, then click it again to see whether it cycles.
- A tick turned up in 4 of 25 games. Watch for something that changes on every action.

## Results on the public games (`run_public.out`)

**Rules found** (all 4 runs; each rule re-induced before every step from that level's earlier steps):

| Rule kind | Games | Right when it predicted | Confirmed after (median actions into level) | Human baseline of those levels (median) |
|---|---|---|---|---|
| steer | 15 | 79.8% (1662/2083) | 4 | 45 |
| remote | 9 | 89.8% (681/758) | 6 | 28 |
| change | 8 | 85.1% (166/195) | 3 | 32 |
| solid | 7 | 84.1% (37/44) | 21 | 54 |
| inert | 7 | 56.8% (21/37) | 18 | 43 |
| effect | 6 | 86.9% (146/168) | 9 | 58 |
| tick | 4 | 88.2% (514/583) | 3 | 42 |
| toggle | 2 | 92.7% (203/219) | 6 | 36 |
| noop | 1 | 0/1 | 80 | 61 |

**Carried to the next level without relearning:**

| Rule kind | With level L's names | Wording only |
|---|---|---|
| steer | 69.4% (1187/1711) | **85.7%** (1467/1711) |
| tick | 64.5% (302/468) | **92.1%** (431/468) |
| change | 78.0% (96/123) | **85.9%** (244/284), covering 2.3× more clicks |
| toggle | 100% (15/15) | 92.2% (47/51), covering 3.4× more clicks |
| effect | 47.6% (39/82) | 47.6% (39/82) |

**Example codes, read from the screen alone** (role names are shared; names after `#` belong to the game):

```
ls20 level 1   on ACTION1-4: move(AVATAR, step)   # 59/60   AVATAR = O989 (+b768); step A1=(-5,+0) A2=(+5,+0) A3=(+0,-5) A4=(+0,+5); 6 presses blocked
tu93 level 1   on ACTION1-4: move(AVATAR, step)   # 17/17   AVATAR = bbef; step 2
               every action: move(TICKER)         # 17/17   TICKER = W717 (moves the opposite way)
g50t level 1   on ACTION1-4: move(AVATAR, step)   # 72/72   AVATAR = bde6; step 6; 31 presses blocked
               on ACTION1-4: nothing if WALL ahead# 21/26   WALL = {c8}
bp35 level 2   on ACTION1-4: nothing if WALL ahead# 9/9     WALL = {c3}
               on ACTION6(x,y) at TRIGGER: move(TARGET)     TRIGGER = N946; TARGET = pf8e
ft09 level 1-3 on ACTION6(x,y): change(CLICKED)   # 3/3, 8/8, 13/13   colour 8<->9, then 9<->12, then 8<->12
```

## The replay (`demo_replay.out`)

ft09-0d8bbf25, played by gemini-3.1-pro-preview with the benchmark_agent harness ([replay](https://arcprize.org/replay/34a9614e-9b77-4f82-bda4-ff1320f2e15b)):

```
level 1 (11 clicks)  on ACTION6(x,y): toggle(CLICKED)   # 7/11    A<->B (colour 8 <-> 9)
level 2 (90 clicks)  on ACTION6(x,y): toggle(CLICKED)   # 76/88   A<->O (colour 9 <-> 12)   online 71/71
                     on ACTION6(x,y): nothing if CLICKED is INERT # 12/12
level 1's rule on level 2: with level 1's names it covers 55 of 88 clicks (55 right);
                           worded only, it covers all 88 (76 right; the 12 misses are the inert clicks)
```

On level 2 the model wrote, in order:
1. "match … the pattern shown in the central miniature";
2. "activate the remaining blocks connected to the wires";
3. "fix the circuit … pipes";
4. "paint the red blocks … a Padlock";
5. "activate the Right switch for the top AND gate".

The mechanics never changed. What it lacked was the goal: which pattern the blocks must match when two miniatures overlap. This matches Twin's conclusion: "building a usable world model is simpler than anticipated, whereas the harder problem is inferring the right goal" ([arXiv 2608.14490](https://arxiv.org/abs/2608.14490)).

## Why this is AGI-first and not game-specific

- **Where the vocabulary comes from:** the engine interface, the Core Knowledge list in the technical report, and the documented action semantics. It does not come from any game. The rule kinds are designed; the bindings are learned.
- **How bindings are learned:** by intervention. Every action is an experiment, and every rule carries its counts and its online record.
- **Coverage of unseen games:** in the leave-one-game-out check, the vocabulary from 24 games covered every rule kind in the 25th, for 24 of 25 games. The exception is sk48, whose only unshared kind is `noop`.
- **What is stored:** nothing a game's novelty would invalidate. No mechanics, pictures or colours.
- **Fit with the published systems:**
  - Executable World Models, Twin and OPINE-World build a verified program of the game at test time.
  - OPINE-World notes that programmatic world models such as WorldCoder need a symbolic representation supplied up front ([arXiv 2607.01531](https://arxiv.org/abs/2607.01531)). The lexicon provides that representation from pixels, and the rule code is a small verified world model a 6B-active model can read.

## Limits (measured)

- **Many blocked presses have no visible cause.** Of 421 steer misses, 369 were presses where the avatar stayed put. Colour walls explain few of them: `solid` is found in 7 games and lifts directional predictions only from 78.4% to 79.9%. In 176 of the 369, the path held nothing but background, so something the screen doesn't show stopped the avatar (hidden state, cooldowns, rails). That needs a rule kind that depends on history.
- **`inert` is state-dependent.** It is right only 57% of the time: an object that ignored one click often reacts later.
- **No goal layer yet,** and that is where the replay failed.
- **The public set is easier and not representative.** The frequencies above set test order, not beliefs.
- **These are agent plays, not a designed probe,** and there is no score evidence. This is an offline measurement of reading and predicting. The lexicon view itself showed no score effect beyond noise.

## Next steps

1. **Goal layer, in the same vocabulary.**
   - At each level change, record which relations hold that did not hold at the level's start:
     - every X vanished;
     - AVATAR on Y;
     - pattern A equals pattern B under a colour map;
     - counts equal.
   - Carry these to the next level as goal candidates. Twin infers the goal before any reward on 87% of the levels it clears.
2. **Unexplained events.** Each step, list the events no rule predicted, and let the model write a rule for them (as code). Check it with the same predict-and-hold loop, so the vocabulary can grow at test time.
3. **In the notebook.**
   - Add `current_frame.rules` (text) and an "unexplained" line to the lexicon cell. It is stdlib only and uses the same sandbox.
   - Measure use and wasted actions on the levels after the first.
   - One save run per arm checks only mechanics; the score noise is about ±10 points.

## Files

| File | What it is |
|---|---|
| `effect_code.py` | layers 2 and 3 (stdlib, on top of `kaggle/lexicon-dfranzen/lexicon.py`) |
| `demo_replay.py` → `demo_replay.out` | the official replay, read into code (download command in the docstring) |
| `run_public.py` → `run_public.out`, `run_public.json` | 55 recorded plays replayed on the engine (Python 3.12, arc-agi 0.9.8, arcengine 0.9.3) |

The engine-operation counts come from a regex survey of the 25 public game sources: the number of games whose source calls each operation.
