# v4A: harness context window 32768 -> 24576. Runs after solver setup (which wrote the
# 32768 default into the setup env) and before the benchmark is unpickled, which is the
# first import of the harness modules, so both call-time and import-time reads see it.
ARC3_CTX_WINDOW = 24576
ARC3_CTX_V3_BUDGET = 31744   # v3 prompt logs at a 32768 window (window - 512 reply - 512 margin)
ARC3_CTX_EXPECTED_BUDGET = ARC3_CTX_WINDOW - 1024

_ctx_before = os.environ.get("LOCAL_ANALYZER_CONTEXT_WINDOW")
os.environ["LOCAL_ANALYZER_CONTEXT_WINDOW"] = str(ARC3_CTX_WINDOW)
# Teardown commands and any child process read the setup env file, so write it there too.
_ctx_env = json.loads(SETUP_ENV_PATH.read_text())
_ctx_env["LOCAL_ANALYZER_CONTEXT_WINDOW"] = str(ARC3_CTX_WINDOW)
SETUP_ENV_PATH.write_text(json.dumps(_ctx_env, indent=2, sort_keys=True) + "\n")

_ctx_preloaded = sorted(m for m in sys.modules if m == "inference" or m.startswith("inference."))
print(
    "ARC3_CTX_SET window %s -> %d expected_budget=%d harness_modules_already_imported=%s"
    % (_ctx_before, ARC3_CTX_WINDOW, ARC3_CTX_EXPECTED_BUDGET, _ctx_preloaded or "none"),
    flush=True,
)

# Record where the bundled harness reads the variable (evidence for the evaluation).
try:
    _ctx_hits = []
    for _p in sorted((BUNDLE_DIR / "src").rglob("*.py")):
        _txt = _p.read_text(encoding="utf-8", errors="replace")
        if "LOCAL_ANALYZER_CONTEXT_WINDOW" not in _txt:
            continue
        for _i, _line in enumerate(_txt.splitlines(), 1):
            if "LOCAL_ANALYZER_CONTEXT_WINDOW" in _line:
                _ctx_hits.append("%s:%d: %s" % (_p.relative_to(BUNDLE_DIR), _i, _line.strip()[:160]))
    print("ARC3_CTX_READERS", len(_ctx_hits), flush=True)
    for _h in _ctx_hits[:12]:
        print("  " + _h, flush=True)
except Exception as _ctx_exc:
    print("ARC3_CTX_READERS scan failed: %r" % (_ctx_exc,), flush=True)
