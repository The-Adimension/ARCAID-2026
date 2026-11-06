"""Pre-flight for arc3_tricks v2. Run before every Kaggle push:

    ../ARC-AGI-3-Kaggle-Starter/.venv/Scripts/python.exe abtest/test_v2.py

Covers what a Kaggle save run would otherwise discover an hour and one GPU quota later:
install() applies every source patch, the guard signature learns a timer, no legal action
is ever demoted to a no-op, UNDO maps both ways, the stall detector fires on the right
action and not before, and the whole thing is inert in the plain arm.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(HERE), str(ROOT / "taaf/src/ARC3-Inference"), str(ROOT / "taaf/src/tufa-arc-agi-framework/src")]

import _local_stub  # noqa: E402  (stubs imageio/scipy; arcengine + arc_agi come from the venv)
import arc3_tricks  # noqa: E402

FAILS: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    print(f"{'PASS' if condition else 'FAIL'}  {name}{('  -- ' + detail) if detail else ''}")
    if not condition:
        FAILS.append(name)


def timer_board(step: int, extra: bool = False) -> tuple:
    """64x64 board whose last row is a shrinking timer bar; `extra` moves a real cell."""
    grid = [[0] * 64 for _ in range(64)]
    for col in range(64 - step % 64):
        grid[63][col] = 5
    if extra:
        grid[30][30] = 7
    return tuple(map(tuple, grid))


def main() -> int:
    env = arc3_tricks.os.environ
    env["ARC3_MODE"] = "ab"
    env["ARC3_STALL_N"] = "80"
    env["ARC3_TAIL_S"] = "150"

    result = arc3_tricks.install()
    check("install applies every patch", result.get("installed") is True, str(result))
    check("install is idempotent", arc3_tricks.install().get("installed") == "already")

    from inference.agent import action_names, tool_agent as ta
    from inference.agent.runtime_state import Frame, write_runtime_state
    from inference.framework import solver as solver_mod

    # --- UNDO / ACTION7 ---------------------------------------------------
    check("ACTION7 -> UNDO", action_names.to_model_action("ACTION7") == "UNDO")
    check("UNDO -> ACTION7", action_names.to_engine_action("UNDO") == "ACTION7")
    check("other actions untouched", action_names.to_model_action("ACTION3") == "LEFT"
          and action_names.to_engine_action("RESET") == "RESET")

    # --- guard signature --------------------------------------------------
    agent = ta.ToolAgent.__new__(ta.ToolAgent)
    agent._arc3_on = True
    state_path = Path(tempfile.mkdtemp()) / f"g_{ta.RUNTIME_STATE_FILENAME}"
    agent._arc3_stats_path = state_path.with_name("g_arc3.json")

    before = timer_board(0)
    demotions = 0
    for step in range(1, arc3_tricks.MIN_OBS + 4):
        after = timer_board(step)
        write_runtime_state(state_path, current_frame=Frame(grid=after, step=step, level=1), history=[])
        if agent._arc3_observe({"board_changed": True}, before, state_path) is not True:
            demotions += 1
        before = after
    check("no legal action is ever demoted to a no-op", demotions == 0,
          "v1's lockout bug: a demoted action is blocked forever")

    sig_a, sig_b = agent._arc3_sig(timer_board(40)), agent._arc3_sig(timer_board(41))
    check("timer ticks no longer change the guard signature", sig_a == sig_b)
    check("a real board change still changes it", agent._arc3_sig(timer_board(41, extra=True)) != sig_b)
    mask_rows, mask_cols = agent._arc3_masked_lines((64, 64))
    check("only border lines are masked", bool(mask_rows or mask_cols)
          and all(r < arc3_tricks.EDGE or r >= 64 - arc3_tricks.EDGE for r in mask_rows)
          and all(c < arc3_tricks.EDGE or c >= 64 - arc3_tricks.EDGE for c in mask_cols),
          f"rows {sorted(mask_rows)} cols {sorted(mask_cols)}")

    # A whole-board redraw (level change / animation) must not teach the statistic.
    n_before = agent.__dict__["_arc3_n"]
    big = tuple(tuple(9 for _ in range(64)) for _ in range(64))
    write_runtime_state(state_path, current_frame=Frame(grid=big, step=99, level=2), history=[])
    agent._arc3_observe({"board_changed": True}, timer_board(50), state_path)
    check("level changes and animations do not pollute the statistic",
          agent.__dict__["_arc3_n"] == n_before)

    plain = ta.ToolAgent.__new__(ta.ToolAgent)
    plain._arc3_on = False
    check("plain arm is byte-identical to stock Duck",
          plain._arc3_sig(timer_board(7)) == ta.board_signature(timer_board(7))
          and plain._arc3_observe({"board_changed": True}, before, state_path) is True)

    # --- stall reset ------------------------------------------------------
    class FakeState:
        def __init__(self, levels):
            self.levels_completed = levels

    class FakeGame:
        def __init__(self):
            self.current_state = FakeState(0)

    class FakeSession:
        _arc3_stalled = solver_mod._HarnessGameSession._arc3_stalled
        _arc3_reset_level = solver_mod._HarnessGameSession._arc3_reset_level

        def __init__(self):
            self.game, self.action_count, self._arc3_on = FakeGame(), 0, True
            self.remaining = 900.0
            self.analyzer, self.resets = agent, 0

        def _execute_auto_reset(self):
            self.resets += 1

        def timing_payload(self):
            return {"time_remaining_seconds": self.remaining}

    session = FakeSession()
    fired = []
    for action in range(1, 200):
        session.action_count = action
        if action == 40:
            session.game.current_state.levels_completed = 1  # a level fell: the clock restarts
        if session._arc3_stalled():
            fired.append(action)
            session._arc3_reset_level()
    check("stall fires only after N actions on one level", fired == [120],
          f"fired at {fired}")
    check("a cleared level restarts the stall clock", 40 not in fired and (not fired or fired[0] >= 120))
    check("the reset goes through Duck's own auto-reset", session.resets == len(fired))
    check("the stale plan is cleared, the evidence is kept",
          agent.__dict__.get("_arc3_stats", {}).get("stall_resets") == len(fired))

    _arc3_out_of_time = solver_mod._HarnessGameSession._arc3_out_of_time
    FakeSession._arc3_out_of_time = _arc3_out_of_time
    session.remaining = 600.0
    check("a turn with time left is not skipped", session._arc3_out_of_time() is False)
    session.remaining = 100.0
    check("a turn that cannot finish is skipped", session._arc3_out_of_time() is True)
    session.remaining = None
    check("no per-game cap means no tail guard", session._arc3_out_of_time() is False)

    session.__dict__["_arc3_on"] = False
    session.action_count += 500
    session.remaining = 10.0
    check("plain arm never stall-resets and never skips a tail turn",
          session._arc3_stalled() is False and session._arc3_out_of_time() is False)

    # --- real recorded game ----------------------------------------------
    events = ROOT / "run1/artifacts/ls20-9607627b_p0_events.jsonl"
    if events.exists():
        import json
        rows = [json.loads(line) for line in events.open(encoding="utf-8")]
        boards = [tuple(map(tuple, r["board"])) for r in rows if r.get("type") in ("initial", "action")]
        replay = ta.ToolAgent.__new__(ta.ToolAgent)
        replay._arc3_on = True
        replay._arc3_stats_path = state_path.with_name("ls20_arc3.json")
        demoted = 0
        for prev, cur in zip(boards, boards[1:]):
            write_runtime_state(state_path, current_frame=Frame(grid=cur, step=0, level=1), history=[])
            if replay._arc3_observe({"board_changed": True}, prev, state_path) is not True:
                demoted += 1
        mrows, mcols = replay._arc3_masked_lines((64, 64))
        distinct_plain = len({ta.board_signature(b) for b in boards})
        distinct_masked = len({replay._arc3_sig(b) for b in boards})
        check("replay of the real ls20 run demotes nothing", demoted == 0)
        check("replay finds the real HUD and collapses repeats",
              bool(mrows or mcols) and distinct_masked < distinct_plain,
              f"rows {sorted(mrows)} cols {sorted(mcols)}, {distinct_plain} -> {distinct_masked} distinct states")

    print("\n" + ("ALL CHECKS PASSED" if not FAILS else f"{len(FAILS)} FAILED: {', '.join(FAILS)}"))
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
