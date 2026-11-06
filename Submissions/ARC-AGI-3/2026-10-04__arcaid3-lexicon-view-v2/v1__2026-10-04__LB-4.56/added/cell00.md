# ARCAID3 lexicon view v2 on Scott Le Grand's sheetu12b (public LB 4.17 for our unchanged copy)

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

**What v2 changes in the prompt, and why.** In version 1 the model never used the view: 0 of 1,130 tool calls.
The harness's own prompt said, three times per request, that a frame exposes "only" `.ascii`, `.step`, `.level`,
`.shape` and `.segmentation`, and our one sentence gave no reason to look
(`arcaid3/part3/WHY-THE-VIEW-WAS-NOT-USED.md`). v2 therefore:
1. adds the new members to those three "only" lines (tool description and two system-prompt lines);
2. adds a "when" line next to the harness's "most recent change" line: on a new level, or when the last action's
   effect is unclear, print `current_frame.code` and `current_frame.changes_since(previous_frame)`;
3. on a game's first turn and after a level change, adds one line to the user message: start with
   `print(current_frame.code)`.

Nothing else changes: same model, serving, images, schedule. Every prompt edit is applied only if its exact anchor
text is found, and the `ARCAID3_LEXICON_READY` line reports which edits applied.

**Why this change and not another.** In this lineage the only change ever reported to move the hidden leaderboard
(F13, 3.20 -> 3.71 in the author's notes) was a perception change of this kind: more of the board, offered in the
sandbox, read only when the model asks. Our own runs lost their score on levels the model never understood, not on
clumsy play (see `arcaid3/part1/PART-I-FINDINGS.md`).

**Honest expectation.** One leaderboard draw cannot show whether this helps: identical code has scored 5.68, 4.09 and
2.30 for another team. Judge it on several draws against several draws of the unchanged base.

**Environment:** Kaggle image `sha256:37c64f7d…fade02bfa8bf3fc647d461` (Python 3.12), set as "Pin to original environment".
keithtyser's vLLM runtime stops on Python 3.13 with `The pinned vLLM runtime requires CPython 3.12`.

**Kill switch:** `ARCAID3_LEXICON=0`. **Log lines:** `ARCAID3_LEXICON_READY` near the start, `ARCAID3_LEXICON_STATS`
every 200 tool calls, `ARCAID3_LEXICON_FINAL` at the end. Success test for this save run: `calls_using_view` above
5% of `tool_calls`.

Credits: Tufa Labs (Duck), keithtyser (Flash-Next serving), Scott Le Grand (sheetu12b, agentfix, F13/F19).
