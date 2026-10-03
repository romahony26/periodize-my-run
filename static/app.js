const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const E=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let HIST=null, DAY=null, SEL=null, S=null, ABOUT=null, view='plan', wiz={step:1,mfa:false,prefs:null}, logs=[], toastT=null;
const LOGO=`<svg viewBox="0 0 48 48"><rect width="48" height="48" rx="12" fill="url(#lg)"/><path d="M10 34l6.5-7 4.5 3.5 6-9.5 4.5 3.5L38 13" fill="none" stroke="#fff" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/><circle cx="38" cy="13" r="3.4" fill="#fff"/></svg>`;
const DOW=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
const DIST=[['5K',3.107],['5 miles',5],['10K',6.214],['10 miles',10],['Half marathon',13.109],['Marathon',26.219],['50K',31.07],['50 miles',50],['100K',62.14],['100 miles',100]];
const KM=1.609344, U=()=>S.settings.units, dU=m=>U()==='mi'?`${Math.round(m).toLocaleString()} mi`:`${Math.round(m*KM).toLocaleString()} km`;
const hmsIn=t=>{const p=String(t||'').trim().split(':').map(Number);if(!p.length||p.some(isNaN))return 0;return p.reduce((a,x)=>a*60+x,0)};
const fmt=s=>{s=Math.round(s);const h=Math.floor(s/3600),m=Math.floor(s%3600/60),x=String(s%60).padStart(2,'0');return h?`${h}:${String(m).padStart(2,'0')}:${x}`:`${m}:${x}`};
const nice=d=>new Date(d+'T12:00').toLocaleDateString(undefined,{day:'numeric',month:'short'});
function toast(t,k){const e=$('#toast');e.textContent=t;e.className='on '+(k||'');clearTimeout(toastT);toastT=setTimeout(()=>e.className='',k?6500:3200)}
async function api(path, body, method){
  const r=await fetch('/api/'+path,{method:method||(body?'POST':'GET'),headers:{'Content-Type':'application/json','X-Requested-With':'periodize'},body:body?JSON.stringify(body):undefined});
  const j=await r.json().catch(()=>({}));
  if(r.status===401){authView(j.auth);throw new Error('auth')}
  if(!r.ok){toast(j.error||'Something went wrong.','err');throw new Error(j.error)}
  return j;
}
let fastT=null;
async function load(){try{if(document.querySelector('.day.drag'))return;const s=await api('state');if(DAY||PACE||TRV){S=s;return}if(document.querySelector('.day.drag'))return;S=s;render();clearTimeout(fastT);if(S.job&&S.job.running)fastT=setTimeout(load,1000)}catch(e){}}
function authView(kind){
  $('#nav').innerHTML='';$('#sync').innerHTML='';
  if(kind==='no_password'){$('#main').innerHTML=`<div class="wiz"><div class="brandhead">${LOGO}<h1>periodize my run</h1></div><div class="card c12"><p class="h">App password needed</p><p class="mute">No app password has been set, so Periodize My Run cannot be opened from another device yet.</p><p class="small">On the computer running Periodize My Run, run <code>python web.py --set-password</code> in the app folder, then reload this page.</p></div></div>`;return}
  $('#main').innerHTML=`<div class="wiz"><div class="brandhead">${LOGO}<h1>periodize my run</h1><div class="mute">Enter the app password</div></div><div class="card c12"><div class="row"><input id="pw" type="password" aria-label="App password" autocomplete="current-password" style="flex:1"><button class="btn" id="go">Continue</button></div><p id="e" class="red small"></p></div></div>`;
  const go=async()=>{const r=await fetch('/api/auth',{method:'POST',headers:{'Content-Type':'application/json','X-Requested-With':'periodize'},body:JSON.stringify({password:$('#pw').value})});
    if(r.ok)load();else $('#e').textContent=(await r.json()).error};
  $('#go').onclick=go;$('#pw').onkeydown=e=>{if(e.key==='Enter')go()};
}

function render(){
  if(!S)return;CH={};CHN=0;
  if(!S.setup_done||!S.setup_seen){$('#nav').innerHTML='';$('#sync').innerHTML='';if(S.setup_done&&!S.setup_seen)wiz.step=6;return wizard()}
  const T={plan:'Plan',hist:'History',you:'Fitness',races:'Races & status',settings:'Settings',about:'How it works',changes:'Change log',log:'Log'};
  $('#nav').innerHTML=Object.keys(T).map(v=>`<button class="${v===view?'on':''}" data-v="${v}">${T[v]}</button>`).join('');
  $$('#nav button').forEach(b=>b.onclick=()=>{view=b.dataset.v;if(view==='log')loadLogs();if(view==='about')loadAbout();if(view==='changes')loadChanges();if(view==='hist')loadHist();if(view==='you')loadTrends();render();scrollTo({top:0})});
  const j=S.job;
  $('#sync').innerHTML=j.running?`<span class="dot busy"></span>${E(j.progress||'Working')}…`
    :`<span class="dot ${j.error||S.stale?'bad':''}"></span>${S.last_run?'Synced '+E(S.last_run.slice(5).replace('T',' ')):'Not synced yet'} <button class="ghost" id="run">Sync</button>`;
  let h='';
  if(j.error&&!j.running)h+=`<div class="alert err">The last sync had a problem: ${E(j.error)}</div>`;
  if(S.stale)h+=`<div class="alert">No successful sync in 7 days. Check the Log tab, then press Sync.</div>`;
  $('#main').innerHTML=h+({plan:planView,hist:histView,you:youView,races:racesView,settings:settingsView,about:aboutView,changes:changesView,log:logView}[view])();
  bind();bindCharts();
}
function ring(pct,label){const c=2*Math.PI*30;return `<svg class="ring" viewBox="0 0 74 74"><circle cx="37" cy="37" r="30" fill="none" stroke="var(--line)" stroke-width="6"/><circle cx="37" cy="37" r="30" fill="none" stroke="url(#lg)" stroke-width="6" stroke-linecap="round" stroke-dasharray="${c}" stroke-dashoffset="${c*(1-pct)}" transform="rotate(-90 37 37)"/><text x="37" y="42" text-anchor="middle">${label}</text></svg>`}
function chart(title,rows,val,tip,label){
  if(!rows||rows.length<2)return '';
  const vs=rows.map(val), mn=Math.min(...vs), mx=Math.max(...vs), lo=mn-Math.max((mx-mn)*0.25,1);
  return `<p class="xs mute" style="margin:12px 0 0">${E(title)} <span class="mute">· hover or tap a bar</span></p><div class="chart" role="list">${rows.map(x=>`<div class="b" role="listitem" tabindex="0" data-tip="${E(tip(x))}" aria-label="${E(tip(x))}" style="height:${Math.max(6,Math.round(100*(val(x)-lo)/(mx-lo||1)))}%"></div>`).join('')}</div>
    <div class="xs mute" style="display:flex;justify-content:space-between"><span>${E(label(rows[0]))}</span><span>${E(label(rows[rows.length-1]))}</span></div>`}
function stepList(text){return text?`<ul class="steps">${text.split('; ').map(x=>`<li>${E(x)}</li>`).join('')}</ul>`:''}

function planView(){
  const f=S.fitness, r=S.readiness, t=S.days.find(d=>d.today)||{};
  const lev={green:'Recovered',amber:'A bit tired',red:'Not recovered',unknown:'Waiting for watch sync'};
  let h='<div class="grid">'+termsNotice()+updateBanner();
  if(f&&f.goal){const g=f.goal, wk=f.week.weeks_to_race||0;
    h+=`<div class="card hero c6">${ring(Math.max(0.03,Math.min(1,1-g.days/252)),wk+'w')}<p class="eyebrow">Goal</p><p class="h">${E(g.name)}</p>
      <div class="mute small">${nice(g.date)} · ${g.days} days to go</div>
      <div class="stats"><div class="stat"><div class="v num">${g.now}</div><div class="k">If you raced today</div></div>
      <div class="stat" style="border-color:var(--brand)"><div class="v num">${g.forecast.time}</div><div class="k">Race-day forecast${g.forecast.change?` · <span class="${g.forecast.change<0?'green':'amber'}">${g.forecast.change<0?'▼':'▲'} ${fmt(Math.abs(g.forecast.change))} this week</span>`:''}</div></div>
      <div class="stat"><div class="v num">${E(g.target||'—')}</div><div class="k">Your goal</div></div></div>
      ${g.heat?`<p class="small" style="margin:10px 0 0">☀ Race-day weather around 9:00: <b>${g.heat.temp}°C, dew point ${g.heat.dew}°C</b>. ${g.heat.pct===null?'<b class="amber">Very hot and humid: race for the finish, not a time, and start well inside your pace.</b>':g.heat.pct>0?`Expect about <b>${g.heat.pct}%</b> slower than the forecast above; start that much slower.`:'No slowdown expected for the heat.'}</p>`:''}
      ${(fc=>`<p class="small" style="margin:12px 0 0">${fc.gap?`The forecast is <b class="${fc.gap[0]==='ahead'?'green':'amber'}">${fc.gap[1]} ${fc.gap[0]==='ahead'?'ahead of':'behind'}</b> your goal. `:''}It assumes you complete <b>${fc.pct}%</b> of the plan${fc.chosen?`, the figure you set${fc.history_pct!==null?` (your last two years averaged ${fc.history_pct}%${fc.plan_pct!==null&&fc.plan_days>=7?`; this plan so far ${fc.plan_pct}%`:''})`:''}`:fc.plan_weight>=100?', your record on this plan so far':fc.plan_weight>0?`, a blend of your history (${fc.history_pct}%) and this plan so far (${fc.plan_pct}%)`:fc.history_pct!==null?', your average over the last two years':', a general figure until there is history'}.</p>
      <p class="xs mute" style="margin:6px 0 0">Complete all of it: <b class="num">${fc.all}</b> · Complete ${fc.poor_pct}%: <b class="num">${fc.poor}</b>${fc.out_of_reach?' · Your goal is beyond the best you have shown in three years; a new best along the way will move the forecast.':fc.needs_all?' · Your goal is within reach only if nearly all of the plan gets done.':''}</p>`)(g.forecast)}</div>`}
  else h+=`<div class="card hero c6"><p class="eyebrow">Goal</p><p class="h">No goal race yet</p><p class="mute small">Add one under Races & status and the plan will build toward it.</p></div>`;
  h+=`<div class="card c6"><p class="eyebrow">Today ${r&&r.date===S.today?`<span class="chip ${r.level}"><i></i>${lev[r.level]}</span>`:''}</p>
    <p class="h">${E(t.label||'Nothing planned')} <span class="mute num" style="font-weight:600">${E(t.dist||'')}</span></p>
    ${stepList(t.text)}
    ${t.adjust?`<p class="small amber" style="margin:10px 0 0">${t.adjust.easy?`<b>${E(t.adjust.advice||'Changed to an easy run today.')}</b>`:`<b>Paces eased ${(t.adjust.slow*100).toFixed(1)}% today.</b> ${E(t.adjust.advice||'')}`}</p>`:''}
    ${S.heat&&S.heat.today?`<p class="xs mute" style="margin:6px 0 0">☀ Around ${S.heat.today.hour}:00: ${S.heat.today.temp}°C, dew point ${S.heat.today.dew}°C${S.heat.today.pct===null?' · too hot for hard running':S.heat.today.pct>0?` · about ${S.heat.today.pct}% slower for the heat`:' · no heat slowdown'}</p>`:''}
    ${r&&r.date===S.today?`<p class="xs mute" style="margin:10px 0 0">${E(r.reasons.join(' · '))}</p>${r.sleep_h||r.hrv?`<p class="xs mute" style="margin:4px 0 0">Last night: ${[r.sleep_h?r.sleep_h.toFixed(1)+' h sleep':'',r.sleep_score?'sleep score '+r.sleep_score:'',r.hrv?'HRV '+Math.round(r.hrv):'',r.rhr?'resting HR '+Math.round(r.rhr):''].filter(Boolean).join(' · ')}</p>`:''}`:''}
    ${t.note?`<p class="xs mute" style="margin:6px 0 0">${E(t.note)}</p>`:''}${t.strength?`<p class="xs" style="margin:6px 0 0"><span class="tag">+ ${E(t.strength)}</span></p>`:''}</div>`;
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
    h+=`<div class="wk"><b>${names[i]||''}</b><span class="mute small">${nice(w[0].date)} – ${nice(w[6].date)}</span>${total?`<span class="tag">${wi&&S.settings.week_start===0?E(wi.mode)+' · ':''}${U()==='mi'?Math.round(total*2)/2+' mi':Math.round(total*KM)+' km'}</span>`:''}${prov?'<span class="tag">provisional</span>':''}${w[0].week_perf!=null?`<span class="tag ${pc(w[0].week_perf)}" title="Pace for your heart rate across the week's runs, against the four weeks before">pace for heart rate ${w[0].week_perf>0?'+':''}${w[0].week_perf.toFixed(1)}%</span>`:''}
      ${i===1?`<span style="margin-left:auto" class="xs mute">Click a day for detail · drag to swap ${S.can_undo?'· <a href="#" id="undo">Undo last move</a>':''}</span>`:''}</div><div class="cal">`;
    for(const d of w){const can=!d.past&&d.type, b=d.body;
      h+=`<div class="dw"><div class="day ${d.type||''} ${d.past?'past':''} ${d.today?'today':''} ${SEL===d.date?'sel':''}" data-date="${d.date}" ${can?'draggable="true"':''} tabindex="0" role="button" aria-label="${d.dow} ${+d.date.slice(8)}: ${E(d.label||'no session')}">
        <div class="d"><span>${d.dow} ${+d.date.slice(8)}</span><span>${d.done&&d.done.id?'':(d.on_watch?'⌚':'')+(d.source==='moved'?' ↔':'')+(d.source==='reshuffled'?' ↻':'')}</span></div>
        ${d.type?`<div class="l">${E(d.label)}</div>${d.dist?`<div class="m num">${E(d.dist)}</div>`:''}<div class="t">${E(d.short||'')}</div>`:''}
        <div class="f">${d.done?`<span class="done">✓ ${E(d.done.dist)}</span>`:''}${d.adjust?`<span class="tag amber">eased ${(d.adjust.slow*100).toFixed(1)}%</span>`:''}</div>
        ${b?`<div class="mt num"><span class="${fc(b.fresh)}" title="Freshness this morning: last night’s sleep, and your 7-day HRV and resting heart rate, against your normal"><b>${b.fresh}</b></span>${b.sleep_score?`<span title="Last night's sleep score">☾${b.sleep_score}</span>`:''}${b.rhr?`<span title="Resting heart rate">♥${Math.round(b.rhr)}</span>`:''}${b.hrv?`<span title="Last night's HRV">∿${Math.round(b.hrv)}</span>`:''}</div>`:''}</div>${d.done&&d.done.id?GLINK(d.done.id,'corner'):''}</div>`}
    h+='</div>'});
  h+=`<p class="xs mute" style="margin:10px 2px 0">On each day: <b>freshness</b> out of 100, from that night's sleep and your 7-day HRV and resting heart rate, against your normal · ☾ that night's sleep score · ♥ resting heart rate · ∿ that night's HRV. In each week's heading: your pace for your heart rate across the week against the four weeks before. ⌚ on your watch · ↔ moved by you · ↻ moved here because it was missed earlier in the week.</p>`;
  const sd=S.days.find(d=>d.date===SEL);
  if(sd){const b=sd.body, a=sd.adjust, sy=sd.sync, sc={synced:'green',pending:'amber',later:'unknown',off:'unknown',past:'unknown',none:'unknown'};
    h+=`<div class="ov" id="ov"><div class="modal" role="dialog" aria-modal="true" aria-labelledby="mt">
    <p class="eyebrow"><span id="mt">${sd.dow} ${nice(sd.date)} ${sd.date.slice(0,4)}</span><button class="ghost" id="selx" style="margin-left:auto" aria-label="Close">Close</button></p>
    <p class="h">${E(sd.label||'No session planned')} <span class="mute num" style="font-weight:600">${E(sd.dist||'')}</span></p>
    ${sd.type&&sd.type!=='Rest'?`<p class="lab2">${a?'Original session':'Session'}</p>${stepList(a?sd.original:sd.text)}`:''}
    ${a?`<p class="lab2">Tuned for today <span class="chip amber" style="margin-left:6px"><i></i>paces eased ${(a.slow*100).toFixed(1)}%</span></p>${stepList(sd.text)}
      <p class="small" style="margin:8px 0 0">Why: ${E((a.reasons||[]).join('; '))}. ${E(a.advice||'')}</p>`
     :sd.type&&sd.type!=='Rest'&&!sd.past?`<p class="small mute" style="margin:8px 0 0">${sd.today?(b?'Not tuned: last night’s sleep and your HRV and resting heart rate trends are normal, so it stands as planned.':'Not tuned yet: waiting for last night’s data from your watch.'):'Tuning happens on the morning of the session, from the night before and your recent trends.'}</p>`:''}
    ${sd.note?`<p class="small mute" style="margin:8px 0 0">${E(sd.note)}</p>`:''}${sd.strength?`<p class="xs" style="margin:8px 0 0"><span class="tag">+ ${E(sd.strength)}</span></p>`:''}
    ${b?`<p class="lab2">Recovery markers</p><div class="stats" style="grid-template-columns:repeat(auto-fit,minmax(118px,1fr));margin-top:6px">
      <div class="stat"><div class="v num ${fc(b.fresh)}">${b.fresh}</div><div class="k">Freshness</div></div>
      ${b.sleep_h?`<div class="stat"><div class="v num">${b.sleep_h.toFixed(1)} h</div><div class="k">Sleep last night${b.normal.sleep_h?' · normal '+b.normal.sleep_h:''}${b.week.sleep_h?' · 3 nights '+b.week.sleep_h:''}</div></div>`:''}
      ${b.sleep_score?`<div class="stat"><div class="v num">${b.sleep_score}</div><div class="k">Sleep score last night${b.normal.sleep_score?' · normal '+b.normal.sleep_score:''}</div></div>`:''}
      ${b.week.hrv?`<div class="stat"><div class="v num">${b.week.hrv}</div><div class="k">HRV, 7-day${b.normal.hrv?' · normal '+b.normal.hrv:''}${b.hrv?' · last night '+Math.round(b.hrv):''}</div></div>`:''}
      ${b.week.rhr?`<div class="stat"><div class="v num">${b.week.rhr}</div><div class="k">Resting HR, 7-day${b.normal.rhr?' · normal '+b.normal.rhr:''}${b.rhr?' · today '+Math.round(b.rhr):''}</div></div>`:''}</div>
      ${a?'':`<p class="xs mute" style="margin:8px 0 0">${E(b.reasons.join('; '))}</p>`}`:''}
    ${sd.fuel?`<p class="lab2">Fuelling · about ${Math.floor(sd.fuel.minutes/60)} h ${String(sd.fuel.minutes%60).padStart(2,'0')}</p><p class="small" style="margin:4px 0 0">${E(sd.fuel.text)}${sd.fuel.per_hour<sd.fuel.guide&&!sd.fuel.race?` <span class="mute">The guideline for this length is up to ${sd.fuel.guide} g an hour; the plan steps you up toward race day.</span>`:''}</p>`:''}
    ${sd.done?`<p class="lab2">What you ran</p><p class="small" style="margin:4px 0 0"><b class="num">${E(sd.done.dist)}</b> at ${E(sd.done.pace)}${sd.done.runs>1?` over ${sd.done.runs} runs`:''} ${sd.done.id?GLINK(sd.done.id):''} <button class="ghost" data-dopen="${sd.date}" style="margin-left:8px">Run detail</button></p>`:''}
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
  if(f)h+=`<div class="grid" style="margin-top:22px"><div class="card c12"><p class="eyebrow">Why this week looks like this</p><ul class="why">${f.week.why.map(w=>`<li>${E(w)}</li>`).join('')||'<li>Nothing unusual.</li>'}</ul></div></div>`;
  return h;
}
function youView(){
  const f=S.fitness,p=S.profile,L=S.limits,st=S.steps;if(!f)return '<div class="grid"><div class="card c12">No plan yet.</div></div>';
  const t=s=>s?`<span class="num">${fmt(s.time_s)}</span> <span class="mute xs">${nice(s.date)} ${s.date.slice(0,4)}</span>`:'—';
  return `<div class="grid">
  <div class="card"><p class="eyebrow" style="display:flex;align-items:center">Threshold pace ${trendBtn('speed')}</p>${TR&&TR.speed?dirTag(TR.speed.dir,TR.speed.window):''}<div class="big num">${E(f.threshold)}</div><p class="small mute">${f.change>=0?'+':''}${f.change.toFixed(1)}% on last week. Best evidence: ${E(f.evidence)}.</p>
    ${S.watch_threshold?(w=>`<p class="xs mute" id="wthr" style="margin:8px 0 0">Your watch's estimate: <b class="num">${E(w.pace)}</b>${w.hr?` at <b class="num">${w.hr}</b> bpm`:''} (${w.date?nice(w.date):'undated'}), ${Math.abs(w.diff)<0.5?'the same as':Math.abs(w.diff)+'% '+(w.diff>0?'faster than':'slower than')} the figure above. ${w.used?'It counts as evidence while it is under six weeks old.':'It is more than six weeks old, so it is shown but not used.'}</p>`)(S.watch_threshold):''}</div>
  <div class="card"><p class="eyebrow" style="display:flex;align-items:center">Race-specific endurance ${trendBtn('base')}</p>${TR&&TR.base?dirTag(TR.base.dir,TR.base.window):''}<div class="big num">${Math.round(f.endurance*100)}%</div>
    ${Object.entries(f.endurance_parts).map(([k,v])=>`<div class="xs mute" style="margin-top:8px">${E(k)} · ${Math.round(v*100)}%</div><div class="bar"><i style="width:${Math.round(v*100)}%"></i></div>`).join('')}</div>
  <div class="card"><p class="eyebrow" style="display:flex;align-items:center">Steps outside your runs ${trendBtn('steps')}</p>${TR&&TR.steps?dirTag(TR.steps.dir,TR.steps.window):''}${st?`<div class="big num">${st.week.toLocaleString()}</div><p class="small mute">a day over the last 7 days. Your normal is ${st.normal.toLocaleString()}${st.yesterday!=null?`; yesterday ${st.yesterday.toLocaleString()}`:''}. About ${U()==='mi'?st.miles_week+' mi':Math.round(st.miles_week*KM)+' km'} of walking a week that the plan does not schedule.</p>
    <div class="bar"><i style="width:${Math.min(100,Math.round(50*st.week/Math.max(st.normal,1)))}%"></i></div><p class="xs mute" style="margin:6px 0 0">Unusually heavy days and weeks ease your training. See How it works.</p>`:'<p class="small mute">Builds up once a few weeks of step counts are in.</p>'}</div>
  ${S.aerobic?(a=>`<div class="card c12"><p class="eyebrow">Is it working? Pace at the same heart rate</p>
    <div class="grid" style="gap:22px"><div style="grid-column:span 7;min-width:0"><table><tr><th>Month</th>${a.monthly.stages.map(x=>`<th class="r">${x} bpm</th>`).join('')}</tr>
      ${a.monthly.rows.map(r=>`<tr><td>${new Date(r.month+'-15').toLocaleDateString(undefined,{month:'short',year:'numeric'})}</td>${r.cells.map(c=>`<td class="r num">${c.pace?`<b>${c.pace}</b>`:'<span class="mute">—</span>'}</td>`).join('')}</tr>`).join('')}
      <tr><td class="mute">Change</td>${a.monthly.change.map(c=>`<td class="r num ${c.s===null?'mute':c.s<0?'green':c.s>0?'amber':''}">${c.s===null?'—':(c.s<0?'▼ ':c.s>0?'▲ ':'')+fmt(Math.abs(c.s))}</td>`).join('')}</tr></table>
      <p class="xs mute" style="margin:8px 0 0">From your road runs, with hills adjusted to their flat equivalent, per ${U()==='mi'?'mile':'km'}. Trail runs are left out. Faster at the same heart rate is the sign the aerobic work is paying off. Not adjusted for wind or heat. A month needs 20 minutes at a heart rate to show.</p></div>
    <div style="grid-column:span 5;min-width:0"><p class="small" style="margin:0 0 6px"><b>Aerobic tests</b> ${a.next_test?`<span class="tag">next: ${nice(a.next_test)}</span>`:''}</p>
      ${a.tests.length?`<table><tr><th>Date</th>${a.tests[a.tests.length-1].stages.map(s=>`<th class="r">${s.hr}</th>`).join('')}<th></th></tr>${a.tests.slice(-6).map(t=>`<tr><td>${nice(t.date)}</td>${t.stages.map(s=>`<td class="r num">${s.pace}</td>`).join('')}<td class="r"><button class="ghost" data-hdel="${t.date}" aria-label="Remove test ${t.date}">×</button></td></tr>${t.change!=null?`<tr><td colspan="${t.stages.length+2}" class="xs ${t.change<0?'green':'amber'}">${t.change<0?'▼':'▲'} ${fmt(Math.abs(t.change))} per ${U()==='mi'?'mile':'km'} on average against the test before</td></tr>`:''}`).join('')}</table>`
        :`<p class="small mute">No tests yet. One is scheduled about every month: ${a.format==='original'?`${a.test_stages.length} stages of 2400 m at ${a.test_stages.join(', ')} bpm`:`a mile at each of ${a.test_stages.join(', ')} bpm, then 500 m all out`}. Run it from your watch and the result appears here.</p>`}
      ${a.peak?`<p class="xs mute" style="margin:8px 0 0">Highest heart rate in your last test: <b>${a.peak.bpm}</b> (${nice(a.peak.date)}).</p>`:''}<p class="xs mute" style="margin:8px 0 0">Expect small changes after 3 weeks and clear ones after 6. Aerobic runs are at <b>${a.lthr}–${a.lthr+5} bpm</b> now; that moves up 5 when you run 10 miles there.</p>
      <details style="margin-top:8px"><summary class="xs" style="cursor:pointer">Enter a test by hand</summary><div class="row" style="margin-top:6px"><div><label for="hd">Date</label><input id="hd" type="date" value="${S.today}"></div>
        ${a.test_stages.map((x,i)=>`<div><label for="ht${i}">${x} bpm: ${a.format==='original'?'2400 m':'mile'} time</label><input id="ht${i}" data-hr="${x}" class="hst" placeholder="mm:ss" size="6"></div>`).join('')}<button class="btn" id="aerobic">Save test</button></div></details></div></div>
    ${a.relationship?`<p class="small" style="margin:16px 0 4px"><b>Your race paces as the distance doubles:</b> you slow by <b class="num">${a.relationship.per_doubling} s</b> per ${U()==='mi'?'mile':'km'} per doubling from ${E(a.relationship.from)} to ${E(a.relationship.to)}, which is <b>${a.relationship.verdict}</b>. ${a.relationship.verdict==='tight'?'Your endurance supports your speed.':'A tighter spread comes from more easy miles and aerobic runs, not from faster training.'}</p>
      <div style="overflow:auto"><table><tr><th>Best in 3 years</th><th class="r">Pace</th><th class="r">Rule-of-thumb target</th><th class="r">Gap</th></tr>${a.relationship.rows.map(r=>`<tr><td>${E(r.name)} <span class="mute xs">${r.date.slice(0,4)}${r.adjusted?` · hills adjusted (${r.course>0?'+':''}${r.course}%)`:' · as raced'}</span></td><td class="r num"><b>${r.pace}</b></td><td class="r num mute">${r.target}</td><td class="r num ${r.gap>3?'amber':'green'}">${r.gap>0?'+':''}${r.gap} s</td></tr>`).join('')}</table></div>
      <p class="xs mute" style="margin:8px 0 0">Treat this as a rough guide. The target is a rule of thumb (${16} s per mile per doubling) for flat courses in still, cool conditions. ${a.relationship.adjusted} of these ${a.relationship.of} paces are adjusted for the course's hills; the rest are as raced, because the watch that recorded them had unreliable altitude or the race predates detailed data. Nothing here allows for wind, heat or surface.</p>`:''}
  </div>`)(S.aerobic):''}
  ${S.form?(F=>`<div class="card c8" id="formcard"><p class="eyebrow">Fitness, fatigue and form</p>
    <div class="stats" style="margin-top:0"><div class="stat"><div class="v num">${Math.round(F.fitness)}</div><div class="k">Fitness${F.fitness_4w_ago!=null?` · ${F.fitness>=F.fitness_4w_ago?'+':''}${Math.round(F.fitness-F.fitness_4w_ago)} in 4 weeks`:''}</div></div>
      <div class="stat"><div class="v num">${Math.round(F.fatigue)}</div><div class="k">Fatigue</div></div>
      <div class="stat"><div class="v num ${F.form<-20?'red':F.form<-10?'amber':'green'}">${F.form>0?'+':''}${Math.round(F.form)}</div><div class="k">Form · ${F.form<-20?'deep in the red: ease off':F.form<-10?'building hard':F.form<5?'building':'fresh'}</div></div></div>
    ${(rows=>{const tip=s=>nice(s[6])+': fitness '+Math.round(s[1])+', fatigue '+Math.round(s[2])+', form '+(s[3]>0?'+':'')+Math.round(s[3])+', load that day '+s[4];
      return lineChart(rows,1,'var(--brand)','Fitness, last '+rows.length+' days',v=>Math.round(v),false,tip)+lineChart(rows,2,'var(--amber)','Fatigue',v=>Math.round(v),false,tip)+lineChart(rows,3,'var(--race)','Form',v=>Math.round(v),false,tip)})(F.days.map((d,i)=>[i,d.fitness,d.fatigue,d.form,d.load,0,d.date]))}
    <p class="xs mute" style="margin:8px 0 0">Load this week ${F.week}, last week ${F.prev_week}. Fitness is your daily load averaged over about six weeks, fatigue over one; form is the difference. See How it works.</p></div>
  <div class="card" id="driftcard"><p class="eyebrow" style="display:flex;align-items:center">Aerobic drift on long runs ${trendBtn('durability')}</p>${TR&&TR.durability?dirTag(TR.durability.dir,TR.durability.window):''}${S.drift&&S.drift.length?`<table><tr><th>Date</th><th class="r">Run</th><th class="r">Drift</th></tr>${S.drift.slice().reverse().slice(0,7).map(d=>`<tr><td>${nice(d.date)}</td><td class="r num">${U()==='mi'?d.mi+' mi':Math.round(d.mi*KM)+' km'}</td><td class="r num ${d.drift<=5?'green':'amber'}"><b>${d.drift}%</b></td></tr>`).join('')}</table>
    <p class="xs mute" style="margin:8px 0 0">How much pace per heartbeat faded in the second half. Lower is better; under 5% is the usual rule of thumb. Heat and hills raise it.</p>`:'<p class="small mute">Appears after a steady run of 70 minutes or more.</p>'}</div>`)(S.form):''}
  <div class="card c12" id="shoecard"><p class="eyebrow">Shoes</p>${S.shoes.length?`<table>${S.shoes.map(s=>`<tr><td><b>${E(s.name)}</b> ${s.current?'<span class="tag green">in use</span>':s.retired?'<span class="tag">retired</span>':''}</td><td class="mute">since ${nice(s.start)} ${s.start.slice(0,4)}</td><td class="r num ${s.over?'amber':''}"><b>${s.dist} ${U()}</b>${s.alert?` <span class="mute">of ${s.alert}</span>`:''}</td><td class="r num mute">${s.runs} runs</td><td class="r"><button class="ghost" data-shdel="${s.id}" aria-label="Remove ${E(s.name)}">Remove</button></td></tr>`).join('')}</table>`:'<p class="small mute">No shoes yet. Add the pair you run in and its distance is counted from your runs.</p>'}
    <div class="row"><div><label for="shn">Name</label><input id="shn" placeholder="Shoe name" maxlength="60"></div><div><label for="shs">Using since</label><input id="shs" type="date" value="${S.today}"></div>
    <div><label for="shm">Distance already on them (${U()})</label><input id="shm" type="number" min="0" size="6"></div><div><label for="sha">Tell me at (${U()}, optional)</label><input id="sha" type="number" min="50" size="6"></div><button class="ghost" id="shadd">Add shoes</button></div>
    <p class="xs mute" style="margin:8px 0 0">A pair counts every run from its start date until the next pair's start date.</p></div>
  <div class="card c8"><p class="eyebrow">Race predictor</p>${S.predictions?`<table><tr><th>Distance</th><th class="r">If you raced today</th><th class="r">Pace</th><th class="r">With endurance built</th><th class="r">Last 6 weeks</th></tr>${S.predictions.map(x=>{const d=TR&&TR.predictions?TR.predictions[x.name]:undefined;return `<tr><td>${E(x.name)}</td><td class="r num"><b>${x.now}</b></td><td class="r num mute">${E(x.pace)}</td><td class="r num">${x.gap?`${x.full} <span class="mute xs">(${x.gap} faster)</span>`:'<span class="mute">same</span>'}</td><td class="r num ${d<0?'green':d>0?'amber':'mute'}">${d==null?'—':d===0?'same':(d<0?'▼ ':'▲ ')+fmt(Math.abs(d))}</td></tr>`}).join('')}</table>
    <p class="xs mute" style="margin:8px 0 0">Times come from your current speed and your own record across distances. For the longer races, part of today's time is endurance you have not built yet: "with endurance built" is the time at the same speed once your long runs and race-pace miles are in place. "Last 6 weeks" shows how each prediction has moved: short races follow your speed, long ones also your endurance, so the column shows which kind of fitness you are gaining. Getting faster on top of that moves every row. 50K ignores terrain.</p>`:'<p class="small mute">Available once a plan exists.</p>'}</div>
  <div class="card"><p class="eyebrow">VO2max</p>${S.vo2?`<div class="big num">${S.vo2.garmin??'—'}</div><div class="xs mute">Garmin's estimate${S.vo2.garmin_date?', '+nice(S.vo2.garmin_date):''}</div>
    ${chart('Garmin VO2max by year',S.vo2.by_year,x=>x.v,x=>x.y+': '+x.v,x=>x.y)}
    <p class="xs mute" style="margin:8px 0 0">Garmin's own estimate from your watch, shown for reference. The app's paces and predictions come from your running, not from this figure.</p>`:'<p class="small mute">Available once a plan exists.</p>'}</div>
  ${accuracyCard()}${recoveryCard()}${trendModal()}
  <div class="card c12"><p class="eyebrow">Race results</p>${S.results.length?`<div style="max-height:340px;overflow:auto"><table><tr><th>Date</th><th>Race</th><th class="r">Time</th><th class="r">Pace</th><th class="r">Age grade</th><th></th><th></th></tr>${S.results.map(x=>`<tr><td class="num">${nice(x.date)} ${x.date.slice(0,4)}</td><td>${E(x.name)}${x.note?`<div class="xs mute" style="max-width:520px">${E(x.note)}</div>`:''}</td><td class="r num"><b>${fmt(x.time_s)}</b></td><td class="r num mute">${E(x.pace)}</td><td class="r num">${x.age_grade?x.age_grade+'%':'<span class="mute">—</span>'}</td><td><span class="tag">${{found:'found in Garmin',log:'your log',entered:'entered'}[x.source]||x.source}</span>${x.counts?'':' <span class="tag">not counted</span>'}</td><td class="r" style="white-space:nowrap"><button class="ghost" data-redit="${x.id}" aria-label="Correct ${E(x.name)}">Correct</button> <button class="ghost" data-rdel="${x.id}" aria-label="Remove ${E(x.name)}">Not a race</button></td></tr>`).join('')}</table></div>`:'<p class="small mute">None yet. They are found in your Garmin history, or add one below.</p>'}
    ${S.best_grade?`<p class="xs mute" style="margin:8px 0 0">Best age grade: <b class="num">${S.best_grade.age_grade}%</b> (${E(S.best_grade.name.split(' · ')[0])}, ${S.best_grade.date.slice(0,4)}). Age grade is your time against the world-best standard for your age and sex.</p>`:S.about_you.sex&&S.about_you.birth_date?'':'<p class="xs mute" style="margin:8px 0 0">Add your sex and date of birth under Settings to see age grades.</p>'}
    <div class="row"><div><label for="xn">Race</label><input id="xn" placeholder="Race name"></div><div><label for="xd">Date</label><input id="xd" type="date"></div>
    <div><label for="xm">Distance</label><select id="xm">${DIST.map(d=>`<option value="${d[1]}">${d[0]}</option>`).join('')}<option value="c">Other</option></select></div>
    <div id="xow" style="display:none"><label for="xo">Distance in ${U()==='mi'?'miles':'km'}</label><input id="xo" type="number" step="0.1" size="6" style="width:90px"></div>
    <div><label for="xt">Time</label><input id="xt" placeholder="1:04:32" size="9"></div>
    <div><label for="xs">Surface</label><select id="xs"><option value="0">Road or track</option><option value="1">Trail, hills or cross-country (not counted)</option></select></div><button class="btn" id="xadd">Add result</button>
    <label class="ghost" style="margin:0;cursor:pointer" for="ximp">Import a race log (CSV)</label><input id="ximp" type="file" accept=".csv,text/csv" style="position:absolute;opacity:0;width:1px;height:1px"></div>
    <p class="xs mute" style="margin:8px 0 0">A race log needs a Date column and a Length or Miles column; Time, Location, Weight and Comment columns are used if present.</p></div>
  <div class="card c6"><p class="eyebrow">Paces now</p><table>${Object.entries(f.zones).map(([k,v])=>`<tr><td>${E(k[0].toUpperCase()+k.slice(1))}</td><td class="r num"><b>${E(v)}</b></td></tr>`).join('')}</table></div>
  <div class="card c6"><p class="eyebrow">Last eight weeks</p><table><tr><th>Week</th><th class="r">Distance</th><th class="r">Runs</th><th class="r">Longest</th><th class="r">Threshold min</th></tr>${f.history.map(w=>`<tr><td>${nice(w.start)}</td><td class="r num">${E(w.dist)}</td><td class="r num">${w.runs}</td><td class="r num">${w.long}</td><td class="r num">${w.t_min}</td></tr>`).join('')}</table></div>
  <div class="card"><p class="eyebrow">Your history</p><table><tr><td>Running since</td><td class="r">${E(p.first_run.slice(0,4))}</td></tr><tr><td>Runs</td><td class="r num">${p.runs.toLocaleString()}</td></tr><tr><td>Lifetime</td><td class="r num">${dU(p.miles)}</td></tr>
    <tr><td>Last 8 weeks, per week</td><td class="r num">${dU(p.recent8)}</td></tr><tr><td>Best 8 weeks in 3 years</td><td class="r num">${dU(p.best8_3y)}</td></tr><tr><td>Breaks of 2+ weeks in 3 years</td><td class="r num">${p.layoffs_3y.length}</td></tr></table></div>
  <div class="card c8"><p class="eyebrow">Personal bests</p>${S.bests.length?`<table><tr><th>Distance</th><th class="r">Best</th><th>Where</th><th class="r">Last 12 months</th></tr>${S.bests.map(x=>`<tr><td>${E(x.name)}</td><td class="r num"><b>${fmt(x.best.time_s)}</b></td><td>${E(x.best.race)} <span class="mute xs">${x.best.date.slice(0,4)}${x.best.official?'':' · from your watch'}</span>${x.watch?`<div class="xs mute">Faster on your watch, not in your log: ${fmt(x.watch.time_s)} (${nice(x.watch.date)} ${x.watch.date.slice(0,4)})</div>`:''}</td><td class="r num">${x.year?fmt(x.year.time_s):'<span class="mute">—</span>'}</td></tr>`).join('')}</table>
    <p class="xs mute" style="margin:8px 0 0">From your race results. Times from your own log are official and come first; add or correct results in the table above.</p>`:'<p class="small mute">No race results yet.</p>'}</div>
  <div class="card"><p class="eyebrow">Your limits, from your history</p><table><tr><td>Peak week</td><td class="r num">${dU(L.peak_miles)}</td></tr><tr><td>Longest long run</td><td class="r num">${dU(L.long_run_cap_specific)}</td></tr><tr><td>Maximum heart rate</td><td class="r num">${L.hrmax}</td></tr><tr><td>Easy under</td><td class="r num">${L.easy_hr_max} bpm</td></tr><tr><td>Threshold cap</td><td class="r num">${L.threshold_hr_cap} bpm</td></tr></table>
    <p class="xs mute" style="margin:8px 0 0">Warning signs this week: ${f.week.flags.length?E(f.week.flags.join('; ')):'none'}.</p></div>
  <div class="card c12"><p class="eyebrow">Plan against actual</p>${S.compliance.length?`<table><tr><th>Week</th><th class="r">Planned</th><th class="r">Done</th><th class="r"></th></tr>${S.compliance.map(w=>`<tr><td>${nice(w.week)}</td><td class="r num">${E(w.planned)}</td><td class="r num">${E(w.done)}</td><td class="r num">${w.pct}%</td></tr>`).join('')}</table>`:'<p class="small mute">Builds up as planned days pass.</p>'}
    ${S.weight?`<p class="small" style="margin:12px 0 0">Weight, 7-day average: <b class="num">${S.weight.now} kg</b>${S.weight.change!==null?` <span class="mute">(${S.weight.change>0?'+':''}${S.weight.change} kg in 4 weeks)</span>`:''}</p>`:''}</div></div>`;
}
function raceForm(){return `<div class="row"><div><label for="rn">Race name</label><input id="rn" placeholder="Race name"></div><div><label for="rd">Date</label><input id="rd" type="date"></div>
  <div><label for="rm">Distance</label><select id="rm">${DIST.map(d=>`<option value="${d[1]}" ${d[0]==='Marathon'?'selected':''}>${d[0]}</option>`).join('')}<option value="c">Other (miles)</option></select></div>
  <div><label for="rp">Importance</label><select id="rp"><option value="A">Goal race</option><option value="B">Tune-up race</option></select></div>
  <div><label for="rg">Goal time (optional)</label><input id="rg" placeholder="3:00:00" size="8"></div><button class="btn" id="radd">Add race</button></div>`}
function raceRead(){let m=$('#rm').value;if(m==='c')m=prompt('Distance in miles?');return {name:$('#rn').value,date:$('#rd').value,miles:parseFloat(m),priority:$('#rp').value,goal_time:$('#rg').value}}
function raceRows(){return S.races.length?`<div style="overflow:auto"><table>${S.races.map(r=>`<tr><td><b>${E(r.name)}</b></td><td>${nice(r.date)} ${r.date.slice(0,4)}</td><td class="num">${r.miles} mi</td><td><span class="tag">${r.priority==='A'?'Goal race':'Tune-up'}</span></td><td class="num">${E(r.goal_time||'')}</td><td>${r.climb_m!=null?`<span class="tag">${Math.round(r.climb_m)} m climb${r.has_course?' · course added':''}</span>`:'<span class="mute xs">no course</span>'}</td>
    <td class="r">${r.has_course?`<button class="ghost" data-pace="${r.id}">Pacing plan</button> `:''}<button class="ghost" data-gpx="${r.id}">${r.has_course?'Replace course':'Add course (GPX)'}</button><input id="gpx${r.id}" class="gpx" data-race="${r.id}" type="file" accept=".gpx,application/gpx+xml" hidden aria-label="Course file for ${E(r.name)}">
      <button class="ghost" data-climb="${r.id}" aria-label="Set total climb for ${E(r.name)}">Set climb</button> <button class="ghost" data-del="${r.id}">Remove</button></td></tr>`).join('')}</table></div>`:'<p class="small mute">No races yet.</p>'}
function paceModal(){if(!PACE)return '';const P=PACE,u=P.units,pp=v=>v==null?'—':Math.floor(v/60)+':'+String(Math.round(v%60)).padStart(2,'0');
  return `<div class="ov" id="pov"><div class="modal" style="width:min(680px,100%)" role="dialog" aria-modal="true" aria-labelledby="pmt"><p class="eyebrow"><span id="pmt">Pacing plan</span><button class="ghost" id="pacex" style="margin-left:auto" aria-label="Close">Close</button></p>
    <p class="h">${E(P.race)} <span class="mute num" style="font-weight:600">${fmt(P.target_s)}</span></p>
    <p class="small" style="margin:4px 0 0">Even effort over the course, for ${E(P.source)}. Flat-equivalent pace <b class="num">${pp(P.flat_pace_s)}/${u}</b> · total climb <b class="num">${P.climb_m} m</b>. Slowest ${u==='mi'?'mile':'km'} is ${P.slowest}, fastest is ${P.fastest}.</p>
    ${P.ultra?'<p class="xs amber" style="margin:6px 0 0">For an ultra this shows how effort should be spread, not times to hit: it does not model fatigue or footing.</p>':''}
    <div class="row" style="align-items:flex-end;margin-top:10px"><div><label for="ptime">Target time (h:mm:ss)</label><input id="ptime" size="9" value="${fmt(P.target_s)}"></div><button class="ghost" id="pgo" data-race="${P.id}">Recalculate</button></div>
    <div style="max-height:46vh;overflow:auto;margin-top:10px" tabindex="0" role="region" aria-label="Splits"><table><tr><th>${u==='mi'?'Mile':'Km'}</th><th class="r">Pace</th><th class="r">Split</th><th class="r">Elapsed</th><th class="r">Up</th><th class="r">Down</th></tr>
      ${P.rows.map(r=>`<tr><td class="num">${r.n}${r.len<0.99?` <span class="mute xs">(${r.len})</span>`:''}${r.walk?' <span class="tag" title="Sustained climb of 20% or steeper: walking it costs less than running">walk</span>':''}</td><td class="r num ${r.pace_s>P.flat_pace_s*1.03?'amber':r.pace_s<P.flat_pace_s*0.97?'green':''}"><b>${pp(r.pace_s)}</b></td><td class="r num mute">${pp(r.split_s)}</td><td class="r num">${fmt(r.cum_s)}</td><td class="r num mute">${r.up_m||''}</td><td class="r num mute">${r.down_m||''}</td></tr>`).join('')}</table></div>
    <p class="xs mute" style="margin:8px 0 0">Amber splits are uphill and slower than flat pace; green are downhill and faster. ${P.rows.some(r=>r.walk)?'<b>walk</b> marks a sustained climb of 20% or steeper: in a long race, walking it briskly costs less than running. ':''}Wind, heat and crowding are not allowed for.</p></div></div>`}
async function readGpx(file){
  if(file.size>30e6)throw new Error('That file is too large.');
  const doc=new DOMParser().parseFromString(await file.text(),'application/xml');
  let pts=[...doc.getElementsByTagName('trkpt')];if(!pts.length)pts=[...doc.getElementsByTagName('rtept')];
  const R=6371000,rad=x=>x*Math.PI/180;let d=0,last=null,lastOut=-1e9;const out=[];
  for(const p of pts){const la=+p.getAttribute('lat'),lo=+p.getAttribute('lon'),el=p.getElementsByTagName('ele')[0];if(isNaN(la)||isNaN(lo)||!el)continue;const e=+el.textContent;if(isNaN(e))continue;
    if(last){const a=Math.sin(rad(la-last[0])/2)**2+Math.cos(rad(last[0]))*Math.cos(rad(la))*Math.sin(rad(lo-last[1])/2)**2;d+=2*R*Math.asin(Math.sqrt(a))}
    last=[la,lo];if(d-lastOut>=50||!out.length){out.push([Math.round(d),Math.round(e*10)/10]);lastOut=d}}
  if(out.length<20)throw new Error('No track with elevation was found in that file.');
  return out}
function racesView(){
  return `<div class="grid"><div class="card c12"><p class="eyebrow">Races</p>${raceRows()}<p class="xs mute" style="margin:8px 0 0">Add a race's course as a GPX file for a split-by-split pacing plan that allows for the hills, and climb targets in training if it is hilly. The file is read here in your browser; only distance and elevation are stored.</p>${raceForm()}</div>${paceModal()}
  <div class="card c12"><p class="eyebrow">Sick, injured or on holiday</p><p class="small mute" style="margin-top:0">Sick or injured: the plan rests you, then brings you back with easy running. Holiday: choose how you want to run while away. Saving replans from today.</p>
    ${S.statuses.length?`<table>${S.statuses.map(s=>`<tr><td><span class="chip ${s.kind==='holiday'?'green':s.end?'unknown':'red'}"><i></i>${{sick:'Sick',injured:'Injured',holiday:'Holiday'}[s.kind]}</span></td><td>${nice(s.start)} → ${s.end?nice(s.end):'ongoing'}</td><td>${s.kind==='holiday'?`<b>${E(S.holiday_modes[s.mode]||'')}</b> `:''}${E(s.note)}</td><td class="r">${s.end?'':`<button class="ghost" data-better="${s.id}">${s.kind==='holiday'?"I'm back today":"I'm better today"}</button>`} <button class="ghost" data-sdel="${s.id}">Remove</button></td></tr>`).join('')}</table>`:''}
    <div class="row"><div><label for="sk">What</label><select id="sk"><option value="sick">Sick</option><option value="injured">Injured</option><option value="holiday">Holiday</option></select></div>
    <div id="smw" style="display:none"><label for="sm">On holiday I want to run</label><select id="sm">${Object.entries(S.holiday_modes).map(([k,v])=>`<option value="${k}" ${k==='easy'?'selected':''}>${E(v)}</option>`).join('')}</select></div><div><label for="ss">From</label><input id="ss" type="date" value="${S.today}"></div>
    <div><label for="se">Until (empty if unknown)</label><input id="se" type="date"></div><div><label for="sn">Note</label><input id="sn" placeholder="e.g. cold, calf, travel"></div><button class="btn" id="sadd">Save</button></div></div></div>`;
}
const opt=(v,l,cur)=>`<option value="${v}" ${String(cur)===String(v)?'selected':''}>${l}</option>`;
const yn=(id,cur,dis)=>`<select id="${id}" ${dis?'disabled':''}>${opt(1,'Yes',cur?1:0)}${opt(0,'No',cur?1:0)}</select>`;
function prefs(s){return `<div class="row"><div><label for="units">Distances in</label><select id="units">${opt('mi','Miles',s.units)}${opt('km','Kilometres',s.units)}</select></div>
  <div><label for="run_days">Running days a week</label><select id="run_days">${[3,4,5,6].map(n=>opt(n,n,s.run_days)).join('')}</select></div>
  <div><label for="long_day">Long run day</label><select id="long_day">${DOW.map((d,i)=>opt(i,d,s.long_day)).join('')}</select></div>
  <div><label for="week_start">Week starts on</label><select id="week_start">${DOW.map((d,i)=>opt(i,d,s.week_start)).join('')}</select></div>
  <div><label for="run_time">Daily sync time</label><input id="run_time" type="time" value="${s.run_time}"></div></div>
  <div class="lab" id="bl">Days you cannot run</div><div id="blocked" class="checks" role="group" aria-labelledby="bl">${DOW.map((d,i)=>`<label><input type="checkbox" value="${i}" ${(s.blocked_days||[]).includes(i)?'checked':''}>${d.slice(0,3)}</label>`).join('')}</div>
  <div class="row"><div><label for="push_enabled">Send workouts to my watch</label>${yn('push_enabled',s.push_enabled)}</div>
  <div><label for="daily_adjust">Ease paces on poor recovery</label>${yn('daily_adjust',s.daily_adjust)}</div>
  <div><label for="strength">Strength sessions</label>${yn('strength',s.strength)}</div>
  <div><label for="easy_target">Easy runs on the watch</label><select id="easy_target">${opt('none','No pace alerts',s.easy_target)}${opt('pace','Pace range alerts',s.easy_target)}</select></div></div>
  <p class="xs mute">Set the sync time for after you usually wake and your watch has synced, so last night's sleep is counted.</p>`}
function prefsRead(){return {week_start:+$('#week_start').value,units:$('#units').value,run_days:+$('#run_days').value,long_day:+$('#long_day').value,run_time:$('#run_time').value,push_enabled:$('#push_enabled').value==='1',
  blocked_days:$$('#blocked input:checked').map(x=>+x.value),daily_adjust:$('#daily_adjust').value==='1',easy_target:$('#easy_target').value,strength:$('#strength').value==='1'}}
function settingsView(){const s=S.settings;
  return `<div class="grid sgrid"><div class="card c12"><p class="eyebrow">How you train</p>${prefs(s)}</div>
  <div class="card c12"><p class="eyebrow">Advanced</p><div class="fgrid">
    <div><label for="hrmax">Maximum heart rate (empty: use ${S.profile.hrmax_observed||'observed'})</label><input id="hrmax" type="number" value="${s.hrmax||''}"></div>
    <div><label for="peak">Peak week in miles (empty: use ${S.limits.peak_miles}, from your history)</label><input id="peak" type="number" value="${s.peak_miles_override||''}"></div>
    <div><label for="forecast_completion">Plan completion assumed in the forecast</label><select id="forecast_completion">${opt('','From my history and this plan',s.forecast_completion?Math.round(s.forecast_completion*100):'')}${[70,75,80,85,90,95,100].map(n=>opt(n,n+'%',s.forecast_completion?Math.round(s.forecast_completion*100):'')).join('')}</select></div>
    <div><label for="aero_test_weeks">Aerobic test</label><select id="aero_test_weeks">${opt(0,'Off',s.aero_test?s.aero_test_weeks:0)}${[4,5,6,8].map(n=>opt(n,'Every '+n+' weeks',s.aero_test?s.aero_test_weeks:0)).join('')}</select></div>
    <div><label for="aero_format">Aerobic test format</label><select id="aero_format">${opt('short','Short: mile stages, then 500 m all out (about 6 miles)',s.aero_format)}${opt('original',"Long: 2400 m stages with rests (about 10 miles)",s.aero_format)}</select></div>
    <div><label for="aero_runs">Aerobic runs by heart rate</label>${yn('aero_runs',s.aero_runs)}</div>
    <div><label for="weeks_ahead">Provisional weeks shown ahead</label><select id="weeks_ahead">${[1,2,3,4,5].map(n=>opt(n,n,s.weeks_ahead)).join('')}</select></div>
    <div><label for="push_days">Days kept on the watch</label><select id="push_days">${[7,14,21].map(n=>opt(n,n,s.push_days)).join('')}</select></div>
    <div><label for="notify">Daily message address (optional)</label><input id="notify" style="width:100%" value="${E(s.notify_url||'')}" placeholder="https://ntfy.sh/your-private-topic"><p class="xs mute" style="margin:6px 0 0">A morning message with the day's session. Save first, then send a test.</p><p style="margin:8px 0 0"><button class="ghost" id="ntest" ${S.notify_set?'':'disabled'}>Send a test message</button></p></div></div>
    <div class="row" style="align-items:center;margin-top:18px;border-top:1px solid var(--line);padding-top:16px"><button class="btn" id="ssave">Save and replan</button><span class="xs mute">Applies to How you train and Advanced.</span>
    <a class="ghost" style="margin-left:auto" href="/api/export">Download backup</a><span class="small mute">App password: ${S.has_password?'set':'not set'}</span></div></div>
  <div class="card" id="youcard"><p class="eyebrow">About you</p><p class="xs mute" style="margin-top:0">Used only for age grading and fuelling. Read from Garmin once; clear them to stop age grading.</p>
    <label for="ysex">Sex (for age-grade standards)</label><select id="ysex">${opt('','Not set',S.about_you.sex||'')}${opt('F','Female',S.about_you.sex||'')}${opt('M','Male',S.about_you.sex||'')}</select>
    <label for="ydob">Date of birth</label><input id="ydob" type="date" value="${E(S.about_you.birth_date||'')}">
    <label for="ygel">Carbohydrate in one of your gels (g)</label><input id="ygel" type="number" min="10" max="60" value="${S.about_you.gel_carbs_g}">
    <p style="margin:12px 0 0"><button class="ghost" id="ysave">Save</button></p></div>
  <div class="card"><p class="eyebrow">Backups</p><p class="xs mute" style="margin-top:0">Made every night and thinned as they age: daily for 7 days, weekly for 4 weeks, monthly for 3 months. Restoring saves the current state first, so it can be undone.</p>
    <label for="abk">Automatic backups</label>${yn('abk',S.auto_backup)}
    <label for="bsel">Backup</label><select id="bsel">${S.backups.map(b=>`<option value="${E(b.name)}" data-part="local">${E(b.made.replace('T',' '))} (${b.size_kb} KB)</option>`).join('')||'<option value="">None yet</option>'}</select>
    <label for="bwhat">What to restore</label><select id="bwhat"><option value="full">Everything</option><option value="config">Settings and races only</option><option value="plan">The plan only</option></select>
    <p class="xs mute">For a copy off this computer, use Download backup above, or see How it works for a daily copy into a cloud folder.</p>
    <p style="margin:12px 0 0"><button class="ghost" id="bnow">Back up now</button> <button class="ghost" id="bres">Restore</button></p></div>
  ${connections()}
  ${aboutCard()}</div>`}
let TERMS=null, TOPEN={};
async function loadTerms(){try{TERMS=await api('terms')}catch(e){TERMS={text:''}}render()}
function md(t){return E(t||'').split(/\n\n+/).map(b=>{b=b.trim();if(!b||b==='---')return '';if(b.startsWith('# '))return '';
  if(b.startsWith('## '))return `<p class="lab2" style="margin:14px 0 4px">${b.slice(3)}</p>`;
  const bold=x=>x.replace(/\*\*([^*]+)\*\*/g,'<b>$1</b>');
  const lines=b.split('\n');if(lines.every(l=>/^\s*- /.test(l)||/^\s{2,}\S/.test(l))){const items=[];lines.forEach(l=>{if(/^\s*- /.test(l))items.push(l.replace(/^\s*- /,''));else items[items.length-1]+=' '+l.trim()});return `<ul class="clist">${items.map(i=>`<li>${bold(i)}</li>`).join('')}</ul>`}
  return `<p class="small" style="margin:6px 0">${bold(lines.join(' '))}</p>`}).join('')}
function termsBox(id){return `<details id="${id}" class="small" style="margin:10px 0 0" ${TOPEN[id]?'open':''}><summary>Read the terms of use and disclaimer</summary><div style="max-height:46vh;overflow:auto;padding:4px 2px 0">${TERMS?md(TERMS.text):'<span class="spin"></span>Loading'}</div></details>`}
function updateBanner(){const u=S.update;if(!u||!u.newer||u.dismissed)return '';const P=S.project||{};
  return `<div class="card c12" id="updnote" style="margin-bottom:18px"><p class="small" style="margin:0"><b>Version ${E(u.latest)} is available</b> (you have ${E(u.running)}).
    ${P.url?`<a href="${E(P.url)}/blob/v${E(u.latest)}/CHANGELOG.md" target="_blank" rel="noopener noreferrer">What's new</a>`:''}</p>
    <p style="margin:10px 0 0"><button class="btn" data-upd="install" data-v="${E(u.latest)}">Update now</button> <button class="ghost" data-upd="dismiss" data-v="${E(u.latest)}">Dismiss</button></p></div>`}
function updatesBox(){const u=S.update;
  if(!S.update_check)return `<p class="small" style="margin:12px 0 0"><b>Updates:</b> not checked automatically. <label class="small" style="margin-left:6px"><input type="checkbox" id="updchk"> Check GitHub once a day</label></p>`;
  if(!u)return '';
  const st=u.status==='not public'?'Update checks start once the project is public on GitHub.':u.status&&u.status!=='ok'?'Last check: '+E(u.status)+'.':u.latest?(u.newer?`Version <b>${E(u.latest)}</b> is available.`:'You have the newest version.'):'';
  const vs=[...new Set([u.base,...(u.installed||[])])].sort((a,b)=>a.split('.').map(Number).reduce((x,y,i)=>x||y-b.split('.').map(Number)[i],0));
  return `<div style="margin-top:12px"><p class="small" style="margin:0"><b>Updates:</b> ${st} ${u.checked?`<span class="mute xs">Checked ${E(u.checked.replace('T',' '))}.</span>`:''}</p>
    <p style="margin:8px 0 0"><button class="ghost" data-upd="check">Check now</button>${u.newer?` <button class="btn" data-upd="install" data-v="${E(u.latest)}">Update to ${E(u.latest)}</button>`:''}</p>
    ${vs.length>1?`<label for="updver">Switch version</label><div class="copyrow"><select id="updver">${vs.map(v=>`<option value="${E(v)}" ${v===u.running?'selected':''}>${E(v)}${v===u.base?' (installed)':''}${v===u.running?' (running now)':''}</option>`).join('')}</select><button class="ghost" id="updgo">Switch</button></div><p class="xs mute">Go back to an earlier version, or forward again. A backup is made first; the app restarts.</p>`:''}
    <label class="small" style="display:block;margin-top:8px"><input type="checkbox" id="updchk" checked> Check GitHub for new versions once a day (nothing about you is sent)</label></div>`}
function termsNotice(){if(!S.setup_done||S.terms_ok)return '';
  return `<div class="card c12" id="termsnote" style="margin-bottom:18px"><p class="eyebrow">Terms of use</p><p class="small" style="margin:0">Periodize My Run is a training tool, not medical advice. You run at your own risk, your data and its security are yours to look after, and the app must not be put on the internet. Please read and accept the terms once.</p>
    ${termsBox('tbox2')}<p style="margin:12px 0 0"><label class="small"><input type="checkbox" id="tok2"> I have read and accept the terms of use</label> <button class="btn" id="taccept" style="margin-left:10px">Accept</button></p></div>`}
function aboutCard(){const P=S.project||{}, x=(href,t)=>`<a href="${E(href)}" target="_blank" rel="noopener noreferrer">${t}</a>`;
  return `<div class="card c12" id="aboutcard"><p class="eyebrow">About Periodize My Run</p>
    <p class="small" style="margin:0">Version <b class="num">${E(S.version)}</b> · <a href="#" id="tochanges">What changed</a>${P.url?' · '+x(P.url,'Source code'):''}</p>
    <ul class="clist">
      <li><b>Licence:</b> MIT. Free to use, change and share, with no warranty${P.url?' ('+x(P.url+'/blob/main/LICENSE','read the licence')+')':''}.</li>
      <li><b>Found a problem or have an idea?</b> ${P.url?x(P.url+'/issues/new','Open an issue')+'. Say what you did, what happened and what you expected; the Log tab often helps, but check it for anything personal before pasting.':'See the README.'}</li>
      <li><b>A security problem?</b> Please report it privately, not in a public issue${P.url?': '+x(P.url+'/security/advisories/new','private security report'):''}. See SECURITY.md.</li>
      ${P.support?`<li><b>Like it?</b> ${x(P.support,'Buy me a coffee')} ☕</li>`:''}
    </ul>${updatesBox()}${termsBox('tbox3')}
    <p class="xs mute" style="margin:8px 0 0">Periodize My Run is a training tool, not medical advice; you use it at your own risk. Keep it off the internet: it is for your own computer or home network. It is not affiliated with Garmin.</p></div>`}
function watchCard(head,chip){const w=S.watch||{source:'garmin'}, opt=(v,t)=>`<option value="${v}" ${w.source===v?'selected':''}>${t}</option>`;
  return `<div class="card c6 conn" id="cwatch">${head('⇄','Where your runs come from',chip(w.connected,E(w.name||'Garmin'),'Not connected',w.source!=='garmin'))}
    <label for="wsrc">Source</label><select id="wsrc">${opt('garmin','Garmin (runs, sleep, HRV, workouts to the watch)')}${opt('fitfolder','FIT files from a folder (any watch, runs only)')}${opt('coros','COROS (experimental, runs only)')}</select>
    <div id="wfit" ${w.source==='fitfolder'?'':'hidden'}><p class="small" style="margin:10px 0 4px">Export your runs as .fit files (COROS, Polar, Suunto, Wahoo or any watch) into one folder, or point this at a folder a sync app fills. New files are read at every sync; runs only, so there is no day-by-day easing from sleep or HRV, and workouts are not sent to the watch.</p>
      ${w.local?`<label for="wfolder">Folder on this computer</label><div class="copyrow"><input id="wfolder" style="flex:1;min-width:0" value="${E(w.fit_folder||'')}" placeholder="/Users/you/FIT files"><button class="ghost" id="wfsave">Use this folder</button></div>`:`<p class="xs mute">${w.fit_folder?'Folder: <code>'+E(w.fit_folder)+'</code>. ':''}The folder can only be chosen on the computer Periodize My Run runs on.</p>`}</div>
    <div id="wcor" ${w.source==='coros'?'':'hidden'}><p class="small" style="margin:10px 0 4px"><span class="tag">Experimental</span> Written without a COROS watch to test against, through COROS's unofficial web interface, which COROS can change or block at any time. It reads runs only and never sends anything to your COROS account or watch.</p>
      ${w.coros?`<p class="cact"><button class="ghost" id="cordis">Disconnect COROS</button></p>`:`<label for="cem">COROS email</label><input id="cem" style="width:100%" autocomplete="username"><label for="cpw">COROS password</label><input id="cpw" type="password" style="width:100%" autocomplete="current-password">
      <p class="xs mute">Sent once to COROS and never stored; only the access token is kept, encrypted.</p><p class="cact"><button class="btn" id="corgo">Sign in to COROS</button></p>`}</div>
    ${w.source==='garmin'?'':`<p class="xs mute" style="margin:10px 0 0">Garmin stays connected if it was, but the plan is not sent to it while another source is chosen.</p>`}</div>`}
function connections(){const gm=S.garmin, chip=(ok,yes,no,warn)=>`<span class="chip ${ok?'green':warn?'amber':'unknown'}"><i></i>${ok?yes:no}</span>`;
  const head=(icon,name,c)=>`<div class="chead"><span class="cicon" aria-hidden="true">${icon}</span><b>${name}</b><span style="margin-left:auto">${c}</span></div>`;
  return `<div class="c12 sechead"><h2>Connections</h2><p class="small mute">Where your data comes from and where copies go. Tokens are kept encrypted on this computer; no passwords are stored.</p></div>
  <div class="card c6 conn" id="cgarmin">${head('⌚','Garmin',chip(gm.connected,'Connected','Not connected'))}
    <p class="small">${gm.connected?'Signed in'+(gm.name?' as <b>'+E(gm.name)+'</b>':'')+'.':'Not connected. The plan cannot sync without it.'}</p>
    <ul class="clist"><li>Reads your runs, sleep, HRV, resting heart rate and steps once a day.</li><li>${S.settings.push_enabled?`Sends the next ${S.settings.push_days} days of workouts to your watch, and checks every four hours that they are still there.`:'Sending workouts to your watch is switched off (How you train, above).'}</li><li>Your password was used once to sign in and was not stored.</li></ul>
    ${gm.connected?'<p class="cact"><button class="ghost" id="gmdis">Disconnect Garmin</button></p><p class="xs mute">To revoke access everywhere, change your Garmin password.</p>':''}</div>
  ${watchCard(head,chip)}
  <div class="card c6 conn" id="ccal">${head('▦','Calendar file',chip(true,'Ready',''))}
    <p class="small">The next sessions as a file for Apple Calendar, Outlook or Google Calendar. Import it by hand; nothing is sent anywhere.</p>
    <p class="cact"><a class="ghost" href="/api/calendar.ics">Download calendar file</a></p></div>
  <div class="card c12 conn" id="cheat">${head('☀','Heat adjustment (Open-Meteo)',chip(S.heat&&S.heat.on,'On','Off'))}
    <p class="small">Eases fast paces on hot, humid days, and shows the race-day forecast for your goal race once it is within 16 days. The weather comes from Open-Meteo (free, no account). The only thing sent is your rough location, rounded to about 10 km, taken from your latest outdoor run. Off unless you switch it on.</p>
    <label for="heatsw">Adjust for heat</label>${yn('heatsw',S.heat&&S.heat.on)}
    ${S.heat&&S.heat.on&&!S.heat.located?'<p class="xs mute" style="margin:6px 0 0">Waiting for the first forecast: it is read at the next sync, once a run with GPS is found.</p>':''}</div>
  <div class="card c12 conn" id="cmaps">${head('◎','Maps (OpenStreetMap)',chip(S.map_tiles,'Real maps on','Outline only'))}
    <p class="small">Shows each run on a real map. Map images are loaded from OpenStreetMap when you open a run, so its servers see which area you are looking at. No account, name or run data is sent. Switched off, routes are drawn as an outline and nothing is loaded from outside.</p>
    <label for="mapsw">Show runs on a real map</label>${yn('mapsw',S.map_tiles)}</div>`}
function aboutView(){if(!ABOUT)return '<div class="grid"><div class="card c12"><span class="spin"></span>Loading</div></div>';
  return '<div class="grid">'+ABOUT.map(s=>`<div class="card c6"><p class="eyebrow">${E(s.title)}</p><ul class="why" style="margin:0">${s.items.map(i=>`<li>${E(i)}</li>`).join('')}</ul></div>`).join('')+'</div>'}
function logView(){return `<div class="grid"><div class="card c12"><p class="eyebrow">Activity log <button class="ghost" id="lr">Refresh</button></p><pre>${E(logs.join(''))||'Loading…'}</pre></div></div>`}
function histView(){
  if(!HIST)return '<div class="grid"><div class="card c12"><span class="spin"></span>Loading</div></div>';
  const H=HIST;
  let h=`<div class="grid"><div class="card"><p class="eyebrow">Execution, last 12 weeks</p>${H.average!==null?`<div class="big num ${scc(H.average)}">${H.average}</div><p class="small mute">average over ${H.count} planned session${H.count===1?'':'s'}</p>`:'<p class="small mute">No planned sessions have passed yet.</p>'}</div>
    <div class="card c8"><p class="eyebrow">By week</p>${H.weeks.length>1?chart('Average execution score',H.weeks,x=>x.avg,x=>'Week of '+nice(x.week)+': '+x.avg+' over '+x.n+' sessions',x=>nice(x.week)):`<p class="small mute">${H.weeks.length?`Week of ${nice(H.weeks[0].week)}: ${H.weeks[0].avg} over ${H.weeks[0].n} session${H.weeks[0].n===1?'':'s'}. A chart appears after a second week.`:'Builds up week by week from the day the app started planning for you.'}</p>`}
      <p class="xs mute" style="margin:10px 0 0">The score is how closely the load you ran matched the load planned, in easy, moderate and hard minutes weighted 1, 2 and 3 (Lucia's TRIMP). Too hard counts the same as too easy. See How it works.</p></div>
    <div class="card c12"><p class="eyebrow">Sessions <span class="mute" style="text-transform:none;letter-spacing:0">· click one for the run in detail</span></p>`;
  if(!H.sessions.length)h+='<p class="small mute">Nothing yet. Each planned session appears here the day after, with what you ran and how closely it matched.</p>';
  else{h+=`<table><tr><th>Date</th><th>Planned</th><th>What you ran</th><th class="r"><span title="${SCTIP}">Execution score <span aria-hidden="true">ⓘ</span></span></th><th></th></tr>`;
    for(const x of H.sessions){const s=x.score;
      h+=`<tr><td class="num" style="white-space:nowrap">${x.dow} ${nice(x.date)}</td><td><b>${E(x.label)}</b> <span class="mute num">${E(x.dist)}</span><div class="xs mute">${E(x.short)}${x.eased?` · eased ${(x.eased*100).toFixed(1)}%`:''}</div></td>
        <td>${x.done?`<span class="num">${E(x.done.dist)}</span> <span class="mute xs">at ${E(x.done.pace)}</span> ${x.done.id?GLINK(x.done.id):''}`:'<span class="mute">—</span>'}${x.moved_to?`<div class="xs mute">missed, moved to ${nice(x.moved_to)}</div>`:''}${x.unplanned?'<div class="xs mute">run on a rest day</div>':''}${s&&s.note?`<div class="xs mute">${E(s.note)}</div>`:''}</td>
        <td class="r">${s?`<span class="sc num ${scc(s.score)}" title="${SCTIP}">${s.score}</span><div class="xs mute">${E(s.verdict)}</div>`:'<span class="mute">—</span>'}</td>
        <td class="r"><button class="ghost" data-dopen="${x.date}">Detail</button></td></tr>`}
    h+='</table>'}
  return h+'</div></div>'+dayModal()}
const scc=v=>v>=85?'green':v>=65?'amber':'red';
const SCTIP='Execution score out of 100: how closely the run matched the planned session. 85 or more is on target, 65 to 84 is close, under 65 is off target. Open the detail to see why.';
let CH={}, CHN=0, CHANGES=null, PACE=null, MAPZ=0, TR=null, TRV=null;
const GLINK=(id,cls)=>`<a class="gl ${cls||''}" href="https://connect.garmin.com/modern/activity/${encodeURIComponent(id)}" target="_blank" rel="noopener noreferrer" title="Open in Garmin Connect" aria-label="Open this activity in Garmin Connect"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1.6 15 14H1z" fill="#007cc3"/></svg></a>`;
function lineChart(series,idx,color,label,fmtv,invert,tip){
  const pts=series.filter(s=>s[idx]!=null);if(pts.length<3)return '';
  const vs=pts.map(s=>s[idx]).sort((a,b)=>a-b), lo=vs[Math.floor(vs.length*0.02)], hi=vs[Math.floor(vs.length*0.98)]||lo+1, T0=series[0][0], T=(series[series.length-1][0]-T0)||1, W=600,Ht=110;
  const y=v=>{const f=Math.max(0,Math.min(1,(v-lo)/((hi-lo)||1)));return (invert?f:1-f)*(Ht-16)+8};
  const d=pts.map((s,i)=>(i?'L':'M')+((s[0]-T0)/T*W).toFixed(1)+' '+y(s[idx]).toFixed(1)).join(' ');
  const id='c'+(++CHN);CH[id]=pts.map(s=>[(s[0]-T0)/T,y(s[idx])/Ht,tip?tip(s):fmtv(s[idx])]);
  return `<div class="xs mute" style="display:flex;justify-content:space-between;margin-top:10px"><span><i style="display:inline-block;width:14px;height:3px;border-radius:2px;background:${color};vertical-align:middle;margin-right:6px"></i><b>${label}</b> <span class="mute">· hover for values</span></span><span class="num">${fmtv(invert?lo:hi)} to ${fmtv(invert?hi:lo)}</span></div>
    <div class="lc" data-ch="${id}" tabindex="0" role="img" aria-label="${label}, from ${fmtv(invert?lo:hi)} to ${fmtv(invert?hi:lo)}. Use the left and right arrow keys to read values."><svg viewBox="0 0 ${W} ${Ht}" preserveAspectRatio="none" style="width:100%;height:110px;display:block" aria-hidden="true"><path d="${d}" fill="none" stroke="${color}" stroke-width="1.8" vector-effect="non-scaling-stroke" stroke-linejoin="round"/></svg><i class="cur"></i><i class="pt" style="background:${color}"></i><span class="tp num" aria-live="polite"></span></div>`}
function bindCharts(){
  $$('.lc').forEach(el=>{const pts=CH[el.dataset.ch];if(!pts)return;let k=-1;const cur=el.querySelector('.cur'),pt=el.querySelector('.pt'),tp=el.querySelector('.tp');
    const show=i=>{k=Math.max(0,Math.min(pts.length-1,i));const p=pts[k],x=p[0]*100;cur.style.left=pt.style.left=x+'%';pt.style.top=(p[1]*100)+'%';tp.textContent=p[2];tp.style.left=Math.max(12,Math.min(88,x))+'%';el.classList.add('on')};
    const at=cx=>{const r=el.getBoundingClientRect(),f=(cx-r.left)/r.width;let b=0,bd=9;pts.forEach((p,i)=>{const dd=Math.abs(p[0]-f);if(dd<bd){bd=dd;b=i}});show(b)};
    el.onmousemove=e=>at(e.clientX);el.ontouchstart=el.ontouchmove=e=>at(e.touches[0].clientX);el.onmouseleave=()=>el.classList.remove('on');el.onblur=()=>el.classList.remove('on');
    el.onkeydown=e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();show(k<0?(e.key==='ArrowRight'?0:pts.length-1):k+(e.key==='ArrowRight'?1:-1))}}})}
function realMap(track){
  const W=600,H=340,TS=256,mx=lo=>(lo+180)/360,my=la=>{const s=Math.sin(la*Math.PI/180);return 0.5-Math.log((1+s)/(1-s))/(4*Math.PI)};
  const xs=track.map(p=>mx(p[1])),ys=track.map(p=>my(p[0])),x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys);
  let z=17;while(z>2&&((x1-x0)*TS*2**z>W-60||(y1-y0)*TS*2**z>H-60))z--;z=Math.max(2,Math.min(18,z+MAPZ));
  const n=2**z,wp=TS*n,ox=(x0+x1)/2*wp-W/2,oy=(y0+y1)/2*wp-H/2,tiles=[];
  for(let tx=Math.floor(ox/TS);tx*TS<ox+W;tx++)for(let ty=Math.floor(oy/TS);ty*TS<oy+H;ty++){if(ty<0||ty>=n)continue;
    tiles.push(`<img alt="" referrerpolicy="origin" src="https://tile.openstreetmap.org/${z}/${((tx%n)+n)%n}/${ty}.png" style="left:${((tx*TS-ox)/W*100).toFixed(3)}%;top:${((ty*TS-oy)/H*100).toFixed(3)}%;width:${(TS/W*100).toFixed(3)}%;height:${(TS/H*100).toFixed(3)}%">`)}
  const px=i=>xs[i]*wp-ox,py=i=>ys[i]*wp-oy,d=track.map((p,i)=>(i?'L':'M')+px(i).toFixed(1)+' '+py(i).toFixed(1)).join(' '),e=track.length-1;
  return `<div class="rmap">${tiles.join('')}<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="Map of the route"><path d="${d}" fill="none" stroke="#fff" stroke-width="6" stroke-linejoin="round" stroke-linecap="round" opacity=".85"/><path d="${d}" fill="none" stroke="#5b5bf0" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round"/>
    <circle cx="${px(0).toFixed(1)}" cy="${py(0).toFixed(1)}" r="6" fill="#12805c" stroke="#fff" stroke-width="2"/><circle cx="${px(e).toFixed(1)}" cy="${py(e).toFixed(1)}" r="6" fill="#14161a" stroke="#fff" stroke-width="2"/></svg>
    <div class="mzoom"><button class="ghost" data-mz="1" aria-label="Zoom in">+</button><button class="ghost" data-mz="-1" aria-label="Zoom out">−</button></div>
    <a class="mattr" href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">© OpenStreetMap contributors</a></div><div class="xs mute" style="margin-top:4px">Green start, dark finish.</div>`}
function route(track){
  if(!track||track.length<5)return '';
  const lat0=track[0][0], k=Math.cos(lat0*Math.PI/180), xs=track.map(p=>p[1]*k), ys=track.map(p=>p[0]);
  const x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys), sc=Math.max(x1-x0,y1-y0)||1, W=300, pad=10;
  const px=i=>pad+(xs[i]-x0)/sc*(W-2*pad)+((sc-(x1-x0))/sc*(W-2*pad))/2, py=i=>W-pad-(ys[i]-y0)/sc*(W-2*pad)-((sc-(y1-y0))/sc*(W-2*pad))/2;
  const d=track.map((p,i)=>(i?'L':'M')+px(i).toFixed(1)+' '+py(i).toFixed(1)).join(' '), n=track.length-1;
  return `<svg viewBox="0 0 ${W} ${W}" style="width:100%;max-width:300px;display:block;background:var(--hover);border-radius:12px" role="img" aria-label="Outline of the route"><path d="${d}" fill="none" stroke="url(#lg)" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
    <circle cx="${px(0).toFixed(1)}" cy="${py(0).toFixed(1)}" r="5" fill="var(--green)"/><circle cx="${px(n).toFixed(1)}" cy="${py(n).toFixed(1)}" r="5" fill="var(--ink)"/></svg><div class="xs mute" style="margin-top:4px">Route outline · green start, dark finish · real maps can be switched on in Settings</div>`}
function dayModal(){
  if(!DAY)return '';
  if(DAY.loading)return `<div class="ov" id="dov"><div class="modal" role="dialog" aria-modal="true" aria-label="Loading"><span class="spin"></span>Loading</div></div>`;
  const D=DAY, s=D.score, u=D.units, pf=v=>Math.floor(v/60)+':'+String(Math.round(v%60)).padStart(2,'0')+'/'+u;
  let h=`<div class="ov" id="dov"><div class="modal" style="width:min(760px,100%)" role="dialog" aria-modal="true" aria-labelledby="dmt">
    <p class="eyebrow"><span id="dmt">${D.dow} ${nice(D.date)} ${D.date.slice(0,4)}</span><button class="ghost" id="dayx" style="margin-left:auto" aria-label="Close">Close</button></p>`;
  if(D.plan)h+=`<p class="h">${E(D.plan.label)} <span class="mute num" style="font-weight:600">${E(D.plan.dist)}</span>${s?` <span class="sc ${scc(s.score)}" style="font-size:13.5px;margin-left:6px;white-space:nowrap" title="${SCTIP}">Execution score <b class="num">${s.score}</b></span>`:''}</p>
    <p class="lab2">Planned${D.plan.eased?` <span class="chip amber" style="margin-left:6px"><i></i>eased ${(D.plan.eased*100).toFixed(1)}%</span>`:''}</p>${stepList(D.plan.text)||'<p class="small mute">Rest day.</p>'}`;
  else h+=`<p class="h">No session was planned</p>`;
  if(s)h+=`<p class="lab2">Execution score · ${s.score} out of 100 · ${E(s.verdict)}</p>
    <div class="explain" id="scwhy"><p class="small" style="margin:0"><b>What this means.</b> The score is how closely the running you did matched the session planned. 100 is exactly as planned; 85 or more is on target, 65 to 84 is close, under 65 is off target. It is not a measure of how fit you are or how hard you tried.</p>
      ${s.cause?`<p class="small" style="margin:8px 0 0"><b>Why ${s.score}.</b> ${E(s.cause)}${s.note?' The biggest difference: '+E(s.note)+'.':''}</p>`:''}</div>
    ${s.parts.length?`<table style="margin-top:10px"><tr><th>Kind of running</th><th class="r">Planned</th><th class="r">You ran</th><th class="r">Counts</th><th class="r">Points lost</th></tr>
      ${s.parts.map(p=>`<tr><td><b>${E(p.name.split(' (')[0])}</b></td><td class="r num">${p.planned_min} min</td><td class="r num ${Math.abs(p.min-p.planned_min)>1?'amber':''}">${p.min} min</td><td class="r num mute">×${p.weight}</td><td class="r num">${p.lost?'−'+p.lost:(p.lost===0?'0':'')}</td></tr>`).join('')}</table>`:''}
    <p class="xs mute" style="margin:8px 0 0">${s.zones?E(s.zones.join(' · '))+'. ':''}Measured by ${E(s.by||'pace')}. A minute of moderate running counts double and a minute of hard running triple, so running reps too fast costs more than running easy miles too long. The first minute of difference in each kind is ignored. More under History and execution score in How it works.</p>`;
  if(!D.runs.length)h+=`<p class="lab2">The run</p><p class="small mute">No run was recorded that day.</p>`;
  D.runs.forEach((r,i)=>{
    const st=r.start_utc?new Date(r.start_utc.replace(' ','T')+'Z'):null;
    h+=`<p class="lab2">${D.runs.length>1?'Run '+(i+1):'The run'} · ${E(r.name)}</p><div class="stats" style="grid-template-columns:repeat(auto-fit,minmax(112px,1fr));margin-top:6px">
      ${st?`<div class="stat"><div class="v num">${st.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}</div><div class="k">Started</div></div>`:''}
      <div class="stat"><div class="v num">${E(r.dist)}</div><div class="k">in ${fmt(r.time_s)}</div></div>
      <div class="stat"><div class="v num">${E(r.pace)}</div><div class="k">Average pace${r.flat_pace?' · flat '+E(r.flat_pace):''}</div></div>
      ${r.avg_hr?`<div class="stat"><div class="v num">${r.avg_hr}</div><div class="k">Average heart rate${r.max_hr?' · max '+r.max_hr:''}</div></div>`:''}
      <div class="stat"><div class="v num">${r.load}</div><div class="k">Load · ${r.zones_min[0]}/${r.zones_min[1]}/${r.zones_min[2]} min easy/mod/hard</div></div>
      ${r.training_effect?`<div class="stat"><div class="v num">${(+r.training_effect).toFixed(1)}</div><div class="k">Garmin training effect${r.garmin_load?' · load '+r.garmin_load:''}</div></div>`:''}
      ${r.climb_m!=null?`<div class="stat"><div class="v num">${r.climb_m} m</div><div class="k">Climb</div></div>`:''}
      ${r.drift!=null?`<div class="stat"><div class="v num ${r.drift<=5?'green':'amber'}">${r.drift}%</div><div class="k">Aerobic drift, second half against first</div></div>`:''}</div>
      ${r.treadmill?'<p class="xs mute" style="margin:6px 0 0">Treadmill run: distance and pace are the watch’s guess, so this run is scored on heart rate and left out of pace trends.</p>':''}
      <div class="grid" style="margin-top:6px;gap:16px"><div style="grid-column:span ${r.track.length>4&&!S.map_tiles?8:12};min-width:0">${(tip=>lineChart(r.series,1,'var(--brand)','Pace',pf,true,tip)+lineChart(r.series,2,'var(--race)','Heart rate',v=>Math.round(v)+' bpm',false,tip))(s=>fmt(s[0])+' in: '+(s[1]?pf(s[1]):'stopped')+(s[2]?', '+s[2]+' bpm':''))}
        ${r.series.length<3?'<p class="small mute">No second-by-second detail is stored for this run.</p>':''}</div>
      ${r.track.length>4?(S.map_tiles?`<div style="grid-column:span 12;min-width:0">${realMap(r.track)}</div>`:`<div style="grid-column:span 4;min-width:0;padding-top:10px">${route(r.track)}</div>`):''}</div>
      <p class="xs" style="margin:8px 0 0">${GLINK(r.id)} <a href="https://connect.garmin.com/modern/activity/${encodeURIComponent(r.id)}" target="_blank" rel="noopener noreferrer">Open in Garmin Connect</a></p>`});
  return h+'</div></div>'}
async function openDay(date){SEL=null;DAY={loading:true};render();try{DAY=await api('day/'+date)}catch(e){DAY=null}render()}
async function loadHist(){HIST=await api('history');if(view==='hist')render()}
async function loadTrends(){try{TR=await api('trends')}catch(e){TR={}}if(view==='you')render()}
const DIRS={rising:['green','▲ Improving'],falling:['amber','▼ Slipping'],steady:['','Steady'],higher:['amber','▲ Above your normal'],lower:['','▼ Below your normal']};
function dirTag(d,win){if(!d)return '';const [c,t]=DIRS[d]||['',d];return `<span class="tag ${c}" title="Over ${E(win||'')}">${t}</span>`}
function trendBtn(k){return `<button class="ghost xs" data-trend="${k}" style="margin-left:auto;padding:3px 9px" aria-label="Show the trend">Trend</button>`}
function secPace(v){if(!v)return '—';const s=(U()==='mi'?1609.344:1000)/v;return Math.floor(s/60)+':'+String(Math.round(s%60)).padStart(2,'0')+'/'+U()}
function dayNum(d){return Date.parse(d+'T12:00:00Z')/864e5}
function trendModal(){if(!TRV)return '';const t=TR&&TR[TRV];
  const body=!TR?'<p><span class="spin"></span>Loading</p>':!t||!t.rows||t.rows.length<3?'<p class="small mute">Not enough history yet for a trend. It builds up week by week.</p>':(()=>{
    const ser=t.rows.map(r=>[dayNum(r.date),r.v]);
    const fv=TRV==='speed'?secPace:TRV==='base'?v=>Math.round(v)+'%':TRV==='durability'?v=>v+'%':v=>Math.round(v).toLocaleString();
    const tip=s=>{const r=t.rows.find(x=>dayNum(x.date)===s[0]);return nice(r.date)+': '+fv(r.v)+(r.mi?` (${U()==='mi'?r.mi+' mi':Math.round(r.mi*KM)+' km'} run)`:'')};
    return lineChart(ser,1,'var(--brand)',t.title,fv,TRV==='durability',tip)})();
  return `<div class="ov" id="tov"><div class="modal" style="width:min(680px,100%)" role="dialog" aria-modal="true" aria-labelledby="tmt"><p class="eyebrow"><span id="tmt">${E(t?t.title:'Trend')}</span> ${t?dirTag(t.dir,t.window):''}<button class="ghost" id="trex" style="margin-left:auto" aria-label="Close">Close</button></p>
    ${body}${t?`<p class="small" style="margin:10px 0 0">${E(t.text)}</p>${t.change!=null&&TRV!=='steps'?`<p class="xs mute" style="margin:6px 0 0">Change over ${E(t.window)}: <b class="num">${t.change>0?'+':''}${t.change}${TRV==='speed'?'%':TRV==='base'?' points':' points of drift'}</b></p>`:''}`:''}</div></div>`}
function accuracyCard(){const A=TR&&TR.races;
  if(!A)return TR?'':`<div class="card c12" id="acccard"><p class="eyebrow">How accurate are the predictions?</p><p class="small mute"><span class="spin"></span>Loading</p></div>`;
  const lean=Math.abs(A.bias)<1?'They are about right on average.':A.bias>0?`On average they are <b>${A.bias}% slower</b> than you actually ran: on the cautious side.`:`On average they are <b>${Math.abs(A.bias)}% faster</b> than you actually ran: on the optimistic side.`;
  return `<div class="card c12" id="acccard"><p class="eyebrow">How accurate are the predictions?</p>
    <p class="small" style="margin:0">Over your last ${A.n} race${A.n>1?'s':''}, predictions were off by <b>${A.mean_abs}%</b> on average. ${lean}</p>
    <div style="max-height:300px;overflow:auto;margin-top:10px"><table><tr><th>Date</th><th>Race</th><th class="r">Predicted</th><th class="r">Actual</th><th class="r">Off by</th></tr>
      ${A.rows.map(r=>`<tr><td class="num">${nice(r.date)} ${r.date.slice(0,4)}</td><td>${E(r.distance)}${r.name!==r.distance?` <span class="mute xs">${E(r.name)}</span>`:''}</td><td class="r num">${r.predicted}</td><td class="r num"><b>${r.actual}</b></td><td class="r num ${Math.abs(r.error)<=2?'green':Math.abs(r.error)<=5?'':'amber'}">${r.error>0?'+':''}${r.error}%</td></tr>`).join('')}</table></div>
    <p class="xs mute" style="margin:8px 0 0">Each prediction is rebuilt from what was known the Monday before the race, with today's rules, and compared with your time adjusted to a flat course where the course is known. A plus means the prediction was slower than you ran. Race-day conditions, pacing and how hard you raced all add to the gap.</p></div>`}
function recoveryCard(){const R=TR&&TR.recovery;
  if(!R)return `<div class="card c12" id="reccard"><p class="eyebrow">Recovery trends</p><p class="small mute">${TR?'Builds up once a few weeks of sleep and HRV are in.':'<span class="spin"></span>Loading'}</p></div>`;
  const one=(k,color,invert)=>{const x=R[k];if(!x||x.rows.length<3)return '';const ser=x.rows.map(r=>[dayNum(r.date),r.v]);const fv=v=>v+' '+x.unit;
    return `<div style="grid-column:span 4;min-width:0">${lineChart(ser,1,color,x.label,fv,invert,s=>{const r=x.rows.find(y=>dayNum(y.date)===s[0]);return nice(r.date)+': '+fv(r.v)})}
      <p class="xs mute" style="margin:4px 0 0">${x.normal?`Your normal ${x.normal[0]} ${x.unit} (±${x.normal[1]}) `:''}${dirTag(x.dir,'7 days against your normal')}</p></div>`};
  return `<div class="card c12" id="reccard"><p class="eyebrow">Recovery trends</p><div class="grid" style="gap:18px">${one('hrv','var(--green)',false)}${one('rhr','var(--amber)',true)}${one('sleep_h','var(--brand)',false)}</div>
    <p class="xs mute" style="margin:8px 0 0">7-day averages over 12 weeks, the way the research reads them: one night is noise, a week-long drift is real. Higher HRV, lower resting heart rate and more sleep are better, so each chart is drawn with better as up. These are the same figures the daily adjustment uses.</p></div>`}
function changesView(){if(!CHANGES)return '<div class="grid"><div class="card c12"><span class="spin"></span>Loading</div></div>';
  const col={Added:'green',Changed:'amber',Removed:'red',Fixed:'unknown'};
  return `<div class="grid"><div class="card c12"><p class="eyebrow">Change log</p><p class="small mute" style="margin:0">You are running version <b class="num">${E(S.version)}</b>. Every version is listed here, newest first, with what was added, changed, removed or fixed.</p></div>
    ${CHANGES.map((v,i)=>`<div class="card c12 ver"><p class="h" style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap"><span class="num">${E(v.version)}</span><span class="mute small" style="font-weight:500">${v.date?new Date(v.date+'T12:00').toLocaleDateString(undefined,{day:'numeric',month:'long',year:'numeric'}):''}</span>${i===0?'<span class="tag green">current</span>':''}</p>
      ${v.sections.map(s=>`<p class="lab2"><span class="chip ${col[s.title]||'unknown'}"><i></i>${E(s.title)}</span></p><ul class="why">${s.items.map(x=>`<li>${E(x)}</li>`).join('')}</ul>`).join('')}</div>`).join('')}</div>`}
async function loadChanges(){CHANGES=(await api('changelog')).versions;if(view==='changes')render()}
async function loadAbout(){ABOUT=(await api('about')).sections;if(view==='about')render()}
async function loadLogs(){logs=(await api('logs')).lines;if(view==='log')render()}

function wizard(){
  const j=S.job, p=S.profile, N=5; let h=`<div class="wiz"><div class="brandhead">${LOGO}<h1>periodize my run</h1><div class="mute">Training that adapts to you, every day</div></div><div class="card c12">`;
  const stepper=n=>`<div class="stepper" role="progressbar" aria-valuemin="1" aria-valuemax="${N}" aria-valuenow="${n}" aria-label="Setup step ${n} of ${N}">${Array.from({length:N},(_,i)=>`<i class="${i<n?'on':''}"></i>`).join('')}</div>`;
  const nav=(back,next,label)=>`<p style="margin:18px 0 0">${back?`<button class="ghost" id="${back}">Back</button> `:''}<button class="btn" id="${next}">${label||'Next'}</button></p>`;
  if(wiz.step===6&&!j.running&&S.fitness){
    const f=S.fitness, L=S.limits;
    h+=`<p class="h">Your plan is ready</p><p class="small mute">This is what the app worked out from your history. Check it looks like you; everything can be changed later in Settings.</p>
      <table><tr><td>Runs found</td><td class="r num">${p.runs.toLocaleString()} since ${p.first_run.slice(0,4)}</td></tr>
      <tr><td>Maximum heart rate</td><td class="r num">${L.hrmax}</td></tr><tr><td>Threshold pace now</td><td class="r num">${E(f.threshold)}</td></tr>
      <tr><td>Peak week it will build to</td><td class="r num">${dU(L.peak_miles)}</td></tr><tr><td>This week</td><td class="r">${E(f.week.mode)}, ${E(f.week.total)}</td></tr>
      ${f.goal?`<tr><td>${E(f.goal.name)}</td><td class="r num">forecast ${f.goal.forecast.time}</td></tr>`:''}</table>
      <label for="whr">Maximum heart rate, if you know it is different</label><input id="whr" type="number" min="120" max="230" placeholder="${L.hrmax}" style="width:120px">
      ${nav(null,'wdone','Open my plan')}`;
  }else if(j.running||wiz.step===5&&S.setup_started){
    h+=stepper(5)+`<p class="h">Building your plan</p><p style="margin:14px 0"><span class="spin"></span>${E(j.progress||'Starting')}</p><p class="small mute">The first run reads your whole Garmin history and downloads your recent runs at an unhurried pace, so it takes 10 to 30 minutes. You can close this page; it carries on.</p>`;
    if(p)h+=`<div class="stats"><div class="stat"><div class="v num">${p.runs.toLocaleString()}</div><div class="k">runs found</div></div><div class="stat"><div class="v num">${p.first_run.slice(0,4)}</div><div class="k">running since</div></div><div class="stat"><div class="v num">${dU(p.miles)}</div><div class="k">lifetime</div></div></div>`;
    if(j.error)h+=`<div class="alert err" style="margin-top:14px">${E(j.error)}</div><button class="btn" id="retry">Try again</button>`;
  }else if(wiz.step===1){
    h+=stepper(1)+`<p class="h">Welcome</p><p class="small">Periodize My Run builds a running plan from your own Garmin history and keeps adjusting it from what you do. Setup takes a few minutes of your time, then 10 to 30 minutes of its own.</p>
      <ul class="why"><li><b>It runs on this computer.</b> Your data stays here. Nothing is sent anywhere except your watch's service, the weather service if you switch heat adjustment on, and a daily version check with GitHub.</li>
      <li><b>No passwords are kept.</b> Your Garmin password is used once to sign in; only an access token is stored, encrypted.</li>
      <li><b>No AI is used.</b> The plan comes from fixed rules and your data, and every decision is explained.</li>
      <li><b>It is not medical advice.</b> For pain that changes your stride, chest symptoms or illness with fever, stop and see a clinician.</li></ul>
      ${S.remote?'':(S.has_password?'':'<p class="xs mute">To open the app from another device later, set an app password on this computer with <code>python web.py --set-password</code>.</p>')}
      ${termsBox('tbox1')}<p style="margin:12px 0 0"><label class="small"><input type="checkbox" id="wterms"> I have read and accept the terms of use, including that this is not medical advice and that I run at my own risk</label></p>
      ${nav(null,'w1','Get started')}`;
  }else if(wiz.step===2){
    h+=stepper(2)+`<p class="h">Connect Garmin</p>`;
    if(S.garmin.connected)h+=`<p>Connected${S.garmin.name?' as <b>'+E(S.garmin.name)+'</b>':''}.</p>${nav('wb1','w2')}`;
    else if(wiz.mfa)h+=`<p class="mute">Garmin sent you a code. Enter it here.</p><div class="row"><input id="code" aria-label="Garmin code" inputmode="numeric" autocomplete="one-time-code"><button class="btn" id="mfa">Confirm</button></div>`;
    else h+=`<p class="small mute">Your password goes straight to Garmin, once, and is not stored. Garmin offers no other way for a personal app to sign in.</p>
      <label for="em">Garmin email</label><input id="em" type="email" autocomplete="username" style="width:100%"><label for="pw">Garmin password</label><input id="pw" type="password" autocomplete="current-password" style="width:100%">
      <p style="margin:18px 0 0"><button class="ghost" id="wb1">Back</button> <button class="btn" id="gl">Connect</button></p>`;
  }else if(wiz.step===3){
    h+=stepper(3)+`<p class="h">Your races</p><p class="small mute">Add the race you are training for as the goal race, and any tune-up races. Or skip this and train for general fitness.</p>${raceRows()}${raceForm()}${nav('wb2','w3')}`;
  }else if(wiz.step===4){
    h+=stepper(4)+`<p class="h">How you train</p>${prefs(S.settings)}
      <label for="sd">A recent race or hard effort, if you have run little in the last two months (optional)</label><div class="row"><select id="sd"><option value="">None</option>${DIST.slice(0,6).map(d=>`<option value="${d[1]}">${d[0]}</option>`).join('')}</select><input id="st" aria-label="Time for that race" placeholder="time, e.g. 24:30" size="14"></div>
      ${nav('wb3','w4')}`;
  }else{
    h+=stepper(5)+`<p class="h">Backups and extras</p>
      <label for="abk">Back up my data on this computer every night</label>${yn('abk',S.auto_backup)}
      <p class="xs mute">Kept daily for 7 days, weekly for 4 weeks and monthly for 3 months.</p>
      <label for="wh">Aerobic tests and heart-rate aerobic runs (one coach's method; optional)</label><select id="wh">${opt(0,'Off',S.settings.aero_test?1:0)}${opt(1,'On',S.settings.aero_test?1:0)}</select>
      ${nav('wb4','start','Build my plan')}`;
  }
  $('#main').innerHTML=h+'</div></div>'; bind();
}
function bind(){
  const on=(id,fn)=>{const e=$(id);if(e)e.onclick=async ev=>{ev.preventDefault();try{await fn()}catch(x){}}};
  on('#gl',async()=>{const r=await api('garmin/login',{email:$('#em').value,password:$('#pw').value});if(r.result==='needs_mfa')wiz.mfa=true;await load()});
  on('#mfa',async()=>{await api('garmin/mfa',{code:$('#code').value});wiz.mfa=false;await load()});
  on('#w1',async()=>{if(!$('#wterms').checked)return toast('Please read and accept the terms of use first.','err');await api('terms',{accept:true});wiz.step=2;render()});
  if($('#taccept'))$('#taccept').onclick=async()=>{if(!$('#tok2').checked)return toast('Tick the box to accept the terms.','err');await api('terms',{accept:true});toast('Thank you');await load()};
  $$('details[id^=tbox]').forEach(d=>d.ontoggle=()=>{TOPEN[d.id]=d.open;if(d.open&&!TERMS)loadTerms()});
  [['#w2',3],['#w3',4],['#wb1',1],['#wb2',2],['#wb3',3],['#wb4',4]].forEach(([id,n])=>on(id,()=>{if(id==='#w4')return;wiz.step=n;render()}));
  on('#w4',()=>{const p=prefsRead();if(p.blocked_days.includes(p.long_day))return toast('Your long run day is marked as a day you cannot run.','err');
    if($('#sd').value&&hmsIn($('#st').value))p.seed_race={miles:+$('#sd').value,time_s:hmsIn($('#st').value)};wiz.prefs=p;wiz.step=5;render()});
  on('#start',async()=>{const hd=$('#wh').value==='1';await api('settings',Object.assign({},wiz.prefs||{}, {aero_test:hd,aero_runs:hd}));await api('settings',{auto_backup:$('#abk').value==='1'});
    await api('run',{kind:'setup'});wiz.step=6;await load()});
  on('#wdone',async()=>{const v=+$('#whr').value;if(v)await api('settings',{hrmax:v});await api('setup/finish',{});wiz.step=1;await load()});
  on('#retry',async()=>{await api('run',{kind:'setup'});await load()});
  on('#radd',async()=>{await api('races',raceRead());toast('Race saved');await load()});
  $$('[data-del]').forEach(b=>b.onclick=async()=>{await api('races/'+b.dataset.del,null,'DELETE');await load()});
  on('#sadd',async()=>{await api('status',{kind:$('#sk').value,mode:$('#sm').value,start:$('#ss').value,end:$('#se').value,note:$('#sn').value});toast('Saved. Replanning from today.');await load()});
  if($('#sk'))$('#sk').onchange=()=>{$('#smw').style.display=$('#sk').value==='holiday'?'':'none'};
  $$('[data-better]').forEach(b=>b.onclick=async()=>{await api('status',{id:+b.dataset.better});toast('Welcome back. Replanning with a gentle return.');await load()});
  $$('[data-sdel]').forEach(b=>b.onclick=async()=>{await api('status/'+b.dataset.sdel,null,'DELETE');await load()});
  on('#ssave',async()=>{const s=prefsRead();if(s.blocked_days.includes(s.long_day))return toast('Your long run day is marked as a day you cannot run.','err');
    s.hrmax=+$('#hrmax').value||null;s.peak_miles_override=+$('#peak').value||null;s.push_days=+$('#push_days').value;s.weeks_ahead=+$('#weeks_ahead').value;s.forecast_completion=$('#forecast_completion').value?+$('#forecast_completion').value/100:null;s.aero_test=+$('#aero_test_weeks').value>0;if(s.aero_test)s.aero_test_weeks=+$('#aero_test_weeks').value;s.aero_runs=$('#aero_runs').value==='1';s.aero_format=$('#aero_format').value;s.notify_url=$('#notify').value.trim();await api('settings',s);toast('Saved. Replanning.');await load()});
  on('#run',async()=>{await api('run',{kind:'daily'});toast('Updating from Garmin');await load()});on('#lr',loadLogs);
  on('#xadd',async()=>{const t=hmsIn($('#xt').value);if(!t)return toast('Enter the time as h:mm:ss or mm:ss.','err');let mi=$('#xm').value==='c'?(+$('#xo').value)/(U()==='mi'?1:KM):+$('#xm').value;if(!mi)return toast('Enter the distance.','err');await api('results',{name:$('#xn').value,date:$('#xd').value,miles:mi,time_s:t,off_road:$('#xs').value==='1'});toast('Result added');await load()});
  if($('#xm'))$('#xm').onchange=()=>{$('#xow').style.display=$('#xm').value==='c'?'':'none'};
  $$('[data-redit]').forEach(b=>b.onclick=async()=>{const x=S.results.find(r=>r.id==b.dataset.redit);const name=prompt('Race name',x.name);if(name===null)return;const t=prompt('Official time (h:mm:ss)',fmt(x.time_s));if(t===null||!hmsIn(t))return;
    await api('results',{id:x.id,name:name,date:x.date,miles:x.dist_m/1609.344,time_s:hmsIn(t),off_road:!x.counts});toast('Result corrected');await load()});
  $$('[data-rdel]').forEach(b=>b.onclick=async()=>{await api('results/'+b.dataset.rdel,null,'DELETE');toast('Removed');await load()});
  on('#aerobic',async()=>{const st=$$('.hst').map(e=>({hr:+e.dataset.hr,time_s:hmsIn(e.value)})).filter(x=>x.time_s);await api('aerobic',{date:$('#hd').value,stages:st});toast('Test saved');await load()});
  $$('[data-hdel]').forEach(b=>b.onclick=async()=>{await api('aerobic/'+b.dataset.hdel,null,'DELETE');await load()});
  if($('#ximp'))$('#ximp').onchange=async e=>{const f=e.target.files[0];if(!f)return;try{const r=await api('results/import',{csv:await f.text()});toast(`Imported: ${r.added} added, ${r.updated} matched to Garmin, ${r.skipped} skipped`);await load()}catch(x){}};
  on('#tochanges',()=>{view='changes';loadChanges();render();scrollTo({top:0})});
  if($('#wsrc'))$('#wsrc').onchange=async()=>{const v=$('#wsrc').value;$('#wfit').hidden=v!=='fitfolder';$('#wcor').hidden=v!=='coros';
    if(v==='garmin'||(v==='fitfolder'&&S.watch.fit_folder)||(v==='coros'&&S.watch.coros)){try{await api('watch',{source:v});toast('Runs now come from '+$('#wsrc').selectedOptions[0].text.split(' (')[0]);await load()}catch(e){}}};
  on('#wfsave',async()=>{await api('watch',{source:'fitfolder',fit_folder:$('#wfolder').value});toast('Folder set. Reading it now.');await load()});
  on('#corgo',async()=>{await api('coros/login',{email:$('#cem').value,password:$('#cpw').value});$('#cpw').value='';toast('COROS connected (experimental)');await api('watch',{source:'coros'});await load()});
  on('#cordis',async()=>{await api('coros/disconnect',{});toast('COROS disconnected');await load()});
  if($('#heatsw'))$('#heatsw').onchange=async()=>{await api('settings',{heat_adjust:$('#heatsw').value==='1'});toast($('#heatsw').value==='1'?'Heat adjustment on':'Heat adjustment off');await load()};
  const restartWait=()=>{toast('Restarting into the new version…');let n=0;const t=setInterval(async()=>{n++;try{const r=await fetch('/api/state',{headers:{'X-Requested-With':'periodize'}});if(r.ok){clearInterval(t);location.reload()}}catch(e){}if(n>60)clearInterval(t)},2000)};
  $$('[data-upd]').forEach(b=>b.onclick=async()=>{const act=b.dataset.upd,v=b.dataset.v;
    if(act==='install'&&!confirm('Update to version '+v+'? A backup is made first, and you can switch back under Settings, About.'))return;
    b.disabled=true;try{const r=await api('updates',{action:act,version:v});if(r.restarting)return restartWait();toast(act==='dismiss'?'Dismissed until the next version':'Checked');await load()}catch(e){b.disabled=false}});
  on('#updgo',async()=>{const v=$('#updver').value;if(v===S.update.running)return toast('That version is already running.');if(!confirm('Switch to version '+v+'? A backup is made first; the app restarts.'))return;
    const r=await api('updates',{action:'choose',version:v});if(r.restarting)restartWait()});
  if($('#updchk'))$('#updchk').onchange=async()=>{await api('settings',{update_check:$('#updchk').checked});toast($('#updchk').checked?'Update checks on':'Update checks off');await load()};
  on('#gmdis',async()=>{if(!confirm('Disconnect Garmin? The plan stops updating until you connect again.'))return;await api('garmin/disconnect',{});toast('Garmin disconnected');await load()});
  $$('.gpx').forEach(inp=>inp.onchange=async e=>{const f=e.target.files[0];if(!f)return;try{const pts=await readGpx(f);await api('races/'+inp.dataset.race+'/course',{points:pts});toast('Course added');await load()}catch(x){if(x&&x.message&&x.message!=='undefined')toast(x.message,'err')}});
  $$('[data-gpx]').forEach(b=>b.onclick=()=>$('#gpx'+b.dataset.gpx).click());
  $$('[data-climb]').forEach(b=>b.onclick=async()=>{const r=S.races.find(x=>x.id==b.dataset.climb);const v=prompt('Total climb of the course in metres (empty to clear)',r.climb_m!=null?Math.round(r.climb_m):'');if(v===null)return;await api('races/'+r.id+'/course',{climb_m:v.trim()});toast('Saved');await load()});
  const pace=async(id,t)=>{const r=await fetch('/api/races/'+id+'/pacing'+(t?'?time='+encodeURIComponent(t):''),{headers:{'X-Requested-With':'periodize'}});const jx=await r.json();if(!r.ok)return toast(jx.error||'Something went wrong.','err');PACE=Object.assign(jx,{id:id});render()};
  $$('[data-pace]').forEach(b=>b.onclick=()=>pace(b.dataset.pace));
  on('#pgo',()=>pace($('#pgo').dataset.race,$('#ptime').value));
  on('#pacex',()=>{PACE=null;render()});
  $$('[data-trend]').forEach(b=>b.onclick=()=>{TRV=b.dataset.trend;render();if(!TR)loadTrends()});
  on('#trex',()=>{TRV=null;render()});
  if($('#tov'))$('#tov').onclick=e=>{if(e.target.id==='tov'){TRV=null;render()}};
  if($('#pov'))$('#pov').onclick=e=>{if(e.target.id==='pov'){PACE=null;render()}};
  $$('[data-mz]').forEach(b=>b.onclick=()=>{MAPZ=Math.max(-3,Math.min(4,MAPZ+(+b.dataset.mz)));render()});
  if($('#mapsw'))$('#mapsw').onchange=async()=>{await api('settings',{map_tiles:$('#mapsw').value==='1'});toast('Saved');location.reload()};
  on('#shadd',async()=>{await api('shoes',{name:$('#shn').value,start:$('#shs').value,start_dist:$('#shm').value,alert_dist:$('#sha').value});toast('Shoes added');await load()});
  $$('[data-shdel]').forEach(b=>b.onclick=async()=>{await api('shoes/'+b.dataset.shdel,null,'DELETE');await load()});
  on('#ysave',async()=>{await api('settings',{sex:$('#ysex').value,birth_date:$('#ydob').value,gel_carbs_g:$('#ygel').value});toast('Saved');await load()});
  on('#ntest',async()=>{await api('notify/test',{});toast('Test message sent')});
  on('#bnow',async()=>{await api('backups',{});await api('settings',{auto_backup:$('#abk').value==='1'});toast('Backup made');await load()});
  on('#bres',async()=>{const o=$('#bsel').selectedOptions[0];if(!o||!o.value)return toast('Choose a backup.','err');const what=$('#bwhat').value, words={full:'everything',config:'your settings and races',plan:'the plan'}[what];
    if(!confirm('Restore '+words+' from this backup? The current state is saved first, so this can be undone.'))return;
    await api('backups',{restore:o.value,what:what});toast('Restored: '+words);await load()});
  if($('#abk'))$('#abk').onchange=async()=>{await api('settings',{auto_backup:$('#abk').value==='1'});toast('Saved')};
  $$('[data-dopen]').forEach(b=>b.onclick=()=>openDay(b.dataset.dopen));
  on('#dayx',()=>{DAY=null;render()});
  if($('#dov'))$('#dov').onclick=e=>{if(e.target.id==='dov'){DAY=null;render()}};
  on('#undo',async()=>{await api('plan/undo',{});toast('Move undone. Updating your watch.');await load()});
  $$('.day').forEach(d=>{const pick=()=>{SEL=SEL===d.dataset.date?null:d.dataset.date;render()};d.onclick=pick;d.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();pick()}}});
  on('#selx',()=>{SEL=null;render()});
  if($('#ov')){$('#ov').onclick=e=>{if(e.target.id==='ov'){SEL=null;render()}};const x=$('#selx');if(x&&document.activeElement===document.body)x.focus()}
  let from=null;
  $$('.day[draggable=true]').forEach(d=>{
    d.ondragstart=e=>{from=d.dataset.date;d.classList.add('drag');e.dataTransfer.effectAllowed='move';e.dataTransfer.setData('text/plain',from)};
    d.ondragend=()=>{d.classList.remove('drag');$$('.day.over').forEach(x=>x.classList.remove('over'))};
    d.ondragover=e=>{e.preventDefault();d.classList.add('over')};d.ondragleave=()=>d.classList.remove('over');
    d.ondrop=async e=>{e.preventDefault();d.classList.remove('over');const a=e.dataTransfer.getData('text/plain')||from,b=d.dataset.date;if(!a||a===b)return;
      try{const r=await api('plan/move',{from:a,to:b});r.warning?toast(r.warning,'warn'):toast('Swapped. Updating your watch.');await load()}catch(x){}}});
}
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&(SEL||DAY||PACE||TRV)){SEL=null;DAY=null;PACE=null;TRV=null;render()}});
load();
setInterval(()=>{const a=document.activeElement;if(a&&['INPUT','SELECT'].includes(a.tagName))return;if(document.querySelector('details[id^=tbox][open]'))return;if(document.querySelector('.day.drag'))return;load()},6000);
