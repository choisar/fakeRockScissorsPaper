"""Independent multinomial enumeration with rational arithmetic; no engine import."""
from fractions import Fraction
from functools import lru_cache
from math import factorial


@lru_cache(None)
def branches(c, n):
    counts = {}
    for rock in range(n + 1):
        for scissors in range(n - rock + 1):
            paper = n - rock - scissors
            hands = (c + rock, scissors, paper)
            present = [i for i, count in enumerate(hands) if count]
            if len(present) != 2:
                continue
            # Independent explicit matchup table, not the engine's modular rule.
            losing = {(0, 1): 1, (0, 2): 0, (1, 2): 2}[tuple(present)]
            lc = c if losing == 0 else 0
            ln = (rock, scissors, paper)[losing]
            weight = factorial(n) // (factorial(rock) * factorial(scissors) * factorial(paper))
            counts[lc, ln] = counts.get((lc, ln), 0) + weight
    return tuple((lc, ln, weight) for (lc, ln), weight in sorted(counts.items()))


@lru_cache(None)
def expected_colluder_catchers(c, n, k):
    if not 0 <= k <= c + n:
        raise ValueError('invalid remaining catcher count')
    if k == 0 or c == 0:
        return Fraction(0)
    if n == 0:
        return Fraction(k)
    if k == c + n:
        return Fraction(c)
    valid = branches(c, n)
    total = sum(w for _, _, w in valid)
    result = Fraction(0)
    for lc, ln, weight in valid:
        if lc + ln >= k:
            future = expected_colluder_catchers(lc, ln, k)
        else:
            future = lc + expected_colluder_catchers(c - lc, n - ln, k - lc - ln)
        result += Fraction(weight, total) * future
    return result


def exact_summary(c, n, k):
    caught = expected_colluder_catchers(c, n, k)
    pc = 1 - caught / c
    pn = 1 - (k - caught) / n
    return {key: {'fraction': str(value), 'value': float(value)}
            for key, value in [('p_c', pc), ('p_n', pn), ('delta', pc - pn)]}


def first_branches(c, n, k):
    valid = branches(c, n)
    total = sum(w for _, _, w in valid)
    return [dict(losing_c=lc, losing_n=ln, probability=str(Fraction(w, total)),
                 terminal=lc + ln == k,
                 next_state=None if lc + ln == k else
                 ([lc, ln, k] if lc + ln > k else [c-lc, n-ln, k-lc-ln]),
                 confirmed_c=0 if lc + ln > k else lc)
            for lc, ln, w in valid]


def _block_domain(c, m, k=None):
    if type(c) is not int or type(m) is not int or c < 1 or m < 0:
        raise ValueError('block size c >= 1 and singleton count m >= 0 must be integers')
    if k is not None and (type(k) is not int or not 0 <= k <= c+m):
        raise ValueError('integer quota must be between zero and total population')


def block_expected_catchers(c, m, k):
    """Closed form for a uniform block position; no RPS enumeration or recursion."""
    _block_domain(c, m, k)
    def triangular_positive(x):
        x = max(x, 0)
        return x*(x+1)//2
    numerator = triangular_positive(k)-triangular_positive(k-c)-triangular_positive(k-m-1)
    return Fraction(numerator, m+1)


def block_rank_pmf(c, m):
    """Theoretical focal-player rank, not an observed ordering of a game."""
    _block_domain(c, m)
    n = c+m
    return tuple(Fraction(min(r, c, m+1, n+1-r), c*(m+1)) for r in range(1, n+1))


def block_summary(c, m, k):
    """Per-player survival from the block theorem; requires both groups."""
    _block_domain(c, m, k)
    if m == 0:
        raise ValueError('both groups are required for a survival comparison')
    caught = block_expected_catchers(c, m, k)
    pc = 1-caught/c
    pn = 1-(k-caught)/m
    return {key: dict(fraction=str(value), value=float(value))
            for key, value in [('p_c', pc), ('p_n', pn), ('delta', pc-pn)]}


def check_block_model(max_players=20, observed=()):
    """Finite computational checks supplement, but do not constitute, the proof."""
    import hashlib
    import json
    from pathlib import Path
    if type(max_players) is not int or max_players < 2:
        raise ValueError('max_players must be an integer >= 2')
    cases, populations = 0, 0
    for n in range(2, max_players+1):
        for c in range(1, n):
            m = n-c
            pmf = block_rank_pmf(c, m)
            if sum(pmf) != 1 or pmf != pmf[::-1]:
                raise ValueError('rank normalization or symmetry failure')
            mean = sum(r*p for r, p in enumerate(pmf, 1))
            variance = sum((r-mean)**2*p for r, p in enumerate(pmf, 1))
            if mean != Fraction(n+1, 2) or variance != Fraction(n*n-1, 12)-Fraction(m*(c-1), 6):
                raise ValueError('rank moment failure')
            populations += 1
            for k in range(1, n):
                e = block_expected_catchers(c, m, k)
                if e != expected_colluder_catchers(c, m, k) or e != c*sum(pmf[:k]):
                    raise ValueError(f'block/recursive/CDF disagreement: {(n,c,k)}')
                summary = block_summary(c, m, k)
                if summary != exact_summary(c, m, k):
                    raise ValueError('per-player summary disagreement')
                delta = Fraction(summary['delta']['fraction'])
                sign = 0 if c == 1 or 2*k == n else (1 if 2*k < n else -1)
                if (delta > 0)-(delta < 0) != sign:
                    raise ValueError('quota sign disagreement')
                opposite = Fraction(block_summary(c, m, n-k)['delta']['fraction'])
                if delta != -opposite:
                    raise ValueError('complement quota disagreement')
                cases += 1
    inputs = []
    for filename in observed:
        path = Path(filename)
        raw = path.read_bytes()
        data = json.loads(raw)
        maximum_z, unavailable, checked = 0.0, 0, 0
        for condition in data['conditions']:
            n, c, k = condition['players'], condition['colluders'], condition['catchers']
            if condition.get('strategy') == 'independent':
                baseline = Fraction(n-k, n)
                expected = {key: dict(fraction=str(value), value=float(value)) for key, value in
                            [('p_c', baseline), ('p_n', baseline), ('delta', Fraction(0))]}
            else:
                expected = block_summary(c, n-c, k)
            if expected != condition['exact']:
                raise ValueError(f'saved exact values disagree: {condition["id"]}')
            se = condition['stats']['standard_error']
            if se:
                z = abs(condition['stats']['delta']-expected['delta']['value'])/se
                if z >= 6:
                    raise ValueError(f'observed deviation exceeds audit threshold: {condition["id"]}')
                maximum_z = max(maximum_z, z)
            else:
                unavailable += 1
            checked += 1
        inputs.append(dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), conditions=checked,
                           maximum_deviation_in_standard_errors=maximum_z,
                           zero_standard_error_conditions=unavailable))
    return dict(kind='finite checks of the general block-order theorem', max_players=max_players,
                mixed_populations=populations, quota_conditions=cases,
                checks=['uniform-block closed form vs recursive RPS enumeration', 'rank PMF/CDF and moments',
                        'quota complement and sign, including single-player controls'],
                observed_inputs=inputs, source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                proof='project.md#묶음-순서-모델의-일반적-증명',
                limitation='Finite checks are not a universal proof; ranks are a mathematical extension, not observed throws.')


if __name__ == '__main__':
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description='Reproduce independent block-order model checks')
    parser.add_argument('--max-players', type=int, default=20)
    parser.add_argument('--observed', nargs='*', type=Path, default=[])
    parser.add_argument('--output', type=Path, help='optional new JSON evidence file')
    args = parser.parse_args()
    result = check_block_model(args.max_players, args.observed)
    serialized = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8') as file:
            file.write(serialized)
    print(serialized)
