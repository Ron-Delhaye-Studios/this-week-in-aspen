/* Historical language follows the approved Denver day rule on an open page. */
(() => {
  const main=document.querySelector('.gh-sync-detail[data-end-day]');
  if(!main)return;
  function refresh(){
    const past=main.dataset.endDay<window.GHEventPolicy.day(new Date());
    main.querySelector('.gh-card-kicker').textContent=past?'Past event':'Event details';
    let label=main.querySelector('.gh-sync-past');
    if(past&&!label){label=document.createElement('p');label.className='gh-sync-past';main.querySelector('h1').after(label)}
    if(label){label.hidden=!past;label.textContent='This event took place on '+main.dataset.when+'. See This Week for current plans.'}
    const ld=document.querySelector('#gh-sync-event');
    if(ld){const data=JSON.parse(ld.textContent);data.description=String(data.description||'').replace(/^Past event\. /,'');if(past)data.description='Past event. '+data.description;ld.textContent=JSON.stringify(data)}
  }
  refresh();setInterval(refresh,60000);addEventListener('pageshow',refresh);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()});
})();
