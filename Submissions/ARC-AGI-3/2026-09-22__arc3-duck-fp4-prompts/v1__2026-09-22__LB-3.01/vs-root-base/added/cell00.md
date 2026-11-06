## Duck + NVFP4 + batching + stuck warning + hypothesis ledger

Competition path = the 3.37 configuration (batching + `arc3_stall` in warn mode) plus one prompt rule from `consult/arc3_ledger.py`: when an attempt fails, keep CONFIRMED facts, blame the ASSUMED part, try its alternatives. Evidence: `consult/walls_2026-09-21.md` -- on sb26 L2 a 3-turn solve and a 153-action failure shared the same correct model of the controls and differed in one reading of the goal; the loser re-investigated confirmed facts for 57 turns.

**Save run is only for submittability:** 1 game (sb26), 1200 s. It also reports whether the model writes the ledger. It is not an effect measurement.
