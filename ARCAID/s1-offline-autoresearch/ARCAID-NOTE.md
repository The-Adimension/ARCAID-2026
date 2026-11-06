# Note on this folder

These are files of the autoresearch loop behind our first starter agent (`arc-prize-2026-arc-agi-3-starter`, versions 1–9, public scores 0.02–0.13). They are taken from the loop's working snapshot. The original `README.md` of the loop is kept unchanged.

- **`perception.py`**: the agent's perception module. It is byte-identical to the starter kit's `agent/my_agent.py`.
- **`play.py`**: the play interface used by the teacher model.
- **`assess.py`**: the locked assessor.
- **`directives.md`**: the loop's rules.

The loop used frontier models as teachers and consultants; see `../../DISCLAIMERS.md`. The submitted notebook runs offline with no LLM. Its exact code is in `../../Submissions/ARC-AGI-3/`.
