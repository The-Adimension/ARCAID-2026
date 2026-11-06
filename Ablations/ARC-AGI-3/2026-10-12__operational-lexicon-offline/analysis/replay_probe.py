"""Replay Franzen's 4 x 25 demo run and grade what an operational lexicon would have said at every step.

For every non-RESET action it records, before the step is seen:
  - what `predict(action, click)` would answer from the attempt's earlier steps (confident / known no-op /
    unknown) and whether that answer came true on the replayed screen;
  - how many of the step's changes no learned rule explains (the `unexplained_recent()` signal);
  - whether the interior screen (4-cell border removed) was already seen in this attempt (the loop signal).

Needs Python 3.12 with arc-agi==0.9.8 and arcengine==0.9.3. From the repo root:
  python experiments/2026-10-12__lexicon-proposals-offline/replay_probe.py <benchmark.json> <out.jsonl> [workers]
The decision rule is in DECISION_RULE.md; summarize.py reads the output.
"""
from __future__ import annotations

import builtins
import collections
import hashlib
import importlib.util
import json
import logging
import pathlib
import sys
import time
from multiprocessing import Pool

logging.disable(logging.CRITICAL)
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ENV_DIR = ROOT / "inputs/official-input-arc-prize-2026-arc-agi-3/environment_files"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / "src" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


LX = _load("lexicon")
builtins.LX = LX            # rule_grammar takes the lexicon from its host when one is present
G = _load("rule_grammar")
NO_FULL = ("resize",)       # as run_compare.judge_new: these never specify the next screen


def judge(preds, click, events):
    """(predictions right, predictions made, indices of changes fully explained)."""
    right, full = 0, set()
    for _, i, eff in preds:
        ks = {k for k, e in enumerate(events) if G.matches(eff, i, e, click)}
        right += bool(ks)
        if eff[0] not in NO_FULL and not (eff[0] == "appear" and eff[2][0] == "somewhere"):
            full |= ks
    return right, len(preds), full


def interior_hash(frame):
    rows = [tuple(r[4:-4]) for r in frame[4:-4]]
    return hashlib.blake2b(repr(rows).encode(), digest_size=8).hexdigest()


def frame_of(f):
    fr = f.frame[-1]
    return fr.tolist() if hasattr(fr, "tolist") else fr


class Attempt:
    def __init__(self, lex, frame, level, start_tok, start_idx):
        self.lex, self.level, self.start_tok, self.start_idx = lex, level, start_tok, start_idx
        self.frames = [frame]
        self.prev = G.State(LX.encode(frame, lex, lock=LX.scale_lock(self.frames)))
        self.learner = G.Learner()
        self.seen = {interior_hash(frame)}
        self.key_changed = collections.defaultdict(list)
        self.rows = []
        self.n_actions = 0

    def read(self, frame):
        self.frames.append(frame)
        lock = LX.scale_lock(self.frames)
        prev = self.prev
        cur = G.State(LX.encode(frame, self.lex, lock=lock, prev=prev.code))
        if (prev.code["scale"], prev.code["offset"]) != (cur.code["scale"], cur.code["offset"]):
            prev = G.State(LX.encode(self.frames[-2], self.lex, lock=lock))
            cur = G.State(LX.encode(frame, self.lex, lock=lock, prev=prev.code))
        return prev, cur

    def step(self, name, data, frame, tok):
        self.n_actions += 1
        h = interior_hash(frame)
        revisit = h in self.seen
        self.seen.add(h)
        prev, cur = self.read(frame)
        row = {"i": self.n_actions, "tok": tok - self.start_tok, "a": name, "loop": revisit}
        if name != "RESET":
            click = (data["x"], data["y"]) if name == "ACTION6" and data else None
            events = G.observe(prev, cur)
            preds, crc = G.predict(self.learner.rules(), prev, name, click)
            right, n, full = judge(preds, crc, events)
            st = G.Step(prev, name, click, [])
            key = (name, prev.objs[st.clicked]["sym"] if st.clicked is not None else "none") if click else (name,)
            past = self.key_changed[key]
            if n:
                answer = "confident"
                good = right == n and len(full) == len(events)
            elif past and not any(past):
                answer = "noop"
                good = not events
            else:
                answer = "unknown"
                good = None
            row.update(ans=answer, good=good, ev=len(events), unexpl=len(events) - len(full),
                       new=len(past) <= 2, npred=n, right=right)
            self.key_changed[key].append(bool(events))
            self.learner.observe(prev, name, click, events)
        self.rows.append(row)
        self.prev = cur


def play(args):
    idx, r = args
    import arc_agi
    from arcengine import GameAction
    t0 = time.time()
    arc = arc_agi.Arcade(operation_mode=arc_agi.OperationMode.OFFLINE, environments_dir=str(ENV_DIR))
    env = arc.make(r["game_id"], seed=0)
    f = env.reset()
    game = env._game
    lex = LX.Lexicon(naming="stable")
    cum, tok = [], 0
    for h in r["history"]:
        tok += h["generated_tokens"]
        cum.append(tok)
    total = max(tok, int((r.get("solver_note") or "tokens=0").split("tokens=")[-1] or 0))
    att = Attempt(lex, frame_of(f), game.level_index, 0, 0)
    out = []
    for j, h in enumerate(r["history"]):
        a = h["action"]
        name, data = a["id"], a.get("data") or None
        f = env.step(GameAction[name], data=data)
        level = game.level_index
        if level != att.level or str(f.state).endswith("WIN"):
            att.n_actions += 1
            out.append(dict(level=att.level, done=level > att.level or str(f.state).endswith("WIN"),
                            actions=att.n_actions, tokens=cum[j] - att.start_tok, rows=att.rows))
            if str(f.state).endswith("WIN"):
                att = None
                break
            att = Attempt(lex, frame_of(f), level, cum[j], j + 1)
            continue
        att.step(name, data, frame_of(f), cum[j])
    if att is not None:
        out.append(dict(level=att.level, done=False, actions=att.n_actions, tokens=total - att.start_tok, rows=att.rows))
    pas = int(r["solver_analysis_html"].split("_p")[-1].split(".")[0])
    return dict(run=idx, game=r["game_id"][:4], pas=pas, levels_completed=r["levels_completed"],
                stored_levels=r["levels_completed"], replay_levels=game.level_index if att is not None else len(r["base_actions_per_level"]),
                base=r["base_actions_per_level"], attempts=out, secs=round(time.time() - t0, 1))


def main():
    src, dst = sys.argv[1], sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    runs = json.load(open(src))["game_runs"]
    only = sys.argv[4].split(",") if len(sys.argv) > 4 else None
    jobs = [(i, r) for i, r in enumerate(runs) if r.get("history") and (only is None or str(i) in only)]
    jobs.sort(key=lambda x: -len(x[1]["history"]))          # longest first, for the pool
    with Pool(workers) as pool, open(dst, "w") as fh:
        for res in pool.imap_unordered(play, jobs, chunksize=1):
            fh.write(json.dumps(res) + "\n")
            fh.flush()
            print(res["run"], res["game"], res["pas"], "levels", res["stored_levels"], "replay", res["replay_levels"],
                  "attempts", len(res["attempts"]), f"{res['secs']}s", flush=True)


if __name__ == "__main__":
    main()
