# inputs/ (extracted 2026-09-26)

## official-input-arc-prize-2026-arc-agi-3/ (from the Kaggle competition input)

- **`environment_files/`:** the 25 public demo games. Each has a `<id>.py` game file and `metadata.json` with `baseline_actions` per level: 183 levels in all, 6–10 per game. These are the same files a Kaggle save run plays offline. Per the host, they are open source; the hidden 110 games are not in the rerun image.
- **`arc_agi_3_wheels/list_of_wheels.md`:** the wheel list only; the wheel files themselves are not included. It pins arc-agi 0.9.8 and arcengine 0.9.3 (CPython 3.12).
- **`ARC-AGI-3-Agents/`:** the official agent framework, without its `.git` folder. The Duck harness does not use it.

## local_play/ (local exploration of the public games)

- **Every `summary.json` "WIN" is false:** 25 of 25. Each records `actions: 1`, `win_actions [[5]]` and an empty final frame (`shape [0,0]`). Replaying RESET + ACTION5 with the pinned engine leaves all 25 games at level 0, NOT_FINISHED, and 11 games do not even offer ACTION5.
- **`full_actions.json` / `full_summary.json` hold the real records.** `verify_local_play.py` replays them on `environment_files`:

  | Game | Result | RHAE |
  |---|---|---|
  | cd82 | WIN 6/6 | 100 |
  | ft09 | WIN 6/6 | 100 |
  | sc25 | WIN 6/6 | 100 |
  | tu93 | 3/9 | 13.33 |
  | vc33 | 2/7 | 10.71 |
  | sp80 | 1/6 | 4.76 |
  | lp85 | 1/8 | 2.78 |
  | lf52 | 0/10 | 0 |
  | r11l | 0/6 | 0 |
  | su15 | 0/9 | 0 |

- **These are public-game solutions only.** They cannot run on the hidden set: the game files are absent there and the games are different.

## verify_local_play.py

Run it with Python 3.12, after `pip install arc-agi==0.9.8 arcengine==0.9.3`:

```
python inputs/verify_local_play.py
```

## replay_benchmark.py

Independent check of a save run's score. It replays `outputs/benchmark.json` action histories on these game files and re-scores them.
- v3 reproduces exactly: 25.08, identical on all 6 games.
- v4 gives 16.23.

```
python inputs/replay_benchmark.py <path/to/outputs/benchmark.json>
```
