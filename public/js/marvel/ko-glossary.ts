// Korean terminology verified against owner-provided physical cards 01005, 02021, 27002.
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
    'damage unit': '점'
} as const;

export function normalizeKoCardText(value: string): string {
    return value
        .replace(/기본 능력/g, koGlossary['basic power'])
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
