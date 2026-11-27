// Korean Learn to Play p. 3 card text; p. 24 explains resolution. No rule changes.
const statusCards: Record<string, {name: string; text: string}> = {
    Tough: {name: '강인함', text: '이 캐릭터가 피해를 입으려 하면, 대신 이 카드를 버립니다.'},
    Stunned: {name: '기절', text: '이 캐릭터가 공격하려 하면, 대신 이 카드를 버립니다.'},
    Confused: {name: '혼란', text: '이 캐릭터가 저지하려 하거나 암약하려 하면, 대신 이 카드를 버립니다.'}
};
export function koStatusCard(cardType: string, name: string) {
    return cardType === 'StatusCard' && Object.prototype.hasOwnProperty.call(statusCards, name)
        ? statusCards[name] : undefined;
}
