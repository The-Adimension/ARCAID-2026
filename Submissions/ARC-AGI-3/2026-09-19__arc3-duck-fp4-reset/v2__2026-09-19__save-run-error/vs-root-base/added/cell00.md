## Duck + NVFP4 + batching + stall RESET (2 passes)

stallrun2 refuted the warning-only detector: 100 warnings moved the normalised loop metric from 0.234 to 0.219, and its +4 levels were **entirely sb26 going 1 to 7**. Without sb26 that run was net negative (23.33 vs 28.81) despite having 42% more actions. The agent is not failing to notice it is looping -- it cannot get out.

So this run takes the pre-registered branch: a stuck batch is replaced by a single `RESET`, which under `ONLY_RESET_LEVELS` rewinds **this level only** and keeps cleared levels and score. One action, against walls of 83-439. Capped at 2 per level, never fabricated when the game does not offer RESET, and the model's own RESET passes through.

**Two passes at concurrency 6** (2 x 6 = 12 runs, 2 waves of 6) so each run still gets ~1/6 of the GPU for 3600 s and we get 12 observations instead of 6 -- one game will not be able to carry the result this time.

Read the verdict on the **five non-sb26 games** and on actions as well as levels. Two passes narrow sampling noise but do not control run-to-run throughput, which is what made stallrun2 unreadable.

Competition path unchanged.
