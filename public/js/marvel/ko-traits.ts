// Display only; never use these labels as engine trait identifiers.
// Korean Learn to Play p.11–12 (incl. printed card examples) and Rules
// Reference p.44–46; other traits keep their English spelling until verified.
export const verifiedKoTraits: Readonly<Record<string,string>> = Object.freeze({
    "AVENGER": "AVENGER",
    "DEFENDER": "DEFENDER",
    "S.H.I.E.L.D": "S.H.I.E.L.D.",
    "BLACK PANTHER": "BLACK PANTHER",
    "GENIUS": "천재",
    "SKILL": "기술",
    "LOCATION": "장소",
    "TACTIC": "전술",
    "BRUTE": "야만",
    "CRIMINAL": "범죄자",
    "SOLDIER": "군인",
    "ARMOR": "갑옷",
    "TECH": "과학",
    "CONDITION": "상태",
    "HERO FOR HIRE": "용병 히어로",
    "AERIAL": "공중",
    "ATTACK": "공격",
    "SUPERPOWER": "슈퍼파워",
    "ITEM": "도구",
    // Doctor Strange physical Korean hero/event/upgrade faces, 2026-11-29.
    "MYSTIC": "신비술사",
    "SPELL": "주문",
    "THWART": "저지",
    "ARTIFACT": "유물",
    // Ms. Marvel physical identity faces; DEFENSE is printed in bold in her ability.
    "CHAMPION": "CHAMPION",
    "INHUMAN": "INHUMAN",
    "DEFENSE": "방어"
});

export function koTraitLabel(value: string): string {
    const key = value.replace(/^t_/i, '').trim().replace(/_/g, ' ').toUpperCase();
    const normalized = key === 'S.H.I.E.L.D.' ? 'S.H.I.E.L.D' : key;
    return Object.prototype.hasOwnProperty.call(verifiedKoTraits, normalized)
        ? verifiedKoTraits[normalized] : key;
}
