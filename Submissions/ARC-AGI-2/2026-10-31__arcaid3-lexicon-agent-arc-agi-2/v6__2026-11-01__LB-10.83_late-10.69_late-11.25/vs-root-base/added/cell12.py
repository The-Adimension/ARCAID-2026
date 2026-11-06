%%writefile /kaggle/working/agent/submit_main.py
"""Everything the competition rerun does after the fallback submission is written:
install the vLLM wheelhouse, start the server, run the agent. It NEVER raises --
an exception in a rerun fails the submission even when submission.json exists --
so every stage is caught and logged, and the fallback stands if a stage fails.

    python submit_main.py '<json config>'
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
import urllib.request
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = Path("/kaggle/working")
SITE = WORK / "vllm-site-packages"
LOG = WORK / "vllm-server.log"


def precache(path, threads=4, chunk=32 << 20):
    """Read the model files once so the server's load hits the page cache (ARCAID3 / dfranzen
    ARC-AGI-3 notebooks: since Oct 20 reads from /kaggle/input are slow and a load took 35-65
    min). Runs in a background thread while the wheelhouse installs; never raises."""
    import threading
    from concurrent.futures import ThreadPoolExecutor

    def run():
        t, jobs = time.time(), []
        for root, _, files in os.walk(path):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    size = os.path.getsize(fp)
                except OSError:
                    continue
                jobs += [(fp, off) for off in range(0, max(size, 1), chunk)]

        def read(job):
            try:
                with open(job[0], "rb") as fh:
                    fh.seek(job[1])
                    fh.read(chunk)
            except Exception:
                pass
        with ThreadPoolExecutor(max_workers=threads) as ex:
            list(ex.map(read, jobs))
        print(f"precache: {len(jobs)} chunks of {path} read in {time.time() - t:.0f}s", flush=True)

    th = threading.Thread(target=run, daemon=True)
    th.start()
    return th


def one(pattern):
    hits = glob.glob(pattern, recursive=True)
    if not hits:
        raise FileNotFoundError(pattern)
    return Path(hits[0])


def install(cfg):
    wh = one("/kaggle/input/**/arc3-vllm-h100-wheelhouse-v3/**/requirements.lock").parent
    t = time.time()
    subprocess.run([sys.executable, "-m", "pip", "install", "--no-index", "--find-links", str(wh),
                    "--requirement", str(wh / "requirements.lock"), "--target", str(SITE),
                    "--upgrade", "--ignore-installed", "--only-binary", ":all:", "--no-compile",
                    "--disable-pip-version-check", "--no-warn-conflicts", "-q"], check=True)
    print(f"wheelhouse installed in {time.time() - t:.0f}s", flush=True)
    if cfg.get("overlay"):
        wheels = sorted(glob.glob(cfg["overlay"], recursive=True))
        if not wheels:
            raise FileNotFoundError(cfg["overlay"])
        for pat in ("transformers", "transformers-*.dist-info", "huggingface_hub",
                    "huggingface_hub-*.dist-info"):
            for p in SITE.glob(pat):
                shutil.rmtree(p) if p.is_dir() else p.unlink()
        subprocess.run([sys.executable, "-m", "pip", "install", "--no-index", "--no-deps",
                        "--target", str(SITE), "--upgrade", "--force-reinstall", "--no-compile",
                        "--disable-pip-version-check", "-q", *wheels], check=True)
        print("overlay installed:", [Path(w).name for w in wheels], flush=True)


def start_server(cfg, extra, wait_s=1500):
    model = one(cfg["model_glob"]).parent
    env = dict(os.environ, PYTHONPATH=str(SITE), USE_TF="0", TRANSFORMERS_NO_TF="1",
               TRANSFORMERS_NO_TORCHVISION="1", VLLM_NO_USAGE_STATS="1",
               LIBRARY_PATH="/usr/local/nvidia/lib64:" + os.environ.get("LIBRARY_PATH", ""))
    cmd = [sys.executable, "-m", "vllm.entrypoints.openai.api_server", "--model", str(model),
           "--served-model-name", "qwen", "--host", "127.0.0.1", "--port", "1234",
           "--tensor-parallel-size", "4", "--enable-auto-tool-choice", *cfg["parsers"],
           "--generation-config", "vllm", "--enable-prefix-caching",
           "--max-model-len", str(cfg.get("max_model_len", 65536)), "--gpu-memory-utilization", "0.90",
           "--max-num-seqs", str(cfg.get("max_num_seqs", 32)), *extra]
    print(" ".join(cmd), flush=True)
    t = time.time()
    # "w": a retry must not see the previous attempt's "EngineCore failed".
    proc = subprocess.Popen(cmd, env=env, stdout=open(LOG, "w"), stderr=subprocess.STDOUT,
                            start_new_session=True)
    # Startup guard (ARCAID3 ARC-AGI-3 SG cell): a slow load is waited out, not mistaken for a
    # failed option set. Only a dead process or "EngineCore failed" moves on early.
    while time.time() - t < wait_s:
        text = LOG.read_text(errors="replace") if LOG.exists() else ""
        if proc.poll() is not None or "EngineCore failed" in text:
            break
        try:
            urllib.request.urlopen("http://127.0.0.1:1234/v1/models", timeout=5)
            print(f"server ready after {time.time() - t:.0f}s", flush=True)
            return proc
        except Exception:
            time.sleep(10)
    print("server FAILED to start; tail:\n" + "\n".join(
        LOG.read_text(errors="replace").splitlines()[-30:]), flush=True)
    kill(proc)
    return None


def kill(proc):
    """Kill the server's whole process group -- engine workers hold GPU memory -- and wait
    for the GPUs to drain, so a restart does not hit out-of-memory."""
    import signal
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except Exception:
        proc.kill()
    try:
        proc.wait(timeout=60)
    except Exception:
        pass
    for _ in range(36):
        used = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                              capture_output=True, text=True).stdout.split()
        if used and all(int(u) < 1500 for u in used if u.strip().isdigit()):
            return
        time.sleep(5)


def server_ladder(cfg):
    """Option sets to try in order. An explicit cfg["server_ladder"] wins (plain serving is
    appended if missing); otherwise server_extra + server_try -> server_extra -> plain."""
    if cfg.get("server_ladder"):
        ladder = [list(x) for x in cfg["server_ladder"]]
        return ladder if [] in ladder else ladder + [[]]
    base = cfg.get("server_extra", [])
    ladder = [base + cfg["server_try"]] if cfg.get("server_try") else []
    return ladder + [base] + ([[]] if base else [])


def main(cfg):
    proc = None
    try:
        t0 = time.time()
        try:
            precache(str(one(cfg["model_glob"]).parent), threads=cfg.get("precache_threads", 4))
        except Exception as e:
            print("precache skipped:", repr(e), flush=True)
        install(cfg)
        # A ladder of server option sets, most ambitious first; the last is plain serving.
        # Untested-on-L4 options (MTP, --reasoning-config) must never cost the whole run.
        ladder = server_ladder(cfg)
        hold_max = cfg.get("server_hold_max_s", 7200)      # SG_HOLD_MAX_S: give up after 2 h
        for i, extra in enumerate(ladder):
            left = hold_max - (time.time() - t0)
            if left < 300:
                print(f"startup guard: {hold_max}s spent starting the server -> fallback stands", flush=True)
                break
            # the first load pays for the cold reads; later option sets reuse the page cache
            wait = cfg.get("first_server_wait_s", 3600) if i == 0 else cfg.get("server_wait_s", 1500)
            proc = start_server(cfg, extra, wait_s=min(wait, left))
            if proc is not None:
                print(f"server up with option set {i}: {extra}", flush=True)
                break
            print(f"option set {i} failed -> next", flush=True)
            time.sleep(20)
        if proc is None:
            return
        sys.path.insert(0, HERE)
        import run_submit
        run_submit.main(dict(cfg, base_url="http://127.0.0.1:1234/v1", model="qwen"))
    except BaseException:
        print("submit_main caught:\n" + traceback.format_exc(), flush=True)
    finally:
        if proc is not None:
            kill(proc)
        shutil.rmtree(SITE, ignore_errors=True)


if __name__ == "__main__":
    try:
        main(json.loads(sys.argv[1]))
    except BaseException:
        print(traceback.format_exc(), flush=True)
    sys.exit(0)
