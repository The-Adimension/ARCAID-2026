# Disclaimers

## 1. Use of AI

Claude Code (Anthropic), running the model **[model: to be stated by the author]**, was used to:
- improve the lexicon;
- analyse run logs;
- write code that supported decisions;
- implement and engineer code.

The concept and the base work are by Shehab Anwer. Every ablation was built on public notebooks by others. Their lineage is in [`ARCAID/LINEAGE.md`](ARCAID/LINEAGE.md), and every source is cited in [`Documentation/REFERENCES.md`](Documentation/REFERENCES.md).

Other AI use, stated for completeness:
- **September 2026 autoresearch loop.** Frontier models were used as teachers and consultants in the loop behind the first starter agent (`ARCAID/s1-offline-autoresearch/`). The records name Claude, Gemini and Grok.
- **No hosted model in a submission.** None of these models ran inside a Kaggle submission. Scored runs use only open-weight models, offline, as the competition requires.
- **This repository.** It was assembled with Claude Code from the work records. The author reviews it before release.

## 2. Affiliation

This work is independent. It is not affiliated with, or endorsed by:
- the ARC Prize Foundation or Kaggle;
- Tufa Labs;
- any author whose notebook it builds on;
- Anthropic, Alibaba (Qwen) or any other model provider.

## 3. Scores

- **Public leaderboard only.** Every score here is a public-leaderboard score: one run of the notebook on half of the hidden games. Private scores will be published on 2026-12-04 and may differ.
- **One draw is noisy.** Identical code can score several points apart. Copies of the base notebook we build on scored 25.77 ± 3.93 (Son Pham's measurement, Kaggle discussion 745062).
- **Selection on noise.**
  - Our 31.90 is the best of three draws of identical code (27.05, 31.90, 26.83).
  - Our 30.57 is the better of two (23.41, 30.57).
  - Choosing the highest draw for final scoring selects on noise. We state this rather than present either number as the method's true level.
- **Save-run scores.** A save-run score (on the public games, printed in a notebook log) is not a leaderboard score, and the two are kept apart throughout.

## 4. What we do not claim

- **The lexicon view does not raise scores.** In three controlled designs it made no detectable difference to levels cleared.
- **Probe-first is not established.** Its paired trials passed the main test (+15.5% levels, p = 0.022). One of its own pre-registered gates failed, so its own rule said not to submit it, and it was submitted anyway. The author's stated reason for selecting it for final scoring, with lexicon view v4: they are the two highest public scores, and they represent two different attempts (author's statement, 2026-11-06).
- **No effect on ARC-AGI-2.** The ARC-AGI-2 entry is a transfer demonstration with no ablation, so we claim no effect of the lexicon there.
- **No general claim.** Nothing here demonstrates artificial general intelligence or fluid intelligence. "Datafication" names what we built and tested, not a proven route to either.
- **Public games only.** Results on the 25 public games do not transfer to the hidden games by default. We report them only as save-run evidence.

## 5. Licences and third-party material

- **Our code.** Code written by the author is released under MIT-0 ([`LICENSE`](LICENSE)), as the competition's open-source rule requires.
- **Others' notebook cells.** Our notebooks contain, unchanged, the cells of the public notebooks they fork. Those cells remain their authors' work under their authors' licences. `Documentation/REFERENCES.md` lists each source and the licence its page shows, or states that none was found.
- **No model weights.** No model weights are redistributed here. The models are referenced by their Kaggle model pages and keep their own licences.
- **No competition data.** Competition data (game files and hidden-set material) is not redistributed. Run outputs that contain game state are listed by name and sha256 only.

## 6. Research use

This is research code for a competition. It is provided as is, without warranty, and is not intended for any safety-critical use.
