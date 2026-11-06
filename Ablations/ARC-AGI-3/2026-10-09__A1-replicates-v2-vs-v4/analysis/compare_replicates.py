"""v4 against v2 with replicates: 3 save runs per arm on the same 10 public games and settings.

  python3 kaggle/lexicon-dfranzen/compare_replicates.py [--fetch]

Runs per arm: the original save run (Kaggle versions 2 and 4 of arcaid3-lexicon-view-dfranzen-m2) and
two replicates (arcaid3-rep-{v2,v4}-r{1,2}, the same notebooks byte for byte; replicates.py). With
--fetch it first downloads each replicate's benchmark.json, log and request logs through the Kaggle
API (read-only), derives request_usage.csv, and keeps the raw request logs out of the repo.

Reports each run (levels, 10-game mean, cache reuse, view and `.rules` usage), each arm's mean and
SD, per-game means, and an exact permutation test on the difference of arm means (all 20 ways of
splitting the 6 runs into two groups of 3).
"""
import csv
import itertools
import json
import pathlib
import re
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
REP = ROOT / "experiments/2026-10-09__replicates-v2-vs-v4"
# Originally a session scratch folder; made configurable when copied into ARCAID-2026 (2026-11-06).
import os
RAW = pathlib.Path(os.environ.get("REPLICATES_RAW", "replicates_raw"))
ARMS = {
    "v2": [ROOT / "experiments/2026-10-07__arcaid3-lexicon-view-dfranzen-m2__v2__unsubmitted__offline10-42.61"]
          + [REP / f"arcaid3-rep-v2-r{r}" for r in (1, 2)],
    "v4": [ROOT / "experiments/2026-10-08__arcaid3-lexicon-view-dfranzen-m2__v4__unsubmitted__offline10-55.36"]
          + [REP / f"arcaid3-rep-v4-r{r}" for r in (1, 2)],
}
COLUMNS = ["game", "analysis_step", "action", "prompt_tokens", "cached_tokens", "image_tokens",
           "completion_tokens", "reasoning_tokens", "finish_reason"]


def fetch(slug, folder):
    """benchmark.json, summary.txt, serve.log and log.txt into the repo folder; request logs to RAW."""
    import requests
    out = folder / "outputs"
    out.mkdir(parents=True, exist_ok=True)
    raw = RAW / slug
    raw.mkdir(parents=True, exist_ok=True)
    url = f"https://www.kaggle.com/api/v1/kernels/output?userName=habanwer&kernelSlug={slug}"
    def get(u):
        """GET with retries on rate limits; any other failure raises instead of leaving files half-written."""
        import time
        for wait in (0, 30, 60, 120, 240, 480):
            time.sleep(wait)
            r = requests.get(u, timeout=900)
            if r.status_code != 429:
                r.raise_for_status()
                return r
        r.raise_for_status()

    files, token = [], None
    while True:
        d = get(url + (f"&pageToken={token}" if token else "")).json()
        files += d.get("files", [])
        if d.get("log"):
            log = d["log"]
            try:
                log = "\n".join(e.get("data", "") for e in json.loads(log))
            except (ValueError, AttributeError):
                pass
            (folder / "log.txt").write_text(log)
        token = d.get("nextPageToken")
        if not token:
            break
    for f in files:
        name = f["fileName"]
        if name in ("benchmark.json", "summary.txt", "serve.log"):
            target = out / name
        elif name.endswith("_p0_requests.jsonl"):
            target = raw / name
        else:
            continue
        if not target.exists():
            target.write_bytes(get(f["url"]).content)
    if not (out / "benchmark.json").exists():
        raise RuntimeError(f"{slug}: no benchmark.json among the outputs ({len(files)} files listed)")
    table = folder / "request_usage.csv"
    if not table.exists():
        with open(table, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(COLUMNS)
            for f in sorted(raw.glob("*_p0_requests.jsonl")):
                for line in open(f):
                    if '"usage"' not in line:
                        continue
                    try:
                        d = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    u = d.get("usage") or {}
                    if u.get("prompt_tokens"):
                        det = u.get("prompt_tokens_details") or {}
                        w.writerow([f.name[:4], d.get("analysis_step"), d.get("action"), u["prompt_tokens"],
                                    det.get("cached_tokens") or 0, det.get("image_tokens") or 0,
                                    u.get("completion_tokens", 0), u.get("reasoning_tokens", 0), d.get("finish_reason")])


def run(folder):
    games = {}
    for g in json.load(open(folder / "outputs/benchmark.json"))["game_runs"]:
        games[g["game_id"][:4]] = (g["levels_completed"], g["final_score"])
    pt = ct = 0
    for r in csv.DictReader(open(folder / "request_usage.csv")):
        pt += int(r["prompt_tokens"])
        ct += int(r["cached_tokens"])
    final = next((l for l in (folder / "log.txt").read_text().splitlines() if l.startswith("ARCAID3_LEXICON_FINAL")), "")
    calls = re.search(r"'tool_calls': (\d+), 'calls_using_view': (\d+)", final)
    rules = re.search(r"'rules': (\d+)", final)
    return {"games": games, "levels": sum(v[0] for v in games.values()),
            "mean": sum(v[1] for v in games.values()) / len(games), "reuse": 100 * ct / max(1, pt),
            "view": f"{100 * int(calls.group(2)) / max(1, int(calls.group(1))):.1f}%" if calls else "-",
            "rules": rules.group(1) if rules else "-"}


def main():
    if "--fetch" in sys.argv:
        for arm in ARMS.values():
            for folder in arm[1:]:
                fetch(folder.name, folder)
    data = {a: [run(f) for f in fs] for a, fs in ARMS.items()}
    lines = ["run                                              levels   mean   cache   view   .rules"]
    for a, fs in ARMS.items():
        for f, r in zip(fs, data[a]):
            lines.append(f"{a} {f.name[:46]:46s} {r['levels']:5d} {r['mean']:7.2f} {r['reuse']:6.1f}% {r['view']:>6s} {r['rules']:>6s}")
    lines.append("")
    means = {a: [r["mean"] for r in data[a]] for a in ARMS}
    levels = {a: [r["levels"] for r in data[a]] for a in ARMS}
    for a in ARMS:
        lines.append(f"{a}: mean of 10-game means {statistics.mean(means[a]):.2f} (SD {statistics.stdev(means[a]):.2f}); "
                     f"levels {statistics.mean(levels[a]):.1f} (SD {statistics.stdev(levels[a]):.1f}); runs {', '.join(f'{m:.2f}' for m in means[a])}")
    diff = statistics.mean(means["v4"]) - statistics.mean(means["v2"])
    pool = means["v2"] + means["v4"]
    splits = list(itertools.combinations(range(6), 3))
    as_big = sum(1 for s in splits
                 if statistics.mean([pool[i] for i in s]) - statistics.mean([pool[i] for i in range(6) if i not in s]) >= diff - 1e-9)
    lines.append(f"v4 - v2: {diff:+.2f} points; exact permutation test (one-sided, 20 splits): p = {as_big}/20 = {as_big / 20:.2f}")
    ldiff = statistics.mean(levels["v4"]) - statistics.mean(levels["v2"])
    lpool = levels["v2"] + levels["v4"]
    las = sum(1 for s in splits
              if statistics.mean([lpool[i] for i in s]) - statistics.mean([lpool[i] for i in range(6) if i not in s]) >= ldiff - 1e-9)
    lines.append(f"levels v4 - v2: {ldiff:+.1f}; exact permutation test (one-sided): p = {las}/20 = {las / 20:.2f}")
    lines += ["", "per game, mean score over 3 runs (levels in brackets):", f"{'game':5s} {'v2':>16s} {'v4':>16s}"]
    for g in sorted(data["v2"][0]["games"]):
        cells = []
        for a in ARMS:
            sc = [r["games"][g][1] for r in data[a]]
            lv = [r["games"][g][0] for r in data[a]]
            cells.append(f"{statistics.mean(sc):6.1f} ({'/'.join(str(x) for x in lv)})")
        lines.append(f"{g:5s} {cells[0]:>16s} {cells[1]:>16s}")
    out = "\n".join(lines)
    REP.mkdir(parents=True, exist_ok=True)
    (REP / "compare_replicates.out").write_text(out + "\n")
    print(out)


if __name__ == "__main__":
    main()
