/* No replacement imagery or invented copy: failed art becomes the type composition. */
(() => {
  const fallback = image => {
    const card = image.closest('.gh-event-card');
    const hero = image.closest('.ev-hero');
    if (card) {
      image.closest('figure')?.remove();
      card.classList.remove('has-media'); card.classList.add('gh-typographic');
      const body=card.querySelector('.gh-card-body');
      if(body&&!card.querySelector('.gh-type-media')){
        const header=document.createElement('header');header.className='gh-type-media';
        body.querySelectorAll(':scope > .gh-card-kicker,:scope > time,:scope > h2').forEach(el=>header.append(el));
        card.prepend(header);
      }
    } else if (hero) {
      hero.hidden=true;
      document.querySelector('.gh-event-title-block')?.classList.add('gh-media-failed');
    }
  };
  document.addEventListener('error', e=>{if(e.target instanceof HTMLImageElement)fallback(e.target)},true);
  document.addEventListener('DOMContentLoaded',()=>document.querySelectorAll('.gh-event-card img,.ev-hero img').forEach(img=>{if(img.complete&&!img.naturalWidth)fallback(img)}));
})();
