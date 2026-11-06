"""Collect public ARC-AGI-3 Kaggle kernels of other teams into external_submission/.

Layout mirrors submissions/: one folder per kernel version with
__notebook__.ipynb, __output__.json (the run log), outputs/ and submission.json,
plus a rebuilt index.csv.

What is kept and what is not:
  * Only the kernel's CURRENT version is available through the API; it may not
    be the version the team submitted. Its outputs are a Save & Run on the public
    games (the competition rerun's play is never returned by Kaggle).
  * HTML files (solver analysis, __results__.html) are skipped by choice.
  * Vendored Python environments / CUDA caches are never requested.
  * A file whose Content-Length exceeds MAX_FILE is skipped before its body is
    read (GitHub rejects files over 100 MB).
  * Kaggle exposes no per-notebook score for other teams; folder names carry the
    TEAM's best public score from the leaderboard snapshot, not this notebook's.

GET requests only. Run from the repo root:
    python external_submission/collect_external.py [--limit N]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

API = "https://www.kaggle.com/api/v1"
ROOT = Path(__file__).resolve().parent
MAX_FILE = 95 * 1024 * 1024
MIN_FREE = 4 * 1024 ** 3
PACE = 2.0
WORKERS = 8

VENDOR = re.compile(
    r"(\.py|\.pyc|\.pyi|\.so(\.\d+)*|\.mo|\.h|\.hpp|\.cuh?|\.pth|\.pxd|\.typed|\.whl|\.a|\.cubin|\.ptx|"
    r"\.fatbin|\.hsaco)$|(^|/)(INSTALLER|METADATA|RECORD|REQUESTED|WHEEL|LICENSE[^/]*|NOTICE[^/]*|COPYING[^/]*|"
    r"top_level\.txt|entry_points\.txt|AUTHORS[^/]*)$|(^|/)N=\d+,K=\d+,|(^|/)E=\d+,N=\d+,|"
    r"(^|/)(site-packages|dist-packages|__pycache__|\.git|[^/]+\.dist-info|[^/]+\.egg-info)/"
)
HTML = re.compile(r"\.html?$", re.I)


def get(url: str, tries: int = 6) -> bytes:
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=180) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and i < tries - 1:
                ra = e.headers.get("Retry-After")
                time.sleep(float(ra) if ra and ra.replace(".", "", 1).isdigit() else 15 * (i + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if i < tries - 1:
                time.sleep(10 * (i + 1))
                continue
            raise
    raise RuntimeError("unreachable")


def api(path: str, **q) -> dict:
    return json.loads(get(f"{API}{path}?" + urllib.parse.urlencode(q)))


def clean_url(url: str) -> str:
    """Percent-encode the path (file names may contain spaces or control characters)."""
    url = re.sub(r"[\x00-\x20\x7f]", lambda m: "%%%02X" % ord(m.group()), url)
    s = urllib.parse.urlsplit(url)
    path = urllib.parse.quote(urllib.parse.unquote(s.path), safe="/:@!$&'()*+,;=-._~")
    return urllib.parse.urlunsplit((s.scheme, s.netloc, path, s.query, s.fragment))


def fetch_file(url: str, dest: Path) -> tuple[str, int, str | None]:
    """Stream url to dest unless its declared size exceeds MAX_FILE. Returns (status, bytes, sha256)."""
    url = clean_url(url)
    for i in range(5):
        try:
            with urllib.request.urlopen(url, timeout=300) as r:
                size = int(r.headers.get("Content-Length") or -1)
                if size > MAX_FILE:
                    return "skipped_over_95MB", size, None
                dest.parent.mkdir(parents=True, exist_ok=True)
                h = hashlib.sha256()
                n = 0
                with open(dest, "wb") as f:
                    while chunk := r.read(1 << 20):
                        f.write(chunk)
                        h.update(chunk)
                        n += len(chunk)
                        if n > MAX_FILE:
                            f.close()
                            dest.unlink(missing_ok=True)
                            return "skipped_over_95MB", n, None
                return "saved", n, h.hexdigest()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and i < 4:
                time.sleep(10 * (i + 1))
                continue
            return f"error_http_{e.code}", 0, None
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if i < 4:
                time.sleep(10 * (i + 1))
                continue
            return "error_network", 0, None
        except Exception as e:  # one bad file must not fail the whole kernel
            return f"error_{type(e).__name__}", 0, None
    return "error_retries", 0, None


def safe_rel(name: str) -> Path | None:
    name = re.sub(r"[\x00-\x1f\x7f]", "_", name)
    p = Path(name)
    if p.is_absolute() or ".." in p.parts:
        return None
    return p


def collect(row: dict) -> dict | None:
    owner, slug = row["owner"], row["slug"]
    pulled = api("/kernels/pull", userName=owner, kernelSlug=slug)
    md = pulled["metadata"]
    time.sleep(PACE)
    files, log, tok, pages = [], None, None, 0
    while True:
        q = {"userName": owner, "kernelSlug": slug, "pageSize": 500}
        if tok:
            q["pageToken"] = tok
        out = api("/kernels/output", **q)
        pages += 1
        if log is None:
            log = out.get("log") or ""
        files += out.get("files", [])
        tok = out.get("nextPageToken")
        time.sleep(PACE)
        if not tok:
            break
    sids = sorted({m.group(1) for f in files if (m := re.search(r"/kf/(\d+)/", f.get("url", "")))})
    version = md.get("currentVersionNumber")
    date = (row.get("last_run_time") or md.get("lastRunTime") or "")[:10] or "unknown-date"
    score = row["team_best_public_score"]
    name = f"{date}__{owner}__{slug}__v{version}__teambest-{score}"
    d = ROOT / name
    tmp = ROOT / (".partial__" + name)
    shutil.rmtree(tmp, ignore_errors=True)
    (tmp / "outputs").mkdir(parents=True)

    blob = pulled.get("blob", {}).get("source")
    if blob:
        (tmp / "__notebook__.ipynb").write_text(blob, encoding="utf-8")
    (tmp / "__output__.json").write_text(log, encoding="utf-8")

    def one(f: dict) -> dict:
        fname = f.get("fileName") or ""
        rel = safe_rel(fname)
        if rel is None:
            status, size, sha = "skipped_unsafe_path", 0, None
        elif VENDOR.search(fname):
            status, size, sha = "skipped_vendored_env", 0, None
        elif HTML.search(fname):
            status, size, sha = "skipped_html", 0, None
        else:
            status, size, sha = fetch_file(f["url"], tmp / "outputs" / rel)
        return {"path": fname, "status": status, "bytes": size, "sha256": sha}

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        manifest = list(pool.map(one, files))
    stats: dict[str, int] = {}
    for m in manifest:
        stats[m["status"]] = stats.get(m["status"], 0) + 1

    saved = [m for m in manifest if m["status"] == "saved"]
    info = {
        "kernel": f"{owner}/{slug}",
        "kernel_title": md.get("title"),
        "version": version,
        "version_note": "current version at collection time; may differ from the version the team submitted",
        "script_version_id": int(sids[0]) if len(sids) == 1 else sids,
        "last_run_time": row.get("last_run_time"),
        "public_score": None,
        "score_note": "Kaggle exposes no per-notebook score for other teams; see team_best_public_score",
        "team_name": row["team_name"],
        "team_rank": int(row["team_rank"]),
        "team_best_public_score": score,
        "team_submission_count": row["team_submission_count"],
        "leaderboard_snapshot": "publicleaderboard-2026-10-01T11:43:58 (sha256 8f64b13baf0dd1ba...)",
        "url": f"https://www.kaggle.com/code/{owner}/{slug}",
        "datasets": md.get("datasetDataSources"),
        "models": md.get("modelDataSources"),
        "competitions": md.get("competitionDataSources"),
        "machine_shape": md.get("machineShape"),
        "docker_image": md.get("dockerImage"),
        "enable_internet": md.get("enableInternet"),
        "licence": "not exposed by the Kaggle API; see the notebook page",
        "output_files": len(files),
        "output_pages": pages,
        "saved_files": len(saved),
        "saved_bytes": sum(m["bytes"] for m in saved),
        "file_status_counts": stats,
        "collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (tmp / "submission.json").write_text(json.dumps(info, indent=2), encoding="utf-8", newline="\r\n")
    with open(tmp / "files.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "status", "bytes", "sha256"])
        w.writeheader()
        w.writerows(manifest)
    shutil.rmtree(d, ignore_errors=True)
    tmp.rename(d)
    return info


def rebuild_index() -> int:
    index = [{"folder": p.parent.name, **json.loads(p.read_text(encoding="utf-8"))}
             for p in sorted(ROOT.glob("*/submission.json")) if not p.parent.name.startswith(".")]
    if not index:
        return 0
    flat = []
    for r in index:
        r = dict(r)
        for k in ("datasets", "models", "competitions", "file_status_counts", "script_version_id"):
            if isinstance(r.get(k), (list, dict)):
                r[k] = json.dumps(r[k], sort_keys=True)
        flat.append(r)
    fields = list(dict.fromkeys(k for row in flat for k in row))
    with open(ROOT / "index.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(flat)
    return len(index)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    rows = list(csv.DictReader(open(ROOT / "selection.csv", encoding="utf-8")))
    done = {json.loads(p.read_text(encoding="utf-8"))["kernel"]
            for p in ROOT.glob("*/submission.json") if not p.parent.name.startswith(".")}
    failed_path = ROOT / "failures.csv"
    failed = {r["ref"] for r in csv.DictReader(open(failed_path, encoding="utf-8"))} if failed_path.exists() else set()
    done |= failed
    n = 0
    for row in rows:
        if row["ref"] in done:
            continue
        if args.limit is not None and n >= args.limit:
            break
        if shutil.disk_usage(ROOT).free < MIN_FREE:
            print("STOP: free disk below 4 GB", flush=True)
            break
        try:
            info = collect(row)
            print(f"OK #{row['team_rank']} {row['ref']}: saved {info['saved_files']} files "
                  f"{info['saved_bytes'] / 1e6:.1f} MB {info['file_status_counts']}", flush=True)
        except Exception as e:  # keep going; record the failure
            print(f"FAIL #{row['team_rank']} {row['ref']}: {type(e).__name__}: {e}", flush=True)
            new = not failed_path.exists()
            with open(failed_path, "a", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                if new:
                    w.writerow(["ref", "team_rank", "error", "at"])
                w.writerow([row["ref"], row["team_rank"], f"{type(e).__name__}: {e}"[:300],
                            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())])
        n += 1
    print("index rows:", rebuild_index(), flush=True)


if __name__ == "__main__":
    main()
