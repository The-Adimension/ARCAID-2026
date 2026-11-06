"""Build the Kaggle A/B notebook: Duck harness vs Duck + arc3 tricks.

Three changes to the public LB-9 Duck fork, in the order the human chose:

2. THROUGHPUT (both arms, serving-level). Measured ceiling on our own scored run: ~880
   generated tokens per executed action at ~25 tok/s wallclock = ~150 actions per game,
   while a 2x-human full clear needs 1500-2600. Three fixes, all config:
     - LOCAL_ANALYZER_MAX_OUTPUT and _TOOL_STEPS are shipped as 0 = UNLIMITED; one
       analysis step in run1 burned 24,893 tokens over 630 s. Cap them.
     - vLLM serves --max-model-len 65536 while the agent never asks for more than 31,744
       prompt tokens, so KV holds ~11.3 full-length sequences against 28-way game
       concurrency. Halving the served window roughly doubles that headroom.
     - The kernel limit is 9 h (deploy_target.max_runtime_s = 32400) but Duck plans
       4 waves x 7920 s = 8 h 48 m of play plus setup, and in submission mode it passes
       NO soft deadline at all, so a hard kill would skip teardown entirely. Derive the
       per-game cap from the time actually left and keep a deadline in submission mode.
3. STALL RESET and 4. UNDO, plus the repaired guard signature: see abtest/arc3_tricks.py.
   Those three are the A/B arm; the throughput settings apply to both arms equally.
"""
import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

# Games we have never taught (our hold split), so a win here is a transfer signal rather
# than the public-set signal that failed to transfer three times in our own history.
GAMES = ["ft09-0d8bbf25", "sb26-7fbdac44", "s5i5-18d95033",
         "re86-8af5384d", "m0r0-492f87ba", "cn04-2fe56bfb"]
PASSES = 4          # 2 per arm: even passes plain, odd passes tricks
CONCURRENCY = 24    # every run in one wave, so each gets the same GPU share as the 28-way rerun
PER_GAME_S = 2700.0
# 80 was tuned for policy.py's 1200-action budget. Measured in abrun2, Duck gets ~16-60
# actions per game under concurrency, so 80 can never fire; 25 is the same fraction of
# Duck's action economy that 80 was of ours.
STALL_N = 25
TAIL_S = 150        # skip a turn whose model request would be cut short and discarded


def code(src: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": src}


# Applied to the bundled setup here-doc, which already gets regex-patched for the model id.
SERVING_PATCHES = [
    ("VLLM_MAX_MODEL_LEN = 65536", "VLLM_MAX_MODEL_LEN = 32768"),
    ("ANALYZER_CONTEXT_WINDOW = 32768", "ANALYZER_CONTEXT_WINDOW = 24576"),
    ("'LOCAL_ANALYZER_MAX_OUTPUT': '0'", "'LOCAL_ANALYZER_MAX_OUTPUT': '3072'"),
    ("'LOCAL_ANALYZER_TOOL_STEPS': '0'", "'LOCAL_ANALYZER_TOOL_STEPS': '12'"),
]

INSTALL = """\
# arc3 tricks: write the add-on, choose the arm policy, install before the benchmark is unpickled.
import importlib

ARC3_TRICKS_SOURCE = __SOURCE__
Path('/kaggle/working/arc3_tricks.py').write_text(ARC3_TRICKS_SOURCE, encoding='utf-8')
if '/kaggle/working' not in sys.path:
    sys.path.insert(0, '/kaggle/working')
# Save run: even passes plain Duck, odd passes Duck + tricks. Competition rerun: tricks on.
os.environ['ARC3_MODE'] = 'on' if _env_bool('KAGGLE_IS_COMPETITION_RERUN', False) else 'ab'
os.environ['ARC3_STALL_N'] = '__STALL_N__'
os.environ['ARC3_TAIL_S'] = '__TAIL_S__'
import arc3_tricks
arc3_tricks = importlib.reload(arc3_tricks)
print('arc3_tricks:', arc3_tricks.install())
"""

# Injected into the run cell, AFTER the rerun has fetched the hidden game list from the
# gateway -- before that point len(bm.games) is still the pickled template.
BUDGET = """\
    # arc3 item 2c: derive the per-game cap from the time actually left in the kernel, and
    # keep a soft deadline in submission mode so Benchmark.run's teardown always executes.
    import math

    KERNEL_LIMIT_S = float(getattr(target, 'max_runtime_s', 0.0) or 32400.0)
    TEARDOWN_RESERVE_S = 900.0
    _elapsed = time.time() - NOTEBOOK_START_EPOCH
    _remaining = max(600.0, KERNEL_LIMIT_S - _elapsed - TEARDOWN_RESERVE_S)
    _waves = max(1, math.ceil(len(bm.games) * max(1, bm.n_passes) / max(1, int(bm.solver.concurrency))))
    _derived_cap = _remaining / _waves
    if true_submission:
        bm.solver.max_runtime_s_per_game = _derived_cap
        soft_end = datetime.fromtimestamp(NOTEBOOK_START_EPOCH) + timedelta(
            seconds=KERNEL_LIMIT_S - TEARDOWN_RESERVE_S)
    else:
        bm.solver.max_runtime_s_per_game = min(bm.solver.max_runtime_s_per_game, _derived_cap)
    print(f'arc3 budget: kernel={KERNEL_LIMIT_S:.0f}s elapsed={_elapsed:.0f}s remaining={_remaining:.0f}s '
          f'games={len(bm.games)} passes={bm.n_passes} waves={_waves} '
          f'per_game={bm.solver.max_runtime_s_per_game:.0f}s soft_end={soft_end}', flush=True)
"""

REPORT = r"""
# A/B report: plain Duck (even passes) vs Duck + arc3 tricks (odd passes)
if not true_submission:
    import collections

    bench = json.loads((WORKING_DIR / 'benchmark.json').read_text(encoding='utf-8'))
    seen = collections.Counter()
    rows = []
    for run in bench.get('game_runs', []):
        gid = run.get('game_id', '')
        p = seen[gid]
        seen[gid] += 1
        stats_files = sorted((WORKING_DIR / 'artifacts').glob(f'{gid}*_p{p}_arc3.json'))
        stats = json.loads(stats_files[0].read_text()) if stats_files else {}
        tokens = re.search(r'tokens=(\d+)', str(run.get('solver_note', '')))
        rows.append({
            'game': gid.split('-')[0],
            'pass': p,
            'arm': stats.get('arm', 'tricks' if p % 2 else 'plain'),
            'levels': run.get('levels_completed', 0) or 0,
            'n_levels': run.get('number_of_levels'),
            'actions': len(run.get('history') or []),
            'actions_per_level': run.get('actions_per_level'),
            'score': round(float(run.get('final_score') or 0), 3),
            'state': run.get('state'),
            'seconds': round(float(run.get('final_wallclock_seconds') or 0)),
            'tokens': int(tokens.group(1)) if tokens else None,
            'counters': stats.get('counters', {}),
            'masked_rows': stats.get('masked_rows'),
            'masked_cols': stats.get('masked_cols'),
        })

    def summarize(arm):
        rs = [r for r in rows if r['arm'] == arm]
        actions = sum(r['actions'] for r in rs)
        tokens = sum(r['tokens'] or 0 for r in rs)
        return {
            'runs': len(rs),
            'mean_score': round(sum(r['score'] for r in rs) / max(1, len(rs)), 3),
            'levels': sum(r['levels'] for r in rs),
            'runs_with_a_level': sum(1 for r in rs if r['levels']),
            'actions': actions,
            'tokens': tokens,
            'tokens_per_action': round(tokens / max(1, actions)),
            'seconds': sum(r['seconds'] for r in rs),
            'stall_resets': sum(r['counters'].get('stall_resets', 0) for r in rs),
            'guard_blocks': sum(r['counters'].get('guard_blocks', 0) for r in rs),
            'tail_skips': sum(r['counters'].get('tail_skips', 0) for r in rs),
        }

    summary = {arm: summarize(arm) for arm in ('plain', 'tricks')}
    per_game = {}
    for game in sorted({r['game'] for r in rows}):
        for arm in ('plain', 'tricks'):
            rs = [r for r in rows if r['game'] == game and r['arm'] == arm]
            per_game.setdefault(game, {})[arm] = {
                'levels': [r['levels'] for r in rs],
                'actions': [r['actions'] for r in rs],
                'mean_score': round(sum(r['score'] for r in rs) / max(1, len(rs)), 3),
            }
    wins = sum(1 for g, d in per_game.items()
               if sum(d['tricks']['levels']) > sum(d['plain']['levels']))
    losses = sum(1 for g, d in per_game.items()
                 if sum(d['tricks']['levels']) < sum(d['plain']['levels']))
    verdict = ('tricks ahead on levels' if wins > losses else
               'plain ahead on levels' if losses > wins else 'tie on levels')
    report = {'label': bench.get('label'), 'summary': summary, 'per_game': per_game,
              'games_won_by_tricks': wins, 'games_lost_by_tricks': losses, 'verdict': verdict,
              'runs': rows,
              'note': 'Decide on levels cleared across 3 passes per arm, not on one game.'}
    (WORKING_DIR / 'arc3_ab_report.json').write_text(json.dumps(report, indent=1), encoding='utf-8')

    lines = ['# arc3 A/B report', '', f'verdict: {verdict} ({wins} games better, {losses} worse)', '',
             '| arm | runs | mean score | levels | runs with a level | actions | tokens/action | stall resets | guard blocks | tail skips |',
             '|---|---|---|---|---|---|---|---|---|---|']
    for arm, s in summary.items():
        lines.append(f"| {arm} | {s['runs']} | {s['mean_score']} | {s['levels']} | {s['runs_with_a_level']} "
                     f"| {s['actions']} | {s['tokens_per_action']} | {s['stall_resets']} | {s['guard_blocks']} "
                     f"| {s['tail_skips']} |")
    lines += ['', '| game | plain levels | tricks levels | plain actions | tricks actions | plain score | tricks score |',
              '|---|---|---|---|---|---|---|']
    for game, d in per_game.items():
        lines.append(f"| {game} | {d['plain']['levels']} | {d['tricks']['levels']} | {d['plain']['actions']} "
                     f"| {d['tricks']['actions']} | {d['plain']['mean_score']} | {d['tricks']['mean_score']} |")
    lines += ['', '| game | pass | arm | levels | actions | score | state | s | tokens | counters | masked rows/cols |',
              '|---|---|---|---|---|---|---|---|---|---|---|']
    for r in sorted(rows, key=lambda r: (r['game'], r['pass'])):
        lines.append(f"| {r['game']} | {r['pass']} | {r['arm']} | {r['levels']}/{r['n_levels']} | {r['actions']} "
                     f"| {r['score']} | {r['state']} | {r['seconds']} | {r['tokens']} | {r['counters']} "
                     f"| {r['masked_rows']}/{r['masked_cols']} |")
    (WORKING_DIR / 'arc3_ab_report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines))
""".lstrip("\n")


def main() -> None:
    base = json.loads((HERE / "baseline" / "arc3-duck-qwen38-baseline.ipynb").read_text(encoding="utf-8"))
    nb = copy.deepcopy(base)
    tricks = (HERE / "abtest" / "arc3_tricks.py").read_text(encoding="utf-8")

    nb["cells"][0]["source"] = (
        "# ARC-AGI-3: Duck harness + arc3 tricks (A/B)\n\n"
        "Harness: TAAF/Tufa Labs Duck (CC0 bundle); model Qwen3.8-27B-FP8 (Apache 2.0); wrapper from the "
        "public notebook foysalemonshanto/lb-9-arc3-duck-v12-with-qwen-3-8-27b.\n\n"
        "**Both arms** get the throughput fixes: bounded analysis turns (`MAX_OUTPUT` 3072, `TOOL_STEPS` 12, "
        "both shipped as unlimited), a 32768 served context so vLLM holds ~2x the concurrent sequences, and a "
        "per-game budget derived from the time actually left in the 9 h kernel with a deadline that also holds "
        "in submission mode.\n\n"
        "**Arm under test** (odd passes): a stall RESET after 25 actions with no level change, a guard that "
        "skips a turn too short to finish, `UNDO`/ACTION7 "
        "made reachable, and a no-op guard signature that ignores timer strips.\n\n"
        f"**Save run:** {len(GAMES)} public games we never taught x {PASSES} passes = 3 per arm. "
        "Output: `arc3_ab_report.md` / `.json`. **Competition rerun:** every hidden game plays with the arm on.\n")

    # --- item 2a/2b: serving knobs, patched into the bundled setup here-doc ---
    cell5 = "".join(nb["cells"][5]["source"])
    marker = "        patched.append(command)"
    assert cell5.count(marker) == 1
    cell5 = cell5.replace(
        marker,
        "        # arc3 item 2: bound the runaway turn and stop paying for a served context\n"
        "        # window the agent never asks for (both shipped as unlimited / 2x oversized).\n"
        "        for _old, _new in ARC3_SERVING_PATCHES:\n"
        "            if _old in command:\n"
        "                command = command.replace(_old, _new)\n"
        "                print('arc3 serving patch:', _old, '->', _new, flush=True)\n"
        + marker)
    cell5 = ("ARC3_SERVING_PATCHES = " + json.dumps([list(p) for p in SERVING_PATCHES], indent=4) + "\n\n") + cell5
    nb["cells"][5]["source"] = cell5

    # --- the add-on install cell, before benchmark_initial.pkl is unpickled ---
    nb["cells"].insert(6, code(INSTALL.replace("__SOURCE__", json.dumps(tricks)).replace("__STALL_N__", str(STALL_N)).replace("__TAIL_S__", str(TAIL_S))))

    # --- item 2c: keep a soft deadline in submission mode ---
    cell7 = "".join(nb["cells"][7]["source"])
    old_guard = "    if run_as_submission or max_runtime_s <= 0:\n        return None"
    assert cell7.count(old_guard) == 1
    nb["cells"][7]["source"] = cell7.replace(
        old_guard,
        "    # arc3: upstream returns None in submission mode, so nothing ever cancels the\n"
        "    # benchmark and a hard kernel kill would skip teardown entirely.\n"
        "    if max_runtime_s <= 0:\n        return None")

    # --- the A/B game set ---
    cell = "".join(nb["cells"][9]["source"])
    start = cell.index("Q38_P1_PUBLIC_GAME_IDS = [")
    end = cell.index("]", start) + 1
    cell = cell[:start] + "Q38_P1_PUBLIC_GAME_IDS = [\n" + "".join(f'    "{g}",\n' for g in GAMES) + "]" + cell[end:]
    for old, new in [
        # benchmark.run() rejects a duplicated games list (taaf/benchmark.py:161) and lays the
        # runs out pass-major itself, so solver.py:1071-1075 numbers each game's repeats 0,1,2...
        ("    bm.n_passes = 1\n", f"    bm.n_passes = {PASSES}\n"),
        ("bm.solver.concurrency = 28", f"bm.solver.concurrency = {CONCURRENCY}"),
        ("bm.solver.max_runtime_s_per_game = 1800.0", f"bm.solver.max_runtime_s_per_game = {PER_GAME_S}"),
        ('bm.label = f"{bm.label}-smoke-1g"', f'bm.label = f"{{bm.label}}-arc3-ab-{len(GAMES)}g"'),
    ]:
        assert cell.count(old) == 1, old[:80]
        cell = cell.replace(old, new)
    nb["cells"][9]["source"] = cell

    # The budget block belongs inside the run cell, after the rerun swaps in the hidden games.
    run_cell = "".join(nb["cells"][10]["source"])
    anchor = "    try:\n        await bm.run("
    assert run_cell.count(anchor) == 1
    nb["cells"][10]["source"] = run_cell.replace(anchor, BUDGET + "\n" + anchor)

    nb["cells"].insert(11, code(REPORT))

    out = HERE / "abnb"
    out.mkdir(exist_ok=True)
    (out / "arc3-duck-ab-tricks.ipynb").write_text(json.dumps(nb, indent=1), encoding="utf-8")
    meta = json.loads((HERE / "baseline" / "kernel-metadata.json").read_text(encoding="utf-8"))
    meta.update({"id": "habanwer/arc3-duck-ab-tricks", "title": "arc3-duck-ab-tricks",
                 "code_file": "arc3-duck-ab-tricks.ipynb"})
    (out / "kernel-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    for i, c in enumerate(nb["cells"]):
        src = "".join(c["source"])
        print(i, c["cell_type"], len(src), src.splitlines()[0][:80])
        if c["cell_type"] == "code":
            compile(src.replace("await bm.run(", "bm.run("), f"cell{i}", "exec")
    print("all code cells compile")


if __name__ == "__main__":
    main()
