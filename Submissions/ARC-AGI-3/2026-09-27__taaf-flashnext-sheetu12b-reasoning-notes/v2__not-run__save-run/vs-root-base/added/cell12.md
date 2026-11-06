## Change A: world-model lines from the model's reasoning

This notebook is **scottlegrand/taaf-flashnext-sheetu12b-0922 version 1 (public LB 5.19, Apache-2.0 licence, all credit to Scott Le Grand and to Tufa Labs for the Duck harness)** with four added cells: the plain-language head cell, this note, the Change A code cell below, and a counter cell at the end. Nothing else changed.
- **The added cell:** after every model response, if the visible reply has no world-model labels, the harness's own parser reads the model's reasoning and writes those fields (capped at 400 characters each) into the carried world model.
- **The last cell:** prints the counters.
- **Kill switch:** `WMREASON=0`.

Details and verification: `kaggle/changeA/README.md` in the ARC3 repo.
