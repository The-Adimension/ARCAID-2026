"""Check arc3_compact on v3's real prompts, end to end through requests -> urllib3.

Each of v3's six prompt snapshots is rebuilt as an OpenAI message list, POSTed with
`requests` to a local echo server, and the body the server received is compared with the
original: same messages and roles, same tool calls and tool results, same newest USER
message, carried world models kept. With the model's tokenizer and chat template (set
ARC3_TOKENIZER and ARC3_CHAT_TEMPLATE to local copies of `tokenizer.json` and
`chat_template.jinja` from RadixArk/Qwen3.8-Flash-Next-NVFP4) it also prints the rendered
prompt tokens before and after.

Run from the repo root: python3 presubmissions/v5/test_arc3_compact.py
"""
import glob
import http.server
import json
import os
import re
import sys
import threading
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import arc3_compact  # noqa: E402

SNAP = HERE.parents[1] / "submissions/2026-09-25__duck-nvfp4-batch-stall-warn-dead-sign__v3__score-3.59/outputs/prompts"
TOOLS = [{"type": "function", "function": {
    "name": "python", "description": "Run one ephemeral Python snippet.",
    "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}}]


def parse(path):
    """Rebuild the message list from a v3 'LATEST MODEL CALL SNAPSHOT' prompt log."""
    t = Path(path).read_text()
    body = t[t.index("[MODEL INPUT]") + len("[MODEL INPUT]"): t.index("[TURN TRANSCRIPT SO FAR]")]
    parts = re.split(r"\n(?=\[(?:SYSTEM|USER|ASSISTANT|REASONING|ASSISTANT TOOL CALL: python|TOOL RESULT: [^\]]+)\]\n)", body)
    msgs = []
    for p in parts:
        m = re.match(r"\s*\[([^\]]+)\](?:\n|$)", p)
        if not m:
            continue
        tag, text = m.group(1), p[m.end():].rstrip("\n")
        if tag == "SYSTEM":
            msgs.append({"role": "system", "content": text})
        elif tag == "USER":
            msgs.append({"role": "user", "content": [{"type": "text", "text": text}]})
        elif tag == "ASSISTANT":
            msgs.append({"role": "assistant", "content": text})
        elif tag == "REASONING":
            msgs[-1]["reasoning_content"] = text
        elif tag.startswith("ASSISTANT TOOL CALL"):
            code = re.search(r"<parameter=code>\n(.*?)\n</parameter>", text, re.S)
            msgs[-1].setdefault("tool_calls", []).append({"id": "x", "type": "function", "function": {
                "name": "python", "arguments": {"code": code.group(1) if code else text}}})
        elif tag.startswith("TOOL RESULT"):
            msgs.append({"role": "tool", "tool_call_id": "x", "content": text})
    return msgs


def token_counter():
    tok_path, tpl_path = os.environ.get("ARC3_TOKENIZER"), os.environ.get("ARC3_CHAT_TEMPLATE")
    if not (tok_path and tpl_path):
        return None
    import jinja2
    from tokenizers import Tokenizer
    tk = Tokenizer.from_file(tok_path)
    env = jinja2.Environment(trim_blocks=True, lstrip_blocks=True)
    env.globals["raise_exception"] = lambda m: (_ for _ in ()).throw(RuntimeError(m))
    tpl = env.from_string(Path(tpl_path).read_text())
    return lambda messages: len(tk.encode(tpl.render(messages=messages, tools=TOOLS, add_generation_prompt=True)).ids)


def main():
    received = []

    class Echo(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            received.append(self.rfile.read(int(self.headers["Content-Length"])))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')

        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Echo)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = "http://127.0.0.1:%d/v1/chat/completions" % srv.server_address[1]

    assert arc3_compact.install() and arc3_compact.install()   # idempotent
    ntok = token_counter()
    snaps = sorted(glob.glob(str(SNAP / "*.log")))
    assert len(snaps) == 6, snaps
    tot_b = tot_a = 0
    for path in snaps:
        msgs = parse(path)
        r = requests.post(url, json={"model": "m", "messages": msgs, "tools": TOOLS}, timeout=10)
        assert r.status_code == 200
        sent = json.loads(received[-1])["messages"]

        assert [m["role"] for m in sent] == [m["role"] for m in msgs]
        last_user = max(i for i, m in enumerate(msgs) if m["role"] == "user")
        assert sent[last_user] == msgs[last_user]
        for a, b in zip(sent, msgs):
            assert a.get("tool_calls") == b.get("tool_calls")
            if a["role"] in ("tool", "system"):
                assert a == b
            if a["role"] == "assistant":
                assert a.get("content") == b.get("content")
            if a["role"] == "user":
                wm = re.search(r"Working world model carried from earlier turns:.*?end of world model", b["content"][0]["text"], re.S)
                assert not wm or wm.group(0) in a["content"][0]["text"]
        kept = [i for i, m in enumerate(sent) if m.get("reasoning_content")]
        assistants = [i for i, m in enumerate(msgs) if m["role"] == "assistant" and m.get("reasoning_content")]
        assert kept == assistants[-2:] or all(i > last_user for i in kept[:-2]), (kept, assistants)

        line = "%-10s msgs=%2d reasoning kept on %d of %d assistant msgs" % (
            Path(path).name[:9], len(msgs), len(kept), len(assistants))
        if ntok:
            before, after = ntok(msgs), ntok(sent)
            tot_b += before
            tot_a += after
            line += "  tokens %6d -> %6d (%.2fx)" % (before, after, after / before)
        print(line)
    if ntok:
        print("MEAN tokens %d -> %d (%.2fx)" % (tot_b // 6, tot_a // 6, tot_a / tot_b))
    print("STATS", json.dumps(arc3_compact.STATS))
    assert arc3_compact.STATS["errors"] == 0 and arc3_compact.STATS["posts_changed"] == 6

    # Other POSTs pass through untouched; a malformed body is sent as-is and counted.
    requests.post(url.replace("/chat/completions", "/completions"), json={"prompt": "x"}, timeout=10)
    assert json.loads(received[-1]) == {"prompt": "x"}
    requests.post(url, data=b"{not json", headers={"Content-Type": "application/json"}, timeout=10)
    assert received[-1] == b"{not json" and arc3_compact.STATS["errors"] == 1
    # A request whose history has nothing to strip is sent byte-for-byte.
    tiny = {"messages": [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]}
    requests.post(url, json=tiny, timeout=10)
    assert json.loads(received[-1]) == tiny
    print("OK")


if __name__ == "__main__":
    main()
