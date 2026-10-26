/* The Settings page. One of the page scripts; see index.html for the order they load in (they share one scope). */
/* Arrow keys, Home and End move between the tabs of a row, and only the selected tab is in the tab order (the pattern screen readers expect). */
function tabKeys(list,activate){if(!list||list.dataset.keys)return;list.dataset.keys='1';
  list.addEventListener('keydown',e=>{const tabs=[...list.querySelectorAll('[role=tab]')],i=tabs.indexOf(document.activeElement);if(i<0)return;
    const to={ArrowRight:(i+1)%tabs.length,ArrowLeft:(i-1+tabs.length)%tabs.length,Home:0,End:tabs.length-1}[e.key];
    if(to===undefined)return;e.preventDefault();tabs[to].focus();activate(tabs[to])})}
function rove(list){list.querySelectorAll('[role=tab]').forEach(b=>b.tabIndex=b.getAttribute('aria-selected')==='true'?0:-1)}
let STAB=(()=>{try{return localStorage.getItem('stab')||'train'}catch(e){return 'train'}})();
const STABS=[['train','Training'],['watch','Watch and data'],['env','Weather and maps'],['backup','Backups'],['about','About']];
function setStab(t){STAB=t;try{localStorage.setItem('stab',t)}catch(e){}
  $$('[data-p]').forEach(x=>x.hidden=x.dataset.p!==t);$$('[data-stab]').forEach(b=>{const on=b.dataset.stab===t;b.classList.toggle('on',on);b.setAttribute('aria-selected',on?'true':'false')});const l=$('.stabs[aria-label="Settings sections"]');if(l)rove(l)}
function statusStrip(){const gm=S.garmin,w=S.watch||{source:'garmin'},chip=(ok,t)=>`<span class="chip ${ok?'green':'unknown'}"><i></i>${t}</span>`;
  const src=w.source==='garmin'?chip(gm.connected,gm.connected?'Garmin connected':'Garmin not connected'):chip(w.connected,E(w.name||'Watch')+(w.connected?' connected':' not connected'));
  return `<div class="sstrip">${src}${chip(S.settings.push_enabled&&w.source==='garmin','Workouts '+(S.settings.push_enabled&&w.source==='garmin'?'sent to the watch':'not sent to the watch'))}${chip(S.heat&&S.heat.on,'Weather '+(S.heat&&S.heat.on?'on':'off'))}${chip(S.has_password,'App password '+(S.has_password?'set':'not set'))}</div>`}
function settingsView(){const s=S.settings;
  const tabs=`<div class="stabs" role="tablist" aria-label="Settings sections">${STABS.map(([k,t])=>`<button role="tab" id="stab-${k}" aria-controls="sp-${k}" tabindex="${STAB===k?0:-1}" class="${STAB===k?'on':''}" data-stab="${k}" aria-selected="${STAB===k}">${t}</button>`).join('')}</div>`;
  const P=(k,html)=>`<div class="grid sgrid" id="sp-${k}" role="tabpanel" aria-labelledby="stab-${k}" data-p="${k}" ${STAB===k?'':'hidden'}>${html}</div>`;
  const train=`<div class="card c12" data-replan><p class="eyebrow">How you train</p>${prefs(s)}${windowFields()}</div>
  <div class="card c12" data-replan><p class="eyebrow">Advanced</p><p class="xs mute" style="margin:0">Leave these alone unless you know you need them: each one starts from your own history.</p>
   <details class="adv"><summary>Show advanced settings</summary><div class="fgrid">
    <div><label for="hrmax">Maximum heart rate</label><input id="hrmax" type="number" value="${s.hrmax||''}" placeholder="Auto: ${S.profile.hrmax_observed||'observed'}"></div>
    <div><label for="peak">Peak week in miles</label><input id="peak" type="number" value="${s.peak_miles_override||''}" placeholder="Auto: ${S.limits.peak_miles}, from your history"></div>
    <div><label for="volume_boost">Extra volume in build weeks</label><select id="volume_boost">${[0,0.05,0.1,0.15].map(n=>opt(n,n?'+'+Math.round(n*100)+'%':'Off (0%)',s.volume_boost||0)).join('')}</select><p class="xs mute" style="margin:6px 0 0">Adds miles to build weeks after the usual 20% rise limit. Beyond what the research supports: ease it back if you are getting niggles or ill.</p></div>
    <div><label for="forecast_completion">Plan completion assumed in the forecast</label><select id="forecast_completion">${opt('','Auto: from my history and this plan',s.forecast_completion?Math.round(s.forecast_completion*100):'')}${[70,75,80,85,90,95,100].map(n=>opt(n,n+'%',s.forecast_completion?Math.round(s.forecast_completion*100):'')).join('')}</select></div>
    <div><label for="aero_test_weeks">Aerobic test (how often)</label><select id="aero_test_weeks">${opt(0,'Off',s.aero_test?s.aero_test_weeks:0)}${[4,5,6,8].map(n=>opt(n,'Every '+n+' weeks',s.aero_test?s.aero_test_weeks:0)).join('')}</select></div>
    <div><label for="aero_format">Aerobic test (format)</label><select id="aero_format">${opt('short','Short: about 6 miles',s.aero_format)}${opt('original','Long: about 10 miles, with rests',s.aero_format)}</select></div>
    <div><label for="aero_runs">Aerobic runs by heart rate</label>${yn('aero_runs',s.aero_runs)}</div>
    <div><label for="apply_learned">Let the learned taper and miles-or-hard-running patterns change the plan</label>${yn('apply_learned',s.apply_learned)}</div>
    <div><label for="weeks_ahead">Provisional weeks shown ahead</label><select id="weeks_ahead">${[1,2,3,4,5,6,8,10,13,16].map(n=>opt(n,n+(n===13?' (about 3 months)':''),s.weeks_ahead)).join('')}</select></div>
    <div><label for="push_days">Days kept on the watch</label><select id="push_days">${[7,14,21].map(n=>opt(n,n,s.push_days)).join('')}</select></div>
    <div><label for="notify">Daily message address (optional)</label><input id="notify" style="width:100%" value="${E(s.notify_url||'')}" placeholder="https://ntfy.sh/your-private-topic"><p class="xs mute" style="margin:6px 0 0">A morning message with the day's session. Save first, then send a test.</p><p style="margin:8px 0 0"><button class="ghost" id="ntest" ${S.notify_set?'':'disabled'}>Send a test message</button></p></div></div></details>
    <div class="row" style="align-items:center;margin-top:18px;border-top:1px solid var(--line);padding-top:16px"><button class="btn" id="ssave">Save and replan</button><span class="xs mute">Applies to How you train and Advanced. Switches and choices elsewhere save as you set them.</span></div></div>
  <div class="card c12" id="youcard"><p class="eyebrow">About you</p><p class="xs mute" style="margin-top:0">Used only for age grading and fuelling. Read from Garmin once; clear them to stop age grading.</p>
    <div class="fgrid"><div><label for="ysex">Sex (for age-grade standards, race pacing and injury advice)</label><select id="ysex">${opt('','Not set',S.about_you.sex||'')}${opt('F','Female',S.about_you.sex||'')}${opt('M','Male',S.about_you.sex||'')}</select></div>
    <div><label for="ydob">Date of birth</label><input id="ydob" type="date" value="${E(S.about_you.birth_date||'')}"></div>
    <div><label for="ygel">Carbohydrate in one of your gels (g)</label><input id="ygel" type="number" min="10" max="60" value="${S.about_you.gel_carbs_g}"></div></div>
    <p style="margin:12px 0 0"><button class="ghost" id="ysave">Save</button></p></div>`;
  const backup=`<div class="card c12"><p class="eyebrow">Backups</p><p class="xs mute" style="margin-top:0">Made every night and thinned as they age: daily for 7 days, weekly for 4 weeks, monthly for 3 months. Restoring saves the current state first, so it can be undone.</p>
    <div class="fgrid"><div><label for="abk">Automatic backups</label>${yn('abk',S.auto_backup)}</div>
    <div><label for="bsel">Backup</label><select id="bsel">${S.backups.map(b=>`<option value="${E(b.name)}" data-part="local">${E(b.made.replace('T',' '))} (${b.size_kb} KB)</option>`).join('')||'<option value="">None yet</option>'}</select></div>
    <div><label for="bwhat">What to restore</label><select id="bwhat"><option value="full">Everything</option><option value="config">Settings and races only</option><option value="plan">The plan only</option></select></div></div>
    <p class="xs mute">For a copy off this computer, download a backup below, or see How it works for a daily copy into a cloud folder.</p>
    <p style="margin:12px 0 0"><button class="ghost" id="bnow">Back up now</button> <button class="ghost" id="bres">Restore</button> <a class="ghost" href="/api/export">Download backup</a></p></div>`;
  return `${statusStrip()}${tabs}
  ${P('train',train)}${P('watch',connections('data'))}${P('env',connections('env'))}${P('backup',backup)}${P('about',aboutCard()+removeCard())}
  <div class="savebar" id="savebar" hidden><span>You have unsaved changes to how you train.</span><button class="btn" id="ssave2">Save and replan</button></div>${UNI&&view==='settings'?removeModal():''}`}
