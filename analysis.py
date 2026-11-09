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


def analyze_log(path, players, colluders, catchers, on_game=None):
    """Build every observed aggregate from saved throws, never from exact probabilities."""
    import gzip
    import json
    from collections import defaultdict

    rows, counts = [], [0] * players
    branches, states = {}, defaultdict(lambda: dict(visits=0, caught_c=0, caught_n=0, safe_c=0, safe_n=0))
    hand_counts = [[0, 0, 0], [0, 0, 0]]
    active_pairs, same_pairs, throws, draws, released_throws = 0, 0, 0, 0, 0
    events, first = [], None
    with gzip.open(path, 'rt', encoding='utf-8') as file:
        for line in file:
            record = json.loads(line)
            if record['game'] != len(rows):
                raise ValueError('nonsequential game ID')
            if record['type'] == 'event':
                event = record['event']
                if record['index'] != len(events):
                    raise ValueError('nonsequential event index')
                events.append(event)
                if first is None and event['branch'] != 'draw':
                    first = event
                pc = sum(p < colluders for p in event['pool'])
                state = states[(pc, len(event['pool'])-pc, event['remaining'], event['branch'], event['released'])]
                state['visits'] += 1
                for name, people in [('caught', event['new_catchers']), ('safe', event['new_survivors'])]:
                    c = sum(p < colluders for p in people)
                    state[name+'_c'] += c
                    state[name+'_n'] += len(people)-c
                if event['kind'] == 'throw':
                    throws += 1
                    draws += event['branch'] == 'draw'
                    released_throws += event['released']
                    group_hands = []
                    for p, hand in zip(event['pool'], event['hands']):
                        hand_counts[int(p >= colluders)][hand] += 1
                        if p < colluders:
                            group_hands.append(hand)
                    if not event['released']:
                        for i, hand in enumerate(group_hands):
                            for other in group_hands[i+1:]:
                                active_pairs += 1
                                same_pairs += hand == other
            elif record['type'] == 'result':
                if not events or not events[-1]['terminal'] or first is None:
                    raise ValueError('incomplete game log')
                caught = record['catchers']
                if len(caught) != catchers or len(set(caught)) != catchers or any(not 0 <= p < players for p in caught):
                    raise ValueError('invalid final catchers')
                if on_game:
                    on_game(len(rows), events, caught)
                for p in caught:
                    counts[p] += 1
                sc = colluders-sum(p < colluders for p in caught)
                sn = players-colluders-sum(p >= colluders for p in caught)
                delta = sc/colluders-sn/(players-colluders)
                rows.append(dict(survived_c=sc, survived_n=sn, delta=delta))
                bucket = branches.setdefault(first['branch'], dict(count=0, sum_delta=0.0,
                    immediate_caught_c=0, immediate_caught_n=0, immediate_safe_c=0, immediate_safe_n=0,
                    samples=[]))
                bucket['count'] += 1
                bucket['sum_delta'] += delta
                for name, people in [('caught', first['new_catchers']), ('safe', first['new_survivors'])]:
                    c = sum(p < colluders for p in people)
                    bucket['immediate_'+name+'_c'] += c
                    bucket['immediate_'+name+'_n'] += len(people)-c
                if len(bucket['samples']) < 2:
                    bucket['samples'].append(dict(game=record['game'], events=events, catchers=caught))
                events, first = [], None
            else:
                raise ValueError('unknown log record')
    if events:
        raise ValueError('truncated game log')
    trials = len(rows)
    observed = []
    for branch, bucket in sorted(branches.items()):
        observed.append(dict(branch=branch, **bucket, frequency=bucket['count']/trials,
                             mean_delta=bucket['sum_delta']/bucket['count'],
                             contribution=bucket['sum_delta']/trials))
    return dict(trials=trials, stats=summarize(rows, players, colluders, catchers),
                individual_survival=[1-count/trials for count in counts], observed_branches=observed,
                observed_states=[dict(pool_c=key[0], pool_n=key[1], remaining=key[2], branch=key[3],
                                      released=key[4], **value) for key, value in sorted(states.items())],
                throws=throws, draws=draws, released_throws=released_throws,
                hand_counts=hand_counts, same_hand_pairs=same_pairs, eligible_pairs=active_pairs)
