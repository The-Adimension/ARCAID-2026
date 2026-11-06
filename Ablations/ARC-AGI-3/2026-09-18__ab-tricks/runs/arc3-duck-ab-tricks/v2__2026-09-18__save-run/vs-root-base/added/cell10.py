run_context = contextlib.nullcontext() if run_as_submission else _tee_to_file(WORKING_DIR / "stdout.log")
with run_context:
    preamble = (BUNDLE_DIR / "preamble.txt").read_text(encoding="utf-8")
    print(preamble)
    print(f"deploy.kaggle: working_dir             = {WORKING_DIR}")
    print(f"deploy.kaggle: run_as_submission       = {run_as_submission}")
    print(f"deploy.kaggle: competition_rerun       = {true_submission}")
    print(f"deploy.kaggle: soft_end_time           = {soft_end}")
    print("---")

    bundled_git_status = BUNDLE_DIR / "git_status.txt"
    if bundled_git_status.is_file():
        (WORKING_DIR / "git_status.txt").write_text(
            bundled_git_status.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    if true_submission:
        # Competition reruns use Kaggle's live gateway instead of the bundled offline games.
        os.environ.setdefault("ARC_API_KEY", "test-key-123")
        os.environ.setdefault("ARC_BASE_URL", "http://gateway:8001/")
        os.environ.setdefault("SCHEME", "http")
        os.environ.setdefault("HOST", "gateway")
        os.environ.setdefault("PORT", "8001")
        os.environ.setdefault("OPERATION_MODE", "competition")
        os.environ.setdefault("ENVIRONMENTS_DIR", "")
        os.environ.setdefault("RECORDINGS_DIR", str(WORKING_DIR / "server_recording"))

        deadline = time.monotonic() + 600.0
        last_error = ""
        while time.monotonic() < deadline:
            try:
                with urlopen("http://gateway:8001/api/games", timeout=10) as response:
                    if response.status < 500:
                        break
            except Exception as exc:
                last_error = repr(exc)
            time.sleep(5)
        else:
            raise RuntimeError(f"Kaggle gateway did not become ready: {last_error}")

        bm.games = _competition_games()
        bm.n_passes = 1
        bm.game_weights = None

    # arc3 item 2c: derive the per-game cap from the time actually left in the kernel, and
    # keep a soft deadline in submission mode so Benchmark.run's teardown always executes.
    import math

    KERNEL_LIMIT_S = float(getattr(target, 'max_runtime_s', 0.0) or 32400.0)
    TEARDOWN_RESERVE_S = 900.0
    _elapsed = time.time() - NOTEBOOK_START_EPOCH
    _remaining = max(600.0, KERNEL_LIMIT_S - _elapsed - TEARDOWN_RESERVE_S)
    _waves = max(1, math.ceil(len(bm.games) * max(1, bm.n_passes) / max(1, int(bm.solver.concurrency))))
    _derived_cap = _remaining / _waves
    if true_submission:
        bm.solver.max_runtime_s_per_game = _derived_cap
        soft_end = datetime.fromtimestamp(NOTEBOOK_START_EPOCH) + timedelta(
            seconds=KERNEL_LIMIT_S - TEARDOWN_RESERVE_S)
    else:
        bm.solver.max_runtime_s_per_game = min(bm.solver.max_runtime_s_per_game, _derived_cap)
    print(f'arc3 budget: kernel={KERNEL_LIMIT_S:.0f}s elapsed={_elapsed:.0f}s remaining={_remaining:.0f}s '
          f'games={len(bm.games)} passes={bm.n_passes} waves={_waves} '
          f'per_game={bm.solver.max_runtime_s_per_game:.0f}s soft_end={soft_end}', flush=True)

    try:
        await bm.run(
            soft_end_time=soft_end,
            runtime_environment=target,
            minimal_diagnostics=run_as_submission,
        )
        if not true_submission and Path("/kaggle/input").exists():
            try:
                import pandas as pd

                submission = pd.DataFrame(
                    data=[["1_0", "1", True, 1]],
                    columns=["row_id", "game_id", "end_of_game", "score"],
                )
                submission.to_parquet(WORKING_DIR / "submission.parquet", index=False)
            except Exception as exc:
                print(f"taaf.kaggle: could not write offline dummy submission: {exc!r}", flush=True)
    finally:
        _run_shell_commands("teardown_commands.json", label="teardown", check=False)
