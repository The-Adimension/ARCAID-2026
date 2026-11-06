# ARCAID3 level trials (evaluation only): every level of every game becomes its own trial.
#
# A whole-game run is noisy because levels are played in a chain: a game stuck on an early level scores
# nothing on the rest. Here each (game, level) entry starts cold at that level (the engine's own
# set_level, then a RESET, which ONLY_RESET_LEVELS keeps on that level), and the outcome is whether the
# agent clears it within the time budget. Two arms that differ in one thing can then be compared level by
# level, paired, over about 180 levels instead of 25 games.
#
# Checked offline: on 42 recorded level solutions, replaying the level's actions from a cold start at that
# level clears it, as in the original run (levels do not depend on how earlier levels were played).
#
# Entries are GameAPI objects with external_game_id "<game_id>@L<k>"; the start level travels inside that
# declared field. Results: per entry, levels_completed >= 1 means level k was cleared.
import re as _a3lt_re

import taaf.game_api as _a3lt_ga
from arcengine import GameAction as _A3LT_ACTION
from taaf.game import GameState as _A3LT_STATE

_A3LT_LEVEL = _a3lt_re.compile(r"@L(\d+)$")


def _arcaid3_start_level(self):
    m = _A3LT_LEVEL.search(self.external_game_id or "")
    return int(m.group(1)) if m else 0


if not getattr(_a3lt_ga.GameAPI._start_game, "_arcaid3_level_trials", False):
    _a3lt_orig_start = _a3lt_ga.GameAPI._start_game

    def _arcaid3_level_start(self, session):
        state = _a3lt_orig_start(self, session)
        k = _arcaid3_start_level(self)
        if k:
            self.env._game.set_level(k)               # offline LocalEnvironmentWrapper only
            resp = self.env.step(_A3LT_ACTION.RESET)  # ONLY_RESET_LEVELS (set by the original) keeps level k
            if resp is None or not resp.frame:
                raise RuntimeError(f"level trial {self.external_game_id}: no frame after set_level({k}) + RESET")
            state = _A3LT_STATE(raw=resp)
        return state

    _arcaid3_level_start._arcaid3_level_trials = True
    _a3lt_ga.GameAPI._start_game = _arcaid3_level_start


def arcaid3_level_trials(games, env_dir):
    """One entry per (game, level), level 0 first for every game, then level 1, and so on."""
    import arc_agi

    arcade = arc_agi.Arcade(operation_mode=arc_agi.OperationMode.OFFLINE, environments_dir=env_dir)
    n_levels = {}
    for g in games:
        env = arcade.make(g.env_name, seed=0)
        n_levels[g.env_name] = len(env._game._levels)
    entries = []
    for k in range(max(n_levels.values())):
        for g in games:
            if k < n_levels[g.env_name]:
                entries.append(_a3lt_ga.GameAPI(env_name=g.env_name, arcade_spec=g.arcade_spec,
                                                external_game_id=f"{g.env_name}@L{k}"))
    print("ARCAID3_LEVEL_TRIALS", len(entries), "entries over", len(games), "games", flush=True)
    return entries
