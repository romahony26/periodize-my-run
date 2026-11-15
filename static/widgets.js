/* Pieces shared by the pages: folding notes, the Fitness sections, rings, charts, step lists. One of the page scripts; see index.html for the order they load in (they share one scope). */
/* After a page is drawn: the long explanations fold away, empty cards shrink to one line, the Fitness page splits into four sections,
   and (on a phone) today's session comes before the goal. Done on the drawn page so every card keeps its own code. */
let FTAB=(()=>{try{return localStorage.getItem('ftab')||'now'}catch(e){return 'now'}})();
const FSECS=[['now','Now'],['progress','Progress'],['pred','Predictions'],['records','Records']];
const FMAP=[['Threshold pace','now'],['Race-specific endurance','now'],['Steps outside','now'],['Fitness, fatigue','now'],['Aerobic drift','now'],['Recovery trends','now'],['When you run','now'],
  ['Is it working','progress'],['Plan scorecard','progress'],['Plan against actual','progress'],['Last eight weeks','progress'],['Paces now','progress'],
  ['What each marathon','pred'],['Three ways to estimate','pred'],['Is the gap closing','pred'],['Race predictor','pred'],['How accurate','pred'],['VO2max','pred'],
  ['Race results','records'],['Personal bests','records'],['Your history','records'],['Your limits','records']];
function foldNotes(root){root.querySelectorAll('p.xs.mute').forEach(p=>{
  if(p.id||p.closest('details,table,.modal,.ov')||p.textContent.length<150||p.parentElement.classList.contains('stat')||/^(Load this week|Warning signs)/.test(p.textContent))return;     // numbers stay in view
  const d=document.createElement('details');d.className='note';d.innerHTML='<summary>What is this?</summary>';p.replaceWith(d);d.append(p)})}
function setFtab(t){FTAB=t;try{localStorage.setItem('ftab',t)}catch(e){}
  $$('[data-fsec]').forEach(c=>c.hidden=c.dataset.fsec!==t);$$('[data-ftab]').forEach(b=>{const on=b.dataset.ftab===t;b.classList.toggle('on',on);b.setAttribute('aria-selected',on?'true':'false')});const l=$('.stabs[aria-label="Fitness sections"]');if(l)rove(l)}
function polish(){const m=$('#main');if(!m)return;
  // on a phone a table's header row is hidden and each row becomes a block, so every cell carries its column's name
  m.querySelectorAll('table').forEach(t=>{const h=[...t.querySelectorAll('th')].map(x=>x.textContent.trim());if(!h.length)return;
    t.querySelectorAll('tr').forEach(r=>[...r.children].forEach((c,i)=>{if(c.tagName==='TD'&&i&&h[i]&&c.colSpan===1)c.dataset.l=h[i]}))});
  if(view==='plan'){
    const g=m.querySelector('.hero');if(g){g.id='goalcard';
      const fp=[...g.querySelectorAll('p.small')].find(p=>p.textContent.includes('It assumes you complete'));
      if(fp){const html=fp.innerHTML,i=html.indexOf('. It assumes'),det=document.createElement('details');det.className='note';det.innerHTML='<summary>How this forecast is built</summary>';
        const body=document.createElement('p');body.className='small';body.style.margin='6px 0 0';
        if(i>0){fp.innerHTML=html.slice(0,i+1);body.innerHTML=html.slice(i+2);det.append(body);const xs=fp.nextElementSibling;if(xs&&xs.matches('p.xs'))det.append(xs);fp.after(det)}
        else{body.innerHTML=html;det.append(body);const xs=fp.nextElementSibling;if(xs&&xs.matches('p.xs'))det.append(xs);fp.replaceWith(det)}}}
    const cards=[...m.querySelectorAll('.grid > .card.c6')];const td=cards.find(c=>c.id==='tomorrowcard')||cards.find(c=>/^(Today|Tomorrow)/.test((c.querySelector('.eyebrow')||{}).textContent||''));
    if(td&&!td.id)td.id='todaycard';
  }
  if(view==='you'){const grid=m.querySelector('.grid');if(!grid)return;
    const cards=[...grid.children].filter(c=>c.classList.contains('card'));
    cards.forEach(c=>{const t=((c.querySelector('.eyebrow')||{}).textContent||'').trim();const hit=FMAP.find(([k])=>t.startsWith(k));c.dataset.fsec=hit?hit[1]:'now'});
    const rr=cards.find(c=>/^Race results/.test((c.querySelector('.eyebrow')||{}).textContent||''));
    if(rr&&!S.results.length){const kids=[...rr.children].filter(x=>!x.classList.contains('eyebrow'));const keep=kids.find(x=>x.matches('p.small'));const d=document.createElement('details');d.className='note';
      d.innerHTML='<summary>Add a result by hand or import a log</summary>';kids.filter(x=>x!==keep).forEach(x=>d.append(x));rr.append(d)}
    foldNotes(grid);
    const bar=document.createElement('div');bar.className='stabs';bar.setAttribute('role','tablist');bar.setAttribute('aria-label','Fitness sections');
    bar.innerHTML=FSECS.map(([k,t])=>`<button role="tab" data-ftab="${k}">${t}</button>`).join('');
    grid.before(bar);bar.querySelectorAll('button').forEach(b=>b.onclick=()=>setFtab(b.dataset.ftab));tabKeys(bar,b=>setFtab(b.dataset.ftab));setFtab(FTAB)}
}
const skel=(n=3)=>`<div class="skel" role="status" aria-live="polite" aria-label="Loading">${Array.from({length:n},(_,i)=>`<i style="width:${[92,78,64,86][i%4]}%"></i>`).join('')}<span class="sr">Loading</span></div>`;
function ring(pct,label){const c=2*Math.PI*30;return `<svg class="ring" viewBox="0 0 74 74"><circle cx="37" cy="37" r="30" fill="none" stroke="var(--line)" stroke-width="6"/><circle cx="37" cy="37" r="30" fill="none" stroke="url(#lg)" stroke-width="6" stroke-linecap="round" stroke-dasharray="${c}" stroke-dashoffset="${c*(1-pct)}" transform="rotate(-90 37 37)"/><text x="37" y="42" text-anchor="middle">${label}</text></svg>`}
function chart(title,rows,val,tip,label){
  if(!rows||rows.length<2)return '';
  const vs=rows.map(val), mn=Math.min(...vs), mx=Math.max(...vs), lo=mn-Math.max((mx-mn)*0.25,1);
  return `<p class="xs mute" style="margin:12px 0 0">${E(title)} <span class="mute">· hover or tap a bar</span></p><div class="chart" role="list">${rows.map(x=>`<div class="b" role="listitem" tabindex="0" data-tip="${E(tip(x))}" aria-label="${E(tip(x))}" style="height:${Math.max(6,Math.round(100*(val(x)-lo)/(mx-lo||1)))}%"></div>`).join('')}</div>
    <div class="xs mute" style="display:flex;justify-content:space-between"><span>${E(label(rows[0]))}</span><span>${E(label(rows[rows.length-1]))}</span></div>`}
function stepList(text){return text?`<ul class="steps">${text.split('; ').map(x=>`<li>${E(x)}</li>`).join('')}</ul>`:''}


/* A session drawn as blocks: width is time, height and colour are effort. The numbers come with each planned day (engine.shape). */
function wprof(p,tall){
  if(!p||p.length<2)return '';
  const tot=p.reduce((a,x)=>a+x[0],0); if(!tot)return '';
  const col=r=>r===0?'var(--line)':r<0.8?'var(--easy)':r<0.9?'var(--brand2)':r<0.97?'var(--key)':r<1.03?'var(--long)':'var(--race)';
  const H=tall?44:30; let x=0;
  const bars=p.map(b=>{const w=1000*b[0]/tot,h=b[1]===0?3:Math.max(5,Math.round(H*Math.min(1,(b[1]-0.55)/0.6))),r=`<rect x="${x.toFixed(1)}" y="${H-h}" width="${Math.max(w-(p.length>12?0.6:2),0.8).toFixed(1)}" height="${h}" rx="1.5" fill="${col(b[1])}"/>`;x+=w;return r}).join('');
  return `<svg class="wprof" viewBox="0 0 1000 ${H}" preserveAspectRatio="none" role="img" aria-label="The session as blocks: width is time, height is effort" style="height:${H}px">${bars}</svg>`;
}
/* Seven small bars for a week: each day's miles, coloured by the kind of day. */
function wkSpark(w){const mi=d=>d.past&&d.done?d.done.miles:(d.miles||0), mx=Math.max(...w.map(mi),1);
  return `<span class="wspark" aria-hidden="true">${w.map(d=>`<i class="${d.past&&d.done&&!d.type?'Easy':d.type||'Rest'}" style="height:${mi(d)?Math.max(3,Math.round(22*mi(d)/mx)):2}px"></i>`).join('')}</span>`}

/* The goal race's forecast week by week against the goal: two lines (if raced that week; forecast for race day), the goal as a level line,
   and a dashed line from where you are now to the goal on race day. Time runs left to right up to race day; faster is higher. */
function trendChart(T){
  const a=T.today||[], b=T.points||[], all=a.concat(b);if(all.length<2)return '';
  const day=d=>Date.parse(d+'T00:00:00Z')/864e5, x0=Math.min(...all.map(p=>day(p.monday))), x1=day(T.race);
  const ys=all.map(p=>p.s).concat(T.goal_s?[T.goal_s]:[]), lo=Math.min(...ys), hi=Math.max(...ys), pad=Math.max((hi-lo)*.15,60);
  const W=innerWidth<700?340:640,H=200,L=54,R=10,Tp=10,B=22, X=d=>L+(W-L-R)*(day(d)-x0)/(x1-x0||1), Y=s=>Tp+(H-Tp-B)*(s-(lo-pad))/((hi+pad)-(lo-pad));
  const line=(ps,cls)=>ps.length?`<polyline class="${cls}" points="${ps.map(p=>X(p.monday).toFixed(1)+','+Y(p.s).toFixed(1)).join(' ')}"/>${ps.map(p=>`<circle class="${cls}" cx="${X(p.monday).toFixed(1)}" cy="${Y(p.s).toFixed(1)}" r="3"><title>Week of ${E(p.monday)}: ${E(p.time)}</title></circle>`).join('')}`:'';
  const last=a[a.length-1], ticks=[lo,T.goal_s&&T.goal_s!==lo?T.goal_s:null,hi].filter((v,i,arr)=>v&&arr.indexOf(v)===i);
  return `<svg class="trend" viewBox="0 0 ${W} ${H}" role="img" aria-label="Marathon estimates week by week against the goal time">
    ${ticks.map(v=>`<text x="${L-6}" y="${(Y(v)+4).toFixed(1)}" text-anchor="end">${hmsOut(v)}</text><line class="grid" x1="${L}" x2="${W-R}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}"/>`).join('')}
    ${T.goal_s?`<line class="goal" x1="${L}" x2="${W-R}" y1="${Y(T.goal_s).toFixed(1)}" y2="${Y(T.goal_s).toFixed(1)}"/>`:''}
    ${T.goal_s&&last?`<line class="need" x1="${X(last.monday).toFixed(1)}" y1="${Y(last.s).toFixed(1)}" x2="${W-R}" y2="${Y(T.goal_s).toFixed(1)}"/>`:''}
    ${line(b,'fc')}${line(a,'nw')}
    <text x="${L}" y="${H-5}">${E(nice(all.map(p=>p.monday).sort()[0]))}</text><text x="${W-R}" y="${H-5}" text-anchor="end">Race day</text></svg>`}
