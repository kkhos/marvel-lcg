import { koHtml, koLabel } from './ko-game.js';
import type { AskOptionPayload, EffectDescriptor } from './data.js';

export type PromptSummary = { action: string; count?: string; context?: string; payment?: {paid:string;required:string[]} };

const phases: Record<string,[string,string]> = {
    'Initialize':['준비','게임 준비 중'], 'Scenario Setup':['준비','시나리오 준비 중'],
    'Resolve Mulligans':['준비','손패 교체'], 'Init Finished':['준비','준비 완료'],
    'Player Turn':['플레이어','행동 선택'], 'Player Turn End':['플레이어','차례 종료'],
    'Main Scheme Place Threat':['빌런','위협 증가'], 'Enemy Activation':['빌런','적 활성화'],
    'Deal Encounter Cards':['빌런','조우 카드 배분'], 'Reveal Encounter Cards':['빌런','조우 카드 공개'],
    'End Phase':['','단계 종료'], 'End Round':['','라운드 종료'], 'Start Round':['','라운드 시작'],
    'Game Over':['','게임 종료']
};
export function phaseLabel(phase: string, round: number): string {
    const player = phase.match(/^Player (\d+) Turn$/);
    const stage = player ? '플레이어' : phases[phase]?.[0] || '';
    return [round>0 && stage!=='준비'?'R'+round:'',stage].filter(Boolean).join(' · ');
}
export function plainPrompt(html:string):string {
    const template=document.createElement('template');template.innerHTML=html;
    return (template.content.textContent||'').trim();
}
export function progressSummary(phase:string, raw:string):PromptSummary|undefined {
    const text=plainPrompt(raw);
    if(!text) return {action:phases[phase]?.[1]||(/^Player \d+ Turn$/.test(phase)?'행동 선택':'게임 진행 중')};
    if (/^[-=\s]*(?:Round \d+ (?:Start|End)|(?:Player|Villain) Phase(?: End)?)[-=\s]*$/.test(text))
        return {action:phases[phase]?.[1]||'단계 전환'};
    if (/resolves mulligans$/i.test(text)) return {action:'손패 교체'};
    if (/^[-=\s]*Game Over/.test(text)) return {action:'게임 종료'};
    // Only known, unambiguous engine notifications are summarized. Unknown card
    // text stays readable verbatim in the original scrollable prompt.
    const patterns:[RegExp,(m:RegExpMatchArray)=>string][]=[
        [/ draws (\d+) card\(s\)/,m=>'카드 '+m[1]+'장 뽑기'],
        [/ will take (\d+) damage from /,m=>'받을 피해 '+m[1]],
        [/ would deal (\d+) damage to /,m=>'피해 '+m[1]+' 예정'],
        [/ would place (\d+)⚠/,m=>'위협 +'+m[1]+' 예정'],
        [/ gained (\d+)⚠/,m=>'위협 +'+m[1]],
        [/ removed (\d+)⚠/,m=>'위협 −'+m[1]],
        [/ would remove (\d+)⚠/,m=>'위협 '+m[1]+' 제거 예정'],
        [/ gains (\d+)♡/,m=>'생명력 +'+m[1]],
        [/ lost (\d+)♡/,m=>'생명력 −'+m[1]],
        [/ gains (\d+) boost icons/,m=>'강화 아이콘 +'+m[1]],
        [/ would count boost icons/,()=> '강화 아이콘 계산'],
        [/ was revealed$/,()=> '조우/카드 공개'],
        [/ is being revealed$/,()=> '카드 공개 중'],
        [/ was defeated(?: by |$)/,()=> '격파'],
        [/ were discarded$/,()=> '카드 버림'],
        [/ was shuffled(?: with |$)/,()=> '덱 섞기'],
        [/ has run out$/,()=> '덱 소진'],
        [/ would surge against /i,()=> '쇄도 · 추가 조우 카드 공개'],
        [/ activation ends$/,()=> '적 활성화 종료']
    ];
    for(const [re,format] of patterns){const match=text.match(re);if(match)return {action:format(match)};}
    return undefined;
}
export function askSummary(ask:Pick<AskOptionPayload,'event_name'|'ability_type'|'show_cancel'|'options'>, phase:string, raw:string):PromptSummary|undefined {
    const choices=ask.options.filter(o=>o.name!=='Cancel'&&!o.failure_reason);
    if (choices.length===1 && choices[0].name_with_space==='Resolve Mulligans') return {action:'교체할 카드 선택'};
    if (choices.length===1 && choices[0].name_with_space==='End Phase') return {action:'버릴 카드 선택'};
    const timing:Record<string,string>={Response:'반응 능력 선택',Interrupt:'난입 능력 선택',ForcedResponse:'강제 반응 해결',ForcedInterrupt:'강제 난입 해결'};
    if(timing[ask.ability_type]) return {action:timing[ask.ability_type],count:ask.show_cancel?'선택 사항':'필수'};
    if(ask.event_name==='WhenPlayerInTurn')return {action:'사용할 카드 또는 능력 선택'};
    // A nonempty custom instruction can encode card-specific conditions.
    if(plainPrompt(raw))return undefined;
    if(ask.event_name==='WhenPlayerChooseAbility')return {action:'해결할 능력 선택',count:ask.show_cancel?'선택 사항':'필수'};
    if(ask.event_name==='WhenResolveSpecialAbility')return {action:'특수 능력 해결'};
    return undefined;
}
export function targetSummary(effect:EffectDescriptor):PromptSummary {
    const [min,max]=effect.target_num_range;
    const n=effect.selected_targets.length;
    const name=effect.name_with_space;
    const known:Record<string,string>={
        'Resolve Mulligans':'교체할 카드 선택','End Phase':'버릴 카드 선택','Attack':'공격할 적 선택',
        'Thwart':'저지할 음모 선택','Defense':'방어할 캐릭터 선택','Recover':'회복할 대상 선택',
        'Discard':'버릴 카드 선택','Ally Limit':'버릴 동료 선택','Change Form':'형태 전환',
        'ChooseAbility':'해결할 능력 선택'
    };
    const action=known[name] || (effect.display_in_target_order?'처리 순서 선택':effect.is_search?'검색할 카드 선택':'대상 선택');
    const label=known[name]?undefined:plainPrompt(koHtml(name))||undefined;
    return {action,count:min===max?n+'/'+max:n+'장 · '+min+'~'+max+' 선택',context:label};
}
export function paymentSummary(effect:EffectDescriptor,paid:number,costOptions:string[],ok:boolean,overpay:boolean,paidSymbols=''):PromptSummary {
    const generic=costOptions.length===1&&/^\d+$/.test(costOptions[0])&&!effect.isCostRuleSameType()&&!effect.isCostRuleDifferentType()&&!effect.isCostRuleUpTo();
    const rules=[effect.isCostRuleSameType()?'같은 유형':'',effect.isCostRuleDifferentType()?'서로 다른 유형':'',effect.isCostRuleUpTo()?'최대 비용':''].filter(Boolean);
    return {action:overpay?'초과 지불 확인':ok?'자원 지불 완료':'자원 지불',count:generic?paid+'/'+Number(costOptions[0]):undefined,context:rules.join(' · ')||undefined,payment:generic?undefined:{paid:paidSymbols,required:costOptions}};
}
export class MobilePrompt {
    static render(container:HTMLElement, output:HTMLElement, raw:string, summary:PromptSummary|undefined, phase:string, round:number) {
        let details=container.querySelector<HTMLButtonElement>('#mobile-prompt-more');
        let dialog=document.getElementById('mobile-prompt-dialog') as HTMLDialogElement|null;
        if(!dialog){
            dialog=document.createElement('dialog');dialog.id='mobile-prompt-dialog';dialog.setAttribute('aria-label','현재 안내 상세');
            const title=document.createElement('h2');title.textContent='현재 안내 상세';
            const content=document.createElement('div');content.id='mobile-prompt-original';
            const close=document.createElement('button');close.type='button';close.textContent='닫기';close.onclick=()=>dialog!.close();
            dialog.append(title,content,close);document.body.append(dialog);
        }
        if(!details){
            details=document.createElement('button');details.type='button';details.id='mobile-prompt-more';
            details.textContent='⋯';details.setAttribute('aria-label','현재 안내 상세');container.append(details);
            details.onclick=()=>{if(!dialog!.open)dialog!.showModal();};
        }
        const full=koHtml(raw);
        const content=dialog.querySelector('#mobile-prompt-original')!;
        if(content.innerHTML!==full)content.innerHTML=full;
        details.hidden=!raw.trim();
        if(!summary){output.innerHTML=full;output.scrollTop=0;return;}
        const row=document.createElement('div');row.className='mobile-prompt-summary';
        const badge=phaseLabel(phase,round);
        if(badge){const stage=document.createElement('span');stage.className='mp-phase';stage.textContent=badge;row.append(stage);}
        const action=document.createElement('span');action.className='mp-action';action.textContent=summary.action;row.append(action);
        if(summary.context){const context=document.createElement('span');context.className='mp-context';context.textContent=summary.context;row.append(context);}
        if(summary.payment){
            const payment=document.createElement('span');payment.className='mp-payment';
            const symbols:Record<string,string>={R:'physical',B:'mental',Y:'energy',G:'wild'};
            const append=(value:string)=>{
                for(const char of value){
                    if(symbols[char]){
                        const icon=document.createElement('span');icon.className='icon-'+symbols[char];payment.append(icon);
                    }else payment.append(document.createTextNode(char));
                }
            };
            append(summary.payment.paid||'0');payment.append(document.createTextNode(' / '));
            summary.payment.required.forEach((value,i)=>{if(i)payment.append(document.createTextNode(' 또는 '));append(value);});
            row.append(payment);
        }
        if(summary.count){const count=document.createElement('span');count.className='mp-count';count.textContent=summary.count;row.append(count);}
        output.replaceChildren(row);output.scrollTop=0;
    }
}
