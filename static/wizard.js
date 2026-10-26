/* The setup wizard. One of the page scripts; see index.html for the order they load in (they share one scope). */
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
    h+=stepper(5)+`<p class="h">Building your plan</p><p style="margin:14px 0"><span class="spin"></span>${E(j.progress||'Starting')}</p><p class="small mute">The first run reads your whole running history and downloads your recent runs at an unhurried pace, so it takes 10 to 30 minutes. You can close this page; it carries on.</p>`;
    if(p)h+=`<div class="stats"><div class="stat"><div class="v num">${p.runs.toLocaleString()}</div><div class="k">runs found</div></div><div class="stat"><div class="v num">${p.first_run.slice(0,4)}</div><div class="k">running since</div></div><div class="stat"><div class="v num">${dU(p.miles)}</div><div class="k">lifetime</div></div></div>`;
    if(j.error)h+=`<div class="alert err" style="margin-top:14px">${E(j.error)}</div><button class="btn" id="retry">Try again</button>`;
  }else if(wiz.step===1){
    h+=stepper(1)+`<p class="h">Welcome</p><p class="small">Periodize My Run builds a running plan from your own running history (Garmin or COROS) and keeps adjusting it from what you do. Setup takes a few minutes of your time, then 10 to 30 minutes of its own.</p>
      <ul class="why"><li><b>It runs on this computer.</b> Your data stays here. Nothing is sent anywhere except your watch's service, the weather services (Open-Meteo and Met Éireann) if you switch heat adjustment on, and a daily version check with GitHub.</li>
      <li><b>No passwords are kept.</b> Your Garmin or COROS password is used once to sign in; only an access token is stored, encrypted.</li>
      <li><b>No AI is used.</b> The plan comes from fixed rules and your data, and every decision is explained.</li>
      <li><b>It is not medical advice.</b> For pain that changes your stride, chest symptoms or illness with fever, stop and see a clinician.</li></ul>
      ${S.remote?'':(S.has_password?'':'<p class="xs mute">To open the app from another device later, set an app password on this computer with <code>python web.py --set-password</code>.</p>')}
      ${termsBox('tbox1')}<p style="margin:12px 0 0"><label class="small"><input type="checkbox" id="wterms"> I have read and accept the terms of use, including that this is not medical advice and that I run at my own risk</label></p>
      ${nav(null,'w1','Get started')}`;
  }else if(wiz.step===2){
    const src=wiz.src||(S.watch&&S.watch.source==='coros'?'coros':'garmin'), ok=src==="coros"?S.watch.coros:S.garmin.connected;
    h+=stepper(2)+`<p class="h">Connect your watch</p><label for="wsw">Which watch do you use?</label><select id="wsw"><option value="garmin" ${src==='garmin'?'selected':''}>Garmin</option><option value="coros" ${src==='coros'?'selected':''}>COROS</option></select>`;
    if(src==='coros'){
      if(ok)h+=`<p>Connected to COROS.</p><p class="xs mute">COROS gives the app your runs. It has no sleep or HRV to share, so sessions are not adjusted day by day, and nothing is sent to your watch.</p>${nav('wb1','w2')}`;
      else h+=`<p class="small mute">Your password goes straight to COROS, once, and is not stored. COROS has no official way for a personal app to sign in, so this uses the web interface its own Training Hub site uses. It reads your runs only and never changes your account. Your region (Europe, USA or China) is found automatically.</p>
        <label for="cem">COROS email</label><input id="cem" type="email" autocomplete="username" style="width:100%"><label for="cpw">COROS password</label><input id="cpw" type="password" autocomplete="current-password" style="width:100%">
        <p style="margin:18px 0 0"><button class="ghost" id="wb1">Back</button> <button class="btn" id="wcl">Connect</button></p>`;
    }else if(S.garmin.connected)h+=`<p>Connected${S.garmin.name?' as <b>'+E(S.garmin.name)+'</b>':''}.</p>${nav('wb1','w2')}`;
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
