"""Test a model-free 'surprise' signal on wall levels (levels the agent got stuck on and never cleared).

For every level >= 2 that a run entered, from observations only:
  S_frame   share of the level's first-frame non-background pixels (HUD border masked) drawn in colours
            never seen in any earlier level of this run
  S_eff@K   share of the level's first K actions whose effect signature -- (action id, set of
            (old colour -> new colour) pairs among changed cells) -- never occurred in an earlier level

Q1  AUC of each signal for 'this run got stuck on this level' vs 'cleared it'
Q2  on levels cleared in some runs and failed in others, the signal in winners vs losers
Q3  actions spent on the stuck level after K (room for an intervention triggered at K)

Usage (Python 3.12, arc-agi==0.9.8, arcengine==0.9.3):
  python inputs/surprise_walls.py [--k 10] <benchmark.json> ...
"""
import argparse, collections, hashlib, json, logging
logging.disable(logging.CRITICAL)
import numpy as np
import arc_agi
from arcengine import GameAction
from replay_system1 import ENV, BORDER, grid

def masked(g):
    x = g.copy()
    x[:BORDER, :] = -1; x[-BORDER:, :] = -1; x[:, :BORDER] = -1; x[:, -BORDER:] = -1
    return x

def effect(g0, g1, aid):
    if g0 is None or g1 is None or g0.shape != g1.shape:
        return (aid, 'reshape')
    a, b = masked(g0), masked(g1); ch = a != b
    if not ch.any():
        return (aid, 'noop')
    pairs = frozenset(zip(a[ch].tolist(), b[ch].tolist()))
    return (aid, pairs if len(pairs) <= 6 else 'many')

def levels_of(arc, run, K):
    env = arc.make(run['game_id'], seed=0); f = env.reset(); g = grid(f); lvl = 0
    seen_colours = set(); seen_eff = set()
    cur = {'first': g, 'effects': [], 'actions': 0}
    out = []
    for step in run['history']:
        a = step['action']; name = a['id']; d = a.get('data') or None
        f = env.step(GameAction[name], data=d); g2 = grid(f)
        if name != 'RESET':
            cur['effects'].append(effect(g, g2, name))
        cur['actions'] += 1
        g = g2
        if f.levels_completed > lvl:
            out.append((lvl, True, cur)); lvl = f.levels_completed
            cur = {'first': g, 'effects': [], 'actions': 0}
    out.append((lvl, False, cur))
    rows = []
    for L, cleared, c in out:
        m = masked(c['first']) if c['first'] is not None else None
        if L > 0 and m is not None:
            vals, cnt = np.unique(m[m >= 0], return_counts=True)
            bg = vals[np.argmax(cnt)] if len(vals) else -2
            fg = (m >= 0) & (m != bg)
            new = np.isin(m, list(set(vals.tolist()) - seen_colours)) & fg
            s_frame = new.sum() / max(1, fg.sum())
            first = c['effects'][:K]
            s_eff = sum(1 for e in first if e not in seen_eff) / max(1, len(first))
            rows.append({'level': L, 'cleared': cleared, 's_frame': float(s_frame), 's_eff': s_eff,
                         'actions': c['actions'], 'after_k': max(0, c['actions'] - K)})
        if m is not None:
            seen_colours |= set(np.unique(m[m >= 0]).tolist())
        seen_eff |= set(c['effects'])
    return rows

def auc(pos, neg):
    if not pos or not neg:
        return float('nan')
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('files', nargs='+'); ap.add_argument('--k', type=int, default=10)
    args = ap.parse_args()
    arc = arc_agi.Arcade(operation_mode=arc_agi.OperationMode.OFFLINE, environments_dir=ENV)
    rows = []; seen = set()
    for fp in args.files:
        for run in json.load(open(fp))['game_runs']:
            sig = hashlib.md5((run['game_id'] + json.dumps([h['action'] for h in run['history']])).encode()).hexdigest()
            if sig in seen or not run['history']:
                continue
            seen.add(sig)
            for r in levels_of(arc, run, args.k):
                r['game'] = run['game_id'][:4]; r['run'] = sig[:8]; rows.append(r)
    stuck = [r for r in rows if not r['cleared']]; ok = [r for r in rows if r['cleared']]
    print(f"runs {len(seen)}, levels>=2 entered {len(rows)}: stuck {len(stuck)}, cleared {len(ok)}, K={args.k}")
    for s in ('s_frame', 's_eff'):
        print(f"Q1 {s:8s} mean stuck {np.mean([r[s] for r in stuck]):.3f}  cleared {np.mean([r[s] for r in ok]):.3f}  "
              f"AUC {auc([r[s] for r in stuck], [r[s] for r in ok]):.3f}")
    # within-game control: compare only levels at the same (game, level) index
    by = collections.defaultdict(list)
    for r in rows:
        by[(r['game'], r['level'])].append(r)
    print("Q2 same level, cleared in some runs and failed in others:")
    for (gm, L), rs in sorted(by.items()):
        w = [r for r in rs if r['cleared']]; l = [r for r in rs if not r['cleared']]
        if w and l:
            print(f"   {gm} L{L+1}: win n={len(w)} s_frame {np.mean([r['s_frame'] for r in w]):.2f} s_eff {np.mean([r['s_eff'] for r in w]):.2f} "
                  f"actions {np.median([r['actions'] for r in w]):.0f} | fail n={len(l)} s_frame {np.mean([r['s_frame'] for r in l]):.2f} "
                  f"s_eff {np.mean([r['s_eff'] for r in l]):.2f} actions {np.median([r['actions'] for r in l]):.0f}")
    pairs = [(w, l) for rs in by.values() for w in rs if w['cleared'] for l in rs if not l['cleared']]
    for s in ('s_frame', 's_eff'):
        d = [l[s] - w[s] for w, l in pairs]
        print(f"   {s}: {len(pairs)} win/fail pairs on the same level, mean(fail - win) {np.mean(d):+.3f}, fail higher in "
              f"{sum(x > 0 for x in d)}, equal {sum(x == 0 for x in d)}, lower {sum(x < 0 for x in d)}")
    print(f"Q3 stuck levels: median actions {np.median([r['actions'] for r in stuck]):.0f}, after K median {np.median([r['after_k'] for r in stuck]):.0f}, "
          f"share of stuck-level actions after K {sum(r['after_k'] for r in stuck) / max(1, sum(r['actions'] for r in stuck)):.1%}")

if __name__ == '__main__':
    main()
