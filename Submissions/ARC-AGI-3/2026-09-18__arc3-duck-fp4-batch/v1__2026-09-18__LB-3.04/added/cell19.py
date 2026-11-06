# Batching metrics. A charged decision is an executed action with generated_tokens > 0;
# the actions that follow it at 0 tokens were folded into that same model decision.
import json as _json
from collections import Counter as _Counter

_p = WORKING_DIR / 'benchmark.json'
if _p.exists():
    _b = _json.loads(_p.read_text(encoding='utf-8'))
    _acts = _dec = _tok = 0
    _sizes = []
    _levels = 0
    for _r in _b['game_runs']:
        _cur = 0
        _levels += _r.get('levels_completed', 0)
        for _h in _r.get('history', []):
            _t = _h.get('generated_tokens', 0) or 0
            _tok += _t
            if _t > 0:
                if _cur:
                    _sizes.append(_cur)
                _cur = 1
                _dec += 1
            else:
                _cur += 1
            _acts += 1
        if _cur:
            _sizes.append(_cur)
    _c = _Counter(_sizes)
    print('ARC3_BATCH_RESULT ' + _json.dumps({
        'actions': _acts,
        'decisions': _dec,
        'actions_per_decision': round(_acts / max(_dec, 1), 3),
        'singleton_share': round(_c[1] / max(len(_sizes), 1), 3),
        'tokens_per_action': round(_tok / max(_acts, 1), 1),
        'levels_completed': _levels,
        'batch_sizes': dict(sorted(_c.items())),
        'baseline_fp4run1': {'actions': 282, 'decisions': 121,
                             'actions_per_decision': 2.33, 'singleton_share': 0.57,
                             'tokens_per_action': 802, 'levels_completed': 7},
    }, sort_keys=True), flush=True)
else:
    print('ARC3_BATCH_RESULT no benchmark.json', flush=True)
