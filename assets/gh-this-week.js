/* WO21: refresh a cached This Week page from the unchanged publication feed. */
(() => {
  const start=()=>{
    if(document.body.dataset.page!=='upcoming/index.html')return;
    const W=window.GHWeek,base=new URL('../',document.querySelector('script[src$="gh-this-week.js"]').src);
    const grid=document.querySelector('.gh-event-grid'),chips=document.querySelector('.gh-filters'),empty=document.querySelector('.gh-list-empty');
    const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const fmt=(d,opts)=>new Intl.DateTimeFormat('en-US',{timeZone:'America/Denver',...opts}).format(new Date(d));
    let rows=null,selected='all',loadedDay='',pending=false,rendered='';
    function card(e){
      const when=fmt(e.starts_at,{weekday:'short',month:'short',day:'2-digit',hour:'2-digit',minute:'2-digit'})+' MT';
      const title='<p class="gh-card-kicker">'+esc(e.category)+'</p><time datetime="'+esc(e.starts_at)+'">'+esc(when)+'</time><h2><a class="gh-card-link" href="'+new URL('events/'+encodeURIComponent(e.slug)+'/',base).href+'">'+esc(e.title)+'</a></h2>';
      const image=e.image?'<figure class="gh-card-media"><img src="'+esc(new URL(e.image,base).href)+'" alt="'+esc(e.title)+' — official event imagery" loading="lazy" decoding="async"></figure>':'';
      const copy=e.title+' — '+e.venue+'\n'+when+'\n'+(e.blurb||'')+'\n'+e.url;
      return '<article id="ev-'+esc(e.id)+'" class="gh-event-card gh-card '+(image?'has-media':'gh-typographic')+'" data-starts="'+esc(e.starts_at)+'" data-slug="'+esc(e.slug)+'" data-cat="'+esc(e.category)+'" data-free="'+(W.free(e)?'1':'0')+'">'+(image||'<header class="gh-type-media">'+title+'</header>')+'<div class="gh-card-body">'+(image?title:'')+'<p class="gh-card-venue">'+esc(e.venue)+'</p><details class="gh-card-details"><summary>Details &amp; booking</summary><dl><div><dt>Price</dt><dd>'+esc(e.price_info||'Confirm with venue')+'</dd></div><div><dt>Ages</dt><dd>'+esc(e.age_policy||'Confirm with venue')+'</dd></div></dl><p>'+esc(e.blurb)+'</p><p>'+esc(e.fit_note)+'</p></details><div class="gh-card-actions"><a class="btn" href="'+esc(e.url)+'" rel="noopener">Official source ↗</a><button type="button" class="copybtn gh-copy" data-copy="'+esc(copy)+'">Copy details</button></div></div></article>';
    }
    function render(){
      const key=W.day(new Date()),range=W.bounds(key);
      document.querySelector('.gh-week-range').textContent=fmt(range.start+'T12:00:00Z',{month:'short',day:'2-digit'})+' – '+fmt(range.end+'T12:00:00Z',{month:'short',day:'2-digit',year:'numeric'})+' · MT';
      if(rows){
        const current=W.select(rows,key),available=W.filters(current);
        if(!available.some(([value])=>value===selected))selected='all';
        const signature=JSON.stringify([key,current]);
        // Keep open details, copy feedback and keyboard focus on unchanged data.
        if(signature!==rendered){
          chips.innerHTML=available.map(([value,label])=>'<button type="button" data-filter="'+value+'" aria-pressed="'+(value===selected)+'">'+label+'</button>').join('');
          grid.innerHTML=current.map(card).join('');
          const ld=document.getElementById('gh-event-list');
          if(ld)ld.textContent=JSON.stringify({'@context':'https://schema.org','@type':'ItemList',name:'This Week — The Golden Hour',itemListElement:current.map((e,i)=>({'@type':'ListItem',position:i+1,item:{'@type':'Event',name:e.title,startDate:e.starts_at,url:'https://thegoldenhour.guide/events/'+e.slug+'/'}}))});
          rendered=signature;
        }
        chips.hidden=!current.length;
        chips.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.filter===selected)));
      }
      const eligible=[...grid.children].filter(c=>W.matches({starts_at:c.dataset.starts},key));
      if(!rows){
        const available=eligible.length?['all',...['music','arts','free'].filter(f=>eligible.some(c=>f==='free'?c.dataset.free==='1':c.dataset.cat===f))]:[];
        if(!available.includes(selected))selected='all';
        chips.querySelectorAll('button').forEach(b=>{b.hidden=!available.includes(b.dataset.filter);b.setAttribute('aria-pressed',String(b.dataset.filter===selected))});
        chips.hidden=!available.length;
        const ld=document.getElementById('gh-event-list');
        if(ld){const data=JSON.parse(ld.textContent);data.itemListElement=data.itemListElement.filter(x=>W.matches({starts_at:x.item.startDate},key)).map((x,i)=>({...x,position:i+1}));ld.textContent=JSON.stringify(data)}
      }
      [...grid.children].forEach(c=>{c.hidden=!eligible.includes(c)||!(selected==='all'||(selected==='free'?c.dataset.free==='1':c.dataset.cat===selected))});
      empty.hidden=eligible.some(c=>!c.hidden);
    }
    async function refresh(){
      render();const key=W.day(new Date());if(pending||loadedDay===key)return;
      pending=true;
      try{const r=await fetch(new URL('data/events.json',base));if(!r.ok)throw Error('Feed unavailable');const data=await r.json();if(!Array.isArray(data))throw Error('Invalid feed');rows=data;loadedDay=key;render()}catch(_){/* Preserve only still-eligible server-rendered listings. */}finally{pending=false}
    }
    chips.addEventListener('click',e=>{const b=e.target.closest('button[data-filter]');if(b){selected=b.dataset.filter;render()}});
    refresh();setInterval(refresh,60000);addEventListener('pageshow',refresh);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()});
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();
