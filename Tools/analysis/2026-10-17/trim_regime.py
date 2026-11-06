"""How much of the stuck-level spend happens after a level's early history can no longer fit.

Reads files only. Two inputs:
  1. a Franzen M2 benchmark.json (default: the 4 x 25 demo run, v3, as stored on
     origin/claude/vibrant-keller-ksqha6 at analysis/2026-10-10/data/dfranzen-m2-v3/benchmark.json);
  2. optionally, a folder of Franzen *_requests.jsonl logs, to count context trims per game.

A level attempt runs from the token after the previous level's completing action to the action that
completes the level; the first level a run did not complete is an unfinished attempt (as in
analysis/2026-10-10/attempts.py). RETAINED is Franzen's configured context drain: after a trim the
harness keeps about this many tokens. An attempt that generated more than RETAINED tokens on its level
cannot keep the level's earliest content once a trim happens. Generated tokens understate context growth
(tool output and images also fill it), so the counts are lower bounds on attempts exposed to the trim.

Usage:
  git show origin/claude/vibrant-keller-ksqha6:analysis/2026-10-10/data/dfranzen-m2-v3/benchmark.json > /tmp/fz.json
  python analysis/2026-10-17-gemma/trim_regime.py /tmp/fz.json \
      external_submission/2026-09-30__dfranzen__arc-agi-3-milestone-2-solution__v1__teambest-27.89/outputs
"""
from __future__ import annotations

import glob
import json
import os
import sys

RETAINED = 59_392  # ARC3 configured context drain in Franzen M2 v1 (write-up, section 1)


def attempts(run: dict) -> list[dict]:
    cum, s = [], 0
    for e in run["history"]:
        s += e["generated_tokens"]
        cum.append(s)
    total = run.get("final_generated_tokens") or s
    out, start_idx, start_tok = [], 0, 0
    for k, n_actions in enumerate(run["actions_per_level"]):
        if k < run["levels_completed"]:
            end_idx = start_idx + n_actions
            end_tok = cum[end_idx - 1]
            out.append(dict(done=True, tokens=end_tok - start_tok))
            start_idx, start_tok = end_idx, end_tok
        else:
            out.append(dict(done=False, tokens=total - start_tok))
            break
    return out


def trims(requests_path: str) -> int:
    """A trim shows as the message list shrinking between consecutive requests of one game."""
    n, prev = 0, None
    for line in open(requests_path):
        m = len(json.loads(line)["messages"])
        if prev is not None and m < prev - 2:
            n += 1
        prev = m
    return n


def main(bench_path: str, requests_dir: str | None) -> None:
    runs = json.load(open(bench_path))["game_runs"]
    atts = [a for r in runs for a in attempts(r)]
    done = [a for a in atts if a["done"]]
    open_ = [a for a in atts if not a["done"]]
    all_tok = sum(a["tokens"] for a in atts)
    open_tok = sum(a["tokens"] for a in open_)
    print(f"game runs {len(runs)}; level attempts {len(atts)}: completed {len(done)}, unfinished {len(open_)}")
    print(f"unfinished attempts' share of all generated tokens: {100 * open_tok / all_tok:.1f}%")
    for thr in (RETAINED, 100_000):
        past = sum(max(0, a["tokens"] - thr) for a in open_)
        print(f"threshold {thr:,} generated tokens on the level:")
        print(f"  completed attempts that finished below it: {100 * sum(a['tokens'] < thr for a in done) / len(done):.1f}%")
        print(f"  unfinished attempts that went past it: {sum(a['tokens'] > thr for a in open_)} of {len(open_)}")
        print(f"  unfinished tokens spent past it: {100 * past / open_tok:.1f}% of unfinished, {100 * past / all_tok:.1f}% of all")
    if requests_dir:
        print("context trims per game (request logs):")
        for f in sorted(glob.glob(os.path.join(requests_dir, "*_requests.jsonl"))):
            print(f"  {os.path.basename(f).split('_')[0]}: {trims(f)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
