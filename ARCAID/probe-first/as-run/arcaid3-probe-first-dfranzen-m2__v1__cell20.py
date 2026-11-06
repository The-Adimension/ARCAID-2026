# First-run defaults (explicit for the record; the cell reads these from the environment).
import os as _pf_env
for _k, _v in (("PF", "1"), ("PF_NUDGE_AT", "3"), ("PF_CAP_AT", "5"), ("PF_CAP_TOKENS", "4096")):
    _pf_env.environ.setdefault(_k, _v)

# ---------------------------------------------------------------------------------------------
# Probe-first governor (PF). Paste-in cell for Daniel Franzen's Milestone 2 notebook (v1, N40)
# or any TAAF/Duck notebook that carries his harness patch. Place it AFTER the cell that puts
# the bundled source on sys.path ("4. Import the bundled source") and BEFORE "9. Run the
# benchmark". Standard library only. Kill switch: set env PF=0 before this cell runs.
#
# What it changes, and nothing else:
#   1. Ledger. Per game, the cell counts (a) actions spent on the CURRENT level and (b) how many
#      consecutive model exchanges executed no action. Both are read from the harness's own
#      step summary (`action_num`, `level`); the cell never issues, skips or re-counts an action.
#   2. Nudge. From the PF_NUDGE_AT-th consecutive no-action exchange, the turn opener gets one
#      extra paragraph that states the ledger and the scoring economics: on a level where few
#      actions have been spent, a 1-3 action test is cheaper than another round of planning.
#      Above a typical human count the wording flips to "every further action costs score".
#   3. Cap. From the PF_CAP_AT-th consecutive no-action exchange, requests are sent with
#      max_tokens=PF_CAP_TOKENS until an action executes. Explicit max_tokens set by the
#      harness (e.g. summary requests) are never overridden.
#
# Invariants: valid actions still come only from the harness (`valid_actions`); a game_over
# auto-RESET keeps the level, so the ledger persists through it; a level_completed resets the
# ledger; RESET counts as an action because the harness's `action_num` advances; no network,
# no files. Any error inside the wrappers falls back to the stock behaviour and is counted.
# ---------------------------------------------------------------------------------------------
import os as _os

PF_ON = _os.environ.get("PF", "1").strip() not in ("0", "", "false", "False")
PF_NUDGE_AT = int(_os.environ.get("PF_NUDGE_AT", "3"))      # consecutive no-action exchanges
PF_CAP_AT = int(_os.environ.get("PF_CAP_AT", "5"))          # consecutive no-action exchanges
PF_CAP_TOKENS = int(_os.environ.get("PF_CAP_TOKENS", "4096"))
# Free-probe allowance per level depth. 0.4 x the per-depth median human action count of the
# 25 public games (medians: L1 30, L2-L4 ~52, L5+ ~90). It is a prior, not the hidden
# baseline; it only decides which wording the nudge uses.
PF_FREE = {1: 12, 2: 20, 3: 20, 4: 20}
PF_FREE_DEFAULT = 30
PF_CAUTION_MULT = 2.5   # free x 2.5 ~ the per-depth median human count; a > h is where (h/a)^2 bites

PF_STATS = globals().get("PF_STATS") or {
    "openers": 0, "nudged": 0, "capped_requests": 0, "max_streak": 0, "errors": 0,
}


def _pf_state(agent):
    return agent.__dict__.setdefault(
        "_pf", {"level": None, "level_start": 0, "last_action": None, "streak": 0}
    )


def _pf_update(agent, summary):
    """Advance the ledger from the harness's step summary. Returns the ledger."""
    st = _pf_state(agent)
    if not isinstance(summary, dict):
        return st
    level, action_num = summary.get("level"), summary.get("action_num")
    if level is None or action_num is None:
        return st
    level, action_num = int(level), int(action_num)
    if st["level"] != level:                       # level_completed: fresh ledger
        st.update(level=level, level_start=action_num, streak=0, last_action=action_num)
        return st
    if st["last_action"] is None or action_num > st["last_action"]:
        st["streak"] = 0                           # something executed since the last opener
    else:
        st["streak"] += 1                          # inspect-only exchange
    st["last_action"] = action_num
    return st


def _pf_lines(st):
    if st["level"] is None or st["last_action"] is None or st["streak"] < PF_NUDGE_AT:
        return []
    used = max(0, st["last_action"] - st["level_start"])
    free = PF_FREE.get(st["level"], PF_FREE_DEFAULT)
    head = (
        f"Probe ledger: {st['streak']} consecutive exchanges executed no action; "
        f"{used} action(s) spent on this level."
    )
    if used < free:
        body = (
            "Actions are cheap here and reasoning is not: a level scores the same once you "
            "beat the human action count, and you are far below it. If any step of your plan "
            "rests on a rule you have not observed, run a 1-3 action test of that rule now and "
            "read `frame_diff()`, instead of searching inside a model you have not verified."
        )
    elif used < free * PF_CAUTION_MULT:
        body = (
            "You are within the normal action range for a level. Prefer one short, decisive "
            "test over another round of planning; batch only what the evidence supports."
        )
    else:
        body = (
            "This is above a typical human action count, so every further action now lowers "
            "this level's score. Spend the next action on whatever most reduces your "
            "uncertainty, and if the level is in an unrecoverable state use RESET if it is "
            "listed in `valid_actions`."
        )
    return [head + " " + body]


def _pf_find_summary(args, kwargs):
    cand = kwargs.get("previous_step_summary")
    if isinstance(cand, dict):
        return cand
    for a in args:
        if isinstance(a, dict) and "action_num" in a:
            return a
    return None


def _pf_cap_kwargs(st, kwargs):
    """Return kwargs with max_tokens capped while the no-action streak is long."""
    if st["streak"] >= PF_CAP_AT and kwargs.get("max_tokens") is None:
        kwargs = dict(kwargs)
        kwargs["max_tokens"] = PF_CAP_TOKENS
        return kwargs, True
    return kwargs, False


def _pf_install():
    import inference.agent.tool_agent as _ta
    cls = _ta.ToolAgent
    if getattr(cls, "_pf_installed", False):
        return "already_installed"

    _orig_prompt = cls._build_user_prompt
    _orig_chat = cls._chat_completion

    def _build_user_prompt(self, *args, **kwargs):
        out = _orig_prompt(self, *args, **kwargs)
        try:
            PF_STATS["openers"] += 1
            st = _pf_update(self, _pf_find_summary(args, kwargs))
            PF_STATS["max_streak"] = max(PF_STATS["max_streak"], st["streak"])
            lines = _pf_lines(st)
            if lines and isinstance(out, str):
                PF_STATS["nudged"] += 1
                out = out + "\n" + "\n".join(lines)
            if PF_STATS["openers"] % 100 == 0:
                print("ARC3_PF_STATS", PF_STATS, flush=True)
        except Exception:
            PF_STATS["errors"] += 1
        return out

    def _chat_completion(self, messages, *args, **kwargs):
        try:
            kwargs, capped = _pf_cap_kwargs(_pf_state(self), kwargs)
            if capped:
                PF_STATS["capped_requests"] += 1
        except Exception:
            PF_STATS["errors"] += 1
        return _orig_chat(self, messages, *args, **kwargs)

    for new, old in ((_build_user_prompt, _orig_prompt), (_chat_completion, _orig_chat)):
        for attr in ("__doc__", "__name__", "__qualname__"):
            setattr(new, attr, getattr(old, attr, None))
    cls._build_user_prompt = _build_user_prompt
    cls._chat_completion = _chat_completion
    cls._pf_installed = True
    return "installed"


def _pf_selftest():
    class _Stub:
        pass
    a = _Stub()
    # level 1, three exchanges with no new action -> nudge appears on the 3rd no-action exchange
    assert _pf_update(a, {"level": 1, "action_num": 4})["streak"] == 0
    assert _pf_update(a, {"level": 1, "action_num": 4})["streak"] == 1
    assert _pf_update(a, {"level": 1, "action_num": 4})["streak"] == 2
    assert _pf_lines(_pf_state(a)) == []
    st = _pf_update(a, {"level": 1, "action_num": 4})
    assert st["streak"] == 3 and len(_pf_lines(st)) == 1 and "Actions are cheap" in _pf_lines(st)[0]
    # an executed action clears the streak; the cap is off below PF_CAP_AT
    assert _pf_update(a, {"level": 1, "action_num": 7})["streak"] == 0
    assert _pf_cap_kwargs(_pf_state(a), {"max_tokens": None})[1] is False
    # long streak -> cap, but never over an explicit max_tokens
    for _ in range(PF_CAP_AT):
        _pf_update(a, {"level": 1, "action_num": 7})
    kw, capped = _pf_cap_kwargs(_pf_state(a), {"max_tokens": None})
    assert capped and kw["max_tokens"] == PF_CAP_TOKENS
    assert _pf_cap_kwargs(_pf_state(a), {"max_tokens": 512})[1] is False
    # game_over auto-RESET keeps the level: the ledger persists (RESET advanced action_num)
    assert _pf_update(a, {"level": 1, "action_num": 9})["level_start"] == 4
    # level_completed -> fresh ledger
    st = _pf_update(a, {"level": 2, "action_num": 30})
    assert st["level_start"] == 30 and st["streak"] == 0
    # caution wording once far above the allowance
    for _ in range(PF_NUDGE_AT + 1):   # first call advances the action count, then 3 inspect-only
        st = _pf_update(a, {"level": 2, "action_num": 30 + PF_FREE[2] * 3})
    assert "lowers this level's score" in _pf_lines(st)[0]
    # missing fields are ignored
    assert _pf_update(a, {"stale": True}) is _pf_state(a)
    return "ok"


if PF_ON:
    _state = _pf_install()
    print(f"ARC3_PF_READY {_state} nudge_at={PF_NUDGE_AT} cap_at={PF_CAP_AT} "
          f"cap_tokens={PF_CAP_TOKENS} self_test={_pf_selftest()}", flush=True)
else:
    print("ARC3_PF_READY disabled", flush=True)


# --- Contest-config guard (from lexicon v6, unchanged logic): refuse demo-mode settings on a real rerun.
def arcaid3_check_contest_config(g=None):
    """Guard against accidental demo-mode settings on a real competition rerun."""
    g = g if g is not None else globals()
    if not g.get("TRUE_SUBMISSION") or g.get("bm") is None:
        return "n/a (not TRUE_SUBMISSION)"
    bm = g["bm"]
    if not g.get("USE_PRIORITY_SCHEDULING", True):
        raise RuntimeError("TRUE_SUBMISSION requires USE_PRIORITY_SCHEDULING=True")
    if getattr(bm.solver, "concurrency", None) != 120 or getattr(bm.solver, "max_runtime_s_per_game", None) != 532 * 60:
        raise RuntimeError(
            f"TRUE_SUBMISSION solver config mismatch: concurrency={getattr(bm.solver, 'concurrency', None)}, "
            f"max_runtime_s_per_game={getattr(bm.solver, 'max_runtime_s_per_game', None)}"
        )
    return "ok (concurrency=120, max_runtime_s_per_game=31920)"

print("ARC3_PF_CONTEST_CONFIG", arcaid3_check_contest_config(), flush=True)
