"""Offline HTML report; embedded data, no external dependencies."""
import json


def build_report(data, output):
    output.write_text(TEMPLATE.replace('__DATA__',json.dumps(data,ensure_ascii=False).replace('<','\\u003c')),encoding='utf-8')


TEMPLATE = r'''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>같은 손을 내면 더 유리할까?</title><style>
:root{font-family:system-ui,'Malgun Gothic',sans-serif;color:#193c35;background:#f5f4ee}*{box-sizing:border-box}body{margin:0}main{max-width:1120px;margin:auto;padding:44px 24px}h1{font-size:clamp(28px,5vw,48px);letter-spacing:-2px;margin:12px 0}h2{font-size:21px}p{line-height:1.8}.eyebrow{font-size:12px;letter-spacing:2px;color:#526d64}.muted,small{color:#586b64}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.card{background:white;border:1px solid #dce3dc;border-radius:16px;padding:24px;margin:18px 0}select{font:inherit;padding:12px;border:1px solid #9fb6a9;border-radius:8px;max-width:100%}.metric{font-size:40px;font-weight:750;color:#1c7258}.bar{display:flex;align-items:center;gap:12px;margin:20px 0}.track{flex:1;background:#edf1e9;height:18px}.fill{height:100%;background:#22775f}.orange{background:#cc7743}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:12px 8px;text-align:left;border-bottom:1px solid #e4e9e3;white-space:nowrap}.scroll{overflow:auto}.note{padding:16px;border-left:4px solid #cc7743;background:#fff6ec}.mini{height:12px;display:block;background:#22775f;min-width:1px}.step{border-left:3px solid #a8c6b5;padding:8px 16px;margin:10px 0;font-size:14px}a{color:#176b52}button{padding:8px;font:inherit;cursor:pointer}footer{font-size:13px;margin-top:32px}@media(max-width:700px){.grid{grid-template-columns:1fr;gap:0}main{padding:24px 16px}.card{padding:18px}.metric{font-size:32px}}
</style><main><div class="eyebrow">QUESTION → EXPERIMENT → EXPLANATION</div><h1>같은 손을 내면 더 유리할까?</h1>
<p>빠더너스의 비용 내기 가위바위보를 보고 생긴 질문.<br>담합자 한 명은 비담합자 한 명보다 술래를 피할 확률이 높을까?</p>
<p><a href="https://youtu.be/YJckrnOUaoM" target="_blank" rel="noreferrer">질문의 계기가 된 영상 ↗</a> <small>사용자 제공 출처. 영상과 실험 규칙의 일치는 확인하지 않았습니다.</small></p>
<label for="condition">실험 조건 </label><select id="condition"></select><p class="muted" id="meta"></p>
<div class="grid"><section class="card"><h2>집단별 개인 평균 생존율</h2><div id="bars"></div><p class="muted">생존 = 최종 술래로 선정되지 않음. 집단 전체의 생존 확률이 아닙니다.</p></section>
<section class="card"><h2>담합자 − 비담합자</h2><div class="metric" id="delta"></div><p id="ci"></p><p id="exact"></p><p class="muted" id="significance"></p></section></div>
<section class="card"><h2>모든 조건 비교</h2><p>막대는 정확 계산한 개인 생존율 차이입니다. 행을 선택하면 상세 조건이 바뀝니다.</p><div class="scroll"><table><thead><tr><th>참가/담합/술래</th><th>관측 차이</th><th>정확 차이</th><th>차이 비교</th></tr></thead><tbody id="comparison"></tbody></table></div></section>
<section class="card"><h2>왜 차이가 생길까?</h2><p>담합자는 같은 손을 내므로 함께 이기거나 집니다. 패자 수와 남은 정원의 관계에 따라 다음 참가자 집합이 바뀌어 최종 확률이 달라집니다. 손 하나의 승패 대칭성만으로 최종 생존 확률의 동등성을 보장할 수 없습니다.</p><p id="explanation"></p><h3>첫 유효 투구의 분기</h3><p class="muted">무승부를 제외한 조건부 확률. 다음 상태는 (남은 담합자, 남은 비담합자, 남은 술래 정원)입니다.</p><div class="scroll"><table><thead><tr><th>패자: 담합/비담합</th><th>분기 확률</th><th>이번 확정 담합 술래</th><th>다음 상태</th></tr></thead><tbody id="branches"></tbody></table></div></section>
<section class="card"><h2>개인별 점검과 대조군</h2><p id="baseline"></p><div class="scroll"><table><thead><tr><th>참가자</th><th>실험 집단</th><th>실험 생존율</th><th>전원 무작위 대조군</th></tr></thead><tbody id="individuals"></tbody></table></div></section>
<section class="card"><h2>게임 한 번 따라가기</h2><p class="muted">분석 실험과 분리된 시드로 만든 예시입니다. 참가자 번호는 1부터 시작합니다.</p><details><summary>투구별 기록 보기</summary><div id="trace"></div></details></section>
<section class="card"><h2>분석 방법과 적용 범위</h2><p>게임별 두 집단의 생존 비율 차이를 구하고, 독립 게임들 사이의 표준오차로 점별 95% 정규 근사 신뢰구간을 계산했습니다. 여러 조건의 양측 정규 근사 검정에는 Holm 보정을 적용했습니다. 신뢰구간 자체는 동시 신뢰구간이 아닙니다.</p><p>정확 계산은 비담합자의 손 개수를 다항분포로 열거하고, 상태 전이마다 기대 술래 인원을 유리수로 계산합니다. 무승부는 유효 투구로 조건화합니다. 손 판정은 시뮬레이션과 별도로 구현했습니다.</p><div class="note">비담합자는 매번 독립·균등 선택, 담합자는 바위 고정입니다. 담합자만 남으면 무작위로 전환합니다. 실제 사람의 심리·학습·영상의 세부 규칙까지 설명하는 모델은 아닙니다.</div><details><summary>재현 정보</summary><pre id="metadata" style="white-space:pre-wrap;overflow-wrap:anywhere"></pre></details></section>
<footer>초기 예상 → 조건별 차이 관측 → 정확 확률과 분기로 원인 확인</footer></main>
<script>const data=__DATA__;
const $=id=>document.getElementById(id),pct=x=>(100*x).toFixed(2)+'%',pp=x=>(100*x).toFixed(2)+'%p';
const label=c=>`${c.players}명 / 담합 ${c.colluders}명 / 술래 ${c.catchers}명`;
data.conditions.forEach((c,i)=>{const o=document.createElement('option');o.value=i;o.textContent=label(c);$('condition').append(o);const tr=document.createElement('tr');tr.innerHTML=`<td><button data-index="${i}">${label(c)}</button></td><td>${pp(c.stats.delta)}</td><td>${pp(c.exact.delta.value)}</td><td><span class="mini" style="width:${Math.abs(c.exact.delta.value)*180}px"></span></td>`;$('comparison').append(tr)});
$('comparison').addEventListener('click',e=>{const b=e.target.closest('button');if(b){$('condition').value=b.dataset.index;render()}});
function render(){const c=data.conditions[Number($('condition').value)],s=c.stats,x=c.exact;
$('meta').textContent=`실험군·대조군 각 ${c.trials.toLocaleString()}게임 · 시드 ${c.seed}`;
$('bars').innerHTML=[['담합자',s.p_c,''],['비담합자',s.p_n,'orange']].map(([n,v,cl])=>`<div class="bar"><strong>${n}</strong><div class="track"><div class="fill ${cl}" style="width:${v*100}%"></div></div><span>${pct(v)}</span></div>`).join('');
$('delta').textContent=pp(s.delta);$('ci').textContent=`95% 신뢰구간: ${pp(s.ci95[0])} ~ ${pp(s.ci95[1])}`;
$('exact').textContent=`정확 계산: ${x.delta.fraction} = ${pp(x.delta.value)}`;
$('significance').textContent=`Holm 보정 p = ${s.p_value_holm.toExponential(2)}. ${x.delta.value===0?'정확 계산에서도 차이가 0입니다.':'차이의 크기와 정확 계산값을 함께 확인하세요.'}`;
$('explanation').textContent=`정확 생존율: 담합자 ${x.p_c.fraction} (${pct(x.p_c.value)}), 비담합자 ${x.p_n.fraction} (${pct(x.p_n.value)}). 각 분기의 확률과 이후 상태의 기대 술래 인원을 합산한 결과입니다.`;
$('branches').innerHTML=c.first_branches.map(b=>`<tr><td>${b.losing_c} / ${b.losing_n}</td><td>${b.probability}</td><td>${b.confirmed_c}</td><td>(${b.next_state.join(', ')})</td></tr>`).join('');
$('baseline').textContent=`전원 무작위 이론 생존율: ${pct(s.baseline)}. 술래 총원 고정으로 대조군 전체 평균은 항상 이 값이며, 개인별 결과를 점검해야 합니다.`;
$('individuals').innerHTML=c.individual_survival.map((v,i)=>`<tr><td>${i+1}</td><td>${i<c.colluders?'담합':'비담합'}</td><td>${pct(v)}</td><td>${pct(c.control_individual_survival[i])}</td></tr>`).join('');
$('trace').innerHTML=c.sample_game.events.map((t,i)=>`<div class="step"><strong>투구 ${i+1}</strong> ${t.released?'· 담합 해제':''}<br>${t.pool.map((p,j)=>`${p+1}: ${['바위','가위','보'][t.hands[j]]}`).join(' / ')}<br>${t.action}<br>확정 술래: ${t.selected.map(p=>p+1).join(', ')||'없음'}</div>`).join('')+`<p>최종 술래: ${c.sample_game.catchers.map(p=>p+1).join(', ')}</p>`;
} $('condition').addEventListener('change',render);$('metadata').textContent=JSON.stringify(data.metadata,null,2);render();</script></html>'''
