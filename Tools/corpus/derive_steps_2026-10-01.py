"""New rows for the AGI-RubiQ corpus: external-kernel public_demo rows and step rows.

Reads stored files only. Replays nothing, loads no pickle, starts no engine, and
does not touch the existing rows-*.jsonl files.

Step rows: one row per stored action in this repo's own outputs/ folders
(benchmark.json history entry + the matching type=action event). Reasoning and
tool code come from the type=analysis events of the same analysis_step and sit
on the first action row of that step; later actions of the step point to it.

Run from the repo root:
    python corpus/derive_steps_2026-10-01.py
writes corpus/rows-2026-10-01-steps-N.jsonl (one row set, sharded at MAX_BYTES so
no file nears GitHub's 100 MiB limit) and prints a summary as JSON.
"""

from __future__ import annotations

import collections
import glob
import json
import os
import re

OUT = "corpus/rows-2026-10-01-steps-{}.jsonl"
MAX_BYTES = 45_000_000
OUTPUT_GLOBS = ("submissions/2026-*/outputs", "experiments/2026-*/outputs")

# External kernels: kernel-metadata.json whose id owner is not habanwer.
KERNEL_META_GLOB = "**/kernel-metadata.json"
OWN_USER = "habanwer"

SECTION = re.compile(r"(?m)^\[([A-Z][A-Za-z :_]+)\]\s*$")
CODE = re.compile(r"(?s)<parameter=code>\n?(.*?)\n?</parameter>")
META_KEYS = ("finish_reason", "tool_call_count", "content_chars", "reasoning_chars")


def sections(transcript: str) -> list[tuple[str, str]]:
    parts = SECTION.split(transcript)
    return [(parts[i], parts[i + 1].strip("\n")) for i in range(1, len(parts), 2)]


def parse_analysis(transcript: str) -> dict:
    reasoning, code, meta, status = [], [], [], {}
    for name, body in sections(transcript):
        if name == "THINKING":
            reasoning.append(body)
        elif name.startswith("TOOL CALL"):
            code.extend(CODE.findall(body) or [body])
        elif name == "MODEL RESPONSE META":
            m = {}
            for line in body.splitlines():
                k, _, v = line.partition(": ")
                if k in META_KEYS:
                    m[k] = int(v) if v.isdigit() else v
            meta.append(m)
        elif name == "ANALYZER STATUS":
            for line in body.splitlines():
                k, _, v = line.partition(": ")
                if k in ("model", "step_executed", "message"):
                    status[k] = v
    return {"reasoning": reasoning, "tool_code": code, "response_meta": meta, "status": status}


def kernel_rows() -> list[dict]:
    rows = []
    metas = sorted(p for p in glob.glob(KERNEL_META_GLOB, recursive=True) if "/.git/" not in p)
    for p in metas:
        m = json.load(open(p))
        if m.get("id", "").split("/")[0] == OWN_USER:
            continue
        d = os.path.dirname(p)
        nb = os.path.join(d, m["code_file"])
        trace = sorted(glob.glob(os.path.join(d, "outputs", "**", "*_events.jsonl"), recursive=True))
        n = len(rows) + 1
        rows.append({
            "id": f"PD-K{n:02d}",
            "family": "external_kernel",
            "kind": "public_demo",
            "source": "repo_file",
            "path": nb,
            "assertion": (
                f"External public kernel {m['id']} (title {m.get('title')!r}) stored at {nb}. "
                + ("Has a trace in outputs/: replayer test." if trace else "No trace in outputs/: notebook row.")
                + " The file states no public score."
            ),
            "split": "public_demo",
            "links": [],
            "revoke_if": None,
            "kernel_ref": m["id"],
            "metadata_path": p,
            "row_role": "replayer_test" if trace else "notebook",
            "trace_paths": trace,
            "public_score": None,
            "heldout_evidence": False,
            "training_target": False,
        })
    return rows


def step_rows(summary: dict) -> list[dict]:
    rows = []
    outs = sorted(sum((glob.glob(g) for g in OUTPUT_GLOBS), []))
    for fi, out in enumerate(outs, 1):
        run = out.split("/")[1]
        in_submissions = out.startswith("submissions/")
        bench_path = f"{out}/benchmark.json"
        fsum = {"folder": out, "actions": 0, "game_runs": 0, "game_runs_empty": 0}
        summary["folders"].append(fsum)
        if not os.path.exists(bench_path):
            fsum["note"] = "no benchmark.json; no stored actions"
            continue
        bench = json.load(open(bench_path))
        game_runs = bench["game_runs"]
        n_passes = bench.get("n_passes") or 1
        per_pass = len(game_runs) // n_passes
        fsum["game_runs"] = len(game_runs)
        for gi, gr in enumerate(game_runs):
            hist = gr.get("history") or []
            if not hist:
                fsum["game_runs_empty"] += 1
                continue
            game, pss = gr["game_id"], gi // per_pass
            ev_path = glob.glob(f"{out}/**/{game}_p{pss}_events.jsonl", recursive=True)
            assert len(ev_path) == 1, (out, game, pss, ev_path)
            ev_path = ev_path[0]
            events = [(ln, json.loads(l)) for ln, l in enumerate(open(ev_path), 1)]
            acts = [(ln, e) for ln, e in events if e["type"] == "action"]
            assert len(acts) == len(hist), (ev_path, len(acts), len(hist))
            for (ln, e), h in zip(acts, hist):
                assert e["action_name"] == h["action"]["id"], (ev_path, ln)
            by_step = collections.defaultdict(list)
            for ln, e in events:
                if e["type"] == "analysis":
                    by_step[e["analysis_step"]].append((ln, e))
            act_steps = {e["analysis_step"] for _, e in acts}
            summary["analysis_events_without_action"] += sum(
                len(v) for k, v in by_step.items() if k not in act_steps)
            first_of_step: dict = {}
            for i, ((ln, e), h) in enumerate(zip(acts, hist)):
                rid = f"ST-{fi:02d}-{game.split('-')[0]}-p{pss}-{e['action_num']:04d}"
                step = e["analysis_step"]
                row = {
                    "id": rid,
                    "family": "duck_taaf_save",
                    "kind": "step",
                    "source": "repo_file",
                    "path": ev_path,
                    "assertion": (f"Stored action {e['action_num']} ({e['action_name']}) of {game} "
                                  f"pass {pss} in {out}"),
                    "split": "public_demo",
                    "links": [],
                    "revoke_if": None,
                    "row_role": "replayer_test",
                    "run_folder": out.rsplit("/", 1)[0],
                    "scored_play": False,
                    "heldout_evidence": False,
                    "training_target": False,
                    "event_line": ln,
                    "benchmark_path": bench_path,
                    "game_run_index": gi,
                    "history_index": i,
                    "game_id": game,
                    "pass": pss,
                    "action_num": e["action_num"],
                    "action_name": e["action_name"],
                    "action_data": h["action"].get("data"),
                    "action_display": e.get("action_display"),
                    "level": e.get("level"),
                    "state": e.get("state"),
                    "score": e.get("score"),
                    "reward": e.get("reward"),
                    "board_changed": e.get("board_changed"),
                    "level_completed": e.get("level_completed"),
                    "game_over": e.get("game_over"),
                    "done": e.get("done"),
                    "generated_tokens": h.get("generated_tokens"),
                    "uncached_input_tokens": h.get("uncached_input_tokens"),
                    "wallclock_seconds": h.get("wallclock_seconds"),
                    "analysis_step": step,
                }
                if in_submissions:
                    row["note"] = ("Public-game save run stored in a scored folder's outputs/; "
                                   "not the scored play. The folder's public score does not apply to this row.")
                if step in first_of_step:
                    row["reasoning_ref"] = first_of_step[step]
                else:
                    first_of_step[step] = rid
                    ans = by_step.get(step, [])
                    parsed = [parse_analysis(a["transcript"]) for _, a in ans]
                    row["analysis_event_lines"] = [l for l, _ in ans]
                    row["reasoning"] = [r for p in parsed for r in p["reasoning"]]
                    row["tool_code"] = [c for p in parsed for c in p["tool_code"]]
                    row["response_meta"] = [m for p in parsed for m in p["response_meta"]]
                    row["analyzer_status"] = [p["status"] for p in parsed]
                    summary["reasoning_chars"] += sum(map(len, row["reasoning"]))
                    summary["tool_code_chars"] += sum(map(len, row["tool_code"]))
                rows.append(row)
            fsum["actions"] += len(acts)
    return rows


def main() -> None:
    summary = {"folders": [], "analysis_events_without_action": 0, "reasoning_chars": 0, "tool_code_chars": 0}
    krows = kernel_rows()
    srows = step_rows(summary)
    ids = [r["id"] for r in krows + srows]
    assert len(ids) == len(set(ids))
    shards, size = [[]], 0
    for r in krows + srows:
        line = (json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
        if size + len(line) > MAX_BYTES:
            shards.append([])
            size = 0
        shards[-1].append(line)
        size += len(line)
    for n, lines in enumerate(shards, 1):
        with open(OUT.format(n), "wb") as f:
            f.writelines(lines)
    summary["files"] = {OUT.format(n): len(lines) for n, lines in enumerate(shards, 1)}
    summary.update(kernel_rows=len(krows), step_rows=len(srows),
                   step_rows_with_reasoning=sum("reasoning" in r for r in srows))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
