# Never let the printout fail a run (this cell also runs in the competition rerun).
def _arc3_eval():
    # v4A evaluation printout (replaces v3's completion-only "RHAE" table).
    # Score = frozen scorer per game (benchmark.json final_score == score.json). Efficiency =
    # actions on cleared levels / human baseline on those levels. vLLM concurrency from the
    # server log, token totals from the final metrics scrape. Baselines: v3 and v4 save runs,
    # same 6 games, 3600 s, concurrency 6, same serving profile.
    import json as _json
    import re as _re
    import statistics as _stat

    ARC3_BASELINES = {
        "v3 (LB 3.59)": {"score": 25.08, "levels": 19, "eff": 0.72, "gen_tokens": 880744,
                         "avg_prompt": 21494, "running": 3.07, "waiting": 2.65},
        "v4 (unsub.)": {"score": 16.23, "levels": 19, "eff": 1.41, "gen_tokens": 881771,
                        "avg_prompt": 21801, "running": 3.04, "waiting": 2.53},
    }

    try:
        import arc3_stall as _st
        _stall = dict(_st.STATS)
    except Exception as _e:
        _stall = {"error": repr(_e)}

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
        _cnt = _m.get("vllm:request_prompt_tokens_count") or 0
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

    print(flush=True)
    print("ARC3_EVAL " + _json.dumps(_eval, sort_keys=True), flush=True)
    print("%-14s %-7s %-7s %-6s %-11s %-10s %-8s %s" % ("run", "score", "levels", "eff", "gen_tokens", "avg_prompt", "running", "waiting"), flush=True)
    for _name, _v in list(ARC3_BASELINES.items()) + [("v4A (this run)", _eval)]:
        print("%-14s %-7s %-7s %-6s %-11s %-10s %-8s %s" % (
            _name, _v.get("score"), _v.get("levels"), _v.get("eff"), _v.get("gen_tokens"),
            _v.get("avg_prompt"), _v.get("running"), _v.get("waiting")), flush=True)
    print("stall stats:", _stall, flush=True)


try:
    _arc3_eval()
except Exception as _eval_exc:
    print('ARC3_EVAL failed: %r' % (_eval_exc,), flush=True)
