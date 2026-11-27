(() => {
  if (!/Android|iPhone|iPad/i.test(navigator.userAgent) && !matchMedia('(pointer:coarse)').matches) return;
  const q=(s,r=document)=>r.querySelector(s), el=(tag,cls,text)=>{const x=document.createElement(tag);if(cls)x.className=cls;if(text)x.textContent=text;return x;};
  const button=(text,fn,cls)=>{const x=el('button',cls,text);x.type='button';x.onclick=fn;return x;};
  const fields=[q('#set-images')?.closest('fieldset'),q('#split-scenario-selector'),q('#encounter-sets')?.closest('fieldset')?.parentElement,q('#modular-sets')?.closest('fieldset')?.parentElement,q('#heroes-1')?.closest('fieldset'),q('#game-start')];
  if(fields.some(f=>f?.tagName!=='FIELDSET'))return;
  const [sc,split,standard,modular,hero,game]=fields;
  const shell=el('main','ml-shell'),header=el('header','ml-header'),title=el('h1'),steps=el('span','ml-steps'),body=el('div','ml-body'),foot=el('footer','ml-footer'),msg=el('span','ml-muted');
  let stage=0,slot=1,selected=null,loaded=false,kind='starter',catalogReady=!!window.setupCatalogReady;
  const back=button('‹ 이전',()=>{if(stage)go(stage-1);else history.back();});
  const next=button('',()=>{if(stage<2)go(stage+1);else doCreateNewGame(Object.values(heroes).filter(Boolean).length>1?'hot_seat':'');},'ml-primary');
  header.append(back,title,steps);foot.append(msg,next);shell.append(header,body,foot);document.body.prepend(shell);document.body.classList.add('ml-mobile');
  const panels=[0,1,2].map(()=>el('section','ml-panel'));body.append(...panels);
  const left=el('div','ml-scroll'),right=el('aside','ml-scroll ml-detail'),search=el('input','ml-search');search.type='search';search.placeholder='빌런 / 확장팩 검색';
  const scenarioName=el('h2','ml-scenario-name','시나리오를 선택하세요'),scenarioImage=el('img','ml-big'),mode=el('p','ml-scenario-mode'),scenarioPack=el('p','ml-muted ml-scenario-pack'),scenarioHeading=el('div','ml-scenario-heading');scenarioImage.alt='';scenarioHeading.append(el('span','ml-muted','선택한 시나리오'),scenarioName,mode,scenarioPack);scenarioHeading.setAttribute('aria-live','polite');
  const encounter=el('details','ml-settings');encounter.open=false;encounter.append(el('summary','','조우 세트 설정'),standard,modular);
  const originalFile=q('#scenario-1')?.parentElement;if(originalFile){right.append(originalFile);originalFile.classList.add('ml-file');right.append(button('시나리오 파일 가져오기',()=>q('#scenario-1')?.click()));}
  const catalogStatus=el('p','ml-muted','확장팩을 불러오는 중…');left.append(search,catalogStatus,sc);right.prepend(scenarioHeading,scenarioImage);right.append(split,encounter);panels[0].append(left,right);
  function image(img,id){if(id){img.hidden=false;const name=get_name(id);if(img.getAttribute('src')!==name)img.src=name;}else{img.hidden=true;img.removeAttribute('src');}}
  function filter(){const term=search.value.trim().toLowerCase();document.querySelectorAll('#set-images>.set').forEach(p=>{p.classList.toggle('ml-filter',!!term&&!((p.dataset.package||'').toLowerCase().includes(term)||[...p.querySelectorAll('button[data-scenario]')].some(b=>(b.title+' '+b.value).toLowerCase().includes(term))));});document.querySelectorAll('#set-content button[data-scenario]').forEach(b=>{b.classList.toggle('ml-filter',!!term&&!(q('#set-images>.set.click')?.dataset.package||'').toLowerCase().includes(term)&&!(b.title+' '+b.value).toLowerCase().includes(term));});}
  function annotate(){document.querySelectorAll('#set-content button[data-scenario],#split-scenarios button[data-scenario]').forEach(b=>{try{const d=JSON.parse(b.dataset.scenario);b.dataset.caption=d.name||b.value;b.dataset.mode=d.expert?'전문가':'일반';b.setAttribute('aria-label',b.dataset.caption+' '+b.dataset.mode);}catch{}});filter();}
  search.oninput=filter;
  const hleft=el('div','ml-scroll'),hright=el('aside','ml-scroll ml-detail'),hsearch=el('input','ml-search');hsearch.type='search';hsearch.placeholder='히어로 / 덱 검색';
  const tabs=el('div','ml-tabs'),grid=el('div','ml-grid'),status=el('p','ml-muted','덱 목록을 준비합니다.'),himage=el('img','ml-big'),hname=el('h2','','히어로 선택'),hinfo=el('p','ml-muted'),slots=el('div','ml-slots');himage.alt='';
  const add=button('플레이어 1에 추가',()=>{if(selected){SetHero(selected,slot);refresh();}},'ml-primary');add.disabled=true;
  const starter=button('초심자용 덱',()=>{kind='starter';render();}),custom=button('내 덱',()=>{kind='custom';render();});tabs.append(starter,custom);
  hleft.append(hsearch,tabs,status,grid);hright.append(himage,hname,hinfo,add,slots,hero);panels[1].append(hleft,hright);
  const hp=hero.querySelector('p');if(hp){hp.replaceChildren(document.createTextNode('사용자 덱: '),button('JSON 붙여넣기',()=>{const t=prompt('덱 JSON을 붙여넣으세요.');if(t)try{SetHero(JSON.parse(t),slot);refresh();}catch{alert('올바른 덱 JSON을 입력하세요.');}}));}
  const summary=el('div','ml-scroll'),finalCards=el('div','ml-grid'),finalInfo=el('p','ml-muted'),advanced=el('div','ml-scroll ml-detail');
  summary.append(el('h2','','출격 준비'),finalCards,finalInfo);advanced.append(el('h2','','세부 설정'),game);panels[2].append(summary,advanced);
  const records={starter:[],custom:[]};
  function cardTile(name,id,sub){const box=el('div','ml-tile'),img=el('img');img.alt='';image(img,id);box.append(img,el('strong','',name),el('small','ml-muted',sub));return box;}
  function refresh(){
    const s=scenario||selected_underling;
    const active=q('#set-content button.click[data-scenario]');
    const pack=q('#set-images>.set.click');
    scenarioName.textContent=s?.name||active?.dataset.caption||active?.title||'시나리오를 선택하세요';
    mode.textContent=s?(s.expert?'전문가 모드':'일반 모드')+(scenario?'':' · 주요 음모 선택 필요'):active?'선택 확인 중…':'확장팩과 빌런을 선택하세요.';
    mode.classList.toggle('ml-expert',!!s?.expert);
    scenarioPack.textContent=pack?.dataset.package||'';
    scenarioPack.hidden=!scenarioPack.textContent;
    image(scenarioImage,s?.villain?.[0]||s?.schemes?.[0]||s?.set_aside?.[0]);
    slots.replaceChildren();for(let i=1;i<=4;i++){const row=el('div','ml-slot'),b=button('P'+i+' · '+(heroes[i]?.name||'선택 안 함'),()=>{slot=i;refresh();},slot===i?'ml-active':'');row.append(b);if(heroes[i])row.append(button('×',()=>{SetHero({},i);refresh();}));slots.append(row);}
    add.textContent='플레이어 '+slot+'에 '+(heroes[slot]?'교체':'추가');
    finalCards.replaceChildren();if(scenario)finalCards.append(cardTile(scenario.name,scenario.villain?.[0]||scenario.schemes?.[0],scenario.expert?'전문가 모드':'일반 모드'));
    const count=Object.values(heroes).filter(Boolean).length;Object.entries(heroes).filter(([,d])=>d).forEach(([i,d])=>finalCards.append(cardTile(d.name,d.hero?.[0],'플레이어 '+i)));
    finalInfo.textContent='조우 세트 '+document.querySelectorAll('#encounter-sets button.click,#modular-sets button.click').length+'개 · 플레이어 '+count+'명';
    next.disabled=stage===0?!catalogReady||!scenario:!count||!scenario;
    msg.textContent=stage===0?(scenario?(scenario.name||active?.title||'시나리오 선택 완료')+' · '+(scenario.expert?'전문가 모드':'일반 모드'):catalogReady?'빌런과 난이도를 선택하세요.':'시나리오 불러오는 중…'):stage===1?'히어로와 덱을 선택하세요.':'선택한 구성으로 게임을 시작합니다.';
  }
  function go(n){stage=n;panels.forEach((p,i)=>p.hidden=i!==n);title.textContent=['시나리오 선택','히어로 선택','게임 준비'][n];steps.textContent=(n+1)+' / 3';next.textContent=['히어로 선택 →','게임 준비 →','게임 시작'][n];if(n===1&&!loaded)load();refresh();}
  function render(){
    const term=hsearch.value.trim().toLowerCase(),list=records[kind].filter(r=>r.name.toLowerCase().includes(term));starter.classList.toggle('ml-active',kind==='starter');custom.classList.toggle('ml-active',kind==='custom');grid.replaceChildren();
    for(const r of list){const tile=button('',()=>{selected=r.data;hname.textContent=r.name;hinfo.textContent='플레이어 덱 '+selected.player_deck.length+'장';image(himage,selected.hero[0]);add.disabled=false;render();},'ml-tile'+(selected===r.data&&r.data?' ml-active':''));const img=el('img');img.alt='';img.loading='lazy';image(img,r.data?.hero?.[0]);tile.append(img,el('strong','',r.name));tile.disabled=!r.data;grid.append(tile);}
    status.textContent=list.length+'개 덱';
  }
  async function load(){loaded=true;await Promise.all([['starter','list_starter_deck?'],['custom','list_deck?']].map(async([k,url])=>{try{const res=await fetchFresh(url);if(!res.ok)throw Error();records[k]=[...new Set((await res.json()).map(getFileName))].map(key=>({key,name:key.replace(/_/g,' '),data:null}));if(kind===k)render();let i=0;await Promise.all(Array.from({length:4},async()=>{while(i<records[k].length){const r=records[k][i++];try{const a=await fetchFresh('get_hero_json?'+encodeURIComponent(r.key));if(!a.ok)throw Error();const d=await a.json();if(d.hero?.[0]&&Array.isArray(d.player_deck)){r.data=d;r.name=d.name||r.name;}}catch{}if(kind===k)render();}}));}catch{status.textContent='덱 목록을 불러오지 못했습니다.';}}));}
  hsearch.oninput=render;
  const oldScenario=SetScenario;SetScenario=function(...a){const r=oldScenario.apply(this,a);queueMicrotask(refresh);return r;};
  const oldHero=SetHero;SetHero=function(...a){const r=oldHero.apply(this,a);queueMicrotask(refresh);return r;};
  const observer=new MutationObserver(()=>{annotate();refresh();});observer.observe(q('#set-content'),{childList:true,subtree:true});observer.observe(q('#split-scenarios'),{childList:true,subtree:true});
  [left,right].forEach(x=>x.addEventListener('click',()=>queueMicrotask(refresh)));
  function ready(){catalogReady=true;const sets=[...document.querySelectorAll('#set-images>.set:not(.disable)')];catalogStatus.textContent=sets.length?'확장팩을 선택한 다음 빌런 카드를 선택하세요.':'사용 가능한 시나리오가 없습니다.';if(!q('#set-images>.set.click')&&sets.length&&!scenario)sets[0].click();annotate();refresh();}
  function failed(){catalogStatus.textContent='시나리오 목록을 불러오지 못했습니다.';catalogStatus.append(button('다시 시도',()=>location.reload()));}
  window.addEventListener('setup-catalog-ready',ready);
  window.addEventListener('setup-catalog-error',failed);
  if(catalogReady)ready();else if(window.setupCatalogError)failed();
  window.MarvelSetup={back:()=>{if(stage){go(stage-1);return true;}return false;}};
  image(himage,'');annotate();go(0);
})();