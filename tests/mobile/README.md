# Mobile UI regression
Only Android-like landscape Chromium (915 x 412 CSS px, touch). No emulator or desktop suite.
The real local game server runs in a disposable test process; deterministic synthetic artwork avoids downloading licensed cards and does not test the production artwork service.
Run from the repository root with Python 3.12, Node 22:
```sh
python -m pip install -r mobile/android/requirements-mobile.txt playwright==1.51.0
python -m playwright install --with-deps chromium
npx --yes --package typescript@5.9.3 tsc -p public/js/tsconfig.json
mkdir -p test-results/mobile
python -u tests/mobile/server.py >test-results/mobile/server.log 2>&1 &
server=$!
trap 'kill "$server" 2>/dev/null || true' EXIT
python tests/mobile/test_mobile.py
```
CI uploads screenshots, Playwright traces and server/browser logs even on failure.
Open a trace with `python -m playwright show-trace test-results/mobile/test_gameplay_settings_and_mulligan.zip`.
This first suite covers setup, card viewer, starting a game, settings tap-through and mulligan selection. It does not establish pixel-perfect baselines or verify native WebView, APK install, Android back or real artwork downloads. Extend with stable gameplay fixtures before adding screenshot comparisons.
