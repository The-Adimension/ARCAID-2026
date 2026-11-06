"""Replay a save run's benchmark.json action histories on the official public games and re-score them.

Usage (Python 3.12, arc-agi==0.9.8, arcengine==0.9.3): python inputs/replay_benchmark.py <path/to/benchmark.json>
"""
import json, logging, sys
logging.disable(logging.CRITICAL)
import arc_agi
from arcengine import GameAction
import pathlib
ENV = str(pathlib.Path(__file__).resolve().parent / 'official-input-arc-prize-2026-arc-agi-3' / 'environment_files')
arc=arc_agi.Arcade(operation_mode=arc_agi.OperationMode.OFFLINE, environments_dir=ENV)
b=json.load(open(sys.argv[1]))
def score(apl, base, done):
    N=len(base); W=N*(N+1)/2
    s=sum((i+1)*min((base[i]/apl[i])**2*100,115) for i in range(done))/W
    return min(s, sum(range(1,done+1))/W*100)
tot=[]
for r in b['game_runs']:
    env=arc.make(r['game_id'], seed=0); f=env.reset()
    base=r['base_actions_per_level']; apl=[0]*len(base); lvl=0
    for h in r['history']:
        a=h['action']; name=a['id']; d=a.get('data') or None
        ga=GameAction[name]
        f=env.step(ga, data=d)
        if name!='RESET': apl[min(lvl,len(apl)-1)]+=1
        else: apl[min(lvl,len(apl)-1)]+=1
        lvl=f.levels_completed
    s=score(apl,base,f.levels_completed); tot.append(s)
    print(r['game_id'][:4],'replay levels',f.levels_completed,'score %.2f'%s,'| benchmark levels',r['levels_completed'],'score %.2f'%r['final_score'])
print('replay mean %.2f'%(sum(tot)/len(tot)))
