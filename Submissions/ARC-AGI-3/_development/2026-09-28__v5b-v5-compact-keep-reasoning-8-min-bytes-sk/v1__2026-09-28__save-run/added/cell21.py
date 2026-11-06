# v5 gate, save runs only: the rewrite must have fired on the harness's own model calls.
if not TRUE_SUBMISSION:
    import arc3_compact as _ac_gate
    _s = dict(_ac_gate.STATS)
    _ok = (
        _s.get("posts_changed", 0) > 0
        and _s.get("errors", 0) <= max(1, _s.get("posts_seen", 0) // 100)
        and int(getattr(_ac_gate, "KEEP_REASONING", 0) or 0) >= 8
    )
    print("ARC3_COMPACT_CHECK ok=%s keep=%s min_bytes=%s %s" % (
        _ok, getattr(_ac_gate, "KEEP_REASONING", None),
        getattr(_ac_gate, "MIN_COMPACT_BYTES", None), _s), flush=True)
    if not _ok:
        raise RuntimeError("v5b: compact hook missing, KEEP_REASONING<8, or rewrite never fired; do not submit.")
