# arcaid3-mount-diag

Kaggle notebook: https://www.kaggle.com/code/habanwer/arcaid3-mount-diag
Build: `python3 build.py` (the v4 benchmark cell is `v4_bench.py`) regenerates `arcaid3-mount-diag.ipynb` and `kernel-metadata.json`.

| Ver | Date (UTC) | What it checks |
|-----|-----------|----------------|
| v1 | 2026-10-14 | `/kaggle/input` tree to depth 3, `df -h`, `mount` |
| v2 | 2026-10-14 | Polls up to 10 min for the TAAF bundle mount, shallow tree, NFS mounts, GPU |
| v3 | 2026-10-22 | v2 + timed full read of model weights / wheels, writes `read_bench.json` and an OK / SLOW / DEGRADED verdict |
| v4 | 2026-10-22 | v2 mount check + 45 s probes at 1/4/8/16 parallel streams and 8 ranged readers in one file (fresh files each, no cache), drafter (NFS) and pennyroyal (gcsfuse) single-stream, then a full parallel copy of the model to `/tmp/weights` with the best stream count (40 min budget). Writes `read_bench_v4.json` |

v3 exists because of discussion 751598: mounts appear instantly, but reading weights
went from 4-5 min to ~40 min, so vLLM isn't ready in time and submissions score 0.00.
Verdict thresholds use the estimated full load time: <=10 min OK, <=25 SLOW, else DEGRADED.
The read stops after 45 min and extrapolates from there. A commit run uses a different
VM than the scored rerun, so an OK verdict lowers the risk of a 0.00 but doesn't rule it out.

v3 result (2026-10-22 21:10 UTC run): main model is 168.8 GiB / 49 files, read at a flat
42-49 MiB/s single-stream; final: 129.4 GiB in the 45 min budget, avg 49.1 MiB/s, VERDICT DEGRADED
(~58.7 min est. full load). The mounts had changed since v2: models on NFS
192.168.5.2 (was 192.168.11.2), datasets on `fuse.gcsfuse` (was NFS). v4 tests whether the
cap is per stream, which would make "parallel copy to local disk, then start vLLM" a workaround.

v4 result (2026-10-22 21:32 UTC run, `read_bench_v4.json`): per-stream cap confirmed.
Fresh-file aggregate read: 1 stream 44.7 MiB/s, 4 -> 149.7, 8 -> 282.9, 16 -> 499.3 MiB/s
(x11.2, ~5.8 min for 168.8 GiB). 8 ranged readers in one file: 345.5 MiB/s. Drafter (NFS)
48.6, pennyroyal (gcsfuse) 110.0 MiB/s single-stream. The copy to `/tmp/weights` failed
after ~269 s with `[Errno 30] Read-only file system` despite `df` showing ~1.1 TB free, so
copy-to-local is NOT a safe workaround (its 374.7 MiB/s rate is cache-inflated: only 27.8 of
98.5 GiB were fresh). Workaround: read/prefetch weights from the mount with 8-16 parallel
streams (or a multithreaded vLLM loader), and keep a generous vLLM startup wait.
