"""play.py -- the teacher's window into a game. Human-owned: never edit.

A teaching round is you, the research agent, playing one dev game yourself. You
see what a perception system sees (the player, objects with stable ids, what your
last commands did, whether you are making progress, and a labelled picture of the
board), and you answer with up to four commands per decision.

It is stateless: every call replays your saved answers from the start (the games
are deterministic) and stops at the first decision you have not answered yet. A
crash or a power cut loses nothing.

    python play.py vc33                      # show the current decision
    python play.py vc33 --answer <<'EOF'     # answer it, then see the next one
    {"note": "hypothesis in under 25 words", "do": ["CLICK 4", "CLICK 31,41"]}
    EOF
    python play.py vc33 --round r002 --player claude-opus-5

When the game ends (decisions used up, out of actions, or won) the round is
scored with the competition formula and appended to memory/rounds.tsv.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

import prepare as P

ROOT = P.ROOT
M = P.load_module(ROOT / "perception.py", "perception")   # frozen: the teacher's view never drifts
T = P.GROUND["teacher"]
NAMES = {1: "UP", 2: "DOWN", 3: "LEFT", 4: "RIGHT", 5: "SPACE", 6: "CLICK", 7: "UNDO"}
BY_NAME = {v: k for k, v in NAMES.items()}
MOVES = (1, 2, 3, 4)
LARGE_AREA, LARGE_SPAN, MATCH_DIST, MAX_LINES = 200, 40, 12, 40
PALETTE = [(255, 255, 255), (204, 204, 204), (153, 153, 153), (102, 102, 102), (51, 51, 51), (0, 0, 0),
           (229, 58, 163), (255, 123, 204), (249, 60, 49), (30, 147, 255), (136, 216, 241), (255, 220, 0),
           (255, 133, 27), (146, 18, 49), (79, 204, 48), (163, 86, 214)]
XY = re.compile(r"\bCLICK\W*(?:AT\W*)?\(?\s*(\d+)\s*,\s*(\d+)")
CMD_RE = re.compile(r"\bCLICK\W*(?:AT\W*)?\(?\s*\d+\s*,\s*\d+\s*\)?|\b(?:UP|DOWN|LEFT|RIGHT)\W*\d*"
                    r"|\b(?:GOTO|CLICK)\W*(?:OBJECT\W*|ID\W*)?\d+|\bSPACE\b|\bUNDO\b")


class Finished(Exception):
    """The decision budget is spent: end the game here, even mid-walk."""


class NeedAnswer(Exception):
    def __init__(self, system: str, user: str, grid, objects, decision: int):
        super().__init__("need answer")
        self.system, self.user, self.grid, self.objects, self.decision = system, user, grid, objects, decision


def system_text(ids: list[int]) -> str:
    cmds = []
    if any(a in ids for a in MOVES):
        cmds += ["  UP n / DOWN n / LEFT n / RIGHT n   press that arrow n times (n from 1 to 10)",
                 "  GOTO id                            walk the player onto object id by the shortest known path"]
    if 6 in ids:
        cmds.append("  CLICK id                           click object id")
        if T["click_anywhere"]:
            cmds.append("  CLICK x,y                          click the exact pixel at (x, y), e.g. an empty spot")
    if 5 in ids:
        cmds.append("  SPACE                              the interact action")
    if 7 in ids:
        cmds.append("  UNDO                               undo the last action")
    return f"""You are playing an unknown puzzle game. Nobody tells you the rules or the goal.
Work out the goal by experimenting, then finish each level in as FEW actions as possible:
the score compares your actions per level with a human's, squared.

The board is a 64x64 grid of coloured pixels (colours are numbers 0-15). Positions are
(x, y): x grows to the right, y grows downward, (0, 0) is the top-left corner. Each object
has an id that stays the same from turn to turn while the object exists.

Your note is a HYPOTHESIS about the goal. When the report says you made no progress, state
a DIFFERENT hypothesis and test it. Do not repeat commands that did nothing.

Reply with ONLY one JSON object:
{{"note": "<25 words: your current hypothesis>", "do": ["...", "..."]}}

Commands for this game (at most {T['max_commands_per_decision']} per decision):
""" + "\n".join(cmds)


def parse(text: str) -> tuple[str, list[str]]:
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try:
            d = json.loads(m.group(0))
            raw = d.get("do", [])
            raw = raw if isinstance(raw, list) else [raw]
            cmds = []
            for c in raw:
                found = CMD_RE.findall(str(c).upper())
                cmds += found[:1] if isinstance(c, str) else found
            return str(d.get("note", ""))[:200], cmds[: T["max_commands_per_decision"]]
        except Exception:
            pass
    return "", CMD_RE.findall(text.upper())[: T["max_commands_per_decision"]]


def ranges(ids: list[int]) -> str:
    ids, out, i = sorted(ids), [], 0
    while i < len(ids):
        j = i
        while j + 1 < len(ids) and ids[j + 1] == ids[j] + 1:
            j += 1
        out.append(str(ids[i]) if i == j else f"{ids[i]}-{ids[j]}")
        i = j + 1
    return ", ".join(out)


class Teacher(M.MyAgent):
    """The perception module's Tracker, driven by your answers."""

    def __init__(self, *a, answers: list[dict], max_turns: int, **k):
        super().__init__(*a, **k)
        self.answers, self.max_turns = list(answers), max_turns
        self.tr = M.Tracker()
        self.queue: list[str] = []
        self.expect = self.prev_g = self.prev_key = self.prev_anchor = None
        self.levels, self.note, self.turns, self.n, self.deaths = 0, "", 0, 0, 0
        self.history: list[str] = []
        self.objects: dict[int, dict] = {}
        self.reg: dict[int, dict] = {}
        self.next_id = 1
        self.pending: list[str] = []
        self.steps: list[str] = []
        self.labels: dict[str, str] = {}
        self.prev_label = ""
        self.board_seen: Counter = Counter()
        self.new_boards, self.cur_digest = 0, ""
        self.level_at: list[int] = []
        self.notes: list[str] = []

    def is_done(self, frames, latest_frame) -> bool:
        if self.turns >= self.max_turns and not self.queue:
            return True
        return super().is_done(frames, latest_frame)

    # ── perception -> text ───────────────────────────────────────────────
    def has_player(self, ids) -> bool:
        return self.tr.anchor is not None and bool(self.tr.template) and any(a in ids for a in MOVES)

    def _strides(self):
        d = self.tr.known_deltas()
        return (max([abs(d[a][0]) for a in (3, 4) if a in d] or [0]),
                max([abs(d[a][1]) for a in (1, 2) if a in d] or [0]))

    def _scan(self, grid, ids) -> None:
        tr, bg, hist = self.tr, M.modal_color(grid), M.histogram(grid)
        me = tr.cells_at(tr.anchor) if self.has_player(ids) else set()
        cur = []
        for b in M.blobs(grid):
            if b["color"] == bg or (me and set(b["cells"]) <= me):
                continue
            cells = b["cells"]
            x0, y0, x1, y1 = b["bbox"]
            w, h = x1 - x0 + 1, y1 - y0 + 1
            cx, cy = sum(c[0] for c in cells) // len(cells), sum(c[1] for c in cells) // len(cells)
            cset = set(cells)
            if (cx, cy) not in cset:
                cx, cy = min(cells, key=lambda c: abs(c[0] - cx) + abs(c[1] - cy))
            cur.append({"color": b["color"], "cells": cset, "xy": (cx, cy), "w": w, "h": h, "bbox": b["bbox"],
                        "area": b["area"], "rare": hist[b["color"]], "sig": M.click_sig(b["color"], b["area"], w, h),
                        "large": b["area"] >= LARGE_AREA or max(w, h) >= LARGE_SPAN})
        pairs = []
        for i, c in enumerate(cur):
            for oid, r in self.reg.items():
                if r["color"] == c["color"]:
                    dist = abs(r["xy"][0] - c["xy"][0]) + abs(r["xy"][1] - c["xy"][1])
                    size = abs(r["area"] - c["area"]) / max(r["area"], c["area"])
                    if dist <= MATCH_DIST and size <= 0.6:
                        pairs.append((dist + 10 * size, i, oid))
        assign, used = {}, set()
        for _c, i, oid in sorted(pairs):
            if i not in assign and oid not in used:
                assign[i] = oid
                used.add(oid)
        first = not self.reg
        for i in sorted((i for i in range(len(cur)) if i not in assign),
                        key=lambda i: (cur[i]["large"], cur[i]["rare"], cur[i]["area"])):
            assign[i] = self.next_id
            cur[i]["new"] = not first
            self.next_id += 1
        self.reg = self.objects = {assign[i]: c for i, c in enumerate(cur)}

    def _object_lines(self, ids) -> list[str]:
        tr, dead = self.tr, self.tr.dead_sigs()
        player = self.has_player(ids)
        sx, sy = self._strides()
        pc = (tr.anchor[0] + tr.size[0] / 2, tr.anchor[1] + tr.size[1] / 2) if player else None
        groups: dict = {}
        for oid, o in self.objects.items():
            groups.setdefault(o["sig"], []).append(oid)

        def one(oid: int) -> str:
            o = self.objects[oid]
            tags = []
            if o.get("new"):
                tags.append("NEW")
            if o["large"]:
                tags.append("large area: floor, wall or background")
            if o["sig"] in dead:
                tags.append("clicking it did nothing")
            if all(y in tr.mask_rows for _x, y in o["cells"]) or all(x in tr.mask_cols for x, _y in o["cells"]):
                tags.append("status bar")
            rel = ""
            if pc and sx and sy and not o["large"]:
                dx, dy = round((o["xy"][0] - pc[0]) / sx), round((o["xy"][1] - pc[1]) / sy)
                parts = ([f"{abs(dx)} {'right' if dx > 0 else 'left'}"] if dx else []) + \
                        ([f"{abs(dy)} {'down' if dy > 0 else 'up'}"] if dy else [])
                rel = f", {' and '.join(parts) or 'where you are'} in presses"
            return (f"  {oid}: color {o['color']}, {o['w']}x{o['h']}, at {o['xy']}{rel}"
                    + (f" [{', '.join(tags)}]" if tags else ""))

        lines, shown = [], set()
        # New objects first: they are what your last commands did to the board.
        for oid in sorted(i for i, o in self.objects.items() if o.get("new")):
            lines.append(one(oid))
            shown.add(oid)
        # Identical small objects collapse into one line instead of burying the list.
        for sig, members in sorted(groups.items(), key=lambda kv: min(kv[1])):
            rest = [m for m in members if m not in shown]
            o = self.objects[members[0]]
            if len(rest) >= 4 and not o["large"]:
                xs = [self.objects[m]["xy"][0] for m in rest]
                ys = [self.objects[m]["xy"][1] for m in rest]
                lines.append(f"  {ranges(rest)}: {len(rest)} alike, color {o['color']}, {o['w']}x{o['h']}, "
                             f"centres spanning x {min(xs)}-{max(xs)}, y {min(ys)}-{max(ys)}"
                             + (" [clicking one did nothing]" if sig in dead else ""))
                shown.update(rest)
        for oid in sorted(self.objects):
            if oid not in shown and len(lines) < MAX_LINES:
                lines.append(one(oid))
                shown.add(oid)
        if len(shown) < len(self.objects):
            lines.append(f"  (+{len(self.objects) - len(shown)} more objects not listed)")
        return lines

    def _prompt(self, grid, ids, frame) -> str:
        tr = self.tr
        total = int(getattr(frame, "win_levels", 0) or 0)
        out = [f"Level {self.levels + 1}" + (f" of {total}" if total else "") + f". Actions used so far: {self.n}.",
               "Available actions: " + ", ".join(NAMES[i] for i in ids if i in NAMES) + "."]
        self._scan(grid, ids)
        if self.has_player(ids):
            moves = ", ".join(f"{NAMES[a]} moves it {d}" for a, d in sorted(tr.known_deltas().items()) if a in MOVES)
            out.append(f"Player: a {tr.size[0]}x{tr.size[1]} piece with its top-left at {tr.anchor}. "
                       + (f"One press: {moves} pixels." if moves else "Moves not measured yet."))
            blocked = sorted({NAMES[a] for (anc, a) in tr.blocked if anc == tr.anchor})
            fatal = sorted({NAMES[a] for (anc, a) in tr.fatal if anc == tr.anchor})
            if blocked:
                out.append(f"From here these moves are BLOCKED: {', '.join(blocked)}.")
            if fatal:
                out.append(f"From here these moves KILLED you before: {', '.join(fatal)}.")
        elif any(a in ids for a in MOVES):
            out.append("Player: not located yet (try an arrow key).")
        else:
            out.append("There is no player in this game: you act only by clicking.")
        if self.turns:
            again = self.board_seen[self.cur_digest] - 1
            out.append(f"Progress: your last commands reached {self.new_boards} board(s) you had never seen before"
                       + (f"; you have been on this exact board {again} time(s) before." if again > 0 else "."))
            if self.new_boards == 0 or again >= 2:
                out.append("NO PROGRESS. Your current hypothesis is not working: state a DIFFERENT one and test it.")
        out.append("Objects (id: colour, size, centre):")
        out += self._object_lines(ids) or ["  (none)"]
        if self.steps:
            merged: list[str] = []
            for s in self.steps[-10:]:
                if merged and merged[-1].split(" (x")[0] == s:
                    head, _, cnt = merged[-1].partition(" (x")
                    merged[-1] = f"{head} (x{int(cnt.rstrip(')') or 1) + 1})"
                else:
                    merged.append(s)
            out.append("Results of your last actions, oldest first:\n  " + "\n  ".join(merged))
        if self.pending:
            out.append("Events: " + " ".join(self.pending))
        if self.note:
            out.append(f"Your previous hypothesis: {self.note}")
        return "\n".join(out)

    # ── commands -> keys ─────────────────────────────────────────────────
    def _expand(self, cmd: str, grid, ids) -> list[str]:
        cmd, tr, player = cmd.strip().upper(), self.tr, self.has_player(ids)
        m = XY.search(cmd)
        if m:
            x, y = int(m.group(1)), int(m.group(2))
            if not T["click_anywhere"] or 6 not in ids:
                self.pending.append("CLICK x,y is not available here.")
                return []
            if not (0 <= y < len(grid) and 0 <= x < len(grid[0])):
                self.pending.append(f"CLICK {x},{y}: outside the board.")
                return []
            k = M.make_key(6, x, y)
            self.labels[k] = f"CLICK {x},{y}"
            return [k]
        m = re.search(r"\b(UP|DOWN|LEFT|RIGHT)\W*(\d*)", cmd)
        if m and not cmd.startswith(("GOTO", "CLICK")):
            aid = BY_NAME[m.group(1)]
            if aid not in ids:
                self.pending.append(f"{m.group(1)} is not available in this game.")
                return []
            if player and (tr.anchor, aid) in tr.blocked and not self.queue:
                self.pending.append(f"Refused {m.group(1)}: already known to be blocked from {tr.anchor}.")
                return []
            return [str(aid)] * max(1, min(int(m.group(2) or 1), 10))
        m = re.search(r"\b(GOTO|CLICK)\W*(?:OBJECT\W*|ID\W*)?(\d+)", cmd)
        if m:
            verb, oid = m.group(1), m.group(2)
            obj = self.objects.get(int(oid))
            if obj is None:
                self.pending.append(f"{verb} {oid}: there is no object {oid} on the board now.")
                return []
            if verb == "CLICK" or not player:
                if 6 not in ids:
                    self.pending.append(f"{verb} {oid}: clicking is not available in this game.")
                    return []
                k = M.make_key(6, *obj["xy"])
                self.labels[k] = f"CLICK {oid}"
                return [k]
            xs, ys = [c[0] for c in obj["cells"]], [c[1] for c in obj["cells"]]
            if all(y in tr.mask_rows for y in ys) or all(x in tr.mask_cols for x in xs):
                self.pending.append(f"GOTO {oid}: that is part of the status bar, not a place.")
                return []
            missing = [a for a in MOVES if a in ids and a not in tr.known_deltas()]
            if missing:
                self.pending.append(f"GOTO {oid}: measuring {', '.join(NAMES[a] for a in missing)} first.")
                return [str(a) for a in missing]
            path = tr.route(grid, {(cx - rx, cy - ry) for cx, cy in obj["cells"] for rx, ry, _ in tr.template},
                            ids, horizon=80, max_nodes=8000)
            if path is not None:
                return path
            sw, sh = tr.size
            st = max((max(abs(d[0]), abs(d[1])) for d in tr.known_deltas().values()), default=1)
            near = {(ax, ay) for ax in range(min(xs) - sw - st, max(xs) + st + 1)
                    for ay in range(min(ys) - sh - st, max(ys) + st + 1)}
            path = tr.route(grid, near, ids, horizon=80, max_nodes=8000)
            if path is not None:
                self.pending.append(f"GOTO {oid}: cannot stand on it, walking next to it instead.")
                return path
            self.pending.append(f"GOTO {oid}: no known path (walls in the way or not explored yet).")
            return []
        if cmd.startswith("SPACE"):
            if 5 in ids:
                return ["5"]
            self.pending.append("SPACE is not available in this game.")
        elif cmd.startswith("UNDO"):
            if 7 in ids:
                return ["7"]
            self.pending.append("UNDO is not available in this game.")
        return []

    # ── the loop ─────────────────────────────────────────────────────────
    def choose_action(self, frames, latest_frame):
        st = M.state_name(latest_frame)
        levels = int(getattr(latest_frame, "levels_completed", 0) or 0)
        if st in ("NOT_PLAYED", "GAME_OVER"):
            if st == "GAME_OVER" and self.prev_g is not None:
                self.deaths += 1
                self.tr.note_death(self.prev_anchor, M.parse_key(self.prev_key or "0")[0])
                self.pending.append(f"YOU DIED after {self.prev_label}; the level restarted.")
            self.queue.clear()
            self.prev_g, self.prev_key = None, "0"
            self.n += 1
            return self._emit("0", latest_frame, "reset")
        grid = M.extract_grid(latest_frame)
        if grid is None:
            return self._safe(latest_frame)
        ids = M.legal_ids(latest_frame)
        if self.prev_g is not None and self.prev_key not in (None, "0"):
            self.tr.observe(self.prev_g, self.prev_key, grid)
            self.tr.note_frame(grid)
            paid = M.parse_key(self.prev_key)[0]
            if paid in MOVES and self.prev_anchor is not None and self.has_player(ids):
                self.steps.append(f"{NAMES[paid]}: " + ("BLOCKED, player did not move" if self.tr.anchor == self.prev_anchor
                                                        else f"player moved to {self.tr.anchor}"))
            else:
                d = M.diff(self.tr.mask_grid(self.prev_g), self.tr.mask_grid(grid))
                if not d:
                    self.steps.append(f"{self.prev_label}: nothing changed")
                else:
                    xs, ys = [p[0] for p in d], [p[1] for p in d]
                    self.steps.append(f"{self.prev_label}: {len(d)} pixels changed in x {min(xs)}-{max(xs)}, "
                                      f"y {min(ys)}-{max(ys)}")
            if levels > self.levels:
                self.level_at += [self.n] * (levels - self.levels)
                self.pending.append(f"LEVEL COMPLETE after {self.n} total actions! New level; object ids reset.")
                self.tr.new_level()
                self.queue.clear()
                self.reg, self.next_id = {}, 1
        else:
            self.tr.note_frame(grid)
        self.levels = levels
        self.cur_digest = M.digest(self.tr.mask_grid(grid))
        if self.cur_digest not in self.board_seen:
            self.new_boards += 1
        self.board_seen[self.cur_digest] += 1
        if self.queue and self.expect is not None and self.tr.anchor != self.expect:
            self.pending.append(f"Walk interrupted at {self.tr.anchor}.")
            self.queue.clear()
        if not self.queue:
            self._think(grid, ids, latest_frame)
        if not self.queue:
            self.pending.append("None of your commands could be carried out; one probe action was spent.")
            probes = [str(i) for i in (1, 2, 3, 4, 5) if i in ids]
            probes += [M.make_key(6, *xy) for xy in M.click_targets(grid)] if 6 in ids else []
            self.queue = [probes[self.n % len(probes)]] if probes else ["1"]
        key = self.queue.pop(0)
        aid = M.parse_key(key)[0]
        self.prev_label = self.labels.get(key, NAMES.get(aid, key))
        self.expect = self.tr.step_anchor(self.tr.anchor, aid) if (self.has_player(ids) and aid in MOVES) else None
        self.prev_g, self.prev_key, self.prev_anchor = M.copy_grid(grid), key, self.tr.anchor
        self.n += 1
        return self._emit(key, latest_frame, "teacher")

    def _think(self, grid, ids, frame) -> None:
        if self.turns >= self.max_turns:
            # The last decision's walk was cut short: the budget is spent, so
            # the game ends here rather than asking for decision N+1.
            raise Finished()
        user = (("Your last commands:\n" + "\n".join(self.history[-3:]) + "\n\n") if self.history else "") \
            + self._prompt(grid, ids, frame)
        if self.turns >= len(self.answers):
            raise NeedAnswer(system_text(ids), user, grid, self.objects, self.turns)
        note, cmds = parse(self.answers[self.turns]["text"])
        self.turns += 1
        self.pending, self.new_boards = [], 0
        if note:
            self.note = note
        self.notes.append(note)
        self.history.append(f"at action {self.n}: {cmds}")
        for c in cmds:
            self.queue += self._expand(c, grid, ids)
        self.queue = self.queue[:40]


def render(grid, objects, file: Path) -> None:
    from PIL import Image, ImageDraw
    s = 8
    img = Image.new("RGB", (len(grid[0]) * s, len(grid) * s))
    px = img.load()
    for y, row in enumerate(grid):
        for x, v in enumerate(row):
            c = PALETTE[int(v) % 16]
            for dy in range(s):
                for dx in range(s):
                    px[x * s + dx, y * s + dy] = c
    d = ImageDraw.Draw(img)
    for oid, o in objects.items():
        if not o["large"]:
            x, y = o["xy"][0] * s, o["xy"][1] * s
            for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                d.text((x + ox, y + oy), str(oid), fill=(0, 0, 0))
            d.text((x, y), str(oid), fill=(255, 255, 255))
    file.parent.mkdir(parents=True, exist_ok=True)
    img.save(file)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("game")
    ap.add_argument("--round", default=time.strftime("r%Y%m%d"))
    ap.add_argument("--player", default="", help="who is teaching, e.g. claude-opus-5 (asked once per game)")
    ap.add_argument("--answer", action="store_true", help="read one JSON answer from stdin first")
    a = ap.parse_args()
    game = a.game
    if game not in P.DEV:
        sys.exit(f"{game} is not a dev game. Teaching happens on dev games only; hold games measure transfer.")
    folder = ROOT / "rounds" / a.round / game
    folder.mkdir(parents=True, exist_ok=True)
    answers_f, meta_f, trace_f = folder / "answers.jsonl", folder / "meta.json", folder / "trace.json"
    if trace_f.exists():
        t = json.loads(trace_f.read_text(encoding="utf-8"))
        sys.exit(f"{game} in round {a.round} is finished: {t['levels']} level(s), score {100 * t['score']:.2f}%. "
                 f"Start a new round with --round <name> to play it again.")
    meta = json.loads(meta_f.read_text(encoding="utf-8")) if meta_f.exists() else {}
    if a.player:
        meta["player"] = a.player
    if not meta.get("player"):
        sys.exit("Say who is teaching once, e.g. --player claude-opus-5")
    meta_f.write_text(json.dumps(meta), encoding="utf-8")
    answers = [json.loads(l) for l in answers_f.read_text(encoding="utf-8").splitlines()] if answers_f.exists() else []
    if a.answer:
        text = sys.stdin.read().strip()
        note, cmds = parse(text)
        if not cmds:
            sys.exit("That answer has no command I can read. Nothing was saved; answer again.")
        answers.append({"text": text, "t": time.strftime("%H:%M:%S")})
        answers_f.write_text("\n".join(json.dumps(x) for x in answers) + "\n", encoding="utf-8")

    env = P.arcade().make(game)
    agent = Teacher(card_id="teach", game_id=game, agent_name=f"teach.{game}", ROOT_URL="http://localhost",
                    record=False, arc_env=env, tags=["teach"], answers=answers, max_turns=T["decisions_per_game"])
    agent.MAX_ACTIONS = P.BUDGET
    try:
        agent.main()
    except NeedAnswer as need:
        k = need.decision + 1
        frame = folder / f"frame_{k:03d}.png"
        if T["render_frames"]:
            render(need.grid, need.objects, frame)
        print(f"GAME {game} (dev), round {a.round}, decision {k} of {T['decisions_per_game']}\n")
        print("SYSTEM:\n" + need.system + "\n\nUSER:\n" + need.user)
        if T["render_frames"]:
            print(f"\n[board image with object ids: {frame}]")
        print(f"\nAnswer with:  python play.py {game} --round {a.round} --answer <<'EOF'\n"
              "{\"note\": \"...\", \"do\": [\"...\"]}\nEOF")
        return
    except Finished:
        pass
    human = P.baselines(game)
    s = P.score_game(agent.level_at, human)
    trace = {"game": game, "round": a.round, "player": meta["player"], "levels": s["levels"],
             "level_actions": s["level_actions"], "human": human, "score": s["score"], "actions": agent.n,
             "decisions": agent.turns, "notes": agent.notes, "answers": [x["text"] for x in answers]}
    trace_f.write_text(json.dumps(trace, indent=1), encoding="utf-8")
    tsv = ROOT / "memory" / "rounds.tsv"
    new = not tsv.exists()
    with tsv.open("a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        if new:
            w.writerow(["round", "date", "player", "game", "split", "levels", "level_actions", "human",
                        "score_pct", "decisions", "actions", "last_hypothesis"])
        w.writerow([a.round, time.strftime("%Y-%m-%d"), f"teacher:{meta['player']}", game, "dev", s["levels"],
                    " ".join(map(str, s["level_actions"])), " ".join(map(str, human[: max(1, s["levels"])])),
                    f"{100 * s['score']:.3f}", agent.turns, agent.n, (agent.notes[-1] if agent.notes else "")[:160]])
    print(f"GAME {game} finished: {s['levels']} level(s) in {agent.n} actions over {agent.turns} decisions. "
          f"Score {100 * s['score']:.2f}% (actions per level {s['level_actions']} vs human {human[:len(s['level_actions'])]}).\n"
          f"Logged to memory/rounds.tsv. Now write what you learned: memory/games/{game}.md and memory/principles.md.")


if __name__ == "__main__":
    main()
