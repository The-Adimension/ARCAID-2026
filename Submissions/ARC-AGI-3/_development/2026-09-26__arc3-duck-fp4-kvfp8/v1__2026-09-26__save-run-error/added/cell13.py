# Exact public-25 and competition settings.
# arc3: 110 games at concurrency 28 run as 4 waves. At 7920 s that is 31680 s, about 600 s
# more than is left after setup (~725 s) and the 600 s soft-end reserve, so the last wave
# (~26 games) was cut short. 4 x 7750 = 31000 s fits. The run cell re-fits this to the real
# time left just before bm.run. A save run stays capped at 3600 s.
bm.solver.max_runtime_s_per_game = 7750.0 if TRUE_SUBMISSION else 1800.0
bm.solver.analyzer_timeout = 900.0
# arc3: the rerun keeps 28; the probe pins 6 so two passes run as two waves of six
# rather than twelve streams splitting one GPU, which would halve the per-game budget.
bm.solver.concurrency = 28  # v5: the probe uses the rerun's contention too
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
