/* WO21: shared Saturday–Friday presentation window, always in Denver. */
(() => {
  const day = date => {
    const p = Object.fromEntries(new Intl.DateTimeFormat('en-US', {timeZone:'America/Denver',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(date).map(x=>[x.type,x.value]));
    return `${p.year}-${p.month}-${p.day}`;
  };
  const add = (key, n) => { const d = new Date(key+'T12:00:00Z'); d.setUTCDate(d.getUTCDate()+n); return d.toISOString().slice(0,10); };
  const bounds = key => { const start=add(key,-((new Date(key+'T12:00:00Z').getUTCDay()+1)%7)); return {start,end:add(start,6)}; };
  const verified = e => ('verified' in e ? e.verified : true) === true && ['approved','verified','published'].includes(('status' in e ? e.status : 'approved')) && ['CONFIRMED-2026','CONFIRMED','verified'].includes(('confidence' in e ? e.confidence : 'CONFIRMED-2026'));
  const free = e => /\bfree\b|^\$?0(?:\D|$)/i.test(e.price_info || '');
  const matches = (e,key) => Number.isFinite(Date.parse(e.starts_at)) && verified(e) && day(new Date(e.starts_at))>=key && day(new Date(e.starts_at))<=bounds(key).end;
  const select = (rows,key) => rows.filter(e=>matches(e,key)).sort((a,b)=>Date.parse(a.starts_at)-Date.parse(b.starts_at));
  const filter = (e,key) => key==='all' || (key==='free' ? free(e) : e.category===key);
  const filters = rows => [['all','All'],['music','Music'],['arts','Art'],['free','Free']].filter(([key])=>rows.some(e=>filter(e,key)));
  window.GHWeek = {day,add,bounds,verified,free,matches,select,filter,filters};
  // This new URL bypasses an older worker's cached theme/home scripts. Once
  // the upgraded worker claims this already-controlled page, load its assets.
  if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
    navigator.serviceWorker.addEventListener('controllerchange', () => location.reload(), {once:true});
  }
})();
