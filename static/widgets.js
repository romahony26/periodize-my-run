/* Pieces shared by the pages: folding notes, the Fitness sections, rings, charts, step lists. One of the page scripts; see index.html for the order they load in (they share one scope). */
/* After a page is drawn: the long explanations fold away, empty cards shrink to one line, the Fitness page splits into four sections,
   and (on a phone) today's session comes before the goal. Done on the drawn page so every card keeps its own code. */
let FTAB=(()=>{try{return localStorage.getItem('ftab')||'now'}catch(e){return 'now'}})();
const FSECS=[['now','Now'],['progress','Progress'],['pred','Predictions'],['records','Records']];
const FMAP=[['Threshold pace','now'],['Race-specific endurance','now'],['Steps outside','now'],['Fitness, fatigue','now'],['Aerobic drift','now'],['Recovery trends','now'],['When you run','now'],
  ['Is it working','progress'],['Plan scorecard','progress'],['Plan against actual','progress'],['Last eight weeks','progress'],['Paces now','progress'],
  ['Race predictor','pred'],['How accurate','pred'],['VO2max','pred'],
  ['Race results','records'],['Personal bests','records'],['Shoes','records'],['Your history','records'],['Your limits','records']];
function foldNotes(root){root.querySelectorAll('p.xs.mute').forEach(p=>{
  if(p.id||p.closest('details,table,.modal,.ov')||p.textContent.length<150||p.parentElement.classList.contains('stat')||/^(Load this week|Warning signs)/.test(p.textContent))return;     // numbers stay in view
  const d=document.createElement('details');d.className='note';d.innerHTML='<summary>What is this?</summary>';p.replaceWith(d);d.append(p)})}
function setFtab(t){FTAB=t;try{localStorage.setItem('ftab',t)}catch(e){}
  $$('[data-fsec]').forEach(c=>c.hidden=c.dataset.fsec!==t);$$('[data-ftab]').forEach(b=>{const on=b.dataset.ftab===t;b.classList.toggle('on',on);b.setAttribute('aria-selected',on?'true':'false')});const l=$('.stabs[aria-label="Fitness sections"]');if(l)rove(l)}
function polish(){const m=$('#main');if(!m)return;
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
    // an empty list collapses to its heading and one line
    const sh=$('#shoecard');if(sh&&!S.shoes.length){const rest=[...sh.children].filter(x=>!x.classList.contains('eyebrow'));const d=document.createElement('details');d.className='note';
      d.innerHTML='<summary>No shoes yet: add a pair</summary>';rest.forEach(x=>d.append(x));sh.append(d)}
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

