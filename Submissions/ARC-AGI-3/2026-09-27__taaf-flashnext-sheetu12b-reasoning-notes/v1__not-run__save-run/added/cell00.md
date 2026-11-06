# Sheetu12b Delta

| | Tufa Labs Duck (original, June) | Scott Le Grand's `taaf-flashnext-sheetu12b-0922` v1 (public LB 5.19): the base of this notebook | **This notebook** |
|---|---|---|---|
| AI model | Qwen3.6-27B (older, slower) | Qwen3.8-Flash-Next, compressed to run much faster (NVFP4) | same as the base |
| Games at once / memory | standard | 16 model conversations at once, shorter memory (16K) | same as the base |
| How the AI moves | one or two moves, then thinks again | same as the original | same as the base |
| What the AI sees | a picture of the board | a larger picture (12x), plus the in-between frames when something animates; old board pictures dropped to save memory | same as the base |
| Working notes | notes are wiped when it loses a life; sloppy labels are ignored | notes survive losing a life; looser labels accepted | same as the base |
| **Change A** | none | none | **also keeps the notes the AI writes while thinking silently, not only what it says out loud** (capped at 400 characters each) |

**Note on the base's header below:** "About this fork" says "32K context ... eight vLLM sequences", but the base's own code (cell *1. Environment and submission mode*) sets **16** sequences and a **16K** context. The table above follows the code.

**What was changed:** three cells were added: this one, a note plus the Change A code after the base's agentfix cell, and a counter printout at the end. Every other cell is exactly the base, version 1.

**Credit and licence:** Apache-2.0. Credit to Scott Le Grand, and to Tufa Labs for the Duck harness.

**What to check in the log:**
- `ARC3_WMREASON_READY ... self_test=ok` near the start;
- `ARC3_WMREASON_FINAL` at the end, with `reasoning_applied > 0` and `errors == 0`.

**Status:** Change A has no measured score yet.
