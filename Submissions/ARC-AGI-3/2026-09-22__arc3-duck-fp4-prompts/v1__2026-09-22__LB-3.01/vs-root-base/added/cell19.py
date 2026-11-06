# Mechanism check only: did the model write CONFIRMED / ASSUMED ledgers after a failure?
import json as _json
import re as _re

_p = WORKING_DIR / 'benchmark.json'
if _p.exists():
    _b = _json.loads(_p.read_text(encoding='utf-8'))
    for _r in _b['game_runs']:
        print('ARC3_LEDGER_GAME', _r['game_id'], 'levels', _r['levels_completed'],
              'actions_per_level', _r['actions_per_level'], 'state', _r.get('state'), flush=True)
_hits = {'CONFIRMED': 0, 'ASSUMED': 0}
_turns = 0
for _t in sorted((WORKING_DIR / 'transcripts').glob('*.txt')) if (WORKING_DIR / 'transcripts').exists() else []:
    _s = _t.read_text(encoding='utf-8', errors='replace')
    _turns += len(_re.findall(r'(?m)^--- analysis_step=', _s))
    for _th in _re.findall(r'\[THINKING\]\n(.*?)(?=\n\[[A-Z _]+\]\n|\Z)', _s, _re.S):
        for _k in _hits:
            _hits[_k] += len(_re.findall(r'\b' + _k + r'\b', _th))
print('ARC3_LEDGER_RESULT turns=%d ledger_mentions=%s' % (_turns, _hits), flush=True)
