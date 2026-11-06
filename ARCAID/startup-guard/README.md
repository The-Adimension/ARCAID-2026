# Startup guard: stop slow model loads from scoring 0.00

## What went wrong (Oct 21-25)

Our submission history from the Kaggle API:

| Submitted (UTC) | Ref | Kernel @ scriptVersionId | Result |
|---|---|---|---|
| 10-19 18:33 | 57405782 | `arcaid3-lexicon-dprime-dfranzen-m2` @ 360147562 | **21.18** |
| 10-21 13:19 | 57483523 | same, byte-identical | COMPLETE **0.00** |
| 10-22 04:59 | 57510463 | same, byte-identical | COMPLETE **0.00** |
| 10-24 22:53 | 57608710 | `arcaid3-lt-pf-on-r2` @ 361850417 | ERROR "A system error. Please try resubmitting…" |
| 10-25 06:34 | 57619917 | `arcaid3-probe-first-dfranzen-m2` @ 361509356 | COMPLETE **0.00** |

The same code scored 21.18 and then 0.00 twice, so these zeros don't come from our code. They match [discussion 751598](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/751598):

- Kaggle staff confirmed that the dataset cache was unstable in some regions, which made model and dataset reads slow.
- Other teams measured weight loads of 35-65 min. Before, loads took about 10 min.
- Many teams report the same 3,411-byte `submission.parquet` and runs that finish in about 30 min.

**How Franzen's notebook turns a slow load into a zero.** All of our M2 forks use his startup logic unchanged. Each step below gives the cell and the setting involved:

1. `SERVER_STARTUP_TIMEOUT = 12*60` in *1. Environment*: the benchmark is released at 12 min, with the server still loading.
2. `ARC3_WARMUP_ACTION_GAMES=1`: one game sends one RESET at about 12 min.
3. `ARC3_HTTP_RETRY_INITIAL_SECONDS=900`: each game's first analyzer request retries for 15 min, until about 27 min.
4. After that, every request fails at once. `ARC3_MAX_ANALYZER_FAILURES=10` then gives up on each game within about a minute.
5. Meanwhile the gateway has seen no action since the 12-min RESET, so it closes the scorecard at about 27 min.

The rerun ends COMPLETE with 0.00 after about 30 min. Any load longer than about 27 min ends this way.

The ERROR on 10-24 is the separate platform "system error" that other threads report (751631, 751756). Nothing in the notebook can fix it.

## The fix (`startup_guard_cell.py`)

This is a paste-in cell. It goes after *6. Load the benchmark* and before *9. Run the benchmark*. It uses only the standard library.

1. **Hold.** Before a game makes its first analyzer call, it waits until `http://127.0.0.1:8001/health` returns 200. One monitor thread polls the endpoint for all games. The model is never called while the server is cold, so the 900 s grace and the give-up counter are still unused when the server comes up.
2. **Keep-alive.** While games are held, one held game sends a RESET to the engine, using the same call as the stock warmup. It sends one immediately, then one every `SG_KEEPALIVE_S` (420 s), which keeps the scorecard below the 15-min idle close. Each RESET goes to the held game that has sent the fewest so far, so each game pays at most about one extra action on level 1. The stock warmup is switched off, because the first keep-alive does its job.
3. **Limits.** The hold ends in any of these cases:
   - the server becomes healthy;
   - the server process exits (games then fail fast, as before);
   - `SG_HOLD_MAX_S` (7,200 s) has passed since notebook start.
   The per-game clock (`started_at`) is not changed, so a hold never pushes a game past its stock deadline.
4. **Gateway wait.** `_wait_for_gateway` goes from 600 s to 1,800 s. One team's rerun died when the gateway's DNS took longer than 600 s to come up.
5. **Errors and switches.** Any error in the wrapper falls back to the stock behaviour and increments `SG_STATS['errors']`. Kill switch: `SG=0`.

This design follows the one dennis palatov described in the same thread: hold until `/health` returns 200, RESET every 7 min, give up after 2 h. On public games it survived 35-min and 44-min loads with no auto-close. In their one scored run it removed the 30-min zero, but that run then hit the platform ERROR.

## Tested

The cell was tested against Franzen's real harness: `dfranzen/taaf-kaggle-source-bundle-copy` with our `harness-changes.patch` applied. A fake `/health` server turns healthy after a few seconds, and five threads stand in for game sessions. The test script is `test_sg.py`. It checks five things:

- every game waits for health before its stock `_play_inner` runs;
- the keep-alive RESETs come on schedule and go to a different game each time;
- a game that starts after release is not held and sends nothing;
- re-running the cell does not stack the wrapper;
- a server that exits releases the hold at once.

The cell also runs a self-test when it loads and prints `self_test=ok`.

Not tested: a real scored rerun. We get no logs from those, so a slow load may still fail in a way we cannot see.

## Notebooks (`build.py`)

`build.py` pulls each base at the exact scriptVersionId that was submitted. It adds the note, the guard cell and a final counter cell, and changes the gateway number. Nothing else changes, and `build.py` asserts that.

| Folder | New kernel id (private) | Base |
|---|---|---|
| `notebooks/2026-10-25__arcaid3-probe-first-dfranzen-m2-v2__plus-startup-guard__…` | `habanwer/arcaid3-probe-first-dfranzen-m2-sg` | probe-first v2 (0.00 on 10-25) |
| `notebooks/2026-10-25__arcaid3-lexicon-dprime-dfranzen-m2-v1__plus-startup-guard__…` | `habanwer/arcaid3-lexicon-dprime-dfranzen-m2-sg` | lexicon D' v1 (21.18, then 0.00 twice) |

**What to check in the log:**
- near the start, `ARC3_SG_READY installed ... self_test=ok`;
- `ARC3_SG_RELEASE by=health t=...s keepalive_resets=N`;
- at the end, `ARC3_SG_FINAL {...}`.

On a healthy day `N` is 0 and nothing changes. The server comes up before 12 min, so no game is ever held.

## Also worth doing

- **Ask for rescores.** In thread 751598, post refs 57483523, 57510463 and 57619917 (COMPLETE 0.00) and 57608710 (ERROR). Kaggle staff are collecting submission IDs there for rescoring.
- **Check before submitting.** Run `arcaid3-mount-diag` v3 first and treat a DEGRADED result as a warning sign. The scored rerun runs on a different machine, though, so an OK result is no guarantee.
