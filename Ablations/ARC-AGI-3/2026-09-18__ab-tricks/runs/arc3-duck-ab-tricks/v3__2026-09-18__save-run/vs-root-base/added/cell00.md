# ARC-AGI-3: Duck harness + arc3 tricks (A/B)

Harness: TAAF/Tufa Labs Duck (CC0 bundle); model Qwen3.8-27B-FP8 (Apache 2.0); wrapper from the public notebook foysalemonshanto/lb-9-arc3-duck-v12-with-qwen-3-8-27b.

**Both arms** get the throughput fixes: bounded analysis turns (`MAX_OUTPUT` 3072, `TOOL_STEPS` 12, both shipped as unlimited), a 32768 served context so vLLM holds ~2x the concurrent sequences, and a per-game budget derived from the time actually left in the 9 h kernel with a deadline that also holds in submission mode.

**Arm under test** (odd passes): a stall RESET after 25 actions with no level change, a guard that skips a turn too short to finish, `UNDO`/ACTION7 made reachable, and a no-op guard signature that ignores timer strips.

**Save run:** 6 public games we never taught x 4 passes = 3 per arm. Output: `arc3_ab_report.md` / `.json`. **Competition rerun:** every hidden game plays with the arm on.
