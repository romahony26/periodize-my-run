/* Weather charts, Met Éireann warnings and the weather wording. One of the page scripts; see index.html for the order they load in (they share one scope). */
function wxChart(rows,o){
  // rows: [hour, temp, dew, pct, rain, chance]; one chart, one axis, its own panel. o: {title, unit, kind:'line'|'bar', cols:[[index,color,name]], min, tip, win, best}
  const W=600,Ht=110,n=rows.length,cols=o.cols,vs=rows.flatMap(r=>cols.map(c=>r[c[0]])).filter(v=>v!=null);if(n<3||!vs.length)return '';
  let lo=o.kind==='bar'?0:Math.min(...vs), hi=Math.max(Math.max(...vs),o.kind==='bar'?(o.min||1):lo+2);
  const step=[.5,1,2,5,10,20,50].find(k=>(hi-lo)/k<=4)||50;
  lo=o.kind==='bar'?0:Math.floor(lo/step)*step;hi=Math.ceil(hi/step)*step;if(hi<=lo)hi=lo+step;
  const ticks=[];for(let v=lo;v<=hi+1e-9;v+=step)ticks.push(+v.toFixed(2));
  const x=i=>(i+.5)/n*W, y=v=>(1-(v-lo)/(hi-lo))*(Ht-14)+7, slot=W/n, ST='var(--line)';
  const id='c'+(++CHN);CH[id]=rows.map((r,i)=>[(i+.5)/n,y(r[cols[0][0]]==null?lo:r[cols[0][0]])/Ht,o.tip(r)]);
  let g=ticks.map(v=>`<line x1="0" x2="${W}" y1="${y(v).toFixed(1)}" y2="${y(v).toFixed(1)}" stroke="${ST}" stroke-width="1" vector-effect="non-scaling-stroke"/>`).join('');
  if(o.win){const a=rows.findIndex(r=>r[0]>=o.win[0]),b=rows.length-1-[...rows].reverse().findIndex(r=>r[0]<=o.win[1]);
    if(a>=0&&b>=a&&b<n)g+=`<rect x="${(a*slot).toFixed(1)}" y="0" width="${((b-a+1)*slot).toFixed(1)}" height="${Ht}" fill="var(--brand)" opacity=".09"/>`}
  const bi=rows.findIndex(r=>r[0]===o.best);
  if(bi>=0)g+=`<line x1="${x(bi).toFixed(1)}" x2="${x(bi).toFixed(1)}" y1="0" y2="${Ht}" stroke="var(--brand)" stroke-width="1.5" vector-effect="non-scaling-stroke"/>`;
  if(o.kind==='bar')cols.forEach(c=>rows.forEach((r,i)=>{const v=r[c[0]];if(!v)return;const t=y(v),bw=Math.min(slot-3,24);
    g+=`<rect x="${(x(i)-bw/2).toFixed(1)}" y="${t.toFixed(1)}" width="${bw.toFixed(1)}" height="${(y(0)-t).toFixed(1)}" fill="${c[1]}"/>`}));
  else cols.forEach(c=>{const d=rows.filter(r=>r[c[0]]!=null).map((r,i)=>(i?'L':'M')+x(rows.indexOf(r)).toFixed(1)+' '+y(r[c[0]]).toFixed(1)).join(' ');
    g+=`<path d="${d}" fill="none" stroke="${c[1]}" stroke-width="2" vector-effect="non-scaling-stroke" stroke-linejoin="round" stroke-linecap="round"/>`});
  const yl=ticks.map(v=>`<span style="position:absolute;right:0;top:${(y(v)/Ht*100).toFixed(2)}%;transform:translateY(-50%)">${v}</span>`).join('');
  const xl=rows.map((r,i)=>`<span style="position:absolute;left:${((i+.5)/n*100).toFixed(2)}%;transform:translateX(-50%)">${r[0]}</span>`).join('');
  const key=cols.length>1?cols.map(c=>`<span style="margin-left:12px"><i style="display:inline-block;width:14px;height:3px;border-radius:2px;background:${c[1]};vertical-align:middle;margin-right:5px"></i>${E(c[2])}</span>`).join(''):'';
  return `<div style="border:1px solid var(--line);border-radius:12px;padding:10px 12px 8px;margin-top:12px">
    <div class="xs" style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap"><span><b>${E(o.title)}</b> <span class="mute">${E(o.unit)}</span></span><span class="mute">${key}</span></div>
    <div style="display:grid;grid-template-columns:36px minmax(0,1fr);column-gap:6px;margin-top:8px">
      <div class="xs mute num" style="position:relative;height:96px;text-align:right" aria-hidden="true">${yl}</div>
      <div><div class="lc" data-ch="${id}" tabindex="0" role="img" aria-label="${E(o.title)} by hour, ${E(o.unit)}. Use the left and right arrow keys to read values."><svg viewBox="0 0 ${W} ${Ht}" preserveAspectRatio="none" style="width:100%;height:96px;display:block" aria-hidden="true">${g}</svg><i class="cur"></i><i class="pt" style="background:${cols[0][1]}"></i><span class="tp num" aria-live="polite"></span></div>
        <div class="xs mute num" style="position:relative;height:16px;margin-top:3px" aria-hidden="true">${xl}</div></div></div>
    <div class="xs mute" style="text-align:center;margin-top:0">hour of the day (24 h)</div></div>`}
function wxCharts(w){
  const r=w.hourly||[];if(r.length<3)return '';
  const common={best:w.hour,win:w.window&&!w.dark?w.window:null}, hh=v=>v+':00', anyHeat=r.some(x=>x[3]===null||x[3]>0);
  const t=wxChart(r,Object.assign({title:'Temperature',unit:'°C',kind:'line',cols:[[1,'var(--long)','Air']],tip:x=>`${hh(x[0])} · ${Math.round(x[1])}°C`},common));
  const rain=wxChart(r,Object.assign({title:'Rain',unit:'mm an hour',kind:'bar',min:2,cols:[[4,'var(--brand)','Rain']],tip:x=>`${hh(x[0])} · ${x[4]==null?'no rain figure':x[4]+' mm'}${x[5]!=null?', '+x[5]+'% chance':''}`},common));
  const heat=anyHeat?wxChart(r,Object.assign({title:'Heat cost to your pace',unit:'% slower',kind:'bar',min:2,cols:[[3,'var(--amber)','Slower for the heat']],
    tip:x=>`${hh(x[0])} · ${x[3]===null?'too hot for hard running':(x[3]||0)+'% slower'} (${Math.round(x[1])}°C)`},Object.assign({},common,{}))):'';
  const tab=`<details style="margin-top:8px"><summary class="xs mute" style="cursor:pointer">Hourly figures</summary><table class="xs" style="margin-top:6px"><tr><th>Hour</th><th class="r">Air °C</th><th class="r">Slower %</th><th class="r">Rain mm</th><th class="r">Chance %</th></tr>${r.map(x=>`<tr><td>${hh(x[0])}${x[0]===w.hour?' ★':''}</td><td class="r num">${x[1]}</td><td class="r num">${x[3]===null?'too hot':x[3]}</td><td class="r num">${x[4]??''}</td><td class="r num">${x[5]??''}</td></tr>`).join('')}</table></details>`;
  return t+rain+heat+`<p class="xs mute" style="margin:6px 0 0">The vertical line marks the best hour${common.win?'; the tinted band is your running window':''}. ${anyHeat?'':'No hour of the day costs any pace for heat. '}Daylight hours only.</p>`+tab}
function metWarn(m,day){
  /* Met Éireann's warnings as issued (wording, level, times and area are not changed), with the credit its licence requires.
     One line each; the full text opens on a tap. */
  if(!m)return '';
  const when=t=>{const d=new Date(t);return isNaN(d)?t:d.toLocaleString('en-IE',{weekday:'short',day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'})};
  const col=e=>/^Red/.test(e)?'red':/^Orange/.test(e)?'amber':'';
  const items=(m.days&&m.days[day])||[];
  const attr=`<p class="xs mute" style="margin:4px 0 0">${E(m.attribution[0])} · www.met.ie · CC BY 4.0 · full notice under How it works</p>`;
  if(m.stale)return `<div class="metwarn"><p class="xs mute" style="margin:6px 0 0"><b>Met Éireann warnings</b> could not be refreshed in the last three hours, so none is shown. Check <a href="https://www.met.ie/warnings" target="_blank" rel="noopener noreferrer">www.met.ie/warnings</a>.</p>${attr}</div>`;
  if(!m.county)return '';
  return `<div class="metwarn"><p class="lab2" style="margin:8px 0 0">Met Éireann · ${E(m.county)}</p>`+
    (items.length?items.map(w=>`<details style="margin:4px 0 0"><summary class="small" style="cursor:pointer"><b class="${col(w.event)}">${E(w.event)}</b> · ${E(w.severity)} · ${E(when(w.onset))} to ${E(when(w.expires))}</summary>
      <div class="small" style="margin:4px 0 0 14px">${E(w.headline)}<br><span style="white-space:pre-line">${E(w.description)}</span><br>
      <span class="xs mute" title="${E(w.onset)} to ${E(w.expires)}, issued ${E(w.sent)}">${E(w.certainty)} · issued ${E(when(w.sent))} · ${E(w.area)}</span></div></details>`).join('')
      :`<p class="xs mute" style="margin:2px 0 0">No warning in force.</p>`)+attr+'</div>'}
function wxWind(k){return U()==='mi'?Math.round(k/1.609344)+' mph':k+' km/h'}
function wxTip(w){return wxLines(w).join(' ')}
function wxBest(w){
  const rain=w.chance==null&&w.rain==null?'':w.wet?`${w.chance!=null?w.chance+'%':'Rain'}`:'Dry', rk=w.wet?'Chance of rain':'Rain';
  const stat=(v,k,c)=>`<div class="stat"><div class="v num ${c||''}">${E(v)}</div><div class="k">${E(k)}</div></div>`;
  const why=[w.window?`inside your hours (${w.window[0]}:00 to ${w.window[1]}:00)`:'',w.sunrise?`between sunrise ${w.sunrise} and an hour before sunset ${w.sunset}`:'in daylight'].filter(Boolean).join(', ');
  return `<div id="besttime" style="border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:10px 0 0;background:color-mix(in srgb,var(--brand) 6%,var(--surface))">
    <p class="eyebrow" style="margin:0">Best time to run</p>
    <p style="margin:2px 0 0;font-size:30px;font-weight:730;letter-spacing:-.03em" class="num">${w.hour}:00 <span class="small mute" style="font-size:14px;font-weight:600;letter-spacing:0">${E(w.pct===null?'too hot for hard running':w.pct>0?'about '+w.pct+'% slower for the heat':'no heat slowdown')}</span></p>
    <div class="stats" style="grid-template-columns:repeat(auto-fit,minmax(96px,1fr));margin:8px 0 0">${stat(w.temp+'°C','Air then')}${w.wind!=null?stat(wxWind(w.wind),'Wind'):''}${rain?stat(rain,rk,w.wet?'amber':''):''}${w.rain>0?stat(w.rain+' mm','Rain that hour'):''}</div>
    <p class="xs mute" style="margin:8px 0 0">Chosen as the ${w.wet?'driest start, then the one that costs least pace':'best dry start: the one that costs least pace for the weather, then nearest your usual hour'}, ${E(why)}.${w.dark?' Your hours are in the dark on this day.':''}${w.usual?` Your usual ${w.usual.hour}:00 would be ${w.usual.temp}°C${w.usual.wet?' and wet':''}${w.usual.pct>0?', about '+w.usual.pct+'% slower':''}.`:''}</p></div>`}
function wxLines(w,short){const r=[];
  if(!short)r.push(`Best start ${w.hour}:00: ${w.temp}°C${w.wind!=null?', wind '+wxWind(w.wind):''}${w.chance!=null?', '+(w.wet?w.chance+'% chance of rain':'dry'):''}.`);
  if(!short)r.push(w.pct===null?'Too hot and humid for hard running at any hour: run early or late, or keep it easy.':w.pct>0?`About ${w.pct}% slower for the heat at that hour.`:'No heat slowdown at that hour.');
  if(!short&&w.dark)r.push('Your running window is in the dark on this day.');
  if(!short&&w.wet)r.push('Every hour in daylight has some rain in the forecast; this is the driest.');
  if(!short&&w.usual)r.push(`Your usual ${w.usual.hour}:00 would be ${w.usual.temp}°C${w.usual.wet?' and wet':''}${w.usual.pct===null?', too hot for hard running':w.usual.pct>0?', about '+w.usual.pct+'% slower':''}.`);
  r.push(`Day (daylight): ${w.low}–${w.high}°C${w.rain_day?', '+w.rain_day+' mm of rain':', no rain expected'}${w.sunrise?`. Sunrise ${w.sunrise}, sunset ${w.sunset}.`:'.'}`);
  return r}
