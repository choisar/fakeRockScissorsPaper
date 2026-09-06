import ast
import contextlib
import io
import json
import math
from itertools import product
from pathlib import Path
from statistics import mean, median, stdev

import test


TRIALS = 1_00000
TOTAL_PLAYER_OPTIONS = (4, 6)
COLLUDER_OPTIONS = (2, 3, 4)
TARGET_CATCHER_OPTIONS = (1, 2)
OUTPUT_FILE = Path(__file__).with_name("results.json")
REPORT_FILE = Path(__file__).with_name("report.html")


def build_conditions():
    return [
        {
            "name": f"총원 {total_players}명 / 담합 {colluders}명 / 술래 {target_catchers}명",
            "total_players": total_players,
            "colluders": colluders,
            "target_catchers": target_catchers,
        }
        for total_players, colluders, target_catchers in product(
            TOTAL_PLAYER_OPTIONS,
            COLLUDER_OPTIONS,
            TARGET_CATCHER_OPTIONS,
        )
        if colluders < total_players and target_catchers < total_players
    ]


CONDITIONS = build_conditions()


def run_game(config):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        test.rock_paper_scissors(config)

    final_line = output.getvalue().splitlines()[-2]
    return ast.literal_eval(final_line.split(": ", 1)[1])


def confidence_interval(values):
    if len(values) < 2:
        return 0.0
    return 1.96 * stdev(values) / math.sqrt(len(values))


def summarize(results, players, colluders):
    survival = {
        player: [player not in catchers for catchers in results]
        for player in players
    }
    player_stats = {
        player: {
            "group": "담합자" if player in colluders else "비담합자",
            "survival_rate": mean(values),
            "median": median(values),
            "confidence_interval": confidence_interval(values),
            "catcher_rate": 1 - mean(values),
        }
        for player, values in survival.items()
    }

    group_stats = {}
    for group_name, group_players in (
        ("담합자", [player for player in players if player in colluders]),
        ("비담합자", [player for player in players if player not in colluders]),
    ):
        values = [
            survival[player][trial]
            for player in group_players
            for trial in range(len(results))
        ]
        group_stats[group_name] = {
            "survival_rate": mean(values) if values else None,
            "median": median(values) if values else None,
            "confidence_interval": confidence_interval(values) if len(values) > 1 else None,
        }

    return {
        "players": player_stats,
        "groups": group_stats,
        "catcher_counts": {
            player: sum(player in catchers for catchers in results)
            for player in players
        },
    }


def run_experiment(config, trials, colluders):
    players = [chr(ord("a") + index) for index in range(config.total_players)]
    results = [run_game(config) for _ in range(trials)]
    return {
        "trials": trials,
        "config": {
            "total_players": config.total_players,
            "colluders": config.colluders,
            "fixed_hand": config.fixed_hand,
            "target_catchers": config.target_catchers,
        },
        "summary": summarize(results, players, colluders),
    }


def build_report(data):
    REPORT_FILE.write_text(
        REPORT_TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False)),
        encoding="utf-8",
    )


def main():
    conditions = {}
    for index, condition in enumerate(CONDITIONS, start=1):
        total_players = condition["total_players"]
        colluders_count = condition["colluders"]
        target_catchers = condition["target_catchers"]
        if not 1 <= colluders_count < total_players:
            raise ValueError(f"조건 {index}: 담합인원은 1명 이상이고 총원보다 적어야 합니다.")
        if not 1 <= target_catchers < total_players:
            raise ValueError(f"조건 {index}: 목표 술래는 1명 이상이고 총원보다 적어야 합니다.")

        experimental_config = test.GameConfig(
            total_players=total_players,
            colluders=colluders_count,
            target_catchers=target_catchers,
        )
        control_config = test.GameConfig(
            total_players=total_players,
            colluders=0,
            target_catchers=target_catchers,
        )
        colluders = {chr(ord("a") + index) for index in range(colluders_count)}
        conditions[f"condition_{index}"] = {
            "name": condition["name"],
            "experimental": run_experiment(experimental_config, TRIALS, colluders),
            "control": run_experiment(control_config, TRIALS, set()),
            "theoretical_control_survival": (total_players - target_catchers) / total_players,
        }

    data = {"conditions": conditions}
    OUTPUT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    build_report(data)
    print(f"완료: {TRIALS:,}회씩 실행했습니다.")
    print(f"결과: {OUTPUT_FILE.name}, {REPORT_FILE.name}")


REPORT_TEMPLATE = r'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>가위바위보 담합 실험 리포트</title>
<style>
:root { --ink:#17221d; --muted:#63736a; --paper:#f5f1e8; --panel:#fffdf8; --green:#1f6f58; --orange:#d46b3b; --line:#d9d7cc; }
* { box-sizing:border-box; }
body { margin:0; color:var(--ink); background:var(--paper); font-family:Georgia, "Malgun Gothic", serif; }
main { max-width:1100px; margin:0 auto; padding:48px 24px 72px; }
header { border-bottom:2px solid var(--ink); padding-bottom:24px; margin-bottom:28px; }
h1 { margin:0 0 10px; font-size:clamp(2rem, 5vw, 4rem); line-height:1; letter-spacing:0; }
p { color:var(--muted); }
.grid { display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:18px; }
.panel { background:var(--panel); border:1px solid var(--line); padding:22px; }
h2 { margin:0 0 18px; font-size:1.25rem; }
.metric { font-size:2.2rem; color:var(--green); font-weight:bold; }
.small { font-size:.9rem; color:var(--muted); }
.bar-row { display:grid; grid-template-columns:100px 1fr 70px; gap:12px; align-items:center; margin:13px 0; }
.bar { height:16px; background:#e8e5da; }
.fill { height:100%; background:var(--green); }
.fill.orange { background:var(--orange); }
table { width:100%; border-collapse:collapse; font-size:.95rem; }
th, td { text-align:left; padding:11px 8px; border-bottom:1px solid var(--line); }
th { color:var(--muted); font-weight:normal; }
.note { border-left:4px solid var(--orange); padding:10px 14px; background:#fff7ef; }
@media (max-width:700px) { main { padding:28px 14px 48px; } .grid { grid-template-columns:1fr; } .bar-row { grid-template-columns:80px 1fr 62px; gap:8px; } }
</style>
</head>
<body>
<main>
<header>
<h1>담합 효과 실험</h1>
<label for="condition-select">조건 선택</label>
<select id="condition-select"></select>
<p id="meta"></p>
</header>
<section class="grid">
<div class="panel"><h2>집단별 생존율</h2><div id="group-bars"></div></div>
<div class="panel"><h2>대조군 기준</h2><div class="metric" id="control-rate"></div><p>이론적 무작위 생존율</p><div class="metric" id="delta"></div><p>실험군 담합자와의 차이</p></div>
</section>
<br>
<section class="panel"><h2>개인별 결과</h2><table><thead><tr><th>플레이어</th><th>집단</th><th>생존율</th><th>중앙값</th><th>95% 신뢰구간</th><th>술래 횟수</th></tr></thead><tbody id="players"></tbody></table></section>
<br>
<section class="panel"><h2>해석</h2><p class="note">신뢰구간은 각 게임에서 생존 여부를 0/1로 두고 계산한 95% 근사 구간입니다. 담합 효과를 판단할 때는 생존율 차이뿐 아니라 신뢰구간의 겹침과 추가 반복 횟수도 함께 확인하세요.</p></section>
</main>
<script>
const data = __DATA__;
const fmt = value => `${(value * 100).toFixed(1)}%`;
const ci = value => `+/- ${(value * 100).toFixed(1)}%`;
const select = document.querySelector('#condition-select');
for (const [id, condition] of Object.entries(data.conditions)) {
    select.insertAdjacentHTML('beforeend', `<option value="${id}">${condition.name}</option>`);
}

function renderCondition(id) {
    const condition = data.conditions[id];
    const exp = condition.experimental;
    const bars = document.querySelector('#group-bars');
    bars.innerHTML = '';
    document.querySelector('#meta').textContent = `${exp.config.total_players}명 중 담합자 ${exp.config.colluders}명 | 술래 ${exp.config.target_catchers}명 | 조건별 ${exp.trials.toLocaleString()}회`;
    for (const [name, stats] of Object.entries(exp.summary.groups)) {
        bars.insertAdjacentHTML('beforeend', `<div class="bar-row"><strong>${name}</strong><div class="bar"><div class="fill ${name === '비담합자' ? 'orange' : ''}" style="width:${stats.survival_rate * 100}%"></div></div><span>${fmt(stats.survival_rate)}</span></div>`);
    }
    const baseline = condition.theoretical_control_survival;
    const delta = exp.summary.groups['담합자'].survival_rate - baseline;
    document.querySelector('#control-rate').textContent = fmt(baseline);
    document.querySelector('#delta').textContent = `${delta >= 0 ? '+' : ''}${fmt(delta)}`;
    const rows = document.querySelector('#players');
    rows.innerHTML = '';
    for (const [player, stats] of Object.entries(exp.summary.players)) {
        rows.insertAdjacentHTML('beforeend', `<tr><td>${player}</td><td>${stats.group}</td><td>${fmt(stats.survival_rate)}</td><td>${fmt(stats.median)}</td><td>${ci(stats.confidence_interval)}</td><td>${exp.summary.catcher_counts[player].toLocaleString()}</td></tr>`);
    }
}

select.addEventListener('change', event => renderCondition(event.target.value));
renderCondition(select.value);
</script>
</body>
</html>'''


if __name__ == "__main__":
    main()
