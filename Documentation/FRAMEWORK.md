# Framework: DEITY and datafication

## DEITY

This repository is organised by the DEITY Principles Framework. The framework was proposed in:

> Anwer S. *The Adimension: bridging human ingenuity and machine intelligence through the DEITY principles framework.* European Heart Journal – Imaging Methods and Practice 2026; 4(1): qyaf038. https://doi.org/10.1093/ehjimp/qyaf038 (Letter to the Editor; open access, CC BY-NC 4.0)

The letter defines the principles as follows (quoted):

| Principle | Definition in the letter |
|---|---|
| **Data** | "'Data' emphasizes the transparent inclusion of diverse multi-source inputs in a comprehensive manner." |
| **Ethics** | "'Ethics' establishes governance and safeguards throughout data lifecycle." |
| **Informatics** | "'Informatics' structures interpretable output to build knowledge that can be easily interpreted by both humans and machines." |
| **Technology** | "'Technology' orchestrates adaptive solutions that empower 'You', the human as well as the machine in synergy." |
| **You** | Named within the Technology principle: the human, working with the machine. |

The letter argues a position; it reports no experiment. This repository applies the framework as an organising lens for a competition entry. It does not test the framework.

## How each principle is applied here

| Principle | Applied as | Where |
|---|---|---|
| Data | Every notebook version kept with its log and a sha256 manifest of every output file; third-party inputs listed with their versions | `Submissions/`, `Ablations/`, `Documentation/REFERENCES.md` |
| Ethics | Use of AI disclosed; credit to every upstream author; licences recorded; what is not claimed stated; release checks before anything is made public | `DISCLAIMERS.md`, `ACKNOWLEDGEMENTS.md`, `Documentation/RELEASE-CHECKS.md` |
| Informatics | Every number traceable to a file; the same IDs and links on every platform | `Documentation/LINKS.md`, `2026-Paper-Track/` (to be written) |
| Technology | Our components, each with a kill switch, and the tools that collect and check the record | `ARCAID/`, `Tools/` |
| You | Entry points for readers, judges and anyone re-running the work | `README.md`, `Documentation/REPRODUCE.md` |

## Datafication, as the word is used here

The letter does not use the word "datafication". In this repository it means:

> **Turning something an agent or a researcher would otherwise handle as raw experience into structured records that can be queried, counted and tested.**

In DEITY terms, it is the step from **Data** to **Informatics**: from raw inputs to interpretable output.

We built it at three layers:

| Layer | Raw material | Structured record | Who reads the record | Component |
|---|---|---|---|---|
| Perception | The 64×64 screen (ARC-AGI-3) or the example grids (ARC-AGI-2) | Objects with stable names, changes between frames or pairs, induced rules | The model, through its Python sandbox | `ARCAID/lexicon-view`, `ARCAID/lexicon-arc-agi-2` |
| Economics | The agent's own play | A ledger of actions spent per level and turns without an action | The model, as a nudge, and the server, as a token cap | `ARCAID/probe-first` |
| Evaluation | Our own runs | Levels as paired trials, decision rules written before the runs, logs hashed and indexed | Us | `Tools/`, `Ablations/` |

Whether each layer helped is a question for the measurements in `Ablations/`, and for the paper written from them. It is not assumed here.
