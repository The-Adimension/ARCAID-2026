def _soft_end_time(max_runtime_s: float, *, run_as_submission: bool) -> datetime | None:
    # arc3: upstream returns None in submission mode, so nothing ever cancels the
    # benchmark and a hard kernel kill would skip teardown entirely.
    if max_runtime_s <= 0:
        return None
    budget = max(1.0, max_runtime_s)
    buffer = min(SOFT_DEADLINE_BUFFER_S, budget / 2)
    start = datetime.fromtimestamp(NOTEBOOK_START_EPOCH)
    return start + timedelta(seconds=budget - buffer)


def _competition_games():
    import arc_agi

    import taaf.game_api

    spec = taaf.game_api.ArcadeSpec(
        operation_mode=arc_agi.OperationMode.COMPETITION,
        arc_base_url=os.environ.get("ARC_BASE_URL", "http://gateway:8001/"),
        environments_dir="",
    )
    arcade = arc_agi.Arcade(
        operation_mode=arc_agi.OperationMode.COMPETITION,
        arc_base_url=spec.arc_base_url,
        environments_dir="",
    )
    game_ids = [env_info.game_id for env_info in arcade.available_environments]
    if not game_ids:
        raise RuntimeError("Competition Arcade exposed zero environments.")
    return [taaf.game_api.GameAPI(env_name=game_id, arcade_spec=spec) for game_id in game_ids]


@contextlib.contextmanager
def _tee_to_file(log_path: Path):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = open(log_path, "w", buffering=1)
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = _Tee(original_stdout, log_file)
    sys.stderr = _Tee(original_stderr, log_file)
    try:
        yield
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        log_file.close()


class _Tee:
    def __init__(self, *streams: TextIO) -> None:
        self._streams = streams

    def write(self, data: str) -> int:
        n = 0
        for stream in self._streams:
            n = stream.write(data)
        return n

    def flush(self) -> None:
        for stream in self._streams:
            stream.flush()

    def isatty(self) -> bool:
        return any(getattr(stream, "isatty", lambda: False)() for stream in self._streams)
