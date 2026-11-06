# Make one-off changes to `bm`, `bm.games`, or `bm.solver` here before the run starts.
bm.solver.max_runtime_s_per_game = 48*60 #7920.0
bm.solver.analyzer_timeout = 900.0
bm.solver.concurrency = 10
bm.solver.max_actions_per_game = None
bm.solver.save_request_logs = True
bm.n_passes = 1
bm.game_weights = None

demo_excluded_games = []  # ARCAID3 leaderboard-like save run: all 25 public games at once

if TRUE_SUBMISSION:  # overrides for contest run
    bm.solver.save_request_logs = False
    bm.n_passes = 1
    if USE_PRIORITY_SCHEDULING:
        bm.solver.concurrency = 120  # game count should be 110
        bm.solver.max_runtime_s_per_game = 532*60
    # ARCAID3: fail loudly rather than score a mis-set configuration (cf. 7.16 on 2026-10-11)
    assert USE_PRIORITY_SCHEDULING, 'submission build must run the priority scheduler'
    assert bm.solver.concurrency == 120 and bm.solver.max_runtime_s_per_game == 532*60, (bm.solver.concurrency, bm.solver.max_runtime_s_per_game)
    assert os.environ.get('ARC3_MAX_ACTIVE_STREAMS') == '10', os.environ.get('ARC3_MAX_ACTIVE_STREAMS')
else:
    if USE_PRIORITY_SCHEDULING:
        bm.solver.concurrency = (25 - len(demo_excluded_games)) * bm.n_passes
        bm.solver.max_runtime_s_per_game = 532*60 * bm.solver.concurrency // 110  # ARCAID3: the leaderboard's GPU share per game
    if float(getattr(target, 'max_runtime_s', 0.0) or 0.0) != 32400.0:
        raise RuntimeError(
            f'Expected the 32400-second notebook budget, got {target.max_runtime_s!r}.'
        )

# show config
print('benchmark.solver:', bm.solver)
