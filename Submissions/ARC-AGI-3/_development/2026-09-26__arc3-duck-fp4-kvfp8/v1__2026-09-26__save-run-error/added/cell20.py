# arc3 v5: throughput readout from the vLLM server log. Scores are too noisy to rank variants;
# throughput under contention is not. bf16 baselines (same stack, 25 games queued):
#   fp4-serving 2026-09-18: running 3.96, waiting 20.73, gen 278 tok/s, KV 105,202 tokens
#   fp4-batch   2026-09-18: running 4.16, waiting 20.56, gen 223 tok/s
import re as _re2
_log = WORKING_DIR / 'vllm-openai-server.log'
if not _log.exists():
    _cands = sorted(WORKING_DIR.rglob('vllm-openai-server.log'))
    _log = _cands[0] if _cands else _log
if not _log.exists():
    print('ARC3_THROUGHPUT no vllm-openai-server.log', flush=True)
else:
    _txt = _log.read_text(encoding='utf-8', errors='replace')
    _kv = _re2.search(r'GPU KV cache size: ([\d,]+) tokens, Maximum concurrency for ([\d,]+) tokens per request: ([\d.]+)x', _txt)
    _dt = _re2.search(r"'kv_cache_dtype': '(\w+)'", _txt)
    _pat = _re2.compile(r'Avg prompt throughput: ([\d.]+) tokens/s, Avg generation throughput: ([\d.]+) tokens/s, '
                        r'Running: (\d+) reqs, Waiting: (\d+) reqs, GPU KV cache usage: ([\d.]+)%')
    _rows = [tuple(float(x) for x in m.groups()) for m in _pat.finditer(_txt)]
    _busy = [r for r in _rows if r[2] > 0]
    def _avg(rows, i):
        return round(sum(r[i] for r in rows) / max(len(rows), 1), 2)
    _first15 = _busy[:90]   # vLLM logs every 10 s
    _acc = [float(x) for x in _re2.findall(r'Mean acceptance length: ([\d.]+)', _txt)]
    print('ARC3_THROUGHPUT ' + json.dumps({
        'kv_cache_dtype_arg': _dt.group(1) if _dt else 'auto(not passed)',
        'kv_tokens': _kv.group(1) if _kv else None,
        'kv_max_concurrency_32k': _kv.group(3) if _kv else None,
        'intervals': len(_busy),
        'all': {'running': _avg(_busy, 2), 'waiting': _avg(_busy, 3),
                'gen_tok_s': _avg(_busy, 1), 'prompt_tok_s': _avg(_busy, 0), 'kv_pct': _avg(_busy, 4)},
        'first_15min': {'running': _avg(_first15, 2), 'waiting': _avg(_first15, 3),
                        'gen_tok_s': _avg(_first15, 1), 'kv_pct': _avg(_first15, 4)},
        'mtp_mean_acceptance': round(sum(_acc) / max(len(_acc), 1), 3),
        'baseline_bf16_fp4serving': {'running': 3.96, 'waiting': 20.73, 'gen_tok_s': 278, 'kv_tokens': '105,202'},
    }, sort_keys=True), flush=True)
