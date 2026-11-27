// Korean terminology verified against physical cards and Korean Learn to Play rulebook; see docs/ko-glossary.md.
// Presentation only. Never translate engine identifiers or change gameplay timing.
export const koGlossary = {
    'basic power': '기본 기능',
    'hero action': '히어로 행동',
    'hero response': '히어로 반응',
    'forced response': '강제 반응',
    'attack': '공격',
    'indirect damage': '간접 피해',
    'attach': '장착',
    'discard': '버림',
    'spend': '소모',
    'damage unit': '점',
    'mental': '정신력',
    'physical': '물리력',
    'energy': '에너지',
    'wild': '만능',
    'aspect': '성향',
    'aggression': '용맹',
    'justice': '정의',
    'leadership': '통솔',
    'protection': '수호',
    'basic (aspect)': '기본',
    'identity': '아이덴티티',
    'ally': '동료',
    'villain': '빌런',
    'event': '이벤트',
    'upgrade': '업그레이드',
    'support': '지원',
    'attachment': '장착',
    'obligation': '의무',
    'status card': '부가 상태 카드',
    'main scheme': '주요 음모',
    'encounter set': '조우 세트',
    'modular encounter set': '모듈식 조우 세트',
    'standard encounter set': '일반 조우 세트',
    'expert encounter set': '전문가 조우 세트',
    'discard pile': '버린 카드 더미',
    'boost card': '강화 카드',
    'boost icon': '강화 아이콘',
    'hazard': '수렁',
    'acceleration': '가속',
    'crisis': '위기',
    'per player': '플레이어마다',
    'unique': '고유',
    'stage': '스테이지',
    'trigger (ability)': '격발',
    'resolve (ability)': '해결',
    'ready': '준비',
    'control': '조종',
    'consequential damage': '부수적 피해',
    'overkill': '압살',
    'guard': '경호',
    'setup': '사전 준비',
    'mulligan': '멀리건',
    'first player': '시작 플레이어',
    'threat': '위협',
    'remove threat': '위협 제거',
    'pay': '지불',
    'resource': '자원',
    'generate': '생성',
    'scientist': '과학자',
    'alter-ego': '일상',
    'recover': '회복',
    'hand size': '손 크기',
    'hit points': '생명력',
    'limit once per round': '라운드마다 1회 제한',
    'spider-sense': '스파이더센스',
    'defense': '방어',
    'thwart': '저지',
    'prevent damage': '피해 방지',
    'tough (status)': '강인함',
    'stunned (status)': '기절',
    'confused (status)': '혼란',
    'interrupt': '난입',
    'forced interrupt': '강제 난입',
    'treachery': '배반',
    'cancel': '무효화',
    'when revealed': '공개될 때',
    'encounter deck': '조우 덱',
    'exhaust': '소진',
    'uses': '사용',
    'counter': '카운터',
    'hero form': '히어로 형태',
    'stun': '기절',
    'scheme (verb)': '암약',
    'side scheme': '부가 음모',
    'nemesis': '숙적',
    'minion': '하수인',
    'engaged': '교전 중',
    'surge': '쇄도',
    'set aside': '따로 놓아둠',
    'put into play': '플레이 영역에 내려놓음'
} as const;

export function normalizeKoCardText(value: string): string {
    return value
        .replace(/기본 능력/g, koGlossary['basic power'])
        .replace(/버린 더미/g, '버린 카드 더미')
        .replace(/지배하에 플레이/g, '조종하에 플레이')
        .replace(/당신이 지배하는/g, '당신이 조종하는')
        .replace(/라운드당 (\d+)회 제한/g, '라운드마다 $1회 제한')
        .replace(/위협 (\d+)(?:점)?[을를] 제거/g, '위협을 $1만큼 제거')
        .replace(/스파이더 센스/g, koGlossary['spider-sense'])
        .replace(/예비로 둔/g, '따로 놓아둔')
        .replace(/사용 +\(/g, '사용(')
        .replace(/기본 기능을 사용한 직후/g, '기본 기능을 사용한 후,')
        .replace(/기본 기능 사용당/g, '기본 기능 사용마다')
        .replace(/((?:히어로 |일상 |강제 )?(?:행동|반응|난입)) +\((공격|방어|저지)\)/g, '$1($2)')
        // Only rewrite damage phrases with known verbs; never alter arbitrary numbers,
        // printed names, generic abilities, resource counts, or game-state identifiers.
        .replace(/피해 (\d+)(?:점)?[을를] (줍니다|입힙니다|받습니다|입습니다|받거나|입거나|주기|입히기|받기|입기|치료합니다|방지합니다|예방합니다)/g,
            (_m, n: string, verb: string) => {
                const verbs: Record<string,string> = {
                    줍니다:'입힙니다', 받습니다:'입습니다', 받거나:'입거나',
                    주기:'입히기', 받기:'입기'
                };
                return '피해 '+n+'점을 '+(verbs[verb] ?? verb);
            })
        .replace(/피해를 (받으려 할 때|받습니다|받은|받거나|주려 할 때|줍니다|준 후|줬다면)/g,
            (_m, verb: string) => {
                const verbs: Record<string,string> = {
                    '받으려 할 때':'입으려 할 때', 받습니다:'입습니다', 받은:'입은',
                    받거나:'입거나', '주려 할 때':'입히려 할 때', 줍니다:'입힙니다',
                    '준 후':'입힌 후', 줬다면:'입혔다면'
                };
                return '피해를 '+verbs[verb];
            });
}
