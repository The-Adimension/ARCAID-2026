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
