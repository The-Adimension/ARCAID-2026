"""Unit checks for restart.patch (v2) on Franzen's patched harness, offline, without a model server.

  python kaggle/restart-dfranzen/test_restart.py <bundle dir>

<bundle dir> holds dfranzen/taaf-kaggle-source-bundle-copy with Franzen's harness patch applied (the
notebook's cell 2) and nothing else. The script copies it, applies restart.patch, and checks the hook on
stub agents. sim_restart.py drives the real ToolAgent.analyze() end to end.
  1. restart.patch applies on Franzen's patched bundle;
  2. flag off (unset, 0, negative, junk): the hook does nothing and the level-transition hook does nothing;
  3. flag on: clears the history once per level past the threshold, also on a resumed (no-action) turn,
     and then opens a fresh turn (resume flags cleared);
  4. no re-pricing: _tokens_at_level_start is unchanged; the trim is flagged to the scheduler;
  5. the note is sent again if the turn that carried it was rolled back, and only then;
  6. the note's board sentence follows game_over;
  7. completion is logged on a level transition and on a final-level win, once, with tokens since the restart;
  8. the turn method passes the note in front of the prompt, before the rollback snapshot.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
OK = []


def check(name, cond, detail=""):
    OK.append(bool(cond))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f": {detail}" if detail and not cond else ""))


def main():
    bundle = pathlib.Path(sys.argv[1]).resolve()
    work = pathlib.Path(tempfile.mkdtemp()) / "src"
    shutil.copytree(bundle / "src", work)
    r = subprocess.run(["git", "apply", "--check", "-v", str(HERE / "restart.patch")], cwd=work, capture_output=True, text=True)
    check("restart.patch applies on Franzen's patched bundle", r.returncode == 0, r.stderr[-400:])
    subprocess.run(["git", "apply", str(HERE / "restart.patch")], cwd=work, check=True)
    sys.path.insert(0, str(work / "ARC3-Inference"))
    os.environ.pop("ARC3_STUCK_RESTART_TOKENS", None)
    log_path = pathlib.Path(tempfile.mkdtemp()) / "restarts.jsonl"
    os.environ["ARC3_STUCK_RESTART_LOG"] = str(log_path)
    import inference.agent.tool_agent as T

    def agent(level=3, tokens_on_level=0, actions_on_level=0, history=4, resumed=False, game_over=False):
        a = object.__new__(T.ToolAgent)          # no server, no session: only the fields the hook reads
        a._last_step_summary = {"level": level, "end_action_num": 100 + actions_on_level, "game_over": game_over}
        a._actions_at_level_start = 100
        a._session_generated_tokens = 500_000
        a._tokens_at_level_start = 500_000 - tokens_on_level
        a._history_messages = [{"role": "user", "content": "x"}, {"role": "assistant", "content": "y"}] * (history // 2)
        a._context_was_trimmed = False
        a._has_evicted = False
        a._diag_name = "g07"
        a._game_elapsed_seconds = 1234.0
        a._resume_after_yield = resumed
        a._resume_reason = "yield_bare" if resumed else ""
        return a

    notes = []
    tr = lambda label, text: notes.append((label, text))
    sp = pathlib.Path("/kaggle/working/artifacts/ab12-cdef0123_p0_tool_runtime_state.json")

    # flag off
    for val in (None, "0", " 0 ", "-5", "abc"):
        if val is None:
            os.environ.pop("ARC3_STUCK_RESTART_TOKENS", None)
        else:
            os.environ["ARC3_STUCK_RESTART_TOKENS"] = val
        a = agent(tokens_on_level=250_000, resumed=True)
        before = dict(a.__dict__)
        out = a._maybe_restart_stuck_level(sp, tr)
        a._last_step_summary = {"level": 4, "level_transition": True, "end_action_num": 140}
        a._log_stuck_restart_completion(3, a._last_step_summary)
        check(f"flag {val!r}: no restart, agent state unchanged", out == "" and a.__dict__.keys() == before.keys()
              and a._history_messages == before["_history_messages"] and a._resume_after_yield is True
              and not hasattr(a, "_stuck_restarts"))
    check("flag off: nothing logged", not log_path.exists())

    os.environ["ARC3_STUCK_RESTART_TOKENS"] = "100000"
    a = agent(tokens_on_level=99_999)
    check("flag on: no restart below the threshold", a._maybe_restart_stuck_level(sp, tr) == "" and len(a._history_messages) == 4)

    a = agent(tokens_on_level=100_000, actions_on_level=37, resumed=True)
    note = a._maybe_restart_stuck_level(sp, tr)
    check("fires on a resumed (no-action) turn at the threshold", "cleared after 37 actions" in note, note)
    check("history cleared", a._history_messages == [])
    check("resume flags cleared: the turn opens fresh", a._resume_after_yield is False and a._resume_reason == "")
    check("no re-pricing: level token count unchanged", a._tokens_at_level_start == 400_000)
    check("trim flagged to the scheduler", a._context_was_trimmed and a._has_evicted)
    check("transcript line written", notes and notes[-1][1].startswith("stuck_level_restart: level=3 tokens=100000 actions=37"))
    check("note: current-state wording when no game over", "may differ from its start" in note)

    # the turn carrying the note was rolled back (history still empty at the next invocation)
    again = a._maybe_restart_stuck_level(sp, tr)
    check("rolled-back note is sent again", again == note and a._resume_after_yield is False)
    # the next turn was kept: history non-empty -> pending cleared, no new restart on this level
    a._history_messages = [{"role": "user", "content": note}, {"role": "assistant", "content": "ok"}]
    a._session_generated_tokens += 300_000
    check("kept note is not repeated; at most once per level", a._maybe_restart_stuck_level(sp, tr) == ""
          and len(a._history_messages) == 2 and a._stuck_restart_note == "")
    a._last_step_summary = {"level": 4, "end_action_num": 160}
    check("a later level can restart", a._maybe_restart_stuck_level(sp, tr) != "")

    g = agent(tokens_on_level=150_000, game_over=True)
    check("note: start-state wording after a game over", "reset after a game over" in g._maybe_restart_stuck_level(sp, tr))

    b = agent(tokens_on_level=200_000, history=0)
    check("no restart on an empty history", b._maybe_restart_stuck_level(sp, tr) == "")

    # completion on a level transition, logged once, tokens since the restart
    c = agent(level=2, tokens_on_level=120_000, actions_on_level=50)
    c._maybe_restart_stuck_level(sp, tr)
    c._history_messages = [{"role": "user", "content": "n"}]
    c._session_generated_tokens += 30_000
    c._last_step_summary = {"level": 3, "level_transition": True, "end_action_num": 175}
    c._summarized_knowledge = {}
    try:
        c._update_summarized_knowledge_from_step_summary()
    except AttributeError:
        pass                                  # later, unrelated fields of a stub agent; the hook runs first
    c._log_stuck_restart_completion(2, c._last_step_summary)       # a second call must not log again
    # completion on a final-level win (run_complete, no level transition)
    w = agent(level=7, tokens_on_level=110_000, actions_on_level=40)
    w._maybe_restart_stuck_level(sp, tr)
    w._session_generated_tokens += 20_000
    w._last_step_summary = {"level": 7, "run_complete": True, "level_transition": False, "end_action_num": 160}
    w._summarized_knowledge = {}
    try:
        w._update_summarized_knowledge_from_step_summary()
    except AttributeError:
        pass
    events = [json.loads(l) for l in log_path.read_text().splitlines()]
    done = [e for e in events if e["event"] == "completed_after_restart"]
    check("level-transition completion logged once, tokens since restart", sum(e["level"] == 2 for e in done) == 1
          and [e for e in done if e["level"] == 2][0]["tokens_after"] == 30_000
          and [e for e in done if e["level"] == 2][0]["actions_total"] == 75, json.dumps(done))
    check("final-level win completion logged", sum(e["level"] == 7 for e in done) == 1
          and [e for e in done if e["level"] == 7][0]["tokens_after"] == 20_000, json.dumps(done))
    check("restart events carry game path, resumed flag and session tokens",
          all(e["state_path"] == str(sp) and "resumed_turn" in e and "session_tokens_at_restart" in e
              for e in events if e["event"] == "restart"))

    src = (work / "ARC3-Inference/inference/agent/tool_agent.py").read_text()
    i_call = src.index("restart_note = self._maybe_restart_stuck_level(state_path, append_transcript)")
    i_snap = src.index("previous_history_messages = list(self._history_messages)")
    i_resume = src.index('resuming_after_yield = bool(getattr(self, "_resume_after_yield", False))')
    i_open = src.index("user_prompt, resume_frame if resuming_after_yield else current_frame")
    check("hook runs before the rollback snapshot, the resume read and the opener", i_call < i_snap < i_resume < i_open)
    check("the restart never re-prices the level",
          "self._tokens_at_level_start = self._session_generated_tokens" not in
          src[src.index("    def _maybe_restart_stuck_level"):src.index("    def _maybe_handover")])

    print(f"{sum(OK)} of {len(OK)} pass")
    sys.exit(0 if all(OK) else 1)


if __name__ == "__main__":
    main()
