// Local, opt-in Korean text cache. Independent of engine commands and card rules.
export type KoEntry = {name: string; text?: string};
export const KO_CACHE_KEY = 'marvel-ko-cards-v1';
export const KO_SOURCE_REV = '055b6b427854287943ffa025adf8c39b44494fbf';
export const KO_PACKS = ['core','gob','cap','trors','msm','thor','twc','bkw','drs','hlk','toafk','ant','wsp','qsv','scw'];
const scenarioOnly = new Set(['gob','twc','toafk']);
const validId = /^\d{5}[a-z]?$/;
const hangul = /[가-힣]/;
export function plainKo(value: string): string {
    return value.replace(/<br\s*\/?>/gi, '\n').replace(/<hr\s*\/?>/gi, '\n────\n')
        .replace(/<[^>]*>/g, '').replace(/\[\[([^\]]+)\]\]/g,'$1')
        .replace(/&(?:nbsp|amp|quot|apos|lt|gt);/g, m => (({'&nbsp;':' ','&amp;':'＆','&quot;':'”','&apos;':'’','&lt;':'＜','&gt;':'＞'} as Record<string,string>)[m] || m))
        .replace(/\[(energy|mental|physical|wild|per_hero|boost|star|cost|acceleration|amplify|crisis|hazard|unique|per_group)\]/g,
            (m,k) => (({energy:'에너지',mental:'정신력',physical:'물리력',wild:'만능',per_hero:'플레이어당',boost:'강화 아이콘',star:'★',cost:'비용',acceleration:'가속',amplify:'증폭',crisis:'위기',hazard:'수렁',unique:'고유',per_group:'그룹당'} as Record<string,string>)[k] || m))
        .replace(/[<>&]/g, c => (({'<':'＜','>':'＞','&':'＆'} as Record<string,string>)[c] || c)).trim();
}
function safeName(value: string): string {
    return plainKo(value).replace(/['"]/g, c => c === "'" ? '’' : '”').replace(/[\r\n\\]/g,' ');
}
export function readKoCache(): Record<string,KoEntry> {
    const result: Record<string,KoEntry> = Object.create(null);
    try {
        const saved = JSON.parse(localStorage.getItem(KO_CACHE_KEY) || '{}');
        if (saved.rev !== KO_SOURCE_REV || !saved.cards || typeof saved.cards !== 'object') return result;
        for (const [id, raw] of Object.entries(saved.cards)) {
            const row = raw as KoEntry;
            if (validId.test(id) && row && typeof row.name === 'string' && typeof row.text === 'string' && hangul.test(row.text)) {
                result[id] = {name:safeName(row.name), text:plainKo(row.text)};
            }
        }
    } catch { /* unavailable storage must not prevent play */ }
    return result;
}
export function mergeKoPack(rows: unknown, allowed: Set<string>, prefix: string): Record<string,KoEntry> {
    if (!Array.isArray(rows)) throw new Error('잘못된 카드 데이터');
    const out: Record<string,KoEntry> = Object.create(null);
    for (const row of rows) {
        if (!row || typeof row.code !== 'string' || !validId.test(row.code) || !row.code.startsWith(prefix)
            || !allowed.has(row.code) || typeof row.name !== 'string' || typeof row.text !== 'string' || !hangul.test(row.text)) continue;
        const text = plainKo(row.text);
        if (hangul.test(text) && text.length <= 15000) out[row.code] = {name:safeName(row.name),text};
    }
    return out;
}
export async function importKoCards(progress: (message:string)=>void) {
    const response = await fetch('/get_cards_json?', {cache:'no-store'});
    if (!response.ok) throw new Error('게임 카드 목록을 불러올 수 없습니다.');
    const catalog = await response.json();
    const allowed = new Set<string>();
    for (const group of Object.values(catalog)) if (Array.isArray(group)) {
        for (const card of group) if (card && typeof card.card_id === 'string') allowed.add(card.card_id);
    }
    if (!allowed.size) throw new Error('게임 카드 ID가 없습니다.');
    const cards = readKoCache();
    const failures: string[] = [];
    const jobs = KO_PACKS.flatMap((pack,index) => (scenarioOnly.has(pack)?[pack+'_encounter']:[pack,pack+'_encounter'])
        .map(file=>({file,prefix:String(index+1).padStart(2,'0')})));
    let complete=0;
    // Pack codes and numeric ID ranges are pinned; don't map by name or guess faces.
    for (const job of jobs) {
        try {
            const r = await fetch('https://raw.githubusercontent.com/zzorba/marvelsdb-json-data/'+KO_SOURCE_REV+'/translations/ko/pack/'+job.file+'.json',
                {credentials:'omit',signal:AbortSignal.timeout(15000)});
            if (!r.ok) throw new Error(String(r.status));
            Object.assign(cards,mergeKoPack(await r.json(),allowed,job.prefix));
            localStorage.setItem(KO_CACHE_KEY,JSON.stringify({rev:KO_SOURCE_REV,cards}));
        } catch { failures.push(job.file); }
        progress('한국어 카드 데이터 '+(++complete)+'/'+jobs.length+' · '+Object.keys(cards).length+'개');
    }
    return {count:Object.keys(cards).length, failures};
}
