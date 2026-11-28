import { koKeywords } from './ko-glossary.js';
export type RuleHelp={id:string;label:string;category:string;description:string};
const explanations:Record<string,string>={
 Toughness:'플레이 영역에 들어올 때 강인함 상태 카드 1장을 놓습니다.',
 Stalwart:'기절하거나 혼란에 빠질 수 없습니다.',
 Guard:'이 하수인과 교전 중인 플레이어는 빌런을 공격할 수 없습니다.',
 Peril:'카드를 해결하는 동안 다른 플레이어의 도움을 받을 수 없습니다.',
 Piercing:'공격 피해를 입히기 전에 대상의 강인함 상태 카드를 모두 버립니다.',
 Hinder:'교란 X가 있는 카드가 공개되면 그 카드에 위협 X를 놓습니다.',
 Alliance:'카드 사용을 선언할 때 다른 플레이어도 비용 지불을 도울 수 있습니다.',
 Retaliate:'공격받고 살아남으면 공격자에게 반격 수치만큼 피해를 입힙니다.',
 Uses:'플레이 영역에 들어올 때 명시된 카운터를 놓습니다. 마지막 카운터를 제거하고 효과를 해결한 후 카드를 버립니다.',
 Setup:'게임 준비 중 이 카드를 플레이 영역에 놓고 시작합니다.',
 Quickstrike:'적이 교전을 시작한 후 그 플레이어가 히어로 형태라면 즉시 공격합니다.',
 Surge:'이 카드를 해결한 후 같은 플레이어가 추가 조우 카드 1장을 공개합니다. 그 카드에도 쇄도가 있다면 반복합니다.',
 Temporary:'라운드가 끝날 때 플레이 영역에서 버립니다.',
 Patrol:'이 하수인과 교전 중인 플레이어는 주요 음모를 저지할 수 없습니다.',
 Victory:'이 카드가 격파되면 승점 구역에 놓습니다.',
 Villainous:'이 하수인이 활성화될 때 강화 카드 1장을 받습니다.',
 Overkill:'공격으로 하수인이나 동료를 격파할 때 초과 피해를 각각 빌런이나 동료 조종자의 아이덴티티에 입힙니다.',
 Permanent:'플레이 영역을 떠날 수 없습니다.',
 Ranged:'원거리 공격은 반격을 무시합니다.',
 Steady:'같은 종류의 기절 또는 혼란 상태 카드가 2장 있어야 해당 상태가 적용됩니다.',
 Incite:'진척 X가 있는 카드가 공개되면 주요 음모에 위협 X를 놓습니다.',
 Teamwork:'하수인이 교전에 들어왔을 때 같은 특성의 하수인이 이미 플레이 영역에 있다면 해당 팀워크 키워드를 공유하는 하수인들이 각각 교전 중인 플레이어에 대해 활성화됩니다.',
 Requirement:'비용 지불 시 명시된 자원 유형을 각각 소모해야 합니다.',
 Restricted:'플레이어는 한정 카드를 동시에 2장까지만 조종할 수 있습니다.',
 'Team-Up':'명시된 두 캐릭터가 모두 플레이 영역에 있을 때만 플레이할 수 있습니다.',
 Form:'아이덴티티가 취할 수 있는 고유 형태를 제공합니다.'
};
// Korean Rules Reference p.35 (keywords), plus short explanatory summaries.
export const ruleHelp:RuleHelp[]=[
 ...Object.entries(koKeywords).map(([id,label])=>({id,label,category:'키워드',description:explanations[id]})),
 {id:'Hazard',label:'수렁',category:'아이콘',description:'빌런 페이즈의 조우 카드 배분 때 아이콘 하나마다 플레이어 한 명에게 추가 조우 카드 1장을 줍니다. 플레이어마다 1장이 아닙니다.'},
 {id:'Acceleration',label:'가속',category:'아이콘',description:'주요 음모에 위협을 놓는 빌런 페이즈 단계에서 가속 아이콘 또는 가속 토큰마다 위협을 1씩 추가합니다.'},
 {id:'Crisis',label:'위기',category:'아이콘',description:'위기 아이콘이 있는 동안 플레이어는 주요 음모에서 위협을 제거할 수 없습니다.'},
 {id:'Amplify',label:'증폭',category:'아이콘',description:'적 활성화 중 뒤집는 각 강화 카드의 강화 아이콘 수를 증폭 아이콘 수만큼 늘립니다.'},
 {id:'Boost',label:'강화',category:'아이콘',description:'강화 카드의 강화 아이콘만큼 적의 공격 또는 음모 수치를 높입니다. 별 기호가 있는 강화 능력도 해결합니다.'},
 {id:'Tough',label:'강인함',category:'부가 상태',description:'피해를 입으려 할 때 피해를 모두 방지하고 강인함 상태 카드 1장을 버립니다.'},
 {id:'Stunned',label:'기절',category:'부가 상태',description:'공격하려 할 때 대신 기절 상태 카드를 버립니다.'},
 {id:'Confused',label:'혼란',category:'부가 상태',description:'저지하거나 암약하려 할 때 대신 혼란 상태 카드를 버립니다.'},
 {id:'Interrupt',label:'난입',category:'능력',description:'명시된 격발 조건을 해결하기 전에 사용하는 능력입니다.'},
 {id:'Response',label:'반응',category:'능력',description:'명시된 격발 조건을 해결한 직후 사용하는 능력입니다.'},
 {id:'Forced Interrupt',label:'강제 난입',category:'능력',description:'조건이 충족되면 반드시 해결하며 선택적 난입보다 우선합니다.'},
 {id:'Forced Response',label:'강제 반응',category:'능력',description:'조건이 충족되면 반드시 해결하며 선택적 반응보다 우선합니다.'},
 {id:'Scheme',label:'암약',category:'기본 규칙',description:'적이 음모 수치만큼 주요 음모에 위협을 놓습니다. 빌런은 일반적으로 강화 카드도 사용합니다.'},
 {id:'Indirect Damage',label:'간접 피해',category:'기본 규칙',description:'자신의 아이덴티티와 조종하는 동료 사이에 피해를 나눕니다. 각 캐릭터의 남은 생명력을 넘겨 배분할 수 없습니다.'},
 {id:'Physical Resource',label:'물리력 자원',category:'자원',description:'비용이나 효과에 지정된 물리력 자원으로 사용합니다.'},
 {id:'Mental Resource',label:'정신력 자원',category:'자원',description:'비용이나 효과에 지정된 정신력 자원으로 사용합니다.'},
 {id:'Energy Resource',label:'에너지 자원',category:'자원',description:'비용이나 효과에 지정된 에너지 자원으로 사용합니다.'},
 {id:'Wild Resource',label:'만능 자원',category:'자원',description:'비용을 지불할 때 필요한 다른 자원 유형으로 사용할 수 있습니다.'}
];
const broad=new Set(['Uses','Setup','Form','Victory','Restricted','Temporary','Alliance','Teamwork','Requirement','Team-Up','Permanent']);
function plain(value:string){return value.replace(/<br\s*\/?>/gi,'\n').replace(/<[^>]*>/g,'').replace(/\[\[([^\]]+)\]\]/g,'$1');}
export function relatedRules(english:string,korean:string,info:Record<string,number>={}):RuleHelp[]{
 const en=plain(english),ko=plain(korean);
 const live:Record<string,string[]>={Hazard:['hazard'],Acceleration:['acceleration_icon','k_acceleration_token'],Crisis:['crisis'],Amplify:['amplify'],Tough:['tough'],Stunned:['stunned'],Confused:['confused'],Retaliate:['retaliate'],Restricted:['restricted'],Villainous:['villainous'],Temporary:['temporary']};
 return ruleHelp.filter(r=>{
  if(live[r.id]?.some(k=>Number(info[k])>0))return true;
  if(broad.has(r.id))return new RegExp('(?:^|[\\n.。])\\s*(?:'+r.id+'|'+r.label+')(?=\\s*[(（\\dX.]|\\s*$)','im').test(en+'\n'+ko);
  if(new RegExp('(?:^|[^A-Za-z])'+r.id+'(?:$|[^A-Za-z])','i').test(en))return true;
  if(r.id==='Toughness')return /(?:^|[\n.。])\s*강인(?=\s*[.。:\n]|\s*$)/m.test(ko);
  if(r.id==='Scheme')return /암약/.test(ko);
  if(r.id==='Boost')return /강화(?: 카드| 아이콘|:)/.test(ko);
  return new RegExp('(?:^|[^가-힣])'+r.label+'(?=$|[^가-힣]|(?:을|를|이|가|은|는|의|과|와|에|으로|만|하|시킵|시키|됩))').test(ko);
 });
}
export function searchRules(query:string):RuleHelp[]{
 const q=query.trim().toLowerCase();
 return ruleHelp.filter(r=>[r.id,r.label,r.category,r.description].some(s=>s.toLowerCase().includes(q)));
}
export function renderRelatedRules(container:HTMLElement,entries:RuleHelp[]){
 container.replaceChildren();container.hidden=!entries.length;
 if(!entries.length)return;
 const heading=document.createElement('strong');heading.textContent='관련 규칙 도움말';container.append(heading);
 const buttons=document.createElement('div');buttons.className='rule-help-chips';
 const detail=document.createElement('div');detail.className='rule-help-detail';detail.hidden=true;
 for(const rule of entries){
  const button=document.createElement('button');button.type='button';button.textContent=rule.label+' ⓘ';button.setAttribute('aria-expanded','false');
  button.onclick=()=>{
   const open=button.getAttribute('aria-expanded')==='true';
   buttons.querySelectorAll('button').forEach(b=>b.setAttribute('aria-expanded','false'));
   detail.hidden=open;
   if(!open){button.setAttribute('aria-expanded','true');detail.textContent=rule.label+' ('+rule.id+') — '+rule.description;}
  };
  buttons.append(button);
 }
 container.append(buttons,detail);
}
export function createRuleDictionary(){
 const dialog=document.createElement('dialog');dialog.id='mobile-rule-dictionary';dialog.setAttribute('aria-label','규칙 사전');
 const header=document.createElement('header'),title=document.createElement('h2');title.textContent='규칙 사전';
 const close=document.createElement('button');close.type='button';close.textContent='닫기 ×';close.onclick=()=>dialog.close();header.append(title,close);
 const input=document.createElement('input');input.type='search';input.placeholder='키워드 검색 (한글 / English)';input.setAttribute('aria-label','규칙 검색');
 const count=document.createElement('small');count.setAttribute('aria-live','polite');
 const list=document.createElement('div');list.className='rule-dictionary-list';
 function update(){
  const results=searchRules(input.value);count.textContent=results.length+'개 · 참조 안내서 기반 요약';
  list.replaceChildren(...results.map(rule=>{
   const item=document.createElement('details'),summary=document.createElement('summary'),p=document.createElement('p');
   summary.textContent=rule.label+' ('+rule.id+')';p.textContent=rule.description;item.append(summary,p);return item;
  }));
  list.scrollTop=0;
 }
 input.addEventListener('input',update);dialog.append(header,input,count,list);document.body.append(dialog);update();
 return {dialog,open:()=>{input.value='';update();if(!dialog.open)dialog.showModal();}};
}
