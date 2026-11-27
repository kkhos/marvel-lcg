(() => {
const touch=/Android|iPhone|iPad/i.test(navigator.userAgent)||matchMedia('(pointer:coarse)').matches;
if(!touch)return;
document.documentElement.classList.add('deck-touch');
window.MarvelDeckTouch={
  bindPreview(card,open){
    let start=null, lastTouch=0;
    card.addEventListener('pointerdown',e=>{
      if(e.pointerType!=='touch'||!e.isPrimary||e.target.closest('button'))return;
      start={id:e.pointerId,x:e.clientX,y:e.clientY,time:performance.now()};
    });
    card.addEventListener('pointermove',e=>{
      if(start&&start.id===e.pointerId&&Math.hypot(e.clientX-start.x,e.clientY-start.y)>12)start=null;
    });
    card.addEventListener('pointercancel',()=>{start=null;});
    card.addEventListener('pointerup',e=>{
      const p=start;start=null;
      if(!p||p.id!==e.pointerId||e.target.closest('button')||performance.now()-p.time>650||Math.hypot(e.clientX-p.x,e.clientY-p.y)>12)return;
      lastTouch=performance.now();e.preventDefault();e.stopPropagation();open();
    });
    card.addEventListener('click',e=>{
      if(!e.target.closest('button')&&lastTouch&&performance.now()-lastTouch<650){e.preventDefault();e.stopImmediatePropagation();}
    },true);
    card.addEventListener('contextmenu',e=>{if(e.pointerType==='touch'||(e.sourceCapabilities&&e.sourceCapabilities.firesTouchEvents)){e.preventDefault();e.stopImmediatePropagation();}},true);
  },
  attach(card,actions){
  const controls=document.createElement('div');controls.className='deck-card-controls';
  for(const [symbol,label,run] of actions){const b=document.createElement('button');b.type='button';b.textContent=symbol;b.title=label;b.setAttribute('aria-label',label);b.addEventListener('click',e=>{e.stopPropagation();e.preventDefault();run();});b.addEventListener('pointerdown',e=>e.stopPropagation());controls.append(b);}
  card.append(controls);
}};
window.MarvelDeckTouch.back=()=>{
  const p=document.getElementById('preview');
  if(!p||getComputedStyle(p).display==='none')return false;
  p.style.display='none';return true;
};
})();