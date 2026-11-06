"""Compare a notebook with the notebook it was built on, cell by cell, and write what changed.

  python -I notebook_diff.py BASE.ipynb NEW.ipynb OUT_DIR [--label NAME]

Writes to OUT_DIR:
  DIFF.md            every cell: identical / added / changed / removed, with +/- line counts
  added/cellNN.py    the full source of every added or changed code cell (markdown as .md)
  changed/cellNN.diff  a unified diff of every changed cell against its base cell
Cells are matched in order by exact text (difflib on the cell list). `%%writefile` cells are also
matched by the file they write, so a changed module is reported under its file name.
Only the notebook text is compared; outputs are ignored.
"""
import argparse, difflib, hashlib, json, re
from pathlib import Path


def cells(p):
    nb = json.loads(Path(p).read_text(encoding="utf-8"))
    out = []
    for c in nb["cells"]:
        s = c["source"] if isinstance(c["source"], str) else "".join(c["source"])
        out.append((c["cell_type"], s))
    return out


def wf(s):
    m = re.match(r"\s*%%writefile\s+(\S+)", s)
    return m and Path(m.group(1)).name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base"); ap.add_argument("new"); ap.add_argument("out")
    ap.add_argument("--label", default="")
    a = ap.parse_args()
    A, B = cells(a.base), cells(a.new)
    out = Path(a.out); (out / "added").mkdir(parents=True, exist_ok=True); (out / "changed").mkdir(exist_ok=True)
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
    rows = [f"# Cell diff{': ' + a.label if a.label else ''}", "",
            f"- Base: `{Path(a.base).name}` (sha256 {sha(a.base)}…), {len(A)} cells",
            f"- New: `{Path(a.new).name}` (sha256 {sha(a.new)}…), {len(B)} cells", "",
            "| New cell | Base cell | Type | Status | +lines | −lines | First line |", "|---|---|---|---|---|---|---|"]
    sm = difflib.SequenceMatcher(None, [s for _, s in A], [s for _, s in B], autojunk=False)
    base_by_file = {wf(s): i for i, (_, s) in enumerate(A) if wf(s)}
    tot = {"identical": 0, "added": 0, "changed": 0, "removed": 0}
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            tot["identical"] += i2 - i1
            rows.append(f"| {j1}–{j2-1} | {i1}–{i2-1} | | identical ({i2-i1} cells) | 0 | 0 | |")
            continue
        used = set()
        for j in range(j1, j2):
            t, s = B[j]
            i = None
            f = wf(s)
            if f:
                i = base_by_file.get(f)          # a %%writefile cell is matched only by its file name
            elif op == "replace" and i1 + (j - j1) < i2:
                i = i1 + (j - j1)
            if i is not None and A[i][0] == t:
                used.add(i)
                d = list(difflib.unified_diff(A[i][1].splitlines(), s.splitlines(), lineterm="", n=2,
                                              fromfile=f"base cell {i}", tofile=f"new cell {j}"))
                add = sum(1 for l in d if l.startswith("+") and not l.startswith("+++"))
                rem = sum(1 for l in d if l.startswith("-") and not l.startswith("---"))
                if add == rem == 0:
                    tot["identical"] += 1; continue
                status = "changed"; (out / "changed" / f"cell{j:02d}.diff").write_text("\n".join(d) + "\n")
            else:
                add, rem, status = len(s.splitlines()), 0, "added"
            tot[status] += 1
            ext = ".py" if t == "code" else ".md"
            (out / "added" / f"cell{j:02d}{ext}").write_text(s + ("\n" if not s.endswith("\n") else ""))
            first = (s.strip().splitlines() or [""])[0][:90].replace("|", "\\|")
            rows.append(f"| {j} | {'' if i is None else i} | {t} | {status} | {add} | {rem} | `{first}` |")
        for i in range(i1, i2):
            if i not in used and op in ("delete", "replace") and not any(
                    wf(B[j][1]) and wf(B[j][1]) == wf(A[i][1]) for j in range(len(B))):
                tot["removed"] += 1
                first = (A[i][1].strip().splitlines() or [""])[0][:90].replace("|", "\\|")
                rows.append(f"| | {i} | {A[i][0]} | removed | 0 | {len(A[i][1].splitlines())} | `{first}` |")
    rows += ["", "**Totals:** " + ", ".join(f"{k} {v}" for k, v in tot.items())]
    (out / "DIFF.md").write_text("\n".join(rows) + "\n")
    print(out, tot)


if __name__ == "__main__":
    main()
