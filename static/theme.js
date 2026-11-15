/* The colour theme, set before the page is drawn so it never flashes the wrong one. Loaded first, without waiting.
   The choice is kept on this device only: 'light', 'dark', 'black' (darker, for OLED screens and night), or nothing to follow the device. */
function applyTheme(t){const r=document.documentElement;if(t==='light'||t==='dark'||t==='black')r.dataset.theme=t;else delete r.dataset.theme;
  const bg={light:'#f7f7f5',dark:'#0d0f12',black:'#000000'}[t];
  document.querySelectorAll('meta[name=theme-color]').forEach(m=>{if(!m.dataset.auto)m.dataset.auto=m.content;m.content=bg||m.dataset.auto})}
function themeNow(){try{return localStorage.getItem('theme')||'auto'}catch(e){return 'auto'}}
function setTheme(t){try{if(t==='auto')localStorage.removeItem('theme');else localStorage.setItem('theme',t)}catch(e){}applyTheme(t)}
applyTheme(themeNow());
