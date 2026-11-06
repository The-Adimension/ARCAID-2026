"""Mirror the full run outputs to a Hugging Face dataset, in the same folder layout as this repository.

  HF_TOKEN=<token> python -I upload_outputs_hf.py REPO_ROOT WORK_DIR ORG/NAME

For every row of Documentation/DATASET-MANIFEST.csv (the zips already published as the Kaggle Dataset):
  1. download the run's output zip from Kaggle,
  2. upload it to <repository_folder>/outputs.zip in the Hugging Face dataset,
  3. delete the local copy.
The Hugging Face path of each zip is therefore the GitHub folder of the same run. Files already in the
dataset are skipped, so an interrupted run resumes. The dataset card (README.md) and the manifest are
uploaded at the end. Needs Kaggle API credentials of the notebooks' owner and a Hugging Face write token.
"""
import csv, hashlib, sys, time
from pathlib import Path
from huggingface_hub import HfApi
from requests.exceptions import HTTPError, ConnectionError as CE, ChunkedEncodingError, Timeout
from kaggle.api.kaggle_api_extended import KaggleApi
from kagglesdk.kernels.types.kernels_api_service import ApiDownloadKernelOutputZipRequest


def retry(fn, waits=(0, 10, 30, 60, 120, 240)):
    last = None
    for w in waits:
        time.sleep(w)
        try:
            return fn()
        except (HTTPError, CE, ChunkedEncodingError, Timeout) as e:
            last = e
    raise last


repo, work, hf_repo = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
work.mkdir(parents=True, exist_ok=True)
hf = HfApi()
have = set(hf.list_repo_files(hf_repo, repo_type="dataset"))
rows = list(csv.DictReader(open(repo / "Documentation/DATASET-MANIFEST.csv")))
kg = KaggleApi(); kg.authenticate()
log = work / "hf_uploaded.csv"
with kg.build_kaggle_client() as k:
    c = k.kernels.kernels_api_client
    for i, r in enumerate(rows, 1):
        dest = f"{r['repository_folder']}/outputs.zip"
        if dest in have:
            continue
        path = work / r["file"]
        zr = ApiDownloadKernelOutputZipRequest(); zr.kernel_session_id = int(r["kaggle_script_version_id"])
        path.write_bytes(retry(lambda: c.download_kernel_output_zip(zr).content))
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        retry(lambda: hf.upload_file(path_or_fileobj=str(path), path_in_repo=dest, repo_id=hf_repo,
                                     repo_type="dataset", commit_message=f"Add outputs of {r['file'][:-4]}"))
        with open(log, "a", newline="") as f:
            csv.writer(f).writerow([dest, path.stat().st_size, sha, r["sha256"], sha == r["sha256"]])
        path.unlink()
        print(f"{i}/{len(rows)} {dest} {'same bytes as Kaggle Dataset' if sha == r['sha256'] else 'differs from the Kaggle Dataset zip (Kaggle re-packed it)'}", flush=True)
for local, dest in ((repo / "Documentation/DATASET-MANIFEST.csv", "DATASET-MANIFEST.csv"),
                    (repo / "Tools/huggingface/DATASET-CARD.md", "README.md")):
    hf.upload_file(path_or_fileobj=str(local), path_in_repo=dest, repo_id=hf_repo, repo_type="dataset",
                   commit_message=f"Update {dest}")
print("done")
