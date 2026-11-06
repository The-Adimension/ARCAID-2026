# RESET branch. Judge on the five non-sb26 games and on actions, not on the mean.
import json as _json
from collections import Counter as _Counter

# 6-game RHAE, one pass each, same games/cap/profile.
DEPTH1 = {'sb26': 2.78, 'vc33': 21.43, 'ft09': 47.62, 'lp85': 41.67, 're86': 16.67, 'ar25': 16.67}
STALL2 = {'sb26': 77.78, 'vc33': 21.43, 'ft09': 28.57, 'lp85': 41.67, 're86': 16.67, 'ar25': 8.33}

try:
    import arc3_stall as _st
    _stats = dict(_st.STATS)
    _mode = _st.MODE
except Exception as _e:
    _stats, _mode = {'error': repr(_e)}, '?'

_p = WORKING_DIR / 'benchmark.json'
if not _p.exists():
    print('ARC3_RESET_RESULT no benchmark.json', flush=True)
else:
    _b = _json.loads(_p.read_text(encoding='utf-8'))
    def _key(a):
        d = a.get('data') or {}
        return '%s:%s,%s' % (a['id'], d.get('x'), d.get('y')) if d else a['id']
    _rows = []
    _acts = _dec = _tok = 0
    for _r in _b['game_runs']:
        _g = _r['game_id'][:4]
        _apl = _r['actions_per_level']
        _done = _r['levels_completed']
        _N = _r['number_of_levels']
        _cut = sum(_apl[:_done])
        _hist = [h['action'] for h in _r['history']]
        _wall = _hist[_cut:]
        _c = _Counter(_key(a) for a in _wall)
        _rows.append({
            'game': _g,
            'levels': _done,
            'rhae': round(100.0 * sum(range(1, _done + 1)) / (_N * (_N + 1) / 2), 2),
            'actions': sum(_apl),
            'wall_actions': len(_wall),
            'wall_uniq_frac': round(len(_c) / len(_wall), 3) if _wall else None,
            'wall_top_repeat': _c.most_common(1)[0][1] if _c else 0,
            'loop_metric': round(_c.most_common(1)[0][1] / len(_wall), 3) if _wall else None,
            'state': _r.get('state'),
        })
        for _h in _r['history']:
            _t = _h.get('generated_tokens', 0) or 0
            _tok += _t
            _acts += 1
            if _t > 0:
                _dec += 1

    # average the passes per game
    _by = {}
    for _r in _rows:
        _by.setdefault(_r['game'], []).append(_r)
    _mean = {g: sum(r['rhae'] for r in v) / len(v) for g, v in _by.items()}
    _five = [g for g in _mean if g != 'sb26']

    print('ARC3_RESET_RESULT ' + _json.dumps({
        'mode': _mode, 'stall_stats': _stats, 'runs': _rows,
        'rhae_mean_per_game': {g: round(v, 2) for g, v in _mean.items()},
        'mean_all': round(sum(_mean.values()) / len(_mean), 2),
        'mean_without_sb26': round(sum(_mean[g] for g in _five) / len(_five), 2),
        'baseline_depthrun1_all': round(sum(DEPTH1.values()) / 6, 2),
        'baseline_depthrun1_without_sb26': round(sum(v for k, v in DEPTH1.items() if k != 'sb26') / 5, 2),
        'baseline_stallrun2_all': round(sum(STALL2.values()) / 6, 2),
        'baseline_stallrun2_without_sb26': round(sum(v for k, v in STALL2.items() if k != 'sb26') / 5, 2),
        'actions': _acts, 'decisions': _dec,
        'actions_per_decision': round(_acts / max(_dec, 1), 2),
        'tokens_per_action': round(_tok / max(_acts, 1), 1),
    }, sort_keys=True), flush=True)

    print(flush=True)
    print('%-6s %-7s %-7s %-9s %-11s %-12s %s' % (
        'game', 'levels', 'rhae', 'actions', 'wall_act', 'loop_metric', 'state'), flush=True)
    for _r in _rows:
        print('%-6s %-7d %-7s %-9d %-11d %-12s %s' % (
            _r['game'], _r['levels'], _r['rhae'], _r['actions'],
            _r['wall_actions'], _r['loop_metric'], _r['state']), flush=True)
    print(flush=True)
    print('RHAE mean  all 6: %.2f   (depthrun1 %.2f, stallrun2 %.2f)' % (
        sum(_mean.values()) / len(_mean), sum(DEPTH1.values()) / 6, sum(STALL2.values()) / 6), flush=True)
    print('RHAE mean  WITHOUT sb26: %.2f   (depthrun1 %.2f, stallrun2 %.2f)  <-- THE VERDICT' % (
        sum(_mean[g] for g in _five) / len(_five),
        sum(v for k, v in DEPTH1.items() if k != 'sb26') / 5,
        sum(v for k, v in STALL2.items() if k != 'sb26') / 5), flush=True)
    print('loop metric to beat (depthrun1 / stallrun2 means): 0.234 / 0.219', flush=True)
    print('actions %d, a/d %.2f, tok/act %.0f  (depthrun1 1766 / 6.20 / 493; stallrun2 2509 / 6.66 / 328)' % (
        _acts, _acts / max(_dec, 1), _tok / max(_acts, 1)), flush=True)
    print('stall stats:', _stats, flush=True)
