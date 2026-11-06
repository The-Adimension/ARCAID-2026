"""Ground truth for grading screen views: which sprite owns each screen pixel.

EVALUATION ONLY. This reads the engine's internal sprite list and camera, which
an agent never sees (and which does not exist on Kaggle's hidden games). It is
used to grade `lexicon.py`, never to feed it.

Needs Python 3.12 with arc-agi==0.9.8 and arcengine==0.9.3 (competition pins).
"""
from __future__ import annotations

import json
import logging
import os
import pathlib

import numpy as np

logging.disable(logging.CRITICAL)

REPO = pathlib.Path(__file__).resolve().parents[2]
ENV_DIR = REPO / "inputs" / "official-input-arc-prize-2026-arc-agi-3" / "environment_files"

BACKGROUND, HUD, LETTERBOX = -1, -2, -3


def arcade():
    import arc_agi
    return arc_agi.Arcade(operation_mode=arc_agi.OperationMode.OFFLINE, environments_dir=str(ENV_DIR))


def game_ids(arc) -> dict[str, str]:
    return {e.game_id[:4]: e.game_id for e in arc.available_environments}


def baselines() -> dict[str, list[int]]:
    out = {}
    for g in sorted(os.listdir(ENV_DIR)):
        for v in os.listdir(ENV_DIR / g):
            out[g] = json.load(open(ENV_DIR / g / v / "metadata.json"))["baseline_actions"]
    return out


def owner_map(game) -> dict:
    """Render the current level twice: once in colours (must equal the real frame),
    once with sprite indices. Returns colours, owners and the sprite table.

    owner >= 0: index into `sprites`; -1 background; -2 HUD/interface overlay; -3 letterbox.
    """
    cam = game.camera
    level_sprites = list(game.current_level.get_sprites())
    h, w = cam._height, cam._width
    colours = np.full((h, w), cam._background, dtype=np.int16)
    owners = np.full((h, w), BACKGROUND, dtype=np.int32)
    order = sorted((i for i, s in enumerate(level_sprites) if s.is_visible), key=lambda i: level_sprites[i].layer)
    for i in order:
        s = level_sprites[i]
        px = s.render()
        sh, sw = px.shape
        rx, ry = s.x - cam._x, s.y - cam._y
        x0, x1 = max(0, rx), min(w, rx + sw)
        y0, y1 = max(0, ry), min(h, ry + sh)
        if x1 <= x0 or y1 <= y0:
            continue
        reg = px[y0 - ry:y1 - ry, x0 - rx:x1 - rx]
        m = reg >= 0
        colours[y0:y1, x0:x1][m] = reg[m]
        owners[y0:y1, x0:x1][m] = i
    scale, xo, yo = cam._calculate_scale_and_offset()
    if scale > 1:
        colours = np.repeat(np.repeat(colours, scale, 0), scale, 1)
        owners = np.repeat(np.repeat(owners, scale, 0), scale, 1)
    out_c = np.full((64, 64), cam._letter_box, dtype=np.int16)
    out_o = np.full((64, 64), LETTERBOX, dtype=np.int32)
    out_c[yo:yo + colours.shape[0], xo:xo + colours.shape[1]] = colours
    out_o[yo:yo + owners.shape[0], xo:xo + owners.shape[1]] = owners
    final = cam.render(level_sprites).astype(np.int16)
    out_o[final != out_c] = HUD          # pixels an interface (HUD bar, counter) drew over the picture
    table = [{"name": s.name, "tags": list(getattr(s, "_tags", []) or []), "x": s.x, "y": s.y,
              "layer": s.layer, "visible": bool(s.is_visible)} for s in level_sprites]
    return {"colours": final, "owners": out_o, "sprites": table, "camera_scale": scale,
            "camera_offset": (yo, xo), "world": (h, w)}


def level_start_frames(arc, gid: str):
    """Yield (level_index, real_frame, owner_map) for the start of every level.

    Level 0 comes from env.reset(). Later levels are entered with the engine's own
    set_level(), which is how the engine itself advances; the colour render is
    checked against the camera's output so a mismatch is caught, not hidden.
    """
    env = arc.make(gid, seed=0)
    f = env.reset()
    game = env._game
    first = np.array(f.frame[-1], dtype=np.int16)
    om = owner_map(game)
    assert (om["colours"] == first).all(), f"{gid}: owner-map render differs from the real frame"
    yield 0, first, om
    for li in range(1, len(game._levels)):
        game.set_level(li)
        om = owner_map(game)
        yield li, om["colours"], om
