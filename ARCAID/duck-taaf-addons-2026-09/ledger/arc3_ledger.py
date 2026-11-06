"""arc3_ledger: hypothesis bookkeeping after a failed attempt. PROMPT-ONLY.

Evidence (consult/walls_2026-09-21.md). On sb26 level 2 a run that solved it in 3 turns and a
run that failed after 153 actions perceived the board identically and shared the same, correct
model of the controls. They differed in ONE assumption about the goal: the winner read the green
connector as a path, the loser used reading order. The loser's attempt failed on its second turn,
and it then spent 57 turns re-investigating controls it had already confirmed and never tried
the other ordering. Both runs that passed that level went on to level 8.

So the change is aimed at what happens AFTER a failed attempt: keep what was observed, blame the
assumption the attempt rested on, and try its alternatives. It tells the model something and
leaves the choice to it -- the style of both changes that helped (batching 2.49 -> 3.04, stuck
warning 3.04 -> 3.37), unlike the one that overrode it (forced reset, 2.84).

Same binding trap as arc3_batch: tool_agent does `from inference.agent.prompts import
PYTHON_ADDENDUM`, so both bindings are patched and the result is asserted against
_build_system_prompt, the string the agent actually sends.
"""
from __future__ import annotations

MARKER = "WHEN AN ATTEMPT FAILS"

LEDGER = (
    "- WHEN AN ATTEMPT FAILS -- your plan ran to the end, or you submitted, and the level did not "
    "complete -- do not re-investigate what you have already confirmed by direct observation. "
    "Write two short lists in your reasoning. CONFIRMED: facts you have actually seen happen "
    "(what a control does, what an object is). ASSUMED: the specific guess this attempt depended "
    "on (the order things go in, which object is the target, how pieces are grouped, what the "
    "goal state looks like). The failure is evidence about the ASSUMED list, not the CONFIRMED "
    "one. List the few other readings of that assumption and try the cheapest untried one next. "
    "Reopen a confirmed fact only if a new observation contradicts it.\n"
)


def install() -> dict:
    """Append the ledger rule to PYTHON_ADDENDUM. Idempotent; verified against the real prompt."""
    from inference.agent import prompts as P
    from inference.agent import tool_agent as TA

    if MARKER in TA.PYTHON_ADDENDUM:
        return {"installed": "already"}
    before = len(TA.PYTHON_ADDENDUM)
    new = TA.PYTHON_ADDENDUM + LEDGER
    TA.PYTHON_ADDENDUM = new
    P.PYTHON_ADDENDUM = new
    built = TA._build_system_prompt(tool_output_tokens=1024)
    if MARKER not in built:
        raise RuntimeError("arc3_ledger: rule did not reach _build_system_prompt")
    return {"installed": True, "delta_chars": len(new) - before, "system_prompt_chars": len(built)}
