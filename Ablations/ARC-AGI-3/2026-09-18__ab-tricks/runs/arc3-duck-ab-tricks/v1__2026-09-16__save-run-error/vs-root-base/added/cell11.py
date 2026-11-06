# A/B report: plain Duck (pass 0) vs Duck + arc3 tricks (pass 1)
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
            'human_per_level': run.get('base_actions_per_level'),
            'score': round(float(run.get('final_score') or 0), 3),
            'state': run.get('state'),
            'seconds': round(float(run.get('final_wallclock_seconds') or 0)),
            'tokens': int(tokens.group(1)) if tokens else None,
            'counters': stats.get('counters', {}),
            'hud_rows': stats.get('hud_rows'),
            'hud_cols': stats.get('hud_cols'),
        })

    def arm_summary(arm):
        rs = [r for r in rows if r['arm'] == arm]
        return {
            'runs': len(rs),
            'mean_score': round(sum(r['score'] for r in rs) / max(1, len(rs)), 3),
            'levels': sum(r['levels'] for r in rs),
            'games_with_a_level': sum(1 for r in rs if r['levels']),
            'actions': sum(r['actions'] for r in rs),
            'tokens': sum(r['tokens'] or 0 for r in rs),
            'seconds': sum(r['seconds'] for r in rs),
        }

    summary = {arm: arm_summary(arm) for arm in ('plain', 'tricks')}
    report = {
        'label': bench.get('label'),
        'summary': summary,
        'runs': rows,
        'note': 'One pass per arm: per-game differences are anecdotes; look for a consistent direction.',
    }
    (WORKING_DIR / 'arc3_ab_report.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
    lines = ['# arc3 A/B report', '',
             '| arm | runs | mean score | levels | games with a level | actions | tokens | seconds |',
             '|---|---|---|---|---|---|---|---|']
    for arm, s in summary.items():
        lines.append(f"| {arm} | {s['runs']} | {s['mean_score']} | {s['levels']} | {s['games_with_a_level']} "
                     f"| {s['actions']} | {s['tokens']} | {s['seconds']} |")
    lines += ['',
              '| game | arm | levels | actions per level | human per level | score | state | s | tokens | trick counters | HUD rows/cols |',
              '|---|---|---|---|---|---|---|---|---|---|---|']
    for r in sorted(rows, key=lambda r: (r['game'], r['pass'])):
        lines.append(f"| {r['game']} | {r['arm']} | {r['levels']}/{r['n_levels']} | {r['actions_per_level']} "
                     f"| {r['human_per_level']} | {r['score']} | {r['state']} | {r['seconds']} | {r['tokens']} "
                     f"| {r['counters']} | {r['hud_rows']}/{r['hud_cols']} |")
    (WORKING_DIR / 'arc3_ab_report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines))
