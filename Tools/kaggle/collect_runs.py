"""Pull every ARC Prize 2026 notebook version of one Kaggle user, with its log and outputs.

For each kernel version that used an ARC Prize 2026 competition as input, this writes to RAW/<slug>/v<N>/:
  __notebook__.ipynb   the executed notebook exactly as Kaggle stored it
  __output__.json      the Save & Run log (stream, time, text)
  meta.json            kernel title, version, scriptVersionId, sources, visibility
  outputs-manifest.csv every file of the output zip: path, bytes, sha256
  keep/                the small summary outputs (summary.txt, benchmark.json, submission files)
The full output zip is streamed to a temporary file, hashed and deleted; with --keep-zips it is kept.

These are Save & Run (public-game) logs. Kaggle does not release the log of the hidden-set rerun.

Usage: python -I collect_runs.py RAW_DIR [--owner habanwer] [--keep-zips]
Re-running skips versions already collected. Needs Kaggle API credentials.
"""
import argparse, csv, hashlib, io, json, os, re, shutil, sys, tempfile, time, zipfile
from pathlib import Path
from requests.exceptions import HTTPError, ConnectionError as ReqConnectionError, ChunkedEncodingError, Timeout
from kaggle.api.kaggle_api_extended import KaggleApi
from kagglesdk.kernels.types.kernels_api_service import (
    ApiGetKernelRequest, ApiDownloadKernelOutputRequest, ApiDownloadKernelOutputZipRequest)

COMPS = ("arc-prize-2026-arc-agi-3", "arc-prize-2026-arc-agi-2")
KEEP = re.compile(r"^(summary\.txt|benchmark\.json|submission\.json|submission\.parquet|score\.json)$")


def retry(fn):
    for wait in (0, 10, 30, 60, 120, 240, 480):
        time.sleep(wait)
        try:
            return fn()
        except HTTPError as e:
            if e.response is None or e.response.status_code not in (429, 500, 502, 503):
                raise
        except (ReqConnectionError, ChunkedEncodingError, Timeout):
            pass                                   # dropped connection: wait and try again
    return fn()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw")
    ap.add_argument("--owner", default="habanwer")
    ap.add_argument("--keep-zips", action="store_true")
    ap.add_argument("--local", action="append", default=[],
                    help="a folder of earlier collections (<date>__<slug>__v<N>__*/outputs); its outputs are hashed "
                         "locally instead of downloading the zip again. Caution: an earlier copy may lack files "
                         "(e.g. __pycache__ removed before committing); ARCAID-2026 re-hashed every such manifest "
                         "from the Kaggle zip on 2026-11-06")
    ap.add_argument("--shard", default="0/1", help="i/n: handle only every n-th kernel, starting at i (parallel runs)")
    a = ap.parse_args()
    shard_i, shard_n = map(int, a.shard.split("/"))
    raw = Path(a.raw)
    local = {}
    for root in a.local:
        for d in Path(root).glob("*__*__v*__*"):
            m = re.match(r"\d{4}-\d{2}-\d{2}__(.+?)__v(\d+)__", d.name)
            if m and (d / "outputs").is_dir():
                local[(m.group(1), int(m.group(2)))] = d
    api = KaggleApi(); api.authenticate()

    slugs, page = [], 1
    while True:
        r = retry(lambda: api.kernels_list(user=a.owner, page=page, page_size=100, sort_by="dateRun"))
        slugs += [k.ref.rstrip("/").split("/")[-1] for k in r if k.ref]
        if len(r) < 100:
            break
        page += 1

    with api.build_kaggle_client() as k:
        c = k.kernels.kernels_api_client
        for k_i, slug in enumerate(slugs):
            if k_i % shard_n != shard_i:
                continue
            q = ApiGetKernelRequest(); q.user_name, q.kernel_slug = a.owner, slug
            try:
                m = retry(lambda: c.get_kernel(q)).metadata
            except HTTPError as e:
                print(slug, "metadata", e.response.status_code); continue
            comps = [s for s in (m.competition_data_sources or []) if s in COMPS]
            if not comps:
                continue
            for v in range(1, (m.current_version_number or 0) + 1):
                d = raw / slug / f"v{v}"
                if (d / "meta.json").exists():
                    continue
                d.mkdir(parents=True, exist_ok=True)

                def fetch(fp):
                    r = ApiDownloadKernelOutputRequest()
                    r.owner_slug, r.kernel_slug, r.version_number, r.file_path = a.owner, slug, v, fp
                    return retry(lambda: c.download_kernel_output(r))

                sid, files = None, {}
                for fp in ("__notebook__.ipynb", "__output__.json"):
                    try:
                        res = fetch(fp)
                        (d / fp).write_bytes(res.content)
                        mm = re.search(r"/kf/(\d+)/", res.url or "")
                        sid = sid or (mm and int(mm.group(1)))
                        files[fp] = hashlib.sha256(res.content).hexdigest()
                    except HTTPError as e:
                        files[fp] = f"unavailable ({e.response.status_code})"
                n_out = 0
                if (slug, v) in local:
                    src = local[(slug, v)]
                    with open(d / "outputs-manifest.csv", "w", newline="") as mf:
                        w = csv.writer(mf); w.writerow(["path", "bytes", "sha256"])
                        for f in sorted(p for p in (src / "outputs").rglob("*") if p.is_file()):
                            rel = f.relative_to(src / "outputs").as_posix()
                            w.writerow([rel, f.stat().st_size, hashlib.sha256(f.read_bytes()).hexdigest()]); n_out += 1
                            if KEEP.match(rel):
                                (d / "keep").mkdir(exist_ok=True); shutil.copy(f, d / "keep" / rel)
                    files["outputs"] = f"hashed from local copy {src.name}"
                elif sid:
                    try:
                        zr = ApiDownloadKernelOutputZipRequest(); zr.kernel_session_id = sid
                        content = retry(lambda: c.download_kernel_output_zip(zr).content)  # body read inside retry
                        with tempfile.NamedTemporaryFile(dir=raw, suffix=".zip", delete=False) as tf:
                            tf.write(content); tmp = tf.name
                        del content
                        with zipfile.ZipFile(tmp) as z, open(d / "outputs-manifest.csv", "w", newline="") as mf:
                            w = csv.writer(mf); w.writerow(["path", "bytes", "sha256"])
                            for info in z.infolist():
                                if info.is_dir():
                                    continue
                                h = hashlib.sha256()
                                with z.open(info) as f:
                                    for chunk in iter(lambda: f.read(1 << 20), b""):
                                        h.update(chunk)
                                w.writerow([info.filename, info.file_size, h.hexdigest()]); n_out += 1
                                if KEEP.match(info.filename):
                                    (d / "keep").mkdir(exist_ok=True)
                                    (d / "keep" / info.filename).write_bytes(z.read(info))
                        if a.keep_zips:
                            shutil.move(tmp, d / "outputs.zip")
                        else:
                            os.remove(tmp)
                    except HTTPError as e:
                        files["outputs"] = f"unavailable ({e.response.status_code})"
                meta = {"owner": a.owner, "slug": slug, "title": m.title, "version": v,
                        "script_version_id": sid, "private_now": m.is_private,
                        "competition_sources": comps,
                        "dataset_sources": list(m.dataset_data_sources or []),
                        "model_sources": list(m.model_data_sources or []),
                        "kernel_sources": list(m.kernel_data_sources or []),
                        "output_files": n_out, "files": files,
                        "url": f"https://www.kaggle.com/code/{a.owner}/{slug}" + (f"?scriptVersionId={sid}" if sid else ""),
                        "collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
                (d / "meta.json").write_text(json.dumps(meta, indent=1))
                print(slug, f"v{v}", "sid", sid, "outputs", n_out, flush=True)


if __name__ == "__main__":
    main()
