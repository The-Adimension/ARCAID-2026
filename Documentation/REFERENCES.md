# References

This page cites every external work this repository uses or builds on. Short credits are in [`../ACKNOWLEDGEMENTS.md`](../ACKNOWLEDGEMENTS.md). Which of our notebooks descends from which is in [`../ARCAID/LINEAGE.md`](../ARCAID/LINEAGE.md).

**How the entries were checked:**
- Versions, titles, inputs and licence fields were read from the Kaggle API on 2026-11-06, unless stated otherwise.
- Kaggle's API does not expose a notebook's licence. Public Kaggle notebooks display "released under the Apache 2.0 open source license" on their page by default, but each notebook below is marked **to verify on page** until someone has opened the page and checked. `Documentation/RELEASE-CHECKS.md` tracks this.
- "Version used" is the version our code was built from, where that can be shown. Otherwise it says what is known.

**Tags:**
- **[R1]** = forked or copied into our notebooks;
- **[R2]** = input data, model or software installed by our notebooks;
- **[R3]** = idea, measurement or rule we relied on;
- **[R4]** = consulted only.

## 1. Competitions, benchmarks and official sources

| # | Reference | Use |
|---|---|---|
| C1 | ARC Prize Foundation. *ARC Prize 2026 – ARC-AGI-3* (Kaggle competition). https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3 | [R2] Track of 43 of our submissions |
| C2 | ARC Prize Foundation. *ARC Prize 2026 – ARC-AGI-2* (Kaggle competition). https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-2 | [R2] Track of 4 of our submissions |
| C3 | ARC Prize Foundation. *ARC Prize 2026 – Paper Track* (Kaggle competition). https://www.kaggle.com/competitions/arc-prize-2026-paper-track | Target of the writeup |
| C4 | ARC Prize Foundation. *ARC-AGI-3: A New Challenge for Frontier Agentic Intelligence.* Technical report, arXiv:2603.24621 (v1 2026-03-24, v2 2026-04-17). https://arxiv.org/abs/2603.24621 | [R3] Benchmark definition |
| C5 | ARC Prize Foundation. *ARC-AGI-3 scoring methodology.* https://docs.arcprize.org/methodology | [R3] The RHAE score used in our analyses |
| C6 | ARC Prize Foundation. *ARC Prize 2026* and *Paper Prize* pages. https://arcprize.org/competitions/2026 , https://arcprize.org/competitions/2026/paper | [R3] Rules, open-source requirement, rubric |
| C7 | ARC Prize Foundation. `arc-agi` 0.9.8 and `arcengine` 0.9.3 (PyPI; https://github.com/arcprize/arc-agi , https://github.com/arcprize/arcengine) | [R2] Engine pinned by the competition, used by our replay and evaluation tools |
| C8 | ARC Prize Foundation. *ARC-AGI-3-Agents.* https://github.com/arcprize/arc-agi-3-agents | [R4] |

## 2. Framework

| # | Reference | Use |
|---|---|---|
| F1 | Anwer S. *The Adimension: bridging human ingenuity and machine intelligence through the DEITY principles framework.* European Heart Journal – Imaging Methods and Practice 2026; 4(1): qyaf038. https://doi.org/10.1093/ehjimp/qyaf038 | The organising framework of this repository |

## 3. Notebooks by others (Kaggle)

| # | Notebook | Author | Version used | Licence | Use |
|---|---|---|---|---|---|
| N1 | *ARC-AGI-3 Milestone 2 Solution.* https://www.kaggle.com/code/dfranzen/arc-agi-3-milestone-2-solution | Daniel Franzen (`dfranzen`) | **Version 1**, scriptVersionId 354090904. Our notebooks keep its 23 cells byte-identical (checked by `Tools/lineage/notebook_diff.py`). Current: v3. | To verify on page | [R1] Base of every ARC-AGI-3 submission from 2026-10-05, including both selected ones |
| N2 | *Tufa Labs duck harness [June 30 milestone winner].* https://www.kaggle.com/code/jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner | Jeroen Cottaar, Tufa Labs | Reached us through N1 (dataset D2), N3 and N4. The exact upstream version is not recorded. Current: v6. | To verify on page | [R1] The Duck harness underneath every Duck-based submission |
| N3 | *taaf-flashnext-sheetu12b-0922.* https://www.kaggle.com/code/scottlegrand/taaf-flashnext-sheetu12b-0922 | Scott Le Grand | Version 1 (the only version) | To verify on page | [R1] Copied unchanged for our 4.17 submission; base of 3.90 and of the first lexicon-view notebooks |
| N4 | *Duck Qwen3.8 Flash Next NVFP4 MTP.* https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp | keithtyser | Version not recorded. Current: v14. | To verify on page | [R1] Base of our September FP4/NVFP4 line |
| N5 | *LB-9 arc3 duck v12 with Qwen 3.8 27B.* https://www.kaggle.com/code/foysalemonshanto/lb-9-arc3-duck-v12-with-qwen-3-8-27b | FOYSAL (`foysalemonshanto`) | Copied 2026-09-16; version not recorded. Current: v6. | To verify on page | [R1] Copied for `arc3-duck-qwen38-baseline` (1.37) |
| N6 | *ARC Qwen 3.8 27B agent.* https://www.kaggle.com/code/madarshbb/arc-qwen-3-8-27b-agent | madarshbb | Forked around 2026-10-31. Our diff is against the current v2 (pulled 2026-11-06). | To verify on page | [R1] Base of our ARC-AGI-2 entry |
| N7 | *dfranzen fork + D-prime.* https://www.kaggle.com/code/amatlas/dfranzen-fork-d-prime | amatlas (Zhilei Qiu) | v2 (inferred) | Page text: "dfranzen base = Apache-2.0 … verify the notebook page license" | [R1] D′ cell copied into our D′ variants |
| N8 | *大阪公立大学 Affectify ARC支部🐙｜31.54 in a Single Sub.* https://www.kaggle.com/code/shiiin9/affectify-arc-31-54-in-a-single-sub | shiiin9 | v1 or v2 | To verify on page | [R3] Origin of the D′ formula (via N7) |
| N9 | *Try merging it—you might get lucky and win gold⭐⭐⭐.* https://www.kaggle.com/code/heliosli/try-merging-it-you-might-get-lucky-and-win-gold | heliosli | v5 (inferred). Current: v12. | To verify on page | [R3] Idea for the empty-animation fix in our D′ variant |
| N10 | 154 public ARC-AGI-3 notebooks of other teams, collected 2026-10-01 for analysis: [`references/external-notebooks-consulted.csv`](references/external-notebooks-consulted.csv) | Various | The version current at collection, listed per notebook | Not exposed by the API | [R4] Analysed for our record; none copied into a submission |

## 4. Datasets by others (Kaggle)

| # | Dataset | Owner | Licence (Kaggle API) | Use |
|---|---|---|---|---|
| D1 | *pennyroyal-v253.* https://www.kaggle.com/datasets/dfranzen/pennyroyal-v253 | dfranzen | Unknown | [R2] SGLang serving build in N1 and every fork of it |
| D2 | *TAAF Kaggle Source Bundle (copy).* https://www.kaggle.com/datasets/dfranzen/taaf-kaggle-source-bundle-copy | dfranzen | Unknown | [R2] Duck/TAAF source in N1 and its forks |
| D3 | *Duck Qwen3.8 NVFP4 MTP vLLM smoke v1.* https://www.kaggle.com/datasets/keithtyser/duck-qwen38-nvfp4-mtp-vllm-smoke-v1 | keithtyser | Unknown | [R2] September FP4/NVFP4 line and the sheetu line |
| D4 | *Qwen3.8 Flash Next vLLM NVFP4 runtime v1.* https://www.kaggle.com/datasets/keithtyser/qwen38-flash-next-vllm-nvfp4-runtime-v1 | keithtyser | Unknown | [R2] Same |
| D5 | *TAAF Duck Qwen3.8 serving v1.* https://www.kaggle.com/datasets/keithtyser/taaf-duck-qwen38-serving-v1 | keithtyser | Unknown | [R2] Serving wheels in the ARC-AGI-2 entry |
| D6 | *ARC3 vLLM H100 Wheelhouse V3.* https://www.kaggle.com/datasets/mirzamilanfarabi/arc3-vllm-h100-wheelhouse-v3 | mirzamilanfarabi | Apache 2.0 | [R2] vLLM install in the ARC-AGI-2 entry |
| D7 | ARA Labs public hypothesis ledgers (pinned commits, listed in `Ablations/ARC-AGI-3/` under the hypothesis test) | ARA Labs | CC-BY-4.0 (as recorded in our test) | [R2] Data of the September hypothesis-confidence test |

## 5. Models (Kaggle model pages; weights are not redistributed here)

| # | Model | Owner | Licence (Kaggle API) | Use |
|---|---|---|---|---|
| M1 | *Intel-Qwen3.8-Flash-Next-W4A16-AutoRound*, Transformers/default/1. https://www.kaggle.com/models/dfranzen/intel-qwen3.8-flash-next-w4a16-autoround | dfranzen | "Other (specified in description)" | [R2] The playing model of N1 and both selected submissions |
| M2 | *albucino-Qwen3.8-Flash-Next-drafter*, Transformers/default/1. https://www.kaggle.com/models/dfranzen/albucino-qwen3-8-flash-next-drafter | dfranzen | "Other (specified in description)" | [R2] Speculative drafter, same notebooks |
| M3 | *Qwen3.8 Flash Next NVFP4*, PyTorch/radixark-modelopt-fp4/1. https://www.kaggle.com/models/keithtyser/qwen3-8-flash-next-nvfp4 | keithtyser | Not readable by the API on 2026-11-06 (403); recorded on 2026-10-20 as "Other (specified in description)" | [R2] The playing model of the sheetu and NVFP4 lines |
| M4 | *Qwen3.8 27B FP8 Repacked*, PyTorch/hf-fp8/1. https://www.kaggle.com/models/foysalemonshanto/qwen3-8-27b-fp8-repacked-v1 | foysalemonshanto | Apache 2.0 | [R2] The playing model of our ARC-AGI-2 entry and of the first Duck submission |
| M5 | The Qwen3.8 model family (Qwen team, Alibaba), from which M1–M4 derive | Qwen team | Per model; our 2026-10-17 notes record Qwen3.8-Flash-Next as Qwen Community License 1.0 (to verify) | [R2] |

## 6. Kaggle discussions

| # | Thread | Author | Use |
|---|---|---|---|
| K1 | *Comparing the Milestone 2 winning solutions.* https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/744792 | Tong Hui Kang (`huikang`) | [R3] Franzen v1 public LB 27.89; link to N1 v1 |
| K2 | *Incredible notebook performance variation (Daniel Franzen's copies data analysis).* https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/745062 | Son Pham (`sonphamorg`) | [R3] Noise reference: copies 25.77 ± 3.93 |
| K3 | *My attempt on Datafication & AGI: Can "lexicon view" read the sprites screen back for deeper take?* https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/746295 | Shehab Anwer (ours), with a question by Mintu Kumar | Our post; the question led to two lexicon fixes |
| K4 | *Two 0.00 scores since Oct 16, runs ending early. Anyone else?* https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/750173 | `ishankarnick`; reply by Jeroen Cottaar | [R3] The 15-minute idle rule of the rerun |
| K5 | Slow dataset and model reads, 20–25 October 2026. https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/751598 | Kaggle staff and competitors | [R3] The diagnosis behind our startup guard |

## 7. Papers and other external work cited in our code or records

| # | Reference | Where cited | Use |
|---|---|---|---|
| P1 | DREAMTEAM (NVIDIA). arXiv:2605.09650 | Docstring of `ARCAID/duck-taaf-addons-2026-09/batch/arc3_batch.py` | [R3] Support for multi-action batching |
| P2 | Karpathy A. *autoresearch.* https://github.com/karpathy/autoresearch (via https://github.com/habanwer/autoresearch-MIL) | `ARCAID/s1-offline-autoresearch/README.md` | [R3] Loop design of the first starter agent |
| P3 | The Adimension. *Agent-ProSAT.* https://github.com/The-Adimension/Agent-ProSAT | Same | [R3] Locked assessor / twin-blind design (author's own earlier work) |
| P4 | vLLM. https://github.com/vllm-project/vllm ; SGLang. https://github.com/sgl-project/sglang | Serving in our notebooks (installed from D1, D3–D6) | [R2] Inference servers |
| P5 | Sources consulted for the 2026-09-26 research memo (Kaggle and ARC pages, team writeups, arXiv preprints, blog posts): [`references/research-memo-sources-2026-09-26.md`](references/research-memo-sources-2026-09-26.md) | Research memo | [R4] Background survey; listed for completeness |

## 8. Tools

- **Anthropic, Claude Code:** used as described in [`../DISCLAIMERS.md`](../DISCLAIMERS.md).
- **Kaggle API** (`kaggle`, `kagglesdk`): every collection in `Tools/kaggle/`.
