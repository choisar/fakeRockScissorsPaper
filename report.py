"""Offline HTML report; embedded data, no external dependencies."""
import json


def build_report(data, output):
    template = THROW_TEMPLATE if data.get('mode') == 'throw-analysis' else TEMPLATE
    output.write_text(template.replace('__DATA__',json.dumps(data,ensure_ascii=False).replace('<','\\u003c')),encoding='utf-8')


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
<section class="card"><h2>왜 차이가 생길까?</h2><p>담합자는 같은 손을 내므로 함께 이기거나 집니다. 패자 수와 남은 정원의 관계에 따라 다음 참가자 집합이 바뀌어 최종 확률이 달라집니다. 손 하나의 승패 대칭성만으로 최종 생존 확률의 동등성을 보장할 수 없습니다.</p><p id="explanation"></p><h3>첫 유효 투구의 분기</h3><p class="muted">무승부를 제외한 조건부 확률. 다음 상태는 (남은 담합자, 남은 비담합자, 남은 술래 정원)이며 정원이 채워지면 선정 종료입니다.</p><div class="scroll"><table><thead><tr><th>패자: 담합/비담합</th><th>분기 확률</th><th>이번 확정 담합 술래</th><th>다음 상태</th></tr></thead><tbody id="branches"></tbody></table></div></section>
<section class="card"><h2>개인별 점검과 대조군</h2><p id="baseline"></p><div class="scroll"><table><thead><tr><th>참가자</th><th>실험 집단</th><th>실험 생존율</th><th>전원 무작위 대조군</th></tr></thead><tbody id="individuals"></tbody></table></div></section>
<section class="card"><h2>게임 한 번 따라가기</h2><p class="muted">분석 실험과 분리된 시드로 만든 예시입니다. 참가자 번호는 1부터 시작합니다.</p><details><summary>투구별 기록 보기</summary><div id="trace"></div></details></section>
<section class="card"><h2>분석 방법과 적용 범위</h2><p>게임별 두 집단의 생존 비율 차이를 구하고, 독립 게임들 사이의 표준오차로 점별 95% 정규 근사 신뢰구간을 계산했습니다. 여러 조건의 양측 정규 근사 검정에는 Holm 보정을 적용했습니다. 신뢰구간 자체는 동시 신뢰구간이 아닙니다. 표본분산이 0이면 신뢰구간·p값은 제공하지 않으며, Holm 보정에는 내부적으로 p=1로 포함해 전체 비교 수를 유지합니다. 정규 근사는 소표본의 정확한 검정을 보장하지 않습니다.</p><p>정확 계산은 비담합자의 손 개수를 다항분포로 열거하고, 상태 전이마다 기대 술래 인원을 유리수로 계산합니다. 무승부는 유효 투구로 조건화합니다. 손 판정은 시뮬레이션과 별도로 구현했습니다.</p><div class="note">비담합자는 매번 독립·균등 선택, 담합자는 바위 고정입니다. 실제 사람의 심리·학습·영상의 세부 규칙까지 설명하는 모델은 아닙니다. 담합자만 남으면 무작위로 전환합니다.</div><details><summary>재현 정보</summary><pre id="metadata" style="white-space:pre-wrap;overflow-wrap:anywhere"></pre></details></section>
<footer>초기 예상 → 조건별 차이 관측 → 정확 확률과 분기로 원인 확인</footer></main>
<script>const data=__DATA__;
const $=id=>document.getElementById(id),pct=x=>(100*x).toFixed(2)+'%',pp=x=>(100*x).toFixed(2)+'%p';
const pvalue=p=>p===null?'계산 불가':p===0?'< 1e-300':p.toExponential(2);
const label=c=>`${c.players}명 / 담합 ${c.colluders}명 / 술래 ${c.catchers}명`;
data.conditions.forEach((c,i)=>{const o=document.createElement('option');o.value=i;o.textContent=label(c);$('condition').append(o);const tr=document.createElement('tr');tr.innerHTML=`<td><button data-index="${i}">${label(c)}</button></td><td>${pp(c.stats.delta)}</td><td>${pp(c.exact.delta.value)}</td><td><span class="mini" style="width:${Math.abs(c.exact.delta.value)*180}px"></span></td>`;$('comparison').append(tr)});
$('comparison').addEventListener('click',e=>{const b=e.target.closest('button');if(b){$('condition').value=b.dataset.index;render()}});
function render(){const c=data.conditions[Number($('condition').value)],s=c.stats,x=c.exact;
$('meta').textContent=`실험군·대조군 각 ${c.trials.toLocaleString()}게임 · 시드 ${c.seed}`;
$('bars').innerHTML=[['담합자',s.p_c,''],['비담합자',s.p_n,'orange']].map(([n,v,cl])=>`<div class="bar"><strong>${n}</strong><div class="track"><div class="fill ${cl}" style="width:${v*100}%"></div></div><span>${pct(v)}</span></div>`).join('');
$('delta').textContent=pp(s.delta);$('ci').textContent=s.ci95===null?'표본 변동이 없어 정규 근사 추론 불가':`95% 신뢰구간: ${pp(s.ci95[0])} ~ ${pp(s.ci95[1])}`;
$('exact').textContent=`정확 계산: ${x.delta.fraction} = ${pp(x.delta.value)}`;
$('significance').textContent=`Holm 보정 p = ${pvalue(s.p_value_holm)}. ${x.delta.value===0?'정확 계산에서도 차이가 0입니다.':'차이의 크기와 정확 계산값을 함께 확인하세요.'}`;
$('explanation').textContent=`정확 생존율: 담합자 ${x.p_c.fraction} (${pct(x.p_c.value)}), 비담합자 ${x.p_n.fraction} (${pct(x.p_n.value)}). 각 분기의 확률과 이후 상태의 기대 술래 인원을 합산한 결과입니다.`;
$('branches').innerHTML=c.first_branches.map(b=>`<tr><td>${b.losing_c} / ${b.losing_n}</td><td>${b.probability}</td><td>${b.confirmed_c}</td><td>${b.terminal?'선정 종료':`(${b.next_state.join(', ')})`}</td></tr>`).join('');
$('baseline').textContent=`전원 무작위 이론 생존율: ${pct(s.baseline)}. 술래 총원 고정으로 대조군 전체 평균은 항상 이 값이며, 개인별 결과를 점검해야 합니다.`;
$('individuals').innerHTML=c.individual_survival.map((v,i)=>`<tr><td>${i+1}</td><td>${i<c.colluders?'담합':'비담합'}</td><td>${pct(v)}</td><td>${pct(c.control_individual_survival[i])}</td></tr>`).join('');
$('trace').innerHTML=c.sample_game.events.map((t,i)=>`<div class="step"><strong>투구 ${i+1}</strong> ${t.released?'· 담합 해제':''}<br>${t.pool.map((p,j)=>`${p+1}: ${['바위','가위','보'][t.hands[j]]}`).join(' / ')}<br>${t.action}<br>확정 술래: ${t.selected.map(p=>p+1).join(', ')||'없음'}</div>`).join('')+`<p>최종 술래: ${c.sample_game.catchers.map(p=>p+1).join(', ')}</p>`;
} $('condition').addEventListener('change',render);$('metadata').textContent=JSON.stringify(data.metadata,null,2);render();</script></html>'''


# Reuse the existing report's stylesheet; this view owns only observed-throw presentation.
THROW_TEMPLATE = r'''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>선택의 결합은 어느 분기에서 차이를 만들까?</title><style>__BASE_STYLE__
.controls{display:flex;gap:18px;flex-wrap:wrap;align-items:center}.participant{display:inline-block;padding:8px;margin:4px;border:2px solid #cc7743;border-radius:8px}.focal{border-color:#22775f;background:#e4f2e8}.plot{width:100%;height:auto}input[type=range]{max-width:100%}.legend{display:flex;gap:16px;flex-wrap:wrap}pre{white-space:pre-wrap;overflow-wrap:anywhere}button:disabled{opacity:.4}.status{font-size:18px;font-weight:650}svg text{font:13px system-ui}
</style><main><div class="eyebrow">OBSERVED THROWS → BRANCHES → OUTCOMES</div>
<h1>선택의 결합은 어느 분기에서 차이를 만들까?</h1>
<p>실제로 실행한 모든 투구를 저장한 뒤 다시 읽어 집계했습니다. 비교집단은 참가자 1번부터 지정 인원까지이며, 독립 선택에서도 같은 집단을 비교합니다.</p>
<section class="card"><div class="controls"><label>참가자 / 비교집단 <select id="population"></select></label><label>선택 방식 <select id="strategy"><option value="fixed">같은 손 고정</option><option value="shared_random" selected>공동 무작위 선택</option><option value="independent">독립 무작위 선택</option></select></label><label>술래 <input id="quota" type="range" min="1" max="5" value="2"><output id="quota-label"></output></label></div><p id="meta"></p>
<div class="grid"><div><h2>관측 개인 생존율</h2><div id="bars"></div></div><div><h2>비교집단 − 나머지 집단</h2><div class="metric" id="delta"></div><p id="ci"></p><p id="significance"></p><p id="exact" class="muted"></p></div></div></section>
<section class="card"><h2>술래 정원을 바꾸면 관측 차이가 어떻게 변할까?</h2><p>점과 연결선은 실제 게임의 평균 차이, 세로선은 게임 단위 95% 정규 근사 신뢰구간입니다. 선은 관측점 사이를 연결한 것이며 이론 곡선이 아닙니다.</p><div class="legend"><span style="color:#22775f">● 같은 손 고정</span><span style="color:#b86328">● 공동 무작위</span><span style="color:#6061a5">● 독립 무작위</span></div><svg id="effects" class="plot" viewBox="0 0 760 300" role="img" aria-label="술래 정원별 관측 생존율 차이와 신뢰구간"></svg></section>
<section class="card"><h2>다른 인원 구성에서도 관측 구조가 유지될까?</h2><p>선택한 전략의 모든 참가자·비교집단 조합입니다. 각 버튼은 실제 정원별 관측 차이이며 눌러 상세 기록으로 이동합니다. 녹색은 점별 95% 구간 전체가 양수, 주황색은 전체가 음수, 회색은 0을 포함합니다. 이 표는 다중 비교 보정 판정이 아니며 회색을 효과 없음으로 해석하지 않습니다.</p><div class="scroll"><table><thead><tr><th>전체 / 비교집단</th><th>술래가 절반 미만</th><th>정확히 절반</th><th>절반 초과</th></tr></thead><tbody id="coverage"></tbody></table></div></section>
<section class="card"><h2>첫 유효 투구: 어느 경로가 전체 차이를 구성했나?</h2><p id="branch-denominator"></p><p>즉시 확정 인원은 해당 분기 게임당 평균입니다. 기여도 = 발생 비율 × 해당 경로의 최종 평균 차이. 이 분해는 관측 경로의 구성이며, 분기 자체의 인과 효과를 뜻하지 않습니다.</p><div class="scroll"><table><thead><tr><th>분기</th><th>게임 수 / 비율</th><th>즉시 술래: 비교 / 나머지</th><th>즉시 생존: 비교 / 나머지</th><th>최종 차이</th><th>전체 차이에 대한 기여</th><th>실제 게임</th></tr></thead><tbody id="branches"></tbody></table></div><p id="contribution-sum" class="status"></p><h3>이 경로는 왜 유리하거나 불리할까?</h3><p id="mechanism"></p><p id="mechanism-numbers"></p><p class="muted">아래 실제 게임은 경로를 읽기 위한 예시입니다. 분기 평균은 예시 두 게임이 아닌 전체 해당 게임에서 계산합니다.</p></section>
<section class="card"><h2>실제 투구 따라가기</h2><p>위 분기를 선택하거나 실제 기록에서 보존한 게임을 고르세요. 모든 표시는 해당 게임의 기록입니다.</p><div class="controls"><select id="game"></select><button id="previous">이전 투구</button><button id="next">다음 투구</button></div><p id="game-meta"></p><div id="hands"></div><p id="event-outcome" class="status"></p><p id="transition"></p><p id="final"></p></section>
<section class="card"><h2>전체 투구에서 관측한 선택과 상태 전이</h2><p id="throws"></p><p id="agreement"></p><div class="scroll"><table><thead><tr><th>집단</th><th>바위</th><th>가위</th><th>보</th><th>실제 손 기록 수</th></tr></thead><tbody id="hands-summary"></tbody></table></div><details><summary>후속 투구를 포함한 상태별 집계</summary><p>횟수의 분모는 게임이 아닌 해당 상태의 이벤트 방문 수입니다. 무승부 재방문과 담합 해제 상태를 구분합니다.</p><div class="scroll"><table><thead><tr><th>남은 비교/나머지/정원</th><th>분기</th><th>담합 해제</th><th>방문 수</th><th>확정 술래: 비교/나머지</th><th>확정 생존: 비교/나머지</th></tr></thead><tbody id="states"></tbody></table></div></details></section>
<section class="card"><h2>원자료와 검증 범위</h2><p><a id="raw">전체 압축 투구 원자료</a> — 원자료는 로컬 재현 명령으로 생성합니다. Git에는 요약과 리포트를 보관합니다.</p><p>공동 무작위와 독립 무작위는 개인별 손 선택 확률을 각각 1/3로 유지하면서 선택의 결합을 바꿉니다. 공동 선택 집단만 남으면 독립 선택으로 전환합니다. 게임은 최종 술래만 관측하므로 전체 순위 분포를 관측값으로 표시하지 않습니다.</p><p>정확 계산값은 검산용입니다. 분산 0이면 추론 불가로 표시합니다. 여러 조건의 p값에는 한 실행 전체의 Holm 보정을 적용하며 신뢰구간은 점별 구간입니다. 실제 인간의 전략·학습·영상 규칙까지 일반화하지 않습니다.</p><details><summary>실행 정보</summary><pre id="metadata"></pre></details></section></main>
<script>const data=__DATA__;
const $=id=>document.getElementById(id),pct=x=>(100*x).toFixed(2)+'%',pp=x=>(100*x).toFixed(2)+'%p';
const labels={draw:'무승부',excess:'패자 과다',equal:'정원 일치',shortfall:'패자 미달',automatic:'자동 확정'};
const colors={fixed:'#22775f',shared_random:'#b86328',independent:'#6061a5'};
const populations=[...new Set(data.conditions.map(c=>`${c.players}/${c.colluders}`))];
for(const value of populations){const o=document.createElement('option');o.value=value;o.textContent=value;$('population').append(o)}
let current,samples=[],sampleIndex=0,step=0;
function chosen(){const [n,c]=$('population').value.split('/').map(Number);return data.conditions.filter(r=>r.players===n&&r.colluders===c)}
function drawEffects(){const records=chosen(),quotas=[...new Set(records.map(c=>c.catchers))].sort((a,b)=>a-b), bound=Math.max(.05,...records.flatMap(c=>c.stats.ci95||[c.stats.delta]).map(Math.abs))*1.15;
const x=k=>65+(k-quotas[0])/Math.max(1,quotas.at(-1)-quotas[0])*630,y=v=>140-v/bound*110;
let svg=`<line x1="65" y1="${y(0)}" x2="695" y2="${y(0)}" stroke="#899e91"/><line x1="65" y1="25" x2="65" y2="255" stroke="#899e91"/>`;
for(const v of [-bound,0,bound])svg+=`<text x="5" y="${y(v)+4}">${pp(v)}</text>`;
for(const k of quotas)svg+=`<text x="${x(k)-6}" y="278">${k}명</text>`;
for(const strategy of Object.keys(colors)){const points=records.filter(c=>c.strategy===strategy).sort((a,b)=>a.catchers-b.catchers),color=colors[strategy];svg+=`<polyline fill="none" stroke="${color}" points="${points.map(c=>`${x(c.catchers)},${y(c.stats.delta)}`).join(' ')}"/>`;for(const c of points){if(c.stats.ci95)svg+=`<line x1="${x(c.catchers)}" x2="${x(c.catchers)}" y1="${y(c.stats.ci95[0])}" y2="${y(c.stats.ci95[1])}" stroke="${color}" stroke-width="3"/>`;svg+=`<circle cx="${x(c.catchers)}" cy="${y(c.stats.delta)}" r="4" fill="${color}"><title>${c.strategy}: 술래 ${c.catchers}명, ${pp(c.stats.delta)}</title></circle>`}}
$('effects').innerHTML=svg;}
function renderCoverage(){const strategy=$('strategy').value;const group=(n,c)=>data.conditions.filter(r=>r.players===n&&r.colluders===c&&r.strategy===strategy).sort((a,b)=>a.catchers-b.catchers);const cell=records=>records.map(c=>{const ci=c.stats.ci95,color=ci&&ci[0]>0?'#22775f':ci&&ci[1]<0?'#b86328':'#586b64';const interval=ci?`${pp(ci[0])} ~ ${pp(ci[1])}`:'추론 불가';return `<button data-record="${c.id}" style="color:${color}" title="95% 구간 ${interval}">${c.catchers}명: ${pp(c.stats.delta)}</button>`}).join(' ')||'해당 없음';$('coverage').innerHTML=populations.map(p=>{const [n,c]=p.split('/').map(Number),records=group(n,c);return `<tr><td>${n} / ${c}${c===1?' · 결합 없는 대조':''}</td><td>${cell(records.filter(r=>2*r.catchers<n))}</td><td>${cell(records.filter(r=>2*r.catchers===n))}</td><td>${cell(records.filter(r=>2*r.catchers>n))}</td></tr>`}).join('');}
$('coverage').addEventListener('click',e=>{const button=e.target.closest('button');if(button){const c=data.conditions.find(c=>c.id===button.dataset.record);$('population').value=`${c.players}/${c.colluders}`;$('quota').max=c.players-1;$('quota').value=c.catchers;render()}});

function render(){const records=chosen(),quotas=[...new Set(records.map(c=>c.catchers))].sort((a,b)=>a-b);$('quota').min=quotas[0];$('quota').max=quotas.at(-1);let quota=Number($('quota').value);if(!quotas.includes(quota)){quota=quotas[0];$('quota').value=quota}current=records.find(c=>c.catchers===quota&&c.strategy===$('strategy').value);const c=current,s=c.stats;$('quota-label').textContent=quota+'명';$('meta').textContent=`실제 ${c.trials.toLocaleString()}게임 · 시드 ${c.seed}`;
$('bars').innerHTML=[['비교집단',s.p_c,''],['나머지 집단',s.p_n,'orange']].map(([label,v,cl])=>`<div class="bar"><strong>${label}</strong><div class="track"><div class="fill ${cl}" style="width:${v*100}%"></div></div>${pct(v)}</div>`).join('');$('delta').textContent=pp(s.delta);$('ci').textContent=s.ci95?`95% 신뢰구간: ${pp(s.ci95[0])} ~ ${pp(s.ci95[1])}`:'표본 변동이 없어 정규 근사 추론 불가';$('significance').textContent=s.p_value_holm===null?'Holm 보정 p: 계산 불가':s.p_value_holm===0?'Holm 보정 p < 1e-300':`Holm 보정 p = ${s.p_value_holm.toExponential(2)}`;$('exact').textContent=`검산용 정확 차이: ${c.exact.delta.fraction} (${pp(c.exact.delta.value)})`;
$('branch-denominator').textContent=`분모: ${c.trials.toLocaleString()}게임. 무승부는 첫 유효 투구 이전의 재투구로 별도 집계합니다.`;
$('branches').innerHTML=c.observed_branches.map((b,i)=>`<tr><td>${labels[b.branch]}</td><td>${b.count.toLocaleString()} / ${pct(b.frequency)}</td><td>${(b.immediate_caught_c/b.count).toFixed(3)} / ${(b.immediate_caught_n/b.count).toFixed(3)}</td><td>${(b.immediate_safe_c/b.count).toFixed(3)} / ${(b.immediate_safe_n/b.count).toFixed(3)}</td><td>${pp(b.mean_delta)}</td><td>${pp(b.contribution)}</td><td><button data-branch="${i}">게임 ${b.samples[0].game}</button></td></tr>`).join('');$('contribution-sum').textContent=`기여도 합 ${pp(c.observed_branches.reduce((v,b)=>v+b.contribution,0))} = 전체 관측 차이 ${pp(s.delta)}`;
const branchByName=Object.fromEntries(c.observed_branches.map(b=>[b.branch,b]));
let mechanism='승자는 패자 과다일 때 생존이 확정되지만 패자 미달일 때는 추가 술래 선정에 다시 참여합니다. 패배도 정원보다 많으면 재선정으로 이어집니다. 같은 승패라도 남은 정원과의 관계가 최종 결과를 바꿉니다.';
if(c.strategy!=='independent'&&c.colluders>1){
const focal=c.colluders,other=c.players-focal,equal=branchByName.equal;
if(focal>quota&&quota>other)mechanism=`비교집단 ${focal}명은 같은 손을 내므로 첫 유효 투구에서 함께 이기거나 집니다. 정원 ${quota}명은 나머지 ${other}명보다 많고 비교집단 ${focal}명보다 작습니다. 어느 쪽도 정확히 ${quota}명의 패자를 구성할 수 없어 첫 투구의 정원 일치가 불가능합니다. 과다·미달 경로의 빈도와 최종 차이를 함께 확인해야 합니다.`;
else if(equal&&focal>quota)mechanism=`같은 손을 낸 비교집단 ${focal}명은 정원 일치의 패자 ${quota}명에 들어갈 수 없습니다. 따라서 이 경로에서는 나머지 집단 ${quota}명이 술래가 되고 비교집단 전원이 생존합니다. 그러나 과다 경로의 패자는 재선정하고, 미달 경로의 직전 승자도 추가 선정에 참여하므로 모든 경로의 기여도를 합산해야 합니다.`;
else if(equal&&quota>other)mechanism=`나머지 집단은 ${other}명뿐이므로 정원 일치의 패자 ${quota}명을 혼자 채울 수 없습니다. 같은 손을 낸 비교집단 ${focal}명과 나머지 ${quota-focal}명이 함께 패배해 즉시 술래가 됩니다. 과다·미달 경로까지 합산해야 전체 차이를 설명할 수 있습니다.`;
else mechanism=`비교집단 ${focal}명은 첫 유효 투구에서 함께 이기거나 집니다. 이 정원에서는 패자 집합에 비교집단 전원이 포함되는 경우와 전원이 빠지는 경우가 모두 가능합니다. 정원 일치 하나의 방향을 미리 단정할 수 없으며, 관측한 과다·일치·미달 경로의 기여도를 합산합니다. 전체 차이가 작거나 신뢰구간에 0이 포함돼도 동등성이 입증된 것은 아닙니다.`;
}
if(c.colluders===1)mechanism='비교집단이 한 명이면 여러 사람의 선택을 묶는 효과가 없습니다. 고정 손·공동 무작위·독립 무작위를 결합 효과 없는 대조로 확인합니다. 개별 실행의 차이는 표본 오차를 포함하므로 점 추정만으로 효과를 단정하지 않습니다.';
else if(c.strategy==='independent')mechanism=`독립 선택에서는 비교집단 ${c.colluders}명의 손이 함께 묶이지 않아 패자 집합도 두 집단을 섞어 포함할 수 있습니다. 공동 선택과 같은 선정 규칙·집단 크기를 유지한 대조입니다. 아래 분기 빈도와 최종 결과는 이 독립 선택 실행에서 집계했습니다.`;
$('mechanism').textContent=mechanism;
$('mechanism-numbers').textContent=c.observed_branches.map(b=>`${labels[b.branch]}: ${pct(b.frequency)}의 게임 × 경로 평균 ${pp(b.mean_delta)} = ${pp(b.contribution)}`).join(' / ')+` → 합계 ${pp(s.delta)}. 관측 경로의 구성으로 해석하며 분기 자체의 인과 효과로 해석하지 않습니다.`;
samples=c.observed_branches.flatMap(b=>b.samples.map(sample=>({...sample,branch:b.branch})));$('game').innerHTML=samples.map((sample,i)=>`<option value="${i}">게임 ${sample.game} · ${labels[sample.branch]}</option>`).join('');sampleIndex=0;step=0;renderGame();drawEffects();renderCoverage();
$('throws').textContent=`실제 투구 ${c.throws.toLocaleString()}회 / 무승부 ${c.draws.toLocaleString()}회 / 담합 해제 후 투구 ${c.released_throws.toLocaleString()}회`;$('agreement').textContent=`담합 해제 이벤트를 제외한 비교집단 쌍의 동일 손 비율: ${c.eligible_pairs?pct(c.same_hand_pairs/c.eligible_pairs):'해당 없음'} (동일 손 ${c.same_hand_pairs.toLocaleString()} / 쌍 관측 ${c.eligible_pairs.toLocaleString()}). 같은 게임에서 반복 관측한 기술통계입니다.`;
$('hands-summary').innerHTML=c.hand_counts.map((counts,i)=>{const total=counts.reduce((a,b)=>a+b,0);return `<tr><td>${i?'나머지 집단':'비교집단'}</td>${counts.map(v=>`<td>${total?pct(v/total):'해당 없음'}</td>`).join('')}<td>${total.toLocaleString()}</td></tr>`}).join('');$('states').innerHTML=c.observed_states.map(s=>`<tr><td>${s.pool_c} / ${s.pool_n} / ${s.remaining}</td><td>${labels[s.branch]}</td><td>${s.released?'예':'아니오'}</td><td>${s.visits.toLocaleString()}</td><td>${s.caught_c} / ${s.caught_n}</td><td>${s.safe_c} / ${s.safe_n}</td></tr>`).join('');$('raw').href=c.raw_file;$('metadata').textContent=JSON.stringify({simulation:data.metadata,presentation:data.presentation||null},null,2);}
function ids(people){return people.map(p=>p+1).join(', ')||'없음'}
function renderGame(){const sample=samples[sampleIndex],e=sample.events[step];$('game').value=sampleIndex;$('game-meta').textContent=`게임 ${sample.game} · 이벤트 ${step+1}/${sample.events.length} · ${e.kind==='throw'?'실제 투구':'투구 없는 자동 확정'} · 남은 정원 ${e.remaining}명`;$('hands').innerHTML=e.pool.map((p,i)=>`<span class="participant ${p<current.colluders?'focal':''}">${p+1}번 · ${e.kind==='throw'?['바위','가위','보'][e.hands[i]]:'자동 확정'}</span>`).join('');$('event-outcome').textContent=`${labels[e.branch]}${e.released?' · 담합 해제':''} · 새 술래: ${ids(e.new_catchers)} · 새 생존: ${ids(e.new_survivors)}`;$('transition').textContent=e.terminal?'선정 종료':`다음 참가자: ${ids(e.next_pool)}`;$('final').textContent=`이 게임의 최종 술래: ${ids(sample.catchers)}`;$('previous').disabled=step===0;$('next').disabled=step===sample.events.length-1;}
for(const id of ['population','strategy'])$(id).addEventListener('change',render);$('quota').addEventListener('input',render);$('game').addEventListener('change',()=>{sampleIndex=Number($('game').value);step=0;renderGame()});$('previous').onclick=()=>{step--;renderGame()};$('next').onclick=()=>{step++;renderGame()};$('branches').onclick=e=>{const b=e.target.closest('button');if(b){const branch=current.observed_branches[Number(b.dataset.branch)].branch;sampleIndex=samples.findIndex(s=>s.branch===branch);step=0;renderGame()}};render();</script></html>'''
THROW_TEMPLATE = THROW_TEMPLATE.replace('__BASE_STYLE__', TEMPLATE.split('<style>')[1].split('</style>')[0])


if __name__ == '__main__':
    import argparse
    import hashlib
    from pathlib import Path
    parser = argparse.ArgumentParser(description='Render an existing experiment without rerunning or changing its data')
    parser.add_argument('results', type=Path)
    parser.add_argument('--output', type=Path, required=True, help='new HTML path; existing files are preserved')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('choose a new output file; existing reports are preserved')
    original = args.results.read_bytes()
    data = json.loads(original)
    data['presentation'] = dict(input_file=args.results.name, input_sha256=hashlib.sha256(original).hexdigest(),
                                renderer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                note='Presentation only; original simulation metadata and results remain unchanged')
    build_report(data, args.output)
    print(args.output.resolve())
