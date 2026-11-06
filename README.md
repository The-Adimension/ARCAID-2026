# ARCAID-2026

**Datafication on ARC Prize 2026: what turning screens, spending and runs into data did, and did not, do for an LLM agent on ARC-AGI-3 and ARC-AGI-2.**

Shehab Anwer · [The Adimension](https://www.theadimension.com) · Built on the [DEITY Principles Framework](https://doi.org/10.1093/ehjimp/qyaf038)

> **Status: preparation repository.** This is `habanwer/ARCAID-2026-Prep`. It is being checked for licence and privacy issues before it is released publicly as `The-Adimension/ARCAID-2026`. Until then, some links to Kaggle notebooks point to notebooks that are still private.

---

## At a glance

| Track | Our submissions | Selected for final scoring | Best public score | Public rank | Private score |
|---|---|---|---|---|---|
| [ARC-AGI-3](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3) | 43 (41 scored, 2 Kaggle errors) | **Lexicon view v4** (31.90) and **Probe-first + startup guard v1** (30.57) | 31.90 | 438 of 4,927 | Due 2026-12-04 |
| [ARC-AGI-2](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-2) | 4 (one after the deadline) | To be confirmed | 10.83 | 2,438 of 3,543 | Due 2026-12-04 |
| [Paper Track](https://www.kaggle.com/competitions/arc-prize-2026-paper-track) | To be written from this catalogue into [`2026-Paper-Track/`](2026-Paper-Track/) | n/a | n/a | n/a | Judged on a six-part rubric |

Public scores and ranks are from Kaggle's public leaderboards, downloaded 2026-11-06 10:03 UTC. A public score is one run on half of the hidden games, and one run of identical code can move by several points (see [`DISCLAIMERS.md`](DISCLAIMERS.md)).

## The question

Can an LLM agent play unfamiliar games better if what it sees, what it spends and how we test it are turned into data?

We built **datafication** at three layers. Each was added to someone else's strong public agent as optional code, and most were tested with decision rules written before the runs.

| Layer | What is turned into data | Our component | Tests |
|---|---|---|---|
| **Perception** | The 64×64 screen, read back into objects, names, changes and induced rules | [`ARCAID/lexicon-view`](ARCAID/lexicon-view/) | [`Ablations/ARC-AGI-3`](Ablations/ARC-AGI-3/) |
| **Economics** | The agent's own spending: actions per level and turns that executed no action | [`ARCAID/probe-first`](ARCAID/probe-first/) | [`Ablations/ARC-AGI-3`](Ablations/ARC-AGI-3/) |
| **Evaluation** | Our own runs: every level as a paired trial, every number tied to a log | [`Tools/`](Tools/) | [`Ablations/`](Ablations/) |

The same idea was carried, separately, to the static grids of ARC-AGI-2 as a transfer demonstration ([`ARCAID/lexicon-arc-agi-2`](ARCAID/lexicon-arc-agi-2/)).

This catalogue records what was built, run and measured. Conclusions will be drawn from the whole catalogue in the paper ([`2026-Paper-Track/`](2026-Paper-Track/)).

## Where to start

| You want to… | Go to |
|---|---|
| Read the paper | [`2026-Paper-Track/`](2026-Paper-Track/) (empty until the paper is written from this catalogue) |
| See what each of the two selected submissions is, and how it differs from its base | [`Documentation/SELECTED-SUBMISSIONS.md`](Documentation/SELECTED-SUBMISSIONS.md) |
| See every submission, with its notebook and log | [`Submissions/ARC-AGI-3/`](Submissions/ARC-AGI-3/), [`Submissions/ARC-AGI-2/`](Submissions/ARC-AGI-2/) |
| See the controlled tests behind each claim | [`Ablations/ARC-AGI-3/`](Ablations/ARC-AGI-3/) |
| Read our code | [`ARCAID/`](ARCAID/), starting with [`ARCAID/LINEAGE.md`](ARCAID/LINEAGE.md) |
| Find the Kaggle, GitHub and Hugging Face address of any notebook or run | [`Documentation/LINKS.md`](Documentation/LINKS.md) |
| Check whose work this builds on | [`ACKNOWLEDGEMENTS.md`](ACKNOWLEDGEMENTS.md), [`Documentation/REFERENCES.md`](Documentation/REFERENCES.md) |
| Re-run the analysis | [`Documentation/REPRODUCE.md`](Documentation/REPRODUCE.md) |

## Repository map

```
ARCAID-2026/
├── README.md               this page
├── DISCLAIMERS.md          use of AI, what we do not claim, scores, licences
├── ACKNOWLEDGEMENTS.md     whose work this builds on
├── LICENSE                 MIT-0, for the code we wrote
├── Documentation/          framework, selected submissions, lineage, references, links, reproduction, release checks
├── Submissions/
│   ├── ARC-AGI-3/          one folder per submitted notebook version: notebook, log, run summary, outputs manifest
│   └── ARC-AGI-2/
├── Ablations/
│   ├── ARC-AGI-3/          one folder per controlled test: decision rule, notebooks, logs, analysis, result
│   └── ARC-AGI-2/
├── ARCAID/                 our code that went into the submissions, one folder per component
├── 2026-Paper-Track/       the writeup, paper, figures and tables (to be written from this catalogue)
└── Tools/                  collectors, diff and lineage tools, analysis and release checks
```

## How this repository follows DEITY

The [DEITY Principles Framework](https://doi.org/10.1093/ehjimp/qyaf038) (Data, Ethics, Informatics, Technology, You) is the organising lens. Folder names stay conventional, so you can find code and data without knowing the framework.

| Principle | Where it lives here |
|---|---|
| **Data**: transparent, multi-source inputs | `Submissions/` and `Ablations/`: every notebook version, its log and a sha256 manifest of its outputs |
| **Ethics**: governance and safeguards | `DISCLAIMERS.md`, `ACKNOWLEDGEMENTS.md`, `Documentation/REFERENCES.md`, `Documentation/RELEASE-CHECKS.md` |
| **Informatics**: interpretable outputs | `2026-Paper-Track/` (each number tied to its evidence), `Documentation/` |
| **Technology**: adaptive solutions | `ARCAID/` (the components) and `Tools/` |
| **You**: human and machine together | "Where to start" above, `Documentation/REPRODUCE.md`, and the use-of-AI statement in `DISCLAIMERS.md` |

## Where things are hosted

| Platform | What is there |
|---|---|
| **GitHub** (this repository) | The source of truth: code, notebooks, logs, tables, paper source |
| **Kaggle notebooks** | Every notebook used in the competitions, with its outputs ([`Documentation/LINKS.md`](Documentation/LINKS.md)) |
| **Kaggle Writeup** | The Paper Track submission |
| **Kaggle Dataset and Hugging Face** | Full run outputs, too large for git. Each run folder here lists them with sha256 (planned; published after the release checks) |

## Licence and citation

The code we wrote is released under [MIT-0](LICENSE), as the competition requires. Third-party code, notebooks, datasets and models keep their own licences; see [`DISCLAIMERS.md`](DISCLAIMERS.md) and [`Documentation/REFERENCES.md`](Documentation/REFERENCES.md).

Please cite this work as: Anwer S. *ARCAID-2026: datafication on ARC Prize 2026.* The Adimension, 2026. https://github.com/The-Adimension/ARCAID-2026
