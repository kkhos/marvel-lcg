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

    def test_mobile_native_landscape_art_and_keywords(self):
        self.start_game()
        self.page.evaluate("""async () => {
            const {CardImages}=await import('/public/js/module/card_images.js');
            const {HoverCard}=await import('/public/js/marvel/hover.js');
            const {CardAnimation}=await import('/public/js/marvel/card_animation.js');
            const make=(w,h)=>{
                const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;
                const ctx=canvas.getContext('2d');ctx.fillStyle='#c4a97e';ctx.fillRect(0,0,w,h);
                return canvas.toDataURL('image/png');
            };
            const art=make(194,140), portrait=make(140,194);
            const scheme=document.querySelector('#area-schemes-main .card:not(.hide):not(.facedown)');
            if(!scheme)throw new Error('No main scheme');
            const face=scheme.querySelector('.face');
            CardImages.setBackground(face,'--bg-image-true',art,true);
            const old=CardAnimation.animation_name;
            CardAnimation.animation_name='center_flip';
            HoverCard.center_preview.preview_container.classList.remove('display-none');
            HoverCard.show('url("'+art+'")','Test Scheme','EncounterSideScheme','', '1','',false);
            CardAnimation.animation_name=old;
            const unit=document.querySelector('#area-villain .card:not(.hide)');
            const info=unit.querySelector('.info');
            const keyword=document.createElement('div');keyword.id='test-quickstrike';
            keyword.innerHTML='<span class="quickstrike hide-value">Quickstrike</span>';
            const counter=document.createElement('div');counter.id='test-keyword-counter';
            counter.innerHTML='<span>2x</span><span class="quickstrike counter">test</span>';
            info.append(keyword,counter);
            window.orientationTest={face,scheme,portrait,showPortrait:()=>{
                const prev=CardAnimation.animation_name;CardAnimation.animation_name='center_flip';
                HoverCard.show('url("'+portrait+'")','Test Scheme','EncounterSideScheme','', '1','',false);
                CardAnimation.animation_name=prev;
            }};
        }""")
        preview=self.page.locator("#image-preview-div-center .image-preview")
        expect(preview).to_have_attribute("data-art-orientation","landscape")
        self.page.wait_for_function("""() => {
            const {face,scheme}=window.orientationTest;
            const p=document.querySelector('#image-preview-div-center .image-preview');
            const art=getComputedStyle(face.querySelector('.image'),'::before');
            return face.dataset.artOrientation==='landscape' && art.transform==='none' &&
                p.getBoundingClientRect().width>p.getBoundingClientRect().height &&
                getComputedStyle(p).rotate==='0deg' &&
                getComputedStyle(document.getElementById('test-quickstrike')).display==='none' &&
                getComputedStyle(document.getElementById('test-keyword-counter')).display!=='none';
        }""")
        self.bounds(preview)
        self.screenshot("native-landscape-art")
        self.page.evaluate("window.orientationTest.showPortrait()")
        expect(preview).to_have_attribute("data-art-orientation","portrait")
        self.page.wait_for_function("""() => {
            const p=document.querySelector('#image-preview-div-center .image-preview');
            return getComputedStyle(p).rotate==='90deg';
        }""")
        self.assertEqual(self.errors, [])

    def test_mobile_dynamic_card_focus(self):
        self.start_game()
        result=self.page.evaluate("""async () => {
            const {MobileCardFocus}=await import('/public/js/marvel/mobile-card-focus.js');
            const {SelectStep}=await import('/public/js/marvel/select.js');
            const hand=document.getElementById('player-all-hand-cards');
            const card=hand.querySelector('.card:not(.hide)');
            if(!card) throw new Error('No visible hand card');
            const original=card.dataset.id;
            const step=SelectStep.getStep();
            const count=hand.dataset.focusCount;
            const button=document.getElementById('mobile-dynamic-card-focus');
            const scale=()=>Number(getComputedStyle(hand).getPropertyValue('--focus-hand-scale'))||1.22;
            SelectStep.restoreStep('card');
            MobileCardFocus.setPhase('Player 1 Turn');
            const player=scale(), phase=document.body.dataset.cardFocus;
            MobileCardFocus.setPhase('Enemy Activation');
            const villain=scale();
            SelectStep.restoreStep('cost');
            const cost=scale();
            button.click();
            const off=scale(), offPhase=document.body.dataset.cardFocus;
            button.click();
            MobileCardFocus.setPhase('Resolve Mulligans');
            SelectStep.restoreStep(step);
            return {player,phase,villain,cost,off,offPhase,original,after:card.dataset.id,count};
        }""")
        self.assertEqual(result["phase"], "player")
        self.assertGreater(result["player"], result["villain"])
        self.assertGreater(result["cost"], result["villain"])
        self.assertEqual(result["offPhase"], "off")
        self.assertEqual(result["off"], 1.22)
        self.assertEqual(result["original"], result["after"])
        self.assertEqual(self.errors, [])

    def test_mobile_long_ability_choices(self):
        self.start_game()
        self.page.evaluate("""async () => {
            const {MobileAbilityChoices}=await import('/public/js/marvel/mobile-ability-choices.js');
            const {SelectStep}=await import('/public/js/marvel/select.js');
            const source=document.getElementById('option-buttons');
            window.choiceTest={clicks:0,cancels:0};
            window.choiceTest.render=(labels,optional=false)=>{
                SelectStep.restoreStep('effect');
                source.replaceChildren();
                for(const [i,label] of labels.entries()){
                    const b=document.createElement('button');b.className='button';b.textContent=label;
                    if(i===1 && label==='사용 불가') b.classList.add('disable');
                    b.onclick=()=>{window.choiceTest.clicks++;b.classList.add('clicked');SelectStep.restoreStep('target');};
                    source.append(b);
                }
                MobileAbilityChoices.present(source,()=>optional);
            };
            window.choiceTest.render(['공격','저지']);
        }""")
        popup=self.page.locator("#mobile-ability-choice-dialog")
        expect(self.page.locator("#option-buttons")).to_be_visible()
        expect(popup).to_be_hidden()
        self.page.evaluate("""() => window.choiceTest.render([
            '타고난 반사신경을 손에 더하기 '.repeat(4), '사용 불가', '덱에 남기기'])""")
        expect(popup).to_be_visible()
        expect(popup.locator(".mac-option")).to_have_count(3)
        expect(popup.locator(".mac-option").nth(1)).to_be_disabled()
        expect(popup.locator(".mac-cancel")).to_be_hidden()
        self.page.keyboard.press("Escape")
        expect(popup).to_have_attribute("open", "")
        expect(popup).to_be_visible()
        result=self.page.evaluate("""() => {
            const d=document.getElementById('mobile-ability-choice-dialog');
            const before=d.open;
            const handled=window.MarvelTouch.back();
            return {before,handled,after:d.open,step:document.body.dataset.selectionStep,
                count:document.querySelectorAll('#option-buttons > button').length,
                clicks:window.choiceTest.clicks};
        }""")
        self.assertEqual(result, {"before":True,"handled":True,"after":True,"step":"effect","count":3,"clicks":0})
        expect(popup).to_be_visible()
        for width,height in [(915,412),(740,360)]:
            self.page.set_viewport_size({"width":width,"height":height})
            self.bounds(popup)
            box=popup.bounding_box()
            self.assertLessEqual(abs(box["x"]+box["width"]/2-width/2),2)
            self.assertLessEqual(box["height"],height*.8+2)
        popup.locator(".mac-option").first.tap()
        expect(popup).to_be_hidden()
        self.assertEqual(self.page.evaluate("window.choiceTest.clicks"),1)
        expect(self.page.locator("#option-buttons")).to_be_hidden()
        # Canceling target selection can restore the same long option list.
        self.page.evaluate("""async () => {
            const {SelectStep}=await import('/public/js/marvel/select.js');
            document.querySelector('#option-buttons .clicked').classList.remove('clicked');
            SelectStep.restoreStep('effect');
        }""")
        expect(popup).to_be_visible()
        self.page.evaluate("document.getElementById('option-buttons').replaceChildren()")
        expect(popup).to_be_hidden()
        # Many short choices also exceed the rail's measured capacity.
        self.page.evaluate("() => window.choiceTest.render(Array.from({length:14},(_,i)=>'능력 '+i))")
        expect(popup).to_be_visible()
        self.assertTrue(popup.locator(".mac-list").evaluate("el => el.scrollHeight > el.clientHeight"))
        self.page.evaluate("document.getElementById('option-buttons').replaceChildren()")
        expect(popup).to_be_hidden()
        self.assertEqual(self.errors, [])

    def test_ko_status_and_statistics(self):
        self.goto("/main")
        result = self.page.evaluate("""async () => {
            const {koStatusCard} = await import('/public/js/marvel/ko-status.js');
            const {koLabel, koStatistic, koHtml} = await import('/public/js/marvel/ko-game.js');
            return {cards:['Tough','Stunned','Confused'].map(n=>koStatusCard('StatusCard',n)),
                other:koStatusCard('Event','Tough') === undefined,
                title:koLabel('STATISTIC'),
                spell:koLabel('Spell Mastery'),
                starting:['Add Innate Reflexes to your hand (Starting)',
                    'Put Innate Reflexes into your hand (Starting)',
                    'Leave Innate Reflexes in your deck'].map(koHtml),
                startingMarkup:koHtml('<span data-id="60038">Add Innate Reflexes to your hand (Starting)</span>'),
                untouched:koHtml('Innate Reflexes'),
                events:['Resolve','Resolved','Enters Play','Resource','Defeated'].map(koStatistic),
                html:koHtml('<span data-id="Resolved">Resolved x2</span>')};
        }""")
        self.assertEqual([c["name"] for c in result["cards"]], ["강인함", "기절", "혼란"])
        self.assertTrue(all("버립니다" in c["text"] for c in result["cards"]))
        self.assertTrue(result["other"])
        self.assertEqual(result["title"], "통계")
        self.assertEqual(result["spell"], "주문 숙달")
        self.assertEqual(result["starting"], ["타고난 반사신경을 손에 더하기 (시작 시)", "타고난 반사신경을 손에 더하기 (시작 시)", "타고난 반사신경을 덱에 남기기"])
        self.assertEqual(result["startingMarkup"], '<span data-id="60038">타고난 반사신경을 손에 더하기 (시작 시)</span>')
        self.assertEqual(result["untouched"], "Innate Reflexes")
        self.assertEqual(result["events"], ["효과 처리", "효과 처리 완료", "플레이 영역에 들어옴", "자원으로 사용", "격파"])
        self.assertEqual(result["html"], '<span data-id="Resolved">효과 처리 완료 2회</span>')

    def test_rule_dictionary(self):
        self.start_game()
        self.page.locator("#right-side-bar-handle").tap()
        self.page.locator("#mobile-settings-rule-help").tap()
        dictionary=self.page.locator("#mobile-rule-dictionary")
        expect(dictionary).to_be_visible()
        search=dictionary.get_by_role("searchbox")
        search.fill("Surge")
        expect(dictionary.locator("summary")).to_have_text("쇄도 (Surge)")
        dictionary.locator("summary").tap()
        expect(dictionary.locator("details p")).to_contain_text("추가 조우 카드 1장")
        search.fill("수렁")
        expect(dictionary.locator("summary")).to_have_text("수렁 (Hazard)")
        dictionary.get_by_role("button",name="닫기 ×").tap()
        expect(dictionary).to_be_hidden()
        expect(self.page.locator("#mobile-settings-dialog")).to_be_visible()
        self.page.locator("#mobile-settings-dialog").get_by_role("button",name="닫기 ×").tap()
        result=self.page.evaluate("""async () => {
            const {ruleHelp,relatedRules,renderRelatedRules}=await import('/public/js/marvel/ko-rule-help.js');
            const {progressSummary}=await import('/public/js/marvel/mobile-prompt.js');
            const el=document.createElement('div');
            renderRelatedRules(el,relatedRules('Surge.','쇄도.'));
            el.querySelector('button').click();
            return {count:ruleHelp.filter(r=>r.category==='키워드').length,description:el.querySelector('.rule-help-detail').textContent,
                noToughness:!relatedRules('Tough','강인함').some(x=>x.id==='Toughness'),
                hazard:relatedRules('','',{hazard:1}).some(x=>x.id==='Hazard'),
                surge:progressSummary('Reveal Encounter Cards','Card would surge against Peter Parker').action};
        }""")
        self.assertEqual(result["count"],26)
        self.assertIn("추가 조우 카드 1장",result["description"])
        self.assertTrue(result["noToughness"])
        self.assertTrue(result["hazard"])
        self.assertEqual(result["surge"],"쇄도 · 추가 조우 카드 공개")
        self.assertEqual(self.errors,[])

    def test_mobile_prompt_summary(self):
        self.goto("/main")
        result=self.page.evaluate("""async () => {
            const {phaseLabel,askSummary,targetSummary,paymentSummary,progressSummary}=await import('/public/js/marvel/mobile-prompt.js');
            const {EffectDescriptor}=await import('/public/js/marvel/data.js');
            const e=new EffectDescriptor({name:'Resolve Mulligans',target_num_range:[0,6],all_legal_targets:[1,2,3,4,5,6]});
            e.selected_targets=[1,2];
            const custom=new EffectDescriptor({name:'Choose a card with a printed energy resource',target_num_range:[1,1]});
            const cost=new EffectDescriptor({name:'Play',target_num_range:[0,0]});
            return {phase:phaseLabel('Player 1 Turn',2),target:targetSummary(e),custom:targetSummary(custom),
                cost:paymentSummary(cost,2,['3'],false,false),typedCost:paymentSummary(cost,1,['RY'],false,false,'R'),
                unknown:progressSummary('Enemy Activation','Custom scenario: do not discard this card')===undefined,
                customAsk:askSummary({event_name:'WhenPlayerChooseAbility',ability_type:'Normal',show_cancel:false,options:[custom]},'Player 1 Turn','Choose a card with a printed energy resource')===undefined};
        }""")
        self.assertEqual(result["phase"],"R2 · 플레이어")
        self.assertEqual(result["target"]["action"],"교체할 카드 선택")
        self.assertIn("0~6",result["target"]["count"])
        self.assertEqual(result["cost"]["count"],"2/3")
        self.assertEqual(result["typedCost"]["payment"],{"paid":"R","required":["RY"]})
        self.assertEqual(result["custom"]["context"],"Choose a card with a printed energy resource")
        self.assertTrue(result["unknown"])
        self.assertTrue(result["customAsk"])

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

    def test_ko_imported_pack_priority(self):
        self.goto("/main")
        result=self.page.evaluate("""async () => {
            const {KO_IMPORTED_KEY,cleanImportedCards}=await import('/public/js/marvel/ko-local.js');
            const {koCard,koCardSource,refreshKoCards}=await import('/public/js/marvel/ko-cards.js');
            const clean=cleanImportedCards({'09001b':{name:'Stephen Strange',text:'타고난 재능'},'01001a':{name:'오류',text:'틀린 번역'},'07034':{name:'오류',text:'틀린 번역'},'bad':{name:'오류',text:'오류'}});
            localStorage.setItem(KO_IMPORTED_KEY,JSON.stringify(clean));refreshKoCards();
            const result={ids:Object.keys(clean),doctor:koCard('09001b').text,source:koCardSource('09001b'),hero:koCard('01001a').name,wreck:koCard('07034').name};
            localStorage.removeItem(KO_IMPORTED_KEY);refreshKoCards();return result;
        }""")
        self.assertEqual(result["doctor"],"타고난 재능")
        self.assertEqual(result["source"],"imported")
        self.assertEqual(result["hero"],"Spider-Man")
        self.assertEqual(result["wreck"],"강화하다!")
        self.assertNotIn("bad",result["ids"])
        self.goto("/artwork")
        expect(self.page.locator("#ko-pack-install")).to_be_visible()

    def test_ko_imported_character_names_batch_one(self):
        self.goto("/main")
        result = self.page.evaluate("""async () => {
            const {KO_IMPORTED_KEY}=await import('/public/js/marvel/ko-local.js');
            const {koCard,koCardSource,refreshKoCards}=await import('/public/js/marvel/ko-cards.js');
            const {normalizeImportedKoText}=await import('/public/js/marvel/ko-glossary.js');
            const sample='닥터 스트레인지 카드. 스파이더맨, 피터 파커, 스티븐 스트레인지, 고스트 스파이더, 그웬 스테이시, 블랙 캣, 닉 퓨리. 버린 더미. 스파이더센스. 거미줄 날아차기.';
            const before=koCard('01001a').text;
            const saved=localStorage.getItem(KO_IMPORTED_KEY);
            try {
                localStorage.setItem(KO_IMPORTED_KEY, JSON.stringify({'09001b':{name:'Stephen Strange',text:sample},'01001a':{name:'오류',text:'틀린 번역'}}));
                refreshKoCards();
                const normalized=normalizeImportedKoText(sample);
                return {text:koCard('09001b').text, source:koCardSource('09001b'),
                    verified:koCard('01001a').text===before && koCardSource('01001a')==='verified',
                    idempotent:normalizeImportedKoText(normalized)===normalized};
            } finally {
                if(saved===null)localStorage.removeItem(KO_IMPORTED_KEY);
                else localStorage.setItem(KO_IMPORTED_KEY,saved);
                refreshKoCards();
            }
        }""")
        self.assertEqual(result["text"], "Doctor Strange 카드. Spider-Man, Peter Parker, Stephen Strange, Ghost-Spider, Gwen Stacy, Black Cat, Nick Fury. 버린 카드 더미. 스파이더센스. 거미줄 날아차기.")
        self.assertEqual(result["source"], "imported")
        self.assertTrue(result["verified"])
        self.assertTrue(result["idempotent"])

    def test_ko_imported_character_names_batch_two(self):
        self.goto("/main")
        result = self.page.evaluate("""async () => {
            const {normalizeImportedKoText}=await import('/public/js/marvel/ko-glossary.js');
            const {KO_IMPORTED_KEY}=await import('/public/js/marvel/ko-local.js');
            const {koCard,koCardSource,refreshKoCards}=await import('/public/js/marvel/ko-cards.js');
            const sample="캡틴 아메리카 · 스티브 로저스 · 캡틴 마블 · 캐럴 댄버스 · 아이언맨 · 토니 스타크 · 블랙 팬서 · 트찰라 · 쉬헐크 · 제니퍼 월터스 · 미즈 마블 · 카말라 칸 · 브루스 배너 · 오딘슨 · 블랙 위도우 · 나타샤 로마노프 · 호크아이 · 클린트 바튼 · 스파이더 우먼 · 제시카 드루 · 앤트맨 · 스콧 랭 · 와스프 · 나디아 반 다인 · 퀵실버 · 피에트로 막시모프 · 스칼렛 위치 · 완다 막시모프 · 스타로드 · 피터 퀼 · 로켓 라쿤 · 가모라 · 드랙스 · 그루트 · 모니카 램보 · 워 머신 · 제임스 로즈 · 마일스 모랄레스 · 샘 알렉산더 · 아이언하트 · 리리 윌리엄스 · 사이클롭스 · 스콧 서머스 · 진 그레이 · 울버린 · 갬빗 · 레미 르보 · 키티 프라이드 · 섀도우 캣 · 오로로 먼로 · 피오트르 라스푸틴 · 콜로서스 · 데드풀 · 웨이드 윌슨";
            const unchanged='비전, 폭풍, 로그, 헐크, 레드 헐크, 피닉스, 스파이더센스, 기본 기능';
            const normalized=normalizeImportedKoText(sample);
            const saved=localStorage.getItem(KO_IMPORTED_KEY);
            const before=koCard('01001a').text;
            try {
                localStorage.setItem(KO_IMPORTED_KEY,JSON.stringify({'09001b':{name:'Stephen Strange',text:sample},'01001a':{name:'오류',text:sample}}));
                refreshKoCards();
                return {text:koCard('09001b').text, source:koCardSource('09001b'),
                    protected:koCard('01001a').text===before && koCardSource('01001a')==='verified',
                    idempotent:normalizeImportedKoText(normalized)===normalized,
                    unchanged:normalizeImportedKoText(unchanged)};
            } finally {
                if(saved===null)localStorage.removeItem(KO_IMPORTED_KEY);
                else localStorage.setItem(KO_IMPORTED_KEY,saved);
                refreshKoCards();
            }
        }""")
        self.assertEqual(result["text"], "Captain America · Steve Rogers · Captain Marvel · Carol Danvers · Iron Man · Tony Stark · Black Panther · T'Challa · She-Hulk · Jennifer Walters · Ms. Marvel · Kamala Khan · Bruce Banner · Odinson · Black Widow · Natasha Romanoff · Hawkeye · Clint Barton · Spider-Woman · Jessica Drew · Ant-Man · Scott Lang · Wasp · Nadia Van Dyne · Quicksilver · Pietro Maximoff · Scarlet Witch · Wanda Maximoff · Star-Lord · Peter Quill · Rocket Raccoon · Gamora · Drax · Groot · Monica Rambeau · War Machine · James Rhodes · Miles Morales · Sam Alexander · Ironheart · Riri Williams · Cyclops · Scott Summers · Jean Grey · Wolverine · Gambit · Remy LeBeau · Kitty Pryde · Shadowcat · Ororo Munroe · Piotr Rasputin · Colossus · Deadpool · Wade Wilson")
        self.assertEqual(result["source"], "imported")
        self.assertTrue(result["protected"])
        self.assertTrue(result["idempotent"])
        self.assertEqual(result["unchanged"], "비전, 폭풍, 로그, 헐크, 레드 헐크, 피닉스, 스파이더센스, 기본 기능")

    def test_ko_imported_character_names_batch_three(self):
        self.goto("/main")
        result = self.page.evaluate("""async () => {
            const {normalizeImportedKoText}=await import('/public/js/marvel/ko-glossary.js');
            const {KO_IMPORTED_KEY}=await import('/public/js/marvel/ko-local.js');
            const {koCard,koCardSource,refreshKoCards}=await import('/public/js/marvel/ko-cards.js');
            const sample="라이노 · 울트론 · 그린 고블린 · 노먼 오스본 · 썬더볼 · 파일 드라이버 · 레드 스컬 · 크로스본즈 · 태스크마스터 · 매그니토 · 타노스 · 마담 하이드라 · 닥터 옥토퍼스 · 미스테리오 · 벌처 · 쇼커 · 샌드맨 · 스콜피온 · 일렉트로 · 툼스톤 · 타이거 샤크 · 라디오액티브 맨 · 멜터 · 바론 제모 · 바론 모르도 · 도르마무 · 프록시마 미드나이트 · 컬 옵시디언 · 코르버스 글레이브 · 에보니 모 · 로난의 · 클로우 · 불도저의 · 렉커 · 휠윈드 · 모도크";
            const unchanged="독, 전갈, 모래 인간, 클로, 캉, 칸, 로난드, 불도저로 길을 밀다, 고블린 글라이더, 하이드라 군인, 일렉트로닉";
            const normalized=normalizeImportedKoText(sample);
            const saved=localStorage.getItem(KO_IMPORTED_KEY);
            const before=koCard('07004').text;
            try {
                localStorage.setItem(KO_IMPORTED_KEY,JSON.stringify({'09001b':{name:'Stephen Strange',text:sample},'07004':{name:'오류',text:sample}}));
                refreshKoCards();
                return {text:koCard('09001b').text,source:koCardSource('09001b'),
                    protected:koCard('07004').text===before && koCardSource('07004')==='verified',
                    idempotent:normalizeImportedKoText(normalized)===normalized,
                    unchanged:normalizeImportedKoText(unchanged)};
            } finally {
                if(saved===null)localStorage.removeItem(KO_IMPORTED_KEY);
                else localStorage.setItem(KO_IMPORTED_KEY,saved);
                refreshKoCards();
            }
        }""")
        self.assertEqual(result["text"], "Rhino · Ultron · Green Goblin · Norman Osborn · Thunderball · Piledriver · Red Skull · Crossbones · Taskmaster · Magneto · Thanos · Madame Hydra · Doctor Octopus · Mysterio · Vulture · Shocker · Sandman · Scorpion · Electro · Tombstone · Tiger Shark · Radioactive Man · Melter · Baron Zemo · Baron Mordo · Dormammu · Proxima Midnight · Cull Obsidian · Corvus Glaive · Ebony Maw · Ronan의 · Klaw · Bulldozer의 · Wrecker · Whirlwind · M.O.D.O.K.")
        self.assertEqual(result["source"], "imported")
        self.assertTrue(result["protected"])
        self.assertTrue(result["idempotent"])
        self.assertEqual(result["unchanged"], "독, 전갈, 모래 인간, 클로, 캉, 칸, 로난드, 불도저로 길을 밀다, 고블린 글라이더, 하이드라 군인, 일렉트로닉")

    def test_ko_imported_rule_terms_batch_four(self):
        self.goto("/main")
        result = self.page.evaluate("""async () => {
            const {normalizeImportedKoText,normalizeImportedKoTerms}=await import('/public/js/marvel/ko-glossary.js');
            const {KO_IMPORTED_KEY,cleanImportedCards}=await import('/public/js/marvel/ko-local.js');
            const {koCard,koCardSource,refreshKoCards}=await import('/public/js/marvel/ko-cards.js');
            const sample="임시. 일시적. 임시 키워드를 잃습니다. 조우 버린 더미에서 카드 2장. 승점 구역 구역. 조종 하에. 정신 자원(정신력), 물리 자원(물리력), 와일드 자원(만능), 에너지 자원(에너지). 강화 아이콘(강화 아이콘), 위기 아이콘(위기 아이콘), 가속 아이콘(가속 아이콘), 수렁 아이콘(수렁 아이콘), 증폭 아이콘(증폭 아이콘). 팀워크 (다크 라이더스).";
            const unchanged="임시 카드가 있습니다. 강인. 강인함 상태 카드. 영속. 반격 2. 교란 X. 진척 3. 승점 0. 그러고 나서, 그리고, 대신. 물리력물리력 자원. 버린 조우 더미.";
            const saved=localStorage.getItem(KO_IMPORTED_KEY);
            const before=koCard('01001a').text;
            try {
                const clean=cleanImportedCards({'09001b':{name:'Stephen Strange',text:sample},'01001a':{name:'오류',text:sample},
                    '45180a':{name:'임무',text:'정신 자원([mental])마다 위협을 2만큼 놓습니다. 강화 아이콘([boost])을 무시합니다.'}});
                localStorage.setItem(KO_IMPORTED_KEY,JSON.stringify(clean));refreshKoCards();
                const normalized=normalizeImportedKoText(sample);
                return {text:koCard('09001b').text,source:koCardSource('09001b'),
                    realStyle:koCard('45180a').text,
                    protected:koCard('01001a').text===before && koCardSource('01001a')==='verified',
                    unchanged:normalizeImportedKoTerms(unchanged),
                    discardPiles:['조우 버린 더미','조우 버린 카드 더미','버린 조우 더미','당신의 버린 더미','버린 카드 더미'].map(normalizeImportedKoText),
                    idempotent:normalizeImportedKoText(normalized)===normalized};
            } finally {
                if(saved===null)localStorage.removeItem(KO_IMPORTED_KEY);
                else localStorage.setItem(KO_IMPORTED_KEY,saved);
                refreshKoCards();
            }
        }""")
        self.assertEqual(result["text"], "순간. 순간. 순간 키워드를 잃습니다. 버린 조우 더미에서 카드 2장. 승점 구역. 조종하에. 정신력 자원, 물리력 자원, 만능 자원, 에너지 자원. 강화 아이콘, 위기 아이콘, 가속 아이콘, 수렁 아이콘, 증폭 아이콘. 팀워크(다크 라이더스).")
        self.assertEqual(result["source"], "imported")
        self.assertEqual(result["realStyle"], "정신력 자원마다 위협을 2만큼 놓습니다. 강화 아이콘을 무시합니다.")
        self.assertEqual(result["discardPiles"], ["버린 조우 더미","버린 조우 더미","버린 조우 더미","당신의 버린 카드 더미","버린 카드 더미"])
        self.assertTrue(result["protected"])
        self.assertTrue(result["idempotent"])
        self.assertEqual(result["unchanged"], "임시 카드가 있습니다. 강인. 강인함 상태 카드. 영속. 반격 2. 교란 X. 진척 3. 승점 0. 그러고 나서, 그리고, 대신. 물리력물리력 자원. 버린 조우 더미.")

    def test_ko_verified_trait_labels(self):
        self.goto("/main")
        result = self.page.evaluate("""async () => {
            const {koTraitLabel,verifiedKoTraits}=await import('/public/js/marvel/ko-traits.js');
            return {count:Object.keys(verifiedKoTraits).length,
                verified:['t_aerial','t_tech','t_skill','t_avenger','t_defender','t_s.h.i.e.l.d','S.H.I.E.L.D.','t_hero_for_hire','t_genius'].map(koTraitLabel),
                pending:['t_x-men','t_guardian','t_mutant','t_mystic','t_web-warrior','t_future_trait','constructor'].map(koTraitLabel)};
        }""")
        self.assertEqual(result["count"], 19)
        self.assertEqual(result["verified"], ["공중","과학","기술","AVENGER","DEFENDER","S.H.I.E.L.D.","S.H.I.E.L.D.","용병 히어로","천재"])
        self.assertEqual(result["pending"], ["X-MEN","GUARDIAN","MUTANT","MYSTIC","WEB-WARRIOR","FUTURE TRAIT","CONSTRUCTOR"])

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
        # Compare the actual preview footer controls with the board settings control.
        self.page.evaluate("""() => {
            const d=document.getElementById('touch-preview');
            const setting=document.getElementById('right-side-bar-handle').getBoundingClientRect();
            d.showModal();
            try {
                for(const el of [d, ...d.querySelectorAll('.touch-card-title,.touch-card-text,.touch-buttons button')]) {
                    if(getComputedStyle(el).userSelect !== 'none')
                        throw new Error('Preview permits native text selection');
                }
                const close=d.querySelector('.touch-buttons button:last-child');
                for(const type of ['contextmenu','selectstart']) {
                    if(close.dispatchEvent(new Event(type,{bubbles:true,cancelable:true})))
                        throw new Error('Preview did not cancel '+type);
                }
                for(const b of d.querySelectorAll('.touch-buttons > button:not([hidden])')) {
                    const r=b.getBoundingClientRect();
                    if(Math.abs(r.width-setting.width)>1 || Math.abs(r.height-setting.height)>1)
                        throw new Error('Preview footer and settings button dimensions differ');
                }
            } finally {d.close();}
        }""")
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
        # Native desktop hover details must not obscure mobile identity artwork.
        identity = self.page.locator("#scene .card.type-hero.has-mobile-hud, #scene .card.type-alter-ego.has-mobile-hud").first
        expect(identity.locator(":scope > .mobile-board-hud")).to_be_visible()
        self.assertTrue(identity.evaluate("""el => {
            const details=[...el.querySelectorAll('.info .hover-only')];
            return details.length > 0 && details.every(d => getComputedStyle(d).display === 'none');
        }"""))
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
        self.page.evaluate("""async () => {
            const {SelectStep} = await import('/public/js/marvel/select.js');
            SelectStep.restoreStep('effect');
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
            for (const step of ['target', 'cost', 'effect', 'card']) {
                SelectStep.restoreStep(step);
                const hidden=getComputedStyle(opts).display==='none';
                if(hidden !== ['target','cost'].includes(step) || opts.children.length!==4 ||
                    getComputedStyle(document.getElementById('btn-ok')).display==='none')
                    throw new Error('Mobile action visibility mismatch: '+step);
            }
            SelectStep.restoreStep('effect');
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
                // The same production prompt must center short raw messages,
                // including inline card links, without clipping long messages.
                const original = t.innerHTML;
                try {
                    t.innerHTML = '<span class="log-card">Rhino</span> 공격 예정';
                    const short = t.getBoundingClientRect();
                    const center = r => (r.top+r.bottom)/2;
                    if (t.scrollHeight > t.clientHeight + 1 || Math.abs(center(short)-center(pr)) > 1)
                        throw new Error('One-line raw prompt is not vertically centered');
                    t.innerHTML = '첫 번째 안내<br>두 번째 안내';
                    const two = t.getBoundingClientRect();
                    if (t.scrollHeight <= t.clientHeight + 1 && Math.abs(center(two)-center(pr)) > 1)
                        throw new Error('Two-line prompt that fits is not vertically centered');
                } finally {
                    t.innerHTML = original;
                    t.scrollTop = 0;
                }
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
