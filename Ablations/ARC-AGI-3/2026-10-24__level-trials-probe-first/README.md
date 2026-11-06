# level-trials-probe-first

**Question.** Does the probe-first governor change which levels are cleared?

| | |
|---|---|
| **Design** | The A3 design: 183 cold-start paired trials per round, probe-first on (`arcaid3-lt-pf-on-r*`) vs off (`arcaid3-lt-pf-off-r*`), two rounds. `arcaid3-lt-pf-on-r2` was also submitted and ended in a Kaggle error. |
| **Decision rule** | Primary gate (+15% levels, McNemar p < 0.05) and the action-ratio limit in `ARCAID/probe-first/README.md`, committed 2026-10-23 10:34 UTC; all five gates in code in `analysis/lt_analysis.py`, committed 2026-10-24 07:20 UTC; first result 2026-10-24 16:27 UTC. `DECISION_RULE.md` here is the plan of 2026-10-23. |
| **Recorded outcome** | From `analysis/pooled__paired-analysis.txt`: off 116, on 134, lift +15.5%, exact McNemar p = 0.022; gates: lift PASS, p PASS, action ratio PASS, deaths PASS, no-action token share (≤ 45%) **FAIL** (51%); verdict **DO NOT submit**. Round 1 alone: +19.0%, p = 0.043; round 2 alone: +12.1%, p = 0.281. |
| **Code** | `analysis/`, `ARCAID/probe-first/` |
| **Runs** | Offline or in `Submissions/ARC-AGI-3/`; no Kaggle runs in this folder |

`records/` holds the write-ups as they were written at the time. The outcome above is quoted from the analysis outputs, not reinterpreted.
