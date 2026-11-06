# Exact public-25 and competition settings.
# arc3: the rerun keeps their measured 7920 s; a save run is capped so our first
# end-to-end test of this serving stack is affordable.
bm.solver.max_runtime_s_per_game = 7920.0 if TRUE_SUBMISSION else 7920.0
bm.solver.analyzer_timeout = 1800.0
# arc3: the rerun keeps 28; the probe pins 6 so two passes run as two waves of six
# rather than twelve streams splitting one GPU, which would halve the per-game budget.
bm.solver.concurrency = 28 if TRUE_SUBMISSION else 28
bm.solver.max_actions_per_game = None
bm.solver.save_request_logs = False
if float(getattr(target, 'max_runtime_s', 0.0) or 0.0) != 32400.0:
    raise RuntimeError(
        f'Expected the 32400-second notebook budget, got {target.max_runtime_s!r}.'
    )
print(
    f'PUBLIC25_SETTINGS budget_s={bm.solver.max_runtime_s_per_game} '
    f'concurrency={bm.solver.concurrency} analyzer_timeout={bm.solver.analyzer_timeout} '
    f'action_cap={bm.solver.max_actions_per_game} request_logs={bm.solver.save_request_logs}',
    flush=True,
)
