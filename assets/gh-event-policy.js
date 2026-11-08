/* Shared Denver calendar-day lifecycle. No scoring or inferred editorial bands. */
(function (root) {
  'use strict';
  const day = value => {
    if (/^\d{4}-\d{2}-\d{2}$/.test(String(value))) return String(value);
    const date = new Date(value);
    if (!Number.isFinite(+date)) throw Error('Invalid event date');
    const p = Object.fromEntries(new Intl.DateTimeFormat('en-US', {timeZone:'America/Denver',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(date).map(x=>[x.type,x.value]));
    return `${p.year}-${p.month}-${p.day}`;
  };
  const add = (key,n) => {const d=new Date(key+'T12:00:00Z');d.setUTCDate(d.getUTCDate()+n);return d.toISOString().slice(0,10)};
  const endDay = e => {
    if (e.end_day) return e.end_day;
    let end=day(e.end || e.ends_at || e.start || e.starts_at);
    const start=day(e.start || e.starts_at);
    if(e.all_day && end>start) end=add(end,-1);
    return end;
  };
  const compareWithinDay = (a,b) => (a.band==='FEATURED'?0:1)-(b.band==='FEATURED'?0:1)
    || Date.parse(a.starts_at || a.start)-Date.parse(b.starts_at || b.start)
    || String(a.id).localeCompare(String(b.id));
  const compare = (a,b) => day(a.start_day || a.start || a.starts_at).localeCompare(day(b.start_day || b.start || b.starts_at)) || compareWithinDay(a,b);
  const eligible = (e,today=day(new Date())) => endDay(e)>=today;
  const routine = e => {
    if(['routine-worship','regular-class','standing-hours'].includes(e.event_kind)) return true;
    const title=String(e.title || '');
    if(/christmas|holiday|festival|candlelight|lessons\s*(?:and|&)\s*carols/i.test(title)) return false;
    return /^(?:Sunday\s+(?:Mass|Worship)|(?:Daily|Weekly|Regular|Routine)\s+(?:Worship|Mass|Service|Class)|Standing hours)\b/i.test(title);
  };
  const verified = e => e.verified===true && !routine(e) && ['aurelian-local','aurelian-regional'].includes(e.source);
  const api={day,add,endDay,compare,compareWithinDay,eligible,routine,verified};
  root.GHEventPolicy=api;
  if(typeof module!=='undefined') module.exports=api;
})(typeof window==='undefined'?globalThis:window);
