## Change A: world-model lines from the model's reasoning

This notebook is **our submitted v3 (Duck + NVFP4 + batch + stall warn + dead-sign, public LB 3.59, kernel habanwer/duck-nvfp4-batch-stall-warn-dead-sign v3)** with exactly two added code cells and this markdown cell. Nothing else changed.
- **The added cell:** after every model response, if the visible reply has no world-model labels, the harness's own parser reads the model's reasoning and writes those fields (capped at 400 characters each) into the carried world model.
- **The last cell:** prints the counters.
- **Kill switch:** `WMREASON=0`.

Details and verification: `kaggle/changeA/README.md` in the ARC3 repo.
