/* Terms, updates, the More sheet, removal, How it works, the watch cards, and the log. One of the page scripts; see index.html for the order they load in (they share one scope). */
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
  const vk=v=>{const[c,b]=v.split('-beta.');return[...c.split('.').map(Number),b?0:1,+(b||0)]}, vs=[...new Set([u.base,...(u.installed||[])])].sort((a,b)=>vk(a).reduce((x,y,i)=>x||y-vk(b)[i],0));
  return `<div style="margin-top:12px"><p class="small" style="margin:0"><b>Updates:</b> ${st} ${u.checked?`<span class="mute xs">Checked ${E(u.checked.replace('T',' '))}.</span>`:''}</p>
    <p style="margin:8px 0 0"><button class="ghost" data-upd="check">Check now</button>${u.newer?` <button class="btn" data-upd="install" data-v="${E(u.latest)}">Update to ${E(u.latest)}</button>`:''}</p>
    ${vs.length>1?`<label for="updver">Switch version</label><div class="copyrow"><select id="updver">${vs.map(v=>`<option value="${E(v)}" ${v===u.running?'selected':''}>${E(v)}${v===u.base?' (installed)':''}${v===u.running?' (running now)':''}</option>`).join('')}</select><button class="ghost" id="updgo">Switch</button></div><p class="xs mute">Go back to an earlier version, or forward again. A backup is made first; the app restarts.</p>`:''}
    <label for="updch">Update channel</label><select id="updch"><option value="stable" ${u.channel==='stable'?'selected':''}>Stable (recommended): tested releases only</option><option value="beta" ${u.channel==='beta'?'selected':''}>Beta: early fixes and features, rougher edges</option></select>
    ${u.channel==='beta'?'<p class="xs mute" style="margin:6px 0 0">Betas are tried here before they are released. Your data is backed up before every update, and you can switch back to a release at any time.</p>':''}
    <label class="small" style="display:block;margin-top:8px"><input type="checkbox" id="updchk" checked> Check GitHub for new versions once a day (nothing about you is sent)</label></div>`}
function termsNotice(){if(!S.setup_done||S.terms_ok)return '';
  return `<div class="card c12" id="termsnote" style="margin-bottom:18px"><p class="eyebrow">Terms of use</p><p class="small" style="margin:0">Periodize My Run is a training tool, not medical advice. You run at your own risk, your data and its security are yours to look after, and the app must not be put on the internet. Please read and accept the terms once.</p>
    ${termsBox('tbox2')}<p style="margin:12px 0 0"><label class="small"><input type="checkbox" id="tok2"> I have read and accept the terms of use</label> <button class="btn" id="taccept" style="margin-left:10px">Accept</button></p></div>`}
function moreSheet(){const it=[['about','How it works','The reasoning behind your plan'],['changes','Change log','What is new in version '+S.version],['log','Log','What the app has been doing']];
  return `<div class="ov" id="moreov"><div class="modal sheetm" role="dialog" aria-modal="true" aria-label="More">${it.map(([v,t,d])=>`<button class="morerow" data-go="${v}"><b>${t}</b><span class="mute small">${E(d)}</span></button>`).join('')}<button class="ghost" id="moreno" style="width:100%;margin-top:6px;justify-content:center;text-align:center">Close</button></div></div>`}
function removeCard(){return `<div class="card c12" id="removecard"><p class="eyebrow">Remove Periodize My Run</p>
  <p class="small" style="margin:0">Stops the app, stops it starting by itself and removes its Python environment. Your training data is kept unless you choose to delete it too. You will be asked for the app password.</p>
  ${S.uninstall?'<p style="margin:12px 0 0"><button class="ghost" id="rmopen" style="color:var(--red)">Remove…</button></p>'
    :'<p class="xs mute" style="margin:8px 0 0">Not available on this install. Run the installer once more to turn it on, or use ./uninstall.sh in the app folder.</p>'}</div>`}
function removeModal(){return `<div class="ov" id="rmov"><div class="modal" style="width:min(520px,100%)" role="dialog" aria-modal="true" aria-labelledby="rmt">
  <p class="eyebrow"><span id="rmt">Remove Periodize My Run?</span></p>
  <p class="small">This stops the app and removes it from start-up. The app folder itself is left for you to delete. Workouts already on your watch stay there.</p>
  <label class="small" style="display:block;margin:10px 0"><input type="checkbox" id="rmdata"> Also delete my training data, backups and stored watch login. <b>This cannot be undone.</b></label>
  <label for="rmpw">App password</label><input id="rmpw" type="password" autocomplete="current-password" maxlength="256">
  <p style="margin:14px 0 0"><button class="btn" id="rmgo" style="background:var(--red)">Remove now</button> <button class="ghost" id="rmno">Cancel</button></p></div></div>`}
function aboutCard(){const P=S.project||{}, x=(href,t)=>`<a href="${E(href)}" target="_blank" rel="noopener noreferrer">${t}</a>`;
  return `<div class="card c12" id="aboutcard"><p class="eyebrow">About Periodize My Run</p>
    <p class="small" style="margin:0">Version <b class="num">${E(S.version)}</b> · <a href="#" id="tochanges">What changed</a>${P.url?' · '+x(P.url,'Source code'):''}</p>
    <ul class="clist">
      <li><b>Licence:</b> MIT. Free to use, change and share, with no warranty${P.url?' ('+x(P.url+'/blob/main/LICENSE','read the licence')+')':''}.</li>
      <li><b>Found a problem or have an idea?</b> ${P.url?x(P.url+'/issues/new','Open an issue')+'. Say what you did, what happened and what you expected; the Log tab often helps, but check it for anything personal before pasting.':'See the README.'}</li>
      <li><b>A security problem?</b> Please report it privately, not in a public issue${P.url?': '+x(P.url+'/security/advisories/new','private security report'):''}. See SECURITY.md.</li>
      ${P.support?`<li><b>Like it?</b> ${x(P.support,'Buy me a coffee')} ☕</li>`:''}
    </ul>${updatesBox()}${termsBox('tbox3')}
    <p class="xs mute" style="margin:8px 0 0">Periodize My Run is a training tool, not medical advice; you use it at your own risk. Keep it off the internet: it is for your own computer or home network. It is not affiliated with Garmin or COROS.</p></div>`}
function watchCard(head,chip){const w=S.watch||{source:'garmin'}, opt=(v,t)=>`<option value="${v}" ${w.source===v?'selected':''}>${t}</option>`;
  return `<div class="card c6 conn" id="cwatch">${head('⇄','Where your runs come from',chip(w.connected,E(w.name||'Garmin'),'Not connected',w.source!=='garmin'))}
    <label for="wsrc">Source</label><select id="wsrc">${opt('garmin','Garmin (runs, sleep, HRV, workouts to the watch)')}${opt('fitfolder','FIT files from a folder (any watch, runs only)')}${opt('coros','COROS (runs only)')}</select>
    <div id="wfit" ${w.source==='fitfolder'?'':'hidden'}><p class="small" style="margin:10px 0 4px">Export your runs as .fit files (COROS, Polar, Suunto, Wahoo or any watch) into one folder, or point this at a folder a sync app fills. New files are read at every sync; runs only, so there is no day-by-day easing from sleep or HRV, and workouts are not sent to the watch.</p>
      ${w.local?`<label for="wfolder">Folder on this computer</label><div class="copyrow"><input id="wfolder" style="flex:1;min-width:0" value="${E(w.fit_folder||'')}" placeholder="/Users/you/FIT files"><button class="ghost" id="wfsave">Use this folder</button></div>`:`<p class="xs mute">${w.fit_folder?'Folder: <code>'+E(w.fit_folder)+'</code>. ':''}The folder can only be chosen on the computer Periodize My Run runs on.</p>`}</div>
    ${w.source==='garmin'?'':`<p class="xs mute" style="margin:10px 0 0">Garmin stays connected if it was, but the plan is not sent to it while another source is chosen.</p>`}</div>`}
function corosCard(head,chip){const w=S.watch||{source:'garmin'};
  return `<div class="card c6 conn" id="ccoros">${head('⌚','COROS',chip(w.coros,w.source==='coros'?'In use':'Connected','Not connected',false))}
    <p class="small">${w.coros?'Signed in to COROS.'+(w.source==='coros'?' Your runs come from COROS.':' Choose COROS as the source below to use it.'):'Use a COROS watch instead of Garmin: sign in here and your runs come from COROS.'}</p>
    <ul class="clist"><li>Reads your runs through COROS's unofficial web interface, which COROS can change or block at any time. Your region (Europe, USA or China) is found automatically.</li><li>Runs only: no sleep or HRV, so sessions are not adjusted day by day. Nothing is ever sent to your COROS account or watch.</li></ul>
    ${w.coros?`<p class="cact"><button class="ghost" id="cordis">Disconnect COROS</button></p>`:`<label for="cem">COROS email</label><input id="cem" type="email" style="width:100%" autocomplete="username"><label for="cpw">COROS password</label><input id="cpw" type="password" style="width:100%" autocomplete="current-password">
    <p class="xs mute">Sent once to COROS and never stored; only the access token is kept, encrypted.</p><p class="cact"><button class="btn" id="corgo">Sign in to COROS</button></p>`}</div>`}
function connections(part){const gm=S.garmin, chip=(ok,yes,no,warn)=>`<span class="chip ${ok?'green':warn?'amber':'unknown'}"><i></i>${ok?yes:no}</span>`;
  const head=(icon,name,c)=>`<div class="chead"><span class="cicon" aria-hidden="true">${icon}</span><b>${name}</b><span style="margin-left:auto">${c}</span></div>`;
  const data=`<div class="c12 sechead"><h2>Watch and data</h2><p class="small mute">Where your data comes from and where copies go. Tokens are kept encrypted on this computer; no passwords are stored.</p></div>
  <div class="card c6 conn" id="cgarmin">${head('⌚','Garmin',chip(gm.connected,'Connected','Not connected'))}
    <p class="small">${gm.connected?'Signed in'+(gm.name?' as <b>'+E(gm.name)+'</b>':'')+'.':'Not connected. The plan cannot sync without it.'}</p>
    <ul class="clist"><li>Reads your runs, sleep, HRV, resting heart rate and steps once a day.</li><li>${S.settings.push_enabled?`Sends the next ${S.settings.push_days} days of workouts to your watch, and checks every four hours that they are still there.`:'Sending workouts to your watch is switched off (Training tab).'}</li><li>Your password was used once to sign in and was not stored.</li></ul>
    ${gm.connected&&gm.history?`<p class="xs mute" style="margin:8px 0 0">Everything else Garmin keeps for each day (sleep stages, stress, Body Battery, breathing, blood oxygen, readiness, VO2max and the all-day heart rate) is being saved whole, newest first. ${gm.history.done?`Done: ${gm.history.days.toLocaleString()} days, back to ${E(gm.history.back_to||'')}.`:`${gm.history.days.toLocaleString()} days so far, reading ${E(gm.history.reading||'')}. It carries on by itself and can take days.`}</p>`:''}
    ${gm.connected?'<p class="cact"><button class="ghost" id="gmdis">Disconnect Garmin</button></p><p class="xs mute">To revoke access everywhere, change your Garmin password.</p>':''}</div>
  ${corosCard(head,chip)}
  ${watchCard(head,chip)}
  <div class="card c6 conn" id="ccal">${head('▦','Calendar file',chip(true,'Ready',''))}
    <p class="small">The next sessions as a file for Apple Calendar, Outlook or Google Calendar. Import it by hand; nothing is sent anywhere.</p>
    <p class="cact"><a class="ghost" href="/api/calendar.ics">Download calendar file</a></p></div>
  <div class="card c6 conn" id="cfit">${head('⇩','Workout files (FIT)',chip(true,'Ready',''))}
    <p class="small">The coming days' runs, with their pace targets, as .fit workout files in one zip. Garmin watches load them from the NewFiles folder over USB, and apps that import FIT workouts (intervals.icu, for example, which can pass them on to other watches) can read them. COROS, Suunto and Polar have not been confirmed to import structured workouts from a file. Nothing is sent anywhere.</p>
    <p class="cact"><a class="ghost" href="/api/workouts.zip">Download the next ${S.settings.push_days} days</a></p></div>`;
  const env=`<div class="card c12 conn" id="cheat">${head('☀','Weather (Open-Meteo and Met Éireann)',chip(S.heat&&S.heat.on,'On','Off'))}
    <p class="small">Records the weather each run was done in (temperature, humidity, wind and rain), shows each coming day's forecast with the best hour to start between sunrise and sunset, judges your fitness on what each run was worth in neutral weather, eases fast paces on hot, humid days and in a strong wind, turns a run into an easy one for thunder, ice, heavy snow, damaging wind or an Orange or Red Met Éireann warning, and shows the race-day forecast for your goal race once it is within 16 days. The weather comes from Open-Meteo (free, no account). The only things sent are rough locations, rounded to about 10 km, of where your runs started, and their dates. In Ireland it also reads Met Éireann's public warnings feed (www.met.ie, free, no account): nothing about you is sent, because the feed is the same for everyone and your county is worked out here. Warnings are shown exactly as Met Éireann issues them, with the credit its licence asks for. Off unless you switch it on.</p>
    <label for="heatsw">Track the weather and adjust for it</label>${yn('heatsw',S.heat&&S.heat.on)}
    <p class="xs" style="margin:8px 0 0"><a href="#" data-gohours>Set the hours you can run</a> <span class="mute">(the best time of day is chosen inside them)</span></p>
    ${S.heat&&S.heat.on&&!S.heat.located?'<p class="xs mute" style="margin:6px 0 0">Waiting for the first forecast: it is read at the next sync, once a run with GPS is found.</p>':''}</div>
  <div class="card c12 conn" id="cmaps">${head('◎','Maps (OpenStreetMap)',chip(S.map_tiles,'Real maps on','Outline only'))}
    <p class="small">Shows each run on a real map. Map images are loaded from OpenStreetMap when you open a run, so its servers see which area you are looking at. No account, name or run data is sent. Switched off, routes are drawn as an outline and nothing is loaded from outside.</p>
    <label for="mapsw">Show runs on a real map</label>${yn('mapsw',S.map_tiles)}</div>`;
  return part==='env'?env:data}
function aboutView(){if(!ABOUT)return `<div class="grid"><div class="card c12 loading">${skel(4)}</div></div>`;
  return '<div class="grid">'+ABOUT.map(s=>`<div class="card c6"><p class="eyebrow">${E(s.title)}</p><ul class="why" style="margin:0">${s.items.map(i=>`<li>${E(i)}</li>`).join('')}</ul></div>`).join('')+refsCard()+'</div>'}
function logView(){return `<div class="grid"><div class="card c12"><p class="eyebrow">Activity log <button class="ghost" id="lr">Refresh</button></p><pre tabindex="0" role="region" aria-label="Activity log">${E(logs.join(''))||'Loading…'}</pre></div></div>`}
