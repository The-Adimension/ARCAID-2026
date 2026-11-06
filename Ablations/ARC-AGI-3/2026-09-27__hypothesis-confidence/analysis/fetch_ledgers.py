"""Download every public ARA Labs ARC-AGI-3 prediction ledger (CC-BY-4.0) pinned to its commit.

Source: https://huggingface.co/AgentNativeResearchLab (datasets named arc-agi3-*), licence CC BY 4.0.
Attribution: ARA Labs (Agent-Native Research Lab). Output: inputs/hypotheses/data/ledger_raw.jsonl
(one line per ledger row, plus the source repo and commit) and ledger_manifest.json.
"""
import json, pathlib, sys
from huggingface_hub import HfApi, hf_hub_download
sys.path.insert(0, str(pathlib.Path(__file__).parent)); from runlog import log
OUT = pathlib.Path(__file__).parent / 'data'; OUT.mkdir(exist_ok=True)
api = HfApi()
repos = sorted(d.id for d in api.list_datasets(author='AgentNativeResearchLab', limit=1000) if 'arc-agi3' in d.id)
log('step 2', f'found {len(repos)} ARA Labs arc-agi3 dataset repos')
manifest, rows, with_ledger = [], 0, 0
with open(OUT / 'ledger_raw.jsonl', 'w') as fo:
    for i, r in enumerate(repos, 1):
        info = api.dataset_info(r)
        files = api.list_repo_files(r, repo_type='dataset', revision=info.sha)
        entry = {'repo': r, 'sha': info.sha, 'has_ledger': 'predictions.jsonl' in files, 'rows': 0}
        if entry['has_ledger']:
            p = hf_hub_download(r, 'predictions.jsonl', repo_type='dataset', revision=info.sha,
                                cache_dir=str(OUT / '.hfcache'))
            for line in open(p, encoding='utf-8'):
                if line.strip():
                    try:
                        d = json.loads(line)
                    except json.JSONDecodeError:
                        entry['bad_lines'] = entry.get('bad_lines', 0) + 1; continue
                    fo.write(json.dumps({'repo': r, 'sha': info.sha, **d}) + '\n'); entry['rows'] += 1
            with_ledger += 1; rows += entry['rows']
        manifest.append(entry)
        if i % 10 == 0 or i == len(repos):
            print(f'  heartbeat: {i}/{len(repos)} repos scanned, {rows} ledger rows so far', flush=True)
json.dump(manifest, open(OUT / 'ledger_manifest.json', 'w'), indent=1)
log('step 2', f'downloaded {rows} ledger rows from {with_ledger} of {len(repos)} repos, each pinned to its commit sha (ledger_manifest.json)')
