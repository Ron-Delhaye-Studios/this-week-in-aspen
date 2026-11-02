/* Town pages are filtered views of the publication feed, never local calendars. */
(() => {
  const start=()=>{
    const box=document.querySelector('.gh-feature-week');if(!box)return;
    const W=window.GHWeek,base=new URL('../',document.querySelector('script[src$="gh-feature-live.js"]').src);
    let loaded='',pending=false,feed=null;
    const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    function render(){
      const day=W.day(new Date());
      if(feed){
        const rows=W.select(feed.filter(e=>[box.dataset.townKey,box.dataset.townName].includes(e.place_key||e.town_key||e.town)),day);
        box.querySelector('ol').innerHTML=rows.map(e=>'<li data-starts="'+esc(e.starts_at)+'"><time datetime="'+esc(e.starts_at)+'">'+new Intl.DateTimeFormat('en-US',{timeZone:'America/Denver',weekday:'short',month:'short',day:'2-digit',hour:'2-digit',minute:'2-digit'}).format(new Date(e.starts_at))+' MT</time><a href="'+new URL('events/'+encodeURIComponent(e.slug)+'/',base).href+'">'+esc(e.title)+'</a></li>').join('');
        const ld=document.getElementById('feature-week-events');
        if(ld)ld.textContent=JSON.stringify({'@context':'https://schema.org','@type':'ItemList',itemListElement:rows.map((e,i)=>({'@type':'ListItem',position:i+1,item:{'@type':'Event',name:e.title,startDate:e.starts_at,url:'https://thegoldenhour.guide/events/'+e.slug+'/'}}))});
      }
      box.querySelectorAll('li[data-starts]').forEach(row=>{row.hidden=!W.matches({starts_at:row.dataset.starts},day)});
      box.querySelector('.gh-feature-week-empty').hidden=!!box.querySelector('li:not([hidden])');
      if(!feed){const ld=document.getElementById('feature-week-events');if(ld){const data=JSON.parse(ld.textContent);data.itemListElement=data.itemListElement.filter(x=>W.matches({starts_at:x.item.startDate},day)).map((x,i)=>({...x,position:i+1}));ld.textContent=JSON.stringify(data)}}
    }
    async function refresh(){render();const day=W.day(new Date());if(loaded===day||pending)return;pending=true;try{const r=await fetch(new URL('data/events.json',base));if(!r.ok)throw Error('Feed unavailable');const data=await r.json();if(!Array.isArray(data))throw Error('Invalid feed');feed=data;loaded=day;render()}catch(_){}finally{pending=false}}
    refresh();setInterval(refresh,60000);addEventListener('pageshow',refresh);
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();
