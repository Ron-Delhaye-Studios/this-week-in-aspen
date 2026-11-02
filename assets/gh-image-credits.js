/* CC plate attribution follows the visible images, including live lead changes. */
(() => {
  const start=()=>{
    const map=document.getElementById('gh-credit-map'),footer=document.querySelector('.gh-footer');if(!map||!footer)return;
    const registry=JSON.parse(map.textContent),base=new URL('../',document.querySelector('script[src$="gh-image-credits.js"]').src);
    const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const record=img=>{const url=new URL(img.currentSrc||img.src,base);return url.origin===base.origin?registry.find(r=>new URL(r.file,base).pathname===url.pathname):null};
    const credit=r=>esc(r.title)+' — '+esc(r.author)+', <a href="'+esc(r.license_url)+'" rel="license">'+esc(r.license)+'</a>';
    function sync(){
      const used=new Set();document.querySelectorAll('img[src]').forEach(img=>{if(!img.closest('[hidden]')&&img.getClientRects().length>0){const r=record(img);if(r)used.add(r.file)}});
      const html=registry.filter(r=>used.has(r.file)).map(credit).join(' · ');
      let node=footer.querySelector('.gh-credits');
      if(!html){node?.remove()}else{if(!node){node=document.createElement('p');node.className='gh-credits';footer.append(node)}const value='Image credits: '+html;if(node.innerHTML!==value)node.innerHTML=value}
      const image=document.querySelector('.gh-cover-frame img'),caption=document.querySelector('.gh-cover-credit');
      if(image&&caption){const r=record(image);if(r){const value='Cover: '+credit(r)+(r.note?'. '+esc(r.note):'');if(caption.innerHTML!==value)caption.innerHTML=value}else{caption.textContent=''}}
    }
    let queued=false;
    new MutationObserver(()=>{if(!queued){queued=true;queueMicrotask(()=>{queued=false;sync()})}}).observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['src','srcset','hidden','style']});
    document.addEventListener('load',e=>{if(e.target.tagName==='IMG')sync()},true);sync();
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();
