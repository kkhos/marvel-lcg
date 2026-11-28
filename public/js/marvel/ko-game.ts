import { koKeywordLabel } from './ko-glossary.js';
// Display-only labels; engine commands and card data must never be translated.
// Terminology: Korean Marvel Champions Rules Reference (June 2023), pp. 2–6, 35.
// Scheme as an action = 암약; scheme card = 음모; SCH stat = 음모 수치.
const labels: Record<string, string> = {
  "Assign": "배분",
  "STATISTIC": "통계",
  "Statistic": "통계",
  "Statistics": "통계",
  "RESPONSE": "반응",
  "COMMAND": "명령",
  "Resolve": "효과 처리",
  "Resolved": "효과 처리 완료",
  "Enters Play": "플레이 영역에 들어옴",
  "Entered Play": "플레이 영역에 들어옴",
  "PutIntoPlay": "플레이 영역에 들어옴",
  "Attached": "장착됨",
  "Played": "플레이 완료",
  "Revealed": "공개됨",
  "Reveal": "공개",
  "Discarded": "버려짐",
  "Canceled": "취소됨",
  "Cancelled": "취소됨",
  "GameOver": "게임 종료",
  "Otherwise": "그 외의 경우",
  "Yes": "예",
  "No": "아니요",
  "All": "모두",
  "Spider-Sense": "스파이더센스",
  "Scientist": "과학자",
  "Spell Mastery": "주문 숙달",
  "Natural Talent": "천부적 재능",
  "Invocation Deck": "비술 덱",
  "Invocation deck": "비술 덱",
  "Leave Innate Reflexes in your deck": "타고난 반사신경을 덱에 남기기",
  "Starting": "시작 시",
  "Main scheme phase start": "주요 음모 단계 시작",
  "Main scheme phase end": "주요 음모 단계 종료",
  "Exhaust Peter Parker → remove Eviction Notice from the game": "Peter Parker 소진 → 퇴거 통지를 게임에서 제거",
  "Discard 1 card at random from your hand. This card gains surge. Discard this obligation": "손에서 무작위 카드 1장을 버립니다. 이 카드는 쇄도를 얻습니다. 이 의무 카드를 버립니다",
  "Initialize": "초기화",
  "Scenario Setup": "시나리오 준비",
  "Resolve Mulligans": "멀리건 처리",
  "Init Finished": "준비 완료",
  "Player Turn": "플레이어 차례",
  "Player Turn End": "플레이어 차례 종료",
  "Main Scheme Place Threat": "주요 음모에 위협 놓기",
  "Enemy Activation": "적 활성화",
  "Deal Encounter Cards": "조우 카드 나눠주기",
  "Reveal Encounter Cards": "조우 카드 공개",
  "End Phase": "페이즈 종료",
  "End Round": "라운드 종료",
  "Start Round": "라운드 시작",
  "Game Over": "게임 종료",
  "Player Phase": "플레이어 페이즈",
  "Villain Phase": "빌런 페이즈",
  "Player Phase End": "플레이어 페이즈 종료",
  "Villain Phase End": "빌런 페이즈 종료",
  "Cost": "비용",
  "Targets": "목표",
  "ChooseAbility": "능력 선택",
  "Choose Ability": "능력 선택",
  "Game Rule": "게임 규칙",
  "Ally Limit": "동료 제한",
  "Play": "플레이",
  "Play 1": "플레이 1",
  "Play 2": "플레이 2",
  "Attack": "공격",
  "Thwart": "저지",
  "Defense": "방어",
  "Recover": "회복",
  "Change Form": "변신",
  "Action": "행동",
  "Action 1": "행동 1",
  "Hero Action": "히어로 행동",
  "Alter-Ego Action": "일상 행동",
  "First Player Action": "시작 플레이어 행동",
  "Forced Action": "강제 행동",
  "Response": "반응",
  "Basic Power": "기본 기능",
  "Basic power": "기본 기능",
  "Hero Response": "히어로 반응",
  "Alter-Ego Response": "일상 반응",
  "Forced Response": "강제 반응",
  "Interrupt": "난입",
  "Hero Interrupt": "히어로 난입",
  "Alter-Ego Interrupt": "일상 난입",
  "Forced Interrupt": "강제 난입",
  "Resource": "자원",
  "Special": "특수",
  "When Defeated": "격파될 때",
  "When Revealed": "공개될 때",
  "Ask": "선택",
  "Discard": "버리기",
  "Draw": "뽑기",
  "Ready": "준비",
  "Exhaust": "소진",
  "Cancel": "취소",
  "End": "종료",
  "OK": "확인",
  "Over<br/>Pay": "초과<br/>지불",
  "End<br/>Response": "반응<br/>종료",
  "End<br/>Interrupt": "난입<br/>종료",
  "End<br/>Defense": "방어<br/>종료",
  "End<br/>Turn": "차례<br/>종료",
  "Cancel<br/>Pay": "지불<br/>취소",
  "Load Crash": "오류 복구",
  "Card Tilt": "카드 기울기",
  "Sound": "소리",
  "New Badge": "신규 표시",
  "Enhance Fx": "효과 강화",
  "Card Text": "카드 설명",
  "Preview": "미리보기",
  "QLoad": "빠른 불러오기",
  "Load 1": "불러오기 1",
  "Load 2": "불러오기 2",
  "Load 3": "불러오기 3",
  "Save 1": "저장 1",
  "Save 2": "저장 2",
  "Save 3": "저장 3",
  "Load": "불러오기",
  "Save": "저장",
  "Auto Targeting": "자동 목표 선택",
  "Auto Activate": "자동 활성화",
  "Show Auto Activate Checkbox": "자동 활성화 체크 표시",
  "Auto Pause": "자동 일시정지",
  "Sort Hand": "손패 정렬",
  "By ID": "번호순",
  "By Type": "종류순",
  "Sort Area": "영역 정렬",
  "By Name": "이름순",
  "Restart Turn": "차례 다시 시작",
  "Full Search": "전체 검색",
  "Log": "기록",
  "Pause": "일시정지",
  "Undo": "되돌리기",
  "Redo": "다시 실행",
  "Break": "중단",
  "QSave": "빠른 저장",
  "Replay": "리플레이",
  "VICTORY": "승리",
  "DEFEAT": "패배",
  "Replay complete — VICTORY": "리플레이 완료 — 승리",
  "Replay complete — DEFEAT": "리플레이 완료 — 패배",
  "Please wait": "잠시 기다려 주세요",
  "First Player Interrupt": "시작 플레이어 난입",
  "Hero Action 1": "히어로 행동 1",
  "Hero": "히어로",
  "Alter-Ego": "일상",
  "AlterEgo": "일상",
  "SCH": "음모 수치",
  "Boost": "강화",
  "Scheme": "암약",
  "Stunned": "기절",
  "Confused": "혼란",
  "Tough": "강인함",
  "Indirect Damage": "간접 피해",
  "Hazard": "수렁",
  "Acceleration": "가속",
  "Crisis": "위기",
  "Amplify": "증폭",
  "Ally": "동료",
  "Minion": "하수인",
  "MainScheme": "주요 음모",
  "Main Scheme": "주요 음모",
  "SideScheme": "부가 음모",
  "Side Scheme": "부가 음모",
  "PlayerSideScheme": "플레이어 부가 음모",
  "Treachery": "배반",
  "Attachment": "장착",
  "Villain": "빌런",
  "Obligation": "의무",
  "Status": "부가 상태",
  "Event": "이벤트",
  "Upgrade": "업그레이드",
  "Support": "지원",
  "Environment": "환경",
  "Nemesis": "숙적",
  "Aggression": "용맹",
  "Justice": "정의",
  "Protection": "수호",
  "Leadership": "통솔",
  "Basic": "기본",
  "Turn": "차례",
  "End Turn": "차례 종료",
  "Phase": "페이즈",
  "First Player": "시작 플레이어",
  "First Player Response": "시작 플레이어 반응",
  "Target": "목표",
  "Select Target": "목표 선택",
  "Select Targets": "목표 선택",
  "HP": "생명력",
  "Hit Points": "생명력",
  "ATK": "공격 수치",
  "DEF": "방어 수치",
  "THW": "저지 수치",
  "REC": "회복 수치",
  "Hand Size": "손 크기",
  "Standard Set": "일반 조우 세트",
  "Standard Sets": "일반 조우 세트",
  "Expert Set": "전문가 조우 세트",
  "Expert Sets": "전문가 조우 세트",
  "Modular Set": "모듈식 조우 세트",
  "Modular Sets": "모듈식 조우 세트",
  "Standard Mode": "일반 모드",
  "Expert Mode": "전문가 모드",
  "Heroic Mode": "영웅 모드",
  "Skirmish Mode": "전초전 모드",
  "Rookie Mode": "초보자 모드",
  "Campaign Mode": "캠페인 모드",
  "Campaign Log": "캠페인 기록지",
  "When Completed": "달성될 때",
  "Defeated": "격파",
  "Defeat": "격파",
  "Heal": "치료",
  "Damage": "피해",
  "Threat": "위협",
  "Identity": "아이덴티티",
  "Status Card": "부가 상태 카드",
  "Physical Resource": "물리력 자원",
  "Mental Resource": "정신력 자원",
  "Energy Resource": "에너지 자원",
  "Wild Resource": "만능 자원",
  "Encounter Deck": "조우 덱",
  "Encounter Card": "조우 카드",
  "Discard Pile": "버린 카드 더미",
  "Victory Display": "승점 구역",
  "Engaged": "교전 중",
  "Consequential Damage": "부수적 피해",
  "Play Area": "플레이 영역",
  "Activate": "활성화",
  "Mental": "정신력",
  "Physical": "물리력",
  "Energy": "에너지",
  "Wild": "만능",
  "Aspect": "성향",
  "Stage": "스테이지",
  "Boost Card": "강화 카드",
  "Boost Icon": "강화 아이콘",
  "Per Player": "플레이어마다",
  "Unique": "고유",
  "Player Deck": "플레이어 덱",
  "Encounter Discard Pile": "버린 조우 카드 더미",
  "Player Discard Pile": "버린 플레이어 카드 더미",
  "Ready State": "준비 상태",
  "Exhausted State": "소진 상태",
  "Threat Threshold": "위협 임계점",
  "Triggering Condition": "격발 조건",
  "Constant Ability": "상시 능력",
  "Lasting Effect": "지속 효과",
  "Delayed Effect": "지연 효과",
  "Replacement Effect": "대체 효과",
  "Reminder Text": "되새김 문구",
  "Trait": "특성",
  "Active Player": "활성 플레이어",
  "Remaining Hit Points": "남은 생명력",
  "Maximum Hit Points": "최대 생명력",
  "Excess Damage": "초과 피해",
  "Nemesis Encounter Set": "숙적 조우 세트",
  "Resolve Ability": "능력 해결",
  "Initiate Ability": "능력 개시",
  "Amplify Icon": "증폭 아이콘",
  "Card Play": "카드 플레이"
};
export function koLabel(value: string): string {
    return koKeywordLabel(value) ?? (Object.prototype.hasOwnProperty.call(labels, value) ? labels[value] : value);
}
// Statistics event codes are presentation labels, not engine commands.
export function koStatistic(value: string): string {
    const events: Record<string,string> = {
        Resolve: '효과 처리', Resolved: '효과 처리 완료',
        Play: '플레이', Played: '플레이 완료', Resource: '자원으로 사용',
        Reveal: '공개', Revealed: '공개됨', PutIntoPlay: '플레이 영역에 들어옴',
        Attached: '장착됨', Hero: '플레이 영역에 들어옴',
        Defeated: '격파', Discard: '버려짐', Cancel: '취소',
        GameOver: '게임 종료'
    };
    return Object.prototype.hasOwnProperty.call(events, value) ? events[value] : koLabel(value);
}
export function koGameOverReason(value: string): string {
    const reasons: Record<string,string> = {
        'There were no cards in either the encounter deck or the encounter discard pile': '조우 덱과 조우 버린 카드 더미에 카드가 없습니다',
        'All players were eliminated': '모든 플레이어가 탈락했습니다',
        'The Final Stage of the Villain was Defeated': '빌런의 마지막 단계를 격파했습니다',
        'The Final Stage of the Main Scheme was Completed': '주요 음모의 마지막 단계가 달성되었습니다',
        'The Main Scheme was Completed': '주요 음모가 달성되었습니다',
        'Players Won': '플레이어가 승리했습니다',
        'Players Lost': '플레이어가 패배했습니다'
    };
    for (const [en, ko] of Object.entries(reasons)) {
        if (value.toLowerCase().startsWith(en.toLowerCase())) return ko + value.slice(en.length);
    }
    return koText(value);
}
export function koText(value: string): string {
    const direct = koLabel(value);
    if (direct !== value) return direct;
    return value.replace(/[^\n]+/g, line => {
        const trimmed = line.trim();
        // The Starting choice can contain an engine-generated action prefix.
        if (/^(?:(?:Add|Take|Put|Move|Bring|Search for|Get) )?Innate Reflexes (?:to|into|in) your hand \(Starting\)$/i.test(trimmed)) {
            return line.replace(trimmed, '타고난 반사신경을 손에 더하기 (시작 시)');
        }
        const mapped = koLabel(trimmed);
        if (mapped !== trimmed) return line.replace(trimmed, mapped);
        return line
            .replace(/\b(?:Resolve|Resolved|Play|Played|Resource|Reveal|Revealed|PutIntoPlay|Attached|Hero|Defeated|Discard|Cancel|GameOver|Enters Play)\s+x(\d+)\b/g, (match, count) => koStatistic(match.replace(/\s+x\d+$/, '')) + ' ' + count + '회')
            .replace(/\bRound (\d+) Step (\d+)\b/g, '$1라운드 · $2단계')
            .replace(/\bRound (\d+) Start\b/g, '$1라운드 시작')
            .replace(/\bRound (\d+) End\b/g, '$1라운드 종료')
            .replace(/'s Turn \((\d+)\)/g, '의 차례 ($1)')
            .replace(/\bTurn End\b/g, '차례 종료')
            .replace(/\bEnd Phase\b/g, '페이즈 종료')
            .replace(/\bPlayer Phase End\b/g, '플레이어 페이즈 종료')
            .replace(/\bVillain Phase End\b/g, '빌런 페이즈 종료')
            .replace(/\bPlayer Phase\b/g, '플레이어 페이즈')
            .replace(/\bVillain Phase\b/g, '빌런 페이즈')
            .replace(/--- Game Over ---/g, '--- 게임 종료 ---')
            .replace(/\bresolves mulligans\b/g, '멀리건 처리')
            .replace(/\bdraws (\d+) card\(s\)/g, '카드 $1장 뽑기')
            .replace(/\bwould play\b/g, '사용 예정:')
            .replace(/\bselected\b/g, '선택:')
            .replace(/\benters game area\b/g, '플레이 영역에 들어옴')
            .replace(/\bwill take (\d+) damage from\b/g, "피해 $1점 입을 예정 · 원인:")
            .replace(/\bTake (\d+) damage\b/gi, '피해 $1점 입기')
            .replace(/\bPlace (\d+) threat on the main scheme\b/gi, '주요 음모에 위협 $1 놓기')
            .replace(/\bRemove (\d+) threat from (?:a|the) scheme\b/gi, '음모에서 위협 $1 제거하기')
            .replace(/\bDeal (\d+) damage to an enemy\b/gi, '적에게 피해 $1점 입히기')
            .replace(/\bDraw (\d+) cards?\b/gi, '카드 $1장 뽑기')
            .replace(/\bDiscard (\d+) cards?\b/gi, '카드 $1장 버리기')
            .replace(/\bDiscard (\d+) cards? at random from your hand\b/g, "손에서 무작위 카드 $1장 버리기")
            .replace(/\bThis card gains surge\b/g, "이 카드는 쇄도를 얻습니다")
            .replace(/\bDiscard this obligation\b/g, "이 의무 카드를 버립니다")
            .replace(/\bDiscarded card found:/g, "버린 카드 발견:")
            .replace(/\bwould be revealed\b/g, "공개 예정")
            .replace(/\bis being revealed\b/g, "공개 중")
            .replace(/\bwas revealed\b/g, "공개됨")
            .replace(/\bis being defeated\b/g, "격파 처리 중")
            .replace(/\bwas defeated by\b/g, "격파됨 · 원인:")
            .replace(/\bwas defeated\b/g, "격파됨")
            .replace(/\bwould count boost icons\b/g, "강화 아이콘 계산 예정")
            .replace(/\bgains (\d+) boost icons\b/g, "강화 아이콘 $1개 획득")
            .replace(/\bboost icons were set to (\d+)\b/g, "강화 아이콘 $1개로 설정")
            .replace(/\bboost icons ([+-]\d+)\b/g, "강화 아이콘 $1")
            .replace(/\bmoved to revealing area\b/g, "공개 영역으로 이동")
            .replace(/\bmoved to boosting area\b/g, "강화 영역으로 이동")
            .replace(/\bmoved to boost area\b/g, "강화 영역으로 이동")
            .replace(/\b(?:was|were) discarded to\b/g, "버려짐 · 이동 위치:")
            .replace(/\bwere discarded\b/g, "버려짐")
            .replace(/\bwere returned to hand\b/g, "손으로 돌아감")
            .replace(/\bwere moved to\b/g, "이동 →")
            .replace(/\bis moving to\b/g, "이동 중 →")
            .replace(/\bwere removed from\b/g, "제거됨 · 기존 위치:")
            .replace(/\bwould be removed from game\b/g, "게임에서 제거 예정")
            .replace(/\bwere placed on table\b/g, "플레이 영역에 놓임")
            .replace(/\bwere set aside\b/g, "따로 놓아둠")
            .replace(/\b(?:was|were) flipped\b/g, "뒤집힘")
            .replace(/\bswapped\b/g, "교체됨")
            .replace(/\bis entering play\b/g, "플레이 영역에 들어오는 중")
            .replace(/\bentered play\b/g, "플레이 영역에 들어옴")
            .replace(/\bis treated as if blank\b/g, "카드의 문구가 없는 것으로 취급")
            .replace(/\bexhausted\b/g, "소진됨")
            .replace(/\breadied\b/g, "준비됨")
            .replace(/\bunequipped\b/g, "장착 해제:")
            .replace(/\bequipped\b/g, "장착:")
            .replace(/\bcancels this move\b/g, "이 이동을 취소함")
            .replace(/\bchanges the area to\b/g, "이동 위치 변경 →")
            .replace(/\beffect was canceled by\b/g, "효과 무효화 · 원인:")
            .replace(/\bwould activate against\b/g, "활성화 예정 · 대상:")
            .replace(/\bwould activate\b/g, "활성화 예정")
            .replace(/\bactivation ends\b/g, "활성화 종료")
            .replace(/\bis engaging\b/g, "교전 시작:")
            .replace(/\bengaged\b/g, "교전:")
            .replace(/\bwill scheme\b/g, "암약 예정")
            .replace(/\bwill thwart\b/g, "저지 예정:")
            .replace(/\bwill attack\b/g, "공격 예정:")
            .replace(/\bis being attacked by\b/g, "공격받는 중 · 공격자:")
            .replace(/\bdefense against\b/g, "방어 · 공격자:")
            .replace(/\bResolve this attack to\b/g, "이 공격의 대상:")
            .replace(/\bwould deal (\d+) damage to\b/g, "피해 $1점 입힐 예정 · 대상:")
            .replace(/\bgains (\d+) additional damage\b/g, "추가 피해 $1 획득")
            .replace(/\bThis attack deals indirect damage\b/g, "이 공격은 간접 피해를 입힘")
            .replace(/\bThis damage from attack is prevented\b/g, "이 공격의 피해가 방지됨")
            .replace(/\bPrevented (\d+) of this damage\b/g, "이 피해 중 $1 방지")
            .replace(/\bThe value of this damage has been updated ([+-]\d+)\b/g, "피해량 변경 $1")
            .replace(/\bExcess damage ([+-]\d+)\b/g, "초과 피해 $1")
            .replace(/\bHP reset\b/g, "생명력 초기화")
            .replace(/\bwould be completed\b/g, "달성 예정")
            .replace(/\bcompleted\b/g, "달성됨")
            .replace(/\bwould advance\b/g, "다음 단계 진행 예정")
            .replace(/\badvances?\b/g, "다음 단계 진행")
            .replace(/\bwould place (\d+)⚠/g, "위협 $1 놓을 예정")
            .replace(/\bgained (\d+)⚠/g, "위협 $1 증가")
            .replace(/\bwould remove (\d+)⚠/g, "위협 $1 제거 예정")
            .replace(/\bremoved (\d+)⚠/g, "위협 $1 제거")
            .replace(/\bThreat cannot be removed from\b/g, "위협을 제거할 수 없음 · 대상:")
            .replace(/\bgains (\d+)♡/g, "생명력 $1 회복")
            .replace(/\blost (\d+)♡/g, "생명력 $1 감소")
            .replace(/\bThis thwart will remove (\d+) additional threat\b/g, "이 저지는 추가 위협 $1 제거")
            .replace(/\bwas shuffled with\b/g, "함께 섞음:")
            .replace(/\bwas shuffled\b/g, "섞음")
            .replace(/\bare being shuffled into\b/g, "섞어 넣는 중 →")
            .replace(/\bhas run out\b/g, "소진됨")
            .replace(/\bhas been reset\b/g, "초기화됨")
            .replace(/\bwas created\b/g, "생성됨")
            .replace(/\bactivates, targets\b/g, "활성화 · 대상:")
            .replace(/\bactivates\b/g, "활성화")
            .replace(/\bwould surge against\b/g, "쇄도 예정 · 대상:")
            .replace(/\blooks at\b/g, "확인:")
            .replace(/\bgains resource\b/g, "자원 획득:")
            .replace(/\btotal (?=\d)/g, "합계 ")
            .replace(/\bSpider-Sense\b/g, "스파이더센스")
            .replace(/\bScientist\b/g, "과학자")
            .replace(/\bStunned\b/g, "기절")
            .replace(/\bConfused\b/g, "혼란")
            .replace(/\bTough\b/g, "강인함")
            .replace(/\boverkill\b/g, "압살")
            .replace(/\branged\b/g, "원거리")
            .replace(/\bpiercing\b/g, "관통")
            .replace(/\beliminated\b/g, '탈락');
    });
}
export function koHtml(html: string): string {
    const template = document.createElement('template');
    template.innerHTML = html;
    const walk = document.createTreeWalker(template.content, NodeFilter.SHOW_TEXT);
    let node: Node | null;
    while ((node = walk.nextNode())) {
        // Preserve card names and any card link attributes, icons and markup.
        if (node.parentElement?.closest('.log-card, .card, script, style, code')) continue;
        node.nodeValue = koText(node.nodeValue || '');
    }
    return template.innerHTML;
}
