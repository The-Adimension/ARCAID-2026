# arc3_batch: prompt-only predict-then-commit batching. Nothing else is touched.
#
# tool_agent.py:17 does `from inference.agent.prompts import PYTHON_ADDENDUM`, so the
# value is bound into tool_agent's namespace at import time; patching prompts.py alone
# would be a silent no-op. arc3_batch patches both bindings and then asserts against the
# string _build_system_prompt actually returns, so a miss fails the cell, not the run.
ARC3_BATCH_SOURCE = "\"\"\"arc3_batch: predict-then-commit action batching, as a PROMPT-ONLY change.\n\nWhy this and nothing else (consult/research_2026-09-19_next_jump.md):\n  fp4run1 executed 2.33 actions per charged model decision, 57% of them singletons, at\n  802 generated tokens per executed action. The harness never truncates a batch\n  (stopped_early 0, known_noop 0), so the short batches are the model's own choice --\n  steered by two lines in prompts.py that pull against the one line encouraging batching.\n  Folding an extra action into an existing decision is nearly free, so 2.33 -> ~6 is\n  ~2.5x the actions per game from the same token budget.\n\nExternally corroborated: DREAMTEAM (NVIDIA, arXiv 2605.09650) runs max-actions-per-step\n= 20 behind a commit-then-retrodict gate and reports 54.1 actions per solved level against\na baseline's 100.1; Reki (Milestone-1 2nd) returns 1-4 actions per turn.\n\nTHE PATCH TARGET MATTERS. tool_agent.py:17 does `from inference.agent.prompts import\nPYTHON_ADDENDUM`, so the value is bound into tool_agent's namespace at import time and\n_build_system_prompt (tool_agent.py:499) resolves it as a tool_agent global at call time.\nPatching prompts.PYTHON_ADDENDUM alone is a silent no-op. We patch both and then assert\nagainst the real _build_system_prompt output.\n\nNo harness behaviour is touched: no new mechanism, no gating code, no counters. The only\nthing that changes is the system prompt text.\n\"\"\"\nfrom __future__ import annotations\n\n# --- the three exact lines we rewrite (each must appear exactly once) -----------------\n\nOLD_SHORTEST = (\n    \"- Optimize for the shortest reliable sequence that advances the current goal as \"\n    \"described by your world model. If confidence is low, program a discriminating probe \"\n    \"and revise the world model from the result.\\n\"\n)\nNEW_SHORTEST = (\n    \"- Optimize for the fewest WASTED actions, not the fewest actions per turn. A ten-action \"\n    \"plan you can predict is worth far more than one action you must re-derive next turn. If \"\n    \"confidence is low, program a discriminating probe and revise the world model from the result.\\n\"\n)\n\n# \"After EVERY action, verify\" is a literal instruction to end the turn after one action.\n# The HUD warning itself is a real correctness guard, so it is kept -- moved into the\n# definition of the signature you compare frames on, instead of being a reason to stop.\nOLD_HUD = (\n    \"- After every action, verify whether gameplay objects changed or whether only a timer, \"\n    \"progress bar, or remaining-step bar moved. Do not treat HUD-only changes as evidence \"\n    \"that the move worked.\\n\"\n)\nNEW_HUD = (\n    \"- When you check whether an action worked, ignore HUD-only changes: a timer, progress bar \"\n    \"or remaining-step bar moving is not evidence that the move affected gameplay. Exclude \"\n    \"those rows from any signature you compare frames on.\\n\"\n)\n\n# Anchor: the existing line that already licenses loops. The protocol goes right after it.\nANCHOR_LOOPS = (\n    \"- You can also call `action(...)` multiple times in one Python snippet, including inside \"\n    \"loops. Each call updates the preloaded variables before execution continues.\\n\"\n)\nPROTOCOL = (\n    \"- ACTION BUDGET: reaching one turn of reasoning costs you thousands of tokens; extra actions \"\n    \"inside that same turn cost almost nothing. A turn that executes a single action throws the \"\n    \"turn away. Once you know what the controls do, plan a sequence and commit it.\\n\"\n    \"- PREDICT-THEN-COMMIT: when your world model can predict what the next few actions will do, \"\n    \"execute them in one snippet behind a prediction gate:\\n\"\n    \"      def sig(f):   # cheap board signature; exclude HUD rows\\n\"\n    \"          ...\\n\"\n    \"      plan = [(a1, expected_sig_1), (a2, expected_sig_2), ...]\\n\"\n    \"      for i, (a, expected) in enumerate(plan):\\n\"\n    \"          action([a])\\n\"\n    \"          if last_action_result.get('level_completed') or last_action_result.get('game_over'):\\n\"\n    \"              break\\n\"\n    \"          if sig(current_frame) != expected:\\n\"\n    \"              print('mismatch at step', i, 'expected', expected, 'got', sig(current_frame))\\n\"\n    \"              break        # the world model was wrong: stop here and re-plan next turn\\n\"\n    \"  A mismatch is the most valuable thing the turn can produce, so report where it happened and \"\n    \"what differed. A gated plan is safe: it stops itself the moment reality diverges.\\n\"\n    \"- Aim for 5-15 actions per turn once the controls are understood. Spend one- or two-action \"\n    \"turns only while you are still identifying what the controls do.\\n\"\n)\n\n\ndef build_addendum(current: str) -> str:\n    \"\"\"Apply the three edits to PYTHON_ADDENDUM, failing loudly on upstream drift.\"\"\"\n    for name, old in ((\"OLD_SHORTEST\", OLD_SHORTEST), (\"OLD_HUD\", OLD_HUD),\n                      (\"ANCHOR_LOOPS\", ANCHOR_LOOPS)):\n        n = current.count(old)\n        if n != 1:\n            raise RuntimeError(f\"arc3_batch: expected {name} exactly once in PYTHON_ADDENDUM, found {n}\")\n    out = current.replace(OLD_SHORTEST, NEW_SHORTEST)\n    out = out.replace(OLD_HUD, NEW_HUD)\n    out = out.replace(ANCHOR_LOOPS, ANCHOR_LOOPS + PROTOCOL)\n    return out\n\n\nMARKER = \"PREDICT-THEN-COMMIT\"\n\n\ndef install() -> dict:\n    \"\"\"Patch the system prompt in place. Idempotent; verifies against _build_system_prompt.\"\"\"\n    from inference.agent import prompts as P\n    from inference.agent import tool_agent as TA\n\n    if MARKER in TA.PYTHON_ADDENDUM:\n        return {\"installed\": \"already\"}\n\n    before = len(TA.PYTHON_ADDENDUM)\n    new = build_addendum(TA.PYTHON_ADDENDUM)\n    TA.PYTHON_ADDENDUM = new\n    P.PYTHON_ADDENDUM = new\n\n    # The only proof that matters: the prompt the agent actually sends.\n    built = TA._build_system_prompt(tool_output_tokens=1024)\n    if MARKER not in built:\n        raise RuntimeError(\"arc3_batch: patch did not reach _build_system_prompt\")\n    for name, old in ((\"OLD_SHORTEST\", OLD_SHORTEST), (\"OLD_HUD\", OLD_HUD)):\n        if old in built:\n            raise RuntimeError(f\"arc3_batch: {name} still present in the built system prompt\")\n    return {\n        \"installed\": True,\n        \"addendum_chars\": len(new),\n        \"delta_chars\": len(new) - before,\n        \"system_prompt_chars\": len(built),\n    }\n"
Path('/kaggle/working/arc3_batch.py').write_text(ARC3_BATCH_SOURCE, encoding='utf-8')
if '/kaggle/working' not in sys.path:
    sys.path.insert(0, '/kaggle/working')

import importlib
import arc3_batch
arc3_batch = importlib.reload(arc3_batch)
print('arc3_batch:', arc3_batch.install(), flush=True)

from inference.agent import tool_agent as _ta
_built = _ta._build_system_prompt(tool_output_tokens=1024)
assert arc3_batch.MARKER in _built, 'arc3_batch did not reach the system prompt'
print('ARC3_BATCH_PROMPT chars=%d marker=%s' % (len(_built), arc3_batch.MARKER), flush=True)

# arc3_stall: loop/grind detector on top of arc3_batch. MODE is warn.
# A stuck level adds stuck_warning. Dead signatures are dropped from later batches.
# This file does not issue RESET.
ARC3_STALL_SOURCE = "\"\"\"arc3_stall: tell the agent when it is looping on a level it cannot clear.\n\nEvidence (depthrun1, 6 games x 3600 s). Duck clears every level it clears at or better\nthan human pace, then hits ONE level and grinds without ever clearing it -- 1.4-7.2x the\nhuman baseline, all six games ending `gave_up` still on that level. On the wall level the\naction mix collapses:\n\n    game  cleared-levels uniq_frac -> wall uniq_frac   most-repeated action on the wall\n    sb26            0.67 -> 0.16                       one click x19  of 133\n    vc33            0.24 -> 0.10                       one click x122 of 439\n    lp85            0.29 -> 0.12                       one click x30  of 83\n    re86            0.05 -> 0.02                       ACTION3  x104 of 368\n    ft09            0.67 -> 0.41\n\nvc33 clicked the same cell 122 times. That is a loop, and Duck's own no-op guard cannot\nsee it: the guard only blocks an action that left the board UNCHANGED in that exact state,\nand a looping action usually does change the board (it just changes it pointlessly, or\noscillates). Nothing anywhere else in the harness notices.\n\nMODE is warn. A stuck level adds stuck_warning to the result the model reads. The batch\nis not replaced, and this module does not issue RESET.\n\nDead-signature ban: once reason() is non-empty, a signature that has occurred REPEAT_N\ntimes on this level, or the dominant signature behind that reason, is dropped from\nbatches on this level. The ban clears when the level index changes. RESET and ACTION7\nare never dropped. If every action in a batch is banned, that batch is returned unchanged.\n\nstallrun2 ran warn over the same 6 games: 100 warnings, normalised loop metric 0.234 to\n0.219, levels 19 to 23, and that +4 was entirely sb26 going 1 to 7. Without sb26 that\n6-game mean was 23.33 vs 28.81, with 42% more actions. A 6-game table is not a keep.\nThe public 25-game number for this warn behavior is 3.37 (2026-09-20). The source on that\nrun said MODE=reset, and the print was resets_issued 0, resets_suppressed_invalid 91,\nwarnings_shown 91: the valid-action gate suppressed every RESET, so the run was warn.\nRemoving the gate and issuing RESET scored 2.84. Do not put a batch-replacing RESET back\ninto this file.\n\nBASELINE-FREE BY CONSTRUCTION. base_actions_per_level is None in submission mode\n(game_api.py:232-242), so nothing may compare against the human baseline -- it works on the\n25 public games and silently dies on the hidden set. The grind trigger therefore compares\nthe current level against the median of THAT GAME'S OWN cleared levels. depthrun1 shows the\nseparation is wide: cleared levels ran 4-80 actions, wall levels 83-439.\n\nHooks, and READ THIS BEFORE EDITING. The Kaggle FP4 stack does NOT ship the Duck revision\nin duck-study/taaf. Its bundle (keithtyser/duck-qwen38-nvfp4-mtp-vllm-smoke-v1, dated\n2026-08-31) carries an EARLIER tool_agent.py -- 89,299 bytes against the 108,927 in taaf --\nwith **no noop_guard.py at all**, no `_aggregate_action_batch_result`, and no per-action\nbatch walk: one `action([...])` call is one atomic step_env call. A first version of this\nmodule hooked `NoopGuard.observe` and died on Kaggle with\n`ImportError: cannot import name 'noop_guard' from 'inference.agent'` after 11 minutes of\nsetup. Pre-flight against duck-study/fp4src/ARC3-Inference, which is the shipped source.\n\nBoth hooks are plain methods on ToolAgent, and one ToolAgent plays one game, so per-instance\nstate is per-game state:\n  ToolAgent._normalize_python_actions  -> observe the request, ban dead signatures, drop them\n  ToolAgent._compact_action_result     -> stuck_warning, plus the signatures dropped this call\n`_serialized_runtime_state` and `_handle_action` are CLOSURES inside a method\n(tool_agent.py:1466, :1495 in the shipped file) and cannot be patched from outside.\n\"\"\"\nfrom __future__ import annotations\n\nimport os\nimport statistics\n\nREPEAT_N = int(os.environ.get(\"ARC3_STALL_REPEAT_N\", \"10\"))    # same action this often on one level\nWINDOW = int(os.environ.get(\"ARC3_STALL_WINDOW\", \"40\"))        # rolling window for the mix check\nUNIQ_FRAC = float(os.environ.get(\"ARC3_STALL_UNIQ_FRAC\", \"0.2\"))\nGRIND_MULT = float(os.environ.get(\"ARC3_STALL_GRIND_MULT\", \"3.0\"))\nGRIND_FLOOR = int(os.environ.get(\"ARC3_STALL_GRIND_FLOOR\", \"60\"))\nRENOTIFY_EVERY = int(os.environ.get(\"ARC3_STALL_RENOTIFY\", \"15\"))\n\n# Arming gate, applied to EVERY trigger. Without it the repeat rule fires during healthy\n# play on movement games, where pressing ACTION3 ten times in a row is just walking: the\n# depthrun1 replay warned re86 at action 13 and ar25 at 16 of levels they went on to CLEAR.\n# A warning that interrupts a working plan is worse than a late one, so nothing fires until\n# the level has already cost 3x this game's own cleared levels. At 2.0 the replay still\n# warned inside ar25's level 3 (80 actions against a median of 28) and vc33's level 3,\n# both of which were then CLEARED. 3.0 costs us the ar25 wall entirely and is still the\n# right trade: a late warning wastes actions, a wrong one derails a level being solved.\nMIN_ON_LEVEL = int(os.environ.get(\"ARC3_STALL_MIN_ON_LEVEL\", \"45\"))\n# Warn only. ARC3_STALL_MODE is intentionally not read: a shell export must not\n# turn this file back into a firing reset. The 3.37 public run issued 0 RESET.\nMODE = \"warn\"\nassert MODE == \"warn\"\nARM_MULT = float(os.environ.get(\"ARC3_STALL_ARM_MULT\", \"3.0\"))\n\nSTATS = {\"levels_seen\": 0, \"trips\": 0, \"warnings_shown\": 0,\n         \"bans_armed\": 0, \"actions_dropped\": 0}\n\nclass _Tracker:\n    \"\"\"Per-ToolAgent state, and one ToolAgent plays one game.\"\"\"\n\n    def __init__(self) -> None:\n        self.level = None\n        self.counts: dict[str, int] = {}\n        self.window: list[str] = []\n        self.on_level = 0\n        self.cleared: list[int] = []      # actions spent on each level this game CLEARED\n        self.warned_at = 0\n        self.banned: set[str] = set()\n        self.dropped: list[str] = []\n\n    def _new_level(self, level) -> None:\n        if self.level is not None and self.on_level > 0:\n            # the level advanced, so the previous one was cleared\n            self.cleared.append(self.on_level)\n        self.level = level\n        self.counts = {}\n        self.window = []\n        self.on_level = 0\n        self.warned_at = 0\n        self.banned = set()\n        self.dropped = []\n        STATS[\"levels_seen\"] += 1\n\n    def note_level(self, level) -> None:\n        # First concrete level keeps counts already stored while level was still unknown.\n        if level is None or level == self.level:\n            return\n        if self.level is None:\n            self.level = level\n            STATS[\"levels_seen\"] += 1\n            return\n        self._new_level(level)\n\n    def observe(self, level, action_sig: str) -> None:\n        if level != self.level:\n            self._new_level(level)\n        self.on_level += 1\n        self.counts[action_sig] = self.counts.get(action_sig, 0) + 1\n        self.window.append(action_sig)\n        if len(self.window) > WINDOW:\n            del self.window[0]\n\n    def _dominant(self) -> \"tuple[str, int]\":\n        worst_sig, worst_n = \"\", 0\n        for sig, n in self.counts.items():\n            if n > worst_n:\n                worst_sig, worst_n = sig, n\n        return worst_sig, worst_n\n\n    def reason(self) -> str:\n        \"\"\"Why this level looks stuck, or \"\". Pure: no counters, no state.\"\"\"\n        arm = MIN_ON_LEVEL\n        if self.cleared:\n            arm = max(arm, ARM_MULT * statistics.median(self.cleared))\n        if self.on_level < arm:\n            return \"\"\n\n        worst_sig, worst_n = self._dominant()\n\n        if worst_n >= REPEAT_N:\n            return f\"you have executed {worst_sig} {worst_n} times on this level\"\n        if len(self.window) >= WINDOW and len(set(self.window)) / len(self.window) < UNIQ_FRAC:\n            return (f\"your last {len(self.window)} actions used only \"\n                    f\"{len(set(self.window))} distinct actions\")\n        if self.cleared:\n            budget = max(GRIND_FLOOR, GRIND_MULT * statistics.median(self.cleared))\n            if self.on_level >= budget:\n                return (f\"you have spent {self.on_level} actions on this level, against a median \"\n                        f\"of {statistics.median(self.cleared):.0f} on the levels you already cleared\")\n        elif self.on_level >= max(GRIND_FLOOR, REPEAT_N * 6):\n            return f\"you have spent {self.on_level} actions on this level without clearing it\"\n        return \"\"\n\n    def consider_bans(self) -> None:\n        \"\"\"Mark dead signatures on this level. Never bans RESET or ACTION7.\"\"\"\n        if not self.reason():\n            return\n        worst_sig, _worst_n = self._dominant()\n        for sig, n in self.counts.items():\n            if not sig or _never_ban(sig):\n                continue\n            # reason() is already non-empty, and the level index has not moved:\n            # counts and banned are cleared in _new_level.\n            if n >= REPEAT_N or sig == worst_sig:\n                if sig not in self.banned:\n                    self.banned.add(sig)\n                    STATS[\"bans_armed\"] += 1\n\n    def armed(self) -> str:\n        \"\"\"reason(), rate-limited to once every RENOTIFY_EVERY actions on this level.\"\"\"\n        r = self.reason()\n        if not r:\n            return \"\"\n        if self.warned_at and self.on_level - self.warned_at < RENOTIFY_EVERY:\n            return \"\"\n        self.warned_at = self.on_level\n        STATS[\"trips\"] += 1\n        return r\n\n    def warning(self) -> \"str | None\":\n        r = self.armed()\n        if not r:\n            return None\n        STATS[\"warnings_shown\"] += 1\n        return (\n            f\"STUCK: {r}, and the level has not advanced. Repeating it again will not clear \"\n            \"the level. Your current hypothesis about this level is wrong. Stop executing the plan \"\n            \"you are on, re-read the board from scratch, and form a DIFFERENT hypothesis about what \"\n            \"this level wants -- a different object to act on, a different mechanic, or a different \"\n            \"goal than the one you assumed.\"\n        )\n\n\n_ORIG_NORMALIZE = None\n_ORIG_COMPACT = None\n\n\ndef _tracker(agent) -> \"_Tracker\":\n    t = getattr(agent, \"_arc3_tracker\", None)\n    if t is None:\n        t = _Tracker()\n        try:\n            agent._arc3_tracker = t\n        except Exception:\n            pass\n    return t\n\n\ndef _sig(action) -> str:\n    \"\"\"Signature of one action. Handles BOTH shapes: the tool_agent normalized form\n    {\"action\": NAME, \"row\": r, \"col\": c} (Duck speaks row/col and raises on x/y), and the\n    engine/benchmark form {\"id\": NAME, \"data\": {\"x\": .., \"y\": ..}} used by replays. Getting\n    this wrong collapses every click to one signature and fires the repeat rule on healthy\n    play -- the pre-flight caught exactly that.\n    \"\"\"\n    if not isinstance(action, dict):\n        return str(action)\n    name = str(action.get(\"action\") or action.get(\"id\") or \"?\")\n    if \"row\" in action or \"col\" in action:\n        return f\"{name}:{action.get('row')},{action.get('col')}\"\n    data = action.get(\"data\")\n    if isinstance(data, dict) and data:\n        return f\"{name}:{data.get('x')},{data.get('y')}\"\n    return name\n\n\ndef _never_ban(sig: str) -> bool:\n    name = str(sig).split(\":\", 1)[0]\n    return name in (\"RESET\", \"ACTION7\")\n\n\ndef _level_for(agent, tracker: \"_Tracker\"):\n    last = getattr(agent, \"_last_action_result\", None)\n    if isinstance(last, dict) and last.get(\"level\") is not None:\n        return last.get(\"level\")\n    return tracker.level\n\n\ndef _ban_sentence(sigs: list[str]) -> str:\n    shown = \", \".join(sigs)\n    return (\n        \"banned this level: \"\n        + shown\n        + \" — it was repeated until the level stopped advancing; \"\n        \"do not emit it again on this level; pick a different action.\"\n    )\n\n\ndef install() -> dict:\n    \"\"\"Patch the two ToolAgent methods the shipped revision actually has. Idempotent.\"\"\"\n    global _ORIG_NORMALIZE, _ORIG_COMPACT\n    if MODE != \"warn\":\n        raise RuntimeError(\"arc3_stall: MODE must be warn; this file does not issue RESET\")\n    from inference.agent import tool_agent as TA\n\n    if getattr(TA.ToolAgent._compact_action_result, \"_arc3_stall\", False):\n        return {\"installed\": \"already\"}\n\n    _ORIG_NORMALIZE = TA.ToolAgent._normalize_python_actions\n    _ORIG_COMPACT = TA.ToolAgent._compact_action_result\n\n    def normalize(self, value):\n        out = _ORIG_NORMALIZE(self, value)\n        try:\n            actions = list(out) if isinstance(out, list) else []\n            t = _tracker(self)\n            t.dropped = []\n            level = _level_for(self, t)\n            for action in actions:\n                t.observe(level, _sig(action))\n            t.consider_bans()\n            kept = []\n            dropped = []\n            for action in actions:\n                sig = _sig(action)\n                if _never_ban(sig) or sig not in t.banned:\n                    kept.append(action)\n                else:\n                    dropped.append(action)\n            sigs = []\n            for action in dropped:\n                sig = _sig(action)\n                if sig not in sigs:\n                    sigs.append(sig)\n            t.dropped = sigs\n            # An empty filtered batch is returned unchanged. Do not invent an action.\n            if not kept:\n                return out\n            STATS[\"actions_dropped\"] += len(dropped)\n            return kept\n        except Exception:\n            return out\n\n    normalize._arc3_stall = True\n    TA.ToolAgent._normalize_python_actions = normalize\n\n    def compact(self, payload):\n        out = _ORIG_COMPACT(self, payload)\n        try:\n            if not isinstance(out, dict):\n                return out\n            t = _tracker(self)\n            new_level = out.get(\"level\")\n            advanced = (\n                bool(out.get(\"executed\"))\n                and new_level is not None\n                and t.level is not None\n                and new_level != t.level\n            )\n            dropped = [] if advanced else list(t.dropped or [])\n            t.dropped = []\n            msg = None\n            if out.get(\"executed\") and not advanced:\n                msg = t.warning()\n            if dropped:\n                extra = _ban_sentence(dropped)\n                msg = (msg + \" \" + extra) if msg else extra\n            if msg:\n                out[\"stuck_warning\"] = msg\n            if out.get(\"executed\"):\n                t.note_level(new_level)\n        except Exception:\n            pass   # a counter must never break a run\n        return out\n\n    compact._arc3_stall = True\n    TA.ToolAgent._compact_action_result = compact\n    return {\"installed\": True, \"mode\": MODE,\n            \"repeat_n\": REPEAT_N, \"window\": WINDOW, \"uniq_frac\": UNIQ_FRAC,\n            \"grind_mult\": GRIND_MULT, \"grind_floor\": GRIND_FLOOR,\n            \"min_on_level\": MIN_ON_LEVEL, \"arm_mult\": ARM_MULT,\n            \"bans_armed\": STATS[\"bans_armed\"], \"actions_dropped\": STATS[\"actions_dropped\"]}\n\n\n_BANNED_ACTION_SENTENCE = (\n    \"If a warning lists a banned action, do not emit that same action again on this level.\"\n)\n\nPROMPT_LINE = (\n    \"- `last_action_result` may carry a `stuck_warning` from the runner. It means this level has \"\n    \"already cost far more actions than the levels you cleared, and that you have been repeating \"\n    \"yourself. Treat it as decisive: your hypothesis about this level is wrong. \"\n    \"Re-read the board from scratch and form a different hypothesis about what the level wants \"\n    \"before acting again. \"\n    + _BANNED_ACTION_SENTENCE\n    + \"\\n\"\n)\n\n\ndef install_prompt() -> dict:\n    \"\"\"Tell the model what a stuck_warning means. Same binding trap as arc3_batch.\"\"\"\n    from inference.agent import prompts as P\n    from inference.agent import tool_agent as TA\n\n    have_stuck = \"stuck_warning\" in TA.PYTHON_ADDENDUM\n    have_ban = _BANNED_ACTION_SENTENCE in TA.PYTHON_ADDENDUM\n    if have_stuck and have_ban:\n        return {\"installed\": \"already\"}\n    extra = \"\"\n    if not have_stuck:\n        extra += PROMPT_LINE\n    elif not have_ban:\n        extra += _BANNED_ACTION_SENTENCE + \"\\n\"\n    new = TA.PYTHON_ADDENDUM + extra\n    TA.PYTHON_ADDENDUM = new\n    P.PYTHON_ADDENDUM = new\n    built = TA._build_system_prompt(tool_output_tokens=1024)\n    if \"stuck_warning\" not in built:\n        raise RuntimeError(\"arc3_stall: prompt line did not reach _build_system_prompt\")\n    if \"PREDICT-THEN-COMMIT\" not in built:\n        raise RuntimeError(\"arc3_stall: PREDICT-THEN-COMMIT lost from _build_system_prompt\")\n    if _BANNED_ACTION_SENTENCE not in built:\n        raise RuntimeError(\"arc3_stall: banned-action sentence did not reach _build_system_prompt\")\n    return {\"installed\": True}\n"
Path('/kaggle/working/arc3_stall.py').write_text(ARC3_STALL_SOURCE, encoding='utf-8')
if '/kaggle/working' not in sys.path:
    sys.path.insert(0, '/kaggle/working')
# /kaggle/working was already on sys.path from the arc3_batch cell, so its FileFinder has a
# cached directory listing that predates this write. Without this, `import arc3_stall` raises
# ModuleNotFoundError for a file that is sitting right there -- it did, on reset run v1.
importlib.invalidate_caches()

import arc3_stall
arc3_stall = importlib.reload(arc3_stall)
assert arc3_stall.MODE == 'warn', 'arc3_stall must run in warn mode'
print('arc3_stall:', arc3_stall.install(), flush=True)
print('arc3_stall prompt:', arc3_stall.install_prompt(), flush=True)

_built2 = _ta._build_system_prompt(tool_output_tokens=1024)
assert 'stuck_warning' in _built2, 'arc3_stall prompt line did not reach the system prompt'
assert arc3_batch.MARKER in _built2, 'arc3_batch protocol lost'
print('ARC3_STALL_READY chars=%d' % len(_built2), flush=True)
_BANNED_PROMPT = (
    'WHEN AN ATTEMPT FAILS',
    'SELECT THEN PLACE',
    'PATH BEFORE READING ORDER',
    'CENTER MAP',
    'arc3_ledger',
    'arc3_select',
    'arc3_path',
    'arc3_map',
)
for _banned in _BANNED_PROMPT:
    assert _banned not in _built2, _banned
    assert _banned not in ARC3_STALL_SOURCE, _banned
    assert _banned not in ARC3_BATCH_SOURCE, _banned
assert '_maybe_reset' not in ARC3_STALL_SOURCE
assert not hasattr(arc3_stall, '_maybe_reset')
assert 'resets_issued' not in arc3_stall.STATS
assert '[{"action": "RESET"}]' not in ARC3_STALL_SOURCE
assert 'If a warning lists a banned action, do not emit that same action again on this level.' in _built2
assert 'banned this level' in ARC3_STALL_SOURCE
assert 'level was RESET' not in ARC3_STALL_SOURCE
assert 'bans_armed' in arc3_stall.STATS
assert 'actions_dropped' in arc3_stall.STATS
assert arc3_stall.MODE == 'warn'
assert arc3_stall.ARM_MULT >= 3.0
assert arc3_stall.MIN_ON_LEVEL >= 45
_EXPECTED_PROFILE = {
    "TAAF_VLLM_ENABLE_PREFIX_CACHING": "0",
    "TAAF_VLLM_KV_CACHE_DTYPE": "auto",
    "TAAF_VLLM_KV_CACHE_MEMORY_BYTES": "5368709120",
    "TAAF_VLLM_MAX_CUDAGRAPH_CAPTURE_SIZE": "32",
    "TAAF_VLLM_MAX_NUM_BATCHED_TOKENS": "8192",
    "TAAF_VLLM_MAX_NUM_SEQS": "8",
    "TAAF_VLLM_MTP_TOKENS": "3",
    "TAAF_VLLM_OMP_THREADS": "1",
}
assert PUBLIC25_VLLM_PROFILE_NAME == 'kv5-bf16-mtp3-c8-cg32'
assert PUBLIC25_VLLM_PROFILE_ENV == _EXPECTED_PROFILE
for _k, _v in _EXPECTED_PROFILE.items():
    assert os.environ.get(_k) == _v, (_k, os.environ.get(_k))
assert os.environ.get('ONLY_RESET_LEVELS') == 'true'
assert isinstance(TRUE_SUBMISSION, bool)
print(
    'ARC3_POLICY mode=%s dead_signature=on reset_injector=absent ledger=absent profile=%s only_reset_levels=%s'
    % (arc3_stall.MODE, PUBLIC25_VLLM_PROFILE_NAME, os.environ.get('ONLY_RESET_LEVELS')),
    flush=True,
)


# arc3_score (2026-09-25): scoring, time and click-target lines. Prompt-only, with the same
# binding trap as arc3_batch: patch both PYTHON_ADDENDUM bindings, then assert on the prompt
# _build_system_prompt actually returns. Evidence: disc/743060 went 1.12 -> 1.43 on the hidden
# set with a scoring-formula line plus a time_remaining_seconds pacing line. Formula per
# docs.arcprize.org/methodology (level weight = level index; RESET counts as an action).
import re as _re

_inference_root = Path(_ta.__file__).resolve().parents[1]
_inference_src = "\n".join(
    _p.read_text(encoding="utf-8", errors="replace") for _p in sorted(_inference_root.rglob("*.py"))
)
# Point at the live clock only if this bundle's harness reports it; otherwise state the budget.
ARC3_HAS_TIME_FIELD = "time_remaining_seconds" in _inference_src
# Add the click hint only if the harness itself uses these names.
ARC3_HAS_GRID_NAMES = (
    "current_frame" in _inference_src
    and _re.search(r"""['"]row['"]""", _inference_src) is not None
    and _re.search(r"""['"]col['"]""", _inference_src) is not None
)

ARC3_SCORE_MARKER = "SCORING (how this run is graded)"
ARC3_SCORE_LINE = (
    "- " + ARC3_SCORE_MARKER + ": each level you CLEAR scores (h / a)^2, where h is the number "
    "of actions a first-time human needed on that level and a is the number you used. Every action "
    "counts, including RESET. Level k carries weight k: in a 7-level game level 7 is worth 7/28 of "
    "the game and level 1 only 1/28. A level you do not clear scores 0. Clearing a level at twice "
    "the human's actions still keeps 1/4 of its value; not clearing it keeps nothing. So never "
    "explore less to save actions: save actions by never repeating an action or plan that already "
    "failed.\n"
)
if ARC3_HAS_TIME_FIELD:
    _arc3_clock = "Action results report `time_remaining_seconds`; pace yourself with it."
else:
    _arc3_clock = "You have about %d minutes of wall-clock time for this whole game." % int(
        float(bm.solver.max_runtime_s_per_game) // 60
    )
ARC3_TIME_LINE = (
    "- TIME: the game ends when your wall-clock budget runs out, not when actions run out, and "
    "every turn of reasoning spends that budget. " + _arc3_clock + " Time sunk into a level you "
    "cannot crack is time taken from the deeper levels, which are worth more.\n"
)
ARC3_GRID_LINE = (
    "- CLICK TARGETS: clicks address grid cells (row, col) of the 64x64 grid in `current_frame`: "
    "row counts down from the top (y), col counts right from the left (x), both 0-63. Take targets "
    "from the grid, never by estimating positions in the image: "
    "cells = [(r, c) for r, line in enumerate(current_frame) for c, v in enumerate(line) if v == colour] "
    "lists every cell of one colour; click a cell that is on the object you mean.\n"
)


def _arc3_score_install() -> dict:
    from inference.agent import prompts as P
    from inference.agent import tool_agent as TA

    if ARC3_SCORE_MARKER in TA.PYTHON_ADDENDUM:
        return {"installed": "already"}
    anchor = arc3_batch.NEW_SHORTEST
    n = TA.PYTHON_ADDENDUM.count(anchor)
    if n != 1:
        raise RuntimeError(f"arc3_score: expected the arc3_batch shortest line exactly once, found {n}")
    block = ARC3_SCORE_LINE + ARC3_TIME_LINE + (ARC3_GRID_LINE if ARC3_HAS_GRID_NAMES else "")
    new = TA.PYTHON_ADDENDUM.replace(anchor, block + anchor)
    TA.PYTHON_ADDENDUM = new
    P.PYTHON_ADDENDUM = new
    built = TA._build_system_prompt(tool_output_tokens=1024)
    for need in (ARC3_SCORE_MARKER, "- TIME: the game ends", arc3_batch.MARKER, "stuck_warning"):
        if need not in built:
            raise RuntimeError(f"arc3_score: {need!r} missing from _build_system_prompt")
    if ARC3_HAS_GRID_NAMES and "CLICK TARGETS" not in built:
        raise RuntimeError("arc3_score: click-target line missing from _build_system_prompt")
    return {"installed": True, "delta_chars": len(block), "system_prompt_chars": len(built)}


print("arc3_score:", _arc3_score_install(), flush=True)

# arc3_stall counter, observe-only: the 09-23 probe armed 40 bans and dropped 0 actions. The
# predict-then-commit loop sends one action per action([a]) call, and a fully banned call is
# passed through unchanged, so a banned singleton is never dropped. Count both, change nothing.
arc3_stall.STATS.setdefault("calls_seen", 0)
arc3_stall.STATS.setdefault("calls_single_action", 0)
arc3_stall.STATS.setdefault("calls_fully_banned_passthrough", 0)
if not getattr(_ta.ToolAgent._normalize_python_actions, "_arc3_counter", False):
    _arc3_inner_normalize = _ta.ToolAgent._normalize_python_actions

    def _arc3_counted_normalize(self, value):
        out = _arc3_inner_normalize(self, value)
        try:
            acts = out if isinstance(out, list) else []
            arc3_stall.STATS["calls_seen"] += 1
            if len(acts) == 1:
                arc3_stall.STATS["calls_single_action"] += 1
            t = getattr(self, "_arc3_tracker", None)
            if t is not None and acts and t.banned and all(
                (not arc3_stall._never_ban(arc3_stall._sig(a))) and arc3_stall._sig(a) in t.banned
                for a in acts
            ):
                arc3_stall.STATS["calls_fully_banned_passthrough"] += 1
        except Exception:
            pass   # a counter must never break a run
        return out

    _arc3_counted_normalize._arc3_stall = True
    _arc3_counted_normalize._arc3_counter = True
    _ta.ToolAgent._normalize_python_actions = _arc3_counted_normalize

_built3 = _ta._build_system_prompt(tool_output_tokens=1024)
for _banned in _BANNED_PROMPT:
    assert _banned not in _built3, _banned
assert arc3_batch.MARKER in _built3 and "stuck_warning" in _built3 and ARC3_SCORE_MARKER in _built3
print(
    "ARC3_SCORE_READY chars=%d time_field=%s grid_hint=%s counter=%s"
    % (len(_built3), ARC3_HAS_TIME_FIELD, ARC3_HAS_GRID_NAMES,
       getattr(_ta.ToolAgent._normalize_python_actions, "_arc3_counter", False)),
    flush=True,
)
