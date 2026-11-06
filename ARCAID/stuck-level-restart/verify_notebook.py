"""Check a built restart notebook against Franzen v1 and his bundle, offline.

  python kaggle/restart-dfranzen/verify_notebook.py <notebook.ipynb> <unpatched bundle dir> [<patch the notebook must embed>]

<unpatched bundle dir> is dfranzen/taaf-kaggle-source-bundle-copy as downloaded (no patch applied).
Checks:
  1. every Franzen v1 cell is present and unchanged, except cells 4 and 16, which differ only by the
     anchored ARCAID3 lines;
  2. the two %%writefile patches, applied as cell 4 applies them, patch the bundle and leave the hook in;
  3. the patched tool_agent.py compiles;
  4. the submission branch carries the competition asserts and the save run the leaderboard-like setup.
"""
from __future__ import annotations

import difflib
import json
import pathlib
import py_compile
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / "external_submission/2026-09-30__dfranzen__arc-agi-3-milestone-2-solution__v1__teambest-27.89/__notebook__.ipynb"
OK = []


def check(name, cond, detail=""):
    OK.append(bool(cond))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f": {detail}" if detail and not cond else ""))


def src(c):
    return "".join(c["source"])


def main():
    nb = json.loads(pathlib.Path(sys.argv[1]).read_text())
    bundle = pathlib.Path(sys.argv[2]).resolve()
    base = json.loads(BASE.read_text())["cells"]
    cells = nb["cells"]
    added = [i for i, c in enumerate(cells) if src(c).startswith(("# ARCAID3: stuck-level restart on", "%%writefile /kaggle/restart.patch",
                                                                  "# ARCAID3: restart events"))]
    check("three cells added (head, patch, summary)", len(added) == 3, str(added))
    rest = [c for i, c in enumerate(cells) if i not in added]
    check("Franzen's 23 cells present in order", len(rest) == len(base) == 23, f"{len(rest)} vs {len(base)}")
    changed = [i for i, (a, b) in enumerate(zip(rest, base)) if src(a) != src(b)]
    check("only cells 4 and 16 differ from Franzen v1", changed == [4, 16], str(changed))
    for i in changed:
        diff = [l for l in difflib.unified_diff(src(base[i]).splitlines(), src(rest[i]).splitlines(), lineterm="", n=0)
                if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
        removed = [l for l in diff if l.startswith("-")]
        added_lines = [l for l in diff if l.startswith("+")]
        allowed_removed = {
            4: [],
            16: ["-demo_excluded_games = [] if TRUE_SUBMISSION else ['bp35', 'cd82', 'cn04', 'dc22', 'g50t', 'ka59', 'lf52', 'ls20', 'm0r0', 's5i5', 'sk48', 'sp80', 'su15', 'tn36', 'wa30']",
                 "-        bm.solver.max_runtime_s_per_game = 25*60 #532*60 * bm.solver.concurrency // 110"],
        }[i]
        check(f"cell {i}: only the anchored lines removed", removed == allowed_removed, "\n".join(removed))
        check(f"cell {i}: every added line is marked or is the restart apply/asserts",
              all(("ARCAID3" in l or "restart" in l.lower() or "assert" in l or "_restart_src" in l
                   or "STUCK_RESTART" in l) for l in added_lines), "\n".join(added_lines))

    franzen_patch = src(rest[2])
    assert franzen_patch.startswith("%%writefile /kaggle/harness-changes.patch\n")
    restart_patch = src(cells[added[1]])
    work = pathlib.Path(tempfile.mkdtemp()) / "src"
    shutil.copytree(bundle / "src", work)
    for name, body in (("harness-changes.patch", franzen_patch), ("restart.patch", restart_patch)):
        p = work.parent / name
        # what %%writefile writes: IPython's transform_cell adds a final newline to a cell without one
        p.write_text((body if body.endswith("\n") else body + "\n").split("\n", 1)[1])
        r = subprocess.run(["git", "apply", "--include=ARC3-Inference/*", "-v", str(p)], cwd=work, capture_output=True, text=True)
        check(f"{name} applies as cell 4 applies it", r.returncode == 0, r.stderr[-500:])
    ta = work / "ARC3-Inference/inference/agent/tool_agent.py"
    text = ta.read_text()
    check("hook present after both patches", "def _maybe_restart_stuck_level" in text and "restart_note = self._maybe_restart_stuck_level" in text)
    try:
        py_compile.compile(str(ta), doraise=True)
        check("patched tool_agent.py compiles", True)
    except py_compile.PyCompileError as exc:
        check("patched tool_agent.py compiles", False, str(exc))
    expected = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else HERE / "restart.patch"
    check(f"restart patch in the notebook equals {expected.name}", restart_patch.split("\n", 1)[1] == expected.read_text())

    c16 = src(rest[16])
    check("submission branch asserts concurrency 120 and 532 min", "assert bm.solver.concurrency == 120 and bm.solver.max_runtime_s_per_game == 532*60" in c16)
    check("save run: all 25 games, leaderboard GPU share", "demo_excluded_games = []  # ARCAID3" in c16
          and "532*60 * bm.solver.concurrency // 110  # ARCAID3" in c16)
    c4 = src(rest[4])
    check("restart flag set in cell 4", "STUCK_RESTART_TOKENS = " in c4 and "os.environ['ARC3_STUCK_RESTART_TOKENS']" in c4)
    print(f"{sum(OK)} of {len(OK)} pass")
    sys.exit(0 if all(OK) else 1)


if __name__ == "__main__":
    main()
