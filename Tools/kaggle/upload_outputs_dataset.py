"""Publish the full run outputs of every notebook version as one Kaggle Dataset, one zip per run.

  python -I upload_outputs_dataset.py REPO_ROOT WORK_DIR OWNER/SLUG "TITLE" [--public] [--limit N]

For each version folder in the repository that has an outputs manifest (from its run.json):
  1. download the run's output zip from Kaggle (exactly as Kaggle serves it),
  2. record its sha256 and size,
  3. upload it as a dataset file named <track>__<kernel>__v<N>.zip,
  4. delete the local copy.
Progress (upload tokens, hashes) is kept in WORK_DIR/state.json, so an interrupted run resumes.
When every file is uploaded, the dataset is created (private unless --public) with a description
that links back to this repository, and WORK_DIR/DATASET-MANIFEST.csv is written: one row per zip
with its repository folder and sha256. Copy that file to Documentation/ afterwards.
Needs Kaggle API credentials of the notebooks' owner (private notebooks' outputs are owner-only).
"""
import argparse, csv, hashlib, json, os, sys, time
from pathlib import Path
from requests.exceptions import HTTPError, ConnectionError as CE, ChunkedEncodingError, Timeout
from kaggle.api.kaggle_api_extended import KaggleApi, ResumableUploadContext
from kagglesdk.blobs.types.blob_api_service import ApiBlobType
from kagglesdk.datasets.types.dataset_api_service import ApiCreateDatasetRequest, ApiDatasetNewFile
from kagglesdk.kernels.types.kernels_api_service import ApiDownloadKernelOutputZipRequest


def retry(fn, waits=(0, 10, 30, 60, 120, 240)):
    for w in waits:
        time.sleep(w)
        try:
            return fn()
        except HTTPError as e:
            if e.response is None or e.response.status_code not in (429, 500, 502, 503):
                raise
        except (CE, ChunkedEncodingError, Timeout):
            pass
    return fn()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo"); ap.add_argument("work"); ap.add_argument("ref"); ap.add_argument("title")
    ap.add_argument("--public", action="store_true"); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--description", default="")
    a = ap.parse_args()
    repo, work = Path(a.repo), Path(a.work); work.mkdir(parents=True, exist_ok=True)
    state_f = work / "state.json"
    state = json.loads(state_f.read_text()) if state_f.exists() else {"files": {}}
    api = KaggleApi(); api.authenticate()

    runs = []
    for rj in sorted(repo.glob("**/run.json")):
        r = json.loads(rj.read_text())
        man = rj.parent / "outputs-manifest.csv"
        if not r.get("script_version_id") or not man.exists() or sum(1 for _ in open(man)) <= 1:
            continue
        name = f"{r['track']}__{r['kernel'].split('/')[-1]}__v{r['version']}.zip"
        runs.append((name, r["script_version_id"], rj.parent.relative_to(repo).as_posix()))
    print(len(runs), "runs with outputs;", len(state["files"]), "already uploaded", flush=True)

    done_now = 0
    with api.build_kaggle_client() as k:
        c = k.kernels.kernels_api_client
        for name, sid, folder in runs:
            if name in state["files"]:
                continue
            if a.limit and done_now >= a.limit:
                break
            path = work / name
            zr = ApiDownloadKernelOutputZipRequest(); zr.kernel_session_id = int(sid)
            path.write_bytes(retry(lambda: c.download_kernel_output_zip(zr).content))
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            size = path.stat().st_size
            with ResumableUploadContext() as ctx:
                token = retry(lambda: api._upload_blob(str(path), True, ApiBlobType.DATASET, ctx))
            if not token:
                raise RuntimeError(f"upload failed: {name}")
            state["files"][name] = {"token": token, "sha256": sha, "bytes": size, "folder": folder,
                                    "script_version_id": sid, "uploaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
            state_f.write_text(json.dumps(state, indent=1))
            path.unlink()
            done_now += 1
            print(f"{len(state['files'])}/{len(runs)} {name} {size/1e6:.0f} MB", flush=True)

    with open(work / "DATASET-MANIFEST.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["file", "bytes", "sha256", "kaggle_script_version_id", "repository_folder"])
        for name, v in sorted(state["files"].items()):
            w.writerow([name, v["bytes"], v["sha256"], v["script_version_id"], v["folder"]])
    if len(state["files"]) < len(runs):
        print("not all runs uploaded yet; re-run to continue"); return
    if state.get("created"):
        print("dataset already created:", state["created"]); return

    owner, slug = a.ref.split("/")
    req = ApiCreateDatasetRequest()
    req.owner_slug, req.slug, req.title = owner, slug, a.title
    req.license_name = "other"
    req.subtitle = "Full outputs of every ARC Prize 2026 notebook run in ARCAID-2026"
    req.description = a.description
    req.is_private = not a.public
    req.files = []
    for name, v in sorted(state["files"].items()):
        nf = ApiDatasetNewFile(); nf.token = v["token"]; req.files.append(nf)
    with api.build_kaggle_client() as k:
        res = retry(lambda: k.datasets.dataset_api_client.create_dataset(req))
    print("create:", getattr(res, "url", None), getattr(res, "error", None), getattr(res, "status", None))
    if not getattr(res, "error", None):
        state["created"] = getattr(res, "url", a.ref); state_f.write_text(json.dumps(state, indent=1))


if __name__ == "__main__":
    main()
