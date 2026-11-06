# ARC-AGI-3 A/B: Duck harness vs Duck + arc3 tricks

Harness: TAAF/Tufa Labs Duck (CC0 bundle); model Qwen3.8-27B-FP8 (Apache 2.0); wrapper from the public notebook foysalemonshanto/lb-9-arc3-duck-v12-with-qwen-3-8-27b.

**Save run (not scored):** 8 public games x 2 passes. Pass 0 = plain Duck; pass 1 = Duck + two arc3-autoresearch tricks: (1) a no-op guard that ignores timer/step-counter border strips, (2) `nav_moves()` / `nav_path()` sandbox helpers that learn the player sprite and plan arrow paths. Output: `arc3_ab_report.md` / `.json` with levels, actions, score, time, tokens and trick counters per game and arm.

**Competition rerun (scored):** every hidden game plays with the tricks on (ARC3_MODE=on).
