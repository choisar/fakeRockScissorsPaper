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
                 next_state=[lc, ln, k] if lc + ln >= k
                 else [c-lc, n-ln, k-lc-ln],
                 confirmed_c=0 if lc + ln >= k else lc)
            for lc, ln, w in valid]
