"""arc3_tricks v2 -- three mechanisms grafted onto the Duck harness, A/B-able.

Audited 2026-09-18 (arc3-autoresearch/consult/audit_2026-09-18_*.txt). v1 shipped two
ideas; the audit killed one of them and found a lockout bug in the other, so v2 is:

0. TAIL GUARD (added after the first real A/B, abrun2). Duck shrinks each model
   request's timeout to the game's remaining time, so the last turn of every game is
   generated and then discarded as a read timeout: 68 failures across 36 runs. Skip a
   turn that cannot finish.

1. STALL RESET (new, item 3). Duck has no no-progress reset at all -- the only reset
   trigger in the whole harness is GAME_OVER (solver.py:317-322). Our own lab measured
   this exact intervention as its single largest hold gain (results.tsv 6caf45c: hold
   0.1436 -> 0.1541, ft09's first level ever, hold_levels 2 -> 3) and smooth across N.
   Here: after ARC3_STALL_N actions on one level with no level change, call Duck's own
   _execute_auto_reset(), clear the agent's stale plan, and tell it what happened.

2. UNDO / ACTION7 (new, item 4). ACTION7 is an undo in the engine and 6 of the 25 public
   games offer it at level 1, but Duck's action map (action_names.py:7-15) has no entry
   for it: the harness advertises it in valid_actions and then rejects every attempt.
   One dict entry each way makes it reachable, and undo is far cheaper than RESET on
   RHAE because it rewinds instead of replaying.

3. HUD-MASKED GUARD SIGNATURE (v1 trick, repaired). Duck's no-op guard keys on a hash of
   the entire board (noop_guard.py:16-20), so one ticking counter makes every state look
   new and the guard can never fire -- measured on the public set, masking the volatile
   edge lines collapses 89 distinct signatures to 1 on lf52, 120 to 4 on vc33. v2 keeps
   ONLY the signature half. v1 also demoted "the board changed" to False when the diff
   was HUD-only, which could record a real move as a no-op and then block it forever
   (a blocked action never executes, so the contradicting evidence never arrives). That
   half is deleted. The line statistic now needs FRAC=0.8 over MIN_OBS=12 observations
   and ignores any transition whose diff exceeds SMALL_DIFF of the board, so level
   changes, resets and animations no longer push edge lines toward the threshold.

v1's nav_moves()/nav_path() sandbox helpers are removed: they misidentified the player on
busy boards, rebuilt from the whole history on every call (2.3 s at 400 transitions inside
a 30 s sandbox), and read a raw grid that Duck's own prompt deliberately hides.

Arms: ARC3_MODE=ab -> even passes plain, odd passes tricks; on -> always; off -> never.
Per-run counters land next to the harness artifacts as <run>_arc3.json.

install() must run after the TAAF sources are importable and before benchmark_initial.pkl
is unpickled.
"""
from __future__ import annotations

import inspect
import json
import os
import textwrap
from collections import Counter
from pathlib import Path

# A timer bar moves one cell per tick, so per-cell frequency never identifies it; the
# statistic has to be per line. Per line it is also what the thing actually is: a strip.
EDGE = 3          # a volatile row/column must lie within this many lines of the frame edge
FRAC = 0.8        # ...and change on at least this fraction of small-diff observations
MIN_OBS = 12      # ...once at least this many such observations exist
MAX_LINES = 8     # never mask more lines than this
SMALL_DIFF = 0.05 # ignore transitions whose diff exceeds this fraction of the board

ADDENDUM = (
    "\n\nHarness notes for this run:\n"
    "- The no-op guard ignores border cells that change on almost every action (timers, step "
    "counters) when it decides whether a board state repeats, so a repeated action that only moved "
    "a timer is blocked before it costs an action.\n"
    "- If `UNDO` appears in `valid_actions`, it rewinds the last move. Prefer it to replaying a "
    "level: it costs one action and restores the previous state.\n"
    "- If you spend a long time on one level with no level change, the harness restarts the level "
    "for you and tells you so. A restart costs one action and keeps everything you have learned, so "
    "treat it as a fresh attempt at a level you now understand, not as a loss.\n"
)

_RUN_PATCHES = [
    # Guard signature: mask volatile border lines so a ticking counter stops hiding repeats.
    ("noop_guard_board_sig = board_signature(current_frame.grid) if current_frame is not None else board_signature(())",
     "noop_guard_board_sig = self._arc3_sig(current_frame.grid if current_frame is not None else ())\n"
     "{I}noop_guard_grid = current_frame.grid if current_frame is not None else ()", 1),
    ("nonlocal terminal_action_result, noop_guard_board_sig, noop_guard_level",
     "nonlocal terminal_action_result, noop_guard_board_sig, noop_guard_level, noop_guard_grid", 1),
    # Learn the volatility statistic from every executed action (no demotion of board_changed).
    ('board_changed=bool(compact_payload.get("board_changed")),',
     'board_changed=self._arc3_observe(compact_payload, noop_guard_grid, state_path),', 1),
    ('board_changed=bool(sub_compact.get("board_changed")),',
     'board_changed=self._arc3_observe(sub_compact, noop_guard_grid, state_path),', 1),
    ("noop_guard_board_sig = board_signature(refreshed_frame.grid)",
     "noop_guard_board_sig = self._arc3_sig(refreshed_frame.grid)\n"
     "{I}noop_guard_grid = refreshed_frame.grid", 2),
    ("blocked_actions.append(action_sig)",
     "blocked_actions.append(action_sig)\n{I}self._arc3_count('guard_blocks')", 1),
    ("last_result = self._last_action_result or {}",
     "self._arc3_count('guard_blocks')\n{I}last_result = self._last_action_result or {}", 1),
]

_PLAY_PATCHES = [
    ("while not self.should_stop():",
     "while not self.should_stop():\n"
     "{I}    if self._arc3_out_of_time():\n"
     "{I}        break\n"
     "{I}    if self._arc3_stalled():\n"
     "{I}        self._arc3_reset_level()\n"
     "{I}        continue", 1),
]


def arm_for_pass(pass_index: int) -> bool:
    mode = os.environ.get("ARC3_MODE", "ab").strip().lower()
    if mode == "on":
        return True
    if mode == "off":
        return False
    return int(pass_index) % 2 == 1


def _patch(text: str, old: str, new: str, count: int) -> str:
    """Replace `old` exactly `count` times; `{I}` in `new` becomes the matched line's indentation."""
    found = text.count(old)
    if found != count:
        raise RuntimeError(f"arc3_tricks: expected {count} x {old[:60]!r}, found {found}")
    out, pos = [], 0
    while True:
        at = text.find(old, pos)
        if at < 0:
            break
        line_start = text.rfind("\n", 0, at) + 1
        indent = text[line_start:at]
        indent = indent if not indent.strip() else ""
        out.append(text[pos:at])
        out.append(new.replace("{I}", indent))
        pos = at + len(old)
    out.append(text[pos:])
    return "".join(out)


def _rebind(cls, name, source_owner, patches, extra_globals=None):
    """Re-exec one method's source with text patches applied, and bind it onto cls."""
    src = textwrap.dedent(inspect.getsource(getattr(cls, name)))
    for old, new, count in patches:
        src = _patch(src, old, new, count)
    namespace: dict = {}
    globals_ = dict(vars(source_owner))
    globals_.update(extra_globals or {})
    exec(compile(src, f"<arc3_{name}>", "exec"), globals_, namespace)
    setattr(cls, f"{name}_plain", getattr(cls, name))
    setattr(cls, name, namespace[name])
    return namespace[name]


def install() -> dict:
    from inference.agent import action_names
    from inference.agent import tool_agent as ta
    from inference.framework import solver as solver_mod

    if getattr(ta.ToolAgent, "_arc3_installed", False):
        return {"installed": "already"}

    # ---- 1. guard signature -------------------------------------------------
    _rebind(ta.ToolAgent, "_run_python_tool", ta, _RUN_PATCHES)
    patched_run = ta.ToolAgent._run_python_tool

    def _run_python_tool(self, state_path, arguments):
        self._arc3_count("python_calls")
        try:
            return patched_run(self, state_path, arguments)
        finally:
            self._arc3_flush()

    def _arc3_count(self, key, amount=1):
        self.__dict__.setdefault("_arc3_stats", Counter())[key] += amount

    def _arc3_masked_lines(self, shape):
        """Border rows/columns that change on nearly every small-diff action: timers, counters.

        FRAC is deliberately high. A timer ticks on essentially 100% of actions; a player
        pacing a corridor along an edge row rarely reaches 80% of all actions in a game, and
        masking its row would let the guard confuse two boards that differ only by where the
        player stands.
        """
        rows, cols = shape
        n = self.__dict__.get("_arc3_n", 0)
        if n < MIN_OBS or not rows:
            return frozenset(), frozenset()
        cached = self.__dict__.get("_arc3_mask_cache")
        if cached is not None and cached[0] == n:
            return cached[1]
        need = FRAC * n
        row_hits = self.__dict__.get("_arc3_rows", Counter())
        col_hits = self.__dict__.get("_arc3_cols", Counter())
        mask_rows = frozenset(r for r, hits in row_hits.items()
                              if hits >= need and (r < EDGE or r >= rows - EDGE))
        mask_cols = frozenset(c for c, hits in col_hits.items()
                              if hits >= need and (c < EDGE or c >= cols - EDGE))
        if len(mask_rows) + len(mask_cols) > MAX_LINES:
            mask_rows, mask_cols = frozenset(), frozenset()
        self.__dict__["_arc3_mask_cache"] = (n, (mask_rows, mask_cols))
        return mask_rows, mask_cols

    def _arc3_sig(self, grid):
        if not getattr(self, "_arc3_on", False) or not grid:
            return ta.board_signature(grid)
        mask_rows, mask_cols = self._arc3_masked_lines((len(grid), len(grid[0])))
        if not mask_rows and not mask_cols:
            return ta.board_signature(grid)
        masked = [
            [-1 if (r in mask_rows or c in mask_cols) else v for c, v in enumerate(row)]
            for r, row in enumerate(grid)
        ]
        return ta.board_signature(masked)

    def _arc3_observe(self, payload, before, state_path):
        """Learn which cells are volatile. Never changes what the harness thinks happened."""
        env_changed = bool(payload.get("board_changed"))
        if not getattr(self, "_arc3_on", False):
            return env_changed
        after_frame, _ = ta.load_runtime_state(state_path)
        after = after_frame.grid if after_frame is not None else ()
        if not before or not after or len(before) != len(after):
            return env_changed
        cells = len(after) * len(after[0])
        diff = [
            (r, c)
            for r in range(len(after))
            for c in range(len(after[r]))
            if r < len(before) and c < len(before[r]) and before[r][c] != after[r][c]
        ]
        # A level change, a RESET or a big animation redraws most of the board; counting
        # those would drag every edge cell toward the threshold for the wrong reason.
        if len(diff) <= max(1, int(SMALL_DIFF * cells)):
            self.__dict__["_arc3_n"] = self.__dict__.get("_arc3_n", 0) + 1
            row_hits = self.__dict__.setdefault("_arc3_rows", Counter())
            col_hits = self.__dict__.setdefault("_arc3_cols", Counter())
            for r in {r for r, _ in diff}:
                row_hits[r] += 1
            for c in {c for _, c in diff}:
                col_hits[c] += 1
            self.__dict__.pop("_arc3_mask_cache", None)
        return env_changed

    def _arc3_flush(self):
        path = getattr(self, "_arc3_stats_path", None)
        if path is None:
            return
        on = getattr(self, "_arc3_on", False)
        mask_rows, mask_cols = self._arc3_masked_lines((64, 64)) if on else (frozenset(), frozenset())
        data = {
            "arm": "tricks" if on else "plain",
            "counters": dict(self.__dict__.get("_arc3_stats", Counter())),
            "small_diff_actions": self.__dict__.get("_arc3_n", 0),
            "masked_rows": sorted(mask_rows),
            "masked_cols": sorted(mask_cols),
        }
        try:
            Path(path).write_text(json.dumps(data, indent=1), encoding="utf-8")
        except OSError:
            pass

    for name, fn in [
        ("_run_python_tool", _run_python_tool), ("_arc3_count", _arc3_count),
        ("_arc3_masked_lines", _arc3_masked_lines), ("_arc3_sig", _arc3_sig),
        ("_arc3_observe", _arc3_observe), ("_arc3_flush", _arc3_flush),
    ]:
        setattr(ta.ToolAgent, name, fn)

    # ---- 2. UNDO / ACTION7 --------------------------------------------------
    # Mutate in place: solver.py imported the helper functions, which read these dicts
    # at call time, so rebinding the names would not reach it.
    action_names.ENGINE_TO_MODEL_ACTION.setdefault("ACTION7", "UNDO")
    action_names.MODEL_TO_ENGINE_ACTION.setdefault("UNDO", "ACTION7")

    # ---- 3. stall reset -----------------------------------------------------
    session_cls = solver_mod._HarnessGameSession

    def _arc3_out_of_time(self):
        """Don't start a turn that cannot finish.

        Duck shrinks each model request's timeout to the game's remaining time
        (solver.py request_timeout_seconds), so the last turn of every game is spent
        generating a reply that is then thrown away as a read timeout. Measured in
        abrun2: 68 such failures across 36 runs, ~2 per game, each costing a full turn
        of tokens and returning no action.
        """
        tail = float(os.environ.get("ARC3_TAIL_S", "0") or 0)
        if not tail or not getattr(self, "_arc3_on", False):
            return False
        remaining = self.timing_payload().get("time_remaining_seconds")
        if remaining is None or remaining > tail:
            return False
        self.analyzer._arc3_count("tail_skips")
        return True

    def _arc3_stalled(self):
        limit = int(os.environ.get("ARC3_STALL_N", "0") or 0)
        if not limit or not getattr(self, "_arc3_on", False):
            return False
        level = int(self.game.current_state.levels_completed)
        if level != self.__dict__.get("_arc3_level", -1):
            self.__dict__["_arc3_level"] = level
            self.__dict__["_arc3_mark"] = self.action_count
            return False
        return self.action_count - self.__dict__.get("_arc3_mark", 0) >= limit

    def _arc3_reset_level(self):
        spent = self.action_count - self.__dict__.get("_arc3_mark", 0)
        self.__dict__["_arc3_mark"] = self.action_count
        self._execute_auto_reset()
        agent = self.analyzer
        agent._arc3_count("stall_resets")
        # The plan that wedged us is stale; the evidence behind it is not, so history stays.
        knowledge = getattr(agent, "_summarized_knowledge", None)
        if isinstance(knowledge, dict):
            knowledge["current_plan"] = ""
            note = (
                f"Level restarted by the harness after {spent} actions with no level change. "
                "The board is back at the start of this level; everything learned still applies."
            )
            previous = str(knowledge.get("recent_findings") or "")
            knowledge["recent_findings"] = (note if not previous else f"{previous} | {note}")[:2000]

    session_cls._arc3_out_of_time = _arc3_out_of_time
    session_cls._arc3_stalled = _arc3_stalled
    session_cls._arc3_reset_level = _arc3_reset_level
    _rebind(session_cls, "play", solver_mod, _PLAY_PATCHES)
    plain_play = session_cls.play

    def play(self, *args, **kwargs):
        on = arm_for_pass(self.pass_index)
        self._arc3_on = on
        agent = self.analyzer
        agent._arc3_on = on
        agent._arc3_stats_path = Path(str(self.state_path).replace(ta.RUNTIME_STATE_FILENAME, "arc3.json"))
        if on and ADDENDUM not in agent._system_prompt:
            agent._system_prompt = agent._system_prompt + ADDENDUM
        agent._arc3_flush()
        return plain_play(self, *args, **kwargs)

    session_cls.play = play
    ta.ToolAgent._arc3_installed = True
    return {
        "installed": True,
        "mode": os.environ.get("ARC3_MODE", "ab"),
        "stall_n": os.environ.get("ARC3_STALL_N", "0"),
        "tail_s": os.environ.get("ARC3_TAIL_S", "0"),
        "undo": action_names.ENGINE_TO_MODEL_ACTION.get("ACTION7"),
    }
