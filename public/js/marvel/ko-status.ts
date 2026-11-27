// Display-only descriptions for public status cards. No rule changes.
const statusCards: Record<string, {name: string; text: string}> = {
    Tough: {name: '강인함', text: '이 캐릭터가 다음에 피해를 입으려 할 때, 그 피해를 모두 방지하고 대신 이 부가 상태 카드를 버립니다.'},
    Stunned: {name: '기절', text: '이 캐릭터가 다음에 공격하려 할 때, 공격하는 대신 이 부가 상태 카드를 버립니다.'},
    Confused: {name: '혼란', text: '이 캐릭터가 다음에 저지하거나 암약하려 할 때, 그 행동 대신 이 부가 상태 카드를 버립니다.'}
};
export function koStatusCard(cardType: string, name: string) {
    return cardType === 'StatusCard' && Object.prototype.hasOwnProperty.call(statusCards, name)
        ? statusCards[name] : undefined;
}
