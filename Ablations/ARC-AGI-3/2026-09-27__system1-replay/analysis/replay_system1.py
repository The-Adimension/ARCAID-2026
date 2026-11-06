"""Design-1 System-1 replay: how much of the agent's play an online state graph could have answered.

Replays every saved `benchmark.json` action history on the official public games and, per level,
builds the graph the harness could have built while playing: node = screen (HUD border masked),
edge = (action, click) -> next screen. Every quantity uses only what was observed BEFORE the action.

Per action it reports:
  known_noop    (state, action) already tried here and it changed nothing
  known_result  (state, action) already tried here; outcome known (deterministic engine)
  first_noop    first try of this (state, action) and nothing changed (a lookup can't know; a learned
                effect model could -- the step-3 target)
  new           first try, something changed

Removable actions (upper bound for a pure lookup layer): every maximal run of actions whose (state,
action) pairs were all already known walks the known graph from X to Y; it could have been done in
shortest_path(X, Y) actions on the graph known at the run's start. Excess = run length - that path.

Model calls: a call starts at an action with generated_tokens > 0. A call whose actions are all
known-territory could have been executed by the harness, given its endpoint.

Score: the cleared levels are re-scored with their excess removed (same formula as
replay_benchmark.py). Levels never cleared stay at 0; their excess is time, not score.

Usage (Python 3.12, arc-agi==0.9.8, arcengine==0.9.3):
  python inputs/replay_system1.py [--exact] [--json out.json] <benchmark.json> ...
"""
import argparse, collections, hashlib, json, logging, os, pathlib
from collections import deque
logging.disable(logging.CRITICAL)
import numpy as np
import arc_agi
from arcengine import GameAction

ENV = str(pathlib.Path(__file__).resolve().parent / 'official-input-arc-prize-2026-arc-agi-3' / 'environment_files')
BORDER = 2  # HUD mask: the step/progress bars public games draw along the edges


def baselines():
    out = {}
    for g in os.listdir(ENV):
        for v in os.listdir(f'{ENV}/{g}'):
            out[g] = json.load(open(f'{ENV}/{g}/{v}/metadata.json'))['baseline_actions']
    return out


def score(apl, base, done):
    N = len(base); W = N * (N + 1) / 2
    s = sum((i + 1) * min((base[i] / apl[i]) ** 2 * 100, 115) for i in range(done) if apl[i] > 0) / W
    return min(s, sum(range(1, done + 1)) / W * 100)


def grid(frame):
    return np.array(frame.frame[-1]) if len(frame.frame) else None


def state_hash(g, exact):
    if g is None:
        return 'none'
    x = g.copy()
    if not exact and x.shape[0] > 2 * BORDER and x.shape[1] > 2 * BORDER:
        x[:BORDER, :] = -1; x[-BORDER:, :] = -1; x[:, :BORDER] = -1; x[:, -BORDER:] = -1
    return hashlib.md5(x.tobytes() + str(x.shape).encode()).hexdigest()


def shortest(edges, src, dst):
    if src == dst:
        return 0
    seen = {src}; q = deque([(src, 0)])
    while q:
        s, d = q.popleft()
        for t in edges.get(s, ()):
            if t == dst:
                return d + 1
            if t not in seen:
                seen.add(t); q.append((t, d + 1))
    return None


def replay_run(arc, run, base, exact):
    env = arc.make(run['game_id'], seed=0); f = env.reset(); g = grid(f)
    s = state_hash(g, exact); lvl = 0
    outcome = {}; edges = collections.defaultdict(set)
    per_level = collections.defaultdict(lambda: collections.Counter())
    apl = [0] * len(base)
    calls = []  # [known_only(bool), tokens]
    seg = None  # [start_state, length, edges snapshot not needed: graph only grows]
    mismatch = 0
    classes = []

    def close_segment(end_state, level):
        nonlocal seg
        if seg and seg[1] > 0:
            sp = shortest(seg[2], seg[0], end_state)
            per_level[level]['excess'] += max(0, seg[1] - sp) if sp is not None else 0
        seg = None

    for step in run['history']:
        a = step['action']; name = a['id']; d = a.get('data') or None
        key = (s, name, json.dumps(d, sort_keys=True) if d else '')
        tok = step.get('generated_tokens') or 0
        if tok > 0 or not calls:
            calls.append([True, tok, lvl])
        f = env.step(GameAction[name], data=d); g2 = grid(f); s2 = state_hash(g2, exact)
        apl[min(lvl, len(apl) - 1)] += 1
        c = per_level[lvl]; c['actions'] += 1
        if key in outcome:
            cls = 'known_noop' if outcome[key] == s else 'known_result'
            if outcome[key] != s2:
                mismatch += 1
            if seg is None:
                seg = [s, 0, {k: set(v) for k, v in edges.items()}]
            seg[1] += 1
        else:
            cls = 'first_noop' if s2 == s else 'new'
            calls[-1][0] = False
            close_segment(s, lvl)
            outcome[key] = s2
        c[cls] += 1; classes.append(cls)
        if s2 != s:
            edges[s].add(s2)
        if f.levels_completed > lvl:
            close_segment(s2, lvl)
            lvl = f.levels_completed; outcome = {}; edges = collections.defaultdict(set)
        s = s2
    close_segment(s, lvl)
    return f.levels_completed, apl, per_level, calls, mismatch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+')
    ap.add_argument('--exact', action='store_true', help='no HUD mask (sensitivity check)')
    ap.add_argument('--json')
    args = ap.parse_args()
    arc = arc_agi.Arcade(operation_mode=arc_agi.OperationMode.OFFLINE, environments_dir=ENV)
    bases = baselines()
    seen_runs = set(); tot = collections.Counter(); stuck = collections.Counter(); cleared = collections.Counter()
    calls_all = calls_known = tok_all = tok_known = 0
    orig_scores = []; new_scores = []; check_fail = 0; per_game = collections.defaultdict(collections.Counter)
    for fp in args.files:
        for run in json.load(open(fp))['game_runs']:
            sig = hashlib.md5((run['game_id'] + json.dumps([h['action'] for h in run['history']])).encode()).hexdigest()
            if sig in seen_runs or not run['history']:
                continue
            seen_runs.add(sig)
            gid = run['game_id'][:4]; base = bases[gid]
            done, apl, per_level, calls, mismatch = replay_run(arc, run, base, args.exact)
            tot['mismatch'] += mismatch; tot['runs'] += 1
            if done != run['levels_completed']:
                check_fail += 1
            new_apl = list(apl)
            for L, c in per_level.items():
                bucket = cleared if L < done else stuck
                bucket.update(c); bucket['levels'] += 1
                per_game[gid].update({k: v for k, v in c.items()})
                if L < done:
                    new_apl[L] = max(1, apl[L] - c['excess'])
            orig_scores.append(score(apl, base, done)); new_scores.append(score(new_apl, base, done))
            for known, tok, _ in calls:
                calls_all += 1; tok_all += tok
                if known:
                    calls_known += 1; tok_known += tok
    tot.update(cleared); tot.update(stuck)
    A = cleared['actions'] + stuck['actions']
    print(f"mode: {'exact screens' if args.exact else f'HUD border {BORDER} masked'}")
    print(f"runs {tot['runs']} (deduplicated), actions {A}, replay level-count mismatches vs benchmark: {check_fail}")
    print(f"known pairs whose outcome differed from the first observation: {tot['mismatch']}")
    print(f"{'':22s}{'cleared levels':>16s}{'stuck levels':>16s}{'all':>10s}")
    for k in ['actions', 'known_noop', 'known_result', 'first_noop', 'new', 'excess']:
        row = [cleared[k], stuck[k], cleared[k] + stuck[k]]
        pct = lambda v, n: f"{v} ({100 * v / n:.1f}%)" if k != 'actions' and n else str(v)
        print(f"{k:22s}{pct(row[0], cleared['actions']):>16s}{pct(row[1], stuck['actions']):>16s}{pct(row[2], A):>10s}")
    print(f"levels: cleared {cleared['levels']}, stuck {stuck['levels']}")
    print(f"model calls {calls_all}; all-known calls {calls_known} ({100 * calls_known / max(1, calls_all):.1f}%), "
          f"their tokens {tok_known} of {tok_all} ({100 * tok_known / max(1, tok_all):.1f}%)")
    mo, mn = np.mean(orig_scores), np.mean(new_scores)
    print(f"mean game score on the replayed runs: {mo:.2f} -> {mn:.2f} with cleared-level excess removed ({100 * (mn - mo) / mo:+.1f}%)")
    print('per game (actions / excess% / known_noop% / first_noop%):')
    for gid, c in sorted(per_game.items(), key=lambda x: -x[1]['actions']):
        n = c['actions']
        print(f"  {gid} {n:6d}  {100 * c['excess'] / n:5.1f}  {100 * c['known_noop'] / n:5.1f}  {100 * c['first_noop'] / n:5.1f}")
    if args.json:
        json.dump({'cleared': cleared, 'stuck': stuck, 'calls': calls_all, 'calls_known': calls_known,
                   'tokens': tok_all, 'tokens_known': tok_known, 'score_orig': mo, 'score_new': mn,
                   'per_game': per_game, 'runs': tot['runs'], 'mismatch': tot['mismatch'],
                   'check_fail': check_fail}, open(args.json, 'w'), indent=1)


if __name__ == '__main__':
    main()
