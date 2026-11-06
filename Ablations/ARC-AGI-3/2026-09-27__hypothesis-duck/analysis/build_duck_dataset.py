"""Build hypothesis episodes from our Duck transcripts, under the rules pre-registered in
experiments/hypothesis-test-duck/RUNLOG.md. Usage: python build_duck_dataset.py [jaccard_threshold]
Output: inputs/hypotheses/data/duck_hypotheses_j<thr>.jsonl
"""
import collections, glob, json, os, pathlib, re, sys
os.environ.setdefault('RUNLOG_DIR', 'hypothesis-test-duck')
HERE = pathlib.Path(__file__).parent; ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT / 'inputs' / 'jev'))
from runlog import log
from extract_turns import sections, run_for, PATTERNS
THR = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
HEDGE = re.compile(r'\b(likely|maybe|perhaps|probably|possibly|might|may|seems?|unclear|unknown|uncertain|hypothes\w*|guess|assume\w*|\?)', re.I)
LABEL_RE = re.compile(r'(?m)^\s*[-*]?\s*(World model|Goal model)\s*:\s*(.*?)(?=^\s*[-*]?\s*[A-Z][A-Za-z ]{2,25}:|\Z)', re.S)
tok = lambda s: set(re.findall(r'[a-z]+', s.lower()))
def jac(a, b):
    A, B = tok(a), tok(b)
    return len(A & B) / max(1, len(A | B))

def turns_of(path):
    run, d = run_for(path)
    if run is None: return None, None
    out = []
    for astep, act, parts in sections(open(path, encoding='utf-8', errors='replace').read()):
        up = '\n'.join(parts.get('USER PROMPT', []))
        m = re.search(r'Current state: step (\d+), level (\d+)', up)
        if not m: continue
        wm = re.search(r'Working world model carried from earlier turns:\n(.*?)\nend of world model', up, re.S)
        ex = re.search(r'Executed actions: (.*?)\.\n', up)
        hyp = ' '.join(' '.join(x.group(2).split()) for x in LABEL_RE.finditer(wm.group(1))) if wm else ''
        out.append({'env_step': int(m.group(1)), 'level': int(m.group(2)), 'hyp': hyp, 'ex': ex.group(1) if ex else ''})
    return run, out

files = [p for pat in PATTERNS for p in sorted(glob.glob(str(ROOT / pat)))]
log('duck step 2', f'threshold {THR}: scanning {len(files)} transcript files')
seen, rows, c = set(), [], collections.Counter()
for i, path in enumerate(files, 1):
    run, T = turns_of(path)
    if not T: c['no usable turns or no benchmark'] += 1; continue
    sig = (run['game_id'], tuple(t['ex'] for t in T[:30]))
    if sig in seen: c['duplicate transcript'] += 1; continue
    seen.add(sig); c['unique transcripts'] += 1
    src = os.path.relpath(os.path.dirname(os.path.dirname(path)), ROOT)
    for L in sorted(set(t['level'] for t in T)):
        lt = [t for t in T if t['level'] == L]; start_step = lt[0]['env_step']
        eps = []
        for k, t in enumerate(lt):
            if not t['hyp']: continue
            if not eps or jac(t['hyp'], eps[-1]['text']) < THR:
                eps.append({'text': t['hyp'], 'turn_on_level': k, 'actions_on_level': t['env_step'] - start_step})
        cleared = L <= run['levels_completed']
        for j, e in enumerate(eps):
            last = j == len(eps) - 1
            if last and not cleared: c['excluded: final hypothesis on uncleared level'] += 1; continue
            rows.append({'game': run['game_id'][:4], 'src': src, 'file': os.path.basename(path), 'level': L,
                         'hyp_index': j, 'n_hyps_level': len(eps), 'turn_on_level': e['turn_on_level'],
                         'actions_on_level': e['actions_on_level'], 'hedges': len(HEDGE.findall(e['text'])),
                         'text': e['text'], 'wrong': 0 if last else 1})
    if i % 50 == 0 or i == len(files):
        print(f'  heartbeat: {i}/{len(files)} files, {len(rows)} labelled hypotheses so far', flush=True)
out = HERE / 'data' / f'duck_hypotheses_j{THR}.jsonl'
with open(out, 'w') as f:
    for r in rows: f.write(json.dumps(r) + '\n')
g = collections.Counter(r['game'] for r in rows)
log('duck step 2', f'threshold {THR}: ' + '; '.join(f'{k} {v}' for k, v in c.items()) + f'; wrote {len(rows)} labelled hypotheses '
    f'(wrong {sum(r["wrong"] for r in rows)}, right {sum(1 - r["wrong"] for r in rows)}) over {len(g)} games: '
    + ', '.join(f'{k}:{v}' for k, v in g.most_common()))
