import os, time, glob, json, shutil, threading
from concurrent.futures import ThreadPoolExecutor

MODEL = "/kaggle/input/models/dfranzen/intel-qwen3.8-flash-next-w4a16-autoround"
DRAFTER = "/kaggle/input/models/dfranzen/albucino-qwen3-8-flash-next-drafter"
GCSFUSE = "/kaggle/input/datasets/dfranzen/pennyroyal-v253"
DEST = "/tmp/weights"            # overlay root, ~1.1 TB free; /kaggle/working is only 20 GB
OUT = "/kaggle/working/read_bench_v4.json"
PROBE_S = 45                     # duration of each short probe
LEVELS = [4, 8, 16]              # parallel stream counts to probe
COPY_BUDGET_S = 40 * 60          # cap for the full copy; extrapolated if hit
CHUNK = 16 << 20
GiB, MiB = 1 << 30, 1 << 20


def files_of(root):
    fs = [f for f in glob.glob(f"{root}/**/*", recursive=True) if os.path.isfile(f)]
    return sorted(fs, key=os.path.getsize, reverse=True)   # biggest first


def stream(path, deadline, counter, lock, offset=0, length=None):
    """Read path[offset:offset+length] until done or deadline; add bytes to counter."""
    buf = bytearray(CHUNK)
    mv = memoryview(buf)
    fd = os.open(path, os.O_RDONLY)
    try:
        pos, end = offset, offset + (length if length is not None else os.path.getsize(path))
        while pos < end and time.time() < deadline:
            n = os.preadv(fd, [mv[:min(CHUNK, end - pos)]], pos)
            if n <= 0:
                break
            pos += n
            with lock:
                counter[0] += n
    finally:
        os.close(fd)


def probe(label, jobs):
    """jobs: list of (path, offset, length). Runs them in parallel for PROBE_S."""
    counter, lock = [0], threading.Lock()
    t = time.time()
    deadline = t + PROBE_S
    with ThreadPoolExecutor(len(jobs)) as ex:
        for p, o, l in jobs:
            ex.submit(stream, p, deadline, counter, lock, o, l)
    el = time.time() - t
    rate = counter[0] / MiB / el
    print(f"  {label:<34} streams={len(jobs):>2}  {counter[0]/GiB:6.2f} GiB in {el:4.0f}s  = {rate:6.0f} MiB/s", flush=True)
    return dict(label=label, streams=len(jobs), gib=round(counter[0] / GiB, 2), secs=round(el, 1), mib_s=round(rate, 1))


results = dict(utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), probes=[])
model_files = files_of(MODEL)
model_bytes = sum(os.path.getsize(f) for f in model_files)
print(f"model: {len(model_files)} files, {model_bytes/GiB:.2f} GiB", flush=True)
if not model_files:
    raise SystemExit(f"no files under {MODEL}")

# Every probe uses files no earlier probe touched, so nothing is served from page cache.
unused = list(model_files)
touched = set()


def take(n):
    got = unused[:n]
    del unused[:n]
    touched.update(got)
    return got


print("\n== probes (fresh files each, uncached)", flush=True)
results["probes"].append(probe("model, 1 file", [(f, 0, None) for f in take(1)]))
for n in LEVELS:
    if len(unused) < n:
        print(f"  skip {n} streams: only {len(unused)} untouched files left", flush=True)
        continue
    results["probes"].append(probe(f"model, {n} files", [(f, 0, None) for f in take(n)]))

# Ranged reads inside one file: does a single shard go faster with 8 readers?
if unused:
    f = take(1)[0]
    size = os.path.getsize(f)
    part = -(-size // 8)
    results["probes"].append(probe("model, 1 file x 8 ranges", [(f, i * part, min(part, size - i * part)) for i in range(8) if i * part < size]))

for label, root in [("drafter (nfs), 1 file", DRAFTER), ("pennyroyal (gcsfuse), 1 file", GCSFUSE)]:
    fs = files_of(root)
    if fs:
        results["probes"].append(probe(label, [(fs[0], 0, None)]))
    else:
        print(f"  skip {label}: no files", flush=True)

file_probes = [p for p in results["probes"] if p["label"].startswith("model, ") and "ranges" not in p["label"]]
best = max(file_probes, key=lambda p: p["mib_s"])
base = file_probes[0]["mib_s"] or 1e-6
results["scaling_vs_1_stream"] = {p["streams"]: round(p["mib_s"] / base, 2) for p in file_probes}
print(f"\nscaling vs 1 stream: {results['scaling_vs_1_stream']}  -> using {best['streams']} streams for the copy", flush=True)

# Full copy of the model to local disk with the best stream count. This is the real
# workaround candidate: vLLM would then load from DEST instead of the network mount.
print(f"\n== parallel copy {MODEL} -> {DEST} with {best['streams']} streams (budget {COPY_BUDGET_S//60} min)", flush=True)
os.makedirs(DEST, exist_ok=True)
free = shutil.disk_usage(DEST).free
print(f"  free on {DEST}: {free/GiB:.0f} GiB", flush=True)
copied, fresh, lock, errors = [0], [0], threading.Lock(), []
t0 = time.time()
deadline = t0 + COPY_BUDGET_S


def copy_one(src):
    try:
        _copy_one(src)
    except OSError as e:   # e.g. ENOSPC if the container disk is capped
        errors.append(f"{os.path.basename(src)}: {e}")


def _copy_one(src):
    if errors:
        return
    dst = os.path.join(DEST, os.path.relpath(src, MODEL))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    is_fresh = src not in touched
    buf = bytearray(CHUNK)
    with open(src, "rb", buffering=0) as fi, open(dst, "wb") as fo:
        while time.time() < deadline:
            n = fi.readinto(buf)
            if not n:
                break
            fo.write(memoryview(buf)[:n])
            with lock:
                copied[0] += n
                if is_fresh:
                    fresh[0] += n


stop = threading.Event()


def progress():
    nxt = 10 * GiB
    while not stop.wait(5):
        if copied[0] >= nxt:
            el = time.time() - t0
            print(f"  {copied[0]/GiB:6.1f}/{model_bytes/GiB:.1f} GiB  {copied[0]/MiB/el:6.0f} MiB/s  t={el:5.0f}s", flush=True)
            nxt += 10 * GiB


pt = threading.Thread(target=progress, daemon=True)
pt.start()
# Untouched files first so the measured rate is not flattered by page cache.
order = [f for f in model_files if f not in touched] + [f for f in model_files if f in touched]
with ThreadPoolExecutor(best["streams"]) as ex:
    list(ex.map(copy_one, order))
stop.set()
el = time.time() - t0
rate = copied[0] / MiB / el
done = copied[0] >= model_bytes
est_min = (model_bytes / MiB / rate / 60) if rate else float("inf")
results["copy"] = dict(streams=best["streams"], gib_copied=round(copied[0] / GiB, 2),
                       gib_total=round(model_bytes / GiB, 2), secs=round(el, 1), mib_s=round(rate, 1),
                       complete=done, est_full_copy_min=round(est_min, 1),
                       fresh_gib=round(fresh[0] / GiB, 2), errors=errors[:5])
print(f"DONE copy {results['copy']}", flush=True)

single = file_probes[0]["mib_s"]
results["single_stream_est_min"] = round(model_bytes / MiB / single / 60, 1) if single else None
verdict = ("PARALLEL HELPS" if best["mib_s"] >= 2 * single else "NO GAIN FROM PARALLEL")
results["verdict"] = verdict
shutil.rmtree(DEST, ignore_errors=True)
json.dump(results, open(OUT, "w"), indent=2)
print("\n" + "=" * 70)
print(f"VERDICT: {verdict}")
print(f"  1 stream: {single:.0f} MiB/s (~{results['single_stream_est_min']} min for the model)")
print(f"  best    : {best['mib_s']:.0f} MiB/s with {best['streams']} streams")
print(f"  copy    : {'complete' if done else 'budget hit'}, {rate:.0f} MiB/s, ~{est_min:.1f} min for the full {model_bytes/GiB:.1f} GiB")
print("=" * 70)
