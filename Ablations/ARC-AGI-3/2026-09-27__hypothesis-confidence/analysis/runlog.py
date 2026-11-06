"""Append a timestamped entry to the hypothesis-test run log (experiments/hypothesis-test/RUNLOG.md)."""
import datetime, pathlib, sys
import os
LOG = pathlib.Path(__file__).resolve().parents[2] / "experiments" / os.environ.get("RUNLOG_DIR", "hypothesis-test") / "RUNLOG.md"

def log(step, msg):
    ts = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    line = f"- `{ts}` **{step}**: {msg}\n"
    with open(LOG, 'a') as f:
        f.write(line)
    print(line, end='', flush=True)

if __name__ == '__main__':
    log(sys.argv[1], ' '.join(sys.argv[2:]))
