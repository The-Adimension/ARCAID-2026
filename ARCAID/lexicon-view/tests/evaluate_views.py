"""Grade three ways of cutting a screen into objects against the games' own sprites.

Frames: the start screen of every level of the 25 public games (183 levels).
Truth:  groundtruth.owner_map (engine-internal; evaluation only).
Views (all computed from the screen colours alone):
  duck     single-colour, 4-connected pieces of the 64x64 screen: what the Duck
           harness's `current_frame.segmentation` returns (its background-colour
           pieces are left out here, as they are on the truth side).
  flat     lexicon.objects on the native grid: multi-colour, 8-connected.
  layered  lexicon.layered_objects: flat, with large pieces split into a floor and
           the things on it. This is the lexicon's default.

For every true sprite instance (its visible, non-background, non-HUD pixels):
  exact   one view piece has exactly its pixels
  merged  one view piece holds it plus pixels of other sprites
  split   its pixels are spread over two or more view pieces

Usage (Python 3.12, arc-agi==0.9.8, arcengine==0.9.3), from the repo root:
  python arcaid3/part2/evaluate_views.py  [writes arcaid3/part2/results/views_eval.json + samples.md]
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys
import time

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import groundtruth as gt  # noqa: E402
import lexicon as lx  # noqa: E402

OUT = HERE / "results"
VIEWS = ("duck", "flat", "layered", "layered4")
HUD_SHARE_MAX = 0.25   # screens mostly painted by interface code have no sprite-level truth


def view_map(frame: np.ndarray, view: str) -> tuple[np.ndarray, dict]:
    """Piece id per screen pixel (-1 = in no piece) for one view, plus native-grid facts."""
    grid = frame.tolist()
    nat = lx.native_grid(grid)
    cells, k, (oy, ox) = nat["cells"], nat["scale"], nat["offset"]
    bg = lx.background_colour(cells)
    pid = np.full(frame.shape, -1, dtype=np.int32)
    if view == "duck":
        for i, o in enumerate(lx.objects(grid, bg, connectivity=4, multicolour=False)):
            for r, c in o["cells"]:
                pid[r, c] = i
    else:
        if view == "flat":
            pieces = lx.objects(cells, bg, connectivity=8, multicolour=True)
        else:
            pieces = lx.layered_objects(cells, bg, connectivity=4 if view == "layered4" else 8)
        for i, o in enumerate(pieces):
            for r, c in o["cells"]:
                pid[oy + r * k: oy + (r + 1) * k, ox + c * k: ox + (c + 1) * k] = i
    return pid, {"scale": k, "offset": (oy, ox), "bg": bg, "residue": nat["residue"]}


def grade(frame, om, view):
    pid, facts = view_map(frame, view)
    owners = om["owners"]
    valid = (owners >= 0) & (frame != facts["bg"])
    pid = np.where(owners == gt.HUD, -1, pid)
    res = collections.Counter()
    pieces_per = []
    exact_pairs = []                       # (piece id, sprite index) for the dictionary check
    for s in np.unique(owners[valid]):
        foot = valid & (owners == s)
        ids = set(np.unique(pid[foot]).tolist())
        ids.discard(-1)
        res["gt_instances"] += 1
        res["gt_multicolour"] += int(len(np.unique(frame[foot])) > 1)
        # inseparable by colour: some pixel touches (4-neighbour) a pixel of ANOTHER sprite with the same colour
        ys, xs = np.nonzero(foot)
        touch = False
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = ys + dy, xs + dx
            ok = (yy >= 0) & (yy < 64) & (xx >= 0) & (xx < 64)
            yy, xx, y0, x0 = yy[ok], xx[ok], ys[ok], xs[ok]
            other = valid[yy, xx] & (owners[yy, xx] != s) & (frame[yy, xx] == frame[y0, x0])
            if other.any():
                touch = True
                break
        res["gt_inseparable"] += int(touch)
        pieces_per.append(len(ids))
        if not ids:
            res["missing"] += 1
        elif len(ids) > 1:
            res["split"] += 1
        else:
            (only,) = ids
            if int((pid == only).sum()) == int(foot.sum()):
                res["exact"] += 1
                res["exact_separable"] += int(not touch)
                exact_pairs.append((only, int(s)))
            else:
                res["merged"] += 1
    n_pieces = int(pid.max()) + 1 if pid.max() >= 0 else 0
    pure = 0
    for i in range(n_pieces):
        o = owners[(pid == i) & valid]
        if o.size and len(np.unique(o)) == 1:
            pure += 1
    res["pieces"] += n_pieces
    res["pure_pieces"] += pure
    return res, pieces_per, facts, exact_pairs, pid


def main() -> None:
    OUT.mkdir(exist_ok=True)
    arc = gt.arcade()
    ids = gt.game_ids(arc)
    t0 = time.time()
    total = {v: collections.Counter() for v in VIEWS}
    pieces = {v: [] for v in VIEWS}
    per_game = {}
    scale_check = collections.Counter()
    sizes = collections.Counter()
    dictionary = {}
    samples = []
    interface_drawn = {}
    for g in sorted(ids):
        lex = lx.Lexicon()
        game_tot = {v: collections.Counter() for v in VIEWS}
        sym_to_names = collections.defaultdict(set)
        name_to_syms = collections.defaultdict(set)
        frames = 0
        for li, frame, om in gt.level_start_frames(arc, ids[g]):
            hud_share = float((om["owners"] == gt.HUD).mean())
            if hud_share > HUD_SHARE_MAX:
                interface_drawn[g] = interface_drawn.get(g, 0) + 1
                continue
            frames += 1
            code = lx.encode(frame.tolist(), lex, seen_at=(g, li))
            cam_k, k = om["camera_scale"], code["scale"]
            scale_check["equal" if k == cam_k else ("coarser_lossless" if k % cam_k == 0 else "other")] += 1
            sizes["ascii64_chars"] += 64 * 65
            sizes["native_ascii_chars"] += len(lx.native_ascii(code)) + 1
            sizes["code_chars"] += len(lx.to_text(code))
            sizes["frames"] += 1
            for v in VIEWS:
                res, pp, facts, exact_pairs, pid = grade(frame, om, v)
                total[v].update(res)
                game_tot[v].update(res)
                pieces[v].extend(pp)
                if v == "layered":
                    # map each exactly-recovered piece to its lexicon symbol and its true sprite name
                    kk, (oy, ox) = code["scale"], code["offset"]
                    by_cell = {}
                    for p in code["placed"]:
                        r, c = p["cells"][0]
                        by_cell[(oy + r * kk, ox + c * kk)] = p["sym"]
                    for piece, s in exact_pairs:
                        ys, xs = np.nonzero(pid == piece)
                        first = min(zip(ys.tolist(), xs.tolist()))
                        sym = by_cell.get(first)
                        name = om["sprites"][s]["name"]
                        if sym:
                            sym_to_names[sym].add(name)
                            name_to_syms[name].add(sym)
            if li in (0, 1) and len(samples) < 8 and g in ("ft09", "sb26", "ls20", "lp85"):
                samples.append((g, li, lx.to_text(code)))
        dictionary[g] = {
            "symbols": len(lex.entries),
            "symbols_with_exact_match": len(sym_to_names),
            "symbols_one_name": sum(len(v) == 1 for v in sym_to_names.values()),
            "names_with_exact_match": len(name_to_syms),
            "names_one_symbol": sum(len(v) == 1 for v in name_to_syms.values()),
        }
        per_game[g] = {"frames": frames, **{v: dict(game_tot[v]) for v in VIEWS}}
        print(g, frames, {v: (game_tot[v]["exact"], game_tot[v]["gt_instances"]) for v in VIEWS}, flush=True)

    def summary(c, pp):
        n = c["gt_instances"]
        return {
            "gt_instances": n,
            "exact_share": round(c["exact"] / n, 4),
            "merged_share": round(c["merged"] / n, 4),
            "split_share": round(c["split"] / n, 4),
            "missing_share": round(c["missing"] / n, 4),
            "mean_pieces_per_true_object": round(float(np.mean(pp)), 3),
            "pieces": c["pieces"],
            "pure_piece_share": round(c["pure_pieces"] / max(1, c["pieces"]), 4),
            "multicolour_true_objects_share": round(c["gt_multicolour"] / n, 4),
            "colour_inseparable_share": round(c["gt_inseparable"] / n, 4),
            "exact_share_of_separable": round(c["exact_separable"] / max(1, n - c["gt_inseparable"]), 4),
        }

    d_tot = collections.Counter()
    for v in dictionary.values():
        d_tot.update(v)
    report = {
        "frames": sizes["frames"],
        "frames_skipped_interface_drawn": interface_drawn,
        "views": {v: summary(total[v], pieces[v]) for v in VIEWS},
        "native_scale_vs_camera": dict(scale_check),
        "chars_per_frame": {
            "ascii64": round(sizes["ascii64_chars"] / sizes["frames"], 1),
            "native_ascii": round(sizes["native_ascii_chars"] / sizes["frames"], 1),
            "code_listing": round(sizes["code_chars"] / sizes["frames"], 1),
        },
        "dictionary_alignment": {
            "symbols_total": d_tot["symbols"],
            "symbols_with_exact_match": d_tot["symbols_with_exact_match"],
            "symbols_mapping_to_one_true_name": d_tot["symbols_one_name"],
            "true_names_with_exact_match": d_tot["names_with_exact_match"],
            "true_names_mapping_to_one_symbol": d_tot["names_one_symbol"],
        },
        "per_game_dictionary": dictionary,
        "per_game": per_game,
        "seconds": round(time.time() - t0, 1),
    }
    (OUT / "views_eval.json").write_text(json.dumps(report, indent=1, sort_keys=True))
    with open(OUT / "samples.md", "w") as f:
        f.write("# Sample code listings (level start screens)\n\nGenerated by `evaluate_views.py`.\n\n")
        for g, li, text in samples:
            f.write(f"## {g}, level {li + 1}\n\n```\n{text}\n```\n\n")
    print(json.dumps({k: report[k] for k in ("frames", "frames_skipped_interface_drawn", "views", "native_scale_vs_camera", "chars_per_frame",
                                              "dictionary_alignment", "seconds")}, indent=1))


if __name__ == "__main__":
    main()
