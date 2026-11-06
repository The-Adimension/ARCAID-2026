"""Four save runs on the same 10 public games, 25 min each, 10 streams: dfranzen v1, lexicon v1,
lexicon v2 (scale lock) and lexicon v3 (rules).

  python3 kaggle/lexicon-dfranzen/compare_four.py [V3_OUTPUT_DIR]

For v3 it also (1) derives request_usage.csv from the raw request logs when they are present, and
(2) collects every distinct `current_frame.rules` output the model received (tool messages in the
request logs) into rules_outputs.txt next to the run: how often the rules were read, and what they
said in real games. One run per arm: a mechanics comparison, not a score verdict.
"""
import csv
import glob
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
V3 = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else next(
    ROOT.glob("experiments/2026-10-08__arcaid3-lexicon-view-dfranzen-m2__v3*/outputs"))
RUNS = {
    "dfranzen v1": ROOT / "external_submission/2026-09-30__dfranzen__arc-agi-3-milestone-2-solution__v1__teambest-27.89/outputs",
    "lexicon v1": ROOT / "experiments/2026-10-05__arcaid3-lexicon-view-dfranzen-m2__v1__unsubmitted__offline10-41.13/outputs",
    "lexicon v2 (lock)": ROOT / "experiments/2026-10-07__arcaid3-lexicon-view-dfranzen-m2__v2__unsubmitted__offline10-42.61/outputs",
    "lexicon v3 (rules)": V3,
}
COLUMNS = ["game", "analysis_step", "action", "prompt_tokens", "cached_tokens", "image_tokens",
           "completion_tokens", "reasoning_tokens", "finish_reason"]


def games(folder):
    out = {}
    for g in json.load(open(folder / "benchmark.json"))["game_runs"]:
        tok = int(re.search(r"tokens=(\d+)", g["solver_note"] or "tokens=0").group(1))
        out[g["game_id"][:4]] = dict(lv=g["levels_completed"], score=g["final_score"], tok=tok, wall=g["final_wallclock_seconds"])
    return out


def derive_usage(folder):
    """request_usage.csv (kept in the repo) from the raw request logs (not committed)."""
    table = folder.parent / "request_usage.csv"
    logs = sorted(glob.glob(str(folder / "*_p0_requests.jsonl")))
    if table.exists() or not logs:
        return
    with open(table, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLUMNS)
        for f in logs:
            game = pathlib.Path(f).name[:4]
            for line in open(f):
                if '"usage"' not in line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                u = d.get("usage") or {}
                if not u.get("prompt_tokens"):
                    continue
                det = u.get("prompt_tokens_details") or {}
                w.writerow([game, d.get("analysis_step"), d.get("action"), u["prompt_tokens"], det.get("cached_tokens") or 0,
                            det.get("image_tokens") or 0, u.get("completion_tokens", 0), u.get("reasoning_tokens", 0),
                            d.get("finish_reason")])


def usage(folder):
    pt = ct = n = 0
    table = folder.parent / "request_usage.csv"
    if table.exists():
        for r in csv.DictReader(open(table)):
            pt += int(r["prompt_tokens"]); ct += int(r["cached_tokens"]); n += 1
    else:
        for f in glob.glob(str(folder / "*_p0_requests.jsonl")):
            for line in open(f):
                if '"usage"' not in line:
                    continue
                u = json.loads(line).get("usage") or {}
                if u.get("prompt_tokens"):
                    pt += u["prompt_tokens"]; ct += (u.get("prompt_tokens_details") or {}).get("cached_tokens") or 0
                    n += 1
    return dict(requests=n, reuse=100 * ct / max(1, pt))


def counters(folder):
    log = folder.parent / "log.txt"
    if not log.exists():
        return None, None
    final = ready = None
    for line in log.read_text().splitlines():
        if line.startswith("ARCAID3_LEXICON_FINAL"):
            final = line
        if line.startswith(("ARCAID3_LEXICON_READY", "ARCAID3_LEXICON_OFF")):
            ready = line
    if not final:
        return None, ready
    m = re.search(r"'tool_calls': (\d+), 'calls_using_view': (\d+)", final)
    r = re.search(r"'rules': (\d+)", final)
    text = f"{m.group(2)} of {m.group(1)} tool calls ({100 * int(m.group(2)) / max(1, int(m.group(1))):.1f}%)"
    if r:
        text += f", .rules in {r.group(1)}"
    return text, ready


def rules_outputs(folder):
    """Distinct `.rules` outputs the model received, per game (from tool messages in the request logs)."""
    seen = {}
    for f in sorted(glob.glob(str(folder / "*_p0_requests.jsonl"))):
        game = pathlib.Path(f).name[:4]
        for line in open(f):
            if "RULES for level" not in line and "rules unavailable" not in line:
                continue
            try:
                msgs = json.loads(line).get("messages") or []
            except json.JSONDecodeError:
                continue
            for m in msgs if isinstance(msgs, list) else []:
                content = m.get("content") if isinstance(m, dict) else None
                if isinstance(content, list):
                    content = " ".join(str(c.get("text", "")) for c in content if isinstance(c, dict))
                if isinstance(content, str) and ("RULES for level" in content or "rules unavailable" in content):
                    seen.setdefault(game, {})
                    seen[game].setdefault(content, None)
    return seen


def main():
    derive_usage(V3)
    data = {name: games(f) for name, f in RUNS.items()}
    common = sorted(set.intersection(*(set(d) for d in data.values())))
    lines = [f"{'game':5s}" + "".join(f" | {n:>18s}" for n in RUNS)]
    for g in common:
        lines.append(f"{g:5s}" + "".join(f" | {data[n][g]['lv']:3d} lv {data[n][g]['score']:6.1f}   " for n in RUNS))
    lines.append("")
    for name, folder in RUNS.items():
        d = data[name]
        lv = sum(d[g]["lv"] for g in common)
        sc = sum(d[g]["score"] for g in common) / len(common)
        tok = sum(d[g]["tok"] for g in common)
        wall = max(d[g]["wall"] for g in common)
        u = usage(folder)
        c, _ = counters(folder)
        lines.append(f"{name:18s} levels {lv:2d}  mean {sc:5.2f}  tokens {tok:7d}  tok/s {tok / wall:4.0f}  requests {u['requests']}  "
                     f"cache reuse {u['reuse']:.1f}%" + (f"  view read in {c}" if c else ""))
    _, ready = counters(V3)
    lines += ["", "v3 install line: " + (ready or "(not found)")]
    outs = rules_outputs(V3)
    if outs:
        total = sum(len(v) for v in outs.values())
        lines.append(f"v3 distinct .rules outputs seen by the model: {total} "
                     f"({', '.join(f'{g} {len(v)}' for g, v in sorted(outs.items()))})")
        with open(V3.parent / "rules_outputs.txt", "w") as fh:
            for g, v in sorted(outs.items()):
                for text in v:
                    fh.write(f"===== {g}\n{text}\n\n")
    print("\n".join(lines))
    (V3.parent / "compare_four.out").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
