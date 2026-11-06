# Inline customization hook — Q38 P1-style public evaluation.
#
# Q38 P1 runs the full 25 public ARC-AGI-3 games once each (25 games × 1 pass).
# This override applies only to the public/offline notebook run. Competition reruns
# still replace bm.games from Kaggle's live gateway in the final run cell.

print("Benchmark analyzer model:", os.environ.get("INFERENCE_ANALYZER_MODEL"))
print("Qwen3.8 model path:", os.environ.get("TAAF_QWEN_MODEL_PATH"))

Q38_P1_PUBLIC_GAME_IDS = [
    "ft09-0d8bbf25",
    "sb26-7fbdac44",
    "s5i5-18d95033",
    "re86-8af5384d",
    "m0r0-492f87ba",
    "cn04-2fe56bfb",
]

if not true_submission:
    if len(Q38_P1_PUBLIC_GAME_IDS) < 1 or len(set(Q38_P1_PUBLIC_GAME_IDS)) != len(Q38_P1_PUBLIC_GAME_IDS):
        raise RuntimeError("Public smoke game list must contain unique games.")
    if not bm.games:
        raise RuntimeError("benchmark_initial.pkl contains no template public game.")

    import taaf.game_api

    template_game = bm.games[0]
    arcade_spec = getattr(template_game, "arcade_spec", None)
    if arcade_spec is None:
        arcade_spec = getattr(template_game, "_arcade_spec", None)
    if arcade_spec is None:
        raise RuntimeError(
            "Could not recover the public ArcadeSpec from benchmark_initial.pkl; "
            "cannot construct the 25-game Q38 P1 evaluation set."
        )

    bm.games = [
        taaf.game_api.GameAPI(env_name=game_id, arcade_spec=arcade_spec)
        for game_id in Q38_P1_PUBLIC_GAME_IDS
    ]
    bm.n_passes = 6
    bm.game_weights = None

    # These already match Q38 P1 in the source notebook; set them explicitly so the
    # intended evaluation configuration is visible and stable.
    if hasattr(bm.solver, "concurrency"):
        bm.solver.concurrency = 18
    if hasattr(bm.solver, "max_runtime_s_per_game"):
        bm.solver.max_runtime_s_per_game = 1800.0

    bm.label = f"{bm.label}-arc3-ab-6g"
    print(f"Public evaluation override: {len(bm.games)} games × {bm.n_passes} pass = {len(bm.games) * bm.n_passes} runs")
    print("Public evaluation concurrency:", getattr(bm.solver, "concurrency", None))
    print("Public per-game runtime cap (s):", getattr(bm.solver, "max_runtime_s_per_game", None))
