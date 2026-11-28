"""Mobile landscape UI regression with a real local Python game server."""
import os
import re
import time
import unittest
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import quote
from playwright.sync_api import sync_playwright, expect

BASE = "http://127.0.0.1:2345"
OUT = Path(os.environ.get("MOBILE_TEST_OUTPUT", "test-results/mobile"))
OUT.mkdir(parents=True, exist_ok=True)
expect.set_options(timeout=20000)


class MobileRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        deadline = time.monotonic() + 120
        while True:
            try:
                with urlopen(BASE + "/get_version", timeout=2) as response:
                    cls.version = response.read().decode().strip()
                if cls.version:
                    break
            except Exception:
                pass
            if time.monotonic() > deadline:
                raise RuntimeError("Game server did not become ready; inspect server.log")
            time.sleep(1)
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.context = self.browser.new_context(
            viewport={"width": 915, "height": 412},
            screen={"width": 915, "height": 412},
            is_mobile=True, has_touch=True, device_scale_factor=2,
            user_agent="Mozilla/5.0 (Linux; Android 17; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36 MarvelAndroid",
            locale="ko-KR",
        )
        self.context.tracing.start(screenshots=True, snapshots=True, sources=True)
        self.page = self.context.new_page()
        self.page.set_default_timeout(25000)
        self.errors = []
        self.console = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.on("console", lambda msg: self.console.append(f"{msg.type}: {msg.text}"))
        self.page.on("requestfailed", lambda request: self.console.append(f"requestfailed: {request.url} {request.failure}"))

    def tearDown(self):
        name = self._testMethodName
        try:
            self.page.screenshot(path=str(OUT / f"{name}.png"), timeout=8000, animations="disabled")
        except Exception as exc:
            self.console.append(f"screenshot failed: {exc}")
        try:
            self.context.tracing.stop(path=str(OUT / f"{name}.zip"))
        finally:
            (OUT / f"{name}.log").write_text("\n".join(self.console + self.errors), encoding="utf-8")
            self.context.close()

    def goto(self, path):
        sep = "&" if "?" in path else "?"
        # The version endpoint sets the real browser cookie; urllib's health
        # probe has no shared browser cookie jar.
        response = self.context.request.get(BASE + "/get_version")
        self.assertTrue(response.ok)
        self.page.goto(BASE + path + sep + "v=" + quote(self.version, safe=""))
        self.page.wait_for_function("navigator.maxTouchPoints > 0")

    def bounds(self, locator):
        expect(locator).to_be_visible()
        rect = locator.bounding_box()
        viewport = self.page.viewport_size
        self.assertIsNotNone(rect)
        self.assertGreater(rect["width"], 0)
        self.assertGreater(rect["height"], 0)
        self.assertGreaterEqual(rect["x"], -1)
        self.assertGreaterEqual(rect["y"], -1)
        self.assertLessEqual(rect["x"] + rect["width"], viewport["width"] + 1)
        self.assertLessEqual(rect["y"] + rect["height"], viewport["height"] + 1)

    def screenshot(self, label):
        self.page.screenshot(path=str(OUT / f"{self._testMethodName}-{label}.png"), animations="disabled")

    def open_setup(self):
        self.goto("/main")
        self.page.wait_for_function("document.querySelector('.brand-emblem').naturalWidth === 804")
        self.bounds(self.page.locator(".brand-emblem"))
        self.page.get_by_role("button", name="새 게임", exact=True).tap()
        self.page.wait_for_function("window.setupCatalogReady === true", timeout=90000)
        self.page.locator('#set-images > .set[data-package*="Core Set"]').first.tap()
        rhino = self.page.locator('#set-content button[data-caption="Rhino"][data-mode="일반"]').first
        expect(rhino).to_be_visible()
        rhino.tap()
        expect(self.page.locator(".ml-scenario-name")).to_have_text("Rhino")
        expect(self.page.locator(".ml-scenario-mode")).to_have_text("일반 모드")
        self.bounds(self.page.locator(".ml-footer .ml-primary"))
        return rhino

    def test_home_menu_alignment(self):
        self.goto("/main")
        logo = self.page.locator(".brand-emblem")
        # Verify the real bundled PNG rather than the synthetic card cache.
        response = self.context.request.get(BASE + "/public/images/home/champions.png")
        self.assertTrue(response.ok)
        self.assertEqual(response.body(), (Path(__file__).resolve().parents[2] /
                         "public/images/home/champions.png").read_bytes())
        self.page.wait_for_function("""() => {
            const img = document.querySelector('.brand-emblem');
            return img.complete && img.naturalWidth === 804 && img.naturalHeight === 435;
        }""")
        self.bounds(logo)
        backdrop = Path(__file__).resolve().parents[2] / "public/images/home/doom.webp"
        if backdrop.exists():
            response = self.context.request.get(BASE + "/public/images/home/doom.webp")
            self.assertTrue(response.ok)
            self.assertEqual(response.body(), backdrop.read_bytes())
        self.assertEqual(self.page.locator("body").evaluate(
            "(el) => getComputedStyle(el).getPropertyValue('--mc-accent').trim()"), "#2e6b57")
        buttons = self.page.locator(".main .custom-btn")
        expect(buttons).to_have_count(8)
        for button in buttons.all():
            self.bounds(button)
            result = button.evaluate("""el => {
                const b = el.getBoundingClientRect();
                const s = el.querySelector('span').getBoundingClientRect();
                return [Math.abs((b.left+b.right-s.left-s.right)/2),
                        Math.abs((b.top+b.bottom-s.top-s.bottom)/2),
                        b.height];
            }""")
            self.assertLessEqual(result[0], 1)
            self.assertLessEqual(result[1], 1)
            self.assertGreaterEqual(result[2], 42)
        self.assertEqual(self.errors, [])
        self.screenshot("home-redesign")

    def test_ko_status_and_statistics(self):
        self.goto("/main")
        result = self.page.evaluate("""async () => {
            const {koStatusCard} = await import('/public/js/marvel/ko-status.js');
            const {koLabel, koStatistic, koHtml} = await import('/public/js/marvel/ko-game.js');
            return {cards:['Tough','Stunned','Confused'].map(n=>koStatusCard('StatusCard',n)),
                other:koStatusCard('Event','Tough') === undefined,
                title:koLabel('STATISTIC'),
                events:['Resolve','Resolved','Enters Play','Resource','Defeated'].map(koStatistic),
                html:koHtml('<span data-id="Resolved">Resolved x2</span>')};
        }""")
        self.assertEqual([c["name"] for c in result["cards"]], ["강인함", "기절", "혼란"])
        self.assertTrue(all("버립니다" in c["text"] for c in result["cards"]))
        self.assertTrue(result["other"])
        self.assertEqual(result["title"], "통계")
        self.assertEqual(result["events"], ["효과 처리", "효과 처리 완료", "플레이 영역에 들어옴", "자원으로 사용", "격파"])
        self.assertEqual(result["html"], '<span data-id="Resolved">효과 처리 완료 2회</span>')

    def test_ko_dynamic_choices(self):
        self.goto("/main")
        result = self.page.evaluate("""async () => {
            const {koHtml} = await import('/public/js/marvel/ko-game.js');
            return ['Take 2 damage', 'Place 1 threat on the main scheme',
                    '<u>하이드라 폭탄마</u> was revealed', 'Draw 3 cards'].map(koHtml);
        }""")
        self.assertEqual(result, ['피해 2점 입기', '주요 음모에 위협 1 놓기',
                                  '<u>하이드라 폭탄마</u> 공개됨', '카드 3장 뽑기'])

    def test_ko_engine_messages(self):
        self.goto("/main")
        result = self.page.evaluate("""async () => {
            const {koHtml} = await import('/public/js/marvel/ko-game.js');
            return [
                '<a class="log-card" data-id="19">Rhino</a> will attack <u>Spider-Man</u> (+0)',
                '<u>Spider-Man</u> will take 3 damage from <u>Rhino</u>',
                '<u>Rhino</u> was defeated',
                'Encounter Deck was shuffled',
                '<u>Spider-Man</u> readied',
                '<u>하이드라 폭탄마</u> is being revealed',
                'Exhaust Peter Parker → remove Eviction Notice from the game',
                'Unknown future text'
            ].map(koHtml);
        }""")
        self.assertEqual(result, [
            '<a class="log-card" data-id="19">Rhino</a> 공격 예정: <u>Spider-Man</u> (+0)',
            '<u>Spider-Man</u> 피해 3점 입을 예정 · 원인: <u>Rhino</u>',
            '<u>Rhino</u> 격파됨',
            'Encounter Deck 섞음',
            '<u>Spider-Man</u> 준비됨',
            '<u>하이드라 폭탄마</u> 공개 중',
            'Peter Parker 소진 → 퇴거 통지를 게임에서 제거',
            'Unknown future text',
        ])

    def test_ko_verified_glossary(self):
        self.goto("/main")
        result = self.page.evaluate("""async () => {
            const {koCard,koCardSource} = await import('/public/js/marvel/ko-cards.js');
            const {normalizeKoCardText} = await import('/public/js/marvel/ko-glossary.js');
            const ids = ['01005','02021','27002'];
            const text = '히어로 반응 (공격): 기본 능력을 사용한 직후 적에게 피해 6을 줍니다. (기본 능력 사용당 최대 1회.)';
            const normalized = normalizeKoCardText(text);
            return {cards:ids.map(koCard), sources:ids.map(koCardSource),
                duplicate:koCardSource('02034'), normalized,
                idempotent:normalized === normalizeKoCardText(normalized),
                unchanged:normalizeKoCardText('반응 능력 1개를 해결합니다. 카드 3장. 피해량만큼 위협을 놓습니다.'),
                other:koCard('01087').text};
        }""")
        self.assertEqual(result["sources"], ["verified"] * 3)
        self.assertEqual(result["duplicate"], "draft")
        self.assertEqual(result["cards"][0]["text"], "히어로 행동(공격): 적 하나에게 피해 8점을 입힙니다.")
        self.assertEqual(result["cards"][1]["text"], "빌런에게 장착합니다.\\n★ 강제 반응: 빌런이 당신을 공격한 후, 호박 폭탄을 버리고 당신은 간접 피해 2점을 입습니다.\\n히어로 행동: 물리력 자원 2개를 소모 → 이 카드를 버림.".replace("\\n", "\n"))
        self.assertEqual(result["cards"][2]["text"], "히어로 반응(공격): Ghost-Spider가 기본 기능을 사용한 후, 적 하나에게 피해 6점을 입힙니다. (기본 기능 사용마다 최대 1회.)")
        self.assertEqual(result["normalized"], "히어로 반응(공격): 기본 기능을 사용한 후, 적에게 피해 6점을 입힙니다. (기본 기능 사용마다 최대 1회.)")
        self.assertTrue(result["idempotent"])
        self.assertEqual(result["unchanged"], "반응 능력 1개를 해결합니다. 카드 3장. 피해량만큼 위협을 놓습니다.")
        self.assertIn("피해 3점을 입힙니다", result["other"])

    def test_ko_additional_physical_cards(self):
        self.goto("/main")
        result = self.page.evaluate("""async () => {
            const {koCard,koCardSource} = await import('/public/js/marvel/ko-cards.js');
            const {normalizeKoCardText,koGlossary} = await import('/public/js/marvel/ko-glossary.js');
            const ids = ['01004','01008','01009','01186','01190'];
            return {texts:ids.map(id=>koCard(id).text), sources:ids.map(koCardSource),
                scheme:koGlossary['scheme (verb)'],
                normalized:normalizeKoCardText('예비로 둔 카드. 사용 (카운터 3).')};
        }""")
        self.assertEqual(result["sources"], ["verified"] * 5)
        self.assertIn('그 카드의 "공개될 때" 효과를 모두 무효화합니다', result["texts"][0])
        self.assertIn("카운터가 모두 사라지면 이 카드를 버립니다", result["texts"][1])
        self.assertIn("대신 거미줄 포획을 버립니다", result["texts"][2])
        self.assertEqual(result["texts"][3], "공개될 때: 빌런이 암약합니다.")
        self.assertIn("따로 놓아둔 당신의 숙적 하수인", result["texts"][4])
        self.assertIn("이 카드는 쇄도를 얻습니다", result["texts"][4])
        self.assertEqual(result["scheme"], "암약")
        self.assertEqual(result["normalized"], "따로 놓아둔 카드. 사용(카운터 3).")

    def test_ko_spider_man_physical_cards(self):
        self.goto("/main")
        result = self.page.evaluate("""async () => {
            const {koCard,koCardSource} = await import('/public/js/marvel/ko-cards.js');
            const {koLabel} = await import('/public/js/marvel/ko-game.js');
            const {koGlossary} = await import('/public/js/marvel/ko-glossary.js');
            return {hero:koCard('01001a').text, defense:koCard('01003').text,
                sources:['01001a','01003'].map(koCardSource),
                label:koLabel('Spider-Sense'),
                status:['tough (status)','stunned (status)','confused (status)'].map(k=>koGlossary[k])};
        }""")
        self.assertEqual(result["hero"], "스파이더센스 — 난입: 빌런이 당신에게 공격을 개시할 때, 카드 1장을 뽑습니다.")
        self.assertEqual(result["defense"], "난입(방어): 당신이 공격으로 피해를 입으려 할 때, 그 피해를 모두 방지합니다.")
        self.assertEqual(result["sources"], ["verified"] * 2)
        self.assertEqual(result["label"], "스파이더센스")
        self.assertEqual(result["status"], ["강인함", "기절", "혼란"])

    def test_ko_justice_and_peter_parker(self):
        self.goto("/main")
        result = self.page.evaluate("""async () => {
            const {koCard,koCardSource} = await import('/public/js/marvel/ko-cards.js');
            const {normalizeKoCardText,koGlossary} = await import('/public/js/marvel/ko-glossary.js');
            return {justice:koCard('01060').text, peter:koCard('01001b').text,
                sources:['01060','01001b'].map(koCardSource),
                normalized:normalizeKoCardText('위협 3을 제거합니다. (라운드당 1회 제한.)'),
                unchanged:normalizeKoCardText('위협 3을 놓습니다. 위협을 2만큼 제거합니다.'),
                recover:koGlossary['recover']};
        }""")
        self.assertEqual(result["justice"], "히어로 행동(저지): 음모 하나에서 위협을 3만큼 제거합니다(이 카드에 정신력 자원을 지불했다면 대신 4만큼 제거합니다).")
        self.assertEqual(result["peter"], "과학자 — 자원: 정신력 자원을 생성합니다(라운드마다 1회 제한).")
        self.assertEqual(result["sources"], ["verified"] * 2)
        self.assertEqual(result["normalized"], "위협을 3만큼 제거합니다. (라운드마다 1회 제한.)")
        self.assertEqual(result["unchanged"], "위협 3을 놓습니다. 위협을 2만큼 제거합니다.")
        self.assertEqual(result["recover"], "회복")

    def test_ko_rulebook_terminology(self):
        self.goto("/main")
        result = self.page.evaluate("""async () => {
            const {koGlossary,normalizeKoCardText} = await import('/public/js/marvel/ko-glossary.js');
            const {koLabel} = await import('/public/js/marvel/ko-game.js');
            const {koStatusCard} = await import('/public/js/marvel/ko-status.js');
            const {plainKo} = await import('/public/js/marvel/ko-local.js');
            return {
                resources:['mental','physical','energy','wild'].map(k=>koGlossary[k]),
                aspects:['Aggression','Justice','Leadership','Protection'].map(koLabel),
                statuses:['Tough','Stunned','Confused'].map(k=>koStatusCard('StatusCard',k).text),
                sets:['Standard Set','Expert Set','Modular Set'].map(koLabel),
                symbols:plainKo('[mental] [physical] [energy] [wild] [per_hero]'),
                normalized:normalizeKoCardText('당신이 지배하는 카드. 버린 더미.')
            };
        }""")
        self.assertEqual(result["resources"], ["정신력","물리력","에너지","만능"])
        self.assertEqual(result["aspects"], ["용맹","정의","통솔","수호"])
        self.assertEqual(result["statuses"], ["이 캐릭터가 피해를 입으려 하면, 대신 이 카드를 버립니다.",
            "이 캐릭터가 공격하려 하면, 대신 이 카드를 버립니다.",
            "이 캐릭터가 저지하려 하거나 암약하려 하면, 대신 이 카드를 버립니다."])
        self.assertEqual(result["sets"], ["일반 조우 세트","전문가 조우 세트","모듈식 조우 세트"])
        self.assertEqual(result["symbols"], "정신력 물리력 에너지 만능 플레이어마다")
        self.assertEqual(result["normalized"], "당신이 조종하는 카드. 버린 카드 더미.")

    def test_ko_rules_reference_keywords(self):
        self.goto("/main")
        result = self.page.evaluate("""async () => {
            const {koKeywords,koKeywordLabel,koGlossary} = await import('/public/js/marvel/ko-glossary.js');
            const {koLabel} = await import('/public/js/marvel/ko-game.js');
            return {count:Object.keys(koKeywords).length,
                labels:['Toughness','Tough','Steady','Stalwart','Hinder 2','Retaliate 1','Incite X','Victory 3','Teamwork(Goblin)','Requirement(mental)','Uses(web 3)'].map(koLabel),
                timing:[koGlossary.then,koGlossary.instead,koGlossary['triggering condition']],
                untouched:koKeywordLabel('Retaliate 1 after attacking') === undefined,
                shared:Object.entries(koKeywords).every(([key,value])=>koLabel(key)===value)};
        }""")
        self.assertEqual(result["count"], 26)
        self.assertEqual(result["labels"], ["강인","강인함","의연","견고","교란 2","반격 1","진척 X","승점 3","팀워크(Goblin)","필수(mental)","사용(web 3)"])
        self.assertEqual(result["timing"], ["그러고 나서","대신","격발 조건"])
        self.assertTrue(result["untouched"])
        self.assertTrue(result["shared"])

    def test_ko_core_encounters_and_reprints(self):
        self.goto("/main")
        result = self.page.evaluate("""async () => {
            const {koCard,koCardSource} = await import('/public/js/marvel/ko-cards.js');
            const {koAliases} = await import('/public/js/marvel/ko-aliases.js');
            const {coreEncounterDraft} = await import('/public/js/marvel/ko-core-encounter.js');
            return {aliases:Object.keys(koAliases).length, drafts:Object.keys(coreEncounterDraft).length,
                klaw:koCard('01116a').name, ultron:koCard('01138a').name,
                reprint:koCard('08014').name, original:koCard('01062').name,
                source:koCardSource('08014'), unknown:koCard('99999')===undefined};
        }""")
        self.assertEqual(result["aliases"], 80)
        self.assertEqual(result["drafts"], 61)
        self.assertEqual(result["klaw"], "지하 경제")
        self.assertEqual(result["ultron"], "NORAD 습격")
        self.assertEqual(result["reprint"], result["original"])
        self.assertEqual(result["source"], "reprint")
        self.assertTrue(result["unknown"])

    def test_ko_bundled_module(self):
        self.goto("/main")
        result = self.page.evaluate("""async () => {
            const {bundledKo} = await import('/public/js/marvel/ko-bundled.js');
            const {koCard, bundledKoCount} = await import('/public/js/marvel/ko-cards.js');
            return {count:bundledKoCount, size:Object.keys(bundledKo).length,
                core:koCard('01001a').name, sample:koCard('03001a')?.text};
        }""")
        self.assertEqual(result["count"], result["size"])
        self.assertEqual(result["core"], "Spider-Man")
        if result["count"]:
            self.assertGreaterEqual(result["count"], 250)
            self.assertRegex(result["sample"], "[가-힣]")

    def test_ko_library_import_filter(self):
        # Prevent a real asynchronous download from racing the synthetic cache.
        self.page.route('https://raw.githubusercontent.com/**', lambda route: route.abort())
        self.goto("/main")
        result = self.page.evaluate("""async () => {
            const m = await import('/public/js/marvel/ko-local.js');
            const c = m.mergeKoPack([
                {code:'03001a',name:'Captain America',text:'<b>행동</b>: 카드 1장. [mental]'},
                {code:'03002',name:'English',text:'English only'},
                {code:'03003',name:'Not in engine',text:'번역'},
                {code:'04001a',name:'Other pack',text:'번역'}
            ], new Set(['03001a','03002','04001a']), '03');
            const {koCard,koCardSource,refreshKoCards} = await import('/public/js/marvel/ko-cards.js');
            localStorage.setItem(m.KO_CACHE_KEY,JSON.stringify({rev:m.KO_SOURCE_REV,cards:c}));
            refreshKoCards();
            return {ids:Object.keys(c), name:koCard('03001a')?.name, text:koCard('03001a')?.text,
                    source:koCardSource('03001a'), draft:koCard('27002')?.name, goblin:koCard('02033')?.name, core:koCard('01001a')?.name};
        }""")
        self.assertEqual(result["ids"], ["03001a"])
        self.assertEqual(result["name"], "Captain America")
        # A real offline module has priority over imported fixtures.
        if result["text"] != "행동: 카드 1장. 정신력":
            self.assertRegex(result["text"], "[가-힣]")
        self.assertEqual(result["source"], "community")
        self.assertEqual(result["draft"], "고스트 킥")
        self.assertEqual(result["goblin"], "고블린 글라이더")
        self.assertEqual(result["core"], "Spider-Man")

    def test_ko_core_dictionary(self):
        self.goto("/main")
        result = self.page.evaluate("""async () => {
            const {koCard, koCards} = await import('/public/js/marvel/ko-cards.js');
            return {count:Object.keys(koCards).filter(id=>id.startsWith('01')).length, hero:koCard('01001a').name,
                    name:koCard('01005').name, text:koCard('01005').text,
                    unknown:koCard('99999') === undefined};
        }""")
        self.assertEqual(result["count"], 59)
        self.assertEqual(result["hero"], "Spider-Man")
        self.assertEqual(result["name"], "거미줄 날아차기")
        self.assertIn("피해 8", result["text"])
        self.assertTrue(result["unknown"])

    def test_ko_wrecking_crew(self):
        self.goto("/main")
        result = self.page.evaluate("""async () => {
            const {koCard,koCardSource} = await import('/public/js/marvel/ko-cards.js');
            const ids = ['07001a','07001b',...Array.from({length:58},(_,i)=>String(i+7002).padStart(5,'0'))];
            return {missing:ids.filter(id=>!koCard(id)?.text || !/[가-힣]/.test(koCard(id).text)),
                    verified:ids.filter(id=>koCardSource(id)==='verified').sort(),
                    titles:['07019','07034','07048'].map(id=>koCard(id).name),
                    names:['07002','07017','07032','07046'].map(id=>koCard(id).name)};
        }""")
        self.assertEqual(result["missing"], [])
        self.assertEqual(result["verified"], ["07001a","07001b","07004"])
        self.assertEqual(result["titles"], ["천둥강타","강화하다!","길을 비켜라"])
        self.assertEqual(result["names"], ["Wrecker","Thunderball","Piledriver","Bulldozer"])

    def test_apk_update_refreshes_ui_and_deck_server(self):
        root=Path(__file__).resolve().parents[2]
        source=(root/'mobile/android/app/src/main/java/io/github/kkhos/marvellcg/MainActivity.java').read_text(encoding='utf-8')
        gradle=(root/'mobile/android/app/build.gradle').read_text(encoding='utf-8')
        self.assertIn('UI_REVISION = "apk-" + BuildConfig.VERSION_CODE',source)
        self.assertIn('buildConfig true',gradle)
        self.assertIn('engine/device/web/server/server_get.py',source)
        self.assertIn('!entry.getName().startsWith("public/")',source)

    def test_deck_editor_no_null_growth(self):
        self.goto("/deck")
        self.assertEqual(self.page.evaluate("document.characterSet"), "UTF-8")
        for action in ("저장", "플레이"):
            expect(self.page.get_by_role("button", name=action, exact=True)).to_have_count(1)
            expect(self.page.locator("#deck-toolbar").get_by_role("button", name=action, exact=True)).to_be_visible()
            expect(self.page.locator(f"#deck-footer input[value=\"{action}\"]")).to_be_hidden()
        expect(self.page.locator("#deck-footer").get_by_role("button", name="내보내기", exact=True)).to_be_visible()
        self.page.wait_for_function("window.cardStatistics && window.cardPreview", timeout=90000)
        self.page.evaluate("""async () => {
            hero_data=await getHeroJson('captain_america');
            hero_data.player_deck.push(null,'null','undefined');
            showDeckCards();
        }""")
        main=self.page.locator('#player_deck_images > .image-div')
        side=self.page.locator('#side_deck_images > .image-div')
        expect(main).to_have_count(25)
        expect(main.first.locator('[data-deck-action]')).to_have_count(3)
        expect(main.first.locator('[data-deck-action=move]')).to_have_attribute('aria-label','메인/사이드 덱 이동')
        expect(main.first.locator('[data-deck-action=add]')).to_have_attribute('aria-label','카드 1장 추가')
        expect(main.first.locator('[data-deck-action=remove]')).to_have_attribute('aria-label','카드 1장 제거')
        for _ in range(3):
            self.page.evaluate("""() => {
                const main=document.getElementById('player_deck_images');
                const side=document.getElementById('side_deck_images');
                side.append(main.firstElementChild);updatePeekedCardsString();
                main.prepend(side.firstElementChild);updatePeekedCardsString();
            }""")
        expect(main).to_have_count(25)
        expect(side).to_have_count(0)
        # Exercise the real touch Sortable path, not just DOM moves.
        self.page.locator('#main-deck-section').evaluate(
            "(el) => { el.scrollIntoView({block:'start'}); window.scrollBy(0,-90); }")
        before = self.page.evaluate("hero_data.player_deck.slice()")
        handle = main.first.locator('.deck-drag-handle')
        handle.scroll_into_view_if_needed()
        source = handle.bounding_box()
        target = main.nth(2).bounding_box()
        self.assertIsNotNone(source)
        self.assertIsNotNone(target)
        sx, sy = source['x']+source['width']/2, source['y']+source['height']/2
        tx, ty = target['x']+target['width']*.8, target['y']+target['height']/2
        cdp = self.context.new_cdp_session(self.page)
        try:
            cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':sx,'y':sy}]})
            self.page.wait_for_timeout(180)
            for i in range(1,13):
                cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':sx+(tx-sx)*i/12,'y':sy+(ty-sy)*i/12}]})
                self.page.wait_for_timeout(25)
            cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
        finally:
            cdp.detach()
        self.page.wait_for_function("before => JSON.stringify(hero_data.player_deck) !== JSON.stringify(before)", arg=before)
        self.assertCountEqual(self.page.evaluate("hero_data.player_deck"),before)
        expect(main).to_have_count(25)
        # Simulate an unexpected duplicate left by a drag implementation.
        self.page.evaluate("""() => {
            beginDeckDrag();
            const zone=document.getElementById('player_deck_images');
            zone.append(zone.firstElementChild.cloneNode(true));
            finishDeckDrag();
        }""")
        expect(main).to_have_count(25)
        self.assertCountEqual(self.page.evaluate("hero_data.player_deck"),before)
        main.first.locator('[data-deck-action=move]').tap()
        expect(main).to_have_count(24)
        expect(side).to_have_count(1)
        side.first.locator('[data-deck-action=move]').tap()
        expect(main).to_have_count(25)
        main.first.locator('[data-deck-action=add]').tap()
        expect(main).to_have_count(26)
        main.first.locator('[data-deck-action=remove]').tap()
        expect(main).to_have_count(25)
        state=self.page.evaluate("""() => ({ids:hero_data.player_deck,side:hero_data.side_deck,
            fixed:hero_data.hero_deck.length,slots:document.getElementById('slots').value})""")
        self.assertEqual(len(state['ids']),25)
        self.assertEqual(state['side'],[])
        self.assertEqual(state['fixed'],15)
        self.assertNotIn('null',state['slots'])
        self.assertTrue(all(re.fullmatch(r'\d{5}[a-z]?',id) for id in state['ids']))
        self.assertEqual(self.errors,[])

    def test_my_deck_persistence_and_invalid_slots(self):
        self.goto("/deck")
        self.page.wait_for_function("window.cardStatistics && window.cardPreview", timeout=90000)
        # Mock a real MarvelCDB response, including corrupt IDs and counts.
        self.page.route("https://marvelcdb.com/api/public/decklist/12345.json", lambda route: route.fulfill(
            json={"name":"테스트 덱","hero_name":"Captain America","hero_code":"03001a",
                  "slots":{"03011":2,"03012":1,"null":10,"undefined":5,"03013":-1}},
            headers={"Access-Control-Allow-Origin":"*"}))
        self.page.evaluate("""() => {
            document.getElementById('deck_id').value='12345';
            getDeck(false);
        }""")
        main=self.page.locator('#player_deck_images > .image-div')
        expect(main).to_have_count(3)
        self.page.locator('#deck-name').fill('테스트 덱')
        self.page.evaluate("saveDeck()")
        self.page.wait_for_function("new URLSearchParams(location.search).has('saved')")
        key=self.page.evaluate("new URLSearchParams(location.search).get('saved')")
        self.addCleanup(lambda: (Path(__file__).resolve().parents[2]/'deck'/(key+'.json')).unlink(missing_ok=True))
        expect(self.page.locator('#deck-save-status')).to_have_text('My Deck 저장 완료', timeout=90000)
        expect(main).to_have_count(3)
        saved=self.context.request.get(BASE+'/get_hero_json?'+key).json()
        self.assertEqual(saved['name'],'테스트 덱')
        self.assertEqual(saved['player_deck'],['03011','03011','03012'])
        self.assertTrue(any(key+'.json' in path for path in self.context.request.get(BASE+'/list_deck').json()))
        self.assertEqual(self.errors,[])

    def test_save_slot_delete_confirmation(self):
        # Only the isolated CI checkout gets a synthetic save file.
        fixture = Path(__file__).resolve().parents[2] / "save_3.json"
        self.assertFalse(fixture.exists(), "Do not overwrite an existing save")
        fixture.write_text("{}", encoding="utf-8")
        try:
            self.goto("/main")
            self.page.get_by_role("button", name="저장 게임", exact=True).tap()
            row = self.page.locator("#save-list > div").filter(has_text="저장 3")
            delete = row.get_by_role("button", name="삭제", exact=True)
            expect(delete).to_be_enabled()
            delete.tap()
            expect(self.page.locator("#save-delete-confirm")).to_be_visible()
            self.page.locator("#save-delete-cancel").tap()
            self.assertTrue(fixture.exists())
            delete.tap()
            self.page.locator("#save-delete-apply").tap()
            expect(self.page.locator("#save-status")).to_have_text("저장 게임을 삭제했습니다.")
            expect(delete).to_be_disabled()
            self.assertFalse(fixture.exists())
            self.assertEqual(self.errors, [])
        finally:
            fixture.unlink(missing_ok=True)

    def test_scenario_selection_and_preview(self):
        rhino = self.open_setup()
        self.assertEqual(self.page.locator("body").evaluate(
            "(el) => getComputedStyle(el).getPropertyValue('--mc-accent').trim()"), "#2e6b57")
        self.screenshot("scenario")
        expect(self.page.locator(".ml-header button")).to_have_count(0)
        self.assertEqual(self.page.get_by_role("button", name="시나리오 파일 가져오기").count(), 0)
        rhino.locator(".ml-preview-icon").tap()
        preview = self.page.locator("dialog.ml-card-preview")
        expect(preview).to_be_visible()
        image = preview.locator("img")
        expect(image).to_be_visible()
        self.page.wait_for_function("document.querySelector('.ml-card-preview img').naturalWidth > 0")
        self.bounds(image)
        self.assertTrue(self.page.evaluate("window.MarvelSetup.back()"))
        expect(preview).to_be_hidden()
        expect(self.page.locator(".ml-scenario-name")).to_have_text("Rhino")
        expert = self.page.locator('#set-content button[data-caption="Rhino"][data-mode="전문가"]').first
        expert.tap()
        expect(self.page.locator(".ml-scenario-mode")).to_have_text("전문가 모드")
        expect(self.page.locator(".ml-footer .ml-primary")).to_be_enabled()
        self.page.locator(".ml-footer .ml-primary").tap()
        expect(self.page.locator(".ml-steps")).to_have_text("2 / 3")
        self.assertTrue(self.page.evaluate("window.MarvelSetup.back()"))
        expect(self.page.locator(".ml-steps")).to_have_text("1 / 3")
        expect(self.page.locator(".ml-scenario-mode")).to_have_text("전문가 모드")
        self.assertEqual(self.errors, [])

    def test_card_browser_touch_preview(self):
        self.goto("/cards")
        card = self.page.locator(".image-div[data-card-id]:not(.not-implemented):visible").first
        expect(card).to_be_visible(timeout=90000)
        self.page.wait_for_function("""() => {
            const card = [...document.querySelectorAll('.image-div[data-card-id]:not(.not-implemented)')].find(e => e.getClientRects().length);
            return !!card?.querySelector('img')?.naturalWidth;
        }""", timeout=60000)
        card.tap()
        preview = self.page.locator("#preview")
        expect(preview).to_be_visible()
        self.page.wait_for_function("document.getElementById('preview-img').naturalWidth > 0")
        self.bounds(preview.locator("#preview-img"))
        self.screenshot("preview")
        preview.get_by_role("button", name="닫기 ×").tap()
        expect(preview).to_be_hidden()
        self.assertEqual(self.errors, [])

    def start_game(self):
        self.open_setup()
        self.page.locator(".ml-footer .ml-primary").tap()
        hero = self.page.locator(".ml-grid button.ml-tile:not([disabled])").filter(has_text=re.compile("Captain America", re.I)).first
        expect(hero).to_be_visible(timeout=90000)
        hero.tap()
        self.page.get_by_role("button", name="플레이어 1에 추가", exact=True).tap()
        self.page.locator(".ml-footer .ml-primary").tap()
        expect(self.page.locator(".ml-footer .ml-primary")).to_have_text("게임 시작")
        expect(self.page.locator(".ml-versus .ml-vs")).to_have_text("VS")
        expect(self.page.locator(".ml-versus-team .ml-tile")).to_have_count(2)
        # Same seed for repeatable hand and screenshots.
        self.page.locator("#seed_div").fill("42")
        self.page.locator(".ml-footer .ml-primary").tap()
        self.page.wait_for_function("""() => window.Game?.world_descriptor &&
            window.Game.asking_players.length > 0 &&
            document.querySelectorAll('#player-all-hand-cards .card:not(.hide)').length > 0""", timeout=90000)
        expect(self.page.locator("#right-side-bar-handle")).to_be_visible()

    def wait_hand_images(self):
        # Ensure every rendered hand card has real decoded fixture artwork,
        # rather than only the purple selection border / red selection number.
        self.page.wait_for_function("""() => {
            const hand = [...document.querySelectorAll('#player-all-hand-cards .card:not(.hide)')];
            return hand.length >= 1 && hand.every(card => {
                const face = card.querySelector('.face');
                if (!face) return false;
                const style = getComputedStyle(face);
                const key = card.classList.contains('facedown') ? '--bg-image-false' : '--bg-image-true';
                const image = style.getPropertyValue(key);
                return image.includes('blob:') && getComputedStyle(face).visibility !== 'hidden';
            });
        }""", timeout=60000)

    def test_local_port_lifecycle(self):
        import subprocess
        import sys
        subprocess.run([sys.executable, "-c", "import socket\nimport unittest\n\nfrom engine.network.net_lib import NetLib\n\n\nclass PortLifecycleTests(unittest.TestCase):\n    def test_active_listener_and_recently_closed_listener(self):\n        host = \"127.0.0.1\"\n        with socket.socket() as listener:\n            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)\n            listener.bind((host, 0))\n            port = listener.getsockname()[1]\n            listener.listen(1)\n            self.assertFalse(NetLib.IsPortAvailable(host, port))\n            with socket.create_connection((host, port), timeout=2) as peer:\n                conn, _ = listener.accept()\n                with conn:\n                    conn.shutdown(socket.SHUT_WR)\n                    self.assertEqual(peer.recv(1), b\"\")\n                    peer.shutdown(socket.SHUT_WR)\n                    self.assertEqual(conn.recv(1), b\"\")\n        self.assertTrue(NetLib.IsPortAvailable(host, port))\n\nunittest.main()\n"], cwd=Path(__file__).resolve().parents[2], check=True)

    def test_mobile_game_over_layout(self):
        self.start_game()
        # Render a deterministic result without ending the actual server game.
        self.page.evaluate("""async () => {
            // Use the same versioned module instance already initialized by marvel.js.
            const url = performance.getEntriesByType('resource')
                .find(e => new URL(e.name).pathname === '/public/js/marvel/message.js')?.name;
            if (!url) throw new Error('Game message module not loaded');
            const {Message} = await import(url);
            Message.showGameOverMessage('The Main Scheme was Completed (The Break-In!)');
            const table = document.getElementById('session-statistics');
            table.replaceChildren();
            const header = table.createTHead().insertRow();
            for (const label of ['카드','준 피해','받은 피해','제거한 위협','플레이 영역 진입 횟수']) {
                const th = document.createElement('th'); th.textContent = label; header.append(th);
            }
            const body = table.createTBody();
            for (let i=0; i<25; i++) {
                const row = body.insertRow();
                for (let j=0; j<5; j++) row.insertCell().textContent = String(i+j);
            }
        }""")
        expect(self.page.locator("#game-over-text-2")).to_have_text("주요 음모가 달성되었습니다 (The Break-In!)")
        for width, height in [(915,412), (740,360)]:
            self.page.set_viewport_size({"width":width,"height":height})
            for selector in ["#game-over-box","#game-over-text-2","#session-statistics-container",
                             "#game-over-close","#game-over-buttons .save-replay","#game-over-buttons .share-replay",
                             "#game-over-buttons .retry-game","#game-over-buttons .main-menu"]:
                self.bounds(self.page.locator(selector))
            expect(self.page.locator("#right-side-bar-handle")).to_be_hidden()
            stats = self.page.locator("#session-statistics-container")
            self.assertTrue(stats.evaluate("(el) => { el.scrollTop=el.scrollHeight; return el.scrollTop>0; }"))
            self.assertGreater(stats.bounding_box()["height"], 80)
            self.screenshot(f"result-{width}")
        expect(self.page.locator("#mobile-forecast")).to_be_hidden()
        self.page.locator("#game-over-close").tap()
        expect(self.page.locator("#game-over-message")).to_be_hidden()
        expect(self.page.locator("#mobile-forecast")).to_be_hidden()
        expect(self.page.locator("#right-side-bar-handle")).to_be_visible()
        self.page.locator("#game-over-close").tap()
        expect(self.page.locator("#game-over-message")).to_be_visible()
        # The result is synthetic: the backend must refuse restart of a live game.
        response = self.page.evaluate("""async () => {
            const url = performance.getEntriesByType('resource').find(e => new URL(e.name).pathname === '/public/js/marvel/ui.js').name;
            const {UI}=await import(url);
            const response=await fetch('/retry_finished_game',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({game_id:UI.last_game_id})});
            return response.status;
        }""")
        self.assertEqual(response,409)
        self.page.locator("#game-over-buttons .main-menu").tap()
        expect(self.page.get_by_role("button",name="새 게임",exact=True)).to_be_visible()
        self.assertTrue(self.page.url.split('?')[0].endswith('/main'))
        self.assertEqual(self.errors, [])

    def test_gameplay_settings_and_mulligan(self):
        self.start_game()
        self.wait_hand_images()
        hand = self.page.locator("#player-all-hand-cards .card:not(.hide)")
        for card in hand.all():
            self.bounds(card)
        self.assertTrue(self.page.evaluate("""() => [...document.querySelectorAll('#player-all-hand-cards .card:not(.hide)')].every(c => c.style.getPropertyValue('--hand-angle') !== '')"""))
        self.assertEqual(self.page.evaluate("""() => [
            parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--card-width')),
            parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--card-height'))
        ]"""), [155, 214])
        self.bounds(self.page.locator("#mobile-forecast"))
        self.page.locator("#mobile-forecast").tap()
        expect(self.page.locator("#mobile-forecast-dialog")).to_be_visible()
        expect(self.page.locator("#mobile-forecast-detail")).to_contain_text("조우 카드 기본")
        self.page.locator("#mobile-forecast-dialog").get_by_role("button",name="닫기").tap()
        self.assertGreaterEqual(self.page.locator("#scene .mobile-unit-stats").count(),1)
        villain=self.page.locator("#area-villain .card.has-mobile-hud:not(.hide)").first
        hud=villain.locator(":scope > .mobile-board-hud")
        expect(hud).to_be_visible()
        self.assertGreaterEqual(hud.bounding_box()["x"],villain.bounding_box()["x"]+villain.bounding_box()["width"]-1)
        scheme=self.page.locator("#area-schemes-main .card.has-mobile-threat:not(.hide)").first
        expect(scheme.locator(":scope > .mobile-threat-hud")).to_be_visible()
        expect(scheme.locator(".mobile-threat-track")).to_be_visible()
        self.assertTrue(scheme.evaluate("(el) => el.querySelector('.mobile-threat-hud').getBoundingClientRect().top >= el.querySelector('.face').getBoundingClientRect().bottom-1"))
        self.assertTrue(hand.first.evaluate("(el) => {const m=new DOMMatrix(getComputedStyle(el).transform);return Math.hypot(m.a,m.b)>1.2;}"))
        self.screenshot("hand")
        # The desktop top piles deliberately use negative board coordinates.
        # Mobile must put real top cards entirely inside the camera clip.
        self.page.wait_for_function("""() => {
            const camera = document.getElementById('camera').getBoundingClientRect();
            const piles = ['encounter-deck-0','nemesis-pool','area-advanced'];
            return piles.every(id => {
                const cards = [...document.getElementById(id).querySelectorAll('.card:not(.hide)')];
                const top = cards.at(-1);
                if (!top) return false;
                const r = top.getBoundingClientRect();
                return r.width > 0 && r.height > 0 &&
                    r.top >= camera.top - 1 && r.bottom <= camera.bottom + 1 &&
                    r.left >= camera.left - 1 && r.right <= camera.right + 1;
            });
        }""")
        self.page.evaluate("""() => {
            const scene = document.getElementById('scene');
            const piles = [...scene.querySelectorAll('.encounter-deck,.encounter-discard-pile,#nemesis-pool,#area-advanced,#victory-display,#area-removed')];
            for (const pile of piles) {
                const s = getComputedStyle(pile);
                const y = Number(s.getPropertyValue('--y'));
                const x = Number(s.getPropertyValue('--x'));
                const h = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--card-height'));
                const w = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--card-width'));
                if (!Number.isFinite(x) || !Number.isFinite(y) || x < 0 || y < 0 ||
                    x + w > scene.offsetWidth || y + h > scene.offsetHeight) {
                    throw new Error('Clipped pile: ' + pile.id);
                }
            }
            const top = id => Number(getComputedStyle(document.getElementById(id)).getPropertyValue('--y'));
            const h = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--card-height'));
            if (top('encounter-deck-0') + h > top('encounter-discard-pile-0') ||
                top('nemesis-pool') + h > top('area-schemes-main') - 25) {
                throw new Error('Overlapping mobile pile rows');
            }
        }""")
        self.screenshot("top-piles")
        # Pile dialogs use compact viewport typography rather than scene-scaled headings.
        for pool, title in [('nemesis-pool','숙적 카드'),('area-advanced','예비 카드')]:
            self.page.locator('#'+pool).evaluate("(el) => el.click()")
            pile = self.page.locator('#touch-pile')
            expect(pile).to_be_visible()
            heading = pile.get_by_role('heading', name=title)
            expect(heading).to_be_visible()
            self.assertEqual(heading.evaluate("(el) => getComputedStyle(el).fontSize"), '18px')
            close = pile.get_by_role('button', name='닫기 ×')
            self.bounds(close)
            self.assertGreater(pile.locator('.touch-pile-list img').count(),0)
            self.screenshot(pool)
            close.tap()
            expect(pile).to_be_hidden()
        self.page.locator("#right-side-bar-handle").tap()
        dialog = self.page.locator("#mobile-settings-dialog")
        expect(dialog).to_be_visible()
        speed = dialog.locator("#anime-time")
        expect(speed).to_be_visible()
        self.bounds(speed)
        expect(dialog.locator("#all-hand-cards")).to_contain_text("손패:")
        expect(dialog.locator("#hide-no-action-cards")).to_contain_text("카드 표시:")
        expect(dialog.locator("#undo-btn")).to_be_visible()
        expect(self.page.locator("#players-pin")).to_be_hidden()
        self.screenshot("settings")
        # Settings must not replay the game or drop hand objects on Back.
        board_state = """() => ({
            step: window.Game.current_step_id,
            render: window.Game.world_descriptor.render_id,
            camera: document.getElementById('camera').style.transform,
            cards: [...document.querySelectorAll('#player-all-hand-cards .card:not(.hide),#player-all-area-hero .card:not(.hide),#area-villain .card:not(.hide)')].map(c => ({
                id: c.dataset.id,
                selected: c.classList.contains('selected'),
                x: c.style.getPropertyValue('--x'),
                y: c.style.getPropertyValue('--y')
            }))
        })"""
        original = self.page.evaluate(board_state)
        for index in range(3):
            if index > 0:
                self.page.locator("#right-side-bar-handle").tap()
                expect(dialog).to_be_visible()
            dialog.locator("#hide-no-action-cards").tap()
            dialog.locator("#all-hand-cards").tap()
            speed.fill("1.25" if index % 2 == 0 else "1")
            self.assertTrue(self.page.evaluate("window.MarvelTouch.back()"))
            expect(dialog).to_be_hidden()
            self.wait_hand_images()
            self.assertEqual(original, self.page.evaluate(board_state))
        self.screenshot("settings-back-stable")
        # History is independent from settings, dismissible without advancing
        # the game, and preserves the original controls in a collapsed panel.
        self.page.locator("#right-side-bar-handle").tap()
        expect(dialog).to_be_visible()
        dialog.get_by_role("button", name="기록", exact=True).tap()
        history = self.page.locator("#mobile-history-dialog")
        expect(history).to_be_visible()
        expect(dialog).to_be_hidden()
        self.bounds(history)
        expect(history.locator("#history-text .log-id").first).to_be_attached()
        self.assertFalse(history.locator("details").evaluate("(el) => el.open"))
        expect(history.locator("#ex-buttons")).to_be_hidden()
        self.screenshot("history-modal")
        history.locator("#mobile-history-close").tap()
        expect(history).to_be_hidden()
        self.assertEqual(original, self.page.evaluate(board_state))
        self.page.locator("#right-side-bar-handle").tap()
        dialog.get_by_role("button", name="기록", exact=True).tap()
        expect(history).to_be_visible()
        history.locator("summary").tap()
        expect(history.locator("#ex-buttons")).to_be_visible()
        self.assertTrue(self.page.evaluate("window.MarvelTouch.back()"))
        expect(history).to_be_hidden()
        self.assertEqual(original, self.page.evaluate(board_state))
        self.page.locator("#right-side-bar-handle").tap()
        expect(dialog).to_be_visible()
        # A tap outside the dialog must close it, not select the hand card
        # underneath or advance the server's game step.
        card = hand.first
        rect = card.bounding_box()
        self.assertIsNotNone(rect)
        x, y = rect["x"] + rect["width"] / 2, rect["y"] + rect["height"] / 2
        self.assertLess(x, dialog.bounding_box()["x"])
        state = "() => [window.Game.current_step_id, [...document.querySelectorAll('#player-all-hand-cards .card.selected')].map(x => x.dataset.id)]"
        before = self.page.evaluate(state)
        self.page.touchscreen.tap(x, y)
        expect(dialog).to_be_hidden()
        self.page.wait_for_timeout(600)
        self.assertEqual(before, self.page.evaluate(state))
        # A deliberate hand tap now selects a mulligan target.
        selectable = self.page.locator("#player-all-hand-cards .card.highlight-targets:not(.hide)").first
        expect(selectable).to_be_visible()
        selectable.tap()
        expect(selectable).to_have_class(re.compile(r"\bselected\b"))
        self.wait_hand_images()
        self.screenshot("mulligan-selected")
        # Wide initial landscape should use the available tabletop width.
        self.assertGreaterEqual(self.page.evaluate("""() =>
            Number(getComputedStyle(document.documentElement).getPropertyValue('--scene-width'))
        """), 1920)
        # Exercise the actual production layout with synthetic long prompt and
        # option content (no game action is submitted). Keep real card DOM.
        self.page.evaluate("""() => {
            const p = document.getElementById('prompt-box-container');
            p.classList.remove('hide','display-none','prompt-anime');
            document.getElementById('prompt-text').textContent =
                'Nick Fury entered play. Choose an ability. ' + 'Select an enemy or resolve a response. '.repeat(5);
            const opts = document.getElementById('option-buttons');
            opts.replaceChildren();
            for (const label of ['Draw 3 cards','Deal 4 damage to an enemy',
                'Remove 2 threat from a scheme', 'A long ability description '.repeat(4)]) {
                const b = document.createElement('button');
                b.className = 'button'; b.textContent = label; opts.append(b);
            }
            opts.children[1].classList.add('clicked');
            document.getElementById('btn-ok').disabled = false;
        }""")
        for width, height in [(915, 412), (740, 360)]:
            self.page.set_viewport_size({"width": width, "height": height})
            self.page.wait_for_function("""() => {
                const b = document.getElementById('camera').getBoundingClientRect();
                const r = document.getElementById('mobile-action-rail').getBoundingClientRect();
                const h = document.getElementById('mobile-progress-bar').getBoundingClientRect();
                return b.width > 0 && b.right <= innerWidth + 1 && b.right > r.left &&
                    b.top >= h.bottom - 1 && b.bottom <= innerHeight + 1 &&
                    r.width <= 131 && h.height <= 44;
            }""")
            prompt = self.page.locator("#prompt-box-container")
            options = self.page.locator("#option-buttons")
            ok = self.page.locator("#btn-ok")
            for element in [prompt, options, ok]:
                self.bounds(element)
            self.page.evaluate("""() => {
                const p = document.getElementById('prompt-box-container');
                const t = document.getElementById('prompt-text');
                const pr = p.getBoundingClientRect(), tr = t.getBoundingClientRect();
                if (tr.top < pr.top || tr.bottom > pr.bottom + 1 || t.scrollHeight <= t.clientHeight)
                    throw new Error('Long mobile prompt must start at the top and scroll');
                t.scrollTop = t.scrollHeight;
                if (t.scrollTop <= 0) throw new Error('Prompt cannot scroll');
                t.scrollTop = 0;
            }""")
            p, o, c = prompt.bounding_box(), options.bounding_box(), ok.bounding_box()
            self.assertLessEqual(p["y"] + p["height"], o["y"] + 1)
            self.assertLessEqual(o["y"] + o["height"], c["y"] + 1)
            self.bounds(self.page.locator("#right-side-bar-handle"))
            self.assertEqual(self.page.locator("#mobile-action-rail #prompt-box-container").count(), 0)
            self.assertEqual(self.page.locator("#mobile-progress-bar #prompt-box-container").count(), 1)
            self.assertGreaterEqual(self.page.evaluate("""() => {
                const pos = id => Number(getComputedStyle(document.getElementById(id)).getPropertyValue('--x'));
                return pos('area-advanced') - pos('nemesis-pool');
            }"""), 190)
            self.screenshot(f"compact-action-layout-{width}")
        self.assertEqual(self.errors, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
