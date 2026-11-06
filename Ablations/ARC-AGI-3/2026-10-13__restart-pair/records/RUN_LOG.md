# Restart pair: run log

| Time (UTC) | Event |
|---|---|
| 2026-10-14 05:36 | `habanwer/arcaid3-pair-restart-r1` v1 pushed (restart v2, flag 100000). QUEUED. |
| 2026-10-14 05:36 | `habanwer/arcaid3-pair-flag0-r1` push refused: "Maximum batch GPU session count of 2 reached". |

**Why the control could not start:** the account's other GPU session was the user's own `habanwer/gemma4-deva-l3-s34-v4-12b`, started 04:59 and still running. The control is retried every 20 minutes until a slot frees.

**What this changes:** the arms will run on the same day, but not side by side. The offset between their start times is recorded here when the control starts, and is reported with the result.
| 2026-10-14 05:41 | Restart arm started (GPU allocated). It finished at 07:52: healthy, 25 games, no tracebacks. |
| 2026-10-14 05:59 → 10:37 | The control-push retry was delivered late: the session hit its usage limit. |
| 2026-10-14 10:38, 10:39, 10:42 | `arcaid3-pair-flag0-r1` v1–v3 errored in the first cell that copies the source bundle: `cp: cannot stat '/kaggle/input/datasets/dfranzen/taaf-kaggle-source-bundle-copy'`. |
| 2026-10-14 10:40–10:43 | `habanwer/arcaid3-mount-diag` (private) ran on CPU and on an RTX PRO 6000, with the same sources and image. All inputs were mounted at the expected paths at t=0, so the dataset was fine. |
| 2026-10-14 10:43 | The identical control notebook was pushed under a new slug, `habanwer/arcaid3-pair-flag0-r1b`. It runs normally. The old slug appears to carry a stuck mount state. `compare_pair.py` now reads `-r1b`. |

**Start-time offset between the arms:** 5 h 02 min (restart 05:41, control 10:43 UTC), same day.

**Restart arm, preliminary.** Not judged until the control finishes.
- Score 50.48, 109 levels.
- 7 restarts. 5 fired on resumed no-action turns, which v1 could never reach. All 7 fired late in the clock, at 5,083–7,190 s of 7,254.
- The log records no completion after any restart.
