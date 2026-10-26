/* Starts the page. Loaded last. One of the page scripts; see index.html for the order they load in (they share one scope). */
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&(SEL||DAY||PACE||TRV)){SEL=null;DAY=null;PACE=null;TRV=null;render()}});
load();
setInterval(()=>{const a=document.activeElement;if(a&&['INPUT','SELECT'].includes(a.tagName))return;if(document.querySelector('details[open]'))return;if(document.querySelector('.day.drag'))return;load(true)},6000);
