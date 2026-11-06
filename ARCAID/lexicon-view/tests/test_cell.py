"""Tests for the Part III cell against the real Duck sandbox and agent modules.

Uses the Kaggle Duck bundle stored in this repo
(inputs/arc3-collections/1345/fp4src/ARC3-Inference), the 4.17 notebook's own F13 patch,
and real frames from the official public games. Each scenario runs in a fresh Python process.

The v2 scenarios also load Scott Le Grand's full agentfix cell first (cell 10 of the 4.17 notebook),
exactly as the notebook does, and check the prompts the model would receive. agentfix also imports
inference.framework, which keithtyser's stored bundle lacks, so those scenarios run on a composite
tree: keithtyser's agent modules (what ran on Kaggle) plus the missing framework/tools/helper modules
from the Tufa bundle in inputs/arc3-collections/1345/taaf/src. That is a test approximation; on Kaggle
the READY line reports which prompt edits applied.

Needs Python 3.12 with arc-agi==0.9.8 and arcengine==0.9.3, plus (for agentfix) pillow, imageio,
scipy, matplotlib, pandas, requests, pydantic. From the repo root:
  python arcaid3/part3/test_cell.py
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import textwrap

ROOT = pathlib.Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "inputs/arc3-collections/1345/fp4src/ARC3-Inference"
CELL = (ROOT / "arcaid3/part3/lexicon_view_cell.py").read_text()
BASE_NB = ROOT / "submissions/2026-09-30__taaf-flashnext-sheetu12b-0922__v1__score-4.17/__notebook__.ipynb"

# Scott Le Grand's F13 sandbox edit, cut verbatim from the 4.17 notebook's agentfix cell
_agentfix = "".join(json.load(open(BASE_NB))["cells"][10]["source"])
_a = _agentfix.index("# --------------------------------------------------------------------------- sandbox template")
_b = _agentfix.index("# ===== end agentfix_anim.py =====")
F13_SOURCE = _agentfix[_a:_b]
TAAF = ROOT / "inputs/arc3-collections/1345/taaf/src"
PROMPT_CHANGES = ROOT / "arcaid3/part3/notebook-v2/PROMPT-CHANGES.md"


def composite_tree() -> pathlib.Path:
    """keithtyser's ARC3-Inference + the modules agentfix imports that it lacks (from the Tufa bundle)."""
    dest = pathlib.Path(tempfile.mkdtemp(prefix="arcaid3_composite_")) / "ARC3-Inference"
    skip = shutil.ignore_patterns("__pycache__")
    shutil.copytree(BUNDLE, dest, ignore=skip)
    src = TAAF / "ARC3-Inference/inference"
    for sub in ("framework", "tools"):
        shutil.copytree(src / sub, dest / "inference" / sub, ignore=skip)
    for sub in ("utils", "agent"):
        for f in (src / sub).glob("*.py"):
            if not (dest / "inference" / sub / f.name).exists():
                shutil.copy(f, dest / "inference" / sub / f.name)
    return dest

PRELUDE = f"""
import json, logging, sys
logging.disable(logging.CRITICAL)
sys.path.insert(0, {str(BUNDLE)!r})
sys.path.insert(0, {str(ROOT / 'arcaid3/part2')!r})
import inference.agent.python_tool_sandbox as sb
import inference.agent.tool_agent as ta
CELL = {CELL!r}
F13 = {F13_SOURCE!r}

def frame(g, step=1, level=1):
    return {{"ascii": "\\n".join("".join(sb.ARC_COLOR_CHARS[v] for v in row) for row in g),
             "step": step, "level": level, "shape": [len(g), len(g[0])], "grid": g}}

def run(code, state):
    return sb.run_sandboxed_python(code=code, timeout_seconds=60, initial_state=state,
                                   action_handler=lambda a: {{}})

def game_frames(game, actions):
    import arc_agi, groundtruth as gt
    from arcengine import GameAction
    arc = gt.arcade(); env = arc.make(gt.game_ids(arc)[game], seed=0)
    out = [[list(map(int, r)) for r in env.reset().frame[-1]]]
    for name, data in actions:
        f = env.step(GameAction[name], data=data)
        out.append([[int(v) for v in r] for r in f.frame[-1]])
    return out
"""

AGENTFIX_PRELUDE = """
import contextlib, difflib, io, json, logging, os, sys, types
logging.disable(logging.CRITICAL)
os.environ.setdefault("MULTIMODAL_UPSCALE", "4"); os.environ.setdefault("MULTIMODAL_CONTEXT", "current_grid")
sys.path.insert(0, __COMPOSITE__); sys.path.insert(0, __TAAF_SRC__)
AGENTFIX = __AGENTFIX__
CELL = __CELL__
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(AGENTFIX, "agentfix_cell", "exec"), {"__name__": "__main__"})
import inference.agent.tool_agent as ta

def system():
    return ta._build_system_prompt(tool_output_tokens=1024)

def user(action_num, summary=None):
    fake = types.SimpleNamespace(_summarized_knowledge_lines=lambda: [])
    return ta.ToolAgent._build_user_prompt(fake, action_num, valid_actions=["UP"], current_frame=None,
                                           history_entries=[], previous_step_summary=summary)

def run_cell():
    ns = {}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(CELL, ns)
    return ns

NEW_LEVEL = {"executed_count": 1, "executed_actions": ["UP"], "level_transition": True, "level": 2}
SAME_LEVEL = {"executed_count": 1, "executed_actions": ["UP"], "level_transition": False, "level": 1}
ONLY_LINES = ("exposes only `.ascii`, `.step`, `.level`, `.shape`, and `.segmentation`",
              "expose only `.ascii`, `.segmentation`, `.step`, and `.level`")
"""

AGENTFIX_SCENARIOS = {
    "v2_prompt_edits_on_top_of_agentfix": """
stock_sys, stock_tool = system(), ta._PYTHON_TOOL_DESCRIPTION
ns = run_cell()
rep = ns["ARCAID3_REPORT"]
assert rep["installed"] and set(rep["prompt_edits"].values()) == {"applied"}, rep
assert rep["first_turn_cue"] == "installed", rep
new_sys, new_tool = system(), ta._PYTHON_TOOL_DESCRIPTION
for line in ONLY_LINES:
    assert line not in new_sys and line not in new_tool, line
assert "Some actions animate" in new_sys, "F13 note lost"
assert new_sys.count(ns["_A3_TRIGGER"]) == 1 and ns["ARCAID3_NOTE"] in new_sys
assert "`.code`" in new_tool
removed = [l for l in difflib.ndiff(stock_sys.splitlines(), new_sys.splitlines()) if l.startswith("- ")]
added = [l for l in difflib.ndiff(stock_sys.splitlines(), new_sys.splitlines()) if l.startswith("+ ")]
assert len(removed) == 2 and len(added) == 4, (len(removed), len(added))   # 2 rewritten "only" lines; + trigger + note
u0, u_new, u_same = user(0), user(3, NEW_LEVEL), user(3, SAME_LEVEL)
md = ["# Prompt changes in v2 (generated by arcaid3/part3/test_cell.py)", "",
      "Built from the real harness modules with Scott Le Grand's agentfix cell loaded first, then the v2 cell.", "",
      "## System prompt: lines removed", ""] + [f"    {l[2:]}" for l in removed] + [
      "", "## System prompt: lines added", ""] + [f"    {l[2:]}" for l in added] + [
      "", "## Tool description", "", "Before:", "", "    " + stock_tool, "", "After:", "", "    " + new_tool, "",
      "## User message: first turn of a game (last two lines)", ""] + ["    " + l for l in u0.splitlines()[-2:]] + [
      "", "## User message: after a level change (last two lines)", ""] + ["    " + l for l in u_new.splitlines()[-2:]] + [
      "", "## User message: same level (last line; no cue)", "", "    " + u_same.splitlines()[-1], ""]
open(sys.argv[1], "w").write("\\n".join(md))
print("OK", rep["prompt_edits"], "removed", len(removed), "added", len(added))
""",
    "v2_first_turn_and_new_level_cue": """
ns = run_cell()
cue = ns["ARCAID3_CUE"]
assert user(0).count(cue) == 1, "first turn"
assert user(3, NEW_LEVEL).count(cue) == 1, "new level"
assert cue not in user(3, SAME_LEVEL), "ordinary turn must not get the cue"
assert ns["ARCAID3_STATS"]["cue_turns"] == 2, ns["ARCAID3_STATS"]
print("OK cue on first turn and new level only", ns["ARCAID3_STATS"]["cue_turns"])
""",
    "v2_idempotent_on_top_of_agentfix": """
ns = run_cell()
ns2 = run_cell()
rep2 = ns2["ARCAID3_REPORT"]
assert set(rep2["prompt_edits"].values()) == {"already"} and rep2["first_turn_cue"] == "already", rep2
assert system().count(ns2["_A3_TRIGGER"]) == 1
assert user(0).count(ns2["ARCAID3_CUE"]) == 1
print("OK second run changes nothing", rep2["prompt_edits"])
""",
    "v2_kill_switch_on_top_of_agentfix": """
os.environ["ARCAID3_LEXICON"] = "0"
stock_sys, stock_tool, stock_u0 = system(), ta._PYTHON_TOOL_DESCRIPTION, user(0)
ns = run_cell()
assert ns["ARCAID3_REPORT"] == {"enabled": False, "installed": False}
assert system() == stock_sys and ta._PYTHON_TOOL_DESCRIPTION == stock_tool and user(0) == stock_u0
print("OK off switch leaves every prompt byte-identical")
""",
}

SCENARIOS = {
    "installs_and_self_tests": """
ns = {}
exec(CELL, ns)
rep = ns["ARCAID3_REPORT"]
assert rep["installed"] and rep["self_test"] == "ok", rep
assert ns["ARCAID3_NOTE"] in ta.STRUCTURED_RUNTIME_STATE_ADDENDUM
assert "_arcaid3_encode" in sb._SANDBOX_BOOTSTRAP
print("OK", rep)
""",
    "idempotent": """
ns = {}
exec(CELL, ns); first = sb._SANDBOX_BOOTSTRAP; wrapped = ta.run_sandboxed_python
exec(CELL, ns)
assert sb._SANDBOX_BOOTSTRAP == first, "patched twice"
assert ta.STRUCTURED_RUNTIME_STATE_ADDENDUM.count(ns["ARCAID3_NOTE"]) == 1
assert ta.run_sandboxed_python is wrapped, "counter wrapped twice"
print("OK")
""",
    "kill_switch": """
import os
os.environ["ARCAID3_LEXICON"] = "0"
stock = sb._SANDBOX_BOOTSTRAP; addendum = ta.STRUCTURED_RUNTIME_STATE_ADDENDUM
ns = {}
exec(CELL, ns)
assert ns["ARCAID3_REPORT"] == {"enabled": False, "installed": False}
assert sb._SANDBOX_BOOTSTRAP == stock and ta.STRUCTURED_RUNTIME_STATE_ADDENDUM == addendum
print("OK")
""",
    "composes_with_f13_either_order": """
fns = {}
exec(F13, fns)
stock = sb._SANDBOX_BOOTSTRAP
# order used in the notebook: agentfix (F13) first, then this cell
sb._SANDBOX_BOOTSTRAP = fns["_anim_patch_sandbox_source"](stock)
ns = {}
exec(CELL, ns)
assert ns["ARCAID3_REPORT"]["installed"], ns["ARCAID3_REPORT"]
both = sb._SANDBOX_BOOTSTRAP
assert "self.frame_count" in both and "_arcaid3_encode" in both
# reverse order also patches cleanly
rev = fns["_anim_patch_sandbox_source"](ns["arcaid3_patch_sandbox_source"](stock))
compile(rev, "<rev>", "exec")
# an F13 intermediate frame arrives as ascii only: the view must decode it
g0 = [[5] * 64 for _ in range(64)]
g1 = [row[:] for row in g0]
for r in range(20, 24):
    for c in range(20, 24):
        g1[r][c] = 8
mid = {"ascii": frame(g1)["ascii"], "index": 1}
cur = frame(g1, 2); cur["frames"] = [mid]; cur["frame_count"] = 2
state = {"current_frame": cur, "history": [{"action": "RESET", "frame": frame(g0)}, {"action": "UP", "frame": cur}],
         "last_action_result": {}, "valid_actions": ["UP"]}
res = run("print(len(last_transition.frames)); print(last_transition.frames[0].code)", state)
assert not res.get("error"), res
assert "OBJECTS 1 in 1 kinds" in res["stdout"], res["stdout"]
print("OK", res["stdout"].splitlines()[:3])
""",
    "real_game_frames": """
ns = {}
exec(CELL, ns)
report = {}
cases = {"ls20": [("ACTION1", None)], "ft09": [("ACTION6", {"x": 13, "y": 13})], "sb26": [("ACTION1", None)]}
for game, acts in cases.items():
    f0, f1 = game_frames(game, acts)
    state = {"current_frame": frame(f1, 2), "history": [{"action": "RESET", "frame": frame(f0)},
             {"action": acts[0][0], "frame": frame(f1, 2)}], "last_action_result": {}, "valid_actions": []}
    res = run("print(current_frame.code)\\nprint('--- CHANGES')\\nprint(current_frame.changes_since(previous_frame))"
              "\\nprint('--- FIRST OBJECT', current_frame.objects[0])", state)
    assert not res.get("error"), (game, res)
    assert res["stdout"].startswith("SCREEN 64x64"), res["stdout"][:200]
    report[game] = res["stdout"]
open(sys.argv[1], "w").write(json.dumps(report, indent=1))
print("OK", {g: len(t) for g, t in report.items()})
""",
    "stable_names_across_processes": """
ns = {}
exec(CELL, ns)
f0, f1 = game_frames("ft09", [("ACTION6", {"x": 13, "y": 13})])
state = {"current_frame": frame(f1, 2), "history": [{"action": "RESET", "frame": frame(f0)},
         {"action": "ACTION6", "frame": frame(f1, 2)}], "last_action_result": {}, "valid_actions": []}
a = run("print(current_frame.code)", state)["stdout"]
b = run("print(current_frame.code)", state)["stdout"]
assert a == b and a.startswith("SCREEN"), (a[:200], b[:200])
print("OK same text in two sandbox processes")
""",
    "counter_counts_model_use": """
ns = {}
exec(CELL, ns)
g = [[5] * 64 for _ in range(64)]
state = {"current_frame": frame(g), "history": [], "last_action_result": {}, "valid_actions": []}
ta.run_sandboxed_python(code="print(current_frame.code)", timeout_seconds=30, initial_state=state,
                        action_handler=lambda a: {})
ta.run_sandboxed_python(code="print(current_frame.ascii[:5])", timeout_seconds=30, initial_state=state,
                        action_handler=lambda a: {})
st = ns["ARCAID3_STATS"]
assert st["tool_calls"] == 2 and st["calls_using_view"] == 1 and st["code"] == 1, st
print("OK", st)
""",
    "speed_on_all_25_first_frames": """
import time
ns = {}
exec(CELL, ns)
import groundtruth as gt
arc = gt.arcade()
frames = []
for gid in sorted(gt.game_ids(arc).values()):
    env = arc.make(gid, seed=0)
    frames.append([[int(v) for v in r] for r in env.reset().frame[-1]])
hist = [{"action": "RESET", "frame": frame(f)} for f in frames]
state = {"current_frame": frame(frames[0]), "history": hist, "last_action_result": {}, "valid_actions": []}
t = time.time()
res = run("n=0\\nfor h in history:\\n    n += len(h.frame.code)\\nprint(n)", state)
assert not res.get("error"), res
print("OK 25 boards encoded inside one sandbox call in %.2f s" % (time.time() - t))
""",
}


def main() -> None:
    py = sys.executable
    extra_args = {"real_game_frames": ROOT / "arcaid3/part3/test_real_frames_output.json",
                  "v2_prompt_edits_on_top_of_agentfix": PROMPT_CHANGES}
    tree = composite_tree()
    agentfix_prelude = (AGENTFIX_PRELUDE.replace("__COMPOSITE__", repr(str(tree)))
                        .replace("__TAAF_SRC__", repr(str(TAAF / "tufa-arc-agi-framework/src")))
                        .replace("__AGENTFIX__", repr(_agentfix)).replace("__CELL__", repr(CELL)))
    runs = [(n, PRELUDE + textwrap.dedent(b)) for n, b in SCENARIOS.items()]
    runs += [(n, agentfix_prelude + textwrap.dedent(b)) for n, b in AGENTFIX_SCENARIOS.items()]
    failures = 0
    for name, script in runs:
        script_file = tree.parent / f"{name}.py"         # agentfix + cell are too long for a command line
        script_file.write_text(script)
        args = [py, str(script_file)] + ([str(extra_args[name])] if name in extra_args else [])
        p = subprocess.run(args, capture_output=True, text=True, env={**os.environ, "ARCAID3_LEXICON": "1"})
        ok = p.returncode == 0 and "OK" in p.stdout
        failures += not ok
        tail = (p.stdout.strip().splitlines() or [""])[-1][:220]
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {tail}")
        if not ok:
            print(p.stdout[-2000:], p.stderr[-3000:])
    shutil.rmtree(tree.parent, ignore_errors=True)
    print(f"{len(runs) - failures}/{len(runs)} passed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
