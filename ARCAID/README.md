# ARCAID: our code

Every piece of code we wrote that went into a competition notebook, one folder per component. The notebooks that ran each piece are in `../Submissions/` and `../Ablations/`. How the notebooks descend from each other and from others' work is in [`LINEAGE.md`](LINEAGE.md).

| Folder | Track | Layer | What it is | First used | Kill switch |
|---|---|---|---|---|---|
| [`s1-offline-autoresearch/`](s1-offline-autoresearch/) | ARC-AGI-3 | — | Our own starter agent: explores, models the rules, checks the model, then plans. No LLM in the submission. | 2026-09-05 | — |
| [`duck-taaf-addons-2026-09/`](duck-taaf-addons-2026-09/) | ARC-AGI-3 | Economics, memory | Add-ons to the Duck/TAAF harness: action batching, stall warning, hypothesis ledger, prompt compaction, world-model lines from reasoning | 2026-09-19 | Per module |
| [`lexicon-view/`](lexicon-view/) | ARC-AGI-3 | **Perception** | The screen read back into objects, names, changes and induced rules, offered in the agent's Python sandbox | 2026-10-03 | `ARCAID3_LEXICON=0` |
| [`stuck-level-restart/`](stuck-level-restart/) | ARC-AGI-3 | Memory | A level's conversation is cleared once after a token budget without clearing it | 2026-10-12 | `ARC3_STUCK_RESTART_TOKENS=0` |
| [`probe-first/`](probe-first/) | ARC-AGI-3 | **Economics** | A ledger of actions and action-free turns per level, fed back as a nudge and a token cap | 2026-10-23 | `PF=0` |
| [`startup-guard/`](startup-guard/) | ARC-AGI-3 | Infrastructure | Holds games until the model server is healthy and keeps the scorecard open | 2026-10-25 | `SG=0` |
| [`lexicon-arc-agi-2/`](lexicon-arc-agi-2/) | ARC-AGI-2 | **Perception** (transfer) | The lexicon idea on static grids: objects, train-pair changes and invariant facts, as tools for a program-synthesis agent | 2026-10-31 | `ARCAID3_LEXICON=0` |

**Layout of each folder:**
- `source/`: the component's code.
- `build/`: the scripts that wrote it into a notebook.
- `tests/`: checks and offline evaluations.
- `docs/`: design notes as written at the time.
- `as-run/`: the exact cell text extracted from the Kaggle notebook versions that ran it.

**Paths in older scripts.** The build and test scripts were written in our working repository (`habanwer/ARCAID3`). Paths inside them refer to that repository's layout.
