# Reproduce

Everything under `Submissions/`, `Ablations/*/runs/`, `ARCAID/LINEAGE.md` and `Documentation/LINKS.md` is generated from Kaggle by the scripts in `Tools/`. The rest of the repository (READMEs, decision rules, records, component code) is copied or written by hand.

## 1. Rebuild the catalogue from Kaggle

You need Python 3.12 or later and Kaggle API credentials (`~/.kaggle/kaggle.json`). Private notebooks are readable only by their owner, so until they are made public, steps 1–3 work only for the author.

```bash
python -m venv .venv && . .venv/bin/activate && pip install kaggle
```

```bash
python -I Tools/kaggle/collect_submissions.py Submissions
```

```bash
python -I Tools/kaggle/collect_runs.py RAW --shard 0/1
```

```bash
python -I Tools/kaggle/pull_bases.py BASES dfranzen/arc-agi-3-milestone-2-solution scottlegrand/taaf-flashnext-sheetu12b-0922 keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp foysalemonshanto/lb-9-arc3-duck-v12-with-qwen-3-8-27b madarshbb/arc-qwen-3-8-27b-agent amatlas/dfranzen-fork-d-prime jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner
```

```bash
python -I Tools/lineage/infer_parents.py RAW BASES parents.csv
```

```bash
python -I Tools/catalogue/build_catalogue.py RAW parents.csv BASES .
```

```bash
python -I Tools/catalogue/build_indexes.py .
```

```bash
python -I Tools/release/release_check.py . > Documentation/RELEASE-CHECKS.md
```

What each step does:
- `collect_runs.py`: every saved version of every notebook of ours that used an ARC Prize 2026 competition (the notebook, its Save & Run log, the hash of every output file).
- `pull_bases.py`: every version of the third-party notebooks ours were built on.
- `infer_parents.py` and `build_catalogue.py`: find each version's nearest earlier notebook and write the folders with their diffs.

## 2. Check an outputs file

Every version folder has `outputs-manifest.csv` with each output file's sha256. The full outputs of each run are one zip in the Kaggle Dataset `habanwer/arcaid-2026-run-outputs` and at `<folder>/outputs.zip` in the Hugging Face dataset `The-Adimension/ARCAID-2026-run-outputs`. `Documentation/DATASET-MANIFEST.csv` gives each zip's sha256. Unzip and check any file with `sha256sum` against the folder's manifest.

## 3. Re-run an analysis

Each ablation folder's `analysis/` holds the script and its saved output (`*.out` or `*.txt`). The scripts were written in the working repository and read the run outputs from its layout. They need the run's `outputs/benchmark.json`, which is in each version folder here, or the full outputs from the hosted copies.

The engine-based tools (`Tools/replay/`, the lexicon tests) need the competition-pinned packages and the 25 public games from the competition's data page:

```bash
pip install arc-agi==0.9.8 arcengine==0.9.3 numpy
```

## 4. Re-run a notebook

Open its Kaggle link (in the version folder's `run.json`, or in `Documentation/LINKS.md`) and use **Copy & Edit**. The notebooks need the same Kaggle inputs (listed in `run.json`, `inputs_as_run`) and an RTX Pro 6000 (ARC-AGI-3) or 4 × L4 (ARC-AGI-2) accelerator.

A Save & Run plays the public games. Kaggle runs the hidden games only when a version is submitted to the competition.
