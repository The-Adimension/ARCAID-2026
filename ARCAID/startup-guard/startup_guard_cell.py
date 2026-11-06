# ---------------------------------------------------------------------------------------------
# Startup guard (SG): survive a slow model load without the scorecard idling out.
# Paste-in cell for Daniel Franzen's Milestone 2 notebook (or any notebook carrying his harness
# patch). Place it AFTER "6. Load the benchmark" and BEFORE "9. Run the benchmark". Standard
# library only. Kill switch: set env SG=0 before this cell runs.
#
# The failure it fixes (Kaggle discussion 751598, Oct 20-25 2026): dataset/model reads became
# slow, so the SGLang load now takes 35-65 min instead of ~10. The stock notebook releases the
# benchmark at 12 min (SERVER_STARTUP_TIMEOUT), one game sends a single warmup RESET, and every
# game's first analyzer request then waits out a 900 s grace (ARC3_HTTP_RETRY_INITIAL_SECONDS).
# At ~27 min the grace ends, each game fails ARC3_MAX_ANALYZER_FAILURES times and gives up, and
# the gateway closes the scorecard after 15 min with no action. Result: COMPLETE, 0.00, ~30 min,
# the 3,411-byte submission.parquet. Same code scored 21-32 on healthy days.
#
# What this cell changes, and nothing else:
#   1. Hold. Each game, before its first analyzer call, waits until the model server's /health
#      returns 200 (one shared monitor thread polls it). The analyzer is never called against a
#      cold server, so the 900 s grace and the give-up counter are not spent on the load.
#   2. Keep-alive. While games are held, one held game sends a RESET straight to the engine
#      (the same call the stock warmup uses) right away and then every SG_KEEPALIVE_S seconds
#      (default 420 = 7 min, under the 15-min idle close). The game with the fewest keep-alive
#      RESETs so far is picked, so the extra actions are spread one per game. The stock warmup
#      RESET is turned off because the first keep-alive replaces it.
#   3. Limits. The hold ends when the server is healthy, when the server process has exited
#      (fail fast, as before), or SG_HOLD_MAX_S after notebook start (default 7200 = 2 h), so a
#      server that never comes up still ends the run instead of burning the 9 h.
# The per-game clock (started_at) is not touched, so holding never pushes a game past its stock
# deadline. Any error inside the wrapper falls back to the stock behaviour and is counted.
# ---------------------------------------------------------------------------------------------
import os as _sg_os
import threading as _sg_threading
import time as _sg_time
import urllib.request as _sg_urlreq

SG_ON = _sg_os.environ.get("SG", "1").strip() not in ("0", "", "false", "False")
SG_KEEPALIVE_S = float(_sg_os.environ.get("SG_KEEPALIVE_S", "420"))
SG_HOLD_MAX_S = float(_sg_os.environ.get("SG_HOLD_MAX_S", "7200"))
SG_POLL_S = float(_sg_os.environ.get("SG_POLL_S", "5"))
SG_HEALTH_URL = _sg_os.environ.get(
    "SG_HEALTH_URL", f"http://127.0.0.1:{globals().get('SERVED_MODEL_PORT', 8001)}/health")
SG_T0 = float(globals().get("NOTEBOOK_START_TIME") or _sg_time.time())

SG_STATS = {
    "held_games": 0, "keepalive_resets": 0, "released_by": None, "ready_after_s": None,
    "max_hold_s": 0.0, "errors": 0,
}


class _SgGuard:
    """Shared state: one monitor thread decides when holding ends; held games take turns
    sending the keep-alive RESET from their own threads (the engine is only ever touched by
    the game's own thread, exactly as with the stock warmup)."""

    def __init__(self, health_url, proc_getter, t0, hold_max_s, keepalive_s, poll_s, stats, quiet=False):
        self.health_url, self.proc_getter = health_url, proc_getter
        self.t0, self.hold_max_s, self.keepalive_s, self.poll_s = t0, hold_max_s, keepalive_s, poll_s
        self.stats, self.quiet = stats, quiet
        self.released = _sg_threading.Event()
        self.lock = _sg_threading.Lock()
        self.next_keepalive = 0.0            # first held game sends one at once
        self.resets_by_game = {}             # id(session) -> keep-alive RESETs sent
        self.waiting = set()
        self._monitor = None

    def _healthy(self):
        try:
            with _sg_urlreq.urlopen(self.health_url, timeout=5) as r:
                return r.status == 200
        except Exception:
            return False

    def _release(self, why):
        with self.lock:
            if self.stats["released_by"] is None:
                self.stats["released_by"] = why
                self.stats["ready_after_s"] = round(_sg_time.time() - self.t0, 1)
        self.released.set()
        if not self.quiet:
                print(f"ARC3_SG_RELEASE by={why} t={self.stats['ready_after_s']}s "
                  f"keepalive_resets={self.stats['keepalive_resets']}", flush=True)

    def _monitor_loop(self):
        last_note = 0.0
        while not self.released.is_set():
            if self._healthy():
                return self._release("health")
            proc = self.proc_getter()
            if proc is not None and proc.poll() is not None:
                return self._release(f"server_exited_rc={proc.returncode}")
            if _sg_time.time() - self.t0 >= self.hold_max_s:
                return self._release("hold_max")
            if not self.quiet and _sg_time.time() - last_note >= 300:
                last_note = _sg_time.time()
                print(f"  ARC3_SG waiting for {self.health_url}: t={int(last_note - self.t0)}s, "
                      f"held={len(self.waiting)}, keepalive_resets={self.stats['keepalive_resets']}",
                      flush=True)
            self.released.wait(self.poll_s)

    def start(self):
        if self._monitor is None:
            self._monitor = _sg_threading.Thread(target=self._monitor_loop, name="sg-monitor", daemon=True)
            self._monitor.start()

    def _claim_keepalive(self, key):
        """True if this held game should send the keep-alive RESET now: it is due, and no
        other held game has sent fewer of them."""
        with self.lock:
            now = _sg_time.monotonic()
            if self.released.is_set() or now < self.next_keepalive:
                return False
            mine = self.resets_by_game.get(key, 0)
            if any(self.resets_by_game.get(k, 0) < mine for k in self.waiting):
                return False
            self.next_keepalive = now + self.keepalive_s
            self.resets_by_game[key] = mine + 1
            self.stats["keepalive_resets"] += 1
            return True

    def hold(self, session, send_reset):
        """Block this game until the server is up, sending keep-alive RESETs when it is its turn."""
        if self.released.is_set():
            return
        key = id(session)
        start = _sg_time.monotonic()
        with self.lock:
            self.waiting.add(key)
            self.resets_by_game.setdefault(key, 0)
            self.stats["held_games"] += 1
        try:
            while not self.released.is_set():
                if self._claim_keepalive(key):
                    try:
                        send_reset()
                    except Exception as exc:   # a failed RESET must not kill the game
                        self.stats["errors"] += 1
                        print(f"ARC3_SG keep-alive RESET failed: {exc!r}", flush=True)
                self.released.wait(1.0)
        finally:
            with self.lock:
                self.waiting.discard(key)
                self.stats["max_hold_s"] = max(self.stats["max_hold_s"],
                                               round(_sg_time.monotonic() - start, 1))


def _sg_install(guard):
    import inference.framework.solver as _sv
    cls = _sv._HarnessGameSession
    if getattr(cls, "_sg_installed", False):
        cls._sg_guard = guard              # re-run of the cell: point at the new guard
        return "already_installed"
    # The first keep-alive replaces the stock warmup RESET (read from this global in _setup).
    _sv.WARMUP_ACTION_GAMES = 0
    _orig_play_inner = cls._play_inner

    def _play_inner(self, *args, **kwargs):
        try:
            g = type(self)._sg_guard
            if not g.released.is_set():
                run = self.game.game_run
                gid = getattr(run, "game_id", "?")

                def _reset():
                    _sv.log.warning("%s: keep-alive RESET while the model server loads", gid)
                    self._execute_auto_reset()

                g.hold(self, _reset)
        except Exception as exc:
            SG_STATS["errors"] += 1
            print(f"ARC3_SG hold failed, continuing stock: {exc!r}", flush=True)
        return _orig_play_inner(self, *args, **kwargs)

    cls._play_inner = _play_inner
    cls._sg_guard = guard
    cls._sg_installed = True
    return "installed"


def _sg_selftest():
    """Offline: a fake server that turns healthy after a while, three fake games."""
    import http.server, socketserver
    ready_at = _sg_time.time() + 2.5

    class _H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200 if _sg_time.time() >= ready_at else 503); self.end_headers()
        def log_message(self, *a):
            pass

    srv = socketserver.TCPServer(("127.0.0.1", 0), _H)
    _sg_threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        st = {"held_games": 0, "keepalive_resets": 0, "released_by": None, "ready_after_s": None,
              "max_hold_s": 0.0, "errors": 0}
        g = _SgGuard(f"http://127.0.0.1:{srv.server_address[1]}/health", lambda: None,
                     _sg_time.time(), 60, 1.0, 0.2, st, quiet=True)
        g.start()
        sent = []
        ts = [_sg_threading.Thread(target=g.hold, args=(object(), lambda i=i: sent.append(i)))
              for i in range(3)]
        for t in ts: t.start()
        for t in ts: t.join(10)
        assert st["released_by"] == "health", st
        assert 2 <= len(sent) <= 4, sent                     # ~one per second while held
        assert len(set(sent[:3])) == min(3, len(sent)), sent  # spread across games
        g2 = _SgGuard("http://127.0.0.1:9/health", lambda: None, _sg_time.time() - 100, 50, 1, 0.2,
                      dict(st, released_by=None), quiet=True)
        g2.start(); g2.released.wait(5)
        assert g2.stats["released_by"] == "hold_max", g2.stats
        return "ok"
    finally:
        srv.shutdown(); srv.server_close()


if SG_ON:
    _sg_test = _sg_selftest()
    _sg_guard = _SgGuard(SG_HEALTH_URL, lambda: globals().get("proc"), SG_T0, SG_HOLD_MAX_S,
                         SG_KEEPALIVE_S, SG_POLL_S, SG_STATS)
    _sg_state = _sg_install(_sg_guard)
    _sg_guard.start()
    print(f"ARC3_SG_READY {_sg_state} keepalive={SG_KEEPALIVE_S:.0f}s hold_max={SG_HOLD_MAX_S:.0f}s "
          f"url={SG_HEALTH_URL} self_test={_sg_test}", flush=True)
else:
    print("ARC3_SG_READY disabled", flush=True)
