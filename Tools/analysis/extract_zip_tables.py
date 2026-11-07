"""Extract per-turn, per-model-call and per-logged-action tables from the run-output zips.

  HF_TOKEN=<token> python -I extract_zip_tables.py REPO_ROOT WORK_DIR OUT_DIR [--hf-repo ORG/NAME]

Reads Documentation/DATASET-MANIFEST.csv and streams each ARC-AGI-3 zip from the Hugging Face dataset (one at a
time; nothing is unpacked to disk). Per zip it parses, for every game-run:
  transcripts/<game>[_L<k>]_p<N>.txt        -> turns.csv.gz   one row per model turn (analysis_step)
  <game>[_L<k>]_p<N>_requests.jsonl        -> calls.csv.gz   one row per model response (token usage)
  artifacts/<game>[_L<k>]_p<N>_events.jsonl -> events.csv.gz  one row per logged action (turn, batch, flags)
Per-zip results are cached in WORK_DIR, so an interrupted run resumes. Join keys: run_id, game_run, pass,
analysis_step (turn) and action_num (the 1-based action count, as in actions.csv.gz `action_index`).
"""
import argparse, csv, gzip, io, json, re, sys, zipfile
from pathlib import Path
from huggingface_hub import hf_hub_download

MARKERS = {  # code read in the model's python tool calls -> column
    "reads_code": "current_frame.code", "reads_rules": ".rules", "reads_objects": ".objects",
    "reads_native": ".native", "reads_changes_since": ".changes_since", "reads_ascii": ".ascii",
    "reads_segmentation": ".segmentation", "calls_frame_diff": "frame_diff(", "calls_action": "action(",
}
TURN_COLS = ["run_id", "game_run", "pass", "analysis_step", "first_action_num", "requests", "responses",
             "reasoning_chars", "content_chars", "tool_calls", "finish_length", *MARKERS, "user_prompt_chars",
             "pf_nudge", "lexicon_cue", "image_attached"]
CALL_COLS = ["run_id", "game_run", "pass", "analysis_step", "action_num", "request_index_within_turn",
             "prompt_tokens", "cached_tokens", "image_tokens", "completion_tokens", "reasoning_tokens", "finish_reason"]
EVENT_COLS = ["run_id", "game_run", "pass", "action_num", "analysis_step", "action_name", "batch_index", "batch_size",
              "board_changed", "level_completed", "game_over", "level", "score"]
NAME = re.compile(r"(?:^|/)(?P<game>[a-z0-9]{4}-[0-9a-f]{8})(?:_L(?P<lvl>\d+))?_p(?P<p>\d+)")
HEAD = re.compile(r"^--- analysis_step=(\d+) \| action=(\d+) \|", re.M)


def gid(path):
    m = NAME.search(path)
    if not m:
        return None, None
    return m.group("game") + (f"@L{m.group('lvl')}" if m.group("lvl") is not None else ""), int(m.group("p"))


def parse_transcript(text):
    turns = {}
    heads = list(HEAD.finditer(text))
    for i, h in enumerate(heads):
        body = text[h.end(): heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        step, act = int(h.group(1)), int(h.group(2))
        t = turns.setdefault(step, {"analysis_step": step, "first_action_num": act, "requests": 0, "responses": 0,
                                    "reasoning_chars": 0, "content_chars": 0, "tool_calls": 0, "finish_length": 0,
                                    **{k: 0 for k in MARKERS}, "user_prompt_chars": 0, "pf_nudge": 0,
                                    "lexicon_cue": 0, "image_attached": 0})
        t["requests"] += 1
        for meta in re.finditer(r"\[MODEL RESPONSE META\]\n(.*?)(?:\n\n|\n\[)", body, re.S):
            m = meta.group(1); t["responses"] += 1
            for key, col in (("reasoning_chars", "reasoning_chars"), ("content_chars", "content_chars"),
                             ("tool_call_count", "tool_calls")):
                v = re.search(rf"^{key}: (\d+)", m, re.M)
                t[col] += int(v.group(1)) if v else 0
            t["finish_length"] += bool(re.search(r"^finish_reason: length", m, re.M))
        for code in re.findall(r"<parameter=code>\n?(.*?)</parameter>", body, re.S):
            for col, mk in MARKERS.items():
                t[col] += mk in code
        up = re.search(r"\[USER PROMPT\]\n(.*?)(?=\n\[[A-Z][A-Z :]*\]\n|\Z)", body, re.S)
        if up:
            u = up.group(1); t["user_prompt_chars"] += len(u)
            t["pf_nudge"] += "Probe ledger:" in u
            t["lexicon_cue"] += ("print(current_frame.code)" in u) or ("current_frame.rules" in u)
        t["image_attached"] += body.count("[image attached]")
    return turns.values()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo"); ap.add_argument("work"); ap.add_argument("out")
    ap.add_argument("--hf-repo", default="The-Adimension/ARCAID-2026-run-outputs")
    a = ap.parse_args()
    repo, work, out = Path(a.repo), Path(a.work), Path(a.out)
    work.mkdir(parents=True, exist_ok=True); out.mkdir(parents=True, exist_ok=True)
    rows = [r for r in csv.DictReader(open(repo / "Documentation/DATASET-MANIFEST.csv")) if r["file"].startswith("ARC-AGI-3")]
    for r in rows:
        run_id = r["file"][len("ARC-AGI-3__"):-4].replace("__v", "@v")
        part = work / f"{run_id}.json"
        if part.exists():
            continue
        zpath = hf_hub_download(a.hf_repo, r["huggingface_path"], repo_type="dataset", local_dir=str(work / "dl"))
        turns, calls, events = [], [], []
        with zipfile.ZipFile(zpath) as z:
            for name in z.namelist():
                g, p = gid(name)
                if g is None:
                    continue
                if name.startswith("transcripts/") and name.endswith(".txt"):
                    for t in parse_transcript(z.read(name).decode("utf-8", "replace")):
                        turns.append({"run_id": run_id, "game_run": g, "pass": p, **t})
                elif name.endswith("_requests.jsonl") and "/" not in name:
                    for line in io.TextIOWrapper(z.open(name), encoding="utf-8", errors="replace"):
                        try:
                            q = json.loads(line)
                        except Exception:
                            continue
                        if q.get("event") != "response":
                            continue
                        u = q.get("usage") or {}; d = u.get("prompt_tokens_details") or {}
                        calls.append({"run_id": run_id, "game_run": g, "pass": p, "analysis_step": q.get("analysis_step"),
                                      "action_num": q.get("action"), "request_index_within_turn": q.get("request_index_within_turn"),
                                      "prompt_tokens": u.get("prompt_tokens"), "cached_tokens": d.get("cached_tokens"),
                                      "image_tokens": d.get("image_tokens"), "completion_tokens": u.get("completion_tokens"),
                                      "reasoning_tokens": u.get("reasoning_tokens"), "finish_reason": q.get("finish_reason")})
                elif name.startswith("artifacts/") and name.endswith("_events.jsonl"):
                    for line in io.TextIOWrapper(z.open(name), encoding="utf-8", errors="replace"):
                        try:
                            e = json.loads(line)
                        except Exception:
                            continue
                        if e.get("type") != "action":
                            continue
                        events.append({"run_id": run_id, "game_run": g, "pass": p, "action_num": e.get("action_num"),
                                       "analysis_step": e.get("analysis_step"), "action_name": e.get("action_name"),
                                       "batch_index": e.get("batch_index"), "batch_size": e.get("batch_size"),
                                       "board_changed": int(bool(e.get("board_changed"))),
                                       "level_completed": int(bool(e.get("level_completed"))),
                                       "game_over": int(bool(e.get("game_over"))), "level": e.get("level"), "score": e.get("score")})
        Path(zpath).unlink()
        part.write_text(json.dumps({"turns": turns, "calls": calls, "events": events}))
        print(run_id, len(turns), "turns,", len(calls), "calls,", len(events), "events", flush=True)
    for key, cols, fname in (("turns", TURN_COLS, "turns.csv.gz"), ("calls", CALL_COLS, "calls.csv.gz"),
                             ("events", EVENT_COLS, "events.csv.gz")):
        with gzip.open(out / fname, "wt", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols); w.writeheader()
            for part in sorted(work.glob("*.json")):
                for row in json.loads(part.read_text())[key]:
                    w.writerow(row)
    print("tables written to", out)


if __name__ == "__main__":
    main()
