# Decision rule for lexicon on against off, fixed before round 2 (2026-10-09)

**When it was fixed.** This rule was written and committed after round 1 (lexicon on 51.20, off 43.77) and before round 2 was pushed. It is applied by `compare_lb_setup.py` whenever it is given more than one round.

**Measures:**
- **Primary:** the lexicon-on score minus the lexicon-off score (the 25-game mean in this setup), averaged over the rounds.
- **Test:** for each game, average the on − off score difference over the rounds. Then run a two-sided sign-flip test over the 25 games, paired by game.
- **Consistency:** whether on − off is positive in every round.
- **Reported but not decisive:** levels, the levels-over-time area, games fully won, and the run-to-run spread within each arm.

**Decision after round 2:**

| Outcome | Condition | Action |
|---|---|---|
| **Recommend submitting v5** | The primary is +5.0 points or more, on − off is positive in both rounds, and the test gives p < 0.10 | Recommend v5 as the competition entry |
| **No measurable effect** | The primary is below +2.0, or round 2's difference is zero or negative | Keep the code, and stop treating the view as the lever |
| **Inconclusive** | Anything else | Run round 3 and apply the same thresholds to three rounds. If it is still inconclusive, treat it as no measurable effect |

**Limits.**
- Submitting is the user's call; the rule only sets the recommendation.
- The leaderboard's own noise (unchanged copies span about 21–29) means a single submission cannot confirm an effect of this size.
