"""Leave-one-game-out test: does hypothesis text predict 'turns out wrong' beyond stated confidence?

Pre-registered (logged before results): target = wrong; models B0 chance, B1 stated confidence,
B2 confidence + authoring setup, T1 text, T2 text + confidence + setup. Each game is held out in turn.
Pooled held-out AUC and Brier; 95% bootstrap CI (2,000 reps, resampling games then rows) on
AUC(T2) - AUC(B2). Pass rule: CI lower bound > 0.
Outputs: experiments/hypothesis-test/predictions.csv, results.json
"""
import csv, json, pathlib, re, sys
import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss
sys.path.insert(0, str(pathlib.Path(__file__).parent)); from runlog import log
ROOT = pathlib.Path(__file__).resolve().parents[2]; OUT = ROOT / 'experiments' / 'hypothesis-test'
R = [json.loads(l) for l in open(pathlib.Path(__file__).parent / 'data' / 'hypotheses.jsonl')]
y = np.array([r['wrong'] for r in R]); games = np.array([r['game'] for r in R])
clean = lambda t: re.sub(r'\d+', ' ', t)
text = [clean(r['text']) for r in R]
conf = np.array([np.nan if r['confidence'] is None else r['confidence'] for r in R], float)
conf_f = np.where(np.isnan(conf), np.nanmean(conf), conf)[:, None] / 4.0
setups = sorted(set(r['setup'] for r in R)); S = np.array([[r['setup'] == s for s in setups] for r in R], float)
log('step 5', f'loaded {len(R)} rows, {len(set(games))} games, wrong-rate {y.mean():.3f}; starting 11 folds')
P = {k: np.zeros(len(R)) for k in ['B1_confidence', 'B2_conf+setup', 'T1_text', 'T2_text+conf+setup']}
P['B1_confidence'] = conf_f[:, 0] * -1  # higher stated confidence -> lower predicted wrong (rank only)
for i, g in enumerate(sorted(set(games)), 1):
    te = games == g; tr = ~te
    B = np.hstack([conf_f, S])
    m = LogisticRegression(max_iter=2000).fit(B[tr], y[tr]); P['B2_conf+setup'][te] = m.predict_proba(B[te])[:, 1]
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=3, sublinear_tf=True)
    Xtr = vec.fit_transform([text[j] for j in np.where(tr)[0]]); Xte = vec.transform([text[j] for j in np.where(te)[0]])
    m = LogisticRegression(max_iter=3000, C=1.0).fit(Xtr, y[tr]); P['T1_text'][te] = m.predict_proba(Xte)[:, 1]
    m = LogisticRegression(max_iter=3000, C=1.0).fit(hstack([Xtr, csr_matrix(B[tr])]).tocsr(), y[tr])
    P['T2_text+conf+setup'][te] = m.predict_proba(hstack([Xte, csr_matrix(B[te])]).tocsr())[:, 1]
    print(f'  heartbeat: fold {i}/11 held out {g} (n={te.sum()}, wrong-rate {y[te].mean():.2f}) done', flush=True)
res = {'n': len(R), 'wrong_rate': float(y.mean()), 'models': {}, 'per_game': {}}
for k, p in P.items():
    res['models'][k] = {'auc': float(roc_auc_score(y, p))}
    if k != 'B1_confidence':
        res['models'][k]['brier'] = float(brier_score_loss(y, p))
res['models']['B0_chance'] = {'auc': 0.5, 'brier': float(brier_score_loss(y, np.full(len(y), y.mean())))}
for g in sorted(set(games)):
    te = games == g
    if len(set(y[te])) == 2:
        res['per_game'][g] = {'n': int(te.sum()), **{k: round(float(roc_auc_score(y[te], p[te])), 3) for k, p in P.items()}}
rng = np.random.default_rng(0); gl = sorted(set(games)); idx = {g: np.where(games == g)[0] for g in gl}; d = []
for _ in range(2000):
    s = np.concatenate([rng.choice(idx[g], len(idx[g])) for g in rng.choice(gl, len(gl))])
    if len(set(y[s])) < 2: continue
    d.append(roc_auc_score(y[s], P['T2_text+conf+setup'][s]) - roc_auc_score(y[s], P['B2_conf+setup'][s]))
lo, hi = np.percentile(d, [2.5, 97.5]); res['delta_auc_T2_minus_B2'] = {'mean': float(np.mean(d)), 'ci95': [float(lo), float(hi)]}
# CORRECTION (logged): the pre-set rule compares against the STRONGEST baseline, which is B1 (stated
# confidence alone), not B2. Report both text models against B1 with the same bootstrap.
for tk in ('T1_text', 'T2_text+conf+setup'):
    dd = []
    rng = np.random.default_rng(1)
    for _ in range(2000):
        s_ = np.concatenate([rng.choice(idx[g], len(idx[g])) for g in rng.choice(gl, len(gl))])
        if len(set(y[s_])) < 2: continue
        dd.append(roc_auc_score(y[s_], P[tk][s_]) - roc_auc_score(y[s_], P['B1_confidence'][s_]))
    l2, h2 = np.percentile(dd, [2.5, 97.5])
    res[f'delta_auc_{tk}_minus_B1'] = {'mean': float(np.mean(dd)), 'ci95': [float(l2), float(h2)], 'pass': bool(l2 > 0)}
json.dump(res, open(OUT / 'results.json', 'w'), indent=1)
with open(OUT / 'predictions.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['game', 'setup', 'consult_id', 'wrong', 'confidence_raw'] + list(P))
    for j, r in enumerate(R): w.writerow([r['game'], r['setup'], r['consult_id'], r['wrong'], r['confidence_raw']] + [round(float(P[k][j]), 4) for k in P])
log('step 5', 'pooled held-out AUC: ' + ', '.join(f"{k} {v['auc']:.3f}" for k, v in res['models'].items()))
log('step 5', f"(secondary) AUC(text+conf+setup) - AUC(conf+setup) = {res['delta_auc_T2_minus_B2']['mean']:+.3f}, 95% CI [{lo:+.3f}, {hi:+.3f}]")
for tk in ('T1_text', 'T2_text+conf+setup'):
    r_ = res[f'delta_auc_{tk}_minus_B1']
    log('step 5', f"PRE-SET RULE vs strongest baseline (stated confidence): AUC({tk}) - AUC(confidence) = {r_['mean']:+.3f}, 95% CI [{r_['ci95'][0]:+.3f}, {r_['ci95'][1]:+.3f}] -> {'MET' if r_['pass'] else 'NOT met'}")
