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
        self.screenshot("hand")
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
        self.assertEqual(self.errors, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
