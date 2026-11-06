"""Check the ported lexicon cell against Daniel Franzen's patched harness, offline (CPU, no model).

Needs dfranzen's source bundle with his patch applied:
  kaggle datasets download dfranzen/taaf-kaggle-source-bundle-copy  ->  unzip to BUNDLE
  (cd BUNDLE/src && git apply --include='ARC3-Inference/*' <patch from cell 2 of his notebook>)
and a Python with pillow, numpy and openai installed.

  python kaggle/lexicon-dfranzen/verify_port.py BUNDLE

It sets dfranzen's environment flags (cell 4 of his notebook), imports his harness, executes the
ported cell exactly as the notebook will, and checks:
  1. the cell reports installed, self-test ok, all four prompt edits "applied", cue installed;
  2. the system prompt dfranzen actually builds now carries the edits, and his own text is intact
     (persistent-function wording, frame_diff hint), with nothing else changed;
  3. the tool description carries the new members;
  4. the cue fires on dfranzen's first-turn and new-level texts;
  5. one real sandbox call with his extra arguments runs `.code`, `.changes_since`, `.native`,
     `.objects` and his own `frame_diff()` side by side;
  6-7. (v2) the per-level scale lock: its sandbox self-test passes, and a real sandbox call reads a
     sparse frame at its level's 2 px grid (with ARCAID3_SCALE_LOCK=0: the lock is off and the frame
     falls back to its own 6 px detection).
  8-10. (v3) `current_frame.rules`: its sandbox self-test passes; on a toy level where RIGHT moves a
     block and a click toggles a tile, a real sandbox call states both rules and reports the last
     step; a 150-step level answers well inside the harness's 30 s tool limit (with ARCAID3_RULES=0:
     the rules are off and say so).
  11-13. (v4) the `.rules` cue fires after actions that changed nothing and at 6 actions on a level, but
     not before a level's third action; a 1-cell object that steps against a small wall is reported as
     moved, not as the wall becoming a new picture (object permanence); a level whose objects are all
     3 cells wide and move 1 cell at a time is read at its true 2 px grid, with no marker to pin it.
"""
import time
import difflib
import importlib.util
import json
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BUNDLE = pathlib.Path(sys.argv[1]).resolve()
NB = next((ROOT / "notebooks").glob("2026-10-05__dfranzen-M2*/*.ipynb"))


def dfranzen_env():
    cells = json.load(open(NB))["cells"]
    src = next("".join(c["source"]) for c in cells if "setup_env = {" in "".join(c["source"]))
    block = re.search(r"setup_env = \{.*?\n\}\n", src, re.S).group(0)
    prio = re.search(r"if USE_PRIORITY_SCHEDULING: setup_env.update\(\{.*?\}\)", src, re.S).group(0)
    ns = {"SERVER_BASE_URL": "http://127.0.0.1:8001/v1", "SERVED_MODEL_NAME": "flashnext",
          "USE_PRIORITY_SCHEDULING": True}
    exec(block + "\n" + prio, ns)
    env = {k: str(v) for k, v in ns["setup_env"].items()}
    env.update({"MPLBACKEND": "Agg", "TAAF_RUN_AS_SUBMISSION": "0", "TAAF_MINIMAL_DIAGNOSTICS": "0",
                "ONLY_RESET_LEVELS": "true"})
    return env


def main():
    os.environ.update(dfranzen_env())
    for p in (BUNDLE / "src/tufa-arc-agi-framework/src", BUNDLE / "src/ARC3-Inference"):
        sys.path.insert(0, str(p))
    import inference.agent.prompts as pr
    import inference.agent.python_tool_sandbox as sb
    import inference.agent.tool_agent as ta

    before_sys = ta._build_system_prompt(tool_output_tokens=3072)
    before_tool = ta._PYTHON_TOOL_DESCRIPTION

    cell_src = next("".join(c["source"]) for c in json.load(open(NB))["cells"]
                    if "".join(c["source"]).startswith("# ----") and "install_arcaid3_lexicon" in "".join(c["source"]))
    ns = {"__name__": "__main__"}
    exec(compile(cell_src, "<lexicon cell>", "exec"), ns)
    rep = ns["ARCAID3_REPORT"]
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(("PASS " if cond else "FAIL ") + name + (f"  {detail}" if detail else ""))

    check("1 installed + self-test", rep.get("installed") and rep.get("self_test") == "ok", rep.get("error", ""))
    program = len(sb._SANDBOX_BOOTSTRAP.encode("utf-8"))
    check("1 sandbox program fits one command-line argument (< 128 KiB)", program < 131072, f"{program} bytes")
    check("1 prompt edits all applied", set((rep.get("prompt_edits") or {}).values()) == {"applied"}, rep.get("prompt_edits"))
    check("1 cue installed", rep.get("first_turn_cue") == "installed")

    after_sys = ta._build_system_prompt(tool_output_tokens=3072)
    members = ns["_A3_MEMBERS"]
    check("2 system prompt: both 'only' lines list the members", after_sys.count(members) >= 2)
    check("2 system prompt: trigger line present", ns["_A3_TRIGGER"] in after_sys)
    check("2 system prompt: lexicon note present", ns["ARCAID3_NOTE"].strip()[:60] in after_sys)
    check("2 dfranzen persistent-function wording intact", "eligible functions are retained" in after_sys)
    check("2 dfranzen frame_diff hint intact", ("frame_diff" in before_sys) == ("frame_diff" in after_sys))
    removed = [l for l in difflib.ndiff(before_sys.splitlines(), after_sys.splitlines()) if l.startswith("- ")]
    added = [l for l in difflib.ndiff(before_sys.splitlines(), after_sys.splitlines()) if l.startswith("+ ")]
    print(f"     system prompt lines: {len(removed)} replaced, {len(added) - len(removed)} added")
    for l in removed:
        check("2 only an 'only' line was replaced", "exposes only" in l, l[:100])

    check("3 tool description lists the members", members in ta._PYTHON_TOOL_DESCRIPTION and before_tool != ta._PYTHON_TOOL_DESCRIPTION)

    class Fake:
        def _build_user_prompt(self, text):
            return text
    ns["arcaid3_wrap_user_prompt"](Fake)
    first_turn = ("Ground yourself in `current_frame` before acting, but start with a compact structural "
                  "summary rather than restating the full frame.")
    check("4 cue on dfranzen first turn", ns["ARCAID3_CUE"] in Fake()._build_user_prompt(first_turn))
    check("4 cue on dfranzen new level (LEVEL_START_USER_PROMPT)", ns["ARCAID3_CUE"] in Fake()._build_user_prompt(pr.LEVEL_START_USER_PROMPT))
    check("4 no cue on an ordinary turn", ns["ARCAID3_CUE"] not in Fake()._build_user_prompt("You are still on the same level."))

    big = [[5] * 64 for _ in range(64)]
    for r in range(8, 14):
        for c in range(8, 14):
            big[r][c] = 8
    moved = [row[:] for row in big]
    for r in range(8, 14):
        for c in range(8, 14):
            moved[r][c] = 5
    for r in range(8, 14):
        for c in range(12, 18):
            moved[r][c] = 8
    chars = sb.ARC_COLOR_CHARS

    def frame(g, step):
        return {"ascii": "\n".join("".join(chars[v] for v in row) for row in g), "step": step, "level": 1,
                "shape": [64, 64], "grid": g}
    state = {"current_frame": frame(moved, 2), "color_chars": chars,
             "history": [{"action": "RESET", "frame": frame(big, 1)}, {"action": "RIGHT", "frame": frame(moved, 2)}],
             "last_action_result": {}, "valid_actions": ["RIGHT"]}
    code = ("print(current_frame.code)\nprint(current_frame.changes_since(previous_frame))\n"
            "print(len(current_frame.native.splitlines()), len(current_frame.objects))\n"
            "print('FRAME_DIFF', str(frame_diff())[:200])\n"
            "def helper(x):\n    return x + 1\n")
    res = sb.run_sandboxed_python(code=code, timeout_seconds=60, initial_state=state,
                                  action_handler=lambda actions: {}, kept_functions=[], retain_imports=True)
    out = str(res.get("stdout", ""))
    check("5 sandbox call ran without error", not res.get("error"), str(res.get("error"))[:300])
    check("5 .code answers", "SCREEN 64x64 = world" in out and "OBJECTS" in out)
    check("5 .changes_since answers", "moved" in out)
    check("5 dfranzen frame_diff() still works beside it", "FRAME_DIFF" in out and "Traceback" not in out)
    print("---- sandbox stdout ----\n" + out[:1500])

    # v2: per-level scale lock. Run with ARCAID3_SCALE_LOCK=0 to check the kill switch instead.
    lock_on = os.environ.get("ARCAID3_SCALE_LOCK", "1") != "0"
    if lock_on:
        check("6 scale lock on and its sandbox self-test passes", rep.get("scale_lock") == "on, self-test ok", rep.get("scale_lock"))
    else:
        check("6 kill switch: scale lock off", str(rep.get("scale_lock", "")).startswith("off (ARCAID3_SCALE_LOCK=0)"), rep.get("scale_lock"))

    def toy(blocks):
        world = [[5] * 32 for _ in range(32)]
        world[20][20] = 8
        for r0, c0 in blocks:
            for r in range(r0, r0 + 3):
                for c in range(c0, c0 + 3):
                    world[r][c] = 9
        return [[world[y // 2][x // 2] for x in range(64)] for y in range(64)]
    seq = [toy([(5, 5), (5, 12)]), toy([(5, 5), (5, 8)]), toy([(5, 5), (5, 11)])]
    tstate = {"current_frame": frame(seq[2], 3), "color_chars": chars,
              "history": [{"action": "RESET", "frame": frame(seq[0], 1)}, {"action": "LEFT", "frame": frame(seq[1], 2)},
                          {"action": "RIGHT", "frame": frame(seq[2], 3)}],
              "last_action_result": {}, "valid_actions": ["LEFT", "RIGHT"]}
    tres = sb.run_sandboxed_python(code="print(current_frame.code)\nprint(current_frame.changes_since(previous_frame))\n",
                                   timeout_seconds=60, initial_state=tstate, action_handler=lambda actions: {},
                                   kept_functions=[], retain_imports=True)
    tout = str(tres.get("stdout", ""))
    # expected names come from the lexicon's own naming rule, so the checks follow its format
    _spec = importlib.util.spec_from_file_location("lexicon_names", HERE / "lexicon.py")
    _lx = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_lx)
    red1, blue3, blue1 = (_lx._stable_name(p, chars) for p in (((8,),), ((9, 9, 9),) * 3, ((9,),)))
    if lock_on:
        check("7 sparse frame read at the level's 2 px grid, marker kept", "each cell 2x2 px (locked for this level)" in tout and red1 in tout, tout.splitlines()[0][:120] if tout else tres.get("error"))
        check("7 changes_since across the contact keeps the original name", blue3 in tout and not tres.get("error"))
    else:
        check("7 kill switch: sparse frame falls back to its own 6 px detection", "each cell 6x6 px," in tout, tout.splitlines()[0][:120] if tout else tres.get("error"))
    print("---- lock sandbox stdout ----\n" + tout[:800])

    # v3: rules learned in the sandbox. Run with ARCAID3_RULES=0 to check the kill switch instead.
    rules_on = os.environ.get("ARCAID3_RULES", "1") != "0"
    if rules_on:
        check("8 rules on and their sandbox self-test passes", rep.get("rules") == "on, self-test ok", rep.get("rules"))
    else:
        check("8 kill switch: rules off", str(rep.get("rules", "")).startswith("off (ARCAID3_RULES=0)"), rep.get("rules"))

    def level(n_steps):
        """RIGHT moves a 3x3 block one cell; MOUSE on the tile toggles it 7 <-> 10 (2 px per cell)."""
        hist, c0, tile = [], 2, 7
        acts = [""] + [("RIGHT" if i % 2 == 0 else "MOUSE(row=50, col=50)") for i in range(n_steps)]
        for i, a in enumerate(acts):
            if a == "RIGHT":
                c0 = c0 + 1 if c0 < 26 else 2
            elif a:
                tile = 10 if tile == 7 else 7
            world = [[5] * 32 for _ in range(32)]
            world[15][3] = 8                          # one-cell marker: pins the 2 px grid (as in check 7)
            for r in range(5, 8):
                for c in range(c0, c0 + 3):
                    world[r][c] = 9
            for r in range(24, 27):
                for c in range(24, 27):
                    world[r][c] = tile
            g = [[world[y // 2][x // 2] for x in range(64)] for y in range(64)]
            hist.append({"action": a, "frame": frame(g, i + 1)})
        return {"current_frame": hist[-1]["frame"], "history": hist, "last_action_result": {},
                "valid_actions": ["RIGHT", "MOUSE"]}
    rres = sb.run_sandboxed_python(code="print(current_frame.rules)\n", timeout_seconds=60, initial_state=level(10),
                                   action_handler=lambda actions: {}, kept_functions=[], retain_imports=True)
    rout = str(rres.get("stdout", ""))
    if rules_on:
        check("9 toy level: RIGHT moves the block, the click recolours the tile, last step reported",
              "then move(" in rout and "recolor(clicked" in rout and "LAST STEP MOUSE(row=50, col=50)" in rout
              and not rres.get("error"), str(rres.get("error"))[:300])
        t0 = time.time()
        big = sb.run_sandboxed_python(code="print(current_frame.rules)\n", timeout_seconds=60, initial_state=level(150),
                                      action_handler=lambda actions: {}, kept_functions=[], retain_imports=True)
        dt = time.time() - t0
        check("10 a 150-step level answers within 10 s (tool limit 30 s)", dt < 10 and "RULES for level" in str(big.get("stdout", "")),
              f"{dt:.1f}s")
    else:
        check("9 kill switch: .rules says it is off", "switched off (ARCAID3_RULES=0)" in rout, rout[:120])
    print("---- rules sandbox stdout ----\n" + rout[:1500])

    # v4: the rules cue, object permanence, the finer-grid lock check
    class Fr:
        def __init__(self, level):
            self.level = level

    class En:
        def __init__(self, action, level):
            self.action, self.frame = action, Fr(level)

    class Agent:
        def _build_user_prompt(self, *args, **kwargs):
            return "turn"
    ns["arcaid3_wrap_user_prompt"](Agent)
    agent = Agent()

    def turn(n, changed=True):
        hist = [En("", 1)] + [En("RIGHT", 1) for _ in range(n)]
        return agent._build_user_prompt(1, current_frame=Fr(1), history_entries=hist,
                                        previous_step_summary={"executed_count": 1, "gameplay_changed": changed})
    t2, t4, t6 = turn(2, changed=False), turn(4, changed=False), turn(6)
    if rules_on:
        check("11 rules cue: none at 2 actions, 'changed nothing' at 4, 'taken 6 actions' at 6",
              "current_frame.rules" not in t2 and ns["ARCAID3_RULES_CUE_STILL"] in t4
              and "You have taken 6 actions on this level" in t6, repr((t2[-60:], t4[-60:], t6[-60:])))

    def walls(ac, step):
        world = [[5] * 32 for _ in range(32)]
        world[10][10] = world[11][10] = 8
        world[20][20] = 3
        world[10][ac] = 9
        return frame([[world[y // 2][x // 2] for x in range(64)] for y in range(64)], step)
    wstate = {"current_frame": walls(11, 3), "color_chars": chars,
              "history": [{"action": "", "frame": walls(13, 1)}, {"action": "LEFT", "frame": walls(12, 2)},
                          {"action": "LEFT", "frame": walls(11, 3)}],
              "last_action_result": {}, "valid_actions": ["LEFT"]}
    wres = sb.run_sandboxed_python(code="print(current_frame.changes_since(previous_frame))\n", timeout_seconds=60,
                                   initial_state=wstate, action_handler=lambda actions: {}, kept_functions=[],
                                   retain_imports=True)
    wout = str(wres.get("stdout", ""))
    check("12 object permanence: the step against the wall is a move, not the wall becoming a new picture",
          f"{blue1} moved (10, 12)->(10, 11)" in wout and "became" not in wout and not wres.get("error"), wout[:200])

    def block(c0, step):
        world = [[5] * 32 for _ in range(32)]
        for r in range(5, 8):
            for c in range(c0, c0 + 3):
                world[r][c] = 9
        for r in range(24, 27):
            for c in range(24, 27):
                world[r][c] = 7
        return frame([[world[y // 2][x // 2] for x in range(64)] for y in range(64)], step)
    seq3 = [block(c, i + 1) for i, c in enumerate((2, 3, 4, 5))]
    bstate = {"current_frame": seq3[-1], "color_chars": chars,
              "history": [{"action": "" if i == 0 else "RIGHT", "frame": f} for i, f in enumerate(seq3)],
              "last_action_result": {}, "valid_actions": ["RIGHT"]}
    bres = sb.run_sandboxed_python(code="print(current_frame.code)\n", timeout_seconds=60, initial_state=bstate,
                                   action_handler=lambda actions: {}, kept_functions=[], retain_imports=True)
    bout = str(bres.get("stdout", ""))
    if lock_on:
        check("13 lock: 3-cell objects moving 1 cell are read at the true 2 px grid, no marker",
              "each cell 2x2 px (locked for this level)" in bout and not bres.get("error"), bout.splitlines()[0][:120] if bout else bres.get("error"))

    # v5: names wide enough not to collide, and a collision fallback taken from the picture itself
    pq = (((9, 9),), ((9,), (9,)), ((9, 9, 9),))
    short = _lx._stable_name
    _lx._stable_name = lambda patch, cc: "bzzzz"          # force every picture onto one short name
    try:
        l1, l2, l3 = (_lx.Lexicon(naming="stable", color_chars=chars) for _ in range(3))
        n1 = [l1.symbol_for(p) for p in (pq[0], pq[1])]     # q arrives after p
        n2 = [l2.symbol_for(p) for p in (pq[2], pq[1])]     # q arrives after another picture
        n3 = [l3.symbol_for(p) for p in (pq[1], pq[0])]     # p arrives after q
    finally:
        _lx._stable_name = short
    check("14 names: 4 hex digits; a colliding picture's fallback name depends only on the picture",
          re.fullmatch(r"b[0-9a-f]{4}", blue3) is not None and n1[1] == n2[1] != n3[1] and n1[1].startswith("bzzzz_"),
          repr((blue3, n1, n2, n3)))

    # v5: when the rules' time budget runs out, the newest step is still the one reported
    if rules_on:
        rg = {"LX": _lx, "__name__": "arcaid3_rules_check"}
        exec(compile((ROOT / "design/2026-10-07__rule-grammar/rule_grammar.py").read_text(), "rule_grammar", "exec"), rg)
        rv = {"__name__": "arcaid3_rules_view_check"}
        exec(compile((HERE / "rules_view.py").read_text(), "rules_view", "exec"), rv)
        lexr = _lx.Lexicon(naming="stable", color_chars=chars)
        cols = (2, 3, 4, 5, 4)
        rseq = []
        for i, c in enumerate(cols):
            world = [[5] * 32 for _ in range(32)]
            world[15][3] = 8                          # one-cell marker: pins the 2 px grid (as in check 9)
            for r in range(5, 8):
                for cc in range(c, c + 3):
                    world[r][cc] = 9
            rseq.append(("" if i == 0 else ("LEFT" if i == len(cols) - 1 else "RIGHT"),
                         [[world[y // 2][x // 2] for x in range(64)] for y in range(64)]))
        rtext = rv["report"](rg, rseq, lambda fr, prev: _lx.encode(fr, lexr, prev=prev), level=1, budget=0.0)
        check("15 rules out of time: the older steps are skipped, LAST STEP is the newest action",
              "LAST STEP LEFT" in rtext and "older ones skipped for time" in rtext, rtext[:300])
    print("ALL PASS" if ok else "SOME CHECKS FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
