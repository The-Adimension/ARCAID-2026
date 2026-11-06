"""Write every competition submission of the authenticated Kaggle user to a CSV per track.

  python -I collect_submissions.py OUT_ROOT

Writes OUT_ROOT/ARC-AGI-3/submissions.csv and OUT_ROOT/ARC-AGI-2/submissions.csv, oldest first.
`selected` comes from OUT_ROOT/<track>/selected.csv (submission refs the author selected for final
scoring); the Kaggle API does not expose the selection flag. `after_deadline` is set for submissions
made after the deadline the API reports, and for those listed in OUT_ROOT/<track>/late.csv (submissions
the public leaderboard did not count, with the evidence in its `source` column). Needs Kaggle API credentials.
"""
import csv, re, sys, time
from pathlib import Path
from kaggle.api.kaggle_api_extended import KaggleApi

TRACKS = {"ARC-AGI-3": ("arc-prize-2026-arc-agi-3", "2026-11-02T23:59:00"),
          "ARC-AGI-2": ("arc-prize-2026-arc-agi-2", "2026-11-02T23:59:00")}
root = Path(sys.argv[1]); api = KaggleApi(); api.authenticate()
for track, (comp, deadline) in TRACKS.items():
    subs = api.competition_submissions(comp, page_size=200)
    sel_file = root / track / "selected.csv"
    selected = {r["submission_ref"] for r in csv.DictReader(open(sel_file))} if sel_file.exists() else set()
    late_file = root / track / "late.csv"      # submissions the leaderboard did not count (see its source column)
    late = {r["submission_ref"] for r in csv.DictReader(open(late_file))} if late_file.exists() else set()
    rows = []
    for s in subs:
        url = "https://www.kaggle.com" + s.url if s.url and s.url.startswith("/") else (s.url or "")
        m = re.search(r"/code/([^/]+)/([^?]+)\?scriptVersionId=(\d+)", url)
        date = str(s.date).replace(" ", "T")
        rows.append({"submission_ref": str(s.ref), "submitted_utc": date,
                     "kernel": m and f"{m.group(1)}/{m.group(2)}", "script_version_id": m and m.group(3),
                     "status": str(s.status).split(".")[-1], "public_score": s.public_score or "",
                     "private_score": s.private_score or "",
                     "after_deadline": "yes" if date > deadline or str(s.ref) in late else "",
                     "selected": "yes" if str(s.ref) in selected else "",
                     "description": (s.description or "").replace("\r", " ").strip(), "url": url})
    rows.sort(key=lambda r: r["submitted_utc"])
    (root / track).mkdir(parents=True, exist_ok=True)
    with open(root / track / "submissions.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(track, len(rows), "submissions,", sum(r["selected"] == "yes" for r in rows), "selected")
