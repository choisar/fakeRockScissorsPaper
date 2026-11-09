"""Independent games are the sampling units, including for group comparisons."""
from math import sqrt, erfc


def summarize(rows, players, colluders, catchers):
    size = len(rows)
    ds = [r['delta'] for r in rows]
    delta = sum(ds) / size
    variance = sum((d - delta) ** 2 for d in ds) / (size - 1)
    se = sqrt(variance / size)
    pc = sum(r['survived_c'] for r in rows) / (size * colluders)
    pn = sum(r['survived_n'] for r in rows) / (size * (players - colluders))
    return dict(p_c=pc, p_n=pn, delta=delta, standard_error=se,
                ci95=[delta - 1.96 * se, delta + 1.96 * se],
                p_value_normal=erfc(abs(delta) / se / sqrt(2)) if se else (1.0 if delta == 0 else 0.0),
                baseline=(players-catchers)/players)


def holm_adjust(p_values):
    result = [0.0] * len(p_values)
    previous = 0.0
    for rank, index in enumerate(sorted(range(len(p_values)), key=p_values.__getitem__)):
        previous = max(previous, min(1.0, (len(p_values)-rank)*p_values[index]))
        result[index] = previous
    return result
