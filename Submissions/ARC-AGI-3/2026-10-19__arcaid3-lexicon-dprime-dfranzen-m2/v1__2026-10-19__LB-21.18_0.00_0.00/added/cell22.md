## ARCAID3 variant: D' slot priority + animation-schema fix

Two additions on top of the lexicon view, for an A/B against the same notebook without them:

1. **Animation-schema fix** (next cell). After an action that returned a single frame, the harness's `last_animation_timeline` was `{"error": ...}` only, while its prompt documents `action`, `frames` and `steps`, so model code reading `["steps"]` raised `KeyError`. The cell wraps `build_animation_view` so that result also carries `frames=0, steps=[]`. Kill switch: `ARCAID3_ANIMATION_FIX=0`.
2. **D' slot priority** (the cell after it, verbatim from [amatlas/dfranzen-fork-d-prime](https://www.kaggle.com/code/amatlas/dfranzen-fork-d-prime), ported from [shiiin9's notebook](https://www.kaggle.com/code/shiiin9/affectify-arc-31-54-in-a-single-sub)). It replaces the priority Franzen's scheduler uses to give the 10 LLM slots to games: `priority = A·M·C + B·φ` (depth and action efficiency, pace, patience, room to grow, tail fade 0.4), and prices unstarted games by the same formula. Its authors report one submission (31.54) and a simulated gain of about +1.5; neither is a measured gain on this notebook.

Both run before `bm.run`. The lexicon cell, D' and the fix were installed together against Franzen's patched harness offline, in both orders (variants/dprime/README.md).
