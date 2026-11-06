# ARCAID3: restart events of this run (never raises; the run's result does not depend on it).
import json, os
from pathlib import Path
try:
    path = Path(os.environ.get("ARC3_STUCK_RESTART_LOG", "/kaggle/working/stuck_restarts.jsonl"))
    events = [json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []
    fired = [e for e in events if e.get("event") == "restart"]
    done = [e for e in events if e.get("event") == "completed_after_restart"]
    print("ARCAID3_RESTART_FINAL", json.dumps({
        "threshold_tokens": int(os.environ.get("ARC3_STUCK_RESTART_TOKENS", "0") or 0),
        "restarts": len(fired), "completed_after_restart": len(done),
        "levels_restarted": sorted({(e["state_path"], e["level"]) for e in fired}),
    }, default=str))
    for e in events:
        print(" ", json.dumps(e, default=str))
except Exception as exc:
    print("ARCAID3_RESTART_FINAL unavailable:", repr(exc))
