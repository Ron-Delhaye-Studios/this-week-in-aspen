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
    let feed=null,selected='all',loadedDay='',pending=false,rendered='',leadRendered='';
    const empty='Explore <a href="'+new URL('picks/',base).href+'">Top Picks</a> or plan with <a href="'+new URL('activities/',base).href+'">Activities</a>.';
    function select(rows,key){
      const eligible=rows.filter(e=>e.verified!==false&&e.end_day>=key).sort((a,b)=>Date.parse(a.starts_at)-Date.parse(b.starts_at));
      const current=eligible.filter(e=>e.start_day>=key&&e.start_day<=W.add(key,6));
      return {rows:current.length?current:eligible.slice(0,5),horizon:!current.length};
    }
    const detail=e=>window.GHCalSync.detailUrl(e);
    const thumb=e=>e.image?'<img class="gh-row-image" src="'+esc(new URL(e.image,base).href)+'" alt="'+esc(e.title)+'" loading="lazy" decoding="async">':'';
    function schema(rows){let node=document.getElementById('gh-home-events');if(!node){node=document.createElement('script');node.id='gh-home-events';node.type='application/ld+json';document.head.append(node)}node.textContent=JSON.stringify({'@context':'https://schema.org','@type':'ItemList',itemListElement:rows.map((e,i)=>({'@type':'ListItem',position:i+1,item:{'@type':'Event',name:e.title,startDate:e.starts_at,endDate:e.ends_at,url:window.GHCalSync.canonicalUrl(e)}}))})}
    function render(){
      const key=W.day(new Date()),range=W.bounds(key),selection=feed?select(feed,key):null,current=selection?.rows;
      const signature=current?JSON.stringify([key,selected,current]):'';
      if(current&&signature===rendered)return;
      const horizon=selection?selection.horizon:section.dataset.horizon==='true';
      section.dataset.horizon=String(horizon);section.setAttribute('aria-label',horizon?'Next on the Calendar':'Coming up');
      section.querySelector('.gh-sec-head h2').innerHTML=horizon?'Next on the <em>Calendar</em>':'Coming <em>up</em>';
      section.querySelector('.gh-sec-meta').textContent=current?.length?fmt(current[0].start_day,{month:'short',day:'numeric'})+' – '+fmt(current[current.length-1].start_day,{month:'short',day:'numeric',year:'numeric'})+' · MT':'Explore the valley';
      section.dataset.windowEnd=range.end;
      if(!current){lead.hidden=true;filters.hidden=true;rowsBox.innerHTML='<p class="gh-list-empty">Finding what’s on…</p>';schema([]);return;}
      const available=W.filters(current);if(!available.some(([value])=>value===selected))selected='all';
      if([...filters.querySelectorAll('button')].map(b=>b.dataset.filter).join(',')!==available.map(([value])=>value).join(','))filters.innerHTML=available.map(([value,label])=>'<button type="button" data-filter="'+value+'" aria-pressed="'+(value===selected)+'"'+(value===selected?' class="on"':'')+'>'+label+'</button>').join('');filters.hidden=!current.length;
      filters.querySelectorAll('button').forEach(b=>{b.setAttribute('aria-pressed',String(b.dataset.filter===selected));b.classList.toggle('on',b.dataset.filter===selected)});
      const first=current[0];lead.hidden=!first;
      const leadSignature=JSON.stringify([key,horizon,first]);
      if(first&&leadSignature!==leadRendered){
        lead.dataset.starts=first.starts_at;
        lead.querySelector('.gh-lead-image-link')?.remove();lead.querySelector('img')?.remove();
        if(first.image){const img=document.createElement('img');img.src=new URL(first.image,base);img.alt=first.title;img.loading='lazy';img.onerror=()=>img.remove();lead.prepend(img)}
        const titleLink=document.createElement('a');titleLink.href=detail(first);titleLink.textContent=first.title;lead.querySelector('h3').replaceChildren(titleLink);lead.querySelector('.gh-lead-body>p:not(.gh-lead-k)').textContent=summary(first);
        lead.querySelector('.gh-lead-k').textContent=fmt(first.start_day,{weekday:'short',month:'short',day:'numeric'})+(first.all_day?' · All day':' · '+new Intl.DateTimeFormat('en-US',{timeZone:'America/Denver',hour:'numeric',minute:'2-digit'}).format(new Date(first.starts_at))+' MT');const action=lead.querySelector('.gh-btn-solid');action.href=detail(first);action.firstChild.textContent='Event details ';
        if(first.image){const img=lead.querySelector('img');const link=document.createElement('a');link.className='gh-lead-image-link';link.href=detail(first);link.setAttribute('aria-label',first.title+' — event details');img.replaceWith(link);link.append(img)}
      }
      leadRendered=leadSignature;
      rendered=signature;
      const seen=new Set(),chosen=current.filter(e=>W.filter(e,selected)&&!seen.has(e.slug||e.id)&&seen.add(e.slug||e.id)).slice(0,5);
      rowsBox.innerHTML=chosen.map(e=>{const key=W.day(new Date(e.starts_at));return '<a class="gh-row'+(e.image?' has-media':'')+'" data-starts="'+esc(e.starts_at)+'" data-free="'+(W.free(e)?'1':'0')+'" data-cat="'+esc(e.category)+'" href="'+esc(detail(e))+'"><span class="gh-row-date"><span class="dow">'+fmt(key,{weekday:'short'})+'</span><span class="num">'+fmt(key,{day:'2-digit'})+'</span><span class="mon">'+fmt(key,{month:'short'})+'</span></span>'+thumb(e)+'<span class="gh-row-info"><h4>'+esc(e.title)+'</h4><p>'+esc(summary(e,110))+'</p></span><span class="gh-row-tag">'+esc(labels[e.category]||e.category)+'</span><span class="gh-row-go" aria-hidden="true">→</span></a>'}).join('')||'<p class="gh-list-empty">'+empty+'</p>';
      schema(chosen);
    }
    async function refresh(){
      render();const key=W.day(new Date());if(pending||loadedDay===key)return;pending=true;
      try{const sync=await window.GHCalSync.load();if(!sync||!Array.isArray(sync.local))throw Error('Invalid feed');feed=sync.local;loadedDay=key;render()}catch(_){feed=null;rendered='';lead.hidden=true;filters.hidden=true;rowsBox.innerHTML='<p class="gh-list-empty">The calendar is temporarily unavailable. Please try again.</p>';section.querySelector('.gh-sec-meta').textContent='';schema([]);}finally{pending=false}
    }
    filters.addEventListener('click',e=>{const button=e.target.closest('button[data-filter]');if(button){selected=button.dataset.filter;render()}});
    refresh();setInterval(refresh,60000);addEventListener('pageshow',refresh);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()});
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();
