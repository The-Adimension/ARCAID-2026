"""Read each notebook's current visibility on Kaggle and write it to Documentation/KAGGLE-VISIBILITY.csv.

  python -I check_visibility.py REPO_ROOT

Uses Tools/catalogue/placement.csv for the list of notebooks. Run it right before a release check:
Tools/release/release_check.py reads this file when it exists. Needs the owner's Kaggle API credentials.
"""
import csv, sys, time
from pathlib import Path
from kaggle.api.kaggle_api_extended import KaggleApi
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest

root = Path(sys.argv[1]); api = KaggleApi(); api.authenticate()
rows = []
with api.build_kaggle_client() as k:
    c = k.kernels.kernels_api_client
    for r in csv.DictReader(open(root / "Tools/catalogue/placement.csv")):
        if r["place"] == "none":
            continue
        slug = r.get("kaggle_slug_now") or r["kernel"]     # follow a rename made on Kaggle after collection
        q = ApiGetKernelRequest(); q.user_name, q.kernel_slug = "habanwer", slug
        vis = "error"
        for w in (0, 10, 30, 60):
            time.sleep(w)
            try:
                vis = "private" if c.get_kernel(q).metadata.is_private else "public"; break
            except Exception:
                pass
        rows.append({"kernel": f"habanwer/{r['kernel']}", "track": r["track"], "place": r["place"],
                     "visibility": vis, "url": f"https://www.kaggle.com/code/habanwer/{slug}",
                     "checked_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
        time.sleep(0.5)
with open(root / "Documentation/KAGGLE-VISIBILITY.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(sum(r["visibility"] == "private" for r in rows), "private of", len(rows))
