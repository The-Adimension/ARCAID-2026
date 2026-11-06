"""Download every saved version of the third-party notebooks our notebooks were built on.

  python -I pull_bases.py OUT_DIR owner/slug [owner/slug ...]

Writes OUT_DIR/<owner>__<slug>/v<N>.ipynb (the executed notebook as Kaggle stored it) and index.json
(version, scriptVersionId, papermill start time). Used by Tools/lineage/infer_parents.py to find which
version a notebook of ours was built from. Needs Kaggle API credentials.
"""
import json, re, sys, time
from pathlib import Path
from requests.exceptions import HTTPError, ConnectionError as CE, ChunkedEncodingError
from kaggle.api.kaggle_api_extended import KaggleApi
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest, ApiDownloadKernelOutputRequest


def retry(fn):
    for w in (0, 10, 30, 60, 120):
        time.sleep(w)
        try:
            return fn()
        except HTTPError as e:
            if e.response is None or e.response.status_code not in (429, 500, 502, 503):
                raise
        except (CE, ChunkedEncodingError):
            pass
    return fn()


out = Path(sys.argv[1]); api = KaggleApi(); api.authenticate()
with api.build_kaggle_client() as k:
    c = k.kernels.kernels_api_client
    for ref in sys.argv[2:]:
        owner, slug = ref.split("/")
        d = out / f"{owner}__{slug}"; d.mkdir(parents=True, exist_ok=True)
        q = ApiGetKernelRequest(); q.user_name, q.kernel_slug = owner, slug
        n = retry(lambda: c.get_kernel(q)).metadata.current_version_number
        index = []
        for v in range(1, n + 1):
            r = ApiDownloadKernelOutputRequest()
            r.owner_slug, r.kernel_slug, r.version_number, r.file_path = owner, slug, v, "__notebook__.ipynb"
            try:
                res = retry(lambda: c.download_kernel_output(r))
            except HTTPError as e:
                index.append({"version": v, "error": e.response.status_code}); continue
            (d / f"v{v}.ipynb").write_bytes(res.content)
            m = re.search(r"/kf/(\d+)/", res.url or "")
            try:
                pm = json.loads(res.content).get("metadata", {}).get("papermill", {})
            except Exception:
                pm = {}
            index.append({"version": v, "script_version_id": m and int(m.group(1)),
                          "start_time": pm.get("start_time"), "end_time": pm.get("end_time")})
        (d / "index.json").write_text(json.dumps({"ref": ref, "versions": index}, indent=1))
        print(ref, n, "versions")
