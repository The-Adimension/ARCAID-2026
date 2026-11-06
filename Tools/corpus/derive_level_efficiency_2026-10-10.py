import json, glob, statistics as st, sys
files = sorted(set(glob.glob('submissions/*/outputs/benchmark.json') + glob.glob('experiments/*/outputs/benchmark.json')))
ratios = []; tot_actions = 0; stuck_actions = 0; runs = 0; cleared_levels = 0
for f in files:
    d = json.load(open(f))
    for g in d.get('game_runs', []):
        apl = g.get('actions_per_level') or []; base = g.get('base_actions_per_level') or []
        if not apl or sum(a or 0 for a in apl) == 0: continue
        runs += 1
        lc = g.get('levels_completed', 0)
        for i in range(lc):
            if base[i] and apl[i]:
                ratios.append(apl[i] / base[i]); cleared_levels += 1
        n = sum(a or 0 for a in apl)
        tot_actions += n
        # actions spent on the level the run never cleared (index lc), if any
        if lc < len(apl): stuck_actions += (apl[lc] or 0)
print('files', len(files), 'runs', runs, 'cleared levels', cleared_levels)
print('median agent/human on cleared levels', round(st.median(ratios), 3))
print('share of actions on the never-cleared level', round(stuck_actions / tot_actions, 3), tot_actions)
