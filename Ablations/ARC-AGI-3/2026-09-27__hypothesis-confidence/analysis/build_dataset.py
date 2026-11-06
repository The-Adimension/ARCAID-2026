"""Build the hypothesis dataset from the raw ledgers: one row per (prediction, verdict) pair.

Label rules (explicit; every filter is counted and logged):
  wrong (1): verdict starts with 'refut' or 'falsif' (incl. qualified forms such as 'refuted_merge')
  right (0): verdict starts with 'confirm' or 'support', or equals 'resolved-solved'
  excluded : anything containing 'partial', or unresolved/pending/inconclusive, or mixed verdicts
             containing both a refute and a confirm/support word
Input text = prediction + falsifiable_condition only (written before the outcome). Post-outcome fields
(evidence, outcome, result, observed) are never used.
Confidence ordinal: low 0, low-medium/medium-low 1, medium/moderate 2, medium-high 3, high 4, else None.
Output: inputs/hypotheses/data/hypotheses.jsonl
"""
import collections, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent)); from runlog import log
D = pathlib.Path(__file__).parent / 'data'
GAMES = 'ar25 bp35 cd82 cn04 dc22 ft09 g50t ka59 lf52 lp85 ls20 m0r0 r11l re86 s5i5 sb26 sc25 sk48 sp80 su15 tn36 tr87 tu93 vc33 wa30'.split()

def label(v):
    v = str(v).strip().lower()
    neg = v.startswith(('refut', 'falsif'))
    pos = v.startswith(('confirm', 'support')) or v == 'resolved-solved'
    if 'partial' in v or v.startswith(('unresolved', 'pending', 'inconclusive')):
        return None, 'partial/unresolved'
    if (neg and re.search(r'confirm|support', v)) or (pos and re.search(r'refut|falsif', v)):
        return None, 'mixed'
    if neg: return 1, 'wrong'
    if pos: return 0, 'right'
    return None, 'other'

def conf(c):
    c = str(c).strip().lower()
    for pre, val in (('medium-high', 3), ('high', 4), ('low-medium', 1), ('medium-low', 1), ('medium', 2), ('moderate', 2), ('low', 0)):
        if c.startswith(pre): return val
    return None

def meta(repo):
    name = repo.split('/')[1]
    game = next((g for g in GAMES if re.search(rf'(^|-){g}(-|$)', name)), None)
    setup = re.sub(rf'^arc-agi3-|-?({"|".join(GAMES)})(-demo)?$|-{game}-agent-trajectories$', '', name) if game else name
    if (setup or name).endswith('agent-trajectories'):
        setup = 'unknown-agent'  # model not stated in these repo names
    return game, setup or name

R = [json.loads(l) for l in open(D / 'ledger_raw.jsonl')]
log('step 3', f'read {len(R)} raw ledger rows')
preds = collections.defaultdict(list); verds = collections.defaultdict(list); c = collections.Counter()
for r in R:
    key = (r['repo'], r.get('consult_id'))
    if 'prediction' in r: preds[key].append(r)
    if 'verdict' in r: verds[key].append(r)
pairs = []
for key, vs in verds.items():
    ps = preds.get(key, [])
    if key[1] is None: c['verdict without consult_id'] += len(vs); continue
    if not ps: c['verdict with no matching prediction'] += len(vs); continue
    if len(ps) > 1 or len(vs) > 1: c['ambiguous (several predictions/verdicts share an id)'] += 1; continue
    pairs.append((ps[0], vs[0]))
c['predictions never given a verdict'] = sum(1 for k in preds if k not in verds)
log('step 3', f'joined {len(pairs)} prediction/verdict pairs; dropped: ' + '; '.join(f'{k} {v}' for k, v in c.items()))
rows, lab = [], collections.Counter()
for p, v in pairs:
    y, why = label(v['verdict']); lab[why] += 1
    if y is None: continue
    game, setup = meta(p['repo'])
    text = (str(p['prediction']) + ' || ' + str(p.get('falsifiable_condition') or p.get('falsifiable') or '')).strip()
    rows.append({'game': game, 'setup': setup, 'repo': p['repo'], 'consult_id': p['consult_id'], 'level': p.get('level'),
                 'text': text, 'confidence_raw': p.get('confidence'), 'confidence': conf(p.get('confidence')),
                 'verdict_raw': v['verdict'], 'wrong': y})
log('step 3', 'verdict classes: ' + ', '.join(f'{k} {v}' for k, v in lab.most_common()))
seen, out, dup = set(), [], 0
for r in rows:
    k = re.sub(r'\s+', ' ', r['text'].lower())
    if k in seen: dup += 1; continue
    seen.add(k); out.append(r)
with open(D / 'hypotheses.jsonl', 'w') as f:
    for r in out: f.write(json.dumps(r) + '\n')
g = collections.Counter(r['game'] for r in out); s = collections.Counter(r['setup'] for r in out)
log('step 3', f'wrote {len(out)} labelled hypotheses after removing {dup} duplicate texts; wrong-rate {sum(r["wrong"] for r in out)/len(out):.2f}; '
    f'games {len(g)} ({", ".join(f"{k}:{v}" for k, v in sorted(g.items(), key=lambda x: -x[1]))}); setups {len(s)}; '
    f'confidence missing on {sum(r["confidence"] is None for r in out)} rows')
