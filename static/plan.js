const QA_ASK={swap:["Swap today's session with tomorrow's?","Swap"],sick:["Mark today as unwell? Today becomes rest, then you come back with easy running.","Yes, I'm unwell"],busy:["Too busy to run today? Today becomes rest and the week is rebuilt around it. The miles are not made up.","Yes, too busy"]};
let QAC=null;
function qaRow(t){
  const ds=(S.statuses||[]).find(s=>(s.kind==='busy'||s.kind==='sick')&&s.start===S.today&&s.end===S.today);
  const lm=S.last_move,moved=S.can_undo&&lm&&(lm.a===S.today||lm.b===S.today);
  const undo=ds?`<p class="small" style="margin:10px 0 0">${ds.kind==='busy'?'Marked too busy today.':'Marked unwell today.'} <button class="ghost" id="qa-undo-status" data-sid="${ds.id}">Undo</button></p>`
    :moved?`<p class="small" style="margin:10px 0 0">Swapped with another day. <button class="ghost" id="qa-undo-move">Undo</button></p>`:'';
  if(QAC&&t.type&&t.type!=='Rest'&&t.type!=='Race'&&!t.done)return `<div class="qa" role="group" aria-label="Confirm"><p class="small" style="margin:0 0 8px;flex-basis:100%">${E(QA_ASK[QAC][0])}</p><button class="btn" id="qa-yes">${E(QA_ASK[QAC][1])}</button><button class="ghost" id="qa-no">Cancel</button></div>`;
  const row=t.type&&t.type!=='Rest'&&t.type!=='Race'&&!t.done?`<div class="qa" role="group" aria-label="Quick actions for today"><button class="ghost" id="qa-swap" title="Swap today's session with tomorrow's">Swap with tomorrow</button><button class="ghost" id="qa-sick" title="Rest today and come back gently">I'm unwell today</button><button class="ghost" id="qa-busy" title="No run today because of work; the week is rebuilt around it">Too busy today</button></div>`:'';
  return row+undo}
/* The Plan page: why a session changed, the feel tap, the what-if line and the weeks. One of the page scripts; see index.html for the order they load in (they share one scope). */
/* One line saying why today is not what the plan first had: the readings behind an easing, or that you or a missed day moved it. */
function whyChanged(t){
  const a=t.adjust, bits=[];
  if(a&&(a.slow||a.easy)&&a.reasons&&a.reasons.length)bits.push(`<b>Why:</b> ${E(a.reasons.join('; '))}.`);
  if(a&&a.easy&&t.original)bits.push('Planned before: '+E(t.original.split('; ')[0])+'.');
  if(t.source==='moved')bits.push('You moved this session here.');
  else if(t.source==='reshuffled')bits.push('Moved here because a session earlier in the week was missed.');
  return bits.length?`<p class="xs" style="margin:6px 0 0" id="why-today">${bits.join(' ')}</p>`:'';
}

/* One tap after a run, only when the watch did not already carry a rating. Never required: the plan works the same without it. */
function feltRow(t){
  if(!t.done||!t.done.miles||t.done.miles<0.5)return '';
  const have=(S.felt||{})[t.date]; if(have)return `<p class="xs mute" id="felt-row" style="margin:10px 0 0">You said today's run felt <b>${E(have)}</b>. <a href="#" data-felt-redo="1">Change</a></p>`;
  return `<div id="felt-row" role="group" aria-label="How did today's run feel?" style="margin:10px 0 0"><p class="xs mute" style="margin:0 0 6px">How did it feel? One tap, optional.</p><div class="qa">${['easy','fine','hard','wrecked'].map(k=>`<button class="ghost" data-felt="${k}">${k[0].toUpperCase()+k.slice(1)}</button>`).join('')}</div></div>`;
}

/* Also one tap, also optional: where it hurt, if anywhere. Pain on two days in a week holds the sessions at easy running for a few days. */
function painRow(t){
  if(!t.done||!t.done.miles||t.done.miles<0.5)return '';
  const have=(S.pain||{})[t.date], names={foot:'Foot or Achilles',calf:'Calf or shin',knee:'Knee',hip:'Hip or glute',hamstring:'Hamstring',back:'Back'};
  if(have)return `<p class="xs mute" id="pain-row" style="margin:8px 0 0">${have==='none'?'You said nothing hurt.':`You said your <b>${E(names[have]||have).toLowerCase()}</b> hurt.`} <a href="#" data-pain-redo="1">Change</a></p>${S.pain_note?`<p class="xs amber" style="margin:6px 0 0">${E(S.pain_note)}</p>`:''}`;
  return `<div id="pain-row" role="group" aria-label="Did anything hurt?" style="margin:8px 0 0"><p class="xs mute" style="margin:0 0 6px">Did anything hurt? One tap, optional.</p><div class="qa">${Object.entries(names).map(([k,v])=>`<button class="ghost" data-pain="${k}">${v}</button>`).join('')}<button class="ghost" data-pain="none">Nothing</button></div></div>`;
}

/* What tonight's sleep would do to tomorrow's session: the same rules run with different hours, so the athlete sees what would change the plan. */
function whatIfLine(){
  const w=S.what_if; if(!w)return '';
  const h=v=>(Math.round(v*4)/4).toString().replace(/\.0+$/,'')+' h';
  const body=w.already?'Tomorrow\'s paces will be eased whatever you sleep tonight; your 7-day readings already say so.'
    :w.eases_below?`Tomorrow's session is kept as planned if you sleep ${h(w.eases_below)} or more tonight (your normal is ${w.normal} h). Less than that eases its paces${w.easy_below?`, and under ${h(w.easy_below)} it becomes an easy run`:''}.`
    :`Tomorrow's session is kept as planned whatever you sleep tonight.`;
  return `<p class="xs mute" id="whatif" style="margin:10px 0 0"><b>What would change tomorrow:</b> ${body}</p>`;
}

/* Time on feet, for ultras and hilly races, where hours on the legs say more than miles. The plan is still built in miles. */
const hm=m=>m>=60?`${Math.floor(m/60)} h${m%60?' '+String(m%60).padStart(2,'0'):''}`:`${m} min`;

function planView(){
  const f=S.fitness, r=S.readiness, t=S.days.find(d=>d.today)||{};
  const lev={green:'Recovered',amber:'A bit tired',red:'Not recovered',unknown:'Waiting for watch sync'};
  let h='<div class="grid toprow">'+termsNotice()+updateBanner();
  if(f&&f.goal){const g=f.goal, wk=f.week.weeks_to_race||0;
    h+=`<div class="card hero c6">${ring(Math.max(0.03,Math.min(1,1-g.days/252)),wk+'w')}<p class="eyebrow">Goal · ${nice(g.date)} · ${g.days} days to go</p><p class="h">${E(g.name)}</p>
      <div class="stats"><div class="stat"><div class="v num">${g.now}</div><div class="k">If you raced today</div></div>
      <div class="stat" style="border-color:var(--brand)"><div class="v num">${g.forecast.time}</div><div class="k">Race-day forecast${g.forecast.change?` · <span class="${g.forecast.change<0?'green':'amber'}">${g.forecast.change<0?'▼':'▲'} ${fmt(Math.abs(g.forecast.change))} this week</span>`:''}</div></div>
      <div class="stat"><div class="v num">${E(g.target||'—')}</div><div class="k">Your goal</div></div></div>
      <details class="more"><summary class="small">${(f2=>f2.gap?`The forecast is <b class="${f2.gap[0]==='ahead'?'green':'amber'}">${f2.gap[1]} ${f2.gap[0]==='ahead'?'ahead of':'behind'}</b> your goal`:'The forecast')(g.forecast)} <span class="xs mute">· how it is worked out</span></summary>
      ${g.heat?`<p class="small" style="margin:10px 0 0">☀ Race-day weather around 9:00: <b>${g.heat.temp}°C, dew point ${g.heat.dew}°C</b>. ${g.heat.pct===null?'<b class="amber">Very hot and humid: race for the finish, not a time, and start well inside your pace.</b>':g.heat.pct>0?`Expect about <b>${g.heat.pct}%</b> slower than the forecast above; start that much slower.`:'No slowdown expected for the heat.'}${g.heat.pct!==0&&S.heat&&S.heat.exposure?` In the last ${S.heat.exposure.window} days you ran ${S.heat.exposure.days} day${S.heat.exposure.days===1?'':'s'} in real heat. Getting used to heat takes repeated hot runs over one to two weeks (Racinais and colleagues, 2015), so a few runs at the warmest hour of the day in the fortnight before race day help.`:''}</p>`:''}
      ${(fc=>`<p class="small" style="margin:12px 0 0">It assumes you complete <b>${fc.pct}%</b> of the plan${fc.chosen?`, the figure you set${fc.history_pct!==null?` (your last two years averaged ${fc.history_pct}%${fc.plan_pct!==null&&fc.plan_days>=7?`; this plan so far ${fc.plan_pct}%`:''})`:''}`:fc.plan_weight>=100?', your record on this plan so far':fc.plan_weight>0?`, a blend of your history (${fc.history_pct}%) and this plan so far (${fc.plan_pct}%)`:fc.history_pct!==null?', your average over the last two years':', a general figure until there is history'}.</p>
      <p class="xs mute" style="margin:6px 0 0">Complete all of it: <b class="num">${fc.all}</b> · Complete ${fc.poor_pct}%: <b class="num">${fc.poor}</b>${fc.out_of_reach?' · Your goal is beyond the best you have shown in three years; a new best along the way will move the forecast.':fc.needs_all?' · Your goal is within reach only if nearly all of the plan gets done.':''}</p>`)(g.forecast)}</details></div>`}
  else h+=`<div class="card hero c6"><p class="eyebrow">Goal</p><p class="h">No goal race yet</p><p class="mute small">Add one under Races & status and the plan will build toward it.</p></div>`;
  // once a run of half a mile or more is logged today the card shows tomorrow (the app plans one run a day, so there is no second session to wait for)
  const iso=(d,n)=>{const x=new Date(d+'T12:00');x.setDate(x.getDate()+n);return `${x.getFullYear()}-${String(x.getMonth()+1).padStart(2,'0')}-${String(x.getDate()).padStart(2,'0')}`};
  const tomorrow=S.days.find(d=>d.date===iso(S.today,1));
  const doneToday=!!(t.done&&t.done.miles>=0.5);     // half a mile: a warm-up or an accidental start is not the day's run
  if(doneToday&&tomorrow&&tomorrow.label){
    const x=tomorrow;
    h+=`<div class="card c6" id="tomorrowcard"><p class="eyebrow">Tomorrow <span class="chip green"><i></i>Today's run is done</span></p>
    <p class="h">${E(x.label)} <span class="mute num" style="font-weight:600">${E(x.dist||'')}</span></p>
    ${stepList(x.text)}
    ${x.wx?`<p class="xs mute" style="margin:6px 0 0">${x.wx.wet?'☂':'☀'} Around ${x.wx.hour}:00 · ${E(wxTip(x.wx))}</p>`:''}
    ${x.purpose?`<p class="small mute" style="margin:10px 0 0">${E(x.purpose)}</p>`:''}
    ${x.note?`<p class="xs mute" style="margin:6px 0 0">${E(x.note)}</p>`:''}${x.strength?`<p class="xs" style="margin:6px 0 0"><span class="tag">+ ${E(x.strength)}</span></p>`:''}
    <p class="xs mute" style="margin:10px 0 0">Today: ${E(t.done.dist)}${t.done.pace?' at '+E(t.done.pace):''}${t.done.runs>1?' over '+t.done.runs+' runs':''}. Tomorrow's paces are eased in the morning if your recovery signs say so.</p>${feltRow(t)}${painRow(t)}${whatIfLine()}</div>`;
  } else
  h+=`<div class="card c6"><p class="eyebrow">Today</p>
    <p class="h">${E(t.label||'Nothing planned')} <span class="mute num" style="font-weight:600">${E(t.dist||'')}${S.on_feet&&t.mins?' · '+hm(t.mins):''}</span></p>
    ${stepList(t.text)}
    ${qaRow(t)}
    ${t.adjust?`<p class="small amber" style="margin:10px 0 0">${t.adjust.easy?`<b>${E(t.adjust.advice||'Changed to an easy run today.')}</b>`:`<b>Paces eased ${(t.adjust.slow*100).toFixed(1)}% today.</b> ${E(t.adjust.advice||'')}`}</p>`:''}
    ${t.strength?`<p class="xs" style="margin:6px 0 0"><span class="tag">+ ${E(t.strength)}</span></p>`:''}
    ${(x=>x?`<details class="more" id="todaywhy"><summary class="xs mute">${t.adjust||t.source==='moved'||t.source==='reshuffled'?'Why this, and what would change it':'What would change tomorrow'}</summary>${x}</details>`:'')(whyChanged(t)+whatIfLine()+(t.note?`<p class="xs mute" style="margin:6px 0 0">${E(t.note)}</p>`:''))}</div>`;
  // recovery and weather each have a panel of their own
  const wxOn=!!((S.heat&&S.heat.today)||(S.met_warnings&&(S.met_warnings.stale||S.met_warnings.county)));
  const rd=r&&r.date===S.today, nrm=(rd&&r.normal)||{};
  // which way each reading is going: the last 7 days against the 7 before. Up is good for sleep and HRV, down for resting heart rate.
  const tr=(k,goodUp)=>{const x=rd&&r.trend&&r.trend[k];if(!x)return '';const up=x.dir==='up',flat=x.dir==='flat',cls=flat?'mute':(up===goodUp?'green':'amber');
    const amt=k==='sleep_h'?Math.abs(x.change).toFixed(1)+' h':Math.round(Math.abs(x.change));
    return `<div class="xs ${cls}" style="margin-top:3px" title="Average of the last 7 days: ${x.now}. The 7 days before: ${x.prev}."><b>${up?'▲':flat?'→':'▼'}</b> ${flat?'steady':(up?'up ':'down ')+amt} on the week before</div>`};
  h+=`<div class="card ${wxOn?'c6':'c12'}" id="recoverycard"><p class="eyebrow">Recovery <span class="chip ${rd?r.level:'unknown'}"><i></i>${lev[rd?r.level:'unknown']}</span></p>
    ${rd&&(r.sleep_h||r.hrv||r.rhr)?`<div class="stats">${r.sleep_h?`<div class="stat"><div class="v num">${r.sleep_h.toFixed(1)} h</div><div class="k">Sleep last night${nrm.sleep_h?' · normal '+nrm.sleep_h:''}${r.sleep_score?' · score '+r.sleep_score:''}</div>${tr('sleep_h',true)}</div>`:''}
      ${r.hrv?`<div class="stat"><div class="v num">${Math.round(r.hrv)}</div><div class="k">HRV last night${nrm.hrv?' · normal '+nrm.hrv:''}</div>${tr('hrv',true)}</div>`:''}
      ${r.rhr?`<div class="stat"><div class="v num">${Math.round(r.rhr)}</div><div class="k">Resting HR${nrm.rhr?' · normal '+nrm.rhr:''}</div>${tr('rhr',false)}</div>`:''}</div>`:''}
    ${rd?`<p class="xs mute" style="margin:8px 0 0">${E(r.reasons.join(' · '))}</p>${r.hrv_building?`<p class="xs amber" style="margin:6px 0 0">HRV is shown but does not change your plan yet: ${r.hrv_building.nights} of ${r.hrv_building.needed} nights needed to learn your normal.</p>`:''}`:'<p class="xs mute" style="margin:8px 0 0">Recovery appears after your watch has synced last night.</p>'}</div>`;
  if(wxOn)h+=`<div class="card c6" id="weathercard"><p class="eyebrow">Weather</p>
    ${S.heat&&S.heat.today?`<p class="xs mute" style="margin:6px 0 0">☀ Around ${S.heat.today.hour}:00: ${S.heat.today.temp}°C, dew point ${S.heat.today.dew}°C${S.heat.today.pct===null?' · too hot for hard running':S.heat.today.pct>0?` · about ${S.heat.today.pct}% slower for the heat`:' · no heat slowdown'}${S.heat.today.wind!=null?` · wind ${wxWind(S.heat.today.wind)}${S.heat.today.gust?`, gusts ${wxWind(S.heat.today.gust)}`:''}${S.heat.today.wind_pct?` · about ${S.heat.today.wind_pct}% slower for the wind`:''}`:''}</p>`:''}
    ${metWarn(S.met_warnings,S.today)}</div>`;
  h+='</div>';
  if(S.warnings&&S.warnings.length)h+=`<div class="alert" id="watchouts" role="status"><b>Watch-outs</b><ul class="why" style="margin:6px 0 0">${S.warnings.map(w=>`<li>${E(w.text)}</li>`).join('')}</ul></div>`;
  if(S.climb)h+=(c=>`<div class="grid" style="margin-top:14px"><div class="card c12" id="climbcard"><p class="eyebrow">Climb this week · toward ${E(c.race)}</p>
    <div class="stats" style="margin-top:0"><div class="stat"><div class="v num">${c.week_m.toLocaleString()} m</div><div class="k">Target for the week</div></div><div class="stat"><div class="v num">${c.long_m.toLocaleString()} m</div><div class="k">Of it in the long run</div></div>
    <div class="stat"><div class="v num ${c.done_m>=c.week_m?'green':''}">${c.done_m.toLocaleString()} m</div><div class="k">Done so far</div></div></div><div class="bar"><i style="width:${Math.min(100,Math.round(100*c.done_m/Math.max(c.week_m,1)))}%"></i></div>
    <p class="xs mute" style="margin:8px 0 0">The race climbs ${c.race_per_mile} m a mile; you have averaged ${c.now_per_mile} m a mile over four weeks; this week aims for ${c.target_per_mile}. ${c.progress<=0?'The ramp toward the race figure starts 16 weeks out.':c.progress>=1?'You are at the race figure now.':'The target rises each week and reaches the race figure three weeks out.'}</p></div></div>`)(S.climb);
  const weeks=[];for(let i=0;i<S.days.length;i+=7)weeks.push(S.days.slice(i,i+7));
  const names=['Last week','This week','Next week','In 2 weeks','In 3 weeks','In 4 weeks','In 5 weeks'];
  const fc=v=>v>=85?'green':v>=70?'amber':'red', pc=v=>v>=1?'green':v<=-3?'amber':'mute';
  weeks.forEach((w,i)=>{
    const wi=S.week_info[(w.find(d=>d.week)||{}).week], total=w.reduce((a,d)=>a+(d.miles||0),0), prov=w.some(d=>d.week&&S.week_info[d.week]&&!S.week_info[d.week].final);
    h+=`<div class="wk"><b>${names[i]||''}</b><span class="mute small">${nice(w[0].date)} – ${nice(w[6].date)}</span>${S.on_feet&&w.some(d=>d.mins)?`<span class="tag" title="Planned time on your feet this week, from the paces in each session">${hm(w.reduce((a,d)=>a+(d.mins||0),0))} on feet</span>`:''}${total?`<span class="tag">${wi&&S.settings.week_start===0?E(wi.mode)+' · ':''}${U()==='mi'?Math.round(total*2)/2+' mi':Math.round(total*KM)+' km'}</span>`:''}${prov?'<span class="tag">provisional</span>':''}${i===0&&S.streak>=2?`<span class="tag green" title="Whole weeks in a row with 90% or more of the planned miles run">${S.streak} weeks in a row at 90%+</span>`:''}${w[0].week_perf!=null?`<span class="tag ${pc(w[0].week_perf)}" title="Pace for your heart rate across the week's runs, against the four weeks before">pace for heart rate ${w[0].week_perf>0?'+':''}${w[0].week_perf.toFixed(1)}%</span>`:''}
      ${i===1?`<span style="margin-left:auto" class="xs mute"><span class="hint-d">Click a day for detail · drag to swap</span><span class="hint-m">Tap a day for detail</span> ${S.can_undo?'· <a href="#" id="undo">Undo last move</a>':''}</span>`:''}</div><div class="cal">`;
    for(const d of w){const can=!d.past&&d.type, b=d.body;
      h+=`<div class="dw"><div class="day ${d.type||''} ${d.past?'past':''} ${d.today?'today':''} ${SEL===d.date?'sel':''}" data-date="${d.date}" ${can?'draggable="true"':''} tabindex="0" role="button" aria-label="${d.dow} ${+d.date.slice(8)}: ${E(d.label||'no session')}">
        <div class="d"><span>${d.dow} ${+d.date.slice(8)}</span><span>${d.done&&d.done.id?'':(d.on_watch?'⌚':'')+(d.source==='moved'?' ↔':'')+(d.source==='reshuffled'?' ↻':'')}</span></div>
        ${d.type?`<div class="l">${E(d.label)}</div>${d.dist?`<div class="m num">${E(d.dist)}${S.on_feet&&d.mins?` · ${hm(d.mins)}`:''}</div>`:''}<div class="t">${E(d.short||'')}</div>`:''}
        <div class="f">${d.done?`<span class="done">✓ ${E(d.done.dist)}</span>`:''}${d.wx&&!d.done?`<span class="xs mute num" title="${E(wxTip(d.wx))}">${d.wx.wet?'☂':'☀'} ${d.wx.hour}:00 · ${d.wx.temp}°</span>`:''}${d.adjust?`<span class="tag amber">eased ${(d.adjust.slow*100).toFixed(1)}%</span>`:''}</div>
        ${b?`<div class="mt num"><span class="${fc(b.fresh)}" title="Freshness this morning: last night’s sleep, and your 7-day HRV and resting heart rate, against your normal"><b>${b.fresh}</b></span>${b.sleep_score?`<span title="Last night's sleep score">☾${b.sleep_score}</span>`:''}${b.rhr?`<span title="Resting heart rate">♥${Math.round(b.rhr)}</span>`:''}${b.hrv?`<span title="Last night's HRV">∿${Math.round(b.hrv)}</span>`:''}</div>`:''}</div>${d.done&&d.done.id?GLINK(d.done.id,'corner'):''}</div>`}
    h+='</div>'});
  h+=`<p class="xs mute" style="margin:10px 2px 0">On each day: <b>freshness</b> out of 100, from that night's sleep and your 7-day HRV and resting heart rate, against your normal · ☾ that night's sleep score · ♥ resting heart rate · ∿ that night's HRV. In each week's heading: your pace for your heart rate across the week against the four weeks before. ⌚ on your watch · ↔ moved by you · ↻ moved here because it was missed earlier in the week.</p>`;
  const sd=S.days.find(d=>d.date===SEL);
  if(sd){const b=sd.body, a=sd.adjust, sy=sd.sync, sc={synced:'green',pending:'amber',later:'unknown',off:'unknown',past:'unknown',none:'unknown'};
    h+=`<div class="ov" id="ov"><div class="modal" role="dialog" aria-modal="true" aria-labelledby="mt">
    <p class="eyebrow"><span id="mt">${sd.dow} ${nice(sd.date)} ${sd.date.slice(0,4)}</span><button class="ghost" id="selx" style="margin-left:auto" aria-label="Close">Close</button></p>
    <p class="h">${E(sd.label||'No session planned')} <span class="mute num" style="font-weight:600">${E(sd.dist||'')}</span></p>
    ${sd.wx?wxBest(sd.wx):''}
    ${metWarn(S.met_warnings,sd.date)}
    ${sd.type&&sd.type!=='Rest'?`<p class="lab2">${a?'Original session':'Session'}</p>${stepList(a?sd.original:sd.text)}`:''}
    ${a?`<p class="lab2">Tuned for today <span class="chip amber" style="margin-left:6px"><i></i>paces eased ${(a.slow*100).toFixed(1)}%</span></p>${stepList(sd.text)}
      <p class="small" style="margin:8px 0 0">Why: ${E((a.reasons||[]).join('; '))}. ${E(a.advice||'')}</p>`
     :sd.type&&sd.type!=='Rest'&&!sd.past?`<p class="small mute" style="margin:8px 0 0">${sd.today?(b?'Not tuned: last night’s sleep and your HRV and resting heart rate trends are normal, so it stands as planned.':'Not tuned yet: waiting for last night’s data from your watch.'):'Tuning happens on the morning of the session, from the night before and your recent trends.'}</p>`:''}
    ${sd.wx?`<p class="lab2">Weather through the day</p><p class="small" id="daywx" style="margin:4px 0 0">${wxLines(sd.wx,true).map(E).join('<br>')}</p>${wxCharts(sd.wx)}<p class="xs" style="margin:8px 0 0"><a href="#" data-gohours>Change the hours you can run</a></p>`:''}
    ${sd.purpose?`<p class="small" id="purpose" style="margin:8px 0 0"><b>What it is for.</b> ${E(sd.purpose)}</p>`:''}
    ${sd.note?`<p class="small mute" style="margin:8px 0 0">${E(sd.note)}</p>`:''}${sd.strength?`<p class="xs" style="margin:8px 0 0"><span class="tag">+ ${E(sd.strength)}</span></p>`:''}
    ${b?`<p class="lab2">Recovery markers</p><div class="stats" style="grid-template-columns:repeat(auto-fit,minmax(118px,1fr));margin-top:6px">
      <div class="stat"><div class="v num ${fc(b.fresh)}">${b.fresh}</div><div class="k">Freshness</div></div>
      ${b.sleep_h?`<div class="stat"><div class="v num">${b.sleep_h.toFixed(1)} h</div><div class="k">Sleep last night${b.normal.sleep_h?' · normal '+b.normal.sleep_h:''}${b.week.sleep_h?' · 3 nights '+b.week.sleep_h:''}</div></div>`:''}
      ${b.sleep_score?`<div class="stat"><div class="v num">${b.sleep_score}</div><div class="k">Sleep score last night${b.normal.sleep_score?' · normal '+b.normal.sleep_score:''}</div></div>`:''}
      ${b.week.hrv?`<div class="stat"><div class="v num">${b.week.hrv}</div><div class="k">HRV, 7-day${b.normal.hrv?' · normal '+b.normal.hrv:''}${b.hrv?' · last night '+Math.round(b.hrv):''}</div></div>`:''}
      ${b.week.rhr?`<div class="stat"><div class="v num">${b.week.rhr}</div><div class="k">Resting HR, 7-day${b.normal.rhr?' · normal '+b.normal.rhr:''}${b.rhr?' · today '+Math.round(b.rhr):''}</div></div>`:''}</div>
      ${a?'':`<p class="xs mute" style="margin:8px 0 0">${E(b.reasons.join('; '))}</p>`}`:''}
    ${sd.fuel?`<p class="lab2">Fuelling · about ${Math.floor(sd.fuel.minutes/60)} h ${String(sd.fuel.minutes%60).padStart(2,'0')}</p><p class="small" style="margin:4px 0 0">${E(sd.fuel.text)}${sd.fuel.per_hour<sd.fuel.guide&&!sd.fuel.race?` <span class="mute">The guideline for this length is up to ${sd.fuel.guide} g an hour; the plan steps you up toward race day.</span>`:''}</p>`:''}
    ${sd.done?`<p class="lab2">What you ran</p><p class="small" style="margin:4px 0 0"><b class="num">${E(sd.done.dist)}</b> at ${E(sd.done.pace)}${sd.done.runs>1?` over ${sd.done.runs} runs`:''} ${sd.done.id?GLINK(sd.done.id):''} <button class="ghost" data-dopen="${sd.date}" style="margin-left:8px">Run detail</button></p>${sd.done.weather?`<p class="xs mute" id="runwx" style="margin:4px 0 0">Weather: ${E(sd.done.weather)}</p>`:''}`:''}
    ${sy?`<p class="lab2">Garmin</p><p class="small" style="margin:4px 0 0"><span class="chip ${sc[sy.state]}"><i></i>${{synced:'Synced',pending:'Waiting to sync',later:'Not sent yet',off:'Not sending',past:'Past',none:'Nothing to send'}[sy.state]}</span> ${E(sy.text)}</p>`:''}
    </div></div>`}
  h+=dayModal();
  if(S.season&&S.season.length>4){const mx=Math.max(...S.season.map(x=>x.total),1), col={race:'var(--race)',taper:'var(--amber)',down:'var(--mute)',recover:'var(--mute)',postrace:'var(--mute)',return:'var(--mute)',tuneup:'var(--amber)'};
    const races=S.season.flatMap((x,i)=>(x.races||[]).map(r=>Object.assign({week:i+1},r)));
    h+=`<div class="grid" style="margin-top:22px"><div class="card c12" id="season"><p class="eyebrow">Season outline · ${S.season.length} weeks to ${E(f&&f.goal?f.goal.name:'your goal')}</p>
      <div class="sout" role="list" aria-label="Weekly distance for each week of the season">${S.season.map((x,i)=>{const rc=(x.races||[]);const tip='Week of '+nice(x.monday)+': '+x.mode+', '+x.total+' '+U()+', long run '+x.long+' '+U()+(rc.length?'. Race: '+rc.map(r=>r.name).join(', '):'');
        return `<div class="sw" role="listitem" tabindex="0" title="${E(tip)}" aria-label="${E(tip)}"><span class="sv num">${x.total}</span><div class="sbar"><i style="height:${Math.max(4,Math.round(100*x.total/mx))}%;${col[x.mode]?'background:'+col[x.mode]:''}"></i></div>
          <span class="sr">${rc.map(r=>`<b class="${r.priority==='A'?'ra':'rb'}" title="${E(r.name)}">${r.priority==='A'?'★':'●'}</b>`).join('')}</span><span class="sd">${(i===S.season.length-1||(i%4===0&&i<S.season.length-3))?nice(x.monday):''}</span></div>`}).join('')}</div>
      ${races.length?`<ul class="clist" style="margin-top:10px;list-style:none;padding-left:0">${races.map(r=>`<li><b class="${r.priority==='A'?'ra':'rb'}">${r.priority==='A'?'★':'●'}</b> ${E(r.name)} · ${nice(r.date)} · ${r.priority==='A'?'goal race':'tune-up'} · week ${r.week} of ${S.season.length}</li>`).join('')}</ul>`:''}
      <p class="xs mute" style="margin:8px 0 0">Weekly distance in ${U()==='mi'?'miles':'km'} above each bar; ★ goal race, ● tune-up race. Grey: lighter weeks · amber: taper and tune-up race weeks · red: race week. Only this week is fixed; each later week assumes the one before goes to plan, and all are redrawn at every weekly review.</p></div></div>`}
  if(f)h+=`<div class="grid" style="margin-top:22px"><div class="card c12"><button class="btn" id="explain" style="float:right;margin:0 0 8px 12px">Explain my plan</button><p class="eyebrow">Why this week looks like this</p><ul class="why">${f.week.why.map(w=>`<li>${E(w)}</li>`).join('')||'<li>Nothing unusual.</li>'}</ul></div></div>`;
  return h;
}
