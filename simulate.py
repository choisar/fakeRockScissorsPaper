"""Reproducible experiment runner (standard library only)."""
import argparse
import csv
import hashlib
import json
import platform
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from random import Random
from analysis import summarize, holm_adjust
from engine import GameConfig, play_game
from exact import exact_summary, first_branches
from report import build_report


def arguments():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--players', type=int, nargs='+', default=[4, 6])
    p.add_argument('--colluders', type=int, nargs='+', default=[2, 3, 4])
    p.add_argument('--catchers', type=int, nargs='+', default=[1, 2])
    p.add_argument('--trials', type=int, default=100_000)
    p.add_argument('--seed', type=int, default=20261109)
    p.add_argument('--output', type=Path, default=Path(__file__).parent / 'outputs' / 'validated-main')
    p.add_argument('--throw-analysis', action='store_true', help='record all throws and compare three strategies')
    a = p.parse_args()
    if a.trials < 2 or any(not 2 <= n <= 20 for n in a.players):
        p.error('trials >= 2 and 2 <= players <= 20 required')
    if min(a.colluders) < 1 or min(a.catchers) < 1:
        p.error('colluders and catchers must be positive')
    return a


def run(a):
    if getattr(a, 'throw_analysis', False):
        return run_throw_analysis(a)
    configs = [GameConfig(n,c,k) for n,c,k in sorted(set(product(a.players,a.colluders,a.catchers))) if c<n and k<n]
    if not configs:
        raise ValueError('no valid conditions')
    a.output.mkdir(parents=True, exist_ok=True)
    if any(a.output.iterdir()):
        raise FileExistsError('Choose an empty --output directory; previous results are preserved')
    records = []
    for cfg in configs:
        n,c,k = cfg.total_players,cfg.colluders,cfg.target_catchers
        name = f'n{n}_c{c}_k{k}'
        seed = f'{a.seed}:{n}:{c}:{k}'
        rng, control_rng = Random(seed+':experiment'), Random(seed+':control')
        counts, control_counts, rows = [0]*n, [0]*n, []
        with (a.output/f'{name}.csv').open('w',newline='',encoding='utf-8') as f:
            writer = csv.DictWriter(f,fieldnames=['game','survived_c','survived_n','delta'])
            writer.writeheader()
            for i in range(a.trials):
                caught = play_game(cfg,rng)['catchers']
                for player in caught:
                    counts[player] += 1
                sc = c-sum(player<c for player in caught)
                sn = n-c-sum(player>=c for player in caught)
                row = dict(game=i,survived_c=sc,survived_n=sn,delta=sc/c-sn/(n-c))
                writer.writerow(row)
                rows.append(row)
        control = GameConfig(n,0,k)
        for _ in range(a.trials):
            for player in play_game(control,control_rng)['catchers']:
                control_counts[player] += 1
        stats = summarize(rows,n,c,k)
        record = dict(id=name,players=n,colluders=c,catchers=k,trials=a.trials,seed=seed,
            stats=stats,exact=exact_summary(c,n-c,k),
            individual_survival=[1-v/a.trials for v in counts],
            control_individual_survival=[1-v/a.trials for v in control_counts],
            first_branches=first_branches(c,n-c,k),
            sample_game=play_game(cfg,Random(seed+':trace'),trace=True))
        records.append(record)
        print(f'{name}: delta={stats["delta"]:.6f}; exact={record["exact"]["delta"]["fraction"]}',flush=True)
    for r,p in zip(records,holm_adjust([r['stats']['p_value_normal'] for r in records])):
        r['stats']['p_value_holm'] = p
    hashes = {name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ['engine.py','exact.py','analysis.py','simulate.py','report.py']}
    data = dict(metadata=dict(seed=a.seed,trials=a.trials,created_utc=datetime.now(timezone.utc).isoformat(),
        python=platform.python_version(),implementation=platform.python_implementation(),platform=platform.platform(),
        dependencies='Python standard library only',source_sha256=hashes,
        options=dict(players=a.players,colluders=a.colluders,catchers=a.catchers),
        video_url='https://youtu.be/YJckrnOUaoM',
        video_status='User-provided inspiration; video rules not independently verified'),conditions=records)
    (a.output/'results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    build_report(data,a.output/'report.html')
    print(f'Completed: {a.output.resolve()}',flush=True)
    return data


def run_throw_analysis(a):
    import gzip
    from fractions import Fraction
    from analysis import analyze_log

    configs = sorted(set(product(a.players, a.colluders, a.catchers)))
    configs = [(n, c, k) for n, c, k in configs if 0 < c < n and 0 < k < n]
    if not configs or a.trials < 2:
        raise ValueError('valid mixed groups and at least two games required')
    a.output.mkdir(parents=True, exist_ok=True)
    if any(a.output.iterdir()):
        raise FileExistsError('Choose an empty --output directory; previous results are preserved')
    records = []
    for n, c, k in configs:
        for strategy in ('fixed', 'shared_random', 'independent'):
            cfg = GameConfig(n, c, k, strategy)
            name = f'n{n}_c{c}_k{k}_{strategy}'
            seed = f'{a.seed}:{n}:{c}:{k}:{strategy}'
            rng = Random(seed)
            raw = a.output / (name + '.jsonl.gz')
            with gzip.open(raw, 'wt', encoding='utf-8', compresslevel=1) as file:
                for game in range(a.trials):
                    index = 0
                    def save(event):
                        nonlocal index
                        compact = {key: value for key, value in event.items() if key != 'action'}
                        file.write(json.dumps(dict(type='event', game=game, index=index, event=compact),
                                              separators=(',', ':')) + '\n')
                        index += 1
                    result = play_game(cfg, rng, on_event=save)
                    file.write(json.dumps(dict(type='result', game=game, catchers=result['catchers']),
                                          separators=(',', ':')) + '\n')
            observed = analyze_log(raw, n, c, k)
            exact = exact_summary(c, n-c, k)
            if strategy == 'independent':
                baseline = Fraction(n-k, n)
                exact = {key: dict(fraction=str(value), value=float(value)) for key, value in
                         [('p_c', baseline), ('p_n', baseline), ('delta', Fraction(0))]}
            with raw.open('rb') as source:
                digest = hashlib.sha256()
                for chunk in iter(lambda: source.read(1024*1024), b''):
                    digest.update(chunk)
            records.append(dict(id=name, players=n, colluders=c, catchers=k, strategy=strategy, seed=seed,
                                raw_file=raw.name, raw_sha256=digest.hexdigest(),
                                exact=exact, **observed))
            print(f"{name}: games={observed['trials']}; throws={observed['throws']}; delta={observed['stats']['delta']:.6f}", flush=True)
    for record, p in zip(records, holm_adjust([r['stats']['p_value_normal'] for r in records])):
        record['stats']['p_value_holm'] = p
    hashes = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
              for name in ['engine.py', 'exact.py', 'analysis.py', 'simulate.py', 'report.py']}
    data = dict(mode='throw-analysis', schema_version=2, metadata=dict(seed=a.seed, trials=a.trials,
                created_utc=datetime.now(timezone.utc).isoformat(), python=platform.python_version(),
                platform=platform.platform(), source_sha256=hashes,
                options=dict(players=a.players, colluders=a.colluders, catchers=a.catchers)), conditions=records)
    (a.output/'results.json').write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    build_report(data, a.output/'report.html')
    return data


if __name__ == '__main__':
    run(arguments())
