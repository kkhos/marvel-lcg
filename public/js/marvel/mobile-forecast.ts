import type { WorldDescriptor, CardDescriptor } from './descriptor.js';

const unit = (c: CardDescriptor) => c.is_face_up && c.isVisible();
const stat = (c: CardDescriptor, key: string) => Number.isFinite(c.info[key]) ? c.info[key] : undefined;
export function forecastText(world: WorldDescriptor) {
    const players = world.players.filter(p => !p.is_eliminated);
    const villains = world.area_villain.filter(c => c.card_type === 'EncounterVillain' && unit(c));
    const main = world.area_schemes_main.filter(c => c.card_type === 'MainScheme' && unit(c));
    const schemes = [...main, ...world.area_schemes_side.filter(c => c.card_type === 'EncounterSideScheme' && unit(c))];
    const escalation = main.map(c => stat(c,'escalation_threat'));
    const threat = escalation.length && escalation.every(x=>x!==undefined) ? escalation.reduce<number>((n,x)=>n+(x??0),0) : undefined;
    const icons = schemes.reduce((n,c)=>n+(stat(c,'acceleration_icon')??0),0);
    const tokens = schemes.reduce((n,c)=>n+(stat(c,'k_acceleration_token')??0),0);
    const hazards = schemes.reduce((n,c)=>n+(stat(c,'hazard')??0),0);
    const lines = players.map((p,i)=>{
        const hero=p.area_hero.find(c=> (c.card_type==='Hero'||c.card_type==='AlterEgo') && unit(c));
        const key=hero?.card_type==='AlterEgo'?'scheme':'attack';
        const kind=hero?.card_type==='AlterEgo'?'음모':'공격';
        const values=villains.map(v=>stat(v,key));
        const label=hero?.name || '플레이어 '+(i+1);
        const minions=p.engaged_enemies.filter(c=>c.card_type==='Minion'&&unit(c));
        const detail=villains.map((v,j)=>v.name+' '+(values[j]??'?')).join(' / ');
        return {label, kind, detail, minions:minions.length, base:values.length===1?values[0]:undefined};
    });
    const threatLabel=threat===undefined?'위협 ?':'위협 +'+threat;
    const attack=lines.length===1 && lines[0].base!==undefined ? lines[0].kind+' '+lines[0].base+'+★' : '활성화 확인';
    return {summary: threatLabel+' · '+attack+' · 조우 '+players.length,
        details: [
            '주요 음모의 기본 위협 증가: '+(threat===undefined?'확인 필요': '+'+threat),
            '공개된 가속 아이콘 '+icons+' · 가속 토큰 '+tokens+' (기본값에 별도 반영되는지는 시나리오 규칙에 따름)',
            ...lines.map(l=>l.label+' · '+l.kind+' '+(l.detail||'확인 필요')+' · 교전 하수인 '+l.minions+'명'),
            '조우 카드 기본 '+players.length+'장 · 공개된 위험 아이콘 '+hazards+'개',
            '기본 규칙과 현재 공개 정보 기준. 강화 카드, 상태 카드, 추가 활성화 및 시나리오 특수 효과는 결과를 바꿀 수 있습니다.'
        ]};
}
export class MobileForecast {
    static init(header: HTMLElement) {
        const button=document.createElement('button');
        button.id='mobile-forecast';button.type='button';button.hidden=true;
        button.setAttribute('aria-label','빌런 단계 예상 상세');
        const dialog=document.createElement('dialog');dialog.id='mobile-forecast-dialog';
        dialog.setAttribute('aria-label','빌런 단계 예상');
        const title=document.createElement('h2');title.textContent='빌런 단계 예상';
        const detail=document.createElement('div');detail.id='mobile-forecast-detail';
        const close=document.createElement('button');close.type='button';close.textContent='닫기';close.onclick=()=>dialog.close();
        dialog.append(title,detail,close);document.body.append(dialog);header.append(button);
        button.onclick=()=>{if(!dialog.open)dialog.showModal();};
    }
    static update(world: WorldDescriptor) {
        const button=document.getElementById('mobile-forecast') as HTMLButtonElement|null;
        const detail=document.getElementById('mobile-forecast-detail');
        if(!button||!detail)return;
        const result=forecastText(world);
        button.hidden=false;button.textContent=result.summary+' ▾';
        button.title='빌런 단계 기본 예상 · 자세히 보기';
        detail.replaceChildren(...result.details.map(line=>{const p=document.createElement('p');p.textContent=line;return p;}));
    }
}
