// Display-only labels; engine commands and card data must never be translated.
const labels: Record<string, string> = {
  "Initialize": "초기화",
  "Scenario Setup": "시나리오 준비",
  "Resolve Mulligans": "멀리건 처리",
  "Init Finished": "준비 완료",
  "Player Turn": "플레이어 턴",
  "Player Turn End": "플레이어 턴 종료",
  "Main Scheme Place Threat": "주요 음모에 위협 놓기",
  "Enemy Activation": "적 활성화",
  "Deal Encounter Cards": "조우 카드 나눠주기",
  "Reveal Encounter Cards": "조우 카드 공개",
  "End Phase": "단계 종료",
  "End Round": "라운드 종료",
  "Start Round": "라운드 시작",
  "Game Over": "게임 종료",
  "Player Phase": "플레이어 단계",
  "Villain Phase": "빌런 단계",
  "Player Phase End": "플레이어 단계 종료",
  "Villain Phase End": "빌런 단계 종료",
  "Cost": "비용",
  "Targets": "대상",
  "ChooseAbility": "능력 선택",
  "Choose Ability": "능력 선택",
  "Game Rule": "게임 규칙",
  "Ally Limit": "동료 제한",
  "Play": "사용",
  "Play 1": "사용 1",
  "Play 2": "사용 2",
  "Attack": "공격",
  "Thwart": "저지",
  "Defense": "방어",
  "Recover": "회복",
  "Change Form": "형태 변경",
  "Action": "행동",
  "Action 1": "행동 1",
  "Hero Action": "영웅 행동",
  "Alter-Ego Action": "일상 행동",
  "First Player Action": "첫 플레이어 행동",
  "Forced Action": "강제 행동",
  "Response": "반응",
  "Hero Response": "영웅 반응",
  "Alter-Ego Response": "일상 반응",
  "Forced Response": "강제 반응",
  "Interrupt": "중단",
  "Hero Interrupt": "영웅 중단",
  "Alter-Ego Interrupt": "일상 중단",
  "Forced Interrupt": "강제 중단",
  "Resource": "자원",
  "Special": "특수",
  "When Defeated": "쓰러졌을 때",
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
  "End<br/>Interrupt": "중단<br/>종료",
  "End<br/>Defense": "방어<br/>종료",
  "End<br/>Turn": "턴<br/>종료",
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
  "Auto Targeting": "자동 대상 선택",
  "Auto Activate": "자동 활성화",
  "Show Auto Activate Checkbox": "자동 활성화 체크 표시",
  "Auto Pause": "자동 일시정지",
  "Sort Hand": "손패 정렬",
  "By ID": "번호순",
  "By Type": "종류순",
  "Sort Area": "영역 정렬",
  "By Name": "이름순",
  "Restart Turn": "턴 다시 시작",
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
  "Please wait": "잠시 기다려 주세요"
};
export function koLabel(value: string): string {
    return Object.prototype.hasOwnProperty.call(labels, value) ? labels[value] : value;
}
export function koText(value: string): string {
    const direct = koLabel(value);
    if (direct !== value) return direct;
    return value.replace(/[^\n]+/g, line => {
        const trimmed = line.trim();
        const mapped = koLabel(trimmed);
        if (mapped !== trimmed) return line.replace(trimmed, mapped);
        return line
            .replace(/\bRound (\d+) Step (\d+)\b/g, '$1라운드 · $2단계')
            .replace(/\bRound (\d+) Start\b/g, '$1라운드 시작')
            .replace(/\bRound (\d+) End\b/g, '$1라운드 종료')
            .replace(/'s Turn \((\d+)\)/g, '의 턴 ($1)')
            .replace(/\bTurn End\b/g, '턴 종료')
            .replace(/\bEnd Phase\b/g, '단계 종료')
            .replace(/\bPlayer Phase End\b/g, '플레이어 단계 종료')
            .replace(/\bVillain Phase End\b/g, '빌런 단계 종료')
            .replace(/\bPlayer Phase\b/g, '플레이어 단계')
            .replace(/\bVillain Phase\b/g, '빌런 단계')
            .replace(/--- Game Over ---/g, '--- 게임 종료 ---')
            .replace(/\bresolves mulligans\b/g, '멀리건 처리')
            .replace(/\bdraws (\d+) card\(s\)/g, '카드 $1장 뽑기')
            .replace(/\bwould play\b/g, '사용 예정:')
            .replace(/\bselected\b/g, '선택:')
            .replace(/\benters game area\b/g, '게임 영역에 들어옴')
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
