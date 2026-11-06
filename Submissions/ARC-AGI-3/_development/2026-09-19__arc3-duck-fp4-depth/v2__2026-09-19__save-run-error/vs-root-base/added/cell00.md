## Duck + NVFP4 + prompt-only batching, with a level-2 depth probe as the save run

Submission 56342262 (FP4, no batching) scored **2.49**. Clearing level 1 on every game is worth only ~3.0, so breadth is nearly spent and the open question is what happens at **level 2**. A 25-game x 900 s save run cannot answer it -- 11-13 actions per game never gets there.

**Save run:** 6 games that reliably clear level 1, at 3600 s each (~240 actions per game), so the agent actually reaches level 2 and we can see whether it is **starved** (spent well under the human baseline on the level it failed) or **stuck** (spent well over). Those call for opposite next moves.

**Competition path: unchanged** -- live gateway games, 7920 s per game, concurrency 28. This version is submittable as-is, carrying the prompt-only batching change measured in batchrun1 (actions per decision 2.33 -> 3.14, singletons 57% -> 35%, tokens per action 802 -> 619, tokens per decision flat).
