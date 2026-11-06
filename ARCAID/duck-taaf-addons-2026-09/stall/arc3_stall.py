"""arc3_stall: tell the agent when it is looping on a level it cannot clear.

Evidence (depthrun1, 6 games x 3600 s). Duck clears every level it clears at or better
than human pace, then hits ONE level and grinds without ever clearing it -- 1.4-7.2x the
human baseline, all six games ending `gave_up` still on that level. On the wall level the
action mix collapses:

    game  cleared-levels uniq_frac -> wall uniq_frac   most-repeated action on the wall
    sb26            0.67 -> 0.16                       one click x19  of 133
    vc33            0.24 -> 0.10                       one click x122 of 439
    lp85            0.29 -> 0.12                       one click x30  of 83
    re86            0.05 -> 0.02                       ACTION3  x104 of 368
    ft09            0.67 -> 0.41

vc33 clicked the same cell 122 times. That is a loop, and Duck's own no-op guard cannot
see it: the guard only blocks an action that left the board UNCHANGED in that exact state,
and a looping action usually does change the board (it just changes it pointlessly, or
oscillates). Nothing anywhere else in the harness notices.

WARNING FIRST, THEN RESET -- and the warning was refuted. stallrun2 ran the warn-only version
over the same 6 games: it fired 100 warnings and moved the normalised loop metric
(most-repeated action / wall actions) from 0.234 to 0.219, i.e. not at all. Levels went 19 ->
23, but ALL of that was sb26 alone going 1 -> 7; without sb26 the run was net negative
(23.33 vs 28.81 on the 6-game RHAE mean), and it had 42% MORE actions to work with. So the
agent is not failing to notice that it is looping -- it cannot get out. That is the
pre-registered "reset" branch, and MODE now defaults to it: a stuck batch is replaced by a
single RESET, which under ONLY_RESET_LEVELS rewinds THIS level only and keeps cleared levels
and score. A RESET costs one action, against walls of 83-439.

RETRACTION (2026-09-20). resetrun2 and resetrun3 did NOT test the reset. A safety gate that
skipped the reset when "RESET" was absent from `valid_actions` suppressed 91 of 91 trips --
`resets_issued: 0` in resetrun3's counters -- because `valid_actions` NEVER lists RESET; it is
gameplay only. Every RESET in those runs' histories was the model's own: depthrun1, carrying no
add-on at all, already had 10 of them (1.7/run), the same rate as every other run. So all three
"stall" runs measured the WARN branch, and their five-game means -- 23.33, 35.20, 37.46 against
a no-add-on 28.81 -- are one treatment measured three times. That spread IS the noise floor of
this 6-game probe, and the warning has no detectable effect. The gate is gone. Nothing below has
been tested on Kaggle yet.

BASELINE-FREE BY CONSTRUCTION. base_actions_per_level is None in submission mode
(game_api.py:232-242), so nothing may compare against the human baseline -- it works on the
25 public games and silently dies on the hidden set. The grind trigger therefore compares
the current level against the median of THAT GAME'S OWN cleared levels. depthrun1 shows the
separation is wide: cleared levels ran 4-80 actions, wall levels 83-439.

Hooks, and READ THIS BEFORE EDITING. The Kaggle FP4 stack does NOT ship the Duck revision
in duck-study/taaf. Its bundle (keithtyser/duck-qwen38-nvfp4-mtp-vllm-smoke-v1, dated
2026-08-31) carries an EARLIER tool_agent.py -- 89,299 bytes against the 108,927 in taaf --
with **no noop_guard.py at all**, no `_aggregate_action_batch_result`, and no per-action
batch walk: one `action([...])` call is one atomic step_env call. A first version of this
module hooked `NoopGuard.observe` and died on Kaggle with
`ImportError: cannot import name 'noop_guard' from 'inference.agent'` after 11 minutes of
setup. Pre-flight against duck-study/fp4src/ARC3-Inference, which is the shipped source.

Both hooks are plain methods on ToolAgent, and one ToolAgent plays one game, so per-instance
state is per-game state:
  ToolAgent._normalize_python_actions  -> the actions about to run (stash them)
  ToolAgent._compact_action_result     -> the level, and the payload the model reads
`_serialized_runtime_state` and `_handle_action` are CLOSURES inside a method
(tool_agent.py:1466, :1495 in the shipped file) and cannot be patched from outside.
"""
from __future__ import annotations

import os
import statistics

REPEAT_N = int(os.environ.get("ARC3_STALL_REPEAT_N", "10"))    # same action this often on one level
WINDOW = int(os.environ.get("ARC3_STALL_WINDOW", "40"))        # rolling window for the mix check
UNIQ_FRAC = float(os.environ.get("ARC3_STALL_UNIQ_FRAC", "0.2"))
GRIND_MULT = float(os.environ.get("ARC3_STALL_GRIND_MULT", "3.0"))
GRIND_FLOOR = int(os.environ.get("ARC3_STALL_GRIND_FLOOR", "60"))
RENOTIFY_EVERY = int(os.environ.get("ARC3_STALL_RENOTIFY", "15"))

# Arming gate, applied to EVERY trigger. Without it the repeat rule fires during healthy
# play on movement games, where pressing ACTION3 ten times in a row is just walking: the
# depthrun1 replay warned re86 at action 13 and ar25 at 16 of levels they went on to CLEAR.
# A warning that interrupts a working plan is worse than a late one, so nothing fires until
# the level has already cost 3x this game's own cleared levels. At 2.0 the replay still
# warned inside ar25's level 3 (80 actions against a median of 28) and vc33's level 3,
# both of which were then CLEARED. 3.0 costs us the ar25 wall entirely and is still the
# right trade: a late warning wastes actions, a wrong one derails a level being solved.
MIN_ON_LEVEL = int(os.environ.get("ARC3_STALL_MIN_ON_LEVEL", "45"))
# "warn" tells the model it is stuck; "reset" replaces the stuck batch with a single RESET.
# HIDDEN-SET VERDICT (2026-09-21), the only instrument that resolved this:
#     batching only 3.04  |  + warn 3.37  |  + reset 2.84
# Reset scored BELOW batching alone and 0.53 below warn -- the clearest separation we have on
# the hidden set (~2.3 SE by a crude estimate). The 6-game probe ranked reset BEST (39.37); it
# had the direction wrong. Default is therefore "warn". The best submission (56406950, 3.37) was
# built with MODE=reset but every reset suppressed, so it behaved as warn; the Kaggle kernel
# habanwer/arc3-duck-fp4-reset v3 is the exact artifact if byte-for-byte reproduction matters.
MODE = os.environ.get("ARC3_STALL_MODE", "warn").strip().lower()
MAX_RESETS_PER_LEVEL = int(os.environ.get("ARC3_STALL_MAX_RESETS", "2"))
# Scope of that cap. "level" is the documented intent. "game" is what resetrun4 (v4) actually
# ran: `resets` was only zeroed in __init__, never on a new level, so v4 allowed 2 resets per
# GAME and suppressed 39 trips on later walls (resets_issued 10, resets_suppressed_cap 39).
# Set ARC3_STALL_CAP_SCOPE=game to reproduce v4 exactly.
CAP_SCOPE = os.environ.get("ARC3_STALL_CAP_SCOPE", "level").strip().lower()
ARM_MULT = float(os.environ.get("ARC3_STALL_ARM_MULT", "3.0"))

STATS = {"levels_seen": 0, "trips": 0, "warnings_shown": 0, "resets_issued": 0,
         "resets_suppressed_cap": 0}

class _Tracker:
    """Per-ToolAgent state, and one ToolAgent plays one game."""

    def __init__(self) -> None:
        self.level = None
        self.counts: dict[str, int] = {}
        self.window: list[str] = []
        self.on_level = 0
        self.cleared: list[int] = []      # actions spent on each level this game CLEARED
        self.warned_at = 0
        self.resets = 0

    def _new_level(self, level) -> None:
        if self.level is not None and self.on_level > 0:
            # the level advanced, so the previous one was cleared. RESET keeps the level,
            # so a reset cannot land here and pollute the baseline.
            self.cleared.append(self.on_level)
        self.level = level
        self.counts = {}
        self.window = []
        self.on_level = 0
        self.warned_at = 0
        if CAP_SCOPE == "level":
            self.resets = 0               # a new level gets its own reset budget
        STATS["levels_seen"] += 1

    def observe(self, level, action_sig: str) -> None:
        if level != self.level:
            self._new_level(level)
        self.on_level += 1
        self.counts[action_sig] = self.counts.get(action_sig, 0) + 1
        self.window.append(action_sig)
        if len(self.window) > WINDOW:
            del self.window[0]

    def reason(self) -> str:
        """Why this level looks stuck, or "". Pure: no counters, no state."""
        arm = MIN_ON_LEVEL
        if self.cleared:
            arm = max(arm, ARM_MULT * statistics.median(self.cleared))
        if self.on_level < arm:
            return ""

        worst_sig, worst_n = "", 0
        for sig, n in self.counts.items():
            if n > worst_n:
                worst_sig, worst_n = sig, n

        if worst_n >= REPEAT_N:
            return f"you have executed {worst_sig} {worst_n} times on this level"
        if len(self.window) >= WINDOW and len(set(self.window)) / len(self.window) < UNIQ_FRAC:
            return (f"your last {len(self.window)} actions used only "
                    f"{len(set(self.window))} distinct actions")
        if self.cleared:
            budget = max(GRIND_FLOOR, GRIND_MULT * statistics.median(self.cleared))
            if self.on_level >= budget:
                return (f"you have spent {self.on_level} actions on this level, against a median "
                        f"of {statistics.median(self.cleared):.0f} on the levels you already cleared")
        elif self.on_level >= max(GRIND_FLOOR, REPEAT_N * 6):
            return f"you have spent {self.on_level} actions on this level without clearing it"
        return ""

    def armed(self) -> str:
        """reason(), rate-limited to once every RENOTIFY_EVERY actions on this level."""
        r = self.reason()
        if not r:
            return ""
        if self.warned_at and self.on_level - self.warned_at < RENOTIFY_EVERY:
            return ""
        self.warned_at = self.on_level
        STATS["trips"] += 1
        return r

    def on_reset(self) -> None:
        """A RESET keeps the level (ONLY_RESET_LEVELS), so _new_level never fires. Clear the
        per-level counters by hand so the fresh attempt gets a full arming budget, and keep
        `cleared` -- that is the baseline and a reset must not pollute it."""
        self.resets += 1
        self.counts = {}
        self.window = []
        self.on_level = 0
        self.warned_at = 0

    def warning(self) -> "str | None":
        r = self.armed()
        if not r:
            return None
        STATS["warnings_shown"] += 1
        return (
            f"STUCK: {r}, and the level has not advanced. Repeating it again will not clear "
            "the level. Your current hypothesis about this level is wrong. Stop executing the plan "
            "you are on, re-read the board from scratch, and form a DIFFERENT hypothesis about what "
            "this level wants -- a different object to act on, a different mechanic, or a different "
            "goal than the one you assumed."
        )


_ORIG_NORMALIZE = None
_ORIG_COMPACT = None


def _tracker(agent) -> "_Tracker":
    t = getattr(agent, "_arc3_tracker", None)
    if t is None:
        t = _Tracker()
        try:
            agent._arc3_tracker = t
        except Exception:
            pass
    return t


def _sig(action) -> str:
    """Signature of one action. Handles BOTH shapes: the tool_agent normalized form
    {"action": NAME, "row": r, "col": c} (Duck speaks row/col and raises on x/y), and the
    engine/benchmark form {"id": NAME, "data": {"x": .., "y": ..}} used by replays. Getting
    this wrong collapses every click to one signature and fires the repeat rule on healthy
    play -- the pre-flight caught exactly that.
    """
    if not isinstance(action, dict):
        return str(action)
    name = str(action.get("action") or action.get("id") or "?")
    if "row" in action or "col" in action:
        return f"{name}:{action.get('row')},{action.get('col')}"
    data = action.get("data")
    if isinstance(data, dict) and data:
        return f"{name}:{data.get('x')},{data.get('y')}"
    return name


RESET_NOTE = (
    "LEVEL RESET BY THE RUNNER. {reason}, and the level had not advanced, so your batch was "
    "replaced with a single RESET. The level has restarted from its initial state and your "
    "score and cleared levels are untouched -- only this level was rewound. Whatever you were "
    "about to do would have continued a plan that has already failed {n} time(s) here. Do not "
    "replay it. Re-read the board from the fresh start and form a DIFFERENT hypothesis about "
    "what this level wants: a different object to act on, a different mechanic, or a different "
    "goal than the one you assumed."
)


def _maybe_reset(agent, actions):
    """Replace a stuck batch with one RESET. Returns the batch to execute."""
    if not isinstance(actions, list) or not actions:
        return actions
    t = _tracker(agent)
    if len(actions) == 1 and str(actions[0].get("action", "")).upper() == "RESET":
        return actions                      # the model reset on its own; leave it alone
    reason = t.armed()
    if not reason:
        return actions
    if t.resets >= MAX_RESETS_PER_LEVEL:
        STATS["resets_suppressed_cap"] += 1
        _PENDING[id(agent)] = _warn_text(reason)
        return actions                      # already rewound this level twice; just warn
    # NO valid_actions GATE. `valid_actions` NEVER contains RESET -- measured in resetrun3's
    # own prompts, the list is gameplay only (UP/DOWN/LEFT/RIGHT/SPACE/MOUSE/ACTION7). RESET is
    # always executable regardless: the model issued 10-23 of its own per run in every run we
    # have, including depthrun1, which carried no add-on at all. The gate that used to live here
    # suppressed 91 of 91 resets in resetrun3 and silently turned the reset branch back into the
    # warn branch, which is why resetrun2/resetrun3 measured warn and not reset. Do not re-add it.
    STATS["resets_issued"] += 1
    _PENDING[id(agent)] = RESET_NOTE.format(reason=reason[0].upper() + reason[1:], n=t.resets + 1)
    t.on_reset()
    return [{"action": "RESET"}]


def _warn_text(reason: str) -> str:
    STATS["warnings_shown"] += 1
    return (
        f"STUCK: {reason}, and the level has not advanced. Repeating it again will not clear "
        "the level. Your current hypothesis about this level is wrong. Stop executing the plan "
        "you are on, re-read the board from scratch, and form a DIFFERENT hypothesis about what "
        "this level wants -- a different object to act on, a different mechanic, or a different "
        "goal than the one you assumed."
    )


_PENDING: dict = {}


def install() -> dict:
    """Patch the two ToolAgent methods the shipped revision actually has. Idempotent."""
    global _ORIG_NORMALIZE, _ORIG_COMPACT
    from inference.agent import tool_agent as TA

    if getattr(TA.ToolAgent._compact_action_result, "_arc3_stall", False):
        return {"installed": "already"}

    _ORIG_NORMALIZE = TA.ToolAgent._normalize_python_actions
    _ORIG_COMPACT = TA.ToolAgent._compact_action_result

    def normalize(self, value):
        out = _ORIG_NORMALIZE(self, value)
        try:
            if MODE == "reset":
                out = _maybe_reset(self, out)
            self._arc3_pending = list(out) if isinstance(out, list) else []
        except Exception:
            pass
        return out

    normalize._arc3_stall = True
    TA.ToolAgent._normalize_python_actions = normalize

    def compact(self, payload):
        out = _ORIG_COMPACT(self, payload)
        try:
            pending = getattr(self, "_arc3_pending", None) or []
            self._arc3_pending = []
            if pending and isinstance(out, dict) and out.get("executed"):
                t = _tracker(self)
                level = out.get("level")
                msg = None
                for action in pending:
                    t.observe(level, _sig(action))
                    if MODE != "reset":
                        msg = t.warning() or msg
                queued = _PENDING.pop(id(self), None)
                if queued or msg:
                    out["stuck_warning"] = queued or msg
        except Exception:
            pass   # a counter must never break a run
        return out

    compact._arc3_stall = True
    TA.ToolAgent._compact_action_result = compact
    return {"installed": True, "mode": MODE, "max_resets": MAX_RESETS_PER_LEVEL,
            "cap_scope": CAP_SCOPE,
            "repeat_n": REPEAT_N, "window": WINDOW, "uniq_frac": UNIQ_FRAC,
            "grind_mult": GRIND_MULT, "grind_floor": GRIND_FLOOR,
            "min_on_level": MIN_ON_LEVEL, "arm_mult": ARM_MULT}


PROMPT_LINE = (
    "- `last_action_result` may carry a `stuck_warning` from the runner. It means this level has "
    "already cost far more actions than the levels you cleared, and that you have been repeating "
    "yourself. Treat it as decisive: your hypothesis about this level is wrong. If it says the "
    "level was RESET, the board is back at this level's initial state, your cleared levels and "
    "score are intact, and the plan you were running has been discarded -- do not replay it. "
    "Re-read the board from scratch and form a different hypothesis about what the level wants "
    "before acting again.\n"
)


def install_prompt() -> dict:
    """Tell the model what a stuck_warning means. Same binding trap as arc3_batch."""
    from inference.agent import prompts as P
    from inference.agent import tool_agent as TA

    if "stuck_warning" in TA.PYTHON_ADDENDUM:
        return {"installed": "already"}
    new = TA.PYTHON_ADDENDUM + PROMPT_LINE
    TA.PYTHON_ADDENDUM = new
    P.PYTHON_ADDENDUM = new
    if "stuck_warning" not in TA._build_system_prompt(tool_output_tokens=1024):
        raise RuntimeError("arc3_stall: prompt line did not reach _build_system_prompt")
    return {"installed": True}
