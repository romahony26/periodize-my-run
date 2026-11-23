/* The Recovery page: last night, the habits behind it, the illness watch, and what to do today and tonight. One of the page scripts; see index.html for the order they load in (they share one scope). */
let REC=null;
async function loadRec(){try{REC=await api('recovery');if(view==='rec')render()}catch(e){/* the page keeps what it has */}}
setInterval(()=>{if(view==='rec'&&!document.hidden&&!holdUI())loadRec()},300000);
function recView(){
  if(!REC)return `<div class="grid"><div class="card c12 loading">${skel(4)}</div></div>`;
  const R=REC,n=R.night,lv={green:['green','Good'],amber:['amber','Below normal'],red:['red','Poor'],unknown:['','Waiting for data']}[R.level]||['',''];
  const hm=h=>h==null?'—':Math.floor(h)+' h '+String(Math.round((h%1)*60)).padStart(2,'0')+' min';
  const vs=(v,b,u,inv)=>v==null||b==null?'':`<span class="xs ${(inv?v>b:v<b)?'amber':'mute'}"> · normal ${b}${u||''}</span>`;
  const sign=m=>(m>0?'+':m<0?'−':'')+Math.abs(m)+' min';
  const kc={red:'red',amber:'amber',green:'green',info:''};
  const act=R.actions.map(a=>`<li style="margin:0 0 12px"><span class="tag ${kc[a.kind]||''}">${a.kind==='info'?'Worth knowing':a.kind==='green'?'All good':a.kind==='red'?'Act now':'Look at'}</span> <b>${E(a.title)}</b><p class="small" style="margin:4px 0 0">${E(a.body)}</p></li>`).join('');
  const g=R.regularity,wk=R.week,ill=R.illness,lr=R.late_runs,al=R.after_long;
  const tip=(lab,f)=>s=>nice(s[7])+': '+lab+' '+f(s);
  return `<div class="grid">
  <div class="card c12" id="recnow"><p class="eyebrow">Recovery this morning <span class="mute" style="text-transform:none;letter-spacing:0">· read from your watch, refreshed each time it syncs</span></p>
    <div class="big ${lv[0]}">${lv[1]}</div>
    ${R.reasons&&R.level!=='unknown'?`<p class="small" style="margin:4px 0 12px">${E(R.reasons.join('; ').replace(/^./,c=>c.toUpperCase()).replace(/\.$/,''))}.</p>`:''}
    <ul class="steps" style="list-style:none;padding:0;margin:12px 0 0">${act}</ul></div>
  <div class="card" id="recnight"><p class="eyebrow">Last night${R.night_date?` <span class="mute" style="text-transform:none;letter-spacing:0">· wake-up ${nice(R.night_date)}</span>`:''}</p>
    ${n?`<div class="big num">${hm(n.sleep_h)}</div><p class="small ${n.vs_need_min<-30?'amber':'mute'}" style="margin:2px 0 8px">${sign(n.vs_need_min)} against your need of ${hm(R.need_h)}${n.score!=null?` · sleep score ${n.score}`:''}</p>
    <table>${n.bed||n.wake?`<tr><td>Asleep to wake</td><td class="r num">${n.bed||'—'} to ${n.wake||'—'}</td></tr>`:''}
      ${n.awake_min!=null?`<tr><td>Awake in the night</td><td class="r num">${n.awake_min} min${n.awake_n!=null?` (${n.awake_n}×)`:''}</td></tr>`:''}
      <tr><td>HRV, overnight</td><td class="r num">${n.hrv??'—'}${vs(n.hrv,R.norm.hrv,'',false)}</td></tr>
      <tr><td>Resting heart rate</td><td class="r num">${n.rhr??'—'}${vs(n.rhr,R.norm.rhr,'',true)}</td></tr>
      ${n.resp!=null?`<tr><td>Breathing, asleep</td><td class="r num">${n.resp}${vs(n.resp,R.norm.resp,'',true)}</td></tr>`:''}</table>
    <details style="margin-top:8px"><summary class="xs" style="cursor:pointer">Shown for context only</summary>
      <table style="margin-top:6px">${n.deep_min!=null?`<tr><td>Deep sleep</td><td class="r num">${n.deep_min} min</td></tr><tr><td>REM sleep</td><td class="r num">${n.rem_min} min</td></tr>`:''}
      ${n.bb_gain!=null?`<tr><td>Body Battery gained</td><td class="r num">+${n.bb_gain}</td></tr>`:''}${n.sleep_stress!=null?`<tr><td>Stress asleep</td><td class="r num">${n.sleep_stress}</td></tr>`:''}</table>
      <p class="xs mute" style="margin:6px 0 0">Sleep stages from a wrist watch are only moderately accurate against a sleep laboratory, and Body Battery and the stress score have no independent validation. They never change your plan.</p></details>
    `:`<p class="small mute">No sleep recorded for last night yet. It appears when your watch syncs.</p>`}</div>
  <div class="card" id="recweek"><p class="eyebrow">Sleep this week</p>
    ${wk.avg_h!=null?`<div class="big num ${wk.short_h>=3?'amber':'green'}">${wk.avg_h} h</div><p class="small mute" style="margin:2px 0 8px">average of the last ${wk.nights} nights</p>
    <div class="stats" style="margin-top:0"><div class="stat"><div class="v num">${R.need_h}</div><div class="k">h you need</div></div><div class="stat"><div class="v num ${wk.short_h>=3?'amber':''}">${wk.short_h??'—'}</div><div class="k">h short this week</div></div></div>`:`<p class="small mute">Needs four nights of sleep.</p>`}
    <p class="xs mute" style="margin:8px 0 0">Your need is taken from ${E(R.need_source)}.${R.garmin_need_h?` Your watch's own estimate is ${R.garmin_need_h} h.`:''} Short sleep slows endurance running from a single night, mostly by making it feel harder.</p></div>
  <div class="card" id="recreg"><p class="eyebrow">Your sleep habits</p>
    ${g?`<div class="big num">${g.typical_bed}</div><p class="small mute" style="margin:2px 0 8px">typical time you fall asleep${g.typical_wake?`, waking about ${g.typical_wake}`:''}</p>
      <table><tr><td>Bedtime varies by</td><td class="r num ${g.label==='irregular'?'amber':''}">±${g.bed_sd_min} min <span class="tag ${g.label==='regular'?'green':g.label==='irregular'?'amber':''}">${E(g.label)}</span></td></tr>
      ${g.weekend_shift_min!=null?`<tr><td>Weekend nights are</td><td class="r num">${Math.abs(g.weekend_shift_min)} min ${g.weekend_shift_min>0?'later':'earlier'}</td></tr>`:''}</table>
      <p class="xs mute" style="margin:8px 0 0">Regular sleep timing predicts health outcomes at least as well as sleep length (Windred and colleagues, 2024). Under ${45} minutes of spread is regular, over ${60} irregular.</p>`:`<p class="small mute">Needs a week of nights.</p>`}</div>
  ${R.tonight?`<div class="card" id="rectonight"><p class="eyebrow">Tonight</p><div class="big num">${R.tonight.bed_by}</div><p class="small" style="margin:2px 0 0">is when to be asleep to get ${R.tonight.need_h} h before your usual ${R.tonight.wake} wake time.${R.tonight.session?` <b>${E(R.tonight.session)}</b> is tomorrow, so this one counts.`:''}</p></div>`:''}
  <div class="card" id="recill"><p class="eyebrow">Illness watch</p>
    <div class="big ${ill.on?'red':'green'}">${ill.on?'Possible':'Clear'}</div>
    <p class="small" style="margin:4px 0 0">${ill.on?E(ill.reason)+'.':'Resting heart rate, breathing rate and HRV are not moving together the wrong way.'}</p>
    <p class="xs mute" style="margin:8px 0 0">Looks at the last three nights against your own normal, and flags it when two of the three move the wrong way. Resting heart rate and breathing rate rose before symptoms in wearable studies (Mishra and colleagues, 2020; Rentería and colleagues, 2024). It cannot tell a cold from anything else, and it is a prompt to take care, not a diagnosis.</p></div>
  <div class="card c12" id="rectrends"><p class="eyebrow">Last six weeks</p>
    ${lineChart(R.series,1,'var(--brand)','Sleep (hours)',v=>v.toFixed(1),false,tip('slept',s=>s[1]==null?'—':s[1].toFixed(1)+' h'))}
    ${lineChart(R.series,2,'var(--green)','Overnight HRV',v=>Math.round(v),false,tip('HRV',s=>s[2]))}
    ${lineChart(R.series,3,'var(--amber)','Resting heart rate',v=>Math.round(v),false,tip('resting heart rate',s=>s[3]))}
    ${lineChart(R.series,4,'var(--red)','Breathing rate asleep',v=>v.toFixed(1),false,tip('breathing',s=>s[4]))}</div>
  <div class="card c8" id="recdow"><p class="eyebrow">By day of the week <span class="mute" style="text-transform:none;letter-spacing:0">· last eight weeks, night ending that morning</span></p>
    <div id="dowgrid" style="display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:6px;text-align:center">${R.pattern.map(p=>`<div class="mute xs">${p.d}</div>`).join('')}
      ${R.pattern.map(p=>`<div class="num" title="Average sleep">${p.sleep_h==null?'—':p.sleep_h+' h'}</div>`).join('')}
      ${R.pattern.map(p=>`<div class="num mute" title="Average HRV">${p.hrv??'—'}</div>`).join('')}</div>
    <p class="xs mute" style="margin:6px 0 0">Top row: average sleep. Bottom row: average overnight HRV.</p>
    <p class="xs mute" style="margin:8px 0 0">A dip on the same morning each week is usually a habit: a late night, or alcohol, which lowers overnight HRV in a dose-dependent way even in people who train (Pietilä and colleagues, 2018). The app does not ask about either.</p></div>
  <div class="card" id="recown"><p class="eyebrow">Your own patterns</p>
    ${lr?`<p class="small" style="margin:0 0 8px"><b>Late hard runs:</b> ${lr.n} nights followed a hard run ending within 4 hours of sleep. You slept <b class="num">${lr.late_h} h</b> on those, <b class="num">${lr.other_h} h</b> on the others (${lr.diff_min>0?'+':'−'}${Math.abs(lr.diff_min)} min).</p>`:''}
    ${al?`<p class="small" style="margin:0 0 8px"><b>After long runs:</b> over ${al.n} runs of 10 miles or more (16 km), your resting heart rate took a median of <b class="num">${al.median_days}</b> mornings to return to normal.</p>`:''}
    ${!lr&&!al?`<p class="small mute">These appear once there are enough nights and long runs to compare (three late hard runs and ten other nights; four long runs with resting heart rate readings).</p>`:''}</div>
  </div>`}
