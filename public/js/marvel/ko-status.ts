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

// Generated scenario face, not the hidden original player card.
export function koGeneratedCard(cardType: string, id: string, name: string, inPlay: boolean) {
    if (inPlay && cardType === 'Minion' && (id === 'ultron_facedown_drone' || name === 'Drone Minion')) {
        return {name: '드론 하수인', text: '플레이어 덱에서 뒷면으로 내려놓은 카드입니다. 기본 음모·공격·체력은 각각 1입니다. Ultron 및 다른 카드의 효과에 따라 수치가 변경될 수 있습니다. 격파된 후 소유자의 버린 카드 더미에 놓습니다.'};
    }
    return undefined;
}
