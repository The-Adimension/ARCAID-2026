## Duck on the NVFP4 stack + prompt-only action batching (measurement run)

Identical to `arc3-duck-fp4-serving` (submitted as v1) except for **one change: the system prompt**. `consult/arc3_batch.py` rewrites two lines of `PYTHON_ADDENDUM` that pull against batching -- "Optimize for the shortest reliable sequence" and "After **every** action, verify..." -- and adds a predict-then-commit protocol: plan a sequence, predict a board signature per step, execute behind a gate that breaks on the first mismatch.

No harness code, no serving knob, no new mechanism. Duck's sandbox already permits `action(...)` inside loops with state refreshed between calls (`prompts.py:105`), so the whole protocol lives in the model's own code.

**Baseline to beat** (fp4run1, same games, same 900 s cap, same profile): 2.33 actions per charged model decision, 57% singletons, 802 tokens per executed action. Target >= 4.0 and <= 600. The last cell prints `ARC3_BATCH_RESULT` with both.

This notebook is for measurement and is not intended for submission.
