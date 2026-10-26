/* History, a day in detail, trends, the change log and Explain my plan. One of the page scripts; see index.html for the order they load in (they share one scope). */
function histView(){
  if(!HIST)return `<div class="grid"><div class="card c12 loading">${skel(4)}</div></div>`;
  const H=HIST;
  let h=`<div class="grid"><div class="card"><p class="eyebrow">Execution, last 12 weeks</p>${H.average!==null?`<div class="big num ${scc(H.average)}">${H.average}</div><p class="small mute">average over ${H.count} planned session${H.count===1?'':'s'}</p>`:'<p class="small mute">No planned sessions have passed yet.</p>'}</div>
    <div class="card c8" id="exectrend"><p class="eyebrow">Execution score over time</p>${H.weeks.length>1?chart('Average execution score',H.weeks,x=>x.avg,x=>'Week of '+nice(x.week)+': '+x.avg+' over '+x.n+' sessions',x=>nice(x.week)):`<p class="small mute">${H.weeks.length?`Week of ${nice(H.weeks[0].week)}: ${H.weeks[0].avg} over ${H.weeks[0].n} session${H.weeks[0].n===1?'':'s'}. A chart appears after a second week.`:'Builds up week by week from the day the app started planning for you.'}</p>`}
      ${(t=>t.length>=3?lineChart(t.map(x=>[Date.parse(x.date)/864e5,x.score,x.avg,x.date]),2,'var(--brand)','Trend: average of the last 5 sessions',v=>Math.round(v),false,s=>nice(s[3])+': scored '+s[1]+', average '+s[2])
        :`<p class="small mute" id="trendwait" style="margin:10px 0 0">The trend line appears once three sessions have been scored${t.length?` (${t.length} so far)`:''}.</p>`)(H.trend||[])}
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
let UNI=false, MORE=false, CH={}, CHN=0, CHANGES=null, PACE=null, MAPZ=0, TR=null, TRV=null;
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
  if(!A)return TR?'':`<div class="card c12 loading" id="acccard"><p class="eyebrow">How accurate are the predictions?</p>${skel(3)}</div>`;
  const lean=Math.abs(A.bias)<1?'They are about right on average.':A.bias>0?`On average they are <b>${A.bias}% slower</b> than you actually ran: on the cautious side.`:`On average they are <b>${Math.abs(A.bias)}% faster</b> than you actually ran: on the optimistic side.`;
  return `<div class="card c12" id="acccard"><p class="eyebrow">How accurate are the predictions?</p>
    <p class="small" style="margin:0">Over your last ${A.n} race${A.n>1?'s':''}, predictions were off by <b>${A.mean_abs}%</b> on average. ${lean}</p>
    <div style="max-height:300px;overflow:auto;margin-top:10px"><table><tr><th>Date</th><th>Race</th><th class="r">Predicted</th><th class="r">Actual</th><th class="r">Off by</th></tr>
      ${A.rows.map(r=>`<tr><td class="num">${nice(r.date)} ${r.date.slice(0,4)}</td><td>${E(r.distance)}${r.name!==r.distance?` <span class="mute xs">${E(r.name)}</span>`:''}</td><td class="r num">${r.predicted}</td><td class="r num" ${r.weather?`title="${E(r.weather)}"`:''}><b>${r.actual}</b>${r.weather&&r.weather.includes('Worth')?' <span class="xs mute">☀</span>':''}</td><td class="r num ${Math.abs(r.error)<=2?'green':Math.abs(r.error)<=5?'':'amber'}">${r.error>0?'+':''}${r.error}%</td></tr>`).join('')}</table></div>
    <p class="xs mute" style="margin:8px 0 0">Each prediction is rebuilt from what was known the Monday before the race, with today's rules, and compared with your time adjusted to a flat course where the course is known, and to neutral weather where the day's weather is known (marked ☀). A plus means the prediction was slower than you ran. Wind, pacing and how hard you raced all add to the gap.</p></div>`}
function recoveryCard(){const R=TR&&TR.recovery;
  if(!R)return `<div class="card c12${TR?'':' loading'}" id="reccard"><p class="eyebrow">Recovery trends</p>${TR?'<p class="small mute">Builds up once a few weeks of sleep and HRV are in.</p>':skel(4)}</div>`;
  const one=(k,color,invert)=>{const x=R[k];if(!x||x.rows.length<3)return '';const ser=x.rows.map(r=>[dayNum(r.date),r.v]);const fv=v=>v+' '+x.unit;
    return `<div style="grid-column:span 4;min-width:0">${lineChart(ser,1,color,x.label,fv,invert,s=>{const r=x.rows.find(y=>dayNum(y.date)===s[0]);return nice(r.date)+': '+fv(r.v)})}
      <p class="xs mute" style="margin:4px 0 0">${x.normal?`Your normal ${x.normal[0]} ${x.unit} (±${x.normal[1]}) `:''}${dirTag(x.dir,'7 days against your normal')}</p></div>`};
  return `<div class="card c12" id="reccard"><p class="eyebrow">Recovery trends</p><div class="grid" style="gap:18px">${one('hrv','var(--green)',false)}${one('rhr','var(--amber)',true)}${one('sleep_h','var(--brand)',false)}</div>
    <p class="xs mute" style="margin:8px 0 0">7-day averages over 12 weeks, the way the research reads them: one night is noise, a week-long drift is real. Higher HRV, lower resting heart rate and more sleep are better, so each chart is drawn with better as up. These are the same figures the daily adjustment uses.</p></div>`}
let CLALL=false;
function changesView(){if(!CHANGES)return `<div class="grid"><div class="card c12 loading">${skel(4)}</div></div>`;
  const col={Added:'green',Changed:'amber',Removed:'red',Fixed:'unknown'}, SHOW=6;
  const inline=t=>E(t).replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<b>$1</b>');
  const list=CLALL?CHANGES:CHANGES.slice(0,SHOW);
  return `<div class="cl"><div class="cl-head"><h2>Change log</h2><p class="mute">You are running version <b class="num">${E(S.version)}</b>. Every version, newest first, with what was added, changed, removed or fixed.</p></div>
    ${list.map(v=>`<section class="cl-rel"><div class="cl-meta"><div class="cl-v">${E(v.version)}</div>
      <div class="cl-d">${v.date?new Date(v.date+'T12:00').toLocaleDateString(undefined,{day:'numeric',month:'short',year:'numeric'}):''}</div>
      <div class="cl-tags">${v.version===S.version?'<span class="cl-tag" style="color:var(--green)">Running</span>':''}${v.version.includes('-beta')?'<span class="cl-tag" style="color:var(--amber)">Beta</span>':''}</div></div>
      <div>${v.sections.map(x=>`<div class="cl-sec"><h3 class="${col[x.title]||'unknown'}" style="color:var(--${{green:'green',amber:'amber',red:'red'}[col[x.title]]||'mute'})"><i></i>${E(x.title)}</h3><ul>${x.items.map(i=>`<li>${inline(i)}</li>`).join('')}</ul></div>`).join('')}</div></section>`).join('')}
    ${CHANGES.length>SHOW?`<button class="ghost cl-more" id="clmore">${CLALL?'Show fewer':`Show all ${CHANGES.length} versions`}</button>`:''}</div>`}
async function loadChanges(){CHANGES=(await api('changelog')).versions;if(view==='changes')render()}
async function loadAbout(){ABOUT=(await api('about')).sections;REFS=await api('references');if(view==='about')render()}
let REFS=null;
function refsCard(){if(!REFS)return '';const li=x=>`<li>${E(x.text)}${x.used.length?` <span class="mute xs">Used in principle${x.used.length>1?'s':''} ${x.used.join(', ')}.</span>`:''}</li>`;
  return `<div class="card c12" id="refs"><p class="eyebrow">The research behind the plan</p><p class="small">${REFS.papers.length} peer-reviewed studies are used. Only their findings are used: no text, tables or figures are copied. The numbered principles are in PRINCIPLES.md, which comes with the app.</p>
    <details id="refs-papers" ${TOPEN['refs-papers']?'open':''}><summary class="small" style="cursor:pointer"><b>Peer-reviewed studies (${REFS.papers.length})</b></summary><ul class="why">${REFS.papers.map(li).join('')}</ul></details>
    ${REFS.other.length?`<details id="refs-other" ${TOPEN['refs-other']?'open':''}><summary class="small" style="cursor:pointer"><b>Other sources, not peer-reviewed (${REFS.other.length})</b></summary><ul class="why">${REFS.other.map(li).join('')}</ul></details>`:''}</div>`}
async function openExplain(){let d=$('#explaindlg');if(!d){d=document.createElement('dialog');d.id='explaindlg';d.className='sheet';d.setAttribute('aria-label','Explain my plan');document.body.appendChild(d);
    d.addEventListener('click',e=>{if(e.target===d||e.target.id==='explainclose')d.close()})}
  const head='<div class="sh"><p class="eyebrow">Explain my plan</p><button class="ghost" id="explainclose">Close</button></div>';
  d.innerHTML=head+'<div class="sb"><span class="spin"></span>Loading</div>';d.showModal();d.scrollTop=0;
  try{const x=await api('explain');
    d.innerHTML=head+`<div class="sb"><p class="small mute" style="margin:12px 0 0">This plan is written for you. Each decision below shows what was decided, what in your own data led to it, and where the rule comes from.</p>
      ${x.sections.map(s=>`<div class="item"><p class="h">${E(s.title)}</p><p class="dec">${E(s.decision)}</p>
        <p class="k"><b>From your data.</b> ${E(s.because)}</p><p class="k mute"><b>Where the rule comes from.</b> ${E(s.evidence)}</p></div>`).join('')||'<p class="small mute">The plan has not been built yet. Sync first.</p>'}</div>`}
  catch(e){d.innerHTML=head+'<div class="sb"><p class="small">Could not load the explanation.</p></div>'}}
async function loadLogs(){logs=(await api('logs')).lines;if(view==='log')render()}

