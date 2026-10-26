/* Core: helpers, state, the API call, loading and drawing the page. One of the page scripts; see index.html for the order they load in (they share one scope). */
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const E=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let HIST=null, DAY=null, SEL=null, S=null, ABOUT=null, view='plan', wiz={step:1,mfa:false,prefs:null}, logs=[], toastT=null;
const LOGO=`<svg viewBox="0 0 48 48"><rect width="48" height="48" rx="12" fill="url(#lg)"/><path d="M10 34l6.5-7 4.5 3.5 6-9.5 4.5 3.5L38 13" fill="none" stroke="#fff" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/><circle cx="38" cy="13" r="3.4" fill="#fff"/></svg>`;
const DOW=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
const DIST=[['5K',3.107],['5 miles',5],['10K',6.214],['10 miles',10],['Half marathon',13.109],['Marathon',26.219],['50K',31.07],['50 miles',50],['100K',62.14],['100 miles',100]];
const KM=1.609344, U=()=>S.settings.units, dU=m=>U()==='mi'?`${Math.round(m).toLocaleString()} mi`:`${Math.round(m*KM).toLocaleString()} km`;
const hmsOut=s=>{const h=Math.floor(s/3600),m=Math.floor(s%3600/60),x=Math.round(s%60);return h?`${h}:${String(m).padStart(2,'0')}:${String(x).padStart(2,'0')}`:`${m}:${String(x).padStart(2,'0')}`};
const hmsIn=t=>{const p=String(t||'').trim().split(':').map(Number);if(!p.length||p.some(isNaN))return 0;return p.reduce((a,x)=>a*60+x,0)};
const fmt=s=>{s=Math.round(s);const h=Math.floor(s/3600),m=Math.floor(s%3600/60),x=String(s%60).padStart(2,'0');return h?`${h}:${String(m).padStart(2,'0')}:${x}`:`${m}:${x}`};
const nice=d=>new Date(d+'T12:00').toLocaleDateString(undefined,{day:'numeric',month:'short'});
function toast(t,k){const e=$('#toast');e.textContent=t;e.className='on '+(k||'');clearTimeout(toastT);toastT=setTimeout(()=>e.className='',k?6500:3200)}
async function api(path, body, method){
  const r=await fetch('/api/'+path,{method:method||(body?'POST':'GET'),headers:{'Content-Type':'application/json','X-Requested-With':'periodize'},body:body?JSON.stringify(body):undefined});
  const j=await r.json().catch(()=>({}));
  if(r.status===401){authView(j.auth);throw new Error('auth')}
  if(!r.ok){toast(j.error||'Something went wrong.','err');throw new Error(j.error)}
  if(path==='settings')DIRTY=false;
  return j;
}
let fastT=null, LASTUI=0, DIRTY=false;
// The page redraws itself as new data arrives. That closes an open dropdown and resets unsaved choices, so it holds off while you are
// using a control (and, on Settings, until your changes are saved).
document.addEventListener('pointerdown',e=>{if(e.target.closest&&e.target.closest('select,input,textarea,label'))LASTUI=Date.now()},true);
document.addEventListener('focusin',e=>{if(e.target.matches&&e.target.matches('select,input,textarea'))LASTUI=Date.now()},true);
document.addEventListener('keydown',e=>{if(e.target.matches&&e.target.matches('select,input,textarea'))LASTUI=Date.now()},true);
document.addEventListener('change',e=>{if(e.target.matches&&e.target.matches('select,input,textarea,button.tgl')){LASTUI=Date.now();if(view==='settings'){DIRTY=true;const sb=$('#savebar');if(sb&&e.target.closest('[data-replan]'))sb.hidden=false}}},true);
const holdUI=()=>{const a=document.activeElement;return !!SEL||!!document.querySelector('details.note[open]')||Date.now()-LASTUI<20000||(a&&['SELECT','INPUT','TEXTAREA'].includes(a.tagName))||(view==='settings'&&DIRTY)};
async function load(auto){try{if(document.querySelector('.day.drag'))return;const s=await api('state');if(DAY||PACE||TRV||UNI||MORE||(auto&&holdUI())){S=s;return}if(document.querySelector('.day.drag'))return;const fresh=!S||S.last_run!==s.last_run;S=s;render();if(fresh&&HIST&&view==='hist')loadHist();else if(fresh)HIST=null;clearTimeout(fastT);if(S.job&&S.job.running)fastT=setTimeout(()=>load(true),1000)}catch(e){}}
function authView(kind){
  $('#nav').innerHTML='';$('#sync').innerHTML='';if($('#tabbar'))$('#tabbar').innerHTML='';
  if(kind==='no_password'){$('#main').innerHTML=`<div class="wiz"><div class="brandhead">${LOGO}<h1>periodize my run</h1></div><div class="card c12"><p class="h">App password needed</p><p class="mute">No app password has been set, so Periodize My Run cannot be opened from another device yet.</p><p class="small">On the computer running Periodize My Run, run <code>python web.py --set-password</code> in the app folder, then reload this page.</p></div></div>`;return}
  $('#main').innerHTML=`<div class="wiz"><div class="brandhead">${LOGO}<h1>periodize my run</h1><div class="mute">Enter the app password</div></div><div class="card c12"><div class="row"><input id="pw" type="password" aria-label="App password" autocomplete="current-password" style="flex:1"><button class="btn" id="go">Continue</button></div><p id="e" class="red small"></p></div></div>`;
  const go=async()=>{const r=await fetch('/api/auth',{method:'POST',headers:{'Content-Type':'application/json','X-Requested-With':'periodize'},body:JSON.stringify({password:$('#pw').value})});
    if(r.ok)load();else $('#e').textContent=(await r.json()).error};
  $('#go').onclick=go;$('#pw').onkeydown=e=>{if(e.key==='Enter')go()};
}

function render(){
  if(!S)return;CH={};CHN=0;
  {const v=$('#ver');if(v&&S.version){v.hidden=false;v.textContent='v'+S.version;v.classList.toggle('beta',S.version.includes('-beta'));v.title='You are running version '+S.version+(S.version.includes('-beta')?' (a beta). ':'. ')+'Click for the change log.';
    v.onclick=e=>{e.preventDefault();if(!S.setup_done||!S.setup_seen)return;view='changes';loadChanges();render();scrollTo({top:0})}}}
  if(!S.setup_done||!S.setup_seen){$('#nav').innerHTML='';$('#sync').innerHTML='';if($('#tabbar'))$('#tabbar').innerHTML='';if(S.setup_done&&!S.setup_seen)wiz.step=6;return wizard()}
  const T={plan:'Plan',hist:'History',you:'Fitness',races:'Races & status',settings:'Settings',about:'How it works',changes:'Change log',log:'Log'};
  $('#nav').innerHTML=Object.keys(T).map(v=>`<button class="${v===view?'on':''}" data-v="${v}">${T[v]}</button>`).join('');
  {const on=$('#nav button.on');if(on&&on.scrollIntoView)on.scrollIntoView({inline:'center',block:'nearest'})}
  const go=v=>{MORE=false;DIRTY=false;view=v;if(view==='log')loadLogs();if(view==='about')loadAbout();if(view==='changes')loadChanges();if(view==='hist')loadHist();if(view==='you')loadTrends();render();scrollTo({top:0})};
  $$('#nav button').forEach(b=>b.onclick=()=>go(b.dataset.v));
  {const ic={plan:'<rect x="3.5" y="5" width="17" height="15" rx="3"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',hist:'<path d="M3.5 12a8.5 8.5 0 1 0 2.6-6.1L3.5 8.5"/><path d="M3.5 4v4.5H8M12 8v4.5l3 2"/>',you:'<path d="M3 12h4l2.5-6 4 12 2.5-6H21"/>',races:'<path d="M5 21V4M5 5h13l-2.5 4L18 13H5"/>',settings:'<path d="M4 7h10M18 7h2M4 17h2M10 17h10"/><circle cx="16" cy="7" r="2.2"/><circle cx="8" cy="17" r="2.2"/>',more:'<circle cx="5.5" cy="12" r="1.4"/><circle cx="12" cy="12" r="1.4"/><circle cx="18.5" cy="12" r="1.4"/>'};
   const tb=[['plan','Plan'],['hist','History'],['you','Fitness'],['races','Races'],['settings','Settings'],['more','More']], inMore=['about','changes','log'].includes(view);
   $('#tabbar').innerHTML=tb.map(([v,t])=>`<button data-t="${v}" class="${(v==='more'?(inMore||MORE):(v===view&&!MORE))?'on':''}" aria-label="${t}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ic[v]}</svg>${t}</button>`).join('');
   $$('#tabbar button').forEach(b=>b.onclick=()=>{if(b.dataset.t==='more'){MORE=!MORE;render()}else go(b.dataset.t)});
   window.GO=go}
  const j=S.job;
  $('#sync').innerHTML=j.running?`<span class="dot busy"></span><span class="st-run">${E(j.progress||'Working')}…</span>`
    :`<span class="dot ${j.error||S.stale?'bad':''}"></span>${S.last_run?`<span class="st-full">Synced ${E(S.last_run.slice(5).replace('T',' '))}</span><span class="st-short">${E(S.last_run.slice(5,10)===S.today.slice(5)?S.last_run.slice(11):S.last_run.slice(5,10))}</span>`:'Not synced yet'} <button class="ghost" id="run">Sync</button>`;
  let h='';
  if(j.error&&!j.running)h+=`<div class="alert err">The last sync had a problem: ${E(j.error)}</div>`;
  if(S.stale)h+=`<div class="alert err" role="alert">No successful sync in 7 days, so the plan is running on old data. Check the Log tab, then press Sync.</div>`;
  else if(S.sync_age_h!=null&&S.sync_age_h>=12&&S.setup_done)h+=`<div class="alert" role="status">Your watch last synced ${S.sync_age_h<48?Math.round(S.sync_age_h)+' hours':Math.round(S.sync_age_h/24)+' days'} ago, so recovery and the newest runs are not in today's plan yet. ${j.error?'':'It retries every hour; press Sync to try now.'}</div>`;
  $('#main').innerHTML=h+({plan:planView,hist:histView,you:youView,races:racesView,settings:settingsView,about:aboutView,changes:changesView,log:logView}[view])()+(MORE?moreSheet():'');
  polish();bind();bindCharts();
}

