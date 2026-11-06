# Make one-off changes to `bm`, `bm.games`, or `bm.solver` here before the run starts.
bm.solver.max_runtime_s_per_game = 20*60  # ARCAID3 level trials: per (game, level) entry
bm.solver.analyzer_timeout = 900.0
bm.solver.concurrency = 10  # ARCAID3 level trials: one model stream per trial (server runs 10)
bm.solver.max_actions_per_game = None
bm.solver.save_request_logs = True
bm.n_passes = 1
bm.game_weights = None

demo_excluded_games = []  # ARCAID3 level trials: all 25 public games

if TRUE_SUBMISSION:  # overrides for contest run
    bm.solver.save_request_logs = False
    bm.n_passes = 1
    if USE_PRIORITY_SCHEDULING:
        bm.solver.concurrency = 120  # game count should be 110
        bm.solver.max_runtime_s_per_game = 532*60
else:
    if USE_PRIORITY_SCHEDULING:
        bm.solver.concurrency = (25 - len(demo_excluded_games)) * bm.n_passes
        bm.solver.max_runtime_s_per_game = 25*60 #532*60 * bm.solver.concurrency // 110
    if float(getattr(target, 'max_runtime_s', 0.0) or 0.0) != 32400.0:
        raise RuntimeError(
            f'Expected the 32400-second notebook budget, got {target.max_runtime_s!r}.'
        )

# show config
print('benchmark.solver:', bm.solver)
