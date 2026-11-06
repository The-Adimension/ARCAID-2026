# Depth report: where does the agent stall, and was it starved or stuck?
import json as _json
from collections import Counter as _Counter

_p = WORKING_DIR / 'benchmark.json'
if not _p.exists():
    print('ARC3_DEPTH_RESULT no benchmark.json', flush=True)
else:
    _b = _json.loads(_p.read_text(encoding='utf-8'))
    _rows = []
    _acts = _dec = _tok = 0
    _sizes = []
    for _r in _b['game_runs']:
        _apl = _r.get('actions_per_level') or []
        _hum = _r.get('base_actions_per_level') or []
        _done = _r.get('levels_completed', 0)
        # the level it stopped on (0-indexed = _done), and what it spent there
        _spent = _apl[_done] if _done < len(_apl) else 0
        _base = _hum[_done] if _done < len(_hum) else 0
        _rows.append({
            'game': _r['game_id'][:4],
            'levels_cleared': _done,
            'actions_per_level': _apl[:max(_done + 1, 1)],
            'human_per_level': _hum[:max(_done + 1, 1)],
            'stuck_on_level': _done + 1,
            'actions_spent_there': _spent,
            'human_baseline_there': _base,
            'spend_ratio_vs_human': round(_spent / _base, 2) if _base else None,
            'total_actions': sum(_apl),
            'state': _r.get('state'),
            'wallclock_s': round(_r.get('final_wallclock_seconds', 0)),
        })
        _cur = 0
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
    _starved = [r['game'] for r in _rows if (r['spend_ratio_vs_human'] or 0) < 0.8]
    _stuck = [r['game'] for r in _rows if (r['spend_ratio_vs_human'] or 0) >= 1.5]
    print('ARC3_DEPTH_RESULT ' + _json.dumps({
        'per_game': _rows,
        'levels_total': sum(r['levels_cleared'] for r in _rows),
        'actions': _acts,
        'decisions': _dec,
        'actions_per_decision': round(_acts / max(_dec, 1), 3),
        'singleton_share': round(_c[1] / max(len(_sizes), 1), 3),
        'tokens_per_action': round(_tok / max(_acts, 1), 1),
        'batch_sizes': dict(sorted(_c.items())),
        'VERDICT_starved_games': _starved,
        'VERDICT_stuck_games': _stuck,
    }, sort_keys=True), flush=True)
    print(flush=True)
    print('%-6s %-7s %-9s %-9s %-8s %s' % ('game', 'cleared', 'stuck_on', 'spent', 'human', 'ratio'), flush=True)
    for _r in _rows:
        print('%-6s %-7d %-9d %-9d %-8d %s' % (
            _r['game'], _r['levels_cleared'], _r['stuck_on_level'],
            _r['actions_spent_there'], _r['human_baseline_there'],
            _r['spend_ratio_vs_human']), flush=True)
