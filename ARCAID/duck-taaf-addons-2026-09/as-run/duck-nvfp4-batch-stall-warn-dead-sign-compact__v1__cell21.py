# v5 gate, save runs only: the rewrite must have fired on the harness's own model calls.
if not TRUE_SUBMISSION:
    import arc3_compact as _ac_gate
    _s = dict(_ac_gate.STATS)
    _ok = _s["posts_changed"] > 0 and _s["errors"] <= max(1, _s["posts_seen"] // 100)
    print("ARC3_COMPACT_CHECK ok=%s %s" % (_ok, _s), flush=True)
    if not _ok:
        raise RuntimeError("v5: arc3_compact did not rewrite the model calls; do not submit this version.")
