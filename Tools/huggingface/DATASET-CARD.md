---
license: other
license_name: mixed
license_link: https://github.com/The-Adimension/ARCAID-2026/blob/main/DISCLAIMERS.md
pretty_name: ARCAID-2026 run outputs
tags:
- arc-agi
- arc-prize-2026
- agents
- kaggle
---

# ARCAID-2026 run outputs

This dataset holds the full outputs of every saved run of every Kaggle notebook in **ARCAID-2026**. ARCAID-2026 is Shehab Anwer's ([The Adimension](https://www.theadimension.com)) record of the ARC Prize 2026 ARC-AGI-3 and ARC-AGI-2 competitions.

**Same layout as the GitHub repository.** Each run's outputs are one zip, `<folder>/outputs.zip`. `<folder>` is that run's folder in the [GitHub repository](https://github.com/The-Adimension/ARCAID-2026), for example `Submissions/ARC-AGI-3/2026-10-25__arcaid3-probe-first-dfranzen-m2-sg/v1__2026-10-25__LB-23.41_30.57__SELECTED/`.

**The GitHub folder of the same path holds:**
- the notebook with its outputs removed;
- the Save & Run log;
- `run.json`, with the Kaggle notebook version and its inputs;
- `outputs-manifest.csv`, with the sha256 of every file inside the zip.

**The same zips are also a Kaggle Dataset,** `habanwer/arcaid-2026-run-outputs`. `DATASET-MANIFEST.csv` maps every zip to its folder and gives the Kaggle copy's sha256.

## Contents of a run's outputs

The contents vary by notebook:
- `benchmark.json` and `summary.txt`: per-game results on the public games;
- `*_requests.jsonl`: the model's requests and responses;
- `transcripts/`, `prompts/`, `artifacts/`;
- `diagnostics.html` and `serve.log`;
- `submission.parquet` or `submission.json`.

**These are Save & Run outputs on the 25 public games** (ARC-AGI-3) **or the public evaluation tasks** (ARC-AGI-2). Kaggle does not release the outputs of hidden-set reruns.

**Caution:** some runs include Python pickles (`games.pkl`, `intermediate_states.pkl`, `solver.pkl`). Never unpickle files you do not trust. The JSON files hold the same results.

## Licence

- Material authored by Shehab Anwer is released under MIT-0 / CC0-equivalent terms.
- The outputs also contain text produced by third-party harness code and by open-weight models (the Qwen3.8 family). That text remains under its owners' terms.
- See `DISCLAIMERS.md` and `Documentation/REFERENCES.md` in the repository.
