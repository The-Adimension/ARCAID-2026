%%writefile /tmp/my_agent.py
"""ARC Prize 2026 — ARC-AGI-3 agent (offline, one-file).

Compiles two research loops into deterministic search over a world-model DSL:

  habanwer/autoresearch-MIL
    GroundConfig          ~ ground.json   (immutable, human-owned)
    WorldModel            ~ train.py / model.json  (mutable program)
    Memory                ~ sessions/memory.md + results.tsv (append-only)
    MyAgent._research     ~ git-style ratchet (keep iff metric improved)

  The-Adimension/Agent-ProSAT
    WorldModel            ~ prosat.py     (the only mutable solver)
    Assessor              ~ assess.py     (twin-blind verifier)
    MyAgent._research     ~ agent.py commit rule
    Planner traces        ~ short re-executable action keys, not free-form CoT

Kaggle inlines this file only. No network. Stdlib (+ optional numpy grids).
"""
from __future__ import annotations

import copy
import hashlib
import logging
import random
import time
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Optional

try:
    from arcengine import FrameData, GameAction, GameState
    from agents.agent import Agent
except ImportError:  # self-check without the framework on sys.path
    from enum import Enum

    class GameState(str, Enum):
        NOT_PLAYED = "NOT_PLAYED"
        NOT_FINISHED = "NOT_FINISHED"
        WIN = "WIN"
        GAME_OVER = "GAME_OVER"

    class GameAction(Enum):
        RESET = 0
        ACTION1 = 1
        ACTION2 = 2
        ACTION3 = 3
        ACTION4 = 4
        ACTION5 = 5
        ACTION6 = 6
        ACTION7 = 7

        def is_complex(self) -> bool:
            return self is GameAction.ACTION6

        def is_simple(self) -> bool:
            return not self.is_complex()

        def set_data(self, data: dict[str, Any]) -> dict[str, Any]:
            self.action_data = data  # type: ignore[attr-defined]
            return data

        @classmethod
        def from_id(cls, action_id: int) -> "GameAction":
            return cls(action_id)

    class FrameData:  # minimal stub
        def __init__(self, **kw: Any) -> None:
            self.frame = kw.get("frame", [])
            self.state = kw.get("state", GameState.NOT_PLAYED)
            self.levels_completed = kw.get("levels_completed", 0)
            self.win_levels = kw.get("win_levels", 0)
            self.available_actions = kw.get("available_actions", [])
            self.game_id = kw.get("game_id", "")
            self.guid = kw.get("guid")
            self.full_reset = kw.get("full_reset", False)

    class Agent:
        MAX_ACTIONS = 80

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.game_id = kwargs.get("game_id", "toy")
            self.action_counter = 0
            self.frames: list = []
            self.agent_name = kwargs.get("agent_name", "MyAgent")

        @property
        def name(self) -> str:
            return "agent"


logger = logging.getLogger("MyAgent")

# ─────────────────────────────────────────────────────────────────────────────
# A. Immutable ground  (autoresearch-MIL ground.json analog)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class GroundConfig:
    ACTION_BUDGET_PER_GAME: int = 1200
    EXPLORE_BUDGET_PER_LEVEL: int = 40
    PLAN_HORIZON: int = 40
    MAX_MODEL_CANDIDATES: int = 24
    MAX_MEMORY_CHARS: int = 8000
    GRID: int = 64
    COLORS: int = 16


GROUND = GroundConfig()

# Knob panel for scripts/lab.py. Human-owned like GROUND — the ratchet never
# touches it — but unlike GROUND it is meant to be swept. Every default here
# reproduces the shipped agent exactly, so an empty variant is the baseline.
TUNE: dict[str, Any] = {
    "explore_budget": GROUND.EXPLORE_BUDGET_PER_LEVEL,
    "plan_horizon": GROUND.PLAN_HORIZON,
    "max_candidates": GROUND.MAX_MODEL_CANDIDATES,
    "research_max_gap": 32,   # 1 == research every action (pre-backoff behaviour)
    "research_ms": 30,        # per-round candidate budget
    "noise_min": 3,           # observations before a row can be called HUD
    "noise_frac": 0.6,        # fraction of observations it must be dirty in
    "mask_cap": 16,           # never mask more rows/cols than this
    "max_shift": 16,          # largest per-action translation we will fit
    "wall_hits": 2,           # bumps before a colour is suspected of being wall
    # Frontier priority. Measured on ls20: switch-first reaches level 1 at
    # action 34 vs 84 for door-first (scripts/lab.py, 2026-09-07). A switch
    # is the scarce thing on a state-machine level; unexplored ground keeps.
    "tiers": ("switch", "door", "new"),
    # ACTION6 targets per frame. Swept over {6,12,24,48,96,128,256} on all 25
    # public games: 24 clears 5 of them, every other value 3 or 4. Too few
    # never reaches the control that matters; too many bury it in a tail the
    # explorer never works through. (scripts/lab.py, 2026-09-07)
    "avoid_fatal": True,      # refuse to re-walk an edge that has killed us
    "click_cap": 24,
    "consume_hits": 2,        # touches before a colour counts as collectable
    "goal_min_obs": 6,        # observations before the goal channel may fire
    # Dead-signature (Reki, Milestone #1 2nd place): an object class -- colour,
    # area, bbox -- that has been clicked `dead_clicks` times without changing
    # the masked grid is dropped from the click targets. 0 disables. Measured
    # before the patch: lp85 spent 339 of 398 clicks on 14 classes that never
    # did anything; ft09 spent all 398 on 9 such classes. At the 1200-action
    # budget {0,1,2} gives 7/8/8 levels; 1 beats 2 on `first` (275 vs 317) and
    # ties it on the hold half. vc33 is the first public game to finish a
    # second level. (scripts/lab.py --suite deep, 2026-09-08)
    "dead_clicks": 1,
    "dead_scope": "level",    # "level": forget dead classes on a new level; "game": keep
    "dead_coarse": False,     # bucket area/bbox by log2 so a 40-long line and a 44-long one are one class
    "dead_epoch_clear": False,  # a world change (switch, door) forgets dead classes, like walls
    # Effect-first clicking, lifted from the local LLM tests (2026-09-11): on
    # vc33 Qwen3-14B cleared level 1 in 19 actions (this agent: 366) by clicking
    # the two objects that changed the most pixels, over and over. 0 = off;
    # 1 = greedy, at every new state click the class with the largest mean
    # masked change; 2 = scan every visible class once first, then exploit.
    # At 1200 actions on 25 public games: off 8 levels, greedy 7 (loses tn36,
    # though lp85 falls in 16 actions vs 117), scan 9 (sc25 cleared for the
    # first time; tn36 in 340 vs 1048). Hold ties on levels. (lab, 2026-09-11)
    "click_effect": 2,
    # Outcome head, separate from dynamics: what the winning transition touched
    # (a colour walked onto, an object class clicked) is a prior for the next
    # level. Only ever learned from a levels_completed tick, never from colour
    # counts. "win" must be in `tiers` for the navigator to use it.
    "win_prior": True,
    # Principle P7 (memory/principles.md): anchor the player on the patch of its
    # own colours that has its size and sits nearest where the measured step
    # puts it, instead of re-fitting its outline each frame. A player sprite with
    # an inner pixel that changes (tu93) or a ghost copy (g50t) made the outline
    # fit wobble by a pixel, and every walk built on it broke.
    "blob_anchor": True,
    # Retrodiction gate (Retrodict 99.9%, Tycho, Twin): a world model may only
    # plan live actions if it replays the recorded transitions at this ratio.
    "plan_min_ratio": 0.75,
}

_STD_MOVE: dict[int, tuple[int, int]] = {
    1: (0, -1), 2: (0, 1), 3: (-1, 0), 4: (1, 0),
}
_MOVE_VARIANTS: tuple[dict[int, tuple[int, int]], ...] = (
    dict(_STD_MOVE),
    {1: (0, 1), 2: (0, -1), 3: (-1, 0), 4: (1, 0)},
    {1: (0, -1), 2: (0, 1), 3: (1, 0), 4: (-1, 0)},
    {1: (-1, 0), 2: (1, 0), 3: (0, -1), 4: (0, 1)},
    {1: (0, 1), 2: (0, -1), 3: (1, 0), 4: (-1, 0)},
)
_PEEK_SLOTS = ("_oracle", "_future", "_peek", "_answer", "oracle", "_cache")
_N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


# ─────────────────────────────────────────────────────────────────────────────
# Grid helpers (stdlib, bounds-checked, any H×W — 64 is a default not a law)
# ─────────────────────────────────────────────────────────────────────────────

def to_tuple(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(c) for c in row) for row in grid)


def copy_grid(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def histogram(grid: list[list[int]]) -> Counter:
    h: Counter = Counter()
    for row in grid:
        h.update(int(c) for c in row)
    return h


def modal_color(grid: list[list[int]]) -> int:
    hist = histogram(grid)
    return hist.most_common(1)[0][0] if hist else 0


def diff(a: list[list[int]], b: list[list[int]]) -> list[tuple[int, int, int, int]]:
    out: list[tuple[int, int, int, int]] = []
    for y, (ra, rb) in enumerate(zip(a, b)):
        for x, (ca, cb) in enumerate(zip(ra, rb)):
            if ca != cb:
                out.append((x, y, int(ca), int(cb)))
    return out


def blobs(grid: list[list[int]]) -> list[dict[str, Any]]:
    """4-connected same-color components."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = [[False] * w for _ in range(h)]
    out: list[dict[str, Any]] = []
    for y in range(h):
        for x in range(w):
            if seen[y][x]:
                continue
            col = int(grid[y][x])
            stack = [(x, y)]
            seen[y][x] = True
            cells: list[tuple[int, int]] = []
            while stack:
                cx, cy = stack.pop()
                cells.append((cx, cy))
                for dx, dy in _N4:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and int(grid[ny][nx]) == col:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            xs = [p[0] for p in cells]
            ys = [p[1] for p in cells]
            out.append({
                "color": col,
                "cells": cells,
                "bbox": (min(xs), min(ys), max(xs), max(ys)),
                "area": len(cells),
            })
    return out


def blob_at(grid: list[list[int]], x: int, y: int) -> tuple[int, int, int, int]:
    """Class signature of the object under (x, y): (colour, area, bbox w, bbox h).

    A local flood fill, so a click costs one object and not the whole board.
    The signature is what a dead-click record is keyed on: the same button
    drawn in the same place on the next level has the same signature, while
    the exact cell clicked does not survive even a small redraw.
    """
    h = len(grid)
    w = len(grid[0]) if h else 0
    if not (0 <= y < h and 0 <= x < w):
        return (-1, 0, 0, 0)
    col = int(grid[y][x])
    seen = {(x, y)}
    stack = [(x, y)]
    minx = maxx = x
    miny = maxy = y
    while stack:
        cx, cy = stack.pop()
        for dx, dy in _N4:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen and int(grid[ny][nx]) == col:
                seen.add((nx, ny))
                stack.append((nx, ny))
                minx, maxx = min(minx, nx), max(maxx, nx)
                miny, maxy = min(miny, ny), max(maxy, ny)
    return click_sig(col, len(seen), maxx - minx + 1, maxy - miny + 1)


def click_sig(color: int, area: int, bw: int, bh: int) -> tuple[int, int, int, int]:
    """The class key a dead-click record is filed under.

    Exact by default. With `dead_coarse` the three sizes are log2-bucketed:
    on vc33 the board is ruled with one-pixel lines of every length, and an
    exact key makes each length a class that has to die on its own.
    """
    if not TUNE["dead_coarse"]:
        return (color, area, bw, bh)
    return (color, area.bit_length(), bw.bit_length(), bh.bit_length())


def cells_of(grid: list[list[int]], color: int) -> list[tuple[int, int]]:
    return [
        (x, y)
        for y, row in enumerate(grid)
        for x, v in enumerate(row)
        if int(v) == color
    ]


def largest_blob_cells(grid: list[list[int]], color: int) -> list[tuple[int, int]]:
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen: set[tuple[int, int]] = set()
    best: list[tuple[int, int]] = []
    for y in range(h):
        for x in range(w):
            if int(grid[y][x]) != color or (x, y) in seen:
                continue
            stack = [(x, y)]
            seen.add((x, y))
            comp = [(x, y)]
            while stack:
                cx, cy = stack.pop()
                for dx, dy in _N4:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen and int(grid[ny][nx]) == color:
                        seen.add((nx, ny))
                        stack.append((nx, ny))
                        comp.append((nx, ny))
            if len(comp) > len(best):
                best = comp
    return best


def apply_translation(
    grid: list[list[int]],
    color_or_blob: Any,
    dx: int,
    dy: int,
    solids: frozenset[int] | set[int],
) -> Optional[list[list[int]]]:
    """Move a color (all cells) or a blob. None if OOB or solid collision."""
    g = copy_grid(grid)
    h = len(g)
    w = len(g[0]) if h else 0
    if not h or not w:
        return None
    if isinstance(color_or_blob, int):
        moving = cells_of(g, color_or_blob)
        color = color_or_blob
    elif isinstance(color_or_blob, dict):
        moving = list(color_or_blob.get("cells") or [])
        color = int(color_or_blob.get("color", 0))
    else:
        moving = list(color_or_blob or [])
        color = int(g[moving[0][1]][moving[0][0]]) if moving else 0
    if not moving:
        return None
    mset = set(moving)
    dests: list[tuple[int, int]] = []
    solid_set = solids if isinstance(solids, (set, frozenset)) else set(solids)
    for x, y in moving:
        nx, ny = x + dx, y + dy
        if nx < 0 or ny < 0 or nx >= w or ny >= h:
            return None
        if (nx, ny) not in mset and int(g[ny][nx]) in solid_set:
            return None
        dests.append((nx, ny))
    bg = 0
    hist = histogram(g)
    for c, _n in hist.most_common():
        if c != color:
            bg = int(c)
            break
    for x, y in moving:
        g[y][x] = bg
    for nx, ny in dests:
        g[ny][nx] = color
    return g


def hist_dist(a: Counter, b: Counter) -> int:
    return sum(abs(a[k] - b[k]) for k in set(a) | set(b))


def color_stats(grid: list[list[int]]) -> dict[int, tuple[int, int, int]]:
    """colour -> (count, sum_x, sum_y) in a single sweep.

    `cells_of` per colour per transition was 48% of total agent time: every call
    walked all 4096 cells to find one colour. One sweep answers every colour.
    """
    out: dict[int, list[int]] = {}
    for y, row in enumerate(grid):
        for x, v in enumerate(row):
            c = int(v)
            slot = out.get(c)
            if slot is None:
                out[c] = [1, x, y]
            else:
                slot[0] += 1
                slot[1] += x
                slot[2] += y
    return {c: (v[0], v[1], v[2]) for c, v in out.items()}


def _centroid_of(stats: dict[int, tuple[int, int, int]], color: int) -> Optional[tuple[float, float]]:
    st = stats.get(color)
    if not st or not st[0]:
        return None
    return (st[1] / st[0], st[2] / st[0])


def _centroid(grid: list[list[int]], color: int) -> Optional[tuple[float, float]]:
    cells = cells_of(grid, color)
    if not cells:
        return None
    n = len(cells)
    return (sum(p[0] for p in cells) / n, sum(p[1] for p in cells) / n)


def layout_dist(a: list[list[int]], b: list[list[int]]) -> int:
    """Histogram plus per-color centroid L1 — positions, not just counts."""
    ha, hb = histogram(a), histogram(b)
    d = hist_dist(ha, hb)
    for c in set(ha) | set(hb):
        ca, cb = _centroid(a, c), _centroid(b, c)
        if ca and cb:
            d += int(abs(ca[0] - cb[0]) + abs(ca[1] - cb[1]))
        elif ca or cb:
            d += 32
    return d


def extract_grid(frame: Any) -> Optional[list[list[int]]]:
    """Last settled layer of latest_frame.frame (3D animation or 2D grid)."""
    fr = getattr(frame, "frame", None)
    if fr is None:
        return None
    if hasattr(fr, "tolist"):
        fr = fr.tolist()
    if not fr:
        return None
    first = fr[0]
    if hasattr(first, "tolist"):
        first = first.tolist()
    if first and isinstance(first[0], (list, tuple)):
        layer = fr[-1]
    else:
        layer = fr
    if hasattr(layer, "tolist"):
        layer = layer.tolist()
    if not layer:
        return None
    try:
        return [[int(c) for c in row] for row in layer]
    except (TypeError, ValueError):
        return None


def state_name(frame: Any) -> str:
    s = getattr(frame, "state", None)
    if s is None:
        return ""
    return s.name if hasattr(s, "name") else str(s)


def legal_ids(frame: Any) -> list[int]:
    raw = getattr(frame, "available_actions", None) or []
    ids: list[int] = []
    for a in raw:
        try:
            ids.append(int(a.value) if hasattr(a, "value") else int(a))
        except (TypeError, ValueError):
            continue
    ids = [i for i in ids if i != 0]
    return ids or [1, 2, 3, 4, 5, 6, 7]


# ─────────────────────────────────────────────────────────────────────────────
# ActionKey helpers  (serialize GameAction including ACTION6 coords)
# ─────────────────────────────────────────────────────────────────────────────

def make_key(aid: int, x: int | None = None, y: int | None = None) -> str:
    if int(aid) == 6:
        return f"6:{int(x or 0)},{int(y or 0)}"
    return str(int(aid))


def parse_key(action: Any) -> tuple[int, int | None, int | None]:
    if isinstance(action, str):
        if action.startswith("6:"):
            parts = action.split(":", 1)[1].split(",")
            return 6, int(parts[0]), int(parts[1])
        return int(action), None, None
    aid = int(getattr(action, "value", action))
    if aid != 6:
        return aid, None, None
    data = getattr(action, "action_data", None)
    if isinstance(data, dict):
        return 6, int(data.get("x", 0)), int(data.get("y", 0))
    if data is not None:
        return 6, int(getattr(data, "x", 0)), int(getattr(data, "y", 0))
    return 6, 0, 0


def clamp_xy(x: int, y: int) -> tuple[int, int]:
    return max(0, min(63, int(x))), max(0, min(63, int(y)))


def distinctive_cells(grid: list[list[int]]) -> list[tuple[int, int]]:
    """Up to 6 clicks: centroids of 3 rarest non-bg colors + largest-blob corners."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    if not h or not w:
        return [(0, 0)]
    bg = modal_color(grid)
    hist = histogram(grid)
    rare = [c for c, _n in sorted(hist.items(), key=lambda kv: (kv[1], kv[0])) if c != bg][:3]
    out: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()

    def add(x: int, y: int) -> None:
        x = max(0, min(w - 1, int(x)))
        y = max(0, min(h - 1, int(y)))
        p = (x, y)
        if p not in seen:
            seen.add(p)
            out.append(p)

    for col in rare:
        cells = cells_of(grid, col)
        if not cells:
            continue
        add(sum(p[0] for p in cells) // len(cells), sum(p[1] for p in cells) // len(cells))
    non_bg = [b for b in blobs(grid) if b["color"] != bg]
    if non_bg:
        big = max(non_bg, key=lambda b: b["area"])
        x0, y0, x1, y1 = big["bbox"]
        for p in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
            add(p[0], p[1])
    if not out:
        add(w // 2, h // 2)
    return out[:6]


# ─────────────────────────────────────────────────────────────────────────────
# B0. Perception — Tracker  (autoresearch-MIL prepare.py analog)
#     Deterministic and human-owned; the ratchet never edits it. It answers the
#     three questions the world-model DSL cannot ask: which pixels are HUD noise,
#     which object the buttons actually move, and where that object may stand.
# ─────────────────────────────────────────────────────────────────────────────

MAX_SHIFT = 16


def digest(grid: list[list[int]]) -> str:
    return hashlib.md5(
        bytes((int(v) + 2) & 0xFF for row in grid for v in row)
    ).hexdigest()[:16]


def components(points: set) -> list[list[tuple[int, int]]]:
    """8-connected clusters of a cell set, largest first."""
    seen: set = set()
    out: list[list[tuple[int, int]]] = []
    for p in points:
        if p in seen:
            continue
        stack = [p]
        seen.add(p)
        comp: list[tuple[int, int]] = []
        while stack:
            cx, cy = stack.pop()
            comp.append((cx, cy))
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (cx + dx, cy + dy)
                    if q in points and q not in seen:
                        seen.add(q)
                        stack.append(q)
        out.append(comp)
    out.sort(key=len, reverse=True)
    return out


def _fit_shift(
    g0: list[list[int]],
    g1: list[list[int]],
    box: tuple[int, int, int, int],
    max_shift: int,
) -> Optional[tuple]:
    """Inside `box`, find one colour set that translated rigidly."""
    x0, y0, x1, y1 = box
    sub0: dict[int, list] = defaultdict(list)
    sub1: dict[int, list] = defaultdict(list)
    for y in range(y0, y1 + 1):
        r0, r1 = g0[y], g1[y]
        for x in range(x0, x1 + 1):
            sub0[int(r0[x])].append((x, y))
            sub1[int(r1[x])].append((x, y))
    if not sub0:
        return None
    area = (x1 - x0 + 1) * (y1 - y0 + 1)
    bg = max(sub0, key=lambda c: len(sub0[c]))
    votes: dict[tuple[int, int], list] = {}
    for col, a_cells in sub0.items():
        if col == bg or not a_cells or len(a_cells) * 2 > area:
            continue
        b_cells = sub1.get(col)
        if not b_cells or len(b_cells) != len(a_cells):
            continue
        dx = min(p[0] for p in b_cells) - min(p[0] for p in a_cells)
        dy = min(p[1] for p in b_cells) - min(p[1] for p in a_cells)
        if (dx, dy) == (0, 0) or abs(dx) > max_shift or abs(dy) > max_shift:
            continue
        if {(x + dx, y + dy) for x, y in a_cells} != set(b_cells):
            continue
        slot = votes.setdefault((dx, dy), [0, []])
        slot[0] += len(a_cells)
        slot[1].append(col)
    if not votes:
        return None
    (dx, dy), slot = max(votes.items(), key=lambda kv: kv[1][0])
    colors = frozenset(slot[1])
    old = [p for col in colors for p in sub0[col]]
    return dx, dy, colors, old, [(x + dx, y + dy) for x, y in old]


def detect_move(
    g0: list[list[int]], g1: list[list[int]], max_shift: int = 0
) -> Optional[tuple]:
    """Rigid translation of a small object between two frames, or None.

    Returns (dx, dy, colours, old_cells, new_cells). The biggest connected patch
    of changed pixels is tried first, so a status bar on the far side of the
    screen cannot drag the bounding box across unrelated sprites.
    """
    max_shift = max_shift or TUNE["max_shift"]
    h = len(g1)
    w = len(g1[0]) if h else 0
    if not h or not w or len(g0) != h or len(g0[0]) != w:
        return None
    d = diff(g0, g1)
    if not d or len(d) * 3 > w * h:
        return None
    pts = {(x, y) for x, y, _a, _b in d}
    boxes: list[tuple[int, int, int, int]] = []
    comps = components(pts)
    if comps:
        pad = max_shift // 2
        xs = [p[0] for p in comps[0]]
        ys = [p[1] for p in comps[0]]
        boxes.append((max(0, min(xs) - pad), max(0, min(ys) - pad),
                      min(w - 1, max(xs) + pad), min(h - 1, max(ys) + pad)))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    full = (min(xs), min(ys), max(xs), max(ys))
    if full not in boxes:
        boxes.append(full)
    for box in boxes:
        res = _fit_shift(g0, g1, box, max_shift)
        if res is not None:
            return res
    return None


class Tracker:
    """Object-level perception: HUD mask, avatar, per-action deltas, walls.

    Nothing stored here is a hypothesis — every entry is something the agent
    literally observed. `WorldModel` stays the only mutable solver.
    """

    NOISE_MIN = 3
    NOISE_FRAC = 0.6
    MASK_CAP = 16

    def __init__(self) -> None:
        self.delta_votes: dict[int, Counter] = defaultdict(Counter)
        self.noise_rows: Counter = Counter()
        self.noise_cols: Counter = Counter()
        self.mask_rows: frozenset = frozenset()
        self.mask_cols: frozenset = frozenset()
        self.template: tuple = ()
        self.anchor: Optional[tuple[int, int]] = None
        self.colors: frozenset = frozenset()
        self.size: tuple[int, int] = (1, 1)
        self.edges: dict = {}
        self.blocked: set = set()
        self.seen: Counter = Counter()
        self.hit: Counter = Counter()
        self.walk: Counter = Counter()
        self.tried: set = set()
        self.epoch: int = 0
        self.stand: Counter = Counter()
        self.switches: Counter = Counter()
        self.blocked_at: set = set()
        self.retry: set = set()
        self.fatal: set = set()
        self.deaths: int = 0
        self.epoch_stood: set = set()
        self.occ_rows: set = set()
        self.occ_cols: set = set()
        # Goal channel: which colours vanish when we walk onto them.
        self.bg: int = 0
        self.consume: Counter = Counter()
        self.color_floor: dict[int, int] = {}
        # Dead-signature channel: object classes clicked without effect, and
        # classes that did something at least once (which are never dead).
        self.click_dead: Counter = Counter()
        self.click_live: Counter = Counter()
        # Effect size per class: masked pixels changed, summed, and click count.
        self.click_gain: Counter = Counter()
        self.click_n: Counter = Counter()
        # Outcome head: what the transition that finished a level touched.
        self.win_sigs: set = set()
        self.win_colors: set[int] = set()
        self.moves: int = 0
        self.n_obs: int = 0
        self._rescan_due: int = 0
        self.h: int = 0
        self.w: int = 0

    # ── masking ─────────────────────────────────────────────────────────────
    def mask_grid(self, grid: list[list[int]]) -> list[list[int]]:
        if not self.mask_rows and not self.mask_cols:
            return grid
        g = copy_grid(grid)
        for y in self.mask_rows:
            if 0 <= y < len(g):
                g[y] = [0] * len(g[y])
        for row in g:
            for x in self.mask_cols:
                if 0 <= x < len(row):
                    row[x] = 0
        return g

    def _refresh_mask(self) -> None:
        """A row that keeps changing in ways no object move explains is a HUD."""
        noise_min = TUNE["noise_min"]
        if self.moves < 2 or self.n_obs < noise_min:
            return
        floor = max(noise_min, int(TUNE["noise_frac"] * self.n_obs))
        rows = sorted(
            (y for y, n in self.noise_rows.items()
             if n >= floor and y not in self.occ_rows),
            key=lambda y: -self.noise_rows[y],
        )[: TUNE["mask_cap"]]
        cols = sorted(
            (x for x, n in self.noise_cols.items()
             if n >= floor and x not in self.occ_cols),
            key=lambda x: -self.noise_cols[x],
        )[: TUNE["mask_cap"]]
        if self.h and len(rows) * 4 > self.h:
            rows = rows[: self.h // 4]
        if self.w and len(cols) * 4 > self.w:
            cols = cols[: self.w // 4]
        self.mask_rows = frozenset(rows)
        self.mask_cols = frozenset(cols)

    def bump_epoch(self, g0: list[list[int]], g1: list[list[int]], explained: set) -> None:
        """A new epoch = the world itself changed, not just where we stand.

        Coverage cannot be keyed on a digest of the screen: the avatar occludes
        different terrain from every square, so such a digest changes with
        position and every square looks new forever. What is position-free is
        the *event* — pixels that moved, outside the HUD, that our own step does
        not account for. A switch flipped, a door opened, a life was lost.
        """
        novel = 0
        for x, y, _a, _b in diff(g0, g1):
            if (x, y) in explained or y in self.mask_rows or x in self.mask_cols:
                continue
            novel += 1
            if novel >= 2:
                self.epoch += 1
                # What we believed about walls was believed about a world that
                # no longer exists; a closed door may have just opened, so every
                # square that ever stopped us is worth one more push.
                self.blocked.clear()
                self.retry = set(self.blocked_at)
                self.epoch_stood.clear()
                if TUNE["dead_epoch_clear"]:
                    self.click_dead.clear()
                if self.anchor is not None:
                    self.switches[self.anchor] += 1
                return

    # ── avatar ──────────────────────────────────────────────────────────────
    def known_deltas(self) -> dict[int, tuple[int, int]]:
        out: dict[int, tuple[int, int]] = {}
        for aid, votes in self.delta_votes.items():
            if votes:
                out[aid] = votes.most_common(1)[0][0]
        return out

    def ready(self, ids: list[int]) -> bool:
        """Enough perception to steer: an avatar plus every legal arrow mapped."""
        if self.anchor is None or not self.template:
            return False
        simple = [i for i in ids if i in (1, 2, 3, 4)]
        if not simple:
            return False
        deltas = self.known_deltas()
        if any(i not in deltas for i in simple):
            return False
        return not (5 in ids and "5" not in self.tried)

    def _match(self, grid: list[list[int]], ax: int, ay: int) -> bool:
        h = len(grid)
        w = len(grid[0]) if h else 0
        for rx, ry, c in self.template:
            x, y = ax + rx, ay + ry
            if x < 0 or y < 0 or x >= w or y >= h or int(grid[y][x]) != c:
                return False
        return True

    def _match_shape(self, grid: list[list[int]], ax: int, ay: int) -> bool:
        """Same silhouette under a consistent recolouring — sprites repaint."""
        h = len(grid)
        w = len(grid[0]) if h else 0
        remap: dict[int, int] = {}
        for rx, ry, c in self.template:
            x, y = ax + rx, ay + ry
            if x < 0 or y < 0 or x >= w or y >= h:
                return False
            v = int(grid[y][x])
            if remap.setdefault(c, v) != v:
                return False
        return len(set(remap.values())) == len(remap)

    def _player_blob(self, grid: list[list[int]], near: tuple[int, int]) -> Optional[tuple[int, int]]:
        """Top-left of the player-coloured patch of the player's size nearest `near`.

        Robust where outline matching is not: an inner pixel that changes colour
        leaves the patch's bounding box alone, and a ghost copy elsewhere loses on
        distance. None when no patch of exactly the player's size is in reach.
        """
        cols = {c for _rx, _ry, c in self.template}
        h = len(grid)
        w = len(grid[0]) if h else 0
        if not cols or not h or not w:
            return None
        sw, sh = self.size
        reach = TUNE["max_shift"] + max(sw, sh)
        x0, x1 = max(0, near[0] - reach), min(w - 1, near[0] + sw + reach)
        y0, y1 = max(0, near[1] - reach), min(h - 1, near[1] + sh + reach)
        seen: set = set()
        best, best_d = None, None
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if (x, y) in seen or int(grid[y][x]) not in cols:
                    continue
                stack, cells = [(x, y)], []
                seen.add((x, y))
                while stack:
                    cx, cy = stack.pop()
                    cells.append((cx, cy))
                    for dx, dy in _N4:
                        nx, ny = cx + dx, cy + dy
                        if (x0 <= nx <= x1 and y0 <= ny <= y1 and (nx, ny) not in seen
                                and int(grid[ny][nx]) in cols):
                            seen.add((nx, ny))
                            stack.append((nx, ny))
                bx, by = min(c[0] for c in cells), min(c[1] for c in cells)
                if (max(c[0] for c in cells) - bx + 1, max(c[1] for c in cells) - by + 1) != (sw, sh):
                    continue
                d = abs(bx - near[0]) + abs(by - near[1])
                if best is None or d < best_d:
                    best, best_d = (bx, by), d
        return best

    def locate(self, grid: list[list[int]]) -> Optional[tuple[int, int]]:
        if not self.template:
            return None
        if TUNE["blob_anchor"] and self.anchor is not None:
            found = self._player_blob(grid, self.anchor)
            if found is not None:
                return found
        h = len(grid)
        w = len(grid[0]) if h else 0
        if self.anchor and self._match(grid, *self.anchor):
            return self.anchor
        if self.anchor:
            for dx, dy in set(self.known_deltas().values()):
                p = (self.anchor[0] + dx, self.anchor[1] + dy)
                if self._match(grid, *p):
                    return p
        rx0, ry0, c0 = self.template[0]
        for y in range(h):
            row = grid[y]
            for x in range(w):
                if int(row[x]) != c0:
                    continue
                p = (x - rx0, y - ry0)
                if self._match(grid, *p):
                    return p
        # Recolour search is the expensive one (every cell, every template
        # pixel). A game where the avatar is simply not visible must not pay it
        # on every frame of a 1200-action budget.
        if self._rescan_due > 0:
            self._rescan_due -= 1
            return None
        self._rescan_due = 8
        for y in range(h):
            for x in range(w):
                p = (x - rx0, y - ry0)
                if self._match_shape(grid, *p):
                    return p
        return None

    def _adopt(self, grid: list[list[int]], colors: frozenset, cells: list) -> None:
        xs = [p[0] for p in cells]
        ys = [p[1] for p in cells]
        ax, ay = min(xs), min(ys)
        h = len(grid)
        w = len(grid[0]) if h else 0
        tmpl = [
            (x - ax, y - ay, int(grid[y][x]))
            for x, y in cells
            if 0 <= y < h and 0 <= x < w
        ]
        if not tmpl:
            return
        self.template = tuple(sorted(tmpl))
        self.colors = colors
        self.anchor = (ax, ay)
        self.size = (max(xs) - ax + 1, max(ys) - ay + 1)

    # ── geometry ────────────────────────────────────────────────────────────
    def in_bounds(self, anchor: tuple[int, int]) -> bool:
        sw, sh = self.size
        return (
            anchor[0] >= 0 and anchor[1] >= 0
            and anchor[0] + sw <= self.w and anchor[1] + sh <= self.h
        )

    def step_anchor(self, anchor: tuple[int, int], aid: int) -> Optional[tuple[int, int]]:
        seen = self.edges.get((anchor, aid))
        if seen is not None:
            return seen
        d = self.known_deltas().get(aid)
        if d is None:
            return None
        return (anchor[0] + d[0], anchor[1] + d[1])

    def cells_at(self, anchor: Optional[tuple[int, int]]) -> set:
        if anchor is None or not self.template:
            return set()
        return {(anchor[0] + rx, anchor[1] + ry) for rx, ry, _c in self.template}

    def _mark_occupied(self, anchor: Optional[tuple[int, int]]) -> None:
        for x, y in self.cells_at(anchor):
            self.occ_rows.add(y)
            self.occ_cols.add(x)

    def footprint(self, dst: tuple[int, int], src: tuple[int, int]) -> list[tuple[int, int]]:
        """Cells the avatar would newly cover moving src -> dst."""
        here = {(src[0] + rx, src[1] + ry) for rx, ry, _c in self.template}
        return [
            (dst[0] + rx, dst[1] + ry)
            for rx, ry, _c in self.template
            if (dst[0] + rx, dst[1] + ry) not in here
        ]

    def wall_colors(self) -> set[int]:
        """Colours that stopped us twice and never let us through.

        Avatar colours are excluded. When a sprite is clipped by a doorway its
        own body turns up in the destination footprint, and calling that a wall
        walls the agent in.
        """
        return {
            c for c, n in self.hit.items()
            if n >= TUNE["wall_hits"] and not self.walk.get(c) and c not in self.colors
        }

    def walkable(
        self, grid: list[list[int]], src: tuple[int, int], dst: tuple[int, int]
    ) -> bool:
        if not self.in_bounds(dst):
            return False
        walls = self.wall_colors()
        if not walls:
            return True
        h = len(grid)
        w = len(grid[0]) if h else 0
        for x, y in self.footprint(dst, src):
            if 0 <= y < h and 0 <= x < w and int(grid[y][x]) in walls:
                return False
        return True

    # ── learning ────────────────────────────────────────────────────────────
    def note_frame(self, grid: list[list[int]]) -> Optional[int]:
        self.h = len(grid)
        self.w = len(grid[0]) if self.h else 0
        if self.template:
            found = self.locate(grid)
            if found is not None:
                self.anchor = found
        if not self.template or self.anchor is None:
            return None
        self.seen[(self.epoch, self.anchor)] += 1
        self.stand[self.anchor] += 1
        self.epoch_stood.add(self.anchor)
        self.retry.discard(self.anchor)
        self._mark_occupied(self.anchor)
        return self.epoch

    def observe(self, g0: list[list[int]], akey: str, g1: list[list[int]]) -> None:
        self.h = len(g1)
        self.w = len(g1[0]) if self.h else 0
        self.n_obs += 1
        self.tried.add("6" if akey.startswith("6:") else akey)
        aid, _x, _y = parse_key(akey)
        before = self.anchor
        res = detect_move(g0, g1)
        explained: set = set()
        moved = False
        # P7: once we know what the player looks like, measure its step from its
        # own patch. "stayed" means it was blocked: nothing else that moved (a
        # ghost, a patrolling piece) may be mistaken for it.
        blob_state = None
        if TUNE["blob_anchor"] and self.template and before is not None and aid in (1, 2, 3, 4):
            d = self.known_deltas().get(aid)
            guess = (before[0] + d[0], before[1] + d[1]) if d else before
            blob = self._player_blob(g1, guess)
            if blob == before:
                blob_state = "stayed"
            elif blob is not None and max(abs(blob[0] - before[0]), abs(blob[1] - before[1])) <= TUNE["max_shift"]:
                blob_state = "moved"
                self.moves += 1
                moved = True
                self.delta_votes[aid][(blob[0] - before[0], blob[1] - before[1])] += 1
                self.anchor = blob
                explained = self.cells_at(before) | self.cells_at(blob)
        if blob_state is not None:
            pass
        elif res is not None:
            dx, dy, colors, old, new = res
            explained = set(old) | set(new)
            self.moves += 1
            moved = True
            if aid in (1, 2, 3, 4):
                self.delta_votes[aid][(dx, dy)] += 1
            if self.template and before is not None and len(new) < len(self.template):
                # Clipped sighting: a doorway hid part of the sprite. Trust the
                # measured shift instead of shrinking what we think we are.
                self.anchor = (before[0] + dx, before[1] + dy)
            else:
                self._adopt(g1, colors, new)
            explained |= self.cells_at(before) | self.cells_at(self.anchor)
        elif before is not None and self.template and not self._match(g1, *before):
            found = self.locate(g1)
            if found is not None:
                self.anchor = found
        self._mark_occupied(before)
        self._mark_occupied(self.anchor)
        self._learn_terrain(g0, aid, before)
        if aid == 6 and _x is not None and _y is not None:
            self._learn_click(g0, g1, _x, _y)
        if "goal" in TUNE["tiers"]:
            # REFUTED 2026-09-07 (see LAB.md): fires on only 2 of 8 sampled games
            # and converts to no levels on either. Kept behind the tier switch so
            # the negative result stays reproducible at zero cost when off.
            self._learn_consumables(g0, g1)
        if moved or len(diff(g0, g1)) * 20 < self.w * self.h:
            self._learn_noise(g0, g1, explained)
        self._refresh_mask()
        self.bump_epoch(g0, g1, explained)

    def _learn_click(self, g0: list[list[int]], g1: list[list[int]], x: int, y: int) -> None:
        """Did clicking this class of object change anything outside the HUD?

        Reki (Milestone #1, 2nd) reports this as the one heuristic that earned
        its keep without a GPU: stop clicking a class of object that never
        changes the frame. Measured here before the patch, lp85 spent 339 of
        398 clicks on fourteen such classes and ft09 all 398 on nine.
        """
        sig = blob_at(g0, x, y)
        changed = len(diff(self.mask_grid(g0), self.mask_grid(g1)))
        if changed == 0:
            self.click_dead[sig] += 1
        else:
            self.click_live[sig] += 1
        self.click_gain[sig] += changed
        self.click_n[sig] += 1

    def click_effect(self) -> dict:
        """Mean masked pixels changed per click, for every class clicked so far."""
        return {s: self.click_gain[s] / n for s, n in self.click_n.items() if n}

    def dead_sigs(self) -> frozenset:
        """Object classes not worth another click. Empty when the knob is 0."""
        need = TUNE["dead_clicks"]
        if not need:
            return frozenset()
        return frozenset(
            s for s, n in self.click_dead.items()
            if n >= need and not self.click_live.get(s)
        )

    def note_win(
        self, g0: list[list[int]], akey: str, anchor: Optional[tuple[int, int]]
    ) -> None:
        """The level just fell on this transition: remember what it touched.

        This is the outcome head, kept apart from `step`. Twin and Tycho both
        report that dynamics were the easy half and goal identification the
        failure mode that survived. Nothing here is inferred from colour
        counts; it is learned only from a `levels_completed` tick.
        """
        if not TUNE["win_prior"]:
            return
        aid, x, y = parse_key(akey)
        if aid == 6 and x is not None and y is not None:
            self.win_sigs.add(blob_at(g0, x, y))
            return
        if aid in (1, 2, 3, 4) and anchor is not None and self.template:
            d = self.known_deltas().get(aid)
            if d is None:
                return
            dst = (anchor[0] + d[0], anchor[1] + d[1])
            h = len(g0)
            w = len(g0[0]) if h else 0
            bg = modal_color(g0)
            for fx, fy in self.footprint(dst, anchor):
                if 0 <= fy < h and 0 <= fx < w:
                    c = int(g0[fy][fx])
                    if c != bg and c not in self.colors:
                        self.win_colors.add(c)

    def win_cells(self, grid: list[list[int]]) -> set:
        if not self.win_colors:
            return set()
        return {
            (x, y)
            for y, row in enumerate(grid)
            for x, v in enumerate(row)
            if int(v) in self.win_colors
        }

    def _learn_consumables(self, g0: list[list[int]], g1: list[list[int]]) -> None:
        """Which colours disappear when the avatar walks onto them.

        This is the goal that exists before any level has been finished. Frontier
        coverage produces motion and novelty but never converges: across the 25
        public games, 19 of them wander at high novelty and low stuck and finish
        nothing. "Collect the things" is the closest thing to a universal verb
        these games have, so it is worth inferring rather than exploring past.

        Two conditions, because either alone is wrong:

        * the vanished pixels lie under where the avatar now stands -- so this is
          something we touched, not something that moved on its own; and
        * the colour's global count set a new all-time low -- because the avatar
          *occludes* whatever it stands on, so plain floor loses pixels on every
          single step and would otherwise look exactly like treasure. Occlusion
          oscillates inside a band and stops setting records after a few moves.
          A collected item never comes back.
        """
        st1 = color_stats(g1)
        if not st1:
            return
        self.bg = max(st1.items(), key=lambda kv: (kv[1][0], -kv[0]))[0]
        here = self.cells_at(self.anchor)
        if not here:
            for c, (n, _sx, _sy) in st1.items():
                prev = self.color_floor.get(c)
                self.color_floor[c] = n if prev is None else min(prev, n)
            return
        gone: set[int] = set()
        for x, y, ca, cb in diff(g0, g1):
            if ca != cb and (x, y) in here and ca != self.bg and ca not in self.colors:
                gone.add(int(ca))
        for c, (n, _sx, _sy) in st1.items():
            prev = self.color_floor.get(c)
            if prev is None:
                self.color_floor[c] = n
            elif n < prev:
                self.color_floor[c] = n
                if c in gone:
                    self.consume[c] += 1

    def target_colors(self) -> set[int]:
        """Colours worth walking to. Empty until the evidence repeats."""
        if self.n_obs < TUNE["goal_min_obs"]:
            return set()
        need = TUNE["consume_hits"]
        return {
            c for c, n in self.consume.items()
            if n >= need and c != self.bg and c not in self.colors
        }

    def goal_cells(self, grid: list[list[int]]) -> set:
        cols = self.target_colors()
        if not cols:
            return set()
        return {
            (x, y)
            for y, row in enumerate(grid)
            for x, v in enumerate(row)
            if int(v) in cols
        }

    def _learn_terrain(
        self, g0: list[list[int]], aid: int, before: Optional[tuple[int, int]]
    ) -> None:
        if aid not in (1, 2, 3, 4) or before is None or not self.template:
            return
        h = len(g0)
        w = len(g0[0]) if h else 0
        after = self.anchor
        if after is not None and after != before:
            self.edges[(before, aid)] = after
            self.blocked.discard((before, aid))
            for x, y in self.footprint(after, before):
                if 0 <= y < h and 0 <= x < w:
                    self.walk[int(g0[y][x])] += 1
            return
        if after != before:
            return
        self.blocked.add((before, aid))
        self.blocked_at.add(before)
        d = self.known_deltas().get(aid)
        if d is None:
            return
        dst = (before[0] + d[0], before[1] + d[1])
        for x, y in self.footprint(dst, before):
            if 0 <= y < h and 0 <= x < w:
                self.hit[int(g0[y][x])] += 1

    def _learn_noise(
        self, g0: list[list[int]], g1: list[list[int]], explained: set
    ) -> None:
        rows: set[int] = set()
        cols: set[int] = set()
        for x, y, _a, _b in diff(g0, g1):
            if (x, y) in explained:
                continue
            rows.add(y)
            cols.add(x)
        for y in rows:
            self.noise_rows[y] += 1
        for x in cols:
            self.noise_cols[x] += 1

    def note_death(self, anchor: Optional[tuple[int, int]], aid: int) -> None:
        """Record the edge that just ended a life.

        Deaths were only ever written to Memory.known_dead, which is keyed on a
        hash of the whole screen and read by the phase-5 fallback. The phase-4
        navigator plans in avatar-anchor space and never consulted it, so nothing
        the agent learned from dying could reach the planner that produced 1178
        of ls20's 1199 actions. It walked into the same death seventeen times.

        The same bug is reported independently in Nurmi & Toivonen, "Graph-Based
        Exploration for ARC-AGI-3" (arXiv:2512.24156), whose agent placed 3rd:
        actions that triggered a reset were not marked as tested, so the agent
        re-selected reset-inducing state-action pairs and looped.
        """
        self.deaths += 1
        if anchor is not None and aid in (1, 2, 3, 4):
            self.fatal.add((anchor, aid))
        # The world is back at the level's start state, so a switch we already
        # flipped in the life that just ended is worth flipping again.
        self.epoch_stood.clear()

    def new_level(self) -> None:
        """Walls and coverage are per-level; colours and deltas are not.

        `color_floor` is per-level too: a fresh board restocks whatever we
        collected, and a stale all-time low would suppress the goal channel for
        the rest of the game.
        """
        self.color_floor.clear()
        self.click_gain.clear()
        self.click_n.clear()
        if TUNE["dead_scope"] == "level":
            self.click_dead.clear()
            self.click_live.clear()
        self.edges.clear()
        self.blocked.clear()
        self.seen.clear()
        self.stand.clear()
        self.switches.clear()
        self.blocked_at.clear()
        self.retry.clear()
        self.fatal.clear()
        self.epoch_stood.clear()
        self.epoch += 1

    # ── planning in avatar space ────────────────────────────────────────────
    def _moves(self, ids: list[int]) -> list[tuple[int, tuple[int, int]]]:
        deltas = self.known_deltas()
        return [(a, deltas[a]) for a in sorted(deltas) if a in ids]

    def _successors(
        self, grid: list[list[int]], cur: tuple[int, int], moves: list, strict: bool = True
    ):
        """`strict` skips squares whose colours have blocked us before.

        Colour is a guess, so it only ever postpones a square: callers retry
        with strict=False. A colour that walled off the exit in one world state
        must not wall it off forever.
        """
        for aid, (dx, dy) in moves:
            if (cur, aid) in self.blocked:
                continue
            # Unlike a colour-guessed wall, a death is an observed fact, so it is
            # skipped on the permissive pass too -- there is no point retrying it.
            if TUNE["avoid_fatal"] and (cur, aid) in self.fatal:
                continue
            nxt = self.edges.get((cur, aid))
            if nxt is None:
                nxt = (cur[0] + dx, cur[1] + dy)
                if not self.in_bounds(nxt):
                    continue
                if strict and not self.walkable(grid, cur, nxt):
                    continue
            elif not self.in_bounds(nxt):
                continue
            if nxt != cur:
                yield aid, nxt

    def route(
        self,
        grid: list[list[int]],
        goals: set,
        ids: list[int],
        horizon: int,
        max_nodes: int = 3000,
    ) -> Optional[list[str]]:
        """Shortest walk from the avatar to any goal anchor."""
        moves = self._moves(ids)
        if self.anchor is None or not goals or not moves:
            return None
        for strict in (True, False):
            q: deque = deque([(self.anchor, 0)])
            parent: dict = {self.anchor: None}
            while q:
                cur, depth = q.popleft()
                if depth >= horizon:
                    continue
                for aid, nxt in self._successors(grid, cur, moves, strict):
                    if nxt in parent:
                        continue
                    parent[nxt] = (cur, str(aid))
                    if nxt in goals:
                        return _reconstruct(parent, nxt)
                    q.append((nxt, depth + 1))
                if len(parent) >= max_nodes:
                    break
        return None

    def plan_explore(
        self, grid: list[list[int]], ids: list[int], horizon: int, max_nodes: int = 3000
    ) -> Optional[list[str]]:
        """Walk to the nearest square the avatar has never stood on.

        This is the intrinsic goal that exists before any level has ever been
        finished: cover the reachable board. It is what eventually steps on the
        switch, and RHAE prefers it to a thousand random button presses.
        """
        moves = self._moves(ids)
        if self.anchor is None or not moves:
            return None
        start = self.anchor
        want = self.goal_cells(grid) if "goal" in TUNE["tiers"] else set()
        win = self.win_cells(grid) if "win" in TUNE["tiers"] else set()
        for strict in (True, False):
            q: deque = deque([(start, 0)])
            parent: dict = {start: None}
            tiers: dict[str, tuple[int, int]] = {}
            best: Optional[tuple[int, int]] = None
            best_rank: Optional[tuple] = None
            while q:
                cur, depth = q.popleft()
                if depth >= horizon:
                    continue
                for aid, nxt in self._successors(grid, cur, moves, strict):
                    if nxt in parent:
                        continue
                    parent[nxt] = (cur, str(aid))
                    if want and self.cells_at(nxt) & want:
                        tiers.setdefault("goal", nxt)
                    if win and self.stand.get(nxt, 0) == 0 and self.cells_at(nxt) & win:
                        tiers.setdefault("win", nxt)
                    if nxt in self.retry:
                        tiers.setdefault("door", nxt)
                    elif self.stand.get(nxt, 0) == 0:
                        tiers.setdefault("new", nxt)
                    elif self.switches.get(nxt) and nxt not in self.epoch_stood:
                        tiers.setdefault("switch", nxt)
                    # Ranked fallback for when nothing above exists. The minus
                    # on depth breaks ties toward the FARTHEST candidate, so the
                    # agent commits to a walk instead of bouncing between two
                    # equally stale neighbours.
                    rank = (
                        self.seen.get((self.epoch, nxt), 0),
                        self.stand.get(nxt, 0),
                        -(depth + 1),
                    )
                    if best_rank is None or rank < best_rank:
                        best, best_rank = nxt, rank
                    q.append((nxt, depth + 1))
                if len(parent) >= max_nodes:
                    break
            # Order is TUNE["tiers"]; "goal" first means a known collectable
            # outranks curiosity, which is the whole point of the channel.
            for tier in TUNE["tiers"]:
                target = tiers.get(tier)
                if target is not None:
                    return _reconstruct(parent, target)
            here = (
                self.seen.get((self.epoch, start), 0),
                self.stand.get(start, 0),
                0,
            )
            if best is not None and best_rank is not None and best_rank < here:
                return _reconstruct(parent, best)
        return None


_CLICK_CACHE: dict = {}


def click_targets(
    grid: list[list[int]],
    cap: int = 0,
    dead: frozenset = frozenset(),
    prefer: frozenset = frozenset(),
) -> list[tuple[int, int]]:
    """One click target per connected component, rarest and smallest first.

    `dead` is the Tracker's set of object classes that never changed the frame:
    those components are skipped *before* the cap, so a dead button no longer
    shadows the live one behind it. `prefer` ranks classes that once finished
    a level ahead of everything else.

    ACTION6 is legal in 19 of the 25 public games and picks one of 4096 cells.
    The old policy offered six: three rare-colour centroids and four corners of
    the largest blob. On lp85 that meant 1191 explore actions cycling six dead
    cells and six distinct states over a full 1200-action budget.

    A component is the right unit because these boards are drawn from sprites:
    every button, tile and token is one blob, so one representative cell per blob
    covers the interactable surface at a branching factor the explorer can
    actually work through. Order is rarest colour first, then smallest area --
    a ten-pixel token is far likelier to be a control than the background slab.

    The representative is a cell that genuinely belongs to the component (its
    centroid can land outside a ring or an L), so a click always hits the thing
    it was chosen for.
    """
    cap = cap or TUNE["click_cap"]
    h = len(grid)
    w = len(grid[0]) if h else 0
    if not h or not w:
        return [(0, 0)]
    key = (digest(grid), cap, dead, prefer)
    hit = _CLICK_CACHE.get(key)
    if hit is not None:
        return hit
    bg = modal_color(grid)
    hist = histogram(grid)
    out: list[tuple[int, int]] = []
    ranked = []
    for b in blobs(grid):
        if b["color"] == bg:
            continue
        x0, y0, x1, y1 = b["bbox"]
        sig = click_sig(b["color"], b["area"], x1 - x0 + 1, y1 - y0 + 1)
        if sig in dead:
            continue
        cells = b["cells"]
        cx = sum(c[0] for c in cells) // len(cells)
        cy = sum(c[1] for c in cells) // len(cells)
        if (cx, cy) not in set(cells):
            cx, cy = min(cells, key=lambda c: abs(c[0] - cx) + abs(c[1] - cy))
        ranked.append((0 if sig in prefer else 1, hist.get(b["color"], 0), b["area"], cx, cy))
    ranked.sort()
    seen: set[tuple[int, int]] = set()
    for _p, _n, _a, cx, cy in ranked:
        if (cx, cy) not in seen:
            seen.add((cx, cy))
            out.append((cx, cy))
        if len(out) >= cap:
            break
    if not out:
        # A uniform board still has to be probed somewhere; a coarse lattice is
        # the only unbiased guess left.
        step = max(1, min(w, h) // 4)
        for y in range(step // 2, h, step):
            for x in range(step // 2, w, step):
                out.append((x, y))
                if len(out) >= cap:
                    break
            if len(out) >= cap:
                break
    out = out or [(w // 2, h // 2)]
    if len(_CLICK_CACHE) > 64:
        _CLICK_CACHE.clear()
    _CLICK_CACHE[key] = out
    return out


# ─────────────────────────────────────────────────────────────────────────────
# B. Mutable world model  (ProSAT prosat.py analog)
#    step(grid, action) is a pure function. Twin-blind context is ignored.
# ─────────────────────────────────────────────────────────────────────────────

class WorldModel:
    """Executable DSL, not a neural net. Search turns rules on/off."""

    def __init__(self) -> None:
        self.move: dict[int, tuple[int, int]] = dict(_STD_MOVE)
        self.step_n: int = 1
        self.player_color: int | None = None
        self.player_mode: str = "largest"  # largest | all
        self.solids: frozenset[int] = frozenset()
        self.a5: str = "none"  # none | toggle | pick | rotate
        self.t_from: int | None = None
        self.t_to: int | None = None
        self.a6: str = "select"  # select | drop
        self.block: str = "stay"  # stay | illegal
        self.win_hashes: frozenset = frozenset()
        self.win_hist: tuple | None = None

    @classmethod
    def identity(cls) -> "WorldModel":
        return cls()

    def key(self) -> str:
        mv = tuple(sorted(self.move.items()))
        sol = tuple(sorted(self.solids))
        return (
            f"p{self.player_color}|{self.player_mode}|s{sol}|m{mv}|n{self.step_n}"
            f"|5{self.a5}:{self.t_from}->{self.t_to}|6{self.a6}|b{self.block}"
        )

    def complexity(self) -> int:
        n = 0
        if self.player_color is not None:
            n += 1
        n += len(self.solids)
        if self.step_n != 1:
            n += 1
        if self.move != _STD_MOVE:
            n += 1
        if self.a5 != "none":
            n += 1
        if self.a6 != "select":
            n += 1
        if self.block != "stay":
            n += 1
        return n

    def is_win(self, grid: list[list[int]], level_index: int = 0) -> bool:
        del level_index
        t = to_tuple(grid)
        if t in self.win_hashes:
            return True
        if self.win_hist is not None:
            hist = histogram(grid)
            return tuple(hist[i] for i in range(16)) == self.win_hist
        return False

    def _player_cells(self, grid: list[list[int]]) -> list[tuple[int, int]]:
        if self.player_color is None:
            return []
        if self.player_mode == "all":
            return cells_of(grid, self.player_color)
        return largest_blob_cells(grid, self.player_color)

    def _blocked(self, orig: list[list[int]]) -> Optional[list[list[int]]]:
        return None if self.block == "illegal" else copy_grid(orig)

    def step(self, grid: list[list[int]], action: Any, context: Any = None) -> Optional[list[list[int]]]:
        """Pure: (grid, action) -> grid' | None (ILLEGAL). `context` is a twin-blind slot."""
        del context
        aid, ax, ay = parse_key(action)
        if aid == 7 or aid == 0:
            return None
        g = copy_grid(grid)
        if aid in (1, 2, 3, 4):
            return self._step_move(g, aid)
        if aid == 5:
            return self._step_a5(g)
        if aid == 6:
            return self._step_a6(g, int(ax or 0), int(ay or 0))
        return copy_grid(g)

    def _step_move(self, g: list[list[int]], aid: int) -> Optional[list[list[int]]]:
        if self.player_color is None:
            return copy_grid(g)
        dxy = self.move.get(aid)
        if not dxy:
            return copy_grid(g)
        dx, dy = dxy[0] * self.step_n, dxy[1] * self.step_n
        cells = self._player_cells(g)
        if not cells:
            return copy_grid(g)
        moved = apply_translation(
            g, {"color": self.player_color, "cells": cells}, dx, dy, self.solids
        )
        if moved is None:
            return self._blocked(g)
        return moved

    def _step_a5(self, g: list[list[int]]) -> Optional[list[list[int]]]:
        if self.a5 == "none" or self.player_color is None:
            return copy_grid(g)
        cells = self._player_cells(g)
        if self.a5 == "toggle":
            src = self.t_from if self.t_from is not None else self.player_color
            dst = self.t_to if self.t_to is not None else (src + 1) % 16
            out = copy_grid(g)
            h, w = len(out), len(out[0]) if out else 0
            for y in range(h):
                for x in range(w):
                    v = int(out[y][x])
                    if v == src:
                        out[y][x] = dst
                    elif v == dst and self.t_from is not None:
                        out[y][x] = src
            return out
        if self.a5 == "pick":
            if not cells:
                return copy_grid(g)
            bg = modal_color(g)
            out = copy_grid(g)
            for x, y in cells:
                out[y][x] = bg
            return out
        if self.a5 == "rotate":
            if not cells:
                return copy_grid(g)
            xs = [c[0] for c in cells]
            ys = [c[1] for c in cells]
            minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
            rot = [(minx + maxy - y, miny + x - minx) for x, y in cells]
            h, w = len(g), len(g[0])
            for nx, ny in rot:
                if nx < 0 or ny < 0 or nx >= w or ny >= h:
                    return self._blocked(g)
                if int(g[ny][nx]) in self.solids and (nx, ny) not in set(cells):
                    return self._blocked(g)
            bg = modal_color(g)
            out = copy_grid(g)
            for x, y in cells:
                out[y][x] = bg
            for nx, ny in rot:
                out[ny][nx] = self.player_color  # type: ignore[assignment]
            return out
        return copy_grid(g)

    def _step_a6(self, g: list[list[int]], x: int, y: int) -> Optional[list[list[int]]]:
        h, w = len(g), len(g[0]) if g else 0
        if not h:
            return copy_grid(g)
        x = max(0, min(w - 1, x))
        y = max(0, min(h - 1, y))
        if self.a6 == "select" or self.player_color is None:
            return copy_grid(g)
        cells = self._player_cells(g)
        if not cells:
            return copy_grid(g)
        cx = sum(p[0] for p in cells) // len(cells)
        cy = sum(p[1] for p in cells) // len(cells)
        moved = apply_translation(
            g, {"color": self.player_color, "cells": cells}, x - cx, y - cy, self.solids
        )
        return copy_grid(g) if moved is None else moved


def _safe_step(model: WorldModel, grid: list[list[int]], action: Any, context: Any = None) -> Optional[list[list[int]]]:
    try:
        return model.step(grid, action, context)
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# C. Twin-blind assessor  (ProSAT assess.py analog)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Report:
    n_ok: int
    n_total: int
    peeking: int
    complexity: int
    illegal_rate: float

    @property
    def ratio(self) -> float:
        return self.n_ok / self.n_total if self.n_total else 0.0


def _blind_copy(model: WorldModel) -> WorldModel:
    m = copy.copy(model)
    for slot in _PEEK_SLOTS:
        if hasattr(m, slot):
            setattr(m, slot, "BLIND")
    return m


class Assessor:
    """Two-pass isolation: U = step(grid, action); B = same after cache scramble + BLIND.

    `mask` is the Tracker's HUD mask. A step counter that ticks on every action
    is not part of the puzzle, and scoring against it would veto every model
    that is otherwise perfect. Masking is applied to prediction and to truth
    alike, so it cannot manufacture agreement the model has not earned.
    """

    def __init__(self, mask: Any = None) -> None:
        self.mask = mask

    def _hash(self, grid: Optional[list[list[int]]]) -> Any:
        if grid is None:
            return None
        if self.mask is None:
            return to_tuple(grid)
        return to_tuple(self.mask.mask_grid(grid))

    def verify(self, model: WorldModel, transitions: list) -> Report:
        n_ok = n_total = peeking = illegal = 0
        cx = model.complexity()
        # The blind twin is a property of the model, not of any one transition:
        # building it once per transition was pure waste.
        try:
            twin = _blind_copy(model)
        except Exception:
            twin = None
        for item in transitions:
            g0, akey, g1 = item[0], item[1], item[2]
            truth = item[3] if len(item) > 3 else self._hash(g1)
            n_total += 1
            u = _safe_step(model, g0, akey, None)
            if twin is None:
                b = None
                peeking += 1
            else:
                b = _safe_step(twin, g0, akey, "BLIND")
            ut = self._hash(u)
            bt = self._hash(b)
            if ut != bt:
                peeking += 1
            if u is None:
                illegal += 1
            elif ut == truth:
                n_ok += 1
        return Report(
            n_ok=n_ok,
            n_total=n_total,
            peeking=peeking,
            complexity=cx,
            illegal_rate=(illegal / n_total) if n_total else 0.0,
        )


def should_commit(rep: Report, best: Report | None) -> bool:
    """ProSAT commit: peeking==0 AND ratio >= best AND (n_ok up OR complexity down)."""
    if rep.peeking != 0 or rep.n_total <= 0:
        return False
    if best is None:
        return True
    if rep.ratio + 1e-12 < best.ratio:
        return False
    return (rep.n_ok > best.n_ok) or (rep.complexity < best.complexity)


# ─────────────────────────────────────────────────────────────────────────────
# D. Memory-in-the-Loop  (autoresearch-MIL sessions/memory.md analog)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Memory:
    records: list[dict[str, Any]] = field(default_factory=list)
    transitions: list[tuple] = field(default_factory=list)  # (g0, akey, g1) lists
    state_graph: dict = field(default_factory=dict)  # t0 -> {akey: t1}
    known_dead: set = field(default_factory=set)
    known_goal: set = field(default_factory=set)
    goals_by_level: dict = field(default_factory=lambda: defaultdict(set))
    goal_examples: list = field(default_factory=list)
    rejected_hypotheses: set = field(default_factory=set)
    win_routes: dict = field(default_factory=dict)  # level-start hash -> action keys
    tried: dict = field(default_factory=lambda: defaultdict(set))
    visits: Counter = field(default_factory=Counter)
    action_counts: dict = field(default_factory=lambda: defaultdict(Counter))
    t: int = 0
    log: str = ""

    def note(self, rec: dict[str, Any]) -> None:
        self.records.append(rec)
        line = (
            f"{rec.get('t')}|{rec.get('hypothesis','')}|{rec.get('n_ok')}/{rec.get('n_total')}"
            f"|cx={rec.get('complexity')}|acc={rec.get('accepted')}|{rec.get('note','')}\n"
        )
        self.log += line
        if len(self.log) > GROUND.MAX_MEMORY_CHARS:
            self.log = self.log[-GROUND.MAX_MEMORY_CHARS:]

    def log_transition(
        self, g0: list, akey: str, g1: list, *, scored: bool, hasher: Any = to_tuple
    ) -> None:
        t0, t1 = hasher(g0), hasher(g1)
        self.state_graph.setdefault(t0, {})[akey] = t1
        self.tried[t0].add(akey)
        self.action_counts[t0][akey] += 1
        self.visits[t1] += 1
        if scored and len(self.transitions) < 200:
            self.transitions.append((copy_grid(g0), akey, copy_grid(g1)))
        elif scored:
            self.transitions.pop(0)
            self.transitions.append((copy_grid(g0), akey, copy_grid(g1)))


# ─────────────────────────────────────────────────────────────────────────────
# Planner (BFS / uniform-cost on WorldModel.step) + graph replay
# ─────────────────────────────────────────────────────────────────────────────

def _reconstruct(parent: dict, end: Any) -> list[str]:
    path: list[str] = []
    cur = end
    while parent.get(cur) is not None:
        prev, akey = parent[cur]
        path.append(akey)
        cur = prev
    path.reverse()
    return path


def graph_plan(start: tuple, goals: set, graph: dict, dead: set, horizon: int) -> Optional[list[str]]:
    if not goals or start in goals:
        return [] if start in goals else None
    q: deque = deque([start])
    parent: dict = {start: None}
    while q:
        cur = q.popleft()
        edges = graph.get(cur) or {}
        for akey, nxt in edges.items():
            if nxt in parent or nxt in dead:
                continue
            parent[nxt] = (cur, akey)
            if nxt in goals:
                path = _reconstruct(parent, nxt)
                if path and len(path) <= horizon:
                    return path
            if len(parent) >= 4000:
                return None
            q.append(nxt)
    return None


def world_plan(
    model: WorldModel,
    start: list[list[int]],
    goal_hashes: set,
    goal_examples: list,
    horizon: int,
    extra_clicks: list[tuple[int, int]],
    visits: Optional[Counter] = None,
    action_order: Optional[list[str]] = None,
    hasher: Any = to_tuple,
) -> Optional[list[str]]:
    start_t = hasher(start)
    if start_t in goal_hashes or model.is_win(start):
        return None
    q: deque = deque([(start_t, 0)])
    parent: dict = {start_t: None}
    grids = {start_t: start}
    use_layout = (not goal_hashes) and bool(goal_examples)
    use_novel = (not goal_hashes) and (not goal_examples) and visits is not None
    start_d = min((layout_dist(start, ex) for ex in goal_examples), default=10**9) if use_layout else 10**9
    best_t, best_d, best_depth = start_t, start_d, 0
    base_keys = list(action_order) if action_order else [str(i) for i in (1, 2, 3, 4, 5)]

    def acts() -> list[str]:
        keys = list(base_keys)
        if model.a6 == "drop":
            keys.extend(make_key(6, x, y) for x, y in extra_clicks)
        return keys

    while q:
        cur_t, depth = q.popleft()
        if depth >= horizon:
            continue
        g = grids[cur_t]
        for akey in acts():
            nxt = _safe_step(model, g, akey)
            if nxt is None:
                continue
            nt = hasher(nxt)
            if nt in parent:
                continue
            parent[nt] = (cur_t, akey)
            grids[nt] = nxt
            if nt in goal_hashes or model.is_win(nxt):
                return _reconstruct(parent, nt)
            if use_novel and nt not in visits:
                return _reconstruct(parent, nt)
            if use_layout:
                d = min(layout_dist(nxt, ex) for ex in goal_examples)
                if d == 0:
                    return _reconstruct(parent, nt)
                if d < best_d:
                    best_t, best_d, best_depth = nt, d, depth + 1
            if len(parent) >= 4000:
                break
            q.append((nt, depth + 1))
        if len(parent) >= 4000:
            break
    if use_layout and best_t != start_t and best_d < start_d and best_depth > 0:
        return _reconstruct(parent, best_t)
    return None


# ─────────────────────────────────────────────────────────────────────────────
# ExplorePolicy  (informative, not random mash)
# ─────────────────────────────────────────────────────────────────────────────

class ExplorePolicy:
    def __init__(self, rng: random.Random, tracker: Optional[Tracker] = None) -> None:
        self.rng = rng
        self.tracker = tracker

    def candidates(self, grid: list[list[int]], ids: list[int]) -> list[str]:
        keys: list[str] = []
        idset = set(ids)
        for i in (1, 2, 3, 4, 5):
            if i in idset:
                keys.append(str(i))
        if 6 in idset:
            tr = self.tracker
            dead = tr.dead_sigs() if tr is not None else frozenset()
            prefer = frozenset(tr.win_sigs) if tr is not None and TUNE["win_prior"] else frozenset()
            for x, y in click_targets(grid, dead=dead, prefer=prefer):
                keys.append(make_key(6, x, y))
        for i in ids:
            if i not in (0, 1, 2, 3, 4, 5, 6, 7):
                keys.append(str(i))
        if 7 in idset:
            keys.append("7")
        # unique, order-preserving
        seen: set[str] = set()
        out: list[str] = []
        for k in keys:
            if k not in seen:
                seen.add(k)
                out.append(k)
        return out

    def pick(self, grid: list[list[int]], h: tuple, ids: list[int], mem: Memory) -> str:
        cands = self.candidates(grid, ids)
        if not cands:
            return "1"
        idset = set(ids)
        global_tried: set[str] = set()
        global_counts: Counter = Counter()
        for s in mem.tried.values():
            global_tried |= s
        for c in mem.action_counts.values():
            global_counts.update(c)
        # Discover movement / interact once each, even as the hash changes.
        for i in (1, 2, 3, 4):
            k = str(i)
            if i in idset and k not in global_tried:
                return k
        if 5 in idset and "5" not in global_tried:
            return "5"
        tried = mem.tried.get(h, set())
        untried = [k for k in cands if k not in tried]
        mode = TUNE["click_effect"]
        if untried and mode and self.tracker is not None:
            eff = self.tracker.click_effect()
            sig_of = {}
            for k in untried:
                if k.startswith("6:"):
                    _a, x, y = parse_key(k)
                    sig_of[k] = blob_at(grid, int(x or 0), int(y or 0))
            # Mode 2 scans every visible class once before exploiting any.
            scanning = mode == 2 and any(s not in eff for s in sig_of.values())
            best = [k for k, s in sig_of.items() if eff.get(s, 0) > 0]
            if best and not scanning:
                return min(best, key=lambda k: (-eff[sig_of[k]], global_counts.get(k, 0), k))
        if untried:
            return min(untried, key=lambda k: (global_counts.get(k, 0), k))
        counts = mem.action_counts.get(h) or Counter()
        return min(cands, key=lambda k: (counts.get(k, 0), k))


def _stable_seed(game_id: Any) -> int:
    raw = hashlib.md5(str(game_id).encode("utf-8")).hexdigest()[:8]
    return int(raw, 16)


def _infer_candidates(
    transitions: list,
    rejected: set,
    limit: int,
    hints: Optional[dict[int, tuple[int, int]]] = None,
    hint_colors: frozenset | None = None,
) -> list[WorldModel]:
    """Small hypothesis patches from observed diffs. Skip rejected keys.

    `hints` are the Tracker's measured per-action deltas: they seed the search
    with the stride the avatar was actually seen to take, instead of assuming 1.
    """
    out: list[WorldModel] = []
    seen: set[str] = set()

    def add(m: WorldModel) -> None:
        k = m.key()
        if k in seen or k in rejected or len(out) >= limit:
            return
        seen.add(k)
        out.append(m)

    add(WorldModel.identity())
    if not transitions:
        return out

    color_shift: dict[int, Counter] = defaultdict(Counter)
    act_shift: dict[int, Counter] = defaultdict(Counter)
    moved_cols: Counter = Counter()
    static_cells: dict[int, set] | None = None
    toggle_pairs: Counter = Counter()

    for item in transitions:
        g0, akey, g1 = item[0], item[1], item[2]
        aid, _x, _y = parse_key(akey)
        d = diff(g0, g1)
        st0 = color_stats(g0)
        st1 = color_stats(g1)
        if static_cells is None:
            static_cells = {}
            for col in set(st0) | set(st1):
                static_cells[int(col)] = set(cells_of(g0, int(col)))
        for col in list(static_cells.keys()):
            if st1.get(col, (0, 0, 0))[0] != len(static_cells[col]) or \
                    set(cells_of(g1, col)) != static_cells[col]:
                del static_cells[col]
        vanished: Counter = Counter()
        appeared: Counter = Counter()
        for x, y, ca, cb in d:
            vanished[ca] += 1
            appeared[cb] += 1
            if ca != cb:
                toggle_pairs[(ca, cb)] += 1
        for col in set(vanished) | set(appeared):
            c0 = _centroid_of(st0, col)
            c1 = _centroid_of(st1, col)
            if c0 and c1:
                dx, dy = int(round(c1[0] - c0[0])), int(round(c1[1] - c0[1]))
                if (dx, dy) != (0, 0) and max(abs(dx), abs(dy)) <= MAX_SHIFT:
                    color_shift[col][(dx, dy)] += 1
                    moved_cols[col] += 1
                    if aid in (1, 2, 3, 4):
                        act_shift[aid][(dx, dy)] += 1

    solids = frozenset(static_cells.keys()) if static_cells else frozenset()
    bg_guess = 0
    if transitions:
        bg_guess = modal_color(transitions[0][0])
    del d
    solids = frozenset(c for c in solids if c != bg_guess)
    bg_last = modal_color(transitions[-1][2])
    players = [c for c, _n in moved_cols.most_common(4) if c != bg_guess and c != bg_last]
    if not players:
        hist = histogram(transitions[-1][2])
        players = [c for c, n in hist.most_common()[::-1] if c != bg_last][:3]

    emp_move = dict(_STD_MOVE)
    for aid in (1, 2, 3, 4):
        if act_shift[aid]:
            emp_move[aid] = act_shift[aid].most_common(1)[0][0]

    strides: list[int] = [1, 2]
    if hints:
        hint_move = dict(_STD_MOVE)
        stride = 1
        for aid, (dx, dy) in hints.items():
            if aid not in (1, 2, 3, 4):
                continue
            mag = max(abs(dx), abs(dy)) or 1
            stride = max(stride, mag)
            hint_move[aid] = (dx // mag, dy // mag)
        if stride not in strides:
            strides.insert(0, stride)
        emp_move = hint_move
    if hint_colors:
        players = [c for c in hint_colors] + [c for c in players if c not in hint_colors]

    toggles = [p for p, _n in toggle_pairs.most_common(3)]

    for pcol in players:
        for mv in (emp_move, *_MOVE_VARIANTS):
            for step_n in strides:
                for sol in (frozenset(), solids):
                    m = WorldModel()
                    m.player_color = int(pcol)
                    m.move = dict(mv)
                    m.step_n = step_n
                    m.solids = sol
                    add(m)
                    if len(out) >= limit:
                        return out
        for (tf, tt) in toggles:
            m = WorldModel()
            m.player_color = int(pcol)
            m.solids = solids
            m.a5 = "toggle"
            m.t_from, m.t_to = int(tf), int(tt)
            add(m)
        for a5 in ("pick", "rotate"):
            m = WorldModel()
            m.player_color = int(pcol)
            m.solids = solids
            m.a5 = a5
            add(m)
        m = WorldModel()
        m.player_color = int(pcol)
        m.solids = solids
        m.a6 = "drop"
        add(m)
        m = WorldModel()
        m.player_color = int(pcol)
        m.solids = solids
        m.block = "illegal"
        add(m)
    return out[:limit]


# ─────────────────────────────────────────────────────────────────────────────
# MyAgent  — program.md analog (phases 0–5 every choose_action)
# ─────────────────────────────────────────────────────────────────────────────

class MyAgent(Agent):
    """General ARC-AGI-3 agent. One policy for every game; no id forks."""

    MAX_ACTIONS = 1200

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        gid = getattr(self, "game_id", "0")
        self._rng = random.Random(_stable_seed(gid))
        self.mem = Memory()
        self.tracker = Tracker()
        self.model = WorldModel.identity()
        self.best: Report | None = None
        self.assessor = Assessor(self.tracker)
        self.explore = ExplorePolicy(self._rng, self.tracker)
        self.pending_plan: list[str] = []
        self.nav_plan: list[str] = []
        self.replay_plan: list[str] = []
        self._nav_expect: Any = None
        self._pred_t: Any = None
        self._prev_g: list[list[int]] | None = None
        self._prev_key: str | None = None
        self._prev_anchor: tuple[int, int] | None = None
        self._prev_levels: int = 0
        self._explore_used: int = 0
        self._level_idx: int = 0
        self._research_gap: int = 1
        self._research_due: int = 0
        self.stats: Counter = Counter()  # phase counts, read by scripts/lab.py
        self._level_start: Any = None
        self._level_keys: list[str] = []
        self._replayed: set = set()

    @property
    def name(self) -> str:
        return f"{super().name}.{self.MAX_ACTIONS}"

    def _hash(self, grid: list[list[int]]) -> tuple:
        """State identity with the HUD masked out.

        Without this every frame is unique — a ticking step counter makes the
        state graph a straight line, so novelty search always reports "new" and
        the agent wanders instead of noticing it is walking in circles.
        """
        return to_tuple(self.tracker.mask_grid(grid))

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        if state_name(latest_frame) == "WIN":
            return True
        return int(getattr(self, "action_counter", 0) or 0) >= self.MAX_ACTIONS - 1

    def choose_action(self, frames: list[FrameData], latest_frame: FrameData) -> GameAction:
        try:
            return self._choose(frames, latest_frame)
        except Exception:
            logger.warning("choose_action recovered from exception", exc_info=False)
            return self._safe(latest_frame)

    def _choose(self, frames: list[FrameData], latest_frame: FrameData) -> GameAction:
        del frames
        st = state_name(latest_frame)
        levels = int(getattr(latest_frame, "levels_completed", 0) or 0)

        # PHASE 0 — RESET if NOT_PLAYED or GAME_OVER (log death first)
        if st in ("NOT_PLAYED", "GAME_OVER"):
            if st == "GAME_OVER" and self._prev_g is not None:
                self.mem.known_dead.add(self._hash(self._prev_g))
                if self._prev_key:
                    self.mem.tried[self._hash(self._prev_g)].add(self._prev_key)
                    self.tracker.note_death(
                        self._prev_anchor, parse_key(self._prev_key)[0]
                    )
            self.pending_plan.clear()
            self.nav_plan.clear()
            self.replay_plan.clear()
            self._nav_expect = None
            self._level_start = None
            self._level_keys = []
            self._pred_t = None
            self._prev_g = None
            self._prev_key = "0"
            self._prev_levels = levels
            return self._emit("0", latest_frame, "phase0-reset")

        grid = extract_grid(latest_frame)
        if grid is None:
            return self._safe(latest_frame)
        ids = legal_ids(latest_frame)

        # PHASE 1 — LOG the real transition, then re-read the screen
        if self._prev_g is not None and self._prev_key and self._prev_key != "0":
            if levels > self._prev_levels:
                # Outcome before dynamics: the anchor and deltas that produced
                # the winning move are the ones from before this frame.
                self.tracker.note_win(self._prev_g, self._prev_key, self._prev_anchor)
            self.tracker.observe(self._prev_g, self._prev_key, grid)
            if levels > self._prev_levels:
                self._bank_route()
            self.mem.log_transition(
                self._prev_g, self._prev_key, grid, scored=True, hasher=self._hash
            )
            if levels > self._prev_levels:
                nxt = self._hash(grid)
                self.mem.known_goal.add(nxt)
                self.mem.goals_by_level[self._prev_levels].add(nxt)
                if len(self.mem.goal_examples) < 8:
                    self.mem.goal_examples.append(copy_grid(grid))
        self._prev_levels = levels

        self.tracker.note_frame(grid)
        cur_t = self._hash(grid)
        self.mem.visits[cur_t] += 1
        if self._level_start is None:
            self._level_start = cur_t
            self._level_keys = []

        if levels > self._level_idx:
            self._explore_used = 0
            self._level_idx = levels
            self.pending_plan.clear()
            self.nav_plan.clear()
            self._nav_expect = None
            self._pred_t = None
            self.tracker.new_level()
            self._level_start = cur_t
            self._level_keys = []
            self._research_gap = 1
            self._research_due = 0

        # PHASE 3 before PHASE 2 return so the ratchet can raise n_ok (no deadlock).
        # Skip the expensive candidate sweep while a verified plan is still on track.
        aligned = bool(self.pending_plan and self._pred_t is not None and cur_t == self._pred_t)
        if len(self.mem.transitions) >= 2 and not aligned:
            self._maybe_research()

        # PHASE 2 — NEED_DATA? cheap informative explore.
        # Perception, not the ratchet, decides when the probing is over: once the
        # avatar and every legal arrow are measured there is nothing left to
        # learn by mashing buttons, and RHAE squares every wasted action.
        ready = self.tracker.ready(ids)
        need = not ready and (
            len(self.mem.transitions) < 8
            or (
                (self.best is None or self.best.n_ok < 3)
                and self._explore_used < TUNE["explore_budget"]
            )
        )
        if need:
            self._explore_used += 1
            key = self.explore.pick(grid, cur_t, ids, self.mem)
            return self._commit_action(grid, key, latest_frame, "phase2-explore")

        # PHASE 3 — REPLAY a route that finished this level before
        key = self._replay(cur_t, ids)
        if key is not None:
            return self._commit_action(grid, key, latest_frame, "phase3-replay")

        # PHASE 4 — PLAN IN THE TWIN (continue pending plan if prediction matched)
        if self.pending_plan and self._pred_t is not None and cur_t == self._pred_t:
            nxt_key = self.pending_plan[0]
            if self._key_legal(nxt_key, ids):
                self.pending_plan = self.pending_plan[1:]
                return self._commit_action(grid, nxt_key, latest_frame, "phase4-continue")
        if self.pending_plan and (self._pred_t is None or cur_t != self._pred_t):
            self.pending_plan.clear()
            self._pred_t = None
            self._research_gap = 1
            self._research_due = 0
            if len(self.mem.transitions) >= 2:
                self._research()

        plan = self._plan_graph(grid, levels, ids)
        if plan:
            first, rest = plan[0], plan[1:]
            self.pending_plan = rest
            self.nav_plan.clear()
            return self._commit_action(grid, first, latest_frame, "phase4-plan")

        # PHASE 4b — NAVIGATE: walk the avatar somewhere it has never stood.
        # This is the intrinsic goal that exists before any level is finished,
        # and it beats novelty search in the twin, which has no idea what a
        # level even is and wanders one step at a time.
        nav = self._navigate(grid, ids)
        if nav is not None:
            return self._commit_action(grid, nav[0], latest_frame, nav[1])

        # PHASE 4c — BFS IN THE TWIN (games with no steerable avatar)
        plan = self._plan_twin(grid, levels, ids)
        if plan:
            first, rest = plan[0], plan[1:]
            self.pending_plan = rest
            return self._commit_action(grid, first, latest_frame, "phase4-plan")

        # PHASE 5 — FALLBACK EXPLORE (Go-Explore on the real state graph)
        key = self._go_explore(grid, cur_t, ids)
        return self._commit_action(grid, key, latest_frame, "phase5-explore")

    def _bank_route(self) -> None:
        """A level just fell: keep the exact keys that did it, from level start."""
        if self._level_start is None or not self._level_keys:
            return
        route = list(self._level_keys)
        old = self.mem.win_routes.get(self._level_start)
        if old is None or len(route) < len(old):
            self.mem.win_routes[self._level_start] = route
        self.mem.note({
            "t": self.mem.t,
            "hypothesis": "route",
            "n_ok": len(route),
            "n_total": len(route),
            "complexity": 0,
            "accepted": True,
            "note": "level cleared",
        })

    def _replay(self, cur_t: tuple, ids: list[int]) -> Optional[str]:
        """Re-run the keys that cleared this level last time, from its start.

        Dropped the moment the avatar is not where the tape says it should be:
        a stale recording is worth less than nothing when RHAE squares every
        action it wastes.
        """
        tr = self.tracker
        if self.replay_plan:
            if self._nav_expect is not None and tr.anchor != self._nav_expect:
                self.replay_plan = []
                self._nav_expect = None
                return None
        else:
            route = self.mem.win_routes.get(cur_t)
            if not route or cur_t in self._replayed:
                return None
            self._replayed.add(cur_t)
            self.replay_plan = list(route)
        while self.replay_plan:
            key = self.replay_plan.pop(0)
            if self._key_legal(key, ids):
                self._nav_expect = (
                    tr.step_anchor(tr.anchor, parse_key(key)[0])
                    if tr.anchor is not None else None
                )
                return key
        return None

    def _navigate(self, grid: list[list[int]], ids: list[int]) -> Optional[tuple[str, str]]:
        tr = self.tracker
        if tr.anchor is None or not tr._moves(ids):
            return None
        if self.nav_plan and self._nav_expect == tr.anchor:
            key = self.nav_plan[0]
            if self._key_legal(key, ids):
                self.nav_plan = self.nav_plan[1:]
                self._nav_expect = tr.step_anchor(tr.anchor, parse_key(key)[0])
                return key, "phase4-nav-continue"
        self.nav_plan = []
        self._nav_expect = None
        path = tr.plan_explore(grid, ids, TUNE["plan_horizon"])
        if not path:
            return None
        path = [k for k in path if self._key_legal(k, ids)]
        if not path:
            return None
        self.nav_plan = path[1:]
        self._nav_expect = tr.step_anchor(tr.anchor, parse_key(path[0])[0])
        return path[0], "phase4-navigate"

    def _maybe_research(self) -> None:
        """Research on a backoff. It is by far the most expensive thing here, and
        on a game the DSL cannot express it never commits — so paying for it on
        every single action buys nothing. A commit resets the gap to 1; a barren
        round doubles it. A new level or a broken plan resets it too."""
        if self._research_due > 0:
            self._research_due -= 1
            return
        improved = self._research()
        self._research_gap = (
            1 if improved else min(TUNE["research_max_gap"], self._research_gap * 2)
        )
        self._research_due = self._research_gap - 1

    def _research(self) -> bool:
        """Propose ≤ MAX_MODEL_CANDIDATES patches; commit under ProSAT rule."""
        raw = self.mem.transitions[-24:]
        if not raw:
            return False
        # Hash the truth once per round, not once per candidate per transition.
        trans = [(t[0], t[1], t[2], self._hash(t[2])) for t in raw]
        deadline = time.perf_counter() + TUNE["research_ms"] / 1000.0
        committed = False
        if self.model is not None:
            self.best = self.assessor.verify(self.model, trans)
        cands = _infer_candidates(
            trans,
            self.mem.rejected_hypotheses,
            TUNE["max_candidates"],
            hints=self.tracker.known_deltas(),
            hint_colors=self.tracker.colors,
        )
        self.mem.t += 1
        for cand in cands:
            if time.perf_counter() > deadline:
                break
            if cand.key() == self.model.key() and self.best is not None:
                continue
            rep = self.assessor.verify(cand, trans)
            accepted = should_commit(rep, self.best)
            note = "commit" if accepted else ("peek" if rep.peeking else "no-improve")
            self.mem.note({
                "t": self.mem.t,
                "hypothesis": cand.key()[:120],
                "n_ok": rep.n_ok,
                "n_total": rep.n_total,
                "complexity": rep.complexity,
                "accepted": accepted,
                "note": note,
            })
            if rep.peeking:
                self.mem.rejected_hypotheses.add(cand.key())
            if accepted:
                self.model = cand
                self.best = rep
                committed = True
                if self.mem.known_goal:
                    self.model.win_hashes = frozenset(self.mem.known_goal)
                logger.warning(
                    "model accepted n_ok=%s/%s cx=%s",
                    rep.n_ok, rep.n_total, rep.complexity,
                )
        return committed

    def _goals(self, levels: int) -> set:
        """Only this level's finish states. Level 3 is not level 1 with a hat on,
        and steering toward a stale finish line is worse than having none."""
        return set(self.mem.goals_by_level.get(levels, set()))

    def _plan_graph(self, grid: list[list[int]], levels: int, ids: list[int]) -> Optional[list[str]]:
        cur = self._hash(grid)
        path = graph_plan(
            cur, self._goals(levels), self.mem.state_graph,
            self.mem.known_dead, TUNE["plan_horizon"],
        )
        if not path:  # empty list means already at a goal; keep looking
            return None
        return [k for k in path if self._key_legal(k, ids)] or None

    def _plan_twin(self, grid: list[list[int]], levels: int, ids: list[int]) -> Optional[list[str]]:
        goals = self._goals(levels)
        if self.best is None or self.best.n_ok < 3:
            return None
        # Retrodiction gate: a model that cannot replay the log does not get to
        # spend live actions. Retrodict's 99.9% card is this rule and little else.
        if self.best.ratio < TUNE["plan_min_ratio"]:
            return None
        clicks = distinctive_cells(grid) if 6 in ids else []
        gcounts: Counter = Counter()
        for c in self.mem.action_counts.values():
            gcounts.update(c)
        order = [str(i) for i in (1, 2, 3, 4, 5) if i in ids]
        order.sort(key=lambda k: (gcounts.get(k, 0), k))
        path = world_plan(
            self.model, grid, goals, self.mem.goal_examples if goals else [],
            TUNE["plan_horizon"], clicks,
            visits=self.mem.visits,
            action_order=order,
            hasher=self._hash,
        )
        if not path:
            return None
        return [k for k in path if self._key_legal(k, ids)] or None

    def _go_explore(self, grid: list[list[int]], cur: tuple, ids: list[int]) -> str:
        # Prefer ACTION7 only to leave a confirmed dead-end
        tried = self.mem.tried.get(cur, set())
        cands = self.explore.candidates(grid, ids)
        untried = [k for k in cands if k not in tried]
        if untried:
            return self.explore.pick(grid, cur, ids, self.mem)
        neighbors = self.mem.state_graph.get(cur) or {}
        unseen = [k for k, nxt in neighbors.items() if self.mem.visits[nxt] <= 1 and self._key_legal(k, ids)]
        if unseen:
            return unseen[0]
        rare = [
            h for h in self.mem.visits
            if h not in self.mem.known_dead and h != cur
        ]
        rare.sort(key=lambda h: (self.mem.visits[h], -len(self.mem.state_graph.get(h) or {})))
        path = graph_plan(cur, set(rare[:24]), self.mem.state_graph, self.mem.known_dead, TUNE["plan_horizon"])
        if path and self._key_legal(path[0], ids):
            self.pending_plan = path[1:]
            nxt = (self.mem.state_graph.get(cur) or {}).get(path[0])
            self._pred_t = nxt
            return path[0]
        if 7 in ids and cur in self.mem.known_dead:
            return "7"
        return self.explore.pick(grid, cur, ids, self.mem)

    def _key_legal(self, key: str, ids: list[int]) -> bool:
        aid, _x, _y = parse_key(key)
        return aid in ids

    def _commit_action(self, grid: list[list[int]], key: str, frame: FrameData, why: str) -> GameAction:
        pred = _safe_step(self.model, grid, key)
        self._pred_t = self._hash(pred) if pred is not None else None
        self._prev_g = copy_grid(grid)
        self._prev_key = key
        self._prev_anchor = self.tracker.anchor
        self._level_keys.append(key)
        return self._emit(key, frame, why)

    def _emit(self, key: str, frame: FrameData, why: str) -> GameAction:
        self.stats[why] += 1
        if key == "0":
            act = GameAction.RESET
            act.reasoning = why
            return act
        ids = legal_ids(frame)
        aid, x, y = parse_key(key)
        if aid not in ids:
            return self._safe(frame)
        try:
            act = GameAction.from_id(aid)
        except Exception:
            return self._safe(frame)
        if act.is_complex():
            if x is None or y is None:
                g = extract_grid(frame)
                cells = distinctive_cells(g) if g else [(0, 0)]
                x, y = cells[0]
            x, y = clamp_xy(x, y)
            try:
                act.set_data({"x": x, "y": y})
            except Exception:
                act.set_data({"x": 0, "y": 0})
            act.reasoning = {"phase": why, "xy": [x, y]}
        else:
            act.reasoning = why
        return act

    def _safe(self, frame: FrameData) -> GameAction:
        st = state_name(frame)
        if st in ("NOT_PLAYED", "GAME_OVER"):
            return GameAction.RESET
        ids = legal_ids(frame)
        for i in ids:
            if i != 6:
                try:
                    a = GameAction.from_id(i)
                    a.reasoning = "safe"
                    return a
                except Exception:
                    continue
        if 6 in ids:
            try:
                a = GameAction.ACTION6
                a.set_data({"x": 0, "y": 0})
                a.reasoning = "safe-a6"
                return a
            except Exception:
                pass
        return GameAction.ACTION1


# ─────────────────────────────────────────────────────────────────────────────
# Self-check: toy 8×8 translation + twin-blind + BFS (must pass before ship)
# ─────────────────────────────────────────────────────────────────────────────

class _PeekingModel(WorldModel):
    """Returns a constant future grid — must be rejected by Assessor."""

    def __init__(self, future: list[list[int]]) -> None:
        super().__init__()
        self._oracle = copy_grid(future)

    def step(self, grid: list[list[int]], action: Any, context: Any = None) -> Optional[list[list[int]]]:
        o = self._oracle
        if o == "BLIND" or not isinstance(o, list):
            return copy_grid(grid)
        return copy_grid(o)


def _self_check() -> None:
    g0 = [[0] * 8 for _ in range(8)]
    g0[3][3] = 1
    solids: frozenset[int] = frozenset({2})
    g1 = apply_translation(g0, 1, 1, 0, solids)
    assert g1 is not None and g1[3][4] == 1 and g1[3][3] == 0, "translation step 1"
    g2 = apply_translation(g1, 1, 1, 0, solids)
    assert g2 is not None and g2[3][5] == 1 and g2[3][4] == 0, "translation step 2"
    assert to_tuple(g0) != to_tuple(g1)
    assert histogram(g0)[1] == 1
    assert diff(g0, g1)
    bl = blobs(g0)
    assert any(b["color"] == 1 and b["area"] == 1 for b in bl)

    trans = [(g0, "4", g1), (g1, "4", g2)]
    assessor = Assessor()

    peek = _PeekingModel(g2)
    r_peek = assessor.verify(peek, trans)
    assert r_peek.peeking > 0, f"peeking model must be rejected, got {r_peek}"
    assert not should_commit(r_peek, None)

    good = WorldModel()
    good.player_color = 1
    good.move = dict(_STD_MOVE)
    good.solids = frozenset()
    r_good = assessor.verify(good, trans)
    assert r_good.peeking == 0, r_good
    assert r_good.n_ok == 2, r_good
    assert should_commit(r_good, Report(0, 2, 0, 0, 0.0))

    ident = WorldModel.identity()
    r_id = assessor.verify(ident, trans)
    assert r_id.n_ok == 0
    assert should_commit(r_good, r_id)

    plan = world_plan(good, g0, {to_tuple(g2)}, [g2], 8, [])
    assert plan is not None and len(plan) == 2, plan
    assert plan[0] == "4" and plan[1] == "4", plan

    mem = Memory()
    mem.log_transition(g0, "4", g1, scored=True)
    mem.log_transition(g1, "4", g2, scored=True)
    gp = graph_plan(to_tuple(g0), {to_tuple(g2)}, mem.state_graph, set(), 8)
    assert gp == ["4", "4"], gp

    class _DummyEnv:
        observation_space = None

        def step(self, *a: Any, **k: Any) -> None:
            return None

    agent = MyAgent(
        card_id="t",
        game_id="toy-self-check",
        agent_name="t",
        ROOT_URL="http://localhost",
        record=False,
        arc_env=_DummyEnv(),
    )
    idle = FrameData(state=GameState.NOT_PLAYED, frame=[], available_actions=[])
    assert agent.choose_action([], idle) is GameAction.RESET
    play = FrameData(
        state=GameState.NOT_FINISHED,
        frame=[g0],
        available_actions=[1, 2, 3, 4, 5],
        levels_completed=0,
    )
    a1 = agent.choose_action([], play)
    assert a1 is not None and a1 is not GameAction.RESET
    assert int(a1.value) in (1, 2, 3, 4, 5)
    play2 = FrameData(
        state=GameState.NOT_FINISHED,
        frame=[g1],
        available_actions=[1, 2, 3, 4, 5],
        levels_completed=0,
    )
    a2 = agent.choose_action([], play2)
    assert a2 is not None
    assert len(agent.mem.transitions) >= 1
    assert agent.mem.records or len(agent.mem.transitions) >= 1

    planner = MyAgent(
        card_id="t",
        game_id="toy-plan",
        agent_name="t",
        ROOT_URL="http://localhost",
        record=False,
        arc_env=_DummyEnv(),
    )
    planner.model = good
    planner.best = r_good
    planner._explore_used = GROUND.EXPLORE_BUDGET_PER_LEVEL
    planner.mem.known_goal.add(to_tuple(g2))
    planner.mem.goals_by_level[0].add(to_tuple(g2))
    for _ in range(8):
        planner.mem.log_transition(g0, "4", g1, scored=True)
        planner.mem.log_transition(g1, "4", g2, scored=True)
    start_fr = FrameData(
        state=GameState.NOT_FINISHED,
        frame=[g0],
        available_actions=[1, 2, 3, 4, 5],
        levels_completed=0,
    )
    planned = planner.choose_action([], start_fr)
    assert int(planned.value) == 4, planned
    assert planner.pending_plan, "pending_plan should hold the rest of the 2-step route"
    assert "phase4" in str(planned.reasoning)

    over = FrameData(state=GameState.GAME_OVER, frame=[g0], available_actions=[1, 2, 3, 4])
    assert planner.choose_action([], over) is GameAction.RESET
    win = FrameData(state=GameState.WIN, frame=[g2], available_actions=[])
    assert planner.is_done([], win) is True

    _self_check_tracker()
    print("self-check OK")


def _hud_grid(step: int, px: int, py: int) -> list[list[int]]:
    """16x16 board: floor 3, wall 4 border, a 2x2 avatar, and a ticking bar."""
    g = [[3] * 16 for _ in range(16)]
    for i in range(16):
        g[0][i] = g[15][i] = g[i][0] = g[i][15] = 4
    for dy in range(2):
        for dx in range(2):
            g[py + dy][px + dx] = 7
    for i in range(min(step, 14)):  # status bar: one more lit cell per action
        g[14][1 + i] = 11
    return g


def _self_check_tracker() -> None:
    a = _hud_grid(0, 6, 6)
    b = _hud_grid(1, 6, 4)  # avatar moved up two, bar ticked one cell

    mv = detect_move(a, b)
    assert mv is not None, "translation under HUD noise must still be found"
    assert mv[0] == 0 and mv[1] == -2, mv
    assert 7 in mv[2], mv[2]

    tr = Tracker()
    grids = [_hud_grid(0, 6, 6), _hud_grid(1, 6, 4), _hud_grid(2, 6, 6),
             _hud_grid(3, 6, 4), _hud_grid(4, 6, 6)]
    for i, (g0, g1) in enumerate(zip(grids, grids[1:])):
        tr.observe(g0, "1" if i % 2 == 0 else "2", g1)
        tr.note_frame(g1)
    assert tr.known_deltas().get(1) == (0, -2), tr.known_deltas()
    assert tr.known_deltas().get(2) == (0, 2), tr.known_deltas()
    assert tr.anchor == (6, 6), tr.anchor
    assert 14 in tr.mask_rows, sorted(tr.mask_rows)
    assert 6 not in tr.mask_rows, "a row the avatar walks is never HUD"
    assert 7 not in tr.wall_colors(), "the avatar cannot be its own wall"

    # Masked hashing: frames that differ only in the status bar are one state.
    assert to_tuple(tr.mask_grid(_hud_grid(2, 6, 6))) == to_tuple(
        tr.mask_grid(_hud_grid(9, 6, 6))
    ), "HUD must not split one state into many"

    # Routing: unvisited ground is chosen, and a wall we bumped is not retried.
    cur = _hud_grid(4, 6, 6)
    tr.h, tr.w = 16, 16
    path = tr.plan_explore(cur, [1, 2, 3, 4], 12)
    assert path, "must route toward ground it has never stood on"
    tr.blocked.add(((6, 6), 1))
    assert ((6, 6), 1) in tr.blocked
    tr.bump_epoch(_hud_grid(4, 6, 6), _hud_grid(4, 6, 6), set())
    before_epoch = tr.epoch
    changed = _hud_grid(4, 6, 6)
    changed[2][2] = 9
    changed[2][3] = 9
    tr.bump_epoch(_hud_grid(4, 6, 6), changed, set())
    assert tr.epoch == before_epoch + 1, "world change starts a new epoch"
    assert ((6, 6), 1) not in tr.blocked, "a new epoch reopens closed doors"

    # Replay: a banked route is handed back key by key, then abandoned when the
    # avatar is not where the tape says it should be.
    agent = MyAgent(card_id="t", game_id="toy-replay", agent_name="t",
                    ROOT_URL="http://localhost", record=False, arc_env=None)
    agent.tracker = tr
    start = agent._hash(cur)
    agent.mem.win_routes[start] = ["1", "2"]
    assert agent._replay(start, [1, 2, 3, 4]) == "1"
    agent._nav_expect = (99, 99)
    assert agent._replay(start, [1, 2, 3, 4]) is None, "stale tape must be dropped"
    assert agent._replay(start, [1, 2, 3, 4]) is None, "and not restarted"

    # Dead-signature: a class of object that never changes the frame leaves the
    # click list; a class that changed it once never counts as dead.
    board = [[3] * 16 for _ in range(16)]
    board[2][2] = board[2][3] = 9          # a 2x1 button that does nothing
    board[10][10] = 5                      # a 1x1 token that does something
    dead_tr = Tracker()
    dead_tr.observe(board, "6:2,2", board)  # no change
    assert blob_at(board, 2, 2) in dead_tr.dead_sigs(), dead_tr.dead_sigs()
    lit = copy_grid(board)
    lit[10][10] = 6
    dead_tr.observe(board, "6:10,10", lit)  # changed
    dead_tr.observe(board, "6:10,10", board)  # then once did not
    assert blob_at(board, 10, 10) not in dead_tr.dead_sigs(), "a live class is never dead"
    targets = click_targets(board, dead=dead_tr.dead_sigs())
    assert (10, 10) in targets and (2, 2) not in targets and (3, 2) not in targets, targets
    dead_tr.note_win(board, "6:10,10", None)
    assert blob_at(board, 10, 10) in dead_tr.win_sigs
    assert click_targets(board, prefer=frozenset(dead_tr.win_sigs))[0] == (10, 10)



if __name__ == "__main__":
    _self_check()
