# Analysis tools

| Script | What it does |
|---|---|
| `replay_tables.py` | Replays every recorded ARC-AGI-3 action history on the official engine. Writes `replay.csv`, `levels.csv.gz` and `actions.csv.gz` to `2026-Paper-Track/data/`. |
| `extract_zip_tables.py` | Streams the run-output zips and writes `turns.csv.gz`, `calls.csv.gz` and `events.csv.gz` |
| `check_tables.py` | Cross-checks the tables and writes `2026-Paper-Track/data/CHECKS.md` |
| Dated folders (`2026-10-05/`, `2026-10-10/`, `2026-10-11-rubiq/`, `2026-10-17/`) and `extract_turns.py` | Analyses from the competition period, kept as they were run |

The analysis plan these tables serve is [`../../2026-Paper-Track/ANALYSIS-PLAN.md`](../../2026-Paper-Track/ANALYSIS-PLAN.md).
