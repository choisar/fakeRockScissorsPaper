"""Independent games are the sampling units, including for group comparisons."""
from math import sqrt, erfc
from statistics import fmean, variance


def summarize(rows, players, colluders, catchers):
    size = len(rows)
    if size < 2:
        raise ValueError('at least two independent games are required')
    ds = [r['delta'] for r in rows]
    delta = fmean(ds)
    se = sqrt(variance(ds) / size)
    pc = sum(r['survived_c'] for r in rows) / (size * colluders)
    pn = sum(r['survived_n'] for r in rows) / (size * (players - colluders))
    return dict(p_c=pc, p_n=pn, delta=delta, standard_error=se,
                ci95=[delta - 1.96 * se, delta + 1.96 * se] if se else None,
                p_value_normal=erfc(abs(delta) / se / sqrt(2)) if se else None,
                inference_reason=None if se else 'zero_sample_variance',
                baseline=(players-catchers)/players)


def holm_adjust(p_values):
    """Keep the full family size; unavailable tests count as p=1 internally."""
    available = [p if p is not None else 1.0 for p in p_values]
    result = [0.0] * len(p_values)
    previous = 0.0
    for rank, index in enumerate(sorted(range(len(p_values)), key=available.__getitem__)):
        previous = max(previous, min(1.0, (len(p_values)-rank)*available[index]))
        result[index] = previous if p_values[index] is not None else None
    return result
