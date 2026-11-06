# Probe-first governor: final counters for this run (never raises).
try:
    print('ARC3_PF_FINAL', PF_STATS, flush=True)
except Exception as _e:
    print('ARC3_PF_FINAL unavailable', repr(_e), flush=True)
