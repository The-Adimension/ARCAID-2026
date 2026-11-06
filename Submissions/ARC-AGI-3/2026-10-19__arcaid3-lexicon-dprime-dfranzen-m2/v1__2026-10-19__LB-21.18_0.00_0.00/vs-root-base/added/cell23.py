# ---------------------------------------------------------------------------
# ARCAID3 fix: the empty animation timeline keeps its documented schema.
#
# Franzen's prompt (prompts.ANIMATION_ADDENDUM_TIMELINE) tells the model that `last_animation_timeline`
# "is a dict with `action`, `frames` and `steps`". After an action that returned a single frame, his
# build_animation_view() returns only {"error": ...}, so model code that reads timeline["steps"] raises
# KeyError and loses the whole snippet. This cell wraps build_animation_view so that result also carries
# action / frames=0 / steps=[], keeping the error text. Results with an animation are returned unchanged.
# Same fix as heliosli's "V5" notebook, applied at runtime instead of by editing the source bundle.
#
# Kill switch: set ARCAID3_ANIMATION_FIX=0 before this cell runs.
# ---------------------------------------------------------------------------
import os as _a3f_os

import inference.agent.tool_agent as _a3f_ta
import inference.utils.animation as _a3f_anim


def _arcaid3_install_animation_fix():
    if _a3f_os.environ.get("ARCAID3_ANIMATION_FIX", "1").strip() in ("0", "", "false", "False"):
        return "off (ARCAID3_ANIMATION_FIX=0)"
    original = _a3f_anim.build_animation_view
    if getattr(original, "_arcaid3_fix", False):
        return "already installed"
    if getattr(_a3f_ta, "build_animation_view", None) is not original:
        raise RuntimeError("tool_agent.build_animation_view is not inference.utils.animation.build_animation_view: "
                           "the harness changed, so this fix no longer applies as written")

    def build_animation_view(record):
        view = original(record)
        if isinstance(view, dict) and "error" in view and "steps" not in view:
            view = {"action": record.get("action_display") if isinstance(record, dict) else None,
                    "frames": 0, "steps": [], **view}
        return view

    build_animation_view._arcaid3_fix = True
    build_animation_view.__wrapped__ = original
    _a3f_anim.build_animation_view = build_animation_view
    _a3f_ta.build_animation_view = build_animation_view   # tool_agent calls it through this global

    probe = _a3f_ta.build_animation_view(None)
    if not (probe.get("steps") == [] and probe.get("frames") == 0 and "error" in probe):
        raise RuntimeError(f"animation fix self-test failed: {probe!r}")
    return "installed, self-test ok"


ARCAID3_ANIMATION_FIX_STATUS = _arcaid3_install_animation_fix()
print("ARCAID3_ANIMATION_FIX", ARCAID3_ANIMATION_FIX_STATUS, flush=True)
