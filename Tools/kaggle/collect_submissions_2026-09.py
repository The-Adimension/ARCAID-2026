"""Pull every ARC-AGI-3 competition submission's notebook version + full outputs.

Usage (from the repo root):  .venv/Scripts/python.exe submissions/collect.py
Re-running only downloads submissions that are not already collected (matched by
scriptVersionId), and refreshes the score/status of those that are, renaming the
folder when its score changed (e.g. a submission collected while still pending).
"""
import csv, io, json, re, time, zipfile
from pathlib import Path
from requests.exceptions import HTTPError
from kaggle.api.kaggle_api_extended import KaggleApi
from kagglesdk.kernels.types.kernels_api_service import (
    ApiGetKernelRequest, ApiDownloadKernelOutputRequest, ApiDownloadKernelOutputZipRequest)

COMP = "arc-prize-2026-arc-agi-3"
OWNER = "habanwer"
ROOT = Path(__file__).resolve().parent
PAGE = 200


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


def slug_sid(s):
    return (re.search(r"/code/[^/]+/([^?]+)", s.url).group(1),
            int(re.search(r"scriptVersionId=(\d+)", s.url).group(1)))


def scores(s):
    return {"public_score": s.public_score, "private_score": s.private_score,
            "status": str(s.status), "description": s.description}


api = KaggleApi(); api.authenticate()
subs = retry(lambda: api.competition_submissions(COMP, page_size=PAGE))
print(len(subs), "submissions")
if len(subs) >= PAGE:
    print(f"WARNING: got a full page of {PAGE}; older submissions may be missing")

# Refresh the ones already collected, and find the rest.
collected = {json.loads(p.read_text(encoding="utf-8"))["script_version_id"]: p.parent
             for p in ROOT.glob("*/submission.json")}
todo = []
for s in subs:
    slug, sid = slug_sid(s)
    if sid not in collected:
        todo.append(s)
        continue
    d = collected[sid]
    info = json.loads((d / "submission.json").read_text(encoding="utf-8"))
    if any(info[k] != v for k, v in scores(s).items()):
        info.update(scores(s))
        (d / "submission.json").write_text(json.dumps(info, indent=2), encoding="utf-8", newline="\r\n")
        print("updated", d.name)
    name = f"{s.date:%Y-%m-%d}__{slug}__v{info['version']}__score-{s.public_score}"
    if d.name != name:
        d.rename(ROOT / name)
        print(f"renamed {d.name}\n     -> {name}")

with api.build_kaggle_client() as k:
    c = k.kernels.kernels_api_client

    def fetch(slug, version, fp):
        r = ApiDownloadKernelOutputRequest()
        r.owner_slug, r.kernel_slug, r.version_number, r.file_path = OWNER, slug, version, fp
        return retry(lambda: c.download_kernel_output(r))

    # Map scriptVersionId -> (version number, run log) for kernels with uncollected submissions,
    # newest version first, stopping once every wanted submission of that kernel is found.
    vmap, titles = {}, {}
    for slug in sorted({slug_sid(s)[0] for s in todo}):
        want = {slug_sid(s)[1] for s in todo if slug_sid(s)[0] == slug}
        r = ApiGetKernelRequest(); r.user_name, r.kernel_slug = OWNER, slug
        meta = retry(lambda: c.get_kernel(r)).metadata
        titles[slug] = meta.title
        print(slug, "versions:", meta.current_version_number)
        for v in range(meta.current_version_number, 0, -1):
            try:
                log = fetch(slug, v, "__output__.json")
            except HTTPError as e:
                print(f"   v{v}: no saved run ({e.response.status_code})")
                continue
            sid = int(re.search(r"/kf/(\d+)/", log.url).group(1))
            vmap[sid] = (v, log)
            if want <= vmap.keys():
                break

    for s in sorted(todo, key=lambda s: s.date):
        slug, sid = slug_sid(s)
        if sid not in vmap:
            print(f"!! {slug} scriptVersionId={sid}: no saved version matches, skipped")
            continue
        v, log = vmap[sid]
        try:
            zr = ApiDownloadKernelOutputZipRequest(); zr.kernel_session_id = sid
            z = zipfile.ZipFile(io.BytesIO(retry(lambda: c.download_kernel_output_zip(zr)).content))
        except HTTPError as e:
            print(f"!! {slug} v{v}: output zip unavailable ({e.response.status_code}), skipped")
            continue
        name = f"{s.date:%Y-%m-%d}__{slug}__v{v}__score-{s.public_score}"
        d = ROOT / name
        (d / "outputs").mkdir(parents=True, exist_ok=True)
        print("->", name)

        (d / "__output__.json").write_bytes(log.content)
        for fp in ["__notebook__.ipynb", "__results__.html"]:
            try:
                (d / fp).write_bytes(fetch(slug, v, fp).content)
            except HTTPError as e:
                print(f"   missing {fp}: {e.response.status_code}")
        z.extractall(d / "outputs")

        info = {
            "kernel": f"{OWNER}/{slug}", "kernel_title": titles[slug], "version": v,
            "script_version_id": sid, "submission_ref": s.ref, "submitted": s.date.isoformat(),
            **scores(s), "url": "https://www.kaggle.com" + s.url,
            "output_files": len([i for i in z.infolist() if not i.is_dir()]),
        }
        (d / "submission.json").write_text(json.dumps(info, indent=2), encoding="utf-8", newline="\r\n")

# Rebuild the index from every collected folder.
index = [{"folder": p.parent.name, **json.loads(p.read_text(encoding="utf-8"))}
         for p in sorted(ROOT.glob("*/submission.json"))]
fields = list(dict.fromkeys(k for row in index for k in row))
with open(ROOT / "index.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(index)
print("done", len(index))
