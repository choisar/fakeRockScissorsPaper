"""Game engine; standard library only. Hands: rock=0, scissors=1, paper=2."""
from dataclasses import dataclass
from random import Random


@dataclass(frozen=True)
class GameConfig:
    total_players: int = 6
    colluders: int = 2
    target_catchers: int = 2
    strategy: str = 'fixed'

    def __post_init__(self):
        if not 2 <= self.total_players <= 20:
            raise ValueError('total_players must be between 2 and 20')
        if not 0 <= self.colluders <= self.total_players:
            raise ValueError('colluders must be between 0 and total_players')
        if not 1 <= self.target_catchers < self.total_players:
            raise ValueError('target_catchers must be between 1 and total_players-1')
        if self.strategy not in ('fixed', 'shared_random', 'independent'):
            raise ValueError('unknown strategy')


def play_game(config, rng=None, trace=False, on_event=None):
    rng = rng if rng is not None else Random()
    pool = list(range(config.total_players))
    selected, events = [], []
    def emit(event):
        if trace:
            events.append(event)
        if on_event is not None:
            on_event(event)
    while len(selected) < config.target_catchers:
        needed = config.target_catchers - len(selected)
        if needed == len(pool):
            selected.extend(pool)
            if trace or on_event is not None:
                emit(dict(pool=pool, hands=[], released=False, losers=pool,
                                   action='남은 참가자 전원을 술래로 확정, 선정 종료',
                                   next_pool=None, selected=selected.copy(), terminal=True,
                                   kind='automatic', branch='automatic', remaining=needed,
                                   new_catchers=pool.copy(), new_survivors=[]))
            break
        release = config.strategy != 'independent' and all(p < config.colluders for p in pool)
        shared = rng.randrange(3) if config.strategy == 'shared_random' and not release else 0
        hands = [rng.randrange(3) if release or p >= config.colluders or config.strategy == 'independent'
                 else shared for p in pool]
        seen = set(hands)
        losers = []
        if len(seen) == 2:
            winning = next(h for h in seen if (h + 1) % 3 in seen)
            losers = [p for p, h in zip(pool, hands) if h == (winning + 1) % 3]
        before = pool
        new_catchers, new_survivors = [], []
        if not losers:
            branch = 'draw'
            action = '무승부: 동일 참가자로 재투구'
        elif len(losers) > needed:
            branch = 'excess'
            new_survivors = [p for p in pool if p not in losers]
            pool = losers
            action = '패자 과다: 승자는 생존 확정, 패자끼리 재선정'
        elif len(losers) == needed:
            branch = 'equal'
            new_catchers = losers.copy()
            new_survivors = [p for p in pool if p not in losers]
            selected.extend(losers)
            pool = None
            action = '패자를 술래로 확정, 선정 종료'
        else:
            branch = 'shortfall'
            new_catchers = losers.copy()
            selected.extend(losers)
            pool = [p for p in pool if p not in losers]
            action = '패자를 술래로 확정, 부족한 정원은 직전 승자에서 선정'
        if trace or on_event is not None:
            emit(dict(pool=before, hands=hands, released=release,
                               losers=losers, action=action, next_pool=pool,
                               selected=selected.copy(), terminal=pool is None,
                               kind='throw', branch=branch, remaining=needed,
                               new_catchers=new_catchers, new_survivors=new_survivors))
    return dict(catchers=sorted(selected), events=events)
