import numpy as np

RNG = np.random.default_rng()

HANDS = ["가위", "바위", "보"]
BEATS = {
    "가위": "보",
    "바위": "가위",
    "보": "바위"
}

def play_hands(players, fixed_hand=None):
    """
    플레이어 목록의 손 모양을 새로 갱신합니다.
    - 담합자만 남아 있으면 랜덤으로 손을 냄 (무승부 방지)
    - 일반적인 담합자: fixed_hand 지정
    - 일반 플레이어: 무작위 선택
    """
    if players and all(player.get("colludes", False) for player in players):
        for player in players:
            player["hand"] = RNG.choice(HANDS)
        return players

    for player in players:
        if player.get("colludes", False) and fixed_hand:
            player["hand"] = fixed_hand
        else:
            player["hand"] = RNG.choice(HANDS)
    return players

def print_hand_status(players, stage):
    """현재 라운드에서 각 플레이어가 낸 손을 출력합니다."""
    hand_status = ", ".join(f"{player['player']}: {player['hand']}" for player in players)
    print(f"[{stage}] {hand_status}")


def first_round(results):
    """
    가위바위보 1판을 판정하여 (이긴패, 진패, 패배자이름목록)을 반환합니다.
    승패가 나지 않으면 (None, None, []) 반환
    """
    seen_hands = {player["hand"] for player in results}
    if len(seen_hands) != 2:
        return None, None, []

    winning_hand = next(
        hand for hand in seen_hands
        if BEATS[hand] in seen_hands
    )
    losing_hand = BEATS[winning_hand]
    losers = [
        player["player"]
        for player in results
        if player["hand"] == losing_hand
    ]
    return winning_hand, losing_hand, losers

def filter_players_to_exact_count(pool_players, target_count, fixed_hand=None):
    """
    pool_players 중에서 가위바위보를 반복해
    정확히 target_count명의 패배자(이름)를 선출합니다.
    """
    current_pool = [dict(p) for p in pool_players]

    round_no = 1
    while True:
        # 매 판마다 손을 새로 냄
        play_hands(current_pool, fixed_hand)
        print_hand_status(current_pool, f"서브 라운드 {round_no}")
        _, _, losers = first_round(current_pool)
        round_no += 1

        if not losers:
            continue

        # 패배자 수가 목표와 일치할 때
        if len(losers) == target_count:
            return losers

        # 패배자가 목표보다 많을 때: 패배자들끼리 좁혀서 재경기
        elif len(losers) > target_count:
            current_pool = [p for p in current_pool if p["player"] in losers]

        # 패배자가 목표보다 적을 때: 나온 패배자는 확정, 부족분은 생존자들 중에서 추가 선출
        else:
            confirmed_losers = losers
            needed = target_count - len(confirmed_losers)
            survivors = [p for p in current_pool if p["player"] not in losers]
            
            additional_losers = filter_players_to_exact_count(survivors, needed, fixed_hand)
            return confirmed_losers + additional_losers

def rock_paper_scissors():
    total_players = 6
    colluders = 2
    fixed_hand = "바위"
    target_catchers = 2

    # 1. 초기 플레이어 생성 (hand 할당 제거 및 colluders 수 기반 동적 생성)
    results = [
        {"player": chr(ord("a") + i), "colludes": i < colluders}
        for i in range(total_players)
    ]

    # 2. 첫 라운드 진행 (손 부여 및 승패 판정)
    round_no = 1
    while True:
        play_hands(results, fixed_hand)
        print_hand_status(results, f"1차전 라운드 {round_no}")
        winning_hand, losing_hand, candidates = first_round(results)
        round_no += 1
        if candidates:
            break

    print(f"[1차전 결과] 승: {winning_hand}, 패: {losing_hand}, 초기 패배자: {candidates}")

    # 3. 목표 술래 인원(target_catchers) 맞추기
    if len(candidates) > target_catchers:
        loser_pool = [p for p in results if p["player"] in candidates]
        candidates = filter_players_to_exact_count(loser_pool, target_catchers, fixed_hand)

    elif len(candidates) < target_catchers:
        needed_count = target_catchers - len(candidates)
        survivor_pool = [p for p in results if p["player"] not in candidates]
        additional_catchers = filter_players_to_exact_count(survivor_pool, needed_count, fixed_hand)
        candidates.extend(additional_catchers)

    print(f"최종 술래 목록 (정확히 {target_catchers}명): {candidates}")
    print("게임을 종료합니다.")

if __name__ == "__main__":
    rock_paper_scissors()