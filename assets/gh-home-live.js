/* Homepage: current week first; explicitly labeled next-five calendar fallback. */
(() => {
  const start=()=>{
    const section=document.querySelector('.gh-week');if(!section)return;
    const W=window.GHWeek,base=new URL('../',document.querySelector('script[src$="gh-home-live.js"]').src);
    const labels={music:'Music',arts:'Art',outdoors:'Outdoors',family:'Family',comedy:'Comedy',dining:'Dining',dance:'Dance',speakers:'Speakers'};
    const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const fmt=(key,options)=>new Intl.DateTimeFormat('en-US',{timeZone:'America/Denver',...options}).format(new Date(key+'T12:00:00Z'));
    const summary=(e,limit=140)=>{const first=(e.blurb||'').trim().replace(/\s+/g,' ').split(/(?<=[.!?])\s+(?=[A-Z0-9])/)[0];return first&&first.length<=limit&&!/(…|\.\.\.)$/.test(first)?first:(labels[e.category]||e.category)+' · '+e.venue.split(',')[0]};
    const filters=section.querySelector('.gh-filters'),lead=section.querySelector('.gh-lead'),rowsBox=section.querySelector('.gh-rows');
    let feed=null,selected='all',loadedDay='',pending=false;
    const empty='Explore <a href="'+new URL('picks/',base).href+'">Top Picks</a> or plan with <a href="'+new URL('activities/',base).href+'">Activities</a>.';
    function render(){
      const key=W.day(new Date()),range=W.bounds(key),selection=feed?W.coming(feed,key):null,current=selection?.rows;
      const horizon=selection?selection.horizon:section.dataset.horizon==='true';
      section.dataset.horizon=String(horizon);section.setAttribute('aria-label',horizon?'Next on the Calendar':'Coming up');
      section.querySelector('.gh-sec-head h2').innerHTML=horizon?'Next on the <em>Calendar</em>':'Coming <em>up</em>';
      section.querySelector('.gh-sec-meta').textContent=horizon?(current?.length?'Next five verified happenings':'Explore the valley'):fmt(range.start,{weekday:'long',month:'long',day:'2-digit'})+' – '+fmt(range.end,{weekday:'long',month:'long',day:'2-digit',year:'numeric'});
      section.dataset.windowEnd=range.end;
      if(!current){
        const existing=[...section.querySelectorAll('.gh-row')],eligible=existing.filter(row=>(horizon?W.horizonMatches:W.matches)({starts_at:row.dataset.starts},key));
        const available=eligible.length?['all',...['music','arts','free'].filter(f=>eligible.some(row=>f==='free'?row.dataset.free==='1':row.dataset.cat===f))]:[];
        if(!available.includes(selected))selected='all';
        filters.querySelectorAll('button').forEach(b=>{b.hidden=!available.includes(b.dataset.filter);b.setAttribute('aria-pressed',String(b.dataset.filter===selected));b.classList.toggle('on',b.dataset.filter===selected)});
        filters.hidden=!available.length;
        existing.forEach(row=>{row.hidden=!eligible.includes(row)||!(selected==='all'||(selected==='free'?row.dataset.free==='1':row.dataset.cat===selected))});
        lead.hidden=!(horizon?W.horizonMatches:W.matches)({starts_at:lead.dataset.starts},key);
        if(horizon&&eligible.length)section.querySelector('.gh-sec-meta').textContent='Next five verified happenings';
        let notice=rowsBox.querySelector('.gh-list-empty');
        if(!notice){notice=document.createElement('p');notice.className='gh-list-empty';notice.innerHTML=empty;rowsBox.append(notice)}
        notice.hidden=eligible.length>0;
        return;
      }
      const available=W.filters(current);if(!available.some(([value])=>value===selected))selected='all';
      filters.innerHTML=available.map(([value,label])=>'<button type="button" data-filter="'+value+'" aria-pressed="'+(value===selected)+'"'+(value===selected?' class="on"':'')+'>'+label+'</button>').join('');filters.hidden=!current.length;
      const first=current[0];lead.hidden=!first;
      if(first){
        lead.dataset.starts=first.starts_at;
        lead.querySelector('img')?.remove();
        if(first.image){const img=document.createElement('img');img.src=new URL(first.image,base);img.alt=first.title;img.loading='lazy';img.onerror=()=>img.remove();lead.prepend(img)}
        lead.querySelector('h3').textContent=first.title;lead.querySelector('.gh-lead-body>p:not(.gh-lead-k)').textContent=summary(first);
        lead.querySelector('.gh-lead-k').textContent=horizon?'Next on the Calendar':fmt(range.start,{weekday:'short',month:'short',day:'2-digit'})+' — '+fmt(range.end,{weekday:'short',month:'short',day:'2-digit'});lead.querySelector('a').href=new URL('events/'+first.slug+'/',base);
      }
      const seen=new Set(),chosen=current.filter(e=>W.filter(e,selected)&&!seen.has(e.slug)&&seen.add(e.slug)).slice(0,5);
      rowsBox.innerHTML=chosen.map(e=>{const key=W.day(new Date(e.starts_at));return '<a class="gh-row" data-starts="'+esc(e.starts_at)+'" data-free="'+(W.free(e)?'1':'0')+'" data-cat="'+esc(e.category)+'" href="'+new URL('events/'+encodeURIComponent(e.slug)+'/',base).href+'"><span class="gh-row-date"><span class="dow">'+fmt(key,{weekday:'short'})+'</span><span class="num">'+fmt(key,{day:'2-digit'})+'</span><span class="mon">'+fmt(key,{month:'short'})+'</span></span><span class="gh-row-info"><h4>'+esc(e.title)+'</h4><p>'+esc(summary(e,110))+'</p></span><span class="gh-row-tag">'+esc(labels[e.category]||e.category)+'</span><span class="gh-row-go" aria-hidden="true">→</span></a>'}).join('')||'<p class="gh-list-empty">'+empty+'</p>';
    }
    async function refresh(){
      render();const key=W.day(new Date());if(pending||loadedDay===key)return;pending=true;
      try{const r=await fetch(new URL('data/events.json',base));if(!r.ok)throw Error('Feed unavailable');const data=await r.json();if(!Array.isArray(data))throw Error('Invalid feed');feed=data;loadedDay=key;render()}catch(_){/* Preserve the labeled server horizon offline; expired cards remain hidden. */}finally{pending=false}
    }
    filters.addEventListener('click',e=>{const button=e.target.closest('button[data-filter]');if(button){selected=button.dataset.filter;render()}});
    refresh();setInterval(refresh,60000);addEventListener('pageshow',refresh);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()});
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();
