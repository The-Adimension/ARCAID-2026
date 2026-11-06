"""Leave-one-game-out test on Duck hypothesis episodes (rules pre-registered in
experiments/hypothesis-test-duck/RUNLOG.md). Usage: python duck_logo_test.py [threshold]
Baselines: H hedges, C counters (turn/actions on level before the hypothesis, level, hypothesis index),
S run configuration, HCS all three. The strongest baseline is chosen automatically by pooled held-out AUC.
Pass rule: AUC(text+HCS) - AUC(strongest baseline) has 95% bootstrap CI lower bound > 0.
Never used: n_hyps_level (known only after the fact).
"""
import csv, json, os, pathlib, re, sys
os.environ.setdefault('RUNLOG_DIR', 'hypothesis-test-duck')
import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss
HERE = pathlib.Path(__file__).parent; sys.path.insert(0, str(HERE)); from runlog import log
OUT = HERE.parents[1] / 'experiments' / 'hypothesis-test-duck'
THR = sys.argv[1] if len(sys.argv) > 1 else '0.5'
R = [json.loads(l) for l in open(HERE / 'data' / f'duck_hypotheses_j{THR}.jsonl')]
y = np.array([r['wrong'] for r in R]); games = np.array([r['game'] for r in R])
text = [re.sub(r'\d+', ' ', r['text']) for r in R]
H = np.array([[np.log1p(r['hedges'])] for r in R])
C = np.array([[np.log1p(r['turn_on_level']), np.log1p(r['actions_on_level']), r['level'], np.log1p(r['hyp_index'])] for r in R])
srcs = sorted(set(r['src'] for r in R)); S = np.array([[r['src'] == s for s in srcs] for r in R], float)
feat = {'H_hedges': H, 'C_counters': C, 'S_config': S, 'HCS_all': np.hstack([H, C, S])}
log('duck step 3', f'threshold {THR}: {len(R)} rows, {len(set(games))} games, wrong-rate {y.mean():.3f}; running {len(set(games))} folds')
P = {k: np.zeros(len(R)) for k in list(feat) + ['T_text', 'T+HCS']}
for i, g in enumerate(sorted(set(games)), 1):
    te = games == g; tr = ~te
    if len(set(y[tr])) < 2: continue
    for k, X in feat.items():
        mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-9
        P[k][te] = LogisticRegression(max_iter=3000).fit((X[tr] - mu) / sd, y[tr]).predict_proba((X[te] - mu) / sd)[:, 1]
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=3, sublinear_tf=True)
    Xtr = vec.fit_transform([text[j] for j in np.where(tr)[0]]); Xte = vec.transform([text[j] for j in np.where(te)[0]])
    P['T_text'][te] = LogisticRegression(max_iter=3000).fit(Xtr, y[tr]).predict_proba(Xte)[:, 1]
    A = feat['HCS_all']; mu, sd = A[tr].mean(0), A[tr].std(0) + 1e-9
    P['T+HCS'][te] = LogisticRegression(max_iter=3000).fit(hstack([Xtr, csr_matrix((A[tr] - mu) / sd)]).tocsr(), y[tr]).predict_proba(
        hstack([Xte, csr_matrix((A[te] - mu) / sd)]).tocsr())[:, 1]
    print(f'  heartbeat: fold {i}/{len(set(games))} held out {g} (n={te.sum()}, wrong-rate {y[te].mean():.2f})', flush=True)
res = {'threshold': THR, 'n': len(R), 'wrong_rate': float(y.mean()),
       'models': {k: {'auc': float(roc_auc_score(y, p)), 'brier': float(brier_score_loss(y, p))} for k, p in P.items()}}
res['models']['chance'] = {'auc': 0.5, 'brier': float(brier_score_loss(y, np.full(len(y), y.mean())))}
best = max(feat, key=lambda k: res['models'][k]['auc']); res['strongest_baseline'] = best
gl = sorted(set(games)); idx = {g: np.where(games == g)[0] for g in gl}
for tk in ('T_text', 'T+HCS'):
    rng = np.random.default_rng(0); d = []
    for _ in range(2000):
        s = np.concatenate([rng.choice(idx[g], len(idx[g])) for g in rng.choice(gl, len(gl))])
        if len(set(y[s])) < 2: continue
        d.append(roc_auc_score(y[s], P[tk][s]) - roc_auc_score(y[s], P[best][s]))
    lo, hi = np.percentile(d, [2.5, 97.5])
    res[f'delta_{tk}_minus_{best}'] = {'mean': float(np.mean(d)), 'ci95': [float(lo), float(hi)], 'pass': bool(lo > 0)}
res['per_game'] = {g: {'n': int((games == g).sum()), **{k: round(float(roc_auc_score(y[games == g], P[k][games == g])), 3) for k in P}}
                   for g in gl if len(set(y[games == g])) == 2 and (games == g).sum() >= 10}
json.dump(res, open(OUT / f'results_j{THR}.json', 'w'), indent=1)
with open(OUT / f'predictions_j{THR}.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['game', 'src', 'file', 'level', 'hyp_index', 'wrong'] + list(P))
    for j, r in enumerate(R): w.writerow([r['game'], r['src'], r['file'], r['level'], r['hyp_index'], r['wrong']] + [round(float(P[k][j]), 4) for k in P])
log('duck step 3', f'threshold {THR}: pooled held-out AUC: ' + ', '.join(f"{k} {v['auc']:.3f}" for k, v in res['models'].items()) + f'; strongest baseline = {best}')
for tk in ('T_text', 'T+HCS'):
    r_ = res[f'delta_{tk}_minus_{best}']
    log('duck step 3', f"threshold {THR}: PRE-SET RULE AUC({tk}) - AUC({best}) = {r_['mean']:+.3f}, 95% CI [{r_['ci95'][0]:+.3f}, {r_['ci95'][1]:+.3f}] -> {'MET' if r_['pass'] else 'NOT met'}")
