# Acknowledgements

Every submission in this repository is built on public work by others. This page credits them in short. Full citations, with versions, links and the licence each page shows, are in [`Documentation/REFERENCES.md`](Documentation/REFERENCES.md). How each of our notebooks descends from theirs is in [`ARCAID/LINEAGE.md`](ARCAID/LINEAGE.md).

## Agents and notebooks we built on

| Who | What we used | Where it appears here |
|---|---|---|
| **Tufa Labs** (Jeroen Cottaar and team) | The **Duck** harness: an LLM agent that plays through a Python sandbox. Milestone 1 winner. | Underneath every ARC-AGI-3 submission from 2026-09-16 on, and the model for the ARC-AGI-2 agent |
| **Daniel Franzen** (`dfranzen`) | The **ARC-AGI-3 Milestone 2 Solution** notebook, version 1, with its SGLang serving build, TAAF source bundle and quantised Qwen3.8-Flash-Next model and drafter | The base of every ARC-AGI-3 submission from 2026-10-05 on, including both selected submissions. Every one of his cells is kept unchanged. |
| **Scott Le Grand** (`scottlegrand`) | `taaf-flashnext-sheetu12b-0922`, a Duck fork with Flash-Next serving and repairs | The base of our late-September submissions (3.90, 4.17) and of the first lexicon-view notebooks |
| **keithtyser** | The Flash-Next NVFP4 port of Duck, its vLLM runtime datasets and model, and the Duck Qwen3.8 serving dataset | The base of our September FP4/NVFP4 line; the serving wheels of the ARC-AGI-2 agent |
| **caoyupeng** | `arc3-duck-v12`, the notebook FOYSAL's is forked from | Upstream of our first Duck submission |
| **FOYSAL** (`foysalemonshanto`) | `LB-9 arc3 duck v12 with Qwen 3.8 27B`, and the repacked Qwen3.8-27B FP8 model | Our first Duck submission was a copy of the notebook (1.37). The model plays our ARC-AGI-2 entry. |
| **madarshbb** | `ARC Qwen 3.8 27B agent`: a REPL program-synthesis agent for ARC-AGI-2 | The base of our ARC-AGI-2 entry |
| **Intel; Albucino; John Pezzulli; Mamy Ratsimbazafy; Gabriel Olympie** | The quantised model and draft checkpoint, and the Pennyroyal SGLang fork and its patches, credited in Franzen's notebook | Serving and models of every notebook built on Franzen's |
| **mirzamilanfarabi** | The `arc3-vllm-h100-wheelhouse-v3` dataset | Installs vLLM in the ARC-AGI-2 entry |
| **amatlas** and **shiiin9** | The D′ scheduling cell (shiiin9's formula, via amatlas's fork of Franzen's notebook) | Our D′ variants |
| **heliosli** | The idea for the empty-animation fix | Our D′ variant |

## Measurements and discussions we relied on

- **Son Pham** (`sonphamorg`): the run-to-run variance of copies of Franzen's notebook (discussion 745062). Our noise reference.
- **Tong Hui Kang** (`huikang`): the comparison of the Milestone 2 solutions (discussion 744792).
- **Kaggle staff and competitors** in discussion 751598: the diagnosis of slow model loads in late October, which led to our startup guard.
- **Mintu Kumar**: the question about object identity when same-colour sprites touch (discussion 746295). Answering it surfaced two later fixes: the per-level scale lock (lexicon v2) and cutting merged objects back apart (lexicon v4).

## Organisers, models and tools

- **ARC Prize Foundation and Kaggle:** ARC-AGI-3, ARC-AGI-2, the competitions, the open-source toolkit (`arc-agi`, `arcengine`) and the Paper Track.
- **The Qwen team:** the Qwen3.8 models. **Intel AutoRound:** the W4A16 quantisation used in Franzen's model.
- **ARA Labs:** the public hypothesis ledgers (CC-BY-4.0) used in our September hypothesis test.
- **Andrej Karpathy:** `autoresearch`, the loop design behind our first starter agent.
- **Anthropic:** Claude Code. Its use is described in [`DISCLAIMERS.md`](DISCLAIMERS.md).
