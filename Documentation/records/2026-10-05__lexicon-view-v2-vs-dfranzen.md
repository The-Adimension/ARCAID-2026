# Pending submission `arcaid3-lexicon-view-v2` vs the dfranzen base, 2026-10-05

Read 2026-10-05 about 11:00 UTC through the Kaggle API (submission list, kernel pull, kernel output). The kernel has one version, so the pulled source is the submitted source.

## Status

- **Submission:** `56845541`, from `habanwer/arcaid3-lexicon-view-v2`, scriptVersionId `355230214`.
  - Submitted 2026-10-05 07:05 UTC.
  - Status `pending` at about 11:00 UTC.
  - A scored rerun can take up to 9 h, plus queue time.
- **Previous attempt:** `arcaid3-lexicon-view` v1, submission `56806237` (10-03), ended in `error`.
  - The scored-run log is hidden, so the cause can't be confirmed.
  - The v2 notebook pins the Python 3.12 image and says keithtyser's vLLM runtime stops on Python 3.13. That is the likely cause; it is unverified.

## What the notebook is

- **Base:** our unchanged copy of `scottlegrand/taaf-flashnext-sheetu12b-0922` (our LB draw 4.17).
  - All 19 original cells are byte-identical.
  - 3 cells are added: the lexicon view (39K characters), its markdown, and a final counter.
- **It is not built on dfranzen.** It inherits the old serving stack whole.

## Delta against dfranzen

| | lexicon-view-v2 (pending) | dfranzen M2 |
|---|---|---|
| Server / quant | keithtyser vLLM, NVFP4 | SGLang Pennyroyal 2.5.3 + 5 patches, W4A16 AutoRound |
| Speculative decoding | 3-token MTP | 3-token MTP + FR-Spec |
| Prefix caching | **off** (0 cache queries in the save run) | **on**, 94.2% of prompt tokens reused |
| KV cache | **BF16, 5 GiB** | **FP8, about 1.01M tokens** |
| Harness context | **16,384** | **131,072**, trim 118K→59K |
| Prompt size (save run) | median 21.1K, p90 23.3K | median 66.7K, p90 103.5K |
| Prompt tokens prefilled per generated token | 11.9 (21.70M / 1.83M) | 2.1 (uncached only) |
| Aggregate generated tok/s | 254 | 616 |
| vLLM preemptions (save run) | 149 | none by design (admission capped to cache) |
| Scheduling | 28 games at once, fixed 7,920 s each | 110 live, 10 streams, priority gate |
| Board images | upscale 12, newest 2 kept | upscale 10, diff and game-over images |
| Animation | F13 frames, F19 contact sheet | frames as REPL variables, timeline |
| UNDO | prompt mention only (AGENTFIX_ACTION7 = 0) | executable as `UNDO` |
| Extra perception | **lexicon view**: `.code`, `.objects`, `.native`, `.changes_since` | `frame_diff()` |
| Code retention | none | functions kept for the whole game |
| Guards | none | batch no-op, stale-state, terminal |
| Temperature | 0.6 | 0.7 |

- **The four rows that explain the field's jump all sit on the old side here:** prefix caching, KV dtype, context and admission (`report-2026-10-05.md`, section 4A).
- **The lexicon view is a perception change.** Perception changes are in tier B or C: no hidden-board change of this kind has cleared noise.

## Save run (public 25 games, 2 h, same settings as our sheetu run)

| | lexicon-view-v2 (10-04) | sheetu unchanged (09-30) |
|---|---|---|
| Mean score | 6.83 | 7.80 |
| Levels cleared | 37 | 36 |
| Generated tokens | 1.83M | 1.85M |
| View used | 247 of 1,111 tool calls (22%); `changes_since` 104, `code` 84, `native` 70 | — |

- **v2 fixed v1's non-use:** v1 had 0 of 1,130 calls using the view. The notebook's own success bar of 5% is met.
- **Score: no measurable change.**
  - Per-game swings dwarf the gap: ar25 2.78 vs 27.78, ft09 10.13 vs 47.62, sb26 21.41 vs 2.78, re86 27.78 vs 8.33.
  - Public-set scores don't predict the hidden board (report, section 3).
- **One risk specific to this stack:** at a 16K window, view output printed into tool results displaces history. rellik13 measured text additions at a capped context as negative (−35%, −26%).

## Expected result

- **Old-base family on the hidden board:** sheetu draws are 4.17 (ours), 5.19 (author) and 6.09 (best shown). Identical code scored 5.68, 4.09 and 2.30 for another team.
  - Expected draw: about 3–6.
  - Even a +30% lexicon effect lands at about 4–8.
- **dfranzen copies:** 25.8 ± 2.9.
- **Expected delta against dfranzen:** about −20 points (−75% to −85%). Nothing the lexicon view can do closes that gap on this serving stack.
- **The result can't settle whether the view helps.** A single draw against a sheetu baseline with a coefficient of variation of about 0.11–0.15 needs a gap of about 30–40%.

## If the view is worth keeping

- Port it onto the dfranzen notebook unchanged. It is one sandbox-attribute cell plus prompt anchors.
- Judge it at matched tokens on mechanics (turns per game, levels per million tokens), not on one LB draw. With a 128K context, the displacement risk above largely goes away.
- Check that dfranzen's prompt anchors exist before porting. Its patched `prompts.py` and `tool_agent.py` differ from the keithtyser bundle the v2 anchors were written against.
