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

    def test_ko_core_dictionary(self):
        self.goto("/main")
        result = self.page.evaluate("""async () => {
            const {koCard, koCards} = await import('/public/js/marvel/ko-cards.js');
            return {count:Object.keys(koCards).length, hero:koCard('01001a').name,
                    name:koCard('01005').name, text:koCard('01005').text,
                    unknown:koCard('99999') === undefined};
        }""")
        self.assertEqual(result["count"], 59)
        self.assertEqual(result["hero"], "Spider-Man")
        self.assertEqual(result["name"], "거미줄 날아차기")
        self.assertIn("피해 8", result["text"])
        self.assertTrue(result["unknown"])

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

    def test_gameplay_settings_and_mulligan(self):
        self.start_game()
        self.wait_hand_images()
        hand = self.page.locator("#player-all-hand-cards .card:not(.hide)")
        for card in hand.all():
            self.bounds(card)
        self.assertTrue(self.page.evaluate("""() => [...document.querySelectorAll('#player-all-hand-cards .card:not(.hide)')].every(c => c.style.getPropertyValue('--hand-angle') !== '')"""))
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
                    r.width <= 131 && h.height <= 34;
            }""")
            prompt = self.page.locator("#prompt-box-container")
            options = self.page.locator("#option-buttons")
            ok = self.page.locator("#btn-ok")
            for element in [prompt, options, ok]:
                self.bounds(element)
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
