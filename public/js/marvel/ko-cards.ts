import { readKoCache, readImportedKoCache } from './ko-local.js';
import { normalizeKoCardText, normalizeImportedKoText } from './ko-glossary.js';
import { bundledKo } from './ko-bundled.js';
import { goblinDraft } from './ko-goblin.js';
import { coreEncounterDraft } from './ko-core-encounter.js';
import { wreckingCrewDraft } from './ko-wrecking-crew.js';
import { koAliases } from './ko-aliases.js';
// Core Korean display translations, terminology cross-checked against the NamuWiki mirror (Marvel Champions core cards, heroes and villains); not verified against physical Korean cards.
// Presentation only: never use these names or text as rule identifiers.
export const koCards: Record<string, {name: string; text?: string}> = {
  "07001a": {
    "name": "탈옥",
    "text": "시나리오 구성: 빌런으로 Wrecker A, Thunderball A, Piledriver A, Bulldozer A. (어려운 도전은 B버전.) Wrecker, Thunderball, Piledriver, Bulldozer 조우 덱.\n사전 준비: 응징의 날, 천둥강타, 강화하다!, 길을 비켜라 부가 음모를 플레이 영역에 내려놓습니다. Wrecker에 활성 카운터를 놓습니다. 스테이지 1B로 넘어갑니다."
  },
  "07001b": {
    "name": "탈옥",
    "text": "★ 강제 반응: 빌런 페이즈의 1단계를 해결한 후, 모든 부가 음모에 위협을 1만큼씩 놓습니다. 자신의 부가 음모에 위협이 가장 많은 빌런에게로 활성 카운터를 이동합니다(위협의 숫자가 같다면 시작 플레이어가 선택합니다).\n이 스테이지가 달성되면, 플레이어들은 게임에서 패배합니다."
  },
  "07004": {
    "name": "응징의 날",
    "text": "Wrecker의 부가 음모\nWrecker가 플레이 영역에 있는 한, 이 카드는 플레이 영역을 떠날 수 없습니다.\n강타자 - 강제 반응: 이 카드에 위협을 놓은 후, 이 카드에 놓인 위협이 10 이상이라면 모든 아군 캐릭터에게 피해를 2점씩 입힙니다. 이 음모에서 위협을 3만큼만 남기고 모두 제거합니다."
  },
  "01001a": {
    "name": "Spider-Man",
    "text": "스파이더센스 — 난입: 빌런이 당신에게 공격을 개시할 때, 카드 1장을 뽑습니다."
  },
  "01001b": {
    "name": "Peter Parker",
    "text": "과학자 — 자원: 정신력 자원을 생성합니다(라운드마다 1회 제한)."
  },
  "01002": {
    "name": "Black Cat",
    "text": "강제 반응: Black Cat을 플레이한 후, 당신의 덱 맨 위 카드 2장을 버립니다. 이렇게 버린 카드 중 인쇄된 정신력 자원이 있는 카드를 모두 손에 추가합니다."
  },
  "01003": {
    "name": "공중제비",
    "text": "난입(방어): 당신이 공격으로 피해를 입으려 할 때, 그 피해를 모두 방지합니다."
  },
  "01004": {
    "name": "향상된 스파이더센스",
    "text": "히어로 난입: 조우 덱에서 배반 카드가 공개될 때, 그 카드의 \"공개될 때\" 효과를 모두 무효화합니다."
  },
  "01005": {
    "name": "거미줄 날아차기",
    "text": "히어로 행동(공격): 적 하나에게 피해 8점을 입힙니다."
  },
  "01006": {
    "name": "Aunt May",
    "text": "일상 행동: Aunt May를 소진합니다 → Peter Parker의 피해 4를 치료합니다."
  },
  "01007": {
    "name": "스파이더 추적기",
    "text": "하수인 하나에게 장착합니다.\n강제 난입: 장착된 하수인이 격파될 때, 음모 하나에서 위협 3을 제거합니다."
  },
  "01008": {
    "name": "웹슈터",
    "text": "사용(웹 카운터 3). (카운터를 3만큼 놓은 채로 플레이 영역에 들어옵니다. 카운터가 모두 사라지면 이 카드를 버립니다).\n히어로 자원: 웹슈터를 소진하고 이 카드에서 웹 카운터를 1만큼 제거 → 만능 자원을 생성."
  },
  "01009": {
    "name": "거미줄 포획",
    "text": "히어로 형태 전용. 적 하나에게 장착합니다.\n적마다 최대 1장.\n강제 난입: 장착된 적이 공격을 하려 할 때, 대신 거미줄 포획을 버립니다.\n그리고 나서 그 적을 기절시킵니다."
  },
  "01058": {
    "name": "Daredevil",
    "text": "반응: Daredevil이 저지한 후, 적 하나에게 피해 1을 줍니다."
  },
  "01059": {
    "name": "Jessica Jones",
    "text": "플레이 영역에 있는 부가 음모마다 Jessica Jones의 저지 수치가 +1 증가합니다."
  },
  "01060": {
    "name": "정의를 위해!",
    "text": "히어로 행동(저지): 음모 하나에서 위협을 3만큼 제거합니다(이 카드에 정신력 자원을 지불했다면 대신 4만큼 제거합니다)."
  },
  "01061": {
    "name": "큰 힘에는 큰 책임이 따른다",
    "text": "히어로 난입: 음모에 위협이 놓이려 할 때, 그 대신 당신이 그만큼 피해를 받습니다."
  },
  "01062": {
    "name": "정의의 힘",
    "text": "덱당 최대 2장. 정의(노란색) 카드의 비용을 지불할 때 이 카드가 생성하는 자원 수를 두 배로 합니다."
  },
  "01063": {
    "name": "심문실",
    "text": "플레이어당 최대 1장.\n반응: 당신이 하수인을 격파한 후, 심문실을 소진합니다 → 음모 하나에서 위협 1을 제거합니다."
  },
  "01064": {
    "name": "감시팀",
    "text": "사용 (감시 카운터 3개).\n행동: 감시팀을 소진하고 감시 카운터 1개를 제거합니다 → 음모 하나에서 위협 1을 제거합니다."
  },
  "01065": {
    "name": "히어로의 직감",
    "text": "아무 플레이어의 지배하에 플레이합니다. 플레이어당 최대 1장. 당신의 히어로는 저지 수치 +1을 얻습니다."
  },
  "01083": {
    "name": "Mockingbird",
    "text": "반응: Mockingbird가 플레이 영역에 들어온 후, 적 하나를 기절시킵니다."
  },
  "01084": {
    "name": "Nick Fury",
    "text": "강제 반응: Nick Fury가 플레이 영역에 들어온 후, 하나를 선택합니다: 음모 하나에서 위협 2 제거, 카드 3장 뽑기, 적 하나에게 피해 4 주기. 라운드 종료 시 Nick Fury가 플레이 영역에 있다면 버립니다."
  },
  "01085": {
    "name": "비상사태",
    "text": "난입 (저지): 빌런이 암약할 때, 해당 음모에 놓이는 위협을 1 줄입니다."
  },
  "01086": {
    "name": "응급처치",
    "text": "행동: 아무 캐릭터 하나의 피해 2를 치료합니다."
  },
  "01087": {
    "name": "강타",
    "text": "히어로 행동 (공격): 적 하나에게 피해 3을 줍니다."
  },
  "01088": {
    "name": "에너지",
    "text": "덱당 최대 1장."
  },
  "01089": {
    "name": "천재",
    "text": "덱당 최대 1장."
  },
  "01090": {
    "name": "힘",
    "text": "덱당 최대 1장."
  },
  "01091": {
    "name": "어벤져스 맨션",
    "text": "플레이어당 최대 1장.\n행동: 어벤져스 맨션을 소진합니다 → 플레이어 하나를 선택합니다. 그 플레이어는 카드 1장을 뽑습니다."
  },
  "01092": {
    "name": "헬리캐리어",
    "text": "플레이어당 최대 1장.\n행동: 헬리캐리어를 소진합니다 → 플레이어 하나를 선택합니다. 이번 페이즈에 그 플레이어가 다음으로 플레이하는 카드의 자원 비용을 1 줄입니다."
  },
  "01093": {
    "name": "불굴의 의지",
    "text": "히어로 행동: 물리력 자원 1개를 소비하고 이 카드를 버립니다 → 당신의 히어로를 준비시킵니다."
  },
  "01094": {
    "name": "Rhino"
  },
  "01095": {
    "name": "Rhino",
    "text": "공개될 때: 조우 덱과 버린 더미에서 '부수고 챙긴다' 부가 음모를 찾아 공개합니다. 조우 덱을 섞습니다."
  },
  "01096": {
    "name": "Rhino",
    "text": "강인 (플레이 영역에 들어올 때 강인함 상태 카드 1장을 받습니다).\n공개될 때: 각 히어로를 기절시킵니다."
  },
  "01097a": {
    "name": "쳐들어간다!",
    "text": "구성: 일반 모드는 Rhino I·II, 전문가 모드는 Rhino II·III를 사용합니다. Rhino 조우 세트, 일반 조우 세트와 모듈식 조우 세트 1개(추천: 폭탄 테러)를 사용합니다.\n사전 준비: 1B 단계로 진행합니다."
  },
  "01097b": {
    "name": "쳐들어간다!",
    "text": "이 단계가 달성되면 플레이어들은 게임에서 패배합니다."
  },
  "01098": {
    "name": "무장 RHINO 슈트",
    "text": "Rhino에게 장착합니다.\n강제 난입: Rhino에게 피해를 주려 할 때, 대신 이 카드에 피해를 놓습니다. 그런 다음 이 카드에 피해가 5 이상 있다면 이 카드를 버립니다."
  },
  "01099": {
    "name": "돌격",
    "text": "Rhino에게 장착합니다. 공격 +3.\n강제 난입: Rhino가 공격할 때 그 공격에 압살을 적용합니다. 공격이 끝나면 이 카드를 버립니다."
  },
  "01100": {
    "name": "강화 코뿔",
    "text": "Rhino에게 장착합니다. 공격 +1.\n히어로 행동: 물리력 자원 3개를 소비합니다 → 이 카드를 버립니다."
  },
  "01101": {
    "name": "하이드라 용병",
    "text": "경호 (이 하수인과 교전 중인 동안 당신은 빌런을 공격할 수 없습니다)."
  },
  "01102": {
    "name": "Sandman",
    "text": "강인 (플레이 영역에 들어올 때 강인함 상태 카드 1장을 받습니다)."
  },
  "01103": {
    "name": "Shocker",
    "text": "공개될 때: 각 히어로에게 피해 1을 줍니다."
  },
  "01104": {
    "name": "버거운 상대",
    "text": "공개될 때: Rhino의 피해 4를 치료합니다. 이렇게 치료한 피해가 없다면 이 카드는 쇄도를 얻습니다."
  },
  "01105": {
    "name": "난 튼튼하다!",
    "text": "공개될 때: Rhino에게 강인함 상태 카드 1장을 줍니다. 이미 강인함 상태 카드가 있다면 이 카드는 쇄도를 얻습니다."
  },
  "01106": {
    "name": "맹진",
    "text": "공개될 때 (일상): 이 카드는 쇄도를 얻습니다.\n공개될 때 (히어로): Rhino가 당신을 공격합니다. 이 공격으로 피해를 받은 캐릭터는 기절합니다."
  },
  "01107": {
    "name": "부수고 챙긴다",
    "text": "공개될 때: 플레이어 수만큼 이 음모에 위협을 추가합니다.\n수렁 아이콘: 조우 카드 분배 단계에 카드 1장을 추가로 나눠줍니다."
  },
  "01108": {
    "name": "군중 통제",
    "text": "위기 아이콘: 이 음모가 플레이 영역에 있는 동안 주요 음모에서 위협을 제거할 수 없습니다."
  },
  "01109": {
    "name": "폭탄 테러",
    "text": "공개될 때: 플레이어 수만큼 이 음모에 위협을 추가합니다.\n가속 아이콘: 빌런 페이즈 시작 시 주요 음모에 위협 1을 추가합니다."
  },
  "01110": {
    "name": "하이드라 폭탄마",
    "text": "공개될 때: 피해 2를 받거나 주요 음모에 위협 1을 놓는 것 중 하나를 선택합니다."
  },
  "01111": {
    "name": "폭발",
    "text": "공개될 때: 폭탄 테러이 플레이 영역에 있다면 그 음모의 위협 수만큼 피해를 히어로와 동료들에게 분배합니다. 없다면 이 카드는 쇄도를 얻습니다."
  },
  "01112": {
    "name": "가짜 폭탄",
    "text": "공개될 때: 당신은 혼란 상태가 됩니다. 이미 혼란 상태라면 이 카드는 쇄도를 얻습니다."
  },
  "01165": {
    "name": "퇴거 통지",
    "text": "Peter Parker 플레이어에게 줍니다. 일상 형태로 뒤집어도 됩니다. 하나를 선택합니다:\n• Peter Parker를 소진합니다 → 이 카드를 게임에서 제거합니다.\n• 손에서 무작위 카드 1장을 버립니다. 이 카드는 쇄도를 얻습니다. 이 의무 카드를 버립니다."
  },
  "01166": {
    "name": "고속도로 강도",
    "text": "공개될 때: 각 플레이어는 자신의 손에서 무작위 카드 1장을 뒷면으로 여기에 놓습니다.\n격파될 때: 여기에 놓인 뒷면 카드들을 각 소유자의 손으로 되돌립니다.\n가속 아이콘: 빌런 페이즈 시작 시 주요 음모에 위협 1을 추가합니다."
  },
  "01167": {
    "name": "Vulture",
    "text": "속공 (이 하수인이 당신의 히어로와 교전한 후 공격합니다)."
  },
  "01168": {
    "name": "급강하 타격",
    "text": "공개될 때: 당신의 히어로를 기절시킵니다. Vulture가 플레이 영역에 있다면 이 카드는 쇄도를 얻습니다.\n강화: 이번 활성화로 아군 캐릭터에게 피해를 줬다면 그 캐릭터를 기절시킵니다."
  },
  "01169": {
    "name": "VULTURE의 계획",
    "text": "공개될 때: 각 플레이어의 손에서 무작위 카드 1장씩을 버립니다. 이렇게 버린 카드에 있는 서로 다른 자원 종류마다 주요 음모에 위협 1을 놓습니다."
  },
  "01186": {
    "name": "전진",
    "text": "공개될 때: 빌런이 암약합니다."
  },
  "01187": {
    "name": "습격",
    "text": "공개될 때 (일상): 이 카드는 쇄도를 얻습니다.\n공개될 때 (히어로): 빌런이 당신을 공격합니다."
  },
  "01188": {
    "name": "허를 찔리다",
    "text": "공개될 때: 당신이 지배하는 업그레이드 또는 지원 카드 1장을 버립니다. 이렇게 버린 카드가 없다면 이 카드는 쇄도를 얻습니다."
  },
  "01189": {
    "name": "물량공세",
    "text": "공개될 때 (일상): 이 카드는 쇄도를 얻습니다.\n공개될 때 (히어로): 빌런과 당신과 교전 중인 각 하수인이 당신을 공격합니다."
  },
  "01190": {
    "name": "과거의 그림자",
    "text": "공개될 때: 따로 놓아둔 당신의 숙적 하수인을 공개하고 당신과 교전 중인 채로 플레이 영역에 내려놓습니다. 따로 놓아둔 당신의 숙적 부가 음모를 공개하고 플레이 영역에 내려놓습니다. 따로 놓아둔 당신의 나머지 숙적 조우 세트를 조우 덱에 섞어 넣습니다. 당신의 숙적 하수인이 이렇게 게임에 들어오지 않는다면, 이 카드는 쇄도를 얻습니다."
  }
};
// Draft names and effects for the first Sinister Motives hero; compare physical Korean cards.
const sinisterDraft: Record<string, {name:string; text?:string}> = {
  "27002": {
    "name": "고스트 킥",
    "text": "히어로 반응(공격): Ghost-Spider가 기본 기능을 사용한 후, 적 하나에게 피해 6점을 입힙니다. (기본 기능 사용마다 최대 1회.)"
  },
  "27003": {
    "name": "부모로서의 조언",
    "text": "일상 행동: George Stacy가 플레이 영역에 있으면 손 또는 버린 더미의 이벤트 1장을 그에게 뒷면으로 장착합니다. 없다면 덱과 버린 더미에서 George Stacy를 찾아 손에 더하고 덱을 섞습니다."
  },
  "27004": {
    "name": "환상적인 공중제비",
    "text": "히어로 반응 (저지): Ghost-Spider가 기본 능력을 사용한 직후 음모 하나의 위협을 5 제거합니다. (기본 능력 사용당 최대 1회.)"
  },
  "27005": {
    "name": "피루엣 펀치",
    "text": "히어로 난입: 조우 덱에서 카드가 공개될 때 그 카드의 강화 아이콘 수에 1을 더한 만큼 빌런에게 피해를 줍니다. 해당 카드의 공개될 때 효과를 무효화합니다."
  },
  "27006": {
    "name": "거미줄 포박",
    "text": "필수(정신력). 히어로 난입: 적이 활성화되려 할 때 그 활성화를 무효화합니다. 이 방식으로 하수인의 활성화를 무효화했다면 그 하수인에게 피해 4를 줍니다."
  },
  "27007": {
    "name": "George Stacy",
    "text": "George Stacy에 장착된 이벤트를 손에 있는 것처럼 플레이할 수 있습니다. 행동: George Stacy를 소진 → 손의 이벤트 1장을 뒷면으로 여기에 장착합니다(최대 3장)."
  },
  "27008": {
    "name": "멀티버스행 티켓",
    "text": "행동: 이 카드를 게임에서 제거 → 손의 카드를 모두 버리고 버린 더미를 덱에 섞습니다. 손 크기에 이를 때까지 카드를 뽑고 자신이 조종하는 모든 Ghost-Spider 카드를 준비합니다."
  },
  "27009": {
    "name": "거미줄 팔찌",
    "text": "히어로 반응: 이벤트의 난입 또는 반응 능력을 해결한 후 거미줄 팔찌를 소진 → 카드 1장을 뽑습니다. (이벤트당 최대 1회.)"
  },
  "27001a": {
    "name": "Ghost-Spider",
    "text": "현란한 반사 신경 — 반응: 이벤트의 난입 또는 반응 능력을 해결한 후 Ghost-Spider를 준비합니다. (페이즈마다 1회 제한.)"
  },
  "27001b": {
    "name": "Gwen Stacy",
    "text": "행동: 버린 더미에 있는 멀티버스행 티켓을 덱에 섞거나 George Stacy를 준비하는 것 중 하나를 선택합니다. (라운드마다 1회 제한.)"
  }
};
// Seven physical Korean card faces provided 2026-11-29. Transcribe rules text,
// excluding flavor text and printed stat/keyword icons handled by the engine.
const strangeVerified: Record<string,{name:string;text:string}> = {
  "09001a": {
    "name": "Doctor Strange",
    "text": "주문 숙달 - 행동: Doctor Strange를 소진하고 비술 덱 맨 위 1장의 비용을 지불 → 그 카드의 \"특수\" 능력을 해결."
  },
  "09001b": {
    "name": "Stephen Strange",
    "text": "Stephen Strange는 비술 덱을 가지고 게임을 시작합니다(동봉된 규칙 참조).\n천부적 재능 - 행동: 비술 덱 맨 위에서 카드 1장을 버립니다(페이즈마다 1회 제한)."
  },
  "09003": {
    "name": "영적 투영",
    "text": "히어로 행동(저지): 음모 하나를 선택 → 그 음모에서 위협을 3만큼 제거하고 조우 덱 맨 위 1장을 살펴봄. 살펴본 카드에 있는 강화 아이콘마다 선택한 음모에서 위협을 추가로 1만큼 제거."
  },
  "09005": {
    "name": "미스틱 아츠의 달인",
    "text": "히어로 행동: 비술 덱 맨 위 1장의 인쇄된 비용을 지불 → 그 카드의 \"특수\" 능력을 해결. 그러고 나서 그 카드를 다시 비술 덱 맨 위에 앞면으로 놓음."
  },
  "09009": {
    "name": "공중부양 망토",
    "text": "당신은 공중 특성을 얻습니다.\n히어로 행동: 공중부양 망토를 소진 → Doctor Strange를 준비."
  },
  "09029": {
    "name": "다크 디멘션 차원 연결",
    "text": "공개될 때: 이 음모 아래에 비술 덱 맨 위 1장을 뒷면으로 놓습니다.\n격파될 때: 이 카드 아래에 있는 비술 카드를 비술 덱에 섞어 넣습니다."
  },
  "09031": {
    "name": "최면",
    "text": "공개될 때 (일상): 당신의 손에서 가장 비용이 높은 카드 1장을 버립니다. 그 카드에 인쇄된 비용만큼 주요 음모에 위협을 놓습니다.\n공개될 때 (히어로): 당신의 손에서 가장 비용이 높은 카드 1장을 버립니다. 당신은 그 카드에 인쇄된 비용만큼 피해를 입습니다."
  }
};
// Three Wrecking Crew physical scheme cards provided 2026-11-29.
const wreckingVerified: Record<string,{name:string;text:string}> = {
  "07019": {
    "name": "천둥강타",
    "text": "Thunderball의 부가 음모\nThunderball이 플레이 영역에 있는 한, 이 카드는 플레이 영역을 떠날 수 없습니다.\n감마 블래스트 - 강제 반응: 이 카드에 위협을 놓은 후, 이 카드에 놓인 위협이 10 이상이라면 모든 아군 캐릭터를 기절시킵니다. 이 음모에서 위협을 3만큼만 남기고 모두 제거합니다."
  },
  "07034": {
    "name": "강화하다!",
    "text": "Piledriver의 부가 음모\nPiledriver가 플레이 영역에 있는 한, 이 카드는 플레이 영역을 떠날 수 없습니다.\n파일 드라이브 - 강제 반응: 이 카드에 위협을 놓은 후, 이 카드에 놓인 위협이 10 이상이라면 각 플레이어는 자신이 조종하는 업그레이드나 지원 중 비용이 가장 높은 카드를 버립니다. 이 음모에서 위협을 3만큼만 남기고 모두 제거합니다."
  },
  "07048": {
    "name": "길을 비켜라",
    "text": "Bulldozer의 부가 음모\nBulldozer가 플레이 영역에 있는 한, 이 카드는 플레이 영역을 떠날 수 없습니다.\n돌격! - 강제 반응: 이 카드에 위협을 놓은 후, 이 카드에 놓인 위협이 10 이상이라면 각 플레이어는 반드시 자신의 덱 맨 위 10장을 버려야 합니다. 이 음모에서 위협을 3만큼만 남기고 모두 제거합니다."
  }
};
// Ms. Marvel physical Korean identity faces, 2026-11-29.
const msMarvelVerified: Record<string,{name:string;text:string}> = {
  "05001a": {
    "name": "Ms. Marvel",
    "text": "신체 변형 - 반응: 당신이 공격이나 저지, 방어 이벤트를 플레이한 후, Ms. Marvel을 소진 → 그 이벤트를 당신의 손으로 되돌림."
  },
  "05001b": {
    "name": "Kamala Khan",
    "text": "십대 감성 - 행동: Ms. Marvel 카드가 버려질 때까지 당신의 덱 맨 위 카드를 버립니다. 그러고 나서 그 카드를 당신의 손에 더합니다(라운드마다 1회 제한)."
  }
};
const exactPhysical = {...strangeVerified, ...wreckingVerified, ...msMarvelVerified};
export const bundledKoCount = Object.keys(bundledKo).length;
const reviewedDrafts = {...coreEncounterDraft, ...goblinDraft, ...wreckingCrewDraft, ...sinisterDraft};
// Only photographed faces are marked physically verified.
const physicalVerified = new Set(['07001a','07001b','07004','01005','02021','27002','01004','01008','01009','01186','01190','01003','01001a','01060','01001b',...Object.keys(exactPhysical)]);
const normalizedCards: Record<string, {name:string;text?:string}> = Object.create(null);
const draftCards = {...reviewedDrafts, ...koCards, ...exactPhysical};
const sources: Record<string,'verified'|'imported'|'community'|'draft'> = Object.create(null);
export function refreshKoCards() {
    const localCards = {...readKoCache(), ...bundledKo};
    const imported = readImportedKoCache();
    for (const id of Object.keys(normalizedCards)) delete normalizedCards[id];
    for (const id of Object.keys(sources)) delete sources[id];
    for (const id of new Set([...Object.keys(draftCards), ...Object.keys(localCards), ...Object.keys(imported)])) {
    const verified = physicalVerified.has(id);
    const fromPack = !verified && Object.prototype.hasOwnProperty.call(imported,id);
    const community = !verified && !fromPack && Object.prototype.hasOwnProperty.call(localCards,id);
    const entry = (verified ? draftCards[id] : fromPack ? imported[id] : community ? localCards[id] : draftCards[id]) ?? localCards[id];
    if (!entry) continue;
    normalizedCards[id] = {name:entry.name, text:entry.text === undefined ? undefined : (community || Object.prototype.hasOwnProperty.call(exactPhysical,id) ? entry.text : fromPack ? normalizeImportedKoText(entry.text) : normalizeKoCardText(entry.text))};
    sources[id] = verified ? 'verified' : fromPack ? 'imported' : community ? 'community' : 'draft';
    }
}
refreshKoCards();
// Reprints inherit the original description only when no exact-ID translation exists.
function originalId(id: string): string {
    const seen = new Set<string>();
    while (!normalizedCards[id] && Object.prototype.hasOwnProperty.call(koAliases,id) && !seen.has(id)) {
        seen.add(id); id=koAliases[id];
    }
    return id;
}
export function koCard(id: string) { return normalizedCards[originalId(id)]; }
export function koCardSource(id: string) {
    const original=originalId(id);
    if (original !== id && normalizedCards[original]) return 'reprint';
    return sources[id];
}
