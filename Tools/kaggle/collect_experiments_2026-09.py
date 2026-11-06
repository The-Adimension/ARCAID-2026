"""Pull every saved ARC-AGI-3 notebook version that was NOT submitted to the competition.

Usage (from the repo root):  .venv/Scripts/python.exe experiments/collect.py
Re-running only downloads versions that are not already collected.
"""
import csv, io, json, re, time, zipfile
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from requests.exceptions import HTTPError
from kaggle.api.kaggle_api_extended import KaggleApi
from kagglesdk.kernels.types.kernels_api_service import (
    ApiGetKernelRequest, ApiDownloadKernelOutputRequest, ApiDownloadKernelOutputZipRequest)

COMP = "arc-prize-2026-arc-agi-3"
OWNER = "habanwer"
SINCE = datetime(2026, 9, 1)  # competition work started in September; older kernels are other projects
ROOT = Path(__file__).resolve().parent
SUBMISSIONS = ROOT.parent / "submissions"
NOTE = ("offline_public_games_score is the notebook's own score.json on the public games, "
        "not a leaderboard score.")


STAMP = re.compile(rb"2026-\d\d-\d\d[T ]\d\d:\d\d")


def describe(d, saved=None):
    """Run date, folder label and outcome, read from a collected run's own files.

    Kaggle stamps output-zip entries with the download time, so the date comes from
    score.json, else summary.txt's start time, else the newest timestamp in the run's files,
    else `saved` (when Kaggle wrote the run log; set at download for runs with no timestamps).
    """
    out = d / "outputs"
    score = created = None
    if (out / "score.json").exists():
        s = json.loads((out / "score.json").read_text(encoding="utf-8"))
        score, created = round(s["score"], 2), s.get("metadata", {}).get("created_at")
    stamps = []
    for p in d.rglob("*"):
        if p.is_file() and p.suffix in {".json", ".jsonl", ".log", ".txt", ".md", ".ipynb"} and p.name != "experiment.json":
            stamps += STAMP.findall(p.read_bytes())
    summary = (out / "summary.txt").read_text(encoding="utf-8") if (out / "summary.txt").exists() else ""
    started = re.search(r"^started:\s+(\S+ \S+)", summary, re.M)
    run_time = (created or (started and started.group(1).replace(" ", "T"))
                or (max(stamps).decode().replace(" ", "T") if stamps else saved))

    log = "".join(x["data"] for x in json.loads((d / "__output__.json").read_text(encoding="utf-8")))
    errors = re.findall(r"^(\w+(?:Error|Exception)): (.*)$", log, re.M)
    error = f"{errors[-1][0]}: {errors[-1][1]}"[:300] if errors else None
    ab_mean = re.search(r"mean score:\s+([\d.]+)", summary)

    if score is not None:
        label, outcome = f"offline-{score}", "completed"
    elif (out / "vllm-setup-failure.json").exists():
        label, outcome = "error-vllm-setup", "failed: vLLM server setup"
    elif error and "coverage changed" in error:
        label, outcome = "error-coverage-check", "played the games, then failed the public-run coverage check"
    elif ab_mean and not error:
        label, outcome = f"ab-mean-{ab_mean.group(1)}", "completed A/B run (summary.txt mean score, different game set)"
    elif error and re.match(r"(ModuleNotFound|Import)Error", error):
        label, outcome = "error-import", "failed: import error"
    elif error:
        label, outcome = "error", "failed"
    elif "Converting notebook __notebook__.ipynb to notebook" not in log:  # every executed run exports this
        label, outcome = "quick-save", "quick save: saved without running, so no outputs"
    else:
        label, outcome = "completed-no-score", "completed; this notebook writes no score"
    return {"run_date": run_time, "label": label, "outcome": outcome, "error": error,
            "offline_public_games_score": score,
            "ab_mean_score": float(ab_mean.group(1)) if ab_mean else None}


def relabel(d):
    """Rename a collected folder to date__slug__vN__unsubmitted__label and refresh experiment.json."""
    info = json.loads((d / "experiment.json").read_text(encoding="utf-8"))
    desc = describe(d, saved=info.get("run_date"))
    info.update({k: v for k, v in desc.items() if k != "label"})
    slug = info["kernel"].split("/")[1]
    day = desc["run_date"][:10] if desc["run_date"] else "unknown-date"
    name = f"{day}__{slug}__v{info['version']}__unsubmitted__{desc['label']}"
    (d / "experiment.json").write_text(json.dumps(info, indent=2), encoding="utf-8", newline="\r\n")
    if d.name != name:
        d.rename(d.parent / name)
    return name


def retry(fn):
    """Call fn, backing off on Kaggle's 429 rate limit."""
    for wait in (0, 15, 30, 60, 120, 240):
        time.sleep(wait)
        try:
            return fn()
        except HTTPError as e:
            if e.response is None or e.response.status_code != 429:
                raise
            print(f"   rate limited, waiting {wait * 2 or 15}s")
    return fn()


api = KaggleApi(); api.authenticate()
subs = retry(lambda: api.competition_submissions(COMP, page_size=200))
submitted = {int(re.search(r"scriptVersionId=(\d+)", s.url).group(1)) for s in subs}
kernels, page = [], 1
while True:
    got = retry(lambda: api.kernels_list(mine=True, page_size=100, page=page))
    kernels += got
    if len(got) < 100:
        break
    page += 1
recent = sorted({k.ref.split("/")[1] for k in kernels if k.last_run_time and k.last_run_time >= SINCE})
print(len(submitted), "submitted versions;", len(recent), "kernels run since", SINCE.date())

with api.build_kaggle_client() as k:
    c = k.kernels.kernels_api_client

    def fetch(slug, version, fp):
        r = ApiDownloadKernelOutputRequest()
        r.owner_slug, r.kernel_slug, r.version_number, r.file_path = OWNER, slug, version, fp
        return retry(lambda: c.download_kernel_output(r))

    for slug in recent:
        r = ApiGetKernelRequest(); r.user_name, r.kernel_slug = OWNER, slug
        meta = retry(lambda: c.get_kernel(r)).metadata
        if COMP not in " ".join(meta.competition_data_sources or []):
            continue
        print(slug, "versions:", meta.current_version_number)
        for v in range(1, meta.current_version_number + 1):
            if list(ROOT.glob(f"*__{slug}__v{v}__*/experiment.json")):
                continue  # already collected
            if list(SUBMISSIONS.glob(f"*__{slug}__v{v}__*/submission.json")):
                continue  # submitted; submissions/collect.py has it
            try:
                log = fetch(slug, v, "__output__.json")
            except HTTPError as e:
                print(f"   v{v}: no saved run ({e.response.status_code})")
                continue
            sid = int(re.search(r"/kf/(\d+)/", log.url).group(1))
            if sid in submitted:
                continue

            try:
                zr = ApiDownloadKernelOutputZipRequest(); zr.kernel_session_id = sid
                z = zipfile.ZipFile(io.BytesIO(retry(lambda: c.download_kernel_output_zip(zr)).content))
            except HTTPError as e:
                print(f"   v{v}: output zip unavailable ({e.response.status_code}), skipped")
                continue
            d = ROOT / f"new__{slug}__v{v}__unsubmitted__pending"  # relabel() names it below
            (d / "outputs").mkdir(parents=True, exist_ok=True)

            (d / "__output__.json").write_bytes(log.content)
            for fp in ["__notebook__.ipynb", "__results__.html"]:
                try:
                    (d / fp).write_bytes(fetch(slug, v, fp).content)
                except HTTPError as e:
                    print(f"   missing {fp}: {e.response.status_code}")
            z.extractall(d / "outputs")

            info = {  # relabel() fills the score, outcome, error and ab_mean_score, and refines run_date
                "kernel": f"{OWNER}/{slug}", "kernel_title": meta.title, "version": v,
                "script_version_id": sid, "status": "not submitted",
                "run_date": parsedate_to_datetime(log.headers["Last-Modified"]).strftime("%Y-%m-%dT%H:%M:%S")
                if log.headers.get("Last-Modified") else None,
                "offline_public_games_score": None, "note": NOTE,
                "url": f"https://www.kaggle.com/code/{OWNER}/{slug}?scriptVersionId={sid}",
                "output_files": len([i for i in z.infolist() if not i.is_dir()]),
            }
            (d / "experiment.json").write_text(json.dumps(info, indent=2), encoding="utf-8", newline="\r\n")
            print("->", relabel(d))

for p in sorted(ROOT.glob("*/experiment.json")):
    old = p.parent.name
    if json.loads(p.read_text(encoding="utf-8"))["script_version_id"] in submitted:
        print(f"!! {old} has since been submitted; collect it with submissions/collect.py and remove it here")
    new = relabel(p.parent)
    if new != old:
        print(f"renamed {old}\n     -> {new}")

index = [{"folder": p.parent.name, **json.loads(p.read_text(encoding="utf-8"))}
         for p in sorted(ROOT.glob("*/experiment.json"))]
if index:
    fields = list(dict.fromkeys(k for row in index for k in row))
    with open(ROOT / "index.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(index)
print("done", len(index))
