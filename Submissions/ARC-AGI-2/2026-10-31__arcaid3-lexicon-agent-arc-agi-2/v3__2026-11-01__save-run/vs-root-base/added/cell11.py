%%writefile /kaggle/working/agent/run_submit.py
"""Competition run: the REPL agent on the hidden test set, writing submission.json.

    python run_submit.py '<json config>'

Safety first, because a crashed rerun wastes a day's submission:
  * the notebook writes a valid FALLBACK submission (each test input copied into
    both attempts) before anything heavy runs, via write_fallback();
  * as every attempt finishes, the submission is rewritten atomically with the
    best answers so far;
  * the agent stops at a hard deadline well inside the 12 h limit.

Budget: the per-attempt token cap is the estimated token supply (throughput x
time) divided by the number of hidden tasks, clamped -- the task count is only
known at run time (the public placeholder has 240).
"""
import glob
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from client import ChatClient                      # noqa: E402
from repl_agent import solve_repl, AGENT_OPTS      # noqa: E402

SUB = "/kaggle/working/submission.json"


def find(name, root="/kaggle/input"):
    hits = glob.glob(f"{root}/**/{name}", recursive=True)
    if not hits:
        raise FileNotFoundError(name)
    return hits[0]


def write_atomic(obj, path=SUB):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


def write_fallback(challenges, path=SUB):
    """A valid submission with no model at all: every attempt is the test input."""
    write_atomic({t: [{"attempt_1": x["input"], "attempt_2": x["input"]} for x in task["test"]]
                  for t, task in challenges.items()}, path)


def ranked_answers(records, task):
    """Per test input: candidate grids best first. Verified programs vote; then the
    unverified programs by train examples reproduced. Mirrors agent.aggregate."""
    out = []
    ntr = len(task["train"])
    for j in range(len(task["test"])):
        score = {}
        grids = {}
        for r in records:
            for p in r["programs"]:
                g = p["test"][j] if j < len(p["test"]) else None
                if g is None:
                    continue
                k = json.dumps(g)
                grids[k] = g
                verified = p["n_ok"] == ntr
                s = score.get(k, (0, 0, 0))
                score[k] = (s[0] + verified, max(s[1], p["n_ok"]), s[2] + 1)
        out.append([grids[k] for k in sorted(score, key=lambda k: score[k], reverse=True)])
    return out


def direct(cfg, tasks, client, deadline, sub, sub_path, t0):
    """Direct answers (run_direct.answer): every task's sample 0 before any sample 1, each
    task in `tasks` order. attempt_1 = the first answer; attempt_2 = the next DIFFERENT one."""
    from run_direct import answer
    lock = threading.Lock()
    got = {}
    jobs = [(t, k) for k in range(cfg.get("samples", 2)) for t in tasks]
    log = open(cfg.get("log_path", "/kaggle/working/direct_attempts.jsonl"), "a")
    count = {}

    def work(job):
        t, k = job
        if deadline - time.time() < cfg.get("min_start_s", 600):
            rec = {"status": "skipped: deadline", "grids": None, "gen_tokens": 0}
        else:
            ts = time.time()
            rec = answer(client, tasks[t], 1000 * k + 7, deadline, max_tokens=cfg.get("max_tokens"),
                         rescue_tokens=cfg.get("rescue_tokens", 8192))
            rec["wall"] = round(time.time() - ts, 1)
        with lock:
            if rec["grids"]:
                got.setdefault(t, []).append(rec["grids"])
                for j, x in enumerate(tasks[t]["test"]):
                    cands = []
                    for grids in got[t]:
                        if grids[j] not in cands:
                            cands.append(grids[j])
                    sub[t][j] = {"attempt_1": cands[0],
                                 "attempt_2": cands[1] if len(cands) > 1 else x["input"]}
                write_atomic(sub, sub_path)
            st = rec["status"].split(":")[0]
            count[st] = count.get(st, 0) + 1
            log.write(json.dumps(dict({k2: v for k2, v in rec.items() if k2 != "grids"},
                                      task_id=t, sample=k)) + "\n")
            log.flush()
            print(f"[{time.time() - t0:6.0f}s] {t}#{k} {rec['status'][:40]:12s} "
                  f"tok {rec.get('gen_tokens', 0):6d} finish {rec.get('finish')} | {count}", flush=True)

    with ThreadPoolExecutor(max_workers=cfg.get("concurrency", 10)) as ex:
        list(ex.map(work, jobs))
    log.close()
    print(f"done: {len(got)}/{len(tasks)} tasks answered, {count}, {time.time() - t0:.0f}s", flush=True)


def main(cfg):
    t0 = time.time()
    rerun = os.environ.get("KAGGLE_IS_COMPETITION_RERUN", "").strip().lower() in {"1", "true"}
    sub_path = cfg.get("sub_path", SUB)
    ch = json.load(open(find(cfg.get("challenges", "arc-agi_test_challenges.json"),
                             cfg.get("data_dir", "/kaggle/input"))))
    if not rerun and not cfg.get("full_interactive"):
        # Interactive run (should not happen -- versions are Quick Saved): stay tiny.
        ch = {t: ch[t] for t in sorted(ch)[:cfg.get("interactive_tasks", 3)]}
    if not os.path.exists(sub_path):
        write_fallback(ch, sub_path)
    n = len(ch)
    deadline = cfg["deadline_epoch"]
    avail = max(0.0, deadline - time.time())
    supply = cfg.get("tok_per_s", 140) * avail
    cap = int(min(cfg.get("max_cap", 60000), max(cfg.get("min_cap", 15000), supply / max(n, 1) * 1.3)))
    print(f"rerun={rerun} tasks={n} available {avail / 3600:.2f} h, est supply {supply / 1e6:.1f}M "
          f"tokens -> per-attempt cap {cap}", flush=True)

    # Cheapest prompts first: if the deadline bites, the long tasks are the ones lost.
    order = sorted(ch, key=lambda t: len(json.dumps(ch[t])))
    tasks = {t: ch[t] for t in order}
    client = ChatClient(cfg["base_url"], cfg["model"], max_tokens=cfg.get("max_tokens", 16384),
                        temperature=cfg.get("temperature", 0.6), top_p=cfg.get("top_p", 0.95),
                        top_k=cfg.get("top_k", 20), thinking=cfg.get("thinking", True),
                        reasoning_effort=cfg.get("reasoning_effort"),
                        thinking_token_budget=cfg.get("thinking_token_budget"),
                        template_kwargs=cfg.get("template_kwargs"))

    sub = json.load(open(sub_path))
    if cfg.get("mode") == "direct":
        return direct(cfg, tasks, client, deadline, sub, sub_path, t0)

    # Hybrid (cfg["repl_share"] < 1): the REPL agent gets that share of the time and of the
    # token supply; the rest answers the tasks it left unverified in direct mode.
    share = min(1.0, cfg.get("repl_share", 1.0))
    if share < 1.0:
        cap = int(min(cfg.get("max_cap", 60000),
                      max(cfg.get("min_cap", 15000), supply * share / max(n, 1) * 1.3)))
        print(f"hybrid: REPL share {share:.2f} -> per-attempt cap {cap}", flush=True)
    repl_deadline = time.time() + avail * share
    opts = {k: cfg[k] for k in AGENT_OPTS if k in cfg and k not in ("turn_max_tokens", "in_python")}
    if cfg.get("restart_frac"):
        opts["restart_at"] = int(cap * cfg["restart_frac"])

    lock = threading.Lock()
    done, direct_grids = {}, {}

    def publish(tid):
        """Rewrite one task's rows: verified programs, then the direct answer, then the
        unverified programs (cfg["direct_first"]=False puts the direct answer last)."""
        task = tasks[tid]
        recs = done.get(tid, [])
        ntr = len(task["train"])
        for j, cands in enumerate(ranked_answers(recs, task)):
            ver = {json.dumps(p["test"][j]) for r in recs for p in r["programs"]
                   if p["n_ok"] == ntr and j < len(p["test"]) and p["test"][j] is not None}
            top = [g for g in cands if json.dumps(g) in ver]
            rest = [g for g in cands if json.dumps(g) not in ver]
            d = direct_grids.get(tid)
            if d is not None and j < len(d) and d[j] not in cands:
                rest = [d[j]] + rest if cfg.get("direct_first", True) else rest + [d[j]]
            order = top + rest
            inp = task["test"][j]["input"]
            sub[tid][j] = {"attempt_1": order[0] if order else inp,
                           "attempt_2": order[1] if len(order) > 1 else inp}
        write_atomic(sub, sub_path)

    def on_done(rec):
        with lock:
            done.setdefault(rec["task_id"], []).append(rec)
            publish(rec["task_id"])

    _, report = solve_repl(
        tasks, client, attempts=cfg.get("attempts", 1), concurrency=cfg.get("concurrency", 24),
        deadline=repl_deadline, stop_after=1, max_turns=cfg.get("max_turns", 40), max_gen_tokens=cap,
        context_budget=cfg.get("context_budget", 24000), nudge_every=cfg.get("nudge_every", 0),
        turn_max_tokens=cfg.get("turn_max_tokens"), in_python=cfg.get("in_python", False),
        log=lambda m: print(m, flush=True), on_done=on_done, **opts)

    ver_tasks = {a["task_id"] for a in report["attempts"] if a["status"] == "verified"}
    print(f"done: {len(ver_tasks)}/{n} tasks verified, "
          f"{sum(a['gen_tokens'] for a in report['attempts'])} tokens, "
          f"restarts {sum(a.get('restarts', 0) for a in report['attempts'])}, {time.time() - t0:.0f}s",
          flush=True)
    if share >= 1.0:
        return

    from run_direct import answer
    # Direct answers think in one long turn: their own thinking budget and effort, not the
    # agent's per-turn cap.
    dclient = ChatClient(cfg["base_url"], cfg["model"], max_tokens=cfg.get("direct_max_tokens", 32768),
                         temperature=cfg.get("temperature", 0.6), top_p=cfg.get("top_p", 0.95),
                         top_k=cfg.get("top_k", 20), thinking=cfg.get("thinking", True),
                         thinking_token_budget=cfg.get("direct_thinking_token_budget",
                                                       cfg.get("thinking_token_budget")),
                         template_kwargs=cfg.get("direct_template_kwargs", cfg.get("template_kwargs")),
                         timeout=4 * 3600)
    todo = [t for t in tasks if t not in ver_tasks]
    print(f"direct pass on {len(todo)} unverified tasks, {(deadline - time.time()) / 3600:.2f} h left",
          flush=True)
    count = {}

    def work(t):
        if deadline - time.time() < cfg.get("min_start_s", 600):
            st = "skipped: deadline"
        else:
            rec = answer(dclient, tasks[t], 7, deadline, rescue_tokens=cfg.get("rescue_tokens", 8192))
            st = rec["status"]
            if rec["grids"]:
                with lock:
                    direct_grids[t] = rec["grids"]
                    publish(t)
        with lock:
            count[st.split(":")[0]] = count.get(st.split(":")[0], 0) + 1
            print(f"[{time.time() - t0:6.0f}s] direct {t} {st[:30]} | {count}", flush=True)

    with ThreadPoolExecutor(max_workers=cfg.get("direct_concurrency", 10)) as ex:
        list(ex.map(work, todo))
    print(f"direct pass done: {count}, {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main(json.loads(sys.argv[1]))
