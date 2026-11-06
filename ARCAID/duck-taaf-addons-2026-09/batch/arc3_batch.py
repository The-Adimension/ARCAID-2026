"""arc3_batch: predict-then-commit action batching, as a PROMPT-ONLY change.

Why this and nothing else (consult/research_2026-09-19_next_jump.md):
  fp4run1 executed 2.33 actions per charged model decision, 57% of them singletons, at
  802 generated tokens per executed action. The harness never truncates a batch
  (stopped_early 0, known_noop 0), so the short batches are the model's own choice --
  steered by two lines in prompts.py that pull against the one line encouraging batching.
  Folding an extra action into an existing decision is nearly free, so 2.33 -> ~6 is
  ~2.5x the actions per game from the same token budget.

Externally corroborated: DREAMTEAM (NVIDIA, arXiv 2605.09650) runs max-actions-per-step
= 20 behind a commit-then-retrodict gate and reports 54.1 actions per solved level against
a baseline's 100.1; Reki (Milestone-1 2nd) returns 1-4 actions per turn.

THE PATCH TARGET MATTERS. tool_agent.py:17 does `from inference.agent.prompts import
PYTHON_ADDENDUM`, so the value is bound into tool_agent's namespace at import time and
_build_system_prompt (tool_agent.py:499) resolves it as a tool_agent global at call time.
Patching prompts.PYTHON_ADDENDUM alone is a silent no-op. We patch both and then assert
against the real _build_system_prompt output.

No harness behaviour is touched: no new mechanism, no gating code, no counters. The only
thing that changes is the system prompt text.
"""
from __future__ import annotations

# --- the three exact lines we rewrite (each must appear exactly once) -----------------

OLD_SHORTEST = (
    "- Optimize for the shortest reliable sequence that advances the current goal as "
    "described by your world model. If confidence is low, program a discriminating probe "
    "and revise the world model from the result.\n"
)
NEW_SHORTEST = (
    "- Optimize for the fewest WASTED actions, not the fewest actions per turn. A ten-action "
    "plan you can predict is worth far more than one action you must re-derive next turn. If "
    "confidence is low, program a discriminating probe and revise the world model from the result.\n"
)

# "After EVERY action, verify" is a literal instruction to end the turn after one action.
# The HUD warning itself is a real correctness guard, so it is kept -- moved into the
# definition of the signature you compare frames on, instead of being a reason to stop.
OLD_HUD = (
    "- After every action, verify whether gameplay objects changed or whether only a timer, "
    "progress bar, or remaining-step bar moved. Do not treat HUD-only changes as evidence "
    "that the move worked.\n"
)
NEW_HUD = (
    "- When you check whether an action worked, ignore HUD-only changes: a timer, progress bar "
    "or remaining-step bar moving is not evidence that the move affected gameplay. Exclude "
    "those rows from any signature you compare frames on.\n"
)

# Anchor: the existing line that already licenses loops. The protocol goes right after it.
ANCHOR_LOOPS = (
    "- You can also call `action(...)` multiple times in one Python snippet, including inside "
    "loops. Each call updates the preloaded variables before execution continues.\n"
)
PROTOCOL = (
    "- ACTION BUDGET: reaching one turn of reasoning costs you thousands of tokens; extra actions "
    "inside that same turn cost almost nothing. A turn that executes a single action throws the "
    "turn away. Once you know what the controls do, plan a sequence and commit it.\n"
    "- PREDICT-THEN-COMMIT: when your world model can predict what the next few actions will do, "
    "execute them in one snippet behind a prediction gate:\n"
    "      def sig(f):   # cheap board signature; exclude HUD rows\n"
    "          ...\n"
    "      plan = [(a1, expected_sig_1), (a2, expected_sig_2), ...]\n"
    "      for i, (a, expected) in enumerate(plan):\n"
    "          action([a])\n"
    "          if last_action_result.get('level_completed') or last_action_result.get('game_over'):\n"
    "              break\n"
    "          if sig(current_frame) != expected:\n"
    "              print('mismatch at step', i, 'expected', expected, 'got', sig(current_frame))\n"
    "              break        # the world model was wrong: stop here and re-plan next turn\n"
    "  A mismatch is the most valuable thing the turn can produce, so report where it happened and "
    "what differed. A gated plan is safe: it stops itself the moment reality diverges.\n"
    "- Aim for 5-15 actions per turn once the controls are understood. Spend one- or two-action "
    "turns only while you are still identifying what the controls do.\n"
)


def build_addendum(current: str) -> str:
    """Apply the three edits to PYTHON_ADDENDUM, failing loudly on upstream drift."""
    for name, old in (("OLD_SHORTEST", OLD_SHORTEST), ("OLD_HUD", OLD_HUD),
                      ("ANCHOR_LOOPS", ANCHOR_LOOPS)):
        n = current.count(old)
        if n != 1:
            raise RuntimeError(f"arc3_batch: expected {name} exactly once in PYTHON_ADDENDUM, found {n}")
    out = current.replace(OLD_SHORTEST, NEW_SHORTEST)
    out = out.replace(OLD_HUD, NEW_HUD)
    out = out.replace(ANCHOR_LOOPS, ANCHOR_LOOPS + PROTOCOL)
    return out


MARKER = "PREDICT-THEN-COMMIT"


def install() -> dict:
    """Patch the system prompt in place. Idempotent; verifies against _build_system_prompt."""
    from inference.agent import prompts as P
    from inference.agent import tool_agent as TA

    if MARKER in TA.PYTHON_ADDENDUM:
        return {"installed": "already"}

    before = len(TA.PYTHON_ADDENDUM)
    new = build_addendum(TA.PYTHON_ADDENDUM)
    TA.PYTHON_ADDENDUM = new
    P.PYTHON_ADDENDUM = new

    # The only proof that matters: the prompt the agent actually sends.
    built = TA._build_system_prompt(tool_output_tokens=1024)
    if MARKER not in built:
        raise RuntimeError("arc3_batch: patch did not reach _build_system_prompt")
    for name, old in (("OLD_SHORTEST", OLD_SHORTEST), ("OLD_HUD", OLD_HUD)):
        if old in built:
            raise RuntimeError(f"arc3_batch: {name} still present in the built system prompt")
    return {
        "installed": True,
        "addendum_chars": len(new),
        "delta_chars": len(new) - before,
        "system_prompt_chars": len(built),
    }
