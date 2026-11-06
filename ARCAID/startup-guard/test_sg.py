"""Offline test of startup_guard_cell.py against the real patched harness.

Usage: python test_sg.py <bundle src dir with harness-changes.patch applied> <path to startup_guard_cell.py>
"""
import sys, time, threading, http.server, socketserver, types, os
B = sys.argv[1]; CELL = sys.argv[2]
sys.path[:0] = [f'{B}/ARC3-Inference', f'{B}/tufa-arc-agi-framework/src']
import inference.framework.solver as sv
cls = sv._HarnessGameSession
calls = []
cls._play_inner = lambda self: calls.append((self.name, time.time()))   # stands in for the stock body

READY = time.time() + 6
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200 if time.time() >= READY else 503); self.end_headers()
    def log_message(self, *a): pass
srv = socketserver.ThreadingTCPServer(('127.0.0.1', 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()

os.environ.update(SG_KEEPALIVE_S='1.5', SG_POLL_S='0.3')
g = {'SERVED_MODEL_PORT': srv.server_address[1], 'NOTEBOOK_START_TIME': time.time(), 'proc': None}
exec(open(CELL).read(), g)
READY = time.time() + 6
assert sv.WARMUP_ACTION_GAMES == 0
resets = []
def mk(name):
    s = object.__new__(cls); s.name = name
    s.game = types.SimpleNamespace(game_run=types.SimpleNamespace(game_id=name))
    s._execute_auto_reset = lambda: resets.append((name, round(time.time() - g['NOTEBOOK_START_TIME'], 1)))
    return s
ts = [threading.Thread(target=lambda s=mk(f'g{i}'): s._play_inner()) for i in range(5)]
for t in ts: t.start()
for t in ts: t.join(30)
print('resets', resets); print('stats', g['SG_STATS'])
assert all(c[1] >= READY for c in calls) and len(calls) == 5, calls
assert 3 <= len(resets) <= 6 and len({r[0] for r in resets}) == len(resets), resets   # one per game
# after release, a new game is not held and sends nothing
s = mk('late'); n = len(resets); s._play_inner(); assert len(resets) == n and calls[-1][0] == 'late'
# re-running the cell is idempotent (wrapper not stacked)
exec(open(CELL).read(), g); assert g['_sg_state'] == 'already_installed'
# server exit releases immediately
class P:  returncode = 1
P.poll = lambda self: 1
g2 = dict(g, proc=P(), SG_STATS=None); g2['SERVED_MODEL_PORT'] = 9
exec(open(CELL).read(), g2); g2['_sg_guard'].released.wait(3)
assert g2['SG_STATS']['released_by'] == 'server_exited_rc=1', g2['SG_STATS']
print('ALL OK')
