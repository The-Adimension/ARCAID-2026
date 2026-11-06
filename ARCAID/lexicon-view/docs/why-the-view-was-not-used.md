# Why the model never used the lexicon view

Run: `experiments/2026-10-04__arcaid3-lexicon-view-py312__v1__unsubmitted__save-run/` (called "the run" below).
Control: `submissions/2026-09-30__taaf-flashnext-sheetu12b-0922__v1__score-4.17/outputs/` (same base, no view).
All counts below were re-measured from the files. Nothing was run on Kaggle.

## 1. Answer in five bullets

- **The sentence was delivered.** It sat in the system message of every request, unchanged and never trimmed. Delivery did not fail.
- **The harness's own text says the opposite, louder and more often.** Three lines sent with every request say a frame exposes "only" `.ascii`, `.step`, `.level`, `.shape` and `.segmentation`. "Use segmentation as the primary view" appears 3 times up front and again in every user message (median 6 copies per request). Our sentence appears once, 41% of the way into the system prompt.
- **Our sentence gave no trigger and the harness gave no cue.** F13's sentence says *when* to look ("when an action's final board is confusing"). The contact sheet (F19) then shows an animation image and a "Frame sheet:" line whenever an action animates. Every game's first `.frames` use (8 of 8, in both runs) came right after the model reasoned about an animation. Nothing ever prompted `.code`.
- **The model runs on habit.** It starts each game with the same segmentation dump (25 of 25 games). It reads the board image, and it parses `.ascii` with its own helpers (67% of calls). It never calls `dir()` on a frame and never mentions the system prompt.
- **There is no sign of a model-side failure.** Reasoning was almost never cut off (5 of 1,134 replies). The same model does use other lines that appear only in the system prompt (`.shape` in 38 calls, `last_transition.before/after_frame` in 84 calls, `.frames` in 44 calls). Weak instruction-following by a 4-bit MoE model is a hypothesis, not a finding.

## 2. Evidence, per question

### Q1. Did the model receive the sentence on every request?

- **Yes, in the system message.** It is not in the user prompt or the tool description.
- **The same system prompt was used on every turn.** Across 1,115 turns in 25 transcripts, the `[SYSTEM PROMPT]` section has exactly one distinct text. It differs from the control's only by our line (diff of the two runs' system prompts).
- **Where it sits:**
  - Line 41 of 98 lines (87 non-blank).
  - It starts at character 5,380 of 13,198, which is 40.8% of the way in.
  - 731 of 1,967 words come before it.
  - It is the last line of the "Runtime variables" block. It comes right after F13's line and just before "Multimodal context:".
  - In the prompt-log snapshot it is `prompts/ar25-0c556536_p0.log:52`.
- **The surrounding lines, verbatim (ar25 prompt log, lines 50 to 53):**
  ```
  - After `action(actions)` returns, `current_frame`, `previous_frame`, `history`, `transitions`, `valid_actions`, and `last_action_result` are refreshed.
  - Some actions animate: `last_transition.frames` lists the intermediate boards (count in `last_transition.frame_count`); inspect them when an action's final board is confusing.
  - `current_frame.code` describes the board as objects: the true cell size, a legend of symbols (each a small picture with a stable name) and where each symbol sits; `current_frame.changes_since(previous_frame)` lists objects that moved, appeared, disappeared or changed; `current_frame.objects` gives each object's screen row/col for MOUSE.
  Multimodal context:
  ```
- **It is re-sent on every request.** `analyze()` builds `[system, *history, user]` on each turn (`inference/agent/tool_agent.py:1757`). Inside a turn, each tool-loop request keeps `messages[0]`.
- **It is never trimmed.** `_trim_messages_for_context` (tool_agent.py:1672-1688) sets `system_message = messages[0]` aside. It drops only the oldest history blocks. Stored history is `trimmed[1:]` (tool_agent.py:1657-1658), so the system text is not duplicated either.
- **No request-time hook touches it.** The agentfix `_chat_completion` wrappers (timing, F19 sheet stripping) edit user messages only.
- **All 25 prompt-log snapshots show it.** In every `prompts/*.log`, the line is inside the `[SYSTEM]` block (25 of 25).
- **No truncation.** The line is complete (340 characters) in every copy.
- **Where it sits in a typical request.** The median request is 21,079 prompt tokens (p90 23,254, max 26,967), against a trimming budget of 26,112 (kernel log `AGENTFIX_TIMING`; transcript `[ANALYZER STATUS]`). Our line is about 1,300 to 1,700 tokens in (an estimate from character counts). About 19,000 tokens of history and the new user message follow it.

### Q2. What the prompt says about which views to use

Everything below is in every request. In the harness source, the stock lines are in `inference/agent/prompts.py` and `tool_agent.py`. The reference bundle matches what ran: all 84 non-blank lines of the six stock prompt addenda appear verbatim in the run's system prompt.

**Tool description** (sent with every request as the `python` tool schema; tool_agent.py:154-165; prompt log line 11):
- "`current_frame` and each `history[*].frame` expose only `.ascii`, `.segmentation`, `.step`, and `.level`"
- "Use `.segmentation` as the primary view; use `.ascii` only to read a small, specific region."
- "Use `print(...)` for compact output or assign final data to `result`."

**System prompt, stock harness** (line numbers are within the 98-line system prompt):
- Line 15 (prompts.py:40): "`current_frame` exposes only `.ascii`, `.step`, `.level`, `.shape`, and `.segmentation`."
- Line 23 (prompts.py:49): "Use `current_frame.segmentation` as your primary view of the board ... Use `current_frame.ascii` only to read a small, specific region; do not scan the whole board with it."
- Line 27 (prompts.py:54): "each frame exposes only `.ascii`, `.step`, `.level`, `.shape`, and `.segmentation`."
- Line 64 (prompts.py:78): "Use `current_frame.segmentation` as your primary view of the board"
- Line 65 (prompts.py:79): "Use `current_frame.ascii` only to read a small, specific region of the board when `segmentation` is not enough"
- Line 70 (prompts.py:84): "For the most recent change, compare `previous_frame` to `current_frame`, or `last_transition.before_frame` to `last_transition.after_frame`."
- Line 76 (prompts.py:90): "Never print or echo full board frames. Return only compact derived summaries such as object lists, diffs, coordinates, counts, or tiny local crops."
- Line 80 (prompts.py:94): "For frame diffs, summarize changed cells, color transitions, appearing/disappearing components, movement candidates..." This tells the model to build its own diffs.
- Line 97 (prompts.py:112): "Tool responses are capped to about 1024 tokens."
- Multimodal block (lines 44-48): "User turns include an attached image of the current ARC grid."

**System prompt, added by agentfix:** only F13's line 40 (`ANIM_NOTE`, agentfix cell, "Some actions animate: ... inspect them when an action's final board is confusing"). F13b's summary note, F5, F7 and F11 were off in this run (`AGENTFIX LIVE` line in the executed notebook, cell 11 output).

**System prompt, added by us:** line 41 only.

**Per-turn user prompt, stock** (tool_agent.py:1225; prompt log line 111). It is in every user message, so a median of 6 copies sit in each request's history:
- "Keep tool output compact: use `current_frame.segmentation` as the primary view, and `current_frame.ascii` only for a small specific region; never print full boards."
- Also every turn: "Only letter-coded board views and lightweight metadata are exposed" and the `previous_frame` versus `current_frame` comparison hint.
- On the first turn only (tool_agent.py:1236-1238): "Ground yourself in `current_frame` before acting, but start with a compact structural summary rather than restating the full frame."

**Per-turn user prompt, added by agentfix F19:** after an animated action, the first line of the user message reads "Frame sheet: N frames of the last action, panels left-to-right/top-to-bottom = frame 1..N ...". A contact-sheet image comes with it. There were 487 sheet events in this run and 440 in the control (kernel logs).

**Example code given to the model:** none, apart from action-list formats (`['LEFT']`, `[{'action': 'MOUSE', 'row': 4, 'col': 7}]`).

**Tally per request** (latest snapshot of each of the 25 games):
- "primary view": 3 times in the tool description and system prompt, plus 3 to 10 more in the user messages (median 6).
- "only" statements about frame fields: 3.
- `.code`: 1, our line.

### Q3. How the model chooses what to call

**First call on a new game: always a segmentation dump.**
- 25 of 25 games, in both runs, use `.segmentation` and nothing else.
- Real examples:
  - ar25 (`transcripts/ar25-0c556536_p0.txt:147`): `seg=f.segmentation; for n in seg['nodes']: print(n['id'], n['color'], n['pixels'], n['boundary'][:6], ...)`
  - sb26 (`sb26...txt:155`), vc33 (`vc33...txt:148`) and lp85 (`lp85...txt:153`) use near-identical code: `level/step/shape`, then one line per node.
- The thinking before it starts from the image. ar25: "The board appears to be 64x64. There's a blue background..." sb26: "The image shows: top row has 4 colored square outlines..." vc33: "Let me start by inspecting the current frame's segmentation".

**First call on a new level: mostly segmentation.** 34 of 38 new levels used `.segmentation` (26 alone, 8 with `.ascii`), and 4 used `.ascii` only. The control is similar (30 of 36).
- ft09 level 2 (`ft09...txt:1302`): "Let me inspect the segmentation to get exact structure."
- vc33 level 2 (`vc33...txt:2021`): "Let me get segmentation to be precise."
- lp85 level 5 (`lp85...txt:8754`): "Let me just get the segmentation."

**Phrases in thinking** (out of 1,134 THINKING sections):
- "let me ... segmentation": 117
- the image ("the image shows", "from the image", "in the image"): 295
- any mention of "image": 420

**The code is formulaic and hand-built.**
- `ascii.split('\n')`: 759 of 1,135 calls (67%)
- `seg['nodes']` loops: 432 calls (38%)
- The model writes its own before/after diff in 175 calls.
- Its most common helper names are `st`, `norm`, `cells`, `diff` (37 times), `snap`, `crop`.
- Copying from the previous call is partial: median 12% of a call's lines are verbatim from the previous call, and 173 of 1,110 calls copy at least half.

**It never reasons about the prompt's variable list.**
- 0 THINKING sections mention "system prompt", "primary view", "exposes only" or "available globals".
- "the prompt" appears 5 times, always about state lines in the user message ("The prompt says game_over").

### Q4. Why `.frames` was used and `.code` was not

**Usage counts.**
- The run: `.frames` 48 occurrences in 44 of 1,135 calls (3.9%), in 8 games. sb26 has 16 and sp80 13.
- The control: 71 occurrences in 56 of 984 calls (5.7%), in 8 games.
- Our line did not change F13's usage pattern.

**What triggered it.**
- 612 of 2,844 actions animated, and 487 contact sheets were attached (kernel log `AGENTFIX_EVENT`).
- In 34 of 44 calls, the thinking just before the call names an animation, intermediate frames, a flash or the sheet. The control: 52 of 56.
- **Every game's first `.frames` use was cued (8 of 8 in each run).** Example, sb26 (`sb26...txt` thinking at about line 645, call at 659): "The SPACE action triggered an animation... frames 9, 17, 25, 33 show a white/red highlight... Let me look at the full transition frames... last_transition.frames has 42 frames."
- The 10 uncued uses are template reuse inside one game. sb26 lines 1638, 2023, 2624 and 4173 all run `res=action([...])`, then `fr=last_transition.frames`. Once a tool pays off, the model copies it. Our view never got a first use to copy.
- F5's `frames`/`distinct_frames` result fields were off in both runs, so they were not the trigger.

**Wording and placement compared.**

| | F13 (`ANIM_NOTE`) | Ours (`ARCAID3_NOTE`) |
|---|---|---|
| Place | System prompt, line 40 | System prompt, line 41 |
| Says when to use it | Yes: "when an action's final board is confusing" | No |
| Hangs off | `last_transition`, which the prompt already tells the model to use for diffs | `current_frame`, which three lines say exposes "only" five fields |
| Conflicts with other lines | No | Yes: 3 "only" lines and the primary-view line in every user message |
| Per-turn cue | Yes: F19 "Frame sheet:" line and image after each animated action | None |

### Q5. Could the model have found the view another way?

- **`dir()` was never used on a frame.** The run has 0 `dir()` calls. The control has one, `dir(lt)` on `last_transition` (sp80).
- **`print(current_frame)` was never used** (0 calls). The repr shows only `AsciiFrameView(level=, step=, shape=)` (python_tool_sandbox.py, `FrameView.__str__`), so it would not list fields anyway.
- **Error messages did not list fields.** There were 4 AttributeErrors, all on `HistoryEntryView` (`step`, `level`, `ascii`). The sandbox prints `f"{exc.__class__.__name__}: {exc}"` (`_sanitize_exception`), so no "Did you mean" hint appears.
- **`dir(current_frame)` would have shown the view.** Our methods are class members of `FrameView`, and `dir` is in `SAFE_BUILTINS`. But the model never asked.
- **`getattr`/`hasattr` were used 26 times.** All targeted `frames`, `frame_count`, `step`, `action` or `result`.

### Q6. Model-side causes

What the files show:
- **Model:** `Qwen/Qwen3.8-Flash-Next-NVFP4`, served by vLLM. The vLLM log tunes `trtllm::fused_moe` kernels and the config is NVFP4, so it is a mixture-of-experts model quantised to 4 bits (`outputs/vllm-openai-server.log`, `vllm-setup-provenance.json`).
- **Settings** (`outputs/taaf_setup_env.json`): temperature 0.6, top_p 0.95, top_k 20, thinking on, context window 32,768, `MAX_OUTPUT` 0 (server default, so no thinking cap set by the harness), turn yield 60 s.
- **Replies were rarely cut off.** finish_reason was `length` in 5 of 1,134 replies, `tool_calls` in 1,126 and `stop` in 3. Reasoning ran a median of 2,791 characters (p90 9,028).
- **Tool output was never truncated** (0 "cut off" notices).
- **22 requests ended in ReadTimeout.** Requests run close to the budget (median 21k of 26k tokens).
- **Rare use is ruled out.** Zero uses in 1,130 counted calls puts the per-call use rate below about 0.27% (rule of three, 95%). This is not bad luck under sampling at temperature 0.6.

What the files contradict:
- "The model ignores the system prompt." It uses system-prompt-only items: `.shape` in 38 calls, `before_frame`/`after_frame` in 84 and `.frames` in 44.

Hypotheses only (not tested):
- A 4-bit MoE model may weight a single mid-prompt line less than lines repeated near the end.
- Long context may hurt recall of the middle of the system prompt.

### Q7. Ranked causes

See section 3.

## 3. Ranked causes (strongest evidence first)

1. **Outweighed and contradicted by the harness's own lines.** These lines are in every request, verbatim. They say "exposes only" three times and "primary view = segmentation" 3 times plus once per user message. Behaviour matches them exactly: the first call on 25 of 25 games was a segmentation dump.
2. **No trigger and no event cue.** F13 says when to look, and F19 shows a cue each time an action animates. Every first `.frames` use was cued (8 of 8 games, in both runs). Our line had neither.
3. **Habit and substitutes.** The model reads the image (295 to 420 of 1,134 thinking sections). It hand-parses `.ascii` (67% of calls) and writes its own diffs (175 calls), as the prompt asks at line 80. It copies tools that worked. It felt no gap, so it never took a first step to copy.
4. **No discovery path.** It made no `dir()`, `print(frame)` or field-listing errors. This is supporting evidence, not a cause on its own.
5. **Model-side limits (MoE, 4-bit, long context).** Hypothesis only. There is counter-evidence that it follows other system-only lines.

Ruled out: delivery failure, trimming, truncated reasoning, a broken sandbox (`ARCAID3_LEXICON_READY ... self_test: ok`, with the patch applied on top of F13's sandbox edits).

## 4. Correction options

None of these is certain to raise the leaderboard score. The only certain thing is exposure or usage, and a save run's counters can check that.

**Background on per-turn text.** The agentfix notebook's own history (agentfix cell, F19 docstring) says F13 frames in the sandbox moved the leaderboard 3.20 to 3.71. A harness-written text summary of the same frames, sent every turn (F13b), scored 2.57: "Frames yes, narration no."
- These are single draws. Our own draws vary a lot: SD 0.33, range 2.57 to 3.59 (`arcaid3/part1/PART-I-FINDINGS.md`). By coincidence, 2.57 is also one of our own draws (`report-2026-09-27.md:14`).
- So this is weak evidence. It is also the only evidence, and it points against adding harness text to every turn, especially change narration.

**Sizes used for the estimates:**
- Median user prompt: 3,369 characters.
- Median request: 21,079 tokens. Budget: 26,112.
- A `.code` listing: 1,054 to 1,341 characters on three real frames (Part II average 1,215). That is about 300 to 400 tokens.
- A `changes_since` text: 19 to 183 characters, about 5 to 60 tokens.

| Option | Class | Where it hooks | Token cost | Risk | How a save run verifies it |
|---|---|---|---|---|---|
| E1. Put a one-line `changes_since` (board before the last executed sequence versus now) at the top of each new user message, and strip older copies | CERTAIN-EXPOSURE | Wrap `ToolAgent._build_user_prompt` (tool_agent.py:1161), which already receives `current_frame` and `history_entries` with host grids. Run the stdlib lexicon in the kernel. Strip old copies in a `_chat_completion` wrapper, as F19's `_sheet_strip_old` does | About 5-60 tokens per request with one copy. About 30-360 if copies stay in history | This is exactly the narration pattern that drew 2.57. It may anchor the model's judgement of the goal | Grep `prompts/*.log` for the line. Add an injected-line counter. Compare the `AGENTFIX_TIMING` ptok median |
| E2. Put the full `.code` listing in each new user message (newest only) | CERTAIN-EXPOSURE | Same hooks as E1 | About 300-400 tokens per request (+36% of a median user prompt). Without stripping, about 2,000-2,500 tokens (6 copies), which would evict roughly one older turn | Context bloat and history eviction. Longer prefill could mean more ReadTimeouts (22 now). It duplicates the image | As E1, plus the `history_messages` distribution in `[ANALYZER STATUS]` and the ReadTimeout count |
| E3. Append `changes_since` to the tool result of every Python call that ran `action(...)` | CERTAIN-EXPOSURE | Sandbox `action()` wrapper in the patched `_SANDBOX_BOOTSTRAP`, or `ToolAgent._run_python_tool` after `run_sandboxed_python` (tool_agent.py:1547) when `action_results` is non-empty | About 5-60 tokens per acting call (581 of 1,135 calls act) | Uses up part of the 1,024-token tool cap (`_trim_tool_text`, tool_agent.py:1336). It is still narration | Count the appended lines in `[TOOL RESULT]` sections. Check for "cut off" notices |
| L1. Remove the contradiction: add `.code`, `.objects`, `.native` and `.changes_since()` to the three "only" lines | LIKELY-USE (needed but probably not enough) | Replace the strings in `tool_agent._PYTHON_TOOL_DESCRIPTION` (read when each request is built) and in `STRUCTURED_RUNTIME_STATE_ADDENDUM` (prompts.py:40, 54) before `ToolAgent` is built (`_system_prompt` is fixed in `__init__`, tool_agent.py:940) | About +25 tokens per request | Low | `ARCAID3_LEXICON_FINAL calls_using_view` above 0. Grep transcripts for `.code` |
| L2. Reword the per-turn primary-view line, for example: "Start with `print(current_frame.changes_since(previous_frame))`; use `.segmentation` for exact shapes, `.ascii` only for small regions" | LIKELY-USE | Wrap `_build_user_prompt` and replace the exact string at tool_agent.py:1225 (agentfix F11 already carries this string). Also edit prompts.py:78-79 | About +15-25 tokens per user message, about +100-150 per request | It may displace segmentation use that works today | Counters, plus the share of calls with `.segmentation` compared with the control's 412 of 984 |
| L3. Give the line a trigger, F13-style, placed next to "For the most recent change..." (prompts.py:84), for example: "after every action, print `current_frame.changes_since(previous_frame)` before writing your own diff" | LIKELY-USE | String edit to `STRUCTURED_RUNTIME_STATE_ADDENDUM` or `PYTHON_ADDENDUM` before the agent is built | About +30 tokens per request | Low. Each use returns up to about 60 tokens of output | Counters per attribute. The number of hand-built diffs should fall from 175 |
| L4. Change the first-turn line "start with a compact structural summary" to "start with `print(current_frame.code)`" | LIKELY-USE (the first call follows this line in 25 of 25 games) | The `action_num == 0` branch of `_build_user_prompt` (tool_agent.py:1236-1238), via a wrapper | About +10 tokens on the first turn, plus about 300-400 tokens of output once per game | The listing then sits in history until it is trimmed | Count `.code` in the first `[TOOL CALL]` of each game |
| U1. Add a `symbol` key to each `segmentation` node | UNCERTAIN | `FrameView.segmentation` in the patched sandbox | 0 unless printed | The model prints chosen keys only (`id`, `color`, `pixels`, `boundary[:4]`), so it may never see the new key | Grep tool code for `'symbol'` |
| U2. Make `print(current_frame)` show the listing | UNCERTAIN | `FrameView.__str__` in the patched sandbox | 0 unless printed | The model printed a frame 0 times | Grep `[TOOL RESULT]` sections |
| U3. Move or repeat the current line, for example at the end of the system prompt | UNCERTAIN | Prompt string order | About +60 tokens | Relies only on a recency hypothesis. The contradiction stays | Counters |

A sensible order: L1 + L3 + L4 together. This keeps the "data on demand" pattern that matched F13. If counters still show 0 uses, test E3 or E1 in a separate run, knowing they are narration.

## 5. What is not established

- **Causation.** No ablation separates the causes. The ranking is inferred from the prompt text, the model's behaviour and the F13 comparison.
- **Whether using the view would help the score.** The 8.23 versus 7.80 offline difference is not evidence, because the view was never read.
- **Which turns carried a "Frame sheet:" line.** The transcripts do not record that line; only the 25 prompt-log snapshots do. The link between `.frames` and the sheet rests on the model's own thinking (34 of 44 calls, and 8 of 8 first uses).
- **Per-request delivery is shown by code and transcripts.** Prompt logs keep only the last request per game, so it is not shown by 1,134 logged payloads.
- **Where vLLM's chat template places the tool description** relative to the system text is not in the files.
- **Whether the 4-bit MoE model follows single mid-prompt lines weakly** has not been tested.
- **Token figures for lexicon text are estimates** from character counts, not tokenizer counts.
- **The 2.57 narration result is one leaderboard draw** reported in the notebook author's notes. It was not reproduced here.
