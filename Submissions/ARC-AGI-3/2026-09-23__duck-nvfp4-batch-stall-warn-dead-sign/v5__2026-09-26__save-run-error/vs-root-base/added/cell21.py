# v4A gate, save runs only: the new window must have reached the harness. The per-game
# prompt logs record the harness's context budget; v3 logged 31744 at a 32768 window.
if not TRUE_SUBMISSION:
    import re as _re_gate
    _budgets = []
    for _p in sorted((WORKING_DIR / "prompts").glob("*.log")):
        _budgets += [int(x) for x in _re_gate.findall(r"context_budget_tokens:\s*(\d+)", _p.read_text(errors="replace"))]
    _ok = bool(_budgets) and max(_budgets) < ARC3_CTX_V3_BUDGET and max(_budgets) <= ARC3_CTX_WINDOW
    print(
        "ARC3_CTX_CHECK budgets=%s expected=%d ok=%s" % (sorted(set(_budgets)), ARC3_CTX_EXPECTED_BUDGET, _ok),
        flush=True,
    )
    if not _ok:
        raise RuntimeError("v4A: the context window change did not reach the harness; do not submit this version.")
