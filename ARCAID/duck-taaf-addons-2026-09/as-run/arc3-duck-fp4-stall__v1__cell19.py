# Did the warning change behaviour? Compare against depthrun1 (same games, same cap, no stall).
import json as _json
from collections import Counter as _Counter

DEPTH_BASELINE = {'sb26': 1, 'vc33': 3, 'ft09': 4, 'lp85': 5, 're86': 3, 'ar25': 3}

try:
    import arc3_stall as _st
    _stats = dict(_st.STATS)
except Exception as _e:
    _stats = {'error': repr(_e)}

_p = WORKING_DIR / 'benchmark.json'
if not _p.exists():
    print('ARC3_STALL_RESULT no benchmark.json', flush=True)
else:
    _b = _json.loads(_p.read_text(encoding='utf-8'))
    def _key(a):
        d = a.get('data') or {}
        return '%s:%s,%s' % (a['id'], d.get('x'), d.get('y')) if d else a['id']
    _rows = []
    for _r in _b['game_runs']:
        _g = _r['game_id'][:4]
        _apl = _r['actions_per_level']
        _done = _r['levels_completed']
        _cut = sum(_apl[:_done])
        _hist = [h['action'] for h in _r['history']]
        _wall = _hist[_cut:]
        _c = _Counter(_key(a) for a in _wall)
        _rows.append({
            'game': _g,
            'levels': _done,
            'depthrun1_levels': DEPTH_BASELINE.get(_g),
            'delta': _done - DEPTH_BASELINE.get(_g, 0),
            'wall_actions': len(_wall),
            'wall_uniq_frac': round(len(_c) / len(_wall), 3) if _wall else None,
            'wall_top_repeat': _c.most_common(1)[0][1] if _c else 0,
            'total_actions': sum(_apl),
            'state': _r.get('state'),
        })
    print('ARC3_STALL_RESULT ' + _json.dumps({
        'stall_stats': _stats,
        'per_game': _rows,
        'levels_total': sum(r['levels'] for r in _rows),
        'levels_total_depthrun1': sum(DEPTH_BASELINE.values()),
    }, sort_keys=True), flush=True)
    print(flush=True)
    print('%-6s %-8s %-11s %-7s %-13s %-13s %s' % (
        'game', 'levels', 'depthrun1', 'delta', 'wall_actions', 'wall_uniq', 'top_repeat'), flush=True)
    for _r in _rows:
        print('%-6s %-8d %-11s %-7d %-13d %-13s %s' % (
            _r['game'], _r['levels'], _r['depthrun1_levels'], _r['delta'],
            _r['wall_actions'], _r['wall_uniq_frac'], _r['wall_top_repeat']), flush=True)
    print(flush=True)
    print('stall stats:', _stats, flush=True)
    print('READ: wall_uniq_frac UP and top_repeat DOWN vs depthrun1 (0.16/0.10/0.41/0.12/0.02/0.07)', flush=True)
    print('      means the agent broke the loop when told. Unchanged means it CANNOT escape', flush=True)
    print('      and the next version must RESET the level, not just warn.', flush=True)
