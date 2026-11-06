# Never let the printout fail a run (this cell also runs in the competition rerun).
def _arc3_eval():
    # v5 evaluation printout (replaces v3's completion-only "RHAE" table).
    # Score = frozen scorer per game (benchmark.json final_score == score.json). Efficiency =
    # actions on cleared levels / human baseline on those levels. vLLM concurrency from the
    # server log, token totals from the final metrics scrape, history depth from the transcripts.
    # Baselines: v3, v4 and v4A save runs, same 6 games, 3600 s, concurrency 6, same serving.
    import json as _json
    import re as _re
    import statistics as _stat

    ARC3_BASELINES = {
        "v3 (LB 3.59)": {"score": 25.08, "levels": 19, "eff": 0.72, "gen_tokens": 880744, "avg_prompt": 21494,
                         "running": 3.07, "waiting": 2.65, "history": 23.9, "preemptions": 17},
        "v4 (unsub.)": {"score": 16.23, "levels": 19, "eff": 1.41, "gen_tokens": 881771, "avg_prompt": 21801,
                        "running": 3.04, "waiting": 2.53, "history": 22.8, "preemptions": 14},
        "v4A (unsub.)": {"score": 13.41, "levels": 15, "eff": 2.26, "gen_tokens": 977801, "avg_prompt": 15627,
                         "running": 3.63, "waiting": 1.08, "history": 17.8, "preemptions": 53},
    }

    try:
        import arc3_stall as _st
        _stall = dict(_st.STATS)
    except Exception as _e:
        _stall = {"error": repr(_e)}
    try:
        import arc3_compact as _ac
        _compact = dict(_ac.STATS)
    except Exception as _e:
        _compact = {"error": repr(_e)}

    _eval = {}
    _bp = WORKING_DIR / "benchmark.json"
    if _bp.exists():
        _b = _json.loads(_bp.read_text(encoding="utf-8"))
        _rows = []
        for _r in _b["game_runs"]:
            _apl, _base, _done = _r["actions_per_level"], _r["base_actions_per_level"] or [], _r["levels_completed"]
            _clr = sum(_apl[:_done])
            _hum = sum(_base[:_done]) if _base else 0
            _tok = sum((_h.get("generated_tokens") or 0) for _h in _r["history"])
            _dec = sum(1 for _h in _r["history"] if (_h.get("generated_tokens") or 0) > 0)
            _rows.append({
                "game": _r["game_id"][:4], "levels": _done, "of": _r["number_of_levels"],
                "score": round(float(_r["final_score"] or 0.0), 2),
                "cleared_actions": _clr, "human": _hum,
                "eff": round(_clr / _hum, 2) if _hum else None,
                "wall_actions": sum(_apl[_done:]), "actions": sum(_apl),
                "gen_tokens": _tok, "decisions": _dec, "state": _r.get("state"),
            })
        _n = max(1, len(_rows))
        _clr_all = sum(r["cleared_actions"] for r in _rows)
        _hum_all = sum(r["human"] for r in _rows)
        _eval.update({
            "score": round(sum(r["score"] for r in _rows) / _n, 2),
            "levels": sum(r["levels"] for r in _rows),
            "eff": round(_clr_all / _hum_all, 2) if _hum_all else None,
            "actions": sum(r["actions"] for r in _rows),
            "actions_per_decision": round(sum(r["actions"] for r in _rows) / max(1, sum(r["decisions"] for r in _rows)), 2),
        })
        for r in _rows:
            if r["game"] == "ar25":
                _eval["ar25"] = r["score"]
                _eval["ar25_levels"] = r["levels"]
        print("%-5s %-7s %-7s %-16s %-6s %-6s %-8s %s" % ("game", "levels", "score", "cleared/human", "eff", "wall", "gen_tok", "state"), flush=True)
        for r in _rows:
            print("%-5s %d/%-5d %-7.2f %4d/%-11d %-6s %-6d %-8d %s" % (
                r["game"], r["levels"], r["of"], r["score"], r["cleared_actions"], r["human"],
                r["eff"], r["wall_actions"], r["gen_tokens"], r["state"]), flush=True)
    else:
        print("ARC3_EVAL no benchmark.json", flush=True)

    _mp = WORKING_DIR / "vllm-metrics-final.prom"
    if _mp.exists():
        _m = {}
        for _line in _mp.read_text(errors="replace").splitlines():
            _mm = _re.match(r"^(vllm:[a-z_]+)(?:\{[^}]*\})?\s+([0-9.eE+-]+)$", _line)
            if _mm and _mm.group(1) not in _m:
                _m[_mm.group(1)] = float(_mm.group(2))
        _cnt = _m.get("vllm:request_prompt_tokens_count") or _m.get("vllm:e2e_request_latency_seconds_count") or 0
        _eval.update({
            "gen_tokens": int(_m.get("vllm:generation_tokens_total", 0)),
            "avg_prompt": int(_m.get("vllm:prompt_tokens_total", 0) / _cnt) if _cnt else None,
            "requests": int(_cnt),
            "preemptions": int(_m.get("vllm:num_preemptions_total", 0)),
        })

    _lp = WORKING_DIR / "vllm-openai-server.log"
    if _lp.exists():
        _run, _wait, _kv = [], [], []
        _log = _lp.read_text(errors="replace")
        for _mm in _re.finditer(r"Running: (\d+) reqs, Waiting: (\d+) reqs, GPU KV cache usage: ([\d.]+)%", _log):
            _run.append(int(_mm.group(1)))
            _wait.append(int(_mm.group(2)))
            _kv.append(float(_mm.group(3)))
        if _run:
            _eval.update({"running": round(_stat.mean(_run), 2), "waiting": round(_stat.mean(_wait), 2),
                          "kv_usage_pct": round(_stat.mean(_kv), 1)})
        _kvs = _re.search(r"GPU KV cache size: ([\d,]+) tokens", _log)
        _eval["kv_pool_tokens"] = _kvs.group(1) if _kvs else None
        _eval["oom_warnings"] = _log.count("memory allocation failed with OOM")

    _hist = []
    for _tp in sorted((WORKING_DIR / "transcripts").glob("*.txt")):
        _hist += [int(x) for x in _re.findall(r"^history_messages: (\d+)", _tp.read_text(errors="replace"), _re.M)]
    if _hist:
        _eval["history"] = round(_stat.mean(_hist), 1)

    print(flush=True)
    print("ARC3_EVAL " + _json.dumps(_eval, sort_keys=True), flush=True)
    print("ARC3_COMPACT " + _json.dumps(_compact, sort_keys=True), flush=True)
    _cols = ("score", "levels", "eff", "gen_tokens", "avg_prompt", "running", "waiting", "history", "preemptions")
    print("%-14s " % "run" + " ".join("%-11s" % c for c in _cols), flush=True)
    for _name, _v in list(ARC3_BASELINES.items()) + [("v5 (this run)", _eval)]:
        print("%-14s " % _name + " ".join("%-11s" % (_v.get(c),) for c in _cols), flush=True)
    print("stall stats:", _stall, flush=True)

    # Verdict for the save run. Mechanism: prompts at least 20% smaller than v3 with v3's history
    # depth, and more tokens generated. Quality: the failure signature of v4/v4A is efficiency on
    # cleared levels collapsing (1.41x, 2.26x human vs v3's 0.72x) and fewer levels.
    #   SUBMIT = mechanism and quality both pass.
    #   REVIEW = mechanism passes, quality fails on this single noisy pass: submit if the loss sits
    #            in one or two games, hold if efficiency got worse in most games (the v4A pattern).
    #   HOLD   = mechanism failed: the change did not shrink prompts or did not free throughput.
    if not TRUE_SUBMISSION:
        _v3 = ARC3_BASELINES["v3 (LB 3.59)"]
        _mech = {
            "prompt<=0.85*v3": (_eval.get("avg_prompt") or 1e9) <= 0.85 * _v3["avg_prompt"],
            "history>=0.9*v3": (_eval.get("history") or 0) >= 0.9 * _v3["history"],
            "preemptions<40": (_eval.get("preemptions") or 0) < 40,
            "oom==0": (_eval.get("oom_warnings") or 0) == 0,
        }
        _qual = {
            "eff<=1.0": (_eval.get("eff") or 9e9) <= 1.0,
            "levels>=17": (_eval.get("levels") or 0) >= 17,
            "ar25>=v3": (_eval.get("ar25") or 0) >= 27.78,
        }
        _verdict = "HOLD" if not all(_mech.values()) else ("SUBMIT" if all(_qual.values()) else "REVIEW")
        print("ARC3_VERDICT %s mechanism=%s quality=%s" % (_verdict, _json.dumps(_mech), _json.dumps(_qual)), flush=True)


try:
    _arc3_eval()
except Exception as _eval_exc:
    print('ARC3_EVAL failed: %r' % (_eval_exc,), flush=True)
