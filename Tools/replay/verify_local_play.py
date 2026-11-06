"""Replay local_play/*/full_actions.json on the official public game files and score them.

Needs Python 3.12 with arc-agi==0.9.8 and arcengine==0.9.3 (the competition-pinned versions).
"""
import json, logging, os
logging.disable(logging.CRITICAL)
import arc_agi
from arcengine import GameAction
import pathlib
HERE = pathlib.Path(__file__).resolve().parent
ENV = str(HERE / 'official-input-arc-prize-2026-arc-agi-3' / 'environment_files')
LP = str(HERE / 'local_play')
arc=arc_agi.Arcade(operation_mode=arc_agi.OperationMode.OFFLINE, environments_dir=ENV)
ids={e.game_id[:4]:e.game_id for e in arc.available_environments}
meta={}
for g in os.listdir(ENV):
    for v in os.listdir(f'{ENV}/{g}'):
        meta[g]=json.load(open(f'{ENV}/{g}/{v}/metadata.json'))
def score(apl, base, done):
    N=len(base); W=N*(N+1)/2
    s=sum((i+1)*min((base[i]/apl[i])**2*100,115) for i in range(done) if apl[i]>0)/W
    return min(s, sum(range(1,done+1))/W*100)
for g in sorted(os.listdir(LP)):
    p=f'{LP}/{g}/full_actions.json'
    if not os.path.exists(p): continue
    acts=json.load(open(p))
    env=arc.make(ids[g], seed=0); f=env.reset()
    base=meta[g]['baseline_actions']; apl=[0]*len(base); lvl=0
    for a in acts:
        ga=GameAction.from_id(a['id'])
        f=env.step(ga, data=({'x':a['x'],'y':a['y']} if 'x' in a else None))
        apl[lvl]+=1
        if f.levels_completed>lvl: lvl=f.levels_completed
        if str(f.state).endswith(('WIN','GAME_OVER')): break
    print(g, 'replayed', len(acts),'actions ->', f.state, f.levels_completed,'/',f.win_levels, '| per-level actions', apl[:lvl+1], 'vs human', base[:lvl+1], '| RHAE %.2f'%score(apl,base,f.levels_completed))
