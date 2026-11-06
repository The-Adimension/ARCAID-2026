"""Generated games: mechanics composed from Core Knowledge, built on the official engine (arcengine).

Purpose: test a learning procedure on mechanics it was not written around. The 25 public games are
examples, not the rulebook; these 20 games add mechanics chosen to fall outside the nine rule kinds
of the first prototype (gravity, pushing, a chaser, conveyors, ice, a painting trail, teleports, a
mirrored twin, a timer, lights-out, click-to-spawn with gravity, a global colour swap, scrambled
controls), plus a few controls the old kinds do cover (walls, colour cycling, click-to-remove).

Each game is an ARCBaseGame subclass instance built from a spec; layouts are drawn from a seed.
They are played through `perform_action`, exactly as the toolkit plays the official games, and are
read back only through the screen. They were written by the same person who wrote the learner,
which is a bias: the specs are fixed here, before any result, and every result is reported.
"""
from __future__ import annotations

import random

from arcengine import ARCBaseGame, Camera, GameAction, Level, Sprite

FLOOR, BORDER = 0, 5
C = {"wall": 8, "avatar": 9, "box": 2, "rock": 6, "coin": 11, "key": 14, "door": 13, "goal": 3, "padA": 15,
     "padB": 12, "twin": 10, "chaser": 2, "drifter": 3, "trail": 12, "bar": 4, "switch": 12, "shape": 9,
     "block": 6}
MOVES = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
DIRECTIONAL = (GameAction.ACTION1, GameAction.ACTION2, GameAction.ACTION3, GameAction.ACTION4)
CLICK_ONLY = {"cycle3", "lights", "switch_turn", "spawn", "gravity_spawned", "remove", "swap5"}

SPECS = [
    {"id": "w01", "size": 16, "mech": ["walls"], "note": "control: steer + walls"},
    {"id": "w02", "size": 16, "mech": ["walls"], "controls": "scrambled", "note": "scrambled controls"},
    {"id": "w03", "size": 16, "mech": ["walls", "gravity"], "note": "gravity on rocks"},
    {"id": "w04", "size": 16, "mech": ["walls", "push"], "note": "pushable boxes"},
    {"id": "w05", "size": 21, "mech": ["walls", "coins"], "note": "collect coins"},
    {"id": "w06", "size": 16, "mech": ["walls", "keydoor"], "note": "key opens door"},
    {"id": "w07", "size": 16, "mech": ["walls", "teleport"], "note": "teleport pad"},
    {"id": "w08", "size": 16, "mech": ["walls", "twin"], "note": "mirrored twin"},
    {"id": "w09", "size": 21, "mech": ["walls", "chaser"], "note": "chaser"},
    {"id": "w10", "size": 16, "mech": ["walls", "drift"], "note": "conveyor drifters"},
    {"id": "w11", "size": 16, "mech": ["walls", "ice"], "note": "ice: slide until blocked"},
    {"id": "w12", "size": 16, "mech": ["walls", "paint"], "note": "painting trail"},
    {"id": "w13", "size": 21, "mech": ["walls", "coins", "timer"], "note": "coins + timer bar"},
    {"id": "w14", "size": 16, "mech": ["walls", "spin5"], "note": "ACTION5 rotates the avatar"},
    {"id": "w15", "size": 16, "mech": ["cycle3"], "note": "click cycles 3 colours (control)"},
    {"id": "w16", "size": 16, "mech": ["lights"], "note": "lights-out on a lattice"},
    {"id": "w17", "size": 16, "mech": ["switch_turn"], "note": "click switch rotates a shape"},
    {"id": "w18", "size": 16, "mech": ["spawn", "gravity_spawned"], "note": "click spawns falling blocks"},
    {"id": "w19", "size": 21, "mech": ["remove", "swap5"], "note": "click removes (control) + ACTION5 swaps colours"},
    {"id": "w20", "size": 32, "mech": ["walls", "push", "gravity", "coins"], "controls": "scrambled",
     "note": "push + gravity + coins, scrambled controls"},
]


def px(colour, w=1, h=1):
    return [[colour] * w for _ in range(h)]


class World(ARCBaseGame):
    def __init__(self, spec, seed=0):
        self.spec, self.mech = spec, set(spec["mech"])
        self.rng = random.Random(f"{spec['id']}-{seed}")
        n = spec["size"]
        self.n = n
        self.occupied, self.items = set(), set()
        sprites = self._layout()
        names = list(MOVES)
        if spec.get("controls") == "scrambled":
            self.rng.shuffle(names)
        self.dirmap = {a: MOVES[d] for a, d in zip(DIRECTIONAL, names)}
        actions = []
        if not self.mech <= CLICK_ONLY:
            actions += [1, 2, 3, 4]
        if self.mech & {"spin5", "swap5"}:
            actions.append(5)
        if self.mech & CLICK_ONLY - {"swap5", "gravity_spawned"}:
            actions.append(6)
        super().__init__(game_id=spec["id"], levels=[Level(sprites=sprites, grid_size=(n, n))],
                         camera=Camera(background=FLOOR, letter_box=BORDER, width=n, height=n),
                         available_actions=actions, seed=seed)

    # ------------------------------------------------------------------ layout
    def _free(self, margin=1, w=1, h=1):
        """A free spot for a w x h sprite, with a clear cell around it (objects start apart, as
        designed games place them; the border frame may be touched)."""
        for _ in range(10000):
            x, y = self.rng.randrange(margin, self.n - margin - w + 1), self.rng.randrange(margin, self.n - margin - h + 1)
            cells = {(x + i, y + j) for i in range(w) for j in range(h)}
            ring = {(cx + dx, cy + dy) for cx, cy in cells for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
            if not cells & self.occupied and not ring & self.items:
                self.occupied |= cells
                self.items |= cells
                return x, y
        raise RuntimeError("no free spot")

    def _layout(self):
        n, m, out = self.n, self.mech, []
        if not m <= CLICK_ONLY:
            frame = [[C["wall"] if x in (0, n - 1) or y in (0, n - 1) else -1 for x in range(n)] for y in range(n)]
            out.append(Sprite(frame, name="frame", tags=["wall"]))
            self.occupied |= {(x, y) for x in range(n) for y in range(n) if x in (0, n - 1) or y in (0, n - 1)}
            for _ in range(max(3, n * n // 25)):
                x, y = self._free(2)
                out.append(Sprite(px(C["wall"]), x=x, y=y, tags=["wall"]))
            if "spin5" in m:
                ax, ay = self._free(w=2, h=2)
                out.append(Sprite([[C["avatar"], C["avatar"]], [C["avatar"], -1]], x=ax, y=ay, layer=2, tags=["avatar"]))
            else:
                ax, ay = self._free()
                out.append(Sprite(px(C["avatar"]), x=ax, y=ay, layer=2, tags=["avatar"]))
        if "gravity" in m:
            for _ in range(4):
                x, y = self._free(2)
                out.append(Sprite(px(C["rock"]), x=x, y=y, tags=["rock"]))
        if "push" in m:
            for _ in range(4):
                x, y = self._free(2)
                out.append(Sprite(px(C["box"]), x=x, y=y, tags=["box"]))
        if "coins" in m:
            for _ in range(6):
                x, y = self._free()
                out.append(Sprite(px(C["coin"]), x=x, y=y, layer=-1, collidable=False, tags=["coin"]))
        if "keydoor" in m:
            x, y = self._free()
            out.append(Sprite(px(C["key"]), x=x, y=y, layer=-1, collidable=False, tags=["key"]))
            for _ in range(3):
                x, y = self._free()
                out.append(Sprite(px(C["door"]), x=x, y=y, tags=["door"]))
        if "teleport" in m:
            for tag in ("padA", "padB"):
                x, y = self._free()
                out.append(Sprite(px(C[tag]), x=x, y=y, layer=-1, collidable=False, tags=[tag]))
        if "twin" in m:
            x, y = self._free()
            out.append(Sprite(px(C["twin"]), x=x, y=y, layer=2, tags=["twin"]))
        if "chaser" in m:
            x, y = self._free()
            out.append(Sprite(px(C["chaser"]), x=x, y=y, layer=2, tags=["chaser"]))
        if "drift" in m:
            for _ in range(3):
                x, y = self._free(2)
                out.append(Sprite(px(C["drifter"]), x=x, y=y, tags=["drifter"]))
        if "timer" in m:
            for x in range(1, n - 1):
                out.append(Sprite(px(C["bar"]), x=x, y=n - 1, layer=3, collidable=False, tags=["bar"]))
        if "cycle3" in m:
            self.palette = [7, 10, 14]
            for y in range(2, n - 2, 3):
                for x in range(2, n - 2, 3):
                    out.append(Sprite(px(self.rng.choice(self.palette), 2, 2), x=x, y=y, tags=["tile"]))
        if "lights" in m:
            self.palette = [7, 1]
            for y in range(2, n - 2, 3):
                for x in range(2, n - 2, 3):
                    out.append(Sprite(px(self.rng.choice(self.palette), 2, 2), x=x, y=y, tags=["tile"]))
        if "switch_turn" in m:
            x, y = self._free(1, 2, 2)
            out.append(Sprite(px(C["switch"], 2, 2), x=x, y=y, tags=["switch"]))
            x, y = self._free(2, 3, 3)
            out.append(Sprite([[C["shape"], -1, -1], [C["shape"], -1, -1], [C["shape"], C["shape"], 3]],
                              x=x, y=y, tags=["shape"]))
            for _ in range(4):
                x, y = self._free(1, 2, 1)
                out.append(Sprite(px(7, 2, 1), x=x, y=y, tags=["decoy"]))
        if "spawn" in m:
            out.append(Sprite(px(C["wall"], n, 1), x=0, y=n - 1, tags=["ground"]))
            self.occupied |= {(x, n - 1) for x in range(n)}
        if "remove" in m:
            for _ in range(14):
                x, y = self._free(2)
                out.append(Sprite(px(self.rng.choice([7, 10])), x=x, y=y, tags=["block"]))
        return out

    # ------------------------------------------------------------------ helpers
    def _one(self, tag):
        s = self.current_level.get_sprites_by_tag(tag)
        return s[0] if s else None

    def _at(self, x, y, tag):
        return [s for s in self.current_level.get_sprites_by_tag(tag) if s.x == x and s.y == y]

    def _move_avatar(self, av, dx, dy):
        hits = self.try_move_sprite(av, dx, dy)
        if hits and "push" in self.mech and all("box" in s.tags for s in hits):
            if all(not self.try_move_sprite(b, dx, dy) for b in hits):
                hits = self.try_move_sprite(av, dx, dy)
        return not hits

    # ------------------------------------------------------------------ one action
    def step(self):
        a, m, lvl = self.action.id, self.mech, self.current_level
        av = self._one("avatar")
        if a in self.dirmap and av is not None:
            dx, dy = self.dirmap[a]
            x0, y0 = av.x, av.y
            if "ice" in m:
                for _ in range(self.n):
                    if not self._move_avatar(av, dx, dy):
                        break
            else:
                self._move_avatar(av, dx, dy)
            moved = (av.x, av.y) != (x0, y0)
            if "twin" in m and (tw := self._one("twin")):
                self.try_move_sprite(tw, -dx, -dy)
            if "paint" in m and moved and not self._at(x0, y0, "trail"):
                lvl.add_sprite(Sprite(px(C["trail"]), x=x0, y=y0, layer=-1, collidable=False, tags=["trail"]))
            if "teleport" in m and (pa := self._one("padA")) and (av.x, av.y) == (pa.x, pa.y):
                pb = self._one("padB")
                av.set_position(pb.x, pb.y)
            for coin in self._at(av.x, av.y, "coin"):
                lvl.remove_sprite(coin)
            if "keydoor" in m and self._at(av.x, av.y, "key"):
                for s in self._at(av.x, av.y, "key") + lvl.get_sprites_by_tag("door"):
                    lvl.remove_sprite(s)
        if a == GameAction.ACTION5:
            if "spin5" in m and av is not None:
                av.rotate(90)
            if "swap5" in m:
                for b in lvl.get_sprites_by_tag("block"):
                    c = int(b.pixels.max())
                    b.color_remap(None, 10 if c == 7 else 7)
        if a == GameAction.ACTION6:
            cell = self.camera.display_to_grid(self.action.data.get("x", 0), self.action.data.get("y", 0))
            if cell:
                gx, gy = cell
                hit = lvl.get_sprite_at(gx, gy, ignore_collidable=True)
                tags = set(hit.tags) if hit else set()
                if "tile" in tags and "cycle3" in m:
                    c = int(hit.pixels.max())
                    hit.color_remap(None, self.palette[(self.palette.index(c) + 1) % 3])
                if "tile" in tags and "lights" in m:
                    for t in lvl.get_sprites_by_tag("tile"):
                        if abs(t.x - hit.x) + abs(t.y - hit.y) in (0, 3):
                            c = int(t.pixels.max())
                            t.color_remap(None, self.palette[1 - self.palette.index(c)])
                if "switch" in tags:
                    self._one("shape").rotate(90)
                if "spawn" in m and hit is None and 0 < gx < self.n - 1 and 0 < gy < self.n - 1:
                    lvl.add_sprite(Sprite(px(C["block"]), x=gx, y=gy, tags=["spawned"]))
                if "remove" in m and "block" in tags:
                    lvl.remove_sprite(hit)
        # things that happen on every action, whichever it was
        falling = (lvl.get_sprites_by_tag("rock") if "gravity" in m else []) + \
                  (lvl.get_sprites_by_tag("spawned") if "gravity_spawned" in m else [])
        for s in sorted(falling, key=lambda s: -s.y):
            if s.y < self.n - 2:
                self.try_move_sprite(s, 0, 1)
        if "drift" in m:
            for s in lvl.get_sprites_by_tag("drifter"):
                if self.try_move_sprite(s, 1, 0) and s.x >= self.n - 2:
                    s.set_position(1, s.y)
        if "chaser" in m and av is not None and (ch := self._one("chaser")):
            dx, dy = (av.x > ch.x) - (av.x < ch.x), (av.y > ch.y) - (av.y < ch.y)
            first = [(dx, 0), (0, dy)] if abs(av.x - ch.x) >= abs(av.y - ch.y) else [(0, dy), (dx, 0)]
            for mx, my in first:
                if (mx, my) != (0, 0):
                    hits = self.try_move_sprite(ch, mx, my)
                    if av in hits:
                        self.lose()
                    if not hits:
                        break
        if "timer" in m:
            bar = sorted(lvl.get_sprites_by_tag("bar"), key=lambda s: s.x)
            if bar:
                lvl.remove_sprite(bar[-1])
            if len(bar) <= 1:
                self.lose()
        if "coins" in m and not lvl.get_sprites_by_tag("coin"):
            self.next_level()
        self.complete_action()


def make(spec, seed=0):
    return World(spec, seed)
