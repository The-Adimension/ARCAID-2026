"""Build one decision-point dataset from every Duck transcript in the repo.

One record per model turn (analysis step): what the model saw and wrote, what it executed, and how the
level and run ended. Output: JSONL (default inputs/jev/turns.jsonl, git-ignored when large).

Labels come from the run's benchmark.json (levels_completed) and from the level sequence of the
transcript itself. Transcript levels are 1-indexed; level L was cleared in the run iff L <= levels_completed.
"""
import glob, json, os, re, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
PATTERNS = ['submissions/*/outputs/transcripts/*.txt', 'experiments/*/outputs/transcripts/*.txt',
            'inputs/arc3-collections/1345/*/transcripts/*.txt']
TAG = re.compile(r'(?m)^\[([A-Z][A-Z _:a-z]*)\]\s*$')

def sections(text):
    for sec in re.split(r'(?m)^--- analysis_step=', text)[1:]:
        head = sec.split('\n', 1)[0]
        m = re.match(r'(\d+) \| action=(\d+)', head)
        parts = {}
        pos = [(mm.start(), mm.end(), mm.group(1)) for mm in TAG.finditer(sec)]
        for i, (s, e, name) in enumerate(pos):
            end = pos[i + 1][0] if i + 1 < len(pos) else len(sec)
            parts.setdefault(name, []).append(sec[e:end].strip())
        yield (int(m.group(1)) if m else None, int(m.group(2)) if m else None, parts)

def run_for(path):
    d = os.path.dirname(os.path.dirname(path))
    for cand in (os.path.join(d, 'benchmark.json'),):
        if os.path.exists(cand):
            b = json.load(open(cand))
            name = os.path.basename(path); gid = name.split('_p')[0]; p = int(name.split('_p')[1].split('.')[0])
            runs = [r for r in b['game_runs'] if r['game_id'] == gid]
            if runs:
                return runs[min(p, len(runs) - 1)], d
    return None, d

def main(out):
    n = 0
    with open(out, 'w') as fo:
        for pat in PATTERNS:
            for path in sorted(glob.glob(str(ROOT / pat))):
                run, d = run_for(path)
                if run is None:
                    continue
                recs = []
                for astep, act, parts in sections(open(path, encoding='utf-8', errors='replace').read()):
                    up = '\n'.join(parts.get('USER PROMPT', []))
                    m = re.search(r'Current state: step (\d+), level (\d+)', up)
                    if not m:
                        continue
                    wm = re.search(r'Working world model carried from earlier turns:\n(.*?)\nend of world model', up, re.S)
                    ex = re.search(r'Executed actions: (.*?)\.\n', up)
                    status = '\n'.join(parts.get('ANALYZER STATUS', []))
                    recs.append({
                        'src': os.path.relpath(d, ROOT), 'file': os.path.basename(path), 'game': run['game_id'][:4],
                        'analysis_step': astep, 'env_step': int(m.group(1)), 'level': int(m.group(2)),
                        'levels_completed_run': run['levels_completed'], 'n_levels': run['number_of_levels'],
                        'world_model': wm.group(1).strip() if wm else '',
                        'prev_executed': ex.group(1) if ex else '',
                        'thinking': '\n'.join(parts.get('THINKING', []))[:6000],
                        'assistant': '\n'.join(parts.get('ASSISTANT', []))[:3000],
                        'code': '\n'.join(p for k, v in parts.items() if k.startswith('TOOL CALL') for p in v)[:4000],
                        'step_executed': 'step_executed: True' in status,
                    })
                # per-level derived labels
                for i, r in enumerate(recs):
                    r['cleared'] = r['level'] <= r['levels_completed_run']
                    lvl_turns = [x for x in recs if x['level'] == r['level']]
                    r['turn_on_level'] = sum(1 for x in recs[:i] if x['level'] == r['level'])
                    r['turns_on_level_total'] = len(lvl_turns)
                    first = lvl_turns[0]['env_step']
                    r['actions_on_level_so_far'] = r['env_step'] - first
                    nxt = next((x['env_step'] for x in recs[i:] if x['level'] > r['level']), None)
                    r['actions_to_clear'] = (nxt - r['env_step']) if nxt is not None else None
                    fo.write(json.dumps(r) + '\n'); n += 1
    print('records', n, '->', out)

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else str(ROOT / 'inputs/jev/turns.jsonl'))
