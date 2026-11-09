"""Audit experiment folders without modifying their saved results."""
import argparse
import csv
import hashlib
import json
from itertools import product
from math import sqrt, isclose, isfinite
from pathlib import Path
from random import Random

from analysis import summarize, holm_adjust
from engine import GameConfig, play_game
from exact import exact_summary, first_branches

ROOT = Path(__file__).resolve().parent


def require(condition, context):
    # Explicit exceptions keep the audit active under python -O as well.
    if not condition:
        raise ValueError(context)


def same(actual, expected, context, *, probability=False):
    if isinstance(expected, float):
        require(isinstance(actual, (int, float)) and not isinstance(actual, bool)
                and isfinite(actual) and isclose(actual, expected, rel_tol=1e-12,
                                                abs_tol=0 if probability else 1e-14), context)
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected), context)
        for a, e in zip(actual, expected):
            same(a, e, context, probability=probability)
    else:
        require(actual == expected, context)


def verify(folder):
    folder = Path(folder)
    data = json.loads((folder / 'results.json').read_text(encoding='utf-8'))
    hashes = data['metadata']['source_sha256']
    require(set(hashes) == {'engine.py', 'exact.py', 'analysis.py', 'simulate.py', 'report.py'},
            'source hash coverage')
    for name, digest in hashes.items():
        require(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest,
                f'source hash: {name}')
    options = data['metadata']['options']
    expected_ids = {f'n{n}_c{m}_k{k}' for n, m, k in
                    product(options['players'], options['colluders'], options['catchers'])
                    if m < n and k < n}
    conditions = data['conditions']
    require(len(conditions) == len(expected_ids)
            and {c['id'] for c in conditions} == expected_ids, 'condition coverage')
    maximum_z, zero_variance, raw_p = None, [], []
    for c in conditions:
        n, m, k = c['players'], c['colluders'], c['catchers']
        cfg = GameConfig(n, m, k)
        require(0 < m < n and c['id'] == f'n{n}_c{m}_k{k}', 'condition configuration')
        require(c['trials'] == data['metadata']['trials'] and c['trials'] >= 2, 'trial count')
        require(c['seed'] == f"{data['metadata']['seed']}:{n}:{m}:{k}", 'condition seed')
        rows = []
        with (folder / (c['id'] + '.csv')).open(encoding='utf-8', newline='') as file:
            reader = csv.DictReader(file)
            require(reader.fieldnames == ['game', 'survived_c', 'survived_n', 'delta'], 'CSV columns')
            for i, raw in enumerate(reader):
                row = {key: int(raw[key]) for key in ['game', 'survived_c', 'survived_n']}
                row['delta'] = float(raw['delta'])
                require(row['game'] == i, 'CSV game order')
                require(0 <= row['survived_c'] <= m and 0 <= row['survived_n'] <= n-m,
                        'CSV group counts')
                require(row['survived_c'] + row['survived_n'] == n-k, 'CSV survivor total')
                same(row['delta'], row['survived_c']/m-row['survived_n']/(n-m), 'CSV delta')
                rows.append(row)
        require(len(rows) == c['trials'], 'CSV trial count')
        stats = summarize(rows, n, m, k)
        for key, expected in stats.items():
            require(key in c['stats'], f'missing statistic: {key}')
            same(c['stats'][key], expected, f"{c['id']}: {key}", probability=key == 'p_value_normal')
        raw_p.append(stats['p_value_normal'])
        exact = exact_summary(m, n-m, k)
        require(set(c['exact']) == set(exact), 'exact fields')
        for key, expected in exact.items():
            require(c['exact'][key]['fraction'] == expected['fraction'], f'exact fraction: {key}')
            same(c['exact'][key]['value'], expected['value'], f'exact value: {key}')
        require(c['first_branches'] == first_branches(m, n-m, k), 'exact branches')
        require(c['sample_game'] == play_game(cfg, Random(c['seed']+':trace'), trace=True), 'sample trace')
        if stats['standard_error']:
            z = abs(stats['delta'] - exact['delta']['value']) / stats['standard_error']
            require(z < 6, f"{c['id']}: exact deviation {z} SE")
            maximum_z = max(maximum_z or 0, z)
        else:
            # A constant sample does not prove a deterministic population.
            zero_variance.append(c['id'])
        baseline = (n-k)/n
        for field in ['individual_survival', 'control_individual_survival']:
            require(len(c[field]) == n, f'{field}: player count')
            for i, rate in enumerate(c[field]):
                theoretical = baseline if field.startswith('control') else exact['p_c' if i < m else 'p_n']['value']
                require(isfinite(rate) and 0 <= rate <= 1 and
                        abs(rate-theoretical) <= 6*sqrt(theoretical*(1-theoretical)/c['trials']) + 1e-14,
                        f'{field}: player {i}')
        same(sum(c['individual_survival'][:m])/m, stats['p_c'], 'individual colluder average')
        same(sum(c['individual_survival'][m:])/(n-m), stats['p_n'], 'individual noncolluder average')
        same(sum(c['control_individual_survival'])/n, baseline, 'control average')
        rng = Random(c['seed']+':experiment')
        for row in rows[:100]:
            caught = play_game(cfg, rng)['catchers']
            require(row['survived_c'] == m-sum(p < m for p in caught), 'seed replay')
    for c, adjusted in zip(conditions, holm_adjust(raw_p)):
        require('p_value_holm' in c['stats'], 'missing Holm p-value')
        same(c['stats']['p_value_holm'], adjusted, f"{c['id']}: p_value_holm", probability=True)
    return dict(conditions=len(conditions), games_per_arm=data['metadata']['trials'],
                maximum_exact_deviation_in_standard_errors=maximum_z,
                zero_variance_conditions=zero_variance,
                checks='CSV invariants; all statistics including CI and Holm; exact fractions and branches; '
                       'trace and 100-game seed replay; source hashes; individual rates within 6 SE of theory')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folders', nargs='+', type=Path, help='experiment output folders')
    parser.add_argument('--output', type=Path, help='optional new verification JSON file')
    args = parser.parse_args()
    result = {str(folder): verify(folder) for folder in args.folders}
    serialized = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output:
        with args.output.open('x', encoding='utf-8') as file:
            file.write(serialized + '\n')
    print(serialized)


if __name__ == '__main__':
    main()
