(() => {
const touch=/Android|iPhone|iPad/i.test(navigator.userAgent)||matchMedia('(pointer:coarse)').matches;
if(!touch)return;
document.documentElement.classList.add('deck-touch');
window.MarvelDeckTouch={attach(card,actions){
  const controls=document.createElement('div');controls.className='deck-card-controls';
  for(const [symbol,label,run] of actions){const b=document.createElement('button');b.type='button';b.textContent=symbol;b.title=label;b.setAttribute('aria-label',label);b.addEventListener('click',e=>{e.stopPropagation();e.preventDefault();run();});b.addEventListener('pointerdown',e=>e.stopPropagation());controls.append(b);}
  card.append(controls);
}};
})();