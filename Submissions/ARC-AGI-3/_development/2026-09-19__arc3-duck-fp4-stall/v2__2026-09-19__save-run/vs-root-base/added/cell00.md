## Duck + NVFP4 + batching + stall detection (controlled vs depthrun1)

Same 6 games, same 3600 s cap, same serving profile, same `arc3_batch` prompt as the depth probe. The only new thing is `consult/arc3_stall.py`.

**Why.** In the depth probe every game cleared its levels at or better than human pace, then hit one level and ground on it forever -- vc33 clicked the same cell **122 times out of 439**. Duck's no-op guard cannot see this: it only blocks actions that leave the board unchanged, and a looping action usually does change the board.

**What this run decides.** After being told it is looping, does the agent break out (it never noticed) or keep grinding (the board is unrecoverable and the next version must RESET the level)? Read `wall_uniq_frac` and `top_repeat` against depthrun1.

Pre-flight `abtest/test_stall.py` replays the real depthrun1 histories: fires on 5 of the 6 real walls, **zero** false positives during play that went on to clear, 36-377 actions of wall left after the warning.

Competition path unchanged. Also fixes the 25-game audit assertion that ended depthrun1 in ERROR after all six games had already played.
