"""arc3_compact: shrink each chat request to the local vLLM server without dropping history.

Why. The v3 save run was bound by the KV cache: the 5 GiB pool (105,202 tokens) held ~3
requests at a time (average prompt 21.5K tokens) while ~2.7 more waited, and in the
28-game competition rerun far more wait. Two parts of every prompt carry nothing new:
  - The model's chat template keeps the reasoning of every earlier assistant message
    (`preserve_thinking` defaults to true), so old chains of thought pile up in history.
  - Every earlier USER message repeats the same 14 instruction lines.
Measured on v3's six prompt snapshots with the model's own tokenizer: old reasoning is ~36%
of the prompt and the repeated instruction lines are ~14%.

What. On each POST to /chat/completions sent from this process through urllib3 (the
harness's HTTP client; its timeouts are urllib3 `HTTPConnectionPool ... Read timed out`):
  1. Drop the reasoning of assistant messages that are older than both the current turn
     (everything after the newest USER message) and the newest KEEP_REASONING assistant
     messages. Their content, tool calls and tool results stay.
  2. Drop the 14 fixed instruction lines from every USER message except the newest one.
     Executed actions, level/state lines, the carried world model and the grid image stay.
The harness's own history trimming is untouched, so the model sees the same turns as in v3.
Replayed on v3's snapshots (KEEP_REASONING=2), prompts shrink to 0.62x (21.6K -> 13.3K).

Any exception leaves the request exactly as it was. STATS counts what was changed.
"""

import json
import re
import threading

MARKER = "ARC3_COMPACT"
KEEP_REASONING = 2
STRIP_INSTRUCTIONS = True
PATH_SUFFIX = "/chat/completions"
REASONING_KEYS = ("reasoning_content", "reasoning")

# Lines repeated verbatim in every USER turn of v3's prompts (present in >=90% of 38 USER
# messages across the six snapshots). Only exact whole-line matches are removed.
INSTRUCTION_LINES = frozenset([
    "If you use MOUSE, include integer row and col arguments.",
    "Only letter-coded board views and lightweight metadata are exposed; raw numeric color IDs are not available.",
    "Maintain a compact working world model of what the current level seems to contain, what actions appear to do, what the goal seems to be, what is still uncertain, and what plan currently looks best.",
    "If you include assistant text before a tool call, keep it short and use it to update the world model. Helpful optional prefixes are `World model:`, `Goal model:`, `Action model:`, `Recent findings:`, `Open questions:`, `Plan:`, and `Cross-level notes:`.",
    "You may call `action(actions)` more than once in one Python snippet if your search or control loop needs it, but stop immediately if a result reports `game_over`, `run_complete`, `level_completed`, or `done`.",
    "You may call `action(actions)` more than once in one Python snippet if your search or control loop needs it.",
    "Focus on what changed most recently in `history`, update the target environment change if needed, and separate gameplay-object changes from HUD-only changes.",
    "Keep tool output compact: use `current_frame.segmentation` as the primary view, and `current_frame.ascii` only for a small specific region; never print full boards.",
    "Only tool: `python`. It receives `current_frame`, `previous_frame`, `history`, `transitions`, `last_transition`, `valid_actions`, `last_action_result`, and `action(actions)`.",
    "Use Python to inspect the evidence, refine that world model from the newest history, and search or score candidate actions or short sequences against the current goal as you currently understand it.",
    "When calling `python`, emit exactly the tool-call format shown elsewhere in this prompt for this model. Use only that format; do not add markdown fences, prose wrappers, or alternate tool-call syntax. Do not quote or place tool-call markup inside explanatory text; when you decide to call the tool, emit the tool call itself.",
    "When ready, call `action(actions)` from inside the `python` tool with the best valid action or ordered batch selected by your code. If your code has found a reliable short sequence, prefer batching it in one call.",
    "For the most recent change, compare `previous_frame` to `current_frame`, or `last_transition.before_frame` to `last_transition.after_frame`; `history[-1].frame` is the current frame, not the previous one.",
    "Below you are provided with the current world model from the previous turn. The default behavior is to copy it and add or remove things based on the evidence that you gathered. BEFORE EXECUTING NEW ACTIONS YOU MUST ALWAYS GIVE THE REVISED VERSION OF THE WORLD MODEL.",
])

_THINK_RE = re.compile(r"<think>.*?</think>\s*", re.S)
_LOCK = threading.Lock()
STATS = {
    "posts_seen": 0,
    "posts_changed": 0,
    "reasoning_dropped": 0,
    "reasoning_chars": 0,
    "instruction_lines_dropped": 0,
    "instruction_chars": 0,
    "bytes_before": 0,
    "bytes_after": 0,
    "errors": 0,
    "last_error": None,
}


def _strip_lines(text):
    lines = text.split("\n")
    kept = [line for line in lines if line not in INSTRUCTION_LINES]
    dropped = len(lines) - len(kept)
    if not dropped:
        return text, 0, 0
    new = "\n".join(kept)
    return new, dropped, len(text) - len(new)


def compact_messages(messages):
    """Edit an OpenAI-style message list in place. Returns a dict of what changed."""
    out = {"reasoning_dropped": 0, "reasoning_chars": 0,
           "instruction_lines_dropped": 0, "instruction_chars": 0}
    if not isinstance(messages, list):
        return out
    users = [i for i, m in enumerate(messages) if isinstance(m, dict) and m.get("role") == "user"]
    last_user = users[-1] if users else -1
    assistants = [i for i, m in enumerate(messages) if isinstance(m, dict) and m.get("role") == "assistant"]
    keep = set(assistants[-KEEP_REASONING:]) if KEEP_REASONING > 0 else set()
    keep.update(i for i in assistants if i > last_user)

    for i in assistants:
        if i in keep:
            continue
        m = messages[i]
        dropped = False
        for key in REASONING_KEYS:
            value = m.get(key)
            if isinstance(value, str) and value:
                out["reasoning_chars"] += len(value)
                m.pop(key)
                dropped = True
        content = m.get("content")
        if isinstance(content, str) and "<think>" in content:
            new = _THINK_RE.sub("", content)
            out["reasoning_chars"] += len(content) - len(new)
            m["content"] = new
            dropped = True
        if dropped:
            out["reasoning_dropped"] += 1

    if STRIP_INSTRUCTIONS:
        for i in users[:-1]:
            m = messages[i]
            content = m.get("content")
            if isinstance(content, str):
                m["content"], n, c = _strip_lines(content)
                out["instruction_lines_dropped"] += n
                out["instruction_chars"] += c
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
                        part["text"], n, c = _strip_lines(part["text"])
                        out["instruction_lines_dropped"] += n
                        out["instruction_chars"] += c
    return out


def rewrite_body(body):
    """Return (new_body, changed) for a JSON chat-completions body given as bytes or str."""
    raw = body.decode("utf-8") if isinstance(body, (bytes, bytearray)) else body
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        return body, None
    delta = compact_messages(payload.get("messages"))
    if not (delta["reasoning_dropped"] or delta["instruction_lines_dropped"]):
        return body, delta
    new = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return new, delta


def _set_content_length(headers, n):
    if headers is None:
        return
    for key in list(headers.keys()):
        if str(key).lower() == "content-length":
            headers[key] = str(n)
            return


def install():
    """Wrap urllib3's HTTPConnectionPool.urlopen once. Returns True if installed now or before."""
    import urllib3.connectionpool as _cp

    current = _cp.HTTPConnectionPool.urlopen
    if getattr(current, "_arc3_compact", False):
        return True
    inner = current

    def urlopen(self, method, url, body=None, headers=None, *args, **kwargs):
        if (
            body is not None
            and str(method).upper() == "POST"
            and str(url).split("?", 1)[0].endswith(PATH_SUFFIX)
            and isinstance(body, (bytes, bytearray, str))
        ):
            try:
                new, delta = rewrite_body(body)
                with _LOCK:
                    STATS["posts_seen"] += 1
                    if new is not body and delta:
                        STATS["posts_changed"] += 1
                        STATS["bytes_before"] += len(body)
                        STATS["bytes_after"] += len(new)
                        for k in ("reasoning_dropped", "reasoning_chars",
                                  "instruction_lines_dropped", "instruction_chars"):
                            STATS[k] += delta[k]
                if new is not body:
                    body = new
                    _set_content_length(headers, len(new))
            except Exception as exc:   # never break a request
                with _LOCK:
                    STATS["errors"] += 1
                    STATS["last_error"] = repr(exc)[:300]
        return inner(self, method, url, body, headers, *args, **kwargs)

    urlopen._arc3_compact = True
    urlopen.__wrapped__ = inner
    _cp.HTTPConnectionPool.urlopen = urlopen
    return True
