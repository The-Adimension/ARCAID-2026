# ARCAID3 lexicon view on Scott Le Grand's sheetu12b (public LB 4.17 for our unchanged copy)

**What this is.** Scott Le Grand's public notebook `taaf-flashnext-sheetu12b-0922` (Apache-2.0), itself built on
Tufa Labs' Duck harness (CC0) and keithtyser's Flash-Next serving. Every original cell is kept, unchanged and in order.

**The one change.** The model already reads the board through Python (`current_frame.ascii`, `.segmentation`,
and F13's in-between animation frames). This adds one more optional way to read it:

| New in the sandbox | What it gives the model |
|---|---|
| `current_frame.code` | The board as objects: the true cell size (many games draw a 16x16 or 32x32 world scaled up to 64x64), a legend of symbols (small multi-colour pictures with stable names), and where each symbol sits |
| `current_frame.changes_since(previous_frame)` | Which objects moved (and by how much), appeared, disappeared or turned into another symbol |
| `current_frame.objects` | The same objects as data, with a screen row/col to click |
| `current_frame.native` | The board at its true resolution |

One sentence in the system prompt mentions it. Nothing else changes: same model, serving, images, prompts, schedule.

**Why this change and not another.** In this lineage the only change ever reported to move the hidden leaderboard
(F13, 3.20 -> 3.71 in the author's notes) was a perception change of this kind: more of the board, offered in the
sandbox, read only when the model asks. Our own runs lost their score on levels the model never understood, not on
clumsy play (see `arcaid3/part1/PART-I-FINDINGS.md`).

**Honest expectation.** One leaderboard draw cannot show whether this helps: identical code has scored 5.68, 4.09 and
2.30 for another team. Judge it on several draws against several draws of the unchanged base.

**Kill switch:** `ARCAID3_LEXICON=0`. **Log lines:** `ARCAID3_LEXICON_READY` near the start, `ARCAID3_LEXICON_STATS`
every 200 tool calls, `ARCAID3_LEXICON_FINAL` at the end.

Credits: Tufa Labs (Duck), keithtyser (Flash-Next serving), Scott Le Grand (sheetu12b, agentfix, F13/F19).
