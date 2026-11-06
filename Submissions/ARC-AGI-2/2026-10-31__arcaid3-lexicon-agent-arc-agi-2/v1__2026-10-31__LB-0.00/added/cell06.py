%%writefile /kaggle/working/agent/lexicon2.py
"""ARCAID3 grid lexicon: the ARC-AGI-3 lexicon view read on static ARC-AGI-2 grids.

On ARC-AGI-3 (habanwer/arcaid3-lexicon-view-dfranzen-m2, LB 31.90) the sandbox gained
`current_frame.code` (objects with stable picture names and a legend), `.changes_since()`
(objects that moved / appeared / disappeared / became another picture) and `.rules`
(regularities learned from recent steps). Here a train pair plays the part of two frames:

  lexicon(g)       a grid as objects: background, palette, every picture with one name per
                   TASK (the same picture is called the same in every grid), a legend, and
                   rotation/mirror families (B = A rot90).
  changes(i)       train[i] input -> output as object events plus cell colour transitions;
                   for a size change, where the output sits in (or is built from) the input.
  rules()          facts that hold on EVERY train pair (size relation, geometry, colour map,
                   which cells may change, object bookkeeping, symmetry).
  lex_objects(g)   the same objects as data.

This file is executed inside the python tool's namespace (after repl.HELPERS, so `train`
and `test_inputs` are globals there) and is also imported by the harness, which calls
rules(pairs, tests) to put the digest into the first prompt. Names are assigned in a fixed
order (train inputs and outputs, then test inputs), so every fresh sandbox process and the
harness agree on them without saved state.
"""
import numpy as np
from collections import Counter

_N4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_N8 = _N4 + [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def _arr(g):
    return np.asarray(g, dtype=int)


def _bg(g):
    """Most common colour; ties go to 0, then the lower colour."""
    vals, counts = np.unique(g, return_counts=True)
    best = counts.max()
    tied = [int(v) for v, c in zip(vals, counts) if c == best]
    return 0 if 0 in tied else min(tied)


def _pieces(g, bg, diagonal=True):
    """Multicolour connected components of non-background cells (cells as (r, c))."""
    H, W = g.shape
    seen = np.zeros(g.shape, dtype=bool)
    nbrs = _N8 if diagonal else _N4
    out = []
    for r in range(H):
        for c in range(W):
            if seen[r, c] or g[r, c] == bg:
                continue
            seen[r, c] = True
            stack, cells = [(r, c)], []
            while stack:
                y, x = stack.pop()
                cells.append((y, x))
                for dy, dx in nbrs:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny, nx] and g[ny, nx] != bg:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            out.append(sorted(cells))
    return out


def _patch(g, cells):
    """The picture of a piece: its bbox, -1 where the cell is not part of it."""
    ys, xs = [p[0] for p in cells], [p[1] for p in cells]
    r0, c0 = min(ys), min(xs)
    p = [[-1] * (max(xs) - c0 + 1) for _ in range(max(ys) - r0 + 1)]
    for y, x in cells:
        p[y - r0][x - c0] = int(g[y, x])
    return tuple(tuple(row) for row in p), (r0, c0)


def _rot90(p):
    return tuple(tuple(p[len(p) - 1 - r][c] for r in range(len(p))) for c in range(len(p[0])))


def _variants(p):
    out, cur = [], p
    for k in range(4):
        out.append((f"rot{90 * k}", cur))
        out.append((f"mirror+rot{90 * k}", tuple(tuple(reversed(row)) for row in cur)))
        cur = _rot90(cur)
    return out


def _name(i):
    s, i = "", i + 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


class _Lex:
    """Picture -> name for one task, with rotation/mirror families."""

    def __init__(self):
        self.by_key, self.entries, self.by_canon = {}, {}, {}

    def sym(self, patch):
        s = self.by_key.get(patch)
        if s is None:
            s = _name(len(self.entries))
            canon = min(v for _, v in _variants(patch))
            fam = self.by_canon.setdefault(canon, s)
            pose = None
            if fam != s:
                pose = next(n for n, v in _variants(self.entries[fam]["patch"]) if v == patch)
            self.by_key[patch] = s
            self.entries[s] = {"patch": patch, "family": fam, "pose": pose}
        return s

    def picture(self, s):
        return ["".join("." if v < 0 else str(v) for v in row) for row in self.entries[s]["patch"]]


_LEX_CACHE = {}


def _task_lex(pairs=None, tests=None):
    """One lexicon per task, filled in a fixed order so names agree across processes."""
    if pairs is None:
        pairs, tests = train, test_inputs          # noqa: F821 (python-tool globals)
    key = id(pairs)
    if key not in _LEX_CACHE:
        lex = _Lex()
        for a, b in pairs:
            _encode(a, lex)
            _encode(b, lex)
        for t in tests or []:
            _encode(t, lex)
        _LEX_CACHE[key] = lex
    return _LEX_CACHE[key]


def _encode(g, lex, bg=None):
    g = _arr(g)
    bg = _bg(g) if bg is None else bg
    placed = []
    for cells in _pieces(g, bg):
        patch, at = _patch(g, cells)
        placed.append({"sym": lex.sym(patch), "at": at, "size": len(cells), "cells": cells,
                       "colors": sorted({int(g[y, x]) for y, x in cells})})
    placed.sort(key=lambda p: (p["at"], p["sym"]))
    return {"shape": g.shape, "bg": bg, "placed": placed}


def lex_objects(g, pairs=None, tests=None):
    """Objects of g as dicts: sym, at (top-left), bbox, size, colors, cells, patch (-1 = not part)."""
    lex = _task_lex(pairs, tests)
    code = _encode(g, lex)
    out = []
    for p in code["placed"]:
        patch = np.array(lex.entries[p["sym"]]["patch"])
        r0, c0 = p["at"]
        out.append(dict(p, bbox=(r0, c0, r0 + patch.shape[0] - 1, c0 + patch.shape[1] - 1), patch=patch))
    return out


def lexicon(g, legend=True, max_list=10, max_kinds=30, pairs=None, tests=None):
    """A grid as objects with task-wide names. Print it."""
    lex = _task_lex(pairs, tests)
    g = _arr(g)
    code = _encode(g, lex)
    pal = Counter(int(v) for v in g.ravel())
    groups = {}
    for p in code["placed"]:
        groups.setdefault(p["sym"], []).append(p["at"])
    order = sorted(groups, key=lambda s: min(groups[s]))
    lines = [f"GRID {g.shape[0]}x{g.shape[1]}, background {code['bg']}; colours "
             + " ".join(f"{c}:{n}" for c, n in sorted(pal.items())),
             f"OBJECTS {len(code['placed'])} in {len(groups)} kinds (8-connected, multicolour; "
             f"symbol xcount @ (row, col) of top-left cell):"]
    for s in order[:max_kinds]:
        ats = groups[s]
        more = f" ... +{len(ats) - max_list}" if len(ats) > max_list else ""
        lines.append(f"  {s} x{len(ats)} @ " + " ".join(f"({r},{c})" for r, c in ats[:max_list]) + more)
    if len(order) > max_kinds:
        lines.append(f"  ... {len(order) - max_kinds} more kinds")
    if legend:
        lines.append("LEGEND (. = not part of the object):")
        for s in order[:max_kinds]:
            e, pic = lex.entries[s], lex.picture(s)
            rel = f" = {e['family']} {e['pose']}" if e["pose"] else ""
            cols = ",".join(str(v) for v in sorted({v for row in e["patch"] for v in row if v >= 0}))
            body = "/".join(pic) if len(pic) <= 6 and len(pic[0]) <= 12 else "(large; use lex_objects)"
            lines.append(f"  {s} {len(pic)}x{len(pic[0])} [{cols}]{rel}: {body}")
    return "\n".join(lines)


def _object_events(ca, cb):
    """Object-level change between two encodings that share one lexicon (as on ARC-AGI-3)."""
    def by_sym(code):
        d = {}
        for p in code["placed"]:
            d.setdefault(p["sym"], []).append(p["at"])
        return d

    a, b = by_sym(ca), by_sym(cb)
    kept = 0
    for s in set(a) | set(b):
        for p in [p for p in a.get(s, []) if p in b.get(s, [])]:
            a[s].remove(p)
            b[s].remove(p)
            kept += 1
    moved, appeared, gone, became = [], [], [], []
    for s in sorted(set(a) | set(b), key=lambda s: (len(s), s)):
        left, right = list(a.get(s, [])), list(b.get(s, []))
        pairs = sorted((abs(l[0] - r[0]) + abs(l[1] - r[1]), l, r) for l in left for r in right)
        ul, ur = set(), set()
        for _, l, r in pairs:
            if l in ul or r in ur:
                continue
            ul.add(l)
            ur.add(r)
            moved.append((s, l, r))
        gone += [(s, l) for l in left if l not in ul]
        appeared += [(s, r) for r in right if r not in ur]
    for s0, at in list(gone):                      # same place, other picture: one change
        for s1, at1 in appeared:
            if at1 == at:
                became.append((s0, s1, at))
                gone.remove((s0, at))
                appeared.remove((s1, at1))
                break
    return {"kept": kept, "moved": moved, "became": became, "appeared": appeared, "gone": gone}


def _find(small, big):
    """Top-left positions where `small` occurs exactly inside `big`."""
    h, w = small.shape
    H, W = big.shape
    if h > H or w > W:
        return []
    return [(r, c) for r in range(H - h + 1) for c in range(W - w + 1)
            if np.array_equal(big[r:r + h, c:c + w], small)]


_GEOM = [("identity", lambda x: x), ("rot90", lambda x: np.rot90(x, 1)),
         ("rot180", lambda x: np.rot90(x, 2)), ("rot270", lambda x: np.rot90(x, 3)),
         ("flip_lr", np.fliplr), ("flip_ud", np.flipud), ("transpose", lambda x: x.T),
         ("anti_transpose", lambda x: np.rot90(x, 2).T)]


def _size_story(a, b, lex):
    """How a differently sized output relates to its input."""
    out = []
    (H, W), (h, w) = a.shape, b.shape
    if h % H == 0 and w % W == 0:
        kh, kw = h // H, w // W
        if np.array_equal(np.kron(a, np.ones((kh, kw), dtype=int)), b):
            out.append(f"output = input scaled x{kh}x{kw} (each cell becomes a {kh}x{kw} block)")
        elif np.array_equal(np.tile(a, (kh, kw)), b):
            out.append(f"output = input tiled {kh}x{kw}")
        else:
            out.append(f"output is {kh}x{kw} input-sized blocks (not a plain tile/scale)")
    if H % h == 0 and W % w == 0 and (H, W) != (h, w):
        kh, kw = H // h, W // w
        if all(np.array_equal(b, a[r * h:(r + 1) * h, c * w:(c + 1) * w]) for r in range(kh) for c in range(kw)):
            out.append(f"input = output tiled {kh}x{kw}")
        elif np.array_equal(a[::kh, ::kw], b):
            out.append(f"output = input downscaled by {kh}x{kw}")
    spots = _find(b, a)
    if spots:
        out.append(f"output = input crop at (row, col) {spots[0]}" + (f" (+{len(spots) - 1} more spots)" if len(spots) > 1 else ""))
    else:
        for name, f in _GEOM[1:]:
            s2 = _find(f(b), a)
            if s2:
                out.append(f"output = {name} of the input crop at {s2[0]}")
                break
    ca = _encode(a, lex)
    for p in ca["placed"]:
        r0, c0 = p["at"]
        ph, pw = len(lex.entries[p["sym"]]["patch"]), len(lex.entries[p["sym"]]["patch"][0])
        if (ph, pw) == (h, w) and np.array_equal(a[r0:r0 + h, c0:c0 + w], b):
            out.append(f"output = bounding box of input object {p['sym']} @ {p['at']}")
            break
    return out


def changes(i, b=None, pairs=None, tests=None, max_lines=24):
    """What happens from train[i] input to its output (or from grid i to grid b). Print it."""
    lex = _task_lex(pairs, tests)
    if b is None:
        src = train if pairs is None else pairs    # noqa: F821
        a, b, head = _arr(src[i][0]), _arr(src[i][1]), f"Example {i + 1} (train[{i}]): "
    else:
        a, b, head = _arr(i), _arr(b), ""
    lines = [f"{head}input {a.shape[0]}x{a.shape[1]} -> output {b.shape[0]}x{b.shape[1]}"]
    for name, f in _GEOM[1:]:
        if f(a).shape == b.shape and np.array_equal(f(a), b):
            lines.append(f"output = {name}(input) exactly")
    if a.shape != b.shape:
        lines += _size_story(a, b, lex) or ["no simple size relation found"]
        ca, cb = _encode(a, lex), _encode(b, lex)
        sa, sb = Counter(p["sym"] for p in ca["placed"]), Counter(p["sym"] for p in cb["placed"])
        common = sorted(set(sa) & set(sb))
        lines.append(f"objects: input {sum(sa.values())}, output {sum(sb.values())}; pictures in both: "
                     + (", ".join(f"{s}(in x{sa[s]}, out x{sb[s]})" for s in common[:12]) or "none"))
        return "\n".join(lines)
    diff_mask = a != b
    n = int(diff_mask.sum())
    trans = Counter((int(x), int(y)) for x, y in zip(a[diff_mask], b[diff_mask]))
    lines.append(f"{n} of {a.size} cells change"
                 + (": " + ", ".join(f"{x}->{y} x{k}" for (x, y), k in trans.most_common(10)) if n else ""))
    if n:
        ys, xs = np.nonzero(diff_mask)
        lines.append(f"changed cells lie in rows {ys.min()}-{ys.max()}, cols {xs.min()}-{xs.max()}")
    ev = _object_events(_encode(a, lex), _encode(b, lex))
    text = [f"{s} moved {l}->{r} (d_row {r[0] - l[0]:+d}, d_col {r[1] - l[1]:+d})" for s, l, r in ev["moved"]]
    text += [f"{s0} became {s1} @ {at}" for s0, s1, at in ev["became"]]
    text += [f"{s} appeared @ {r}" for s, r in ev["appeared"]]
    text += [f"{s} disappeared from {l}" for s, l in ev["gone"]]
    lines.append(f"objects unchanged: {ev['kept']}; events: {len(text)}")
    lines += ["  " + t for t in text[:max_lines]]
    if len(text) > max_lines:
        lines.append(f"  ... +{len(text) - max_lines} more events")
    return "\n".join(lines)


def _all(xs):
    xs = list(xs)
    return bool(xs) and all(xs)


def rules(pairs=None, tests=None):
    """Facts that hold on EVERY train pair. Print it. Each line is measured, not guessed."""
    if pairs is None:
        pairs, tests = train, test_inputs          # noqa: F821
    lex = _task_lex(pairs, tests)
    P = [(_arr(a), _arr(b)) for a, b in pairs]
    T = [_arr(t) for t in (tests or [])]
    m = len(P)
    facts = []
    same = [a.shape == b.shape for a, b in P]
    if _all(same):
        facts.append("size: output has the same size as the input")
    elif len({b.shape for _, b in P}) == 1:
        facts.append(f"size: output is always {P[0][1].shape[0]}x{P[0][1].shape[1]}")
    if not _all(same):
        def nice(r):                               # k or 1/k: a scale, not a coincidence
            return r >= 1 and r == int(r) or r < 1 and (1 / r) == int(round(1 / r))
        ratios = {(b.shape[0] / a.shape[0], b.shape[1] / a.shape[1]) for a, b in P}
        rh, rw = next(iter(ratios))
        if len(ratios) == 1 and nice(rh) and nice(rw):
            facts.append(f"size: output = input size x ({rh:g}, {rw:g})")
        for axis, word in ((0, "height"), (1, "width")):
            if _all(a.shape[axis] == b.shape[axis] for a, b in P):
                facts.append(f"size: output keeps the input's {word}")
    if not _all(same):
        stories = [_size_story(a, b, lex) for a, b in P]
        for kind in ("output = input scaled", "output = input tiled", "output = input downscaled",
                     "input = output tiled", "output = input crop", "output = bounding box of input object"):
            hits = [next((s for s in st if s.startswith(kind)), None) for st in stories]
            if _all(h is not None for h in hits):
                facts.append(f"size: {hits[0]}" if len(set(hits)) == 1
                             else f"size: in every pair {kind} (details differ: see changes(i))")
        if _all(any("of the input crop" in s for s in st) for st in stories):
            facts.append("size: in every pair the output is a rotated/mirrored crop of the input")
    for name, f in _GEOM[1:]:
        if _all(f(a).shape == b.shape and np.array_equal(f(a), b) for a, b in P):
            facts.append(f"geometry: output = {name}(input) in every pair -- try it on the test input")
    pin = [set(np.unique(a).tolist()) for a, _ in P]
    pout = [set(np.unique(b).tolist()) for _, b in P]
    if _all(o <= i for i, o in zip(pin, pout)):
        facts.append("colours: the output uses only colours present in its input")
    new = set.intersection(*[o - i for i, o in zip(pin, pout)]) if m else set()
    if new:
        facts.append(f"colours: colour(s) {sorted(new)} are added in every pair")
    if _all(same):
        maps, ok = {}, True
        for a, b in P:
            for x, y in zip(a[a != b].tolist(), b[a != b].tolist()):
                if maps.setdefault(x, y) != y:
                    ok = False
        if ok and maps:
            facts.append("colours: every changed cell follows one map " + str(dict(sorted(maps.items())))
                         + " (but not every cell of those colours need change)")
        bgs = [_bg(a) for a, _ in P]
        if _all((a[a != b] == bg).all() for (a, b), bg in zip(P, bgs)):
            facts.append("cells: only background cells change (things are drawn/added, nothing is erased)")
        elif _all((b[a != b] == bg).all() for (a, b), bg in zip(P, bgs)):
            facts.append("cells: changed cells become background (things are erased only)")
        elif _all((a[a != b] != bg).all() for (a, b), bg in zip(P, bgs)):
            facts.append("cells: only non-background cells change (existing things are recoloured)")
        if _all((a != b).sum() == 0 for a, b in P):
            facts.append("cells: output equals input (check the test input instead)")
        evs = [_object_events(_encode(a, lex), _encode(b, lex)) for a, b in P]
        if _all(not e["appeared"] and not e["gone"] and not e["became"] and e["moved"] for e in evs):
            facts.append("objects: every change is an object moving (same pictures, new places)")
        if _all(not e["moved"] and not e["appeared"] and not e["gone"] and e["became"] for e in evs):
            facts.append("objects: objects stay in place and turn into other pictures (recolour/reshape)")
        if _all(not e["moved"] and not e["gone"] and not e["became"] and e["appeared"] for e in evs):
            facts.append("objects: input objects stay; new objects appear")
    for name, f in (("left-right", np.fliplr), ("up-down", np.flipud)):
        if _all(np.array_equal(b, f(b)) for _, b in P) and not _all(np.array_equal(a, f(a)) for a, _ in P):
            facts.append(f"symmetry: every output is {name} symmetric (inputs are not)")
    counts = [(len(_encode(a, lex)["placed"]), len(_encode(b, lex)["placed"])) for a, b in P]
    if _all(x == y for x, y in counts):
        facts.append("objects: output has as many objects as its input")
    elif _all(y == 1 for _, y in counts):
        facts.append("objects: output is a single object")
    if T:
        tin = set().union(*[set(np.unique(t).tolist()) for t in T])
        unseen = tin - set().union(*pin)
        if unseen:
            facts.append(f"test: test input uses colour(s) {sorted(unseen)} never seen in train inputs")
        big = max(max(a.shape) for a, _ in P)
        if any(max(t.shape) > big for t in T):
            facts.append("test: test input is larger than every train input -- do not hard-code sizes")
    head = f"RULES measured on all {m} train pairs (each line holds in every pair):"
    return "\n".join([head] + ["  " + f for f in facts] if facts else [head, "  (no simple regularity found)"])
