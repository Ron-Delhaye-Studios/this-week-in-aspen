/* Advance a cached homepage from the same canonical feed, without inventing an edition. */
(() => {
  const start=()=>{
    const section=document.querySelector('.gh-week');if(!section)return;
    const base=new URL('../',document.querySelector('script[src$="gh-home-live.js"]').src);
    const dateKey=d=>new Intl.DateTimeFormat('en-CA',{timeZone:'America/Denver',year:'numeric',month:'2-digit',day:'2-digit'}).format(d);
    const add=(key,n)=>{const d=new Date(key+'T12:00:00Z');d.setUTCDate(d.getUTCDate()+n);return d.toISOString().slice(0,10)};
    const labels={music:'Music',arts:'Art',outdoors:'Outdoors',family:'Family',comedy:'Comedy',dining:'Dining',dance:'Dance',speakers:'Speakers'};
    const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const fmt=(key,options)=>new Intl.DateTimeFormat('en-US',{timeZone:'America/Denver',...options}).format(new Date(key+'T12:00:00Z'));
    const summary=(e,limit=140)=>{
      const first=(e.blurb||'').trim().replace(/\s+/g,' ').split(/(?<=[.!?])\s+(?=[A-Z0-9])/)[0];
      return first&&first.length<=limit&&!/(…|\.\.\.)$/.test(first)?first:(labels[e.category]||e.category)+' · '+e.venue.split(',')[0];
    };
    const holdExpired=()=>{
      section.querySelector('.gh-week-grid').hidden=true;section.querySelector('.gh-filters').hidden=true;section.querySelector('.gh-sec-meta').textContent='';section.querySelector('.gh-sec-head h2').textContent='Upcoming';
      if(!section.querySelector('[data-gh-recovery]')){const link=document.createElement('a');link.dataset.ghRecovery='';link.href=new URL('events/',base);link.textContent='Events';section.querySelector('.gh-sec-head').append(link)}
    };
    let lastDay='';
    async function refresh(){
      const today=dateKey(new Date());if(today===lastDay)return;
      if(section.dataset.edLive!=='true'&&section.dataset.windowEnd>=today){lastDay=today;return}
      if(section.dataset.windowEnd<today)holdExpired();
      try{
        const response=await fetch(new URL('data/events.json',base));if(!response.ok)throw new Error('Feed unavailable');
        const rows=(await response.json()).filter(e=>dateKey(new Date(e.starts_at))>=today).sort((a,b)=>Date.parse(a.starts_at)-Date.parse(b.starts_at));
        const seen=new Set(),future=rows.filter(e=>!seen.has(e.slug)&&seen.add(e.slug));
        const current=future.filter(e=>dateKey(new Date(e.starts_at))<=add(today,6));
        const from=current.length||!future.length?today:dateKey(new Date(future[0].starts_at)),until=add(from,6),lead=future[0];
        const coming=!current.length&&future.length>0;
        section.querySelector('.gh-week-grid').hidden=false;section.querySelector('.gh-filters').hidden=false;section.querySelector('[data-gh-recovery]')?.remove();
        section.setAttribute('aria-label',coming?'Coming up':'This week in Aspen');
        section.querySelector('.gh-sec-head h2').innerHTML=coming?'Coming <em>up</em>':'This <em>week</em>';
        section.querySelector('.gh-sec-meta').textContent=fmt(from,{weekday:'long',month:'long',day:'2-digit'})+' – '+fmt(until,{weekday:'long',month:'long',day:'2-digit',year:'numeric'});
        section.dataset.edLive='true';section.dataset.windowEnd=until;
        const article=section.querySelector('.gh-lead');article.classList.add('gh-event-lead');
        const oldImage=article.querySelector('img');if(oldImage)oldImage.remove();
        if(lead?.image){const img=document.createElement('img');img.src=new URL(lead.image,base);img.alt=lead.title;img.loading='lazy';img.onerror=()=>img.remove();article.prepend(img)}
        article.querySelector('h3').textContent=lead?.title||'Upcoming';
        article.querySelector('.gh-lead-body>p:not(.gh-lead-k)').textContent=lead?summary(lead):'No upcoming events listed. Check back soon.';
        article.querySelector('.gh-lead-k').textContent=fmt(from,{weekday:'short',month:'short',day:'2-digit'})+' — '+fmt(until,{weekday:'short',month:'short',day:'2-digit'});
        article.querySelector('a').href=new URL(lead?'events/'+lead.slug+'/':'events/',base);
        const selected=future.filter(e=>dateKey(new Date(e.starts_at))<=until).slice(0,5);
        section.querySelector('.gh-rows').innerHTML=selected.map(e=>{
          const key=dateKey(new Date(e.starts_at));return '<a class="gh-row" data-cat="'+esc(e.category)+'" href="'+new URL('events/'+encodeURIComponent(e.slug)+'/',base).href+'"><span class="gh-row-date"><span class="dow">'+fmt(key,{weekday:'short'})+'</span><span class="num">'+fmt(key,{day:'2-digit'})+'</span><span class="mon">'+fmt(key,{month:'short'})+'</span></span><span class="gh-row-info"><h4>'+esc(e.title)+'</h4><p>'+esc(summary(e,110))+'</p></span><span class="gh-row-tag">'+esc(labels[e.category]||e.category)+'</span><span class="gh-row-go" aria-hidden="true">→</span></a>';
        }).join('')||'<p class="gh-list-empty">No upcoming events listed. Check back soon.</p>';
        const filters=section.querySelector('.gh-filters');filters.replaceChildren();
        ['all',...[...new Set(selected.map(e=>e.category))].sort()].forEach((category,i)=>{
          const button=document.createElement('button');button.type='button';button.textContent=category==='all'?'All':labels[category]||category;button.dataset.filter=category;button.classList.toggle('on',i===0);
          button.onclick=()=>{filters.querySelectorAll('button').forEach(b=>b.classList.toggle('on',b===button));section.querySelectorAll('.gh-row').forEach(row=>row.style.display=category==='all'||row.dataset.cat===category?'':'none')};filters.append(button);
        });
        const band=document.querySelector('.gh-band');
        if(band){
          const after=future.filter(e=>dateKey(new Date(e.starts_at))>until).slice(0,2);
          if(!after.length){band.hidden=true}else{
            band.hidden=false;const month=fmt(dateKey(new Date(after[0].starts_at)),{month:'long'});band.querySelector('.gh-band-k').textContent='Coming up — '+month;
            band.querySelector('.gh-band-grid').innerHTML=after.map(e=>'<div class="gh-band-item"><span class="gh-band-when">'+fmt(dateKey(new Date(e.starts_at)),{weekday:'short',month:'short',day:'2-digit'})+'</span><div><h3>'+esc(e.title)+'</h3><p>'+esc(summary(e))+'</p></div></div>').join('')+'<div class="gh-band-item"><span class="gh-band-when">All month</span><div><h3>The Full Calendar</h3><p>Every verified listing for '+month+', in one place. <a href="'+new URL('calendar/',base).href+'">Open it →</a></p></div></div>';
          }
        }
        lastDay=today;
      }catch(_){
        // Do not advertise a finished edition when the cached feed is unavailable.
        if(section.dataset.windowEnd<today)holdExpired();
      }
    }
    refresh();setInterval(refresh,60000);
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();
