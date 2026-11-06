"""End-to-end check of restart.patch: drive the real ToolAgent.analyze() with a fake model, offline.

  python kaggle/restart-dfranzen/sim_restart.py <unpatched bundle dir> <notebook.ipynb>

<unpatched bundle dir> is dfranzen/taaf-kaggle-source-bundle-copy as downloaded. Both patches are taken from the
notebook's %%writefile cells and applied as its setup cell applies them, giving two trees: Franzen only, and
Franzen + restart. Each scenario runs in a fresh interpreter on one tree (fake chat completion and fake action
dispatch; everything else is the harness's own code). Adapted from the 2026-10-13 review's simulation.

  flag0   flag 0 on both trees: no-action turns, action turns, a request failure. The requests sent must be
          byte-identical between the trees, and no restart log is written.
  stuck   flag 100000 on the restart tree: the model deliberates without acting from 90K level tokens. The
          restart must fire inside that no-action chain; the next request is [system, user] with the note first
          and no resume tag; the level's token count (priority) is unchanged.
  retry   the restart turn fails at the HTTP layer: the retry's opener carries the note again; the turn after
          a kept turn does not.
  gameover_resume  the last executed step ended in a game over, then the model deliberates past 100K without acting:
          the restart opener carries that step's full outcome (BAR RULE diagnosis, no reference to deleted
          messages) and as many images as a fresh game-over opener.
  multicall_levelup  after a restart, a two-call reply whose first call completes the level is discarded by the
          harness: the next level's opener must not carry the old level's note.
The environment is the notebook's own setup_env (prompt, vision, guard and context flags), with the priority gate
off and the model endpoint stubbed.
Needs Python 3.12 with the bundle's imports (requests).
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
OK = []

DRIVER = r'''
import json, os, sys, tempfile, pathlib
SP = pathlib.Path(tempfile.mkdtemp())
scenario, flag = sys.argv[1], sys.argv[2]
os.environ.update(json.loads(os.environ.get('NOTEBOOK_ENV', '{}')))
os.environ.update({
    'LOCAL_ANALYZER_TOOL_STEPS': '0', 'LOCAL_ANALYZER_YIELD_SECONDS': '0', 'LOCAL_ANALYZER_YIELD_TOKENS': '2048',
    'LOCAL_ANALYZER_CONTEXT_WINDOW': str((116+12)*1024), 'LOCAL_ANALYZER_MAX_OUTPUT': str(12*1024),
    'ARC3_CONTEXT_DRAIN_TOKENS': str(58*1024), 'ARC3_HISTORY_ASSISTANT_TURNS': '150', 'ARC3_HISTORY_TURN_DRAIN': '30',
    'ARC3_HISTORY_DRAIN_COALESCE': '1', 'ARC3_MEMORY_SECTIONS': 'off', 'ARC3_PERSISTENT_FUNCTIONS': '1',
    'ARC3_PERSISTENT_FUNCTIONS_SCOPE': 'game', 'ARC3_REASONING_HISTORY_KEY': 'reasoning_content',
    'LOCAL_ANALYZER_ENABLE_THINKING': 'true', 'ARC3_STUCK_RESTART_TOKENS': flag,
    'ARC3_STUCK_RESTART_LOG': str(SP / 'r.jsonl'), 'ARC3_MAX_ACTIVE_STREAMS': '0',
    'LOCAL_ANALYZER_BASE_URL': 'http://127.0.0.1:9/v1', 'LOCAL_ANALYZER_PROVIDER': 'vllm', 'LOCAL_ANALYZER_MODEL_ID': 'x',
})
import requests
import inference.agent.tool_agent as T
from inference.agent.runtime_state import Frame, HistoryEntry, write_runtime_state
state = SP / 'ab12-cdef0123_p0_tool_runtime_state.json'
grid = tuple(tuple((r * 7 + c) % 5 for c in range(16)) for r in range(16))
write_runtime_state(state, current_frame=Frame(grid=grid, step=5, level=2),
                    history=[HistoryEntry(action='ACTION1', frame=Frame(grid=grid, step=5, level=2), result={})])
sent = []
mode = {'kind': 'text', 'fail': False}
def fake_chat(self, messages, **kw):
    sent.append(json.loads(json.dumps(messages, default=str)))
    if mode['fail']:
        raise requests.ConnectionError('boom')
    if mode['kind'] == 'text':
        return T._ChatCompletionResult(message={'role': 'assistant', 'content': 'thinking...', 'reasoning_content': 'r'},
                                       finish_reason='stop', usage={'prompt_tokens': 1000, 'completion_tokens': 3000, 'total_tokens': 4000})
    return T._ChatCompletionResult(message={'role': 'assistant', 'content': '', 'tool_calls': [
        {'id': 'c1', 'type': 'function', 'function': {'name': 'python', 'arguments': json.dumps({'code': 'action(["ACTION1"])'})}}]},
        finish_reason='tool_calls', usage={'prompt_tokens': 1000, 'completion_tokens': 500, 'total_tokens': 1500})
T.ToolAgent._chat_completion = fake_chat
def fake_dispatch(self, state_path, name, arguments):
    prev = self._last_step_summary or {}
    self._last_step_summary = {'level': 2, 'end_action_num': prev.get('end_action_num', 10) + 1,
                               'executed_count': 1, 'executed_actions': ['ACTION1'], 'level_transition': False}
    return T._ToolDispatchResult('{"result": "ok"}', step_executed=True, made_progress=True)
T.ToolAgent._dispatch_tool = fake_dispatch
def new_agent(tokens):
    a = T.ToolAgent(model='x', base_url='http://127.0.0.1:9/v1', provider='vllm')
    a._ensure_session(state)
    a._last_step_summary = {'level': 2, 'end_action_num': 10}
    a._actions_at_level_start = 5
    a._history_messages = [{'role': 'user', 'content': 'old opener'}, {'role': 'assistant', 'content': 'old'}]
    a._tokens_at_level_start = 0
    a._session_generated_tokens = tokens
    return a
def opener(req):
    m = req[1]['content']
    return m if isinstance(m, str) else ''.join(p.get('text', '') for p in m if isinstance(p, dict))
out = {}
if scenario == 'flag0':
    a = new_agent(90_000)
    for i in range(12):
        a.analyze(state, 10, valid_actions=['ACTION1'], step_env=None)
    mode['kind'] = 'tool'
    for i in range(3):
        a.analyze(state, 10 + i, valid_actions=['ACTION1'], step_env=None)
    mode['fail'] = True
    a.analyze(state, 13, valid_actions=['ACTION1'], step_env=None)
    mode['fail'] = False
    a.analyze(state, 13, valid_actions=['ACTION1'], step_env=None)
    out = {'sent': sent, 'log_exists': (SP / 'r.jsonl').exists(), 'tokens_at_level_start': a._tokens_at_level_start}
elif scenario == 'stuck':
    a = new_agent(90_000)
    fired_at = None
    for i in range(12):
        n = len(sent)
        a.analyze(state, 10, valid_actions=['ACTION1'], step_env=None)
        if fired_at is None and getattr(a, '_stuck_restarts', {}):
            fired_at = i
            first = sent[n]
    out = {'fired_at_invocation': fired_at, 'resume_flag_after_chain': a._resume_after_yield,
           'first_roles': [m['role'] for m in first] if fired_at is not None else None,
           'first_opener_starts_with_note': opener(first).startswith('Your earlier conversation on this level was cleared') if fired_at is not None else None,
           'first_has_resume_tag': any(m.get('_arc3_control') or m.get('arc3_control') for m in first) if fired_at is not None else None,
           'tokens_at_level_start': a._tokens_at_level_start,
           'events': [json.loads(l) for l in open(SP / 'r.jsonl')] if (SP / 'r.jsonl').exists() else []}
elif scenario == 'gameover_resume':
    def text_chat(self, messages, **kw):
        sent.append(json.loads(json.dumps(messages, default=str)))
        return T._ChatCompletionResult(message={'role': 'assistant', 'content': 'thinking...', 'reasoning_content': 'r'},
                                       finish_reason='stop', usage={'prompt_tokens': 1000, 'completion_tokens': 3000, 'total_tokens': 4000})
    T.ToolAgent._chat_completion = text_chat
    g1 = grid
    g2 = tuple(tuple((r * 3 + c) % 5 for c in range(16)) for r in range(16))
    write_runtime_state(state, current_frame=Frame(grid=g1, step=7, level=2),
                        history=[HistoryEntry(action='ACTION1', frame=Frame(grid=g1, step=5, level=2), result={}),
                                 HistoryEntry(action='ACTION3', frame=Frame(grid=g2, step=6, level=2), result={}),
                                 HistoryEntry(action='RESET', frame=Frame(grid=g1, step=7, level=2), result={})])
    a = new_agent(98_000)
    a._last_step_summary = {'level': 2, 'end_action_num': 6, 'executed_count': 1, 'executed_actions': ['ACTION3'],
                            'level_transition': False, 'game_over': True, 'fatal_action': 'ACTION3',
                            'game_over_trace': ['ACTION3 -> GAME OVER'], 'gameplay_changed': True, 'board_changed': True}
    a._actions_at_level_start = 1
    def last_user(req):
        m = [x for x in req if x['role'] == 'user'][-1]['content']
        return m
    def text_of(m):
        return m if isinstance(m, str) else ''.join(p.get('text', '') for p in m if isinstance(p, dict))
    def images(m):
        return 0 if isinstance(m, str) else sum(1 for p in m if isinstance(p, dict) and p.get('type') == 'image_url')
    invs = []
    for i in range(3):
        n = len(sent)
        had = bool(getattr(a, '_stuck_restarts', {}))
        a.analyze(state, 7, valid_actions=['ACTION1', 'ACTION3'], step_env=None)
        req = sent[n]
        m = last_user(req)
        invs.append({'restart_now': (not had) and bool(getattr(a, '_stuck_restarts', {})), 'roles': [x['role'] for x in req],
                     'images': images(m), 'bar_rule': 'BAR RULE' in text_of(m),
                     'earlier_msg_claim': 'given in an earlier message' in text_of(m),
                     'note': text_of(m).startswith('Your earlier conversation on this level was cleared')})
    out = {'invocations': invs,
           'events': [json.loads(l) for l in open(SP / 'r.jsonl')] if (SP / 'r.jsonl').exists() else []}
elif scenario == 'multicall_levelup':
    two = {'n': 0}
    def chat(self, messages, **kw):
        sent.append(json.loads(json.dumps(messages, default=str)))
        if mode['kind'] == 'two':
            calls = [{'id': f'c{k}', 'type': 'function', 'function': {'name': 'python', 'arguments': json.dumps({'code': 'action(["ACTION1"])'})}} for k in (1, 2)]
            return T._ChatCompletionResult(message={'role': 'assistant', 'content': '', 'tool_calls': calls},
                                           finish_reason='tool_calls', usage={'prompt_tokens': 1000, 'completion_tokens': 500, 'total_tokens': 1500})
        return T._ChatCompletionResult(message={'role': 'assistant', 'content': 'thinking...', 'reasoning_content': 'r'},
                                       finish_reason='stop', usage={'prompt_tokens': 1000, 'completion_tokens': 3000, 'total_tokens': 4000})
    T.ToolAgent._chat_completion = chat
    def levelup_dispatch(self, state_path, name, arguments):
        self._last_step_summary = {'level': 3, 'end_action_num': 60, 'executed_count': 1, 'executed_actions': ['ACTION1'],
                                   'level_transition': True, 'level_completed': True}
        return T._ToolDispatchResult('{"result": "ok"}', step_executed=True, made_progress=True)
    T.ToolAgent._dispatch_tool = levelup_dispatch
    c = new_agent(120_000)
    mode['kind'] = 'two'
    n = len(sent)
    c.analyze(state, 40, valid_actions=['ACTION1'], step_env=None)
    restart_req = sent[n]
    history_after = len(c._history_messages)
    mode['kind'] = 'text'
    n2 = len(sent)
    c.analyze(state, 60, valid_actions=['ACTION1'], step_env=None)
    nxt = sent[n2]
    out = {'restart_turn_has_note': 'was cleared after' in json.dumps(restart_req),
           'history_after_discard': history_after, 'next_has_note': 'was cleared after' in json.dumps(nxt)}
elif scenario == 'retry':
    c = new_agent(120_000)
    mode['fail'] = True
    rc = c.analyze(state, 40, valid_actions=['ACTION1'], step_env=None)
    mode['fail'] = False
    mode['kind'] = 'tool'
    n = len(sent)
    c.analyze(state, 40, valid_actions=['ACTION1'], step_env=None)
    retry = sent[n]
    n2 = len(sent)
    c.analyze(state, 41, valid_actions=['ACTION1'], step_env=None)
    after = sent[n2]
    out = {'retryable': getattr(rc, 'retryable_failure', None),
           'retry_roles': [m['role'] for m in retry], 'retry_has_note': 'was cleared after' in opener(retry),
           'after_has_note_in_last_user': 'was cleared after' in json.dumps(after[-1]),
           'after_roles_start': [m['role'] for m in after][:2],
           'restarts': len([l for l in open(SP / 'r.jsonl')])}
print('RESULT ' + json.dumps(out))
'''


def check(name, cond, detail=""):
    OK.append(bool(cond))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f": {detail}" if detail and not cond else ""))


def cell_body(src):
    src = src if src.endswith("\n") else src + "\n"       # IPython adds a final newline to a cell without one
    return src.split("\n", 1)[1]


def build_trees(bundle, nb_path):
    cells = ["".join(c["source"]) for c in json.loads(pathlib.Path(nb_path).read_text())["cells"]]
    franzen = cell_body(next(c for c in cells if c.startswith("%%writefile /kaggle/harness-changes.patch")))
    restart = cell_body(next(c for c in cells if c.startswith("%%writefile /kaggle/restart.patch")))
    root = pathlib.Path(tempfile.mkdtemp())
    (root / "harness-changes.patch").write_text(franzen)
    (root / "restart.patch").write_text(restart)
    trees = {}
    for name, patches in (("franzen_only", ["harness-changes.patch"]), ("franzen_plus_restart", ["harness-changes.patch", "restart.patch"])):
        d = root / name / "src"
        if bundle.suffix == ".zip":
            zipfile.ZipFile(bundle).extractall(root / name)
        else:
            shutil.copytree(bundle / "src", d)
        for p in patches:
            subprocess.run(["git", "apply", "--include=ARC3-Inference/*", str(root / p)], cwd=d, check=True)
        trees[name] = d / "ARC3-Inference"
    (root / "driver.py").write_text(DRIVER)
    return root, trees


def notebook_env(nb_path):
    """setup_env exactly as the notebook's setup cell builds it (priority flags included, gate turned off here)."""
    cells = ["".join(c["source"]) for c in json.loads(pathlib.Path(nb_path).read_text())["cells"]]
    c4 = next(c for c in cells if "USE_PRIORITY_SCHEDULING = True" in c and "setup_env = {" in c)
    block = c4[c4.index("USE_PRIORITY_SCHEDULING = True"):c4.index("os.environ.update({k: str(v) for k,v in setup_env.items()})")]
    g = {"SERVER_BASE_URL": "http://127.0.0.1:9/v1", "SERVED_MODEL_NAME": "x"}
    exec(block, g)
    env = {k: str(v) for k, v in g["setup_env"].items()}
    env["ARC3_MAX_ACTIVE_STREAMS"] = "0"
    return env


NB_ENV = {}


def run(root, tree, scenario, flag):
    env = dict(os.environ, PYTHONPATH=str(tree), NOTEBOOK_ENV=json.dumps(NB_ENV))
    p = subprocess.run([sys.executable, str(root / "driver.py"), scenario, flag], env=env, capture_output=True, text=True)
    line = [l for l in p.stdout.splitlines() if l.startswith("RESULT ")]
    if not line:
        raise RuntimeError(f"{scenario} on {tree} failed:\n{p.stderr[-2000:]}")
    return json.loads(line[-1][7:])


def main():
    root, trees = build_trees(pathlib.Path(sys.argv[1]).resolve(), sys.argv[2])
    NB_ENV.update(notebook_env(sys.argv[2]))
    a = run(root, trees["franzen_only"], "flag0", "0")
    b = run(root, trees["franzen_plus_restart"], "flag0", "0")
    check("flag 0: requests byte-identical to Franzen only", a["sent"] == b["sent"] and len(a["sent"]) > 10,
          f"{len(a['sent'])} vs {len(b['sent'])} requests")
    check("flag 0: no restart log, no re-pricing", not b["log_exists"] and a["tokens_at_level_start"] == b["tokens_at_level_start"])

    s = run(root, trees["franzen_plus_restart"], "stuck", "100000")
    check("restart fires inside a no-action chain", s["fired_at_invocation"] is not None, json.dumps(s)[:400])
    check("restart opens a fresh turn: [system, user], note first, no resume tag",
          s["first_roles"] == ["system", "user"] and s["first_opener_starts_with_note"] and not s["first_has_resume_tag"], json.dumps(s)[:400])
    check("event marks the resumed turn", s["events"] and s["events"][0].get("resumed_turn") is True, json.dumps(s["events"])[:300])
    check("no re-pricing in the real turn loop", s["tokens_at_level_start"] == 0)

    r = run(root, trees["franzen_plus_restart"], "retry", "100000")
    check("failed restart turn is retryable and its retry carries the note", r["retryable"] and r["retry_has_note"]
          and r["retry_roles"][:2] == ["system", "user"], json.dumps(r))
    check("the turn after a kept turn does not repeat the note", not r["after_has_note_in_last_user"], json.dumps(r))
    check("one restart event despite the retry", r["restarts"] == 1, json.dumps(r))

    g = run(root, trees["franzen_plus_restart"], "gameover_resume", "100000")
    inv = g["invocations"]
    fired = [i for i, x in enumerate(inv) if x["restart_now"]]
    check("game over then deliberation: restart fires on a resumed invocation", fired and fired[0] > 0
          and g["events"] and g["events"][0].get("resumed_turn") is True, json.dumps(g)[:500])
    if fired:
        x = inv[fired[0]]
        check("restart opener after a game over: note, BAR RULE diagnosis, no reference to deleted messages",
              x["note"] and x["bar_rule"] and not x["earlier_msg_claim"] and x["roles"] == ["system", "user"], json.dumps(x))
        check("restart opener after a game over: as many images as the fresh game-over opener",
              x["images"] >= inv[0]["images"] and inv[0]["images"] > 1, json.dumps([y["images"] for y in inv]))
    m = run(root, trees["franzen_plus_restart"], "multicall_levelup", "100000")
    check("discarded two-call turn that completes the level: the next level's opener has no stale note",
          m["restart_turn_has_note"] and m["history_after_discard"] == 0 and not m["next_has_note"], json.dumps(m))
    print(f"{sum(OK)} of {len(OK)} pass")
    sys.exit(0 if all(OK) else 1)


if __name__ == "__main__":
    main()
