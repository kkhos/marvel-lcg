# Android runtime PoC (not a release)

Goal: preserve upstream Python card logic and existing HTML/TypeScript UI; run the aiohttp server on-device. This first experiment does not claim game compatibility or mobile UX.

## Build

Requirements: JDK 17, Gradle 8.9, Android SDK 35, host Python 3.12, Node 22.
From repository root:

```sh
npx --yes --package typescript@5.9.3 tsc -p public/js/tsconfig.json
gradle -p mobile/android :app:assembleDebug
adb install -r mobile/android/app/build/outputs/apk/debug/app-debug.apk
```

The app first probes Python, NumPy, Pillow, HTTP and WebSocket; press Start game engine only after success. The bootstrap copies the bundled tree into private storage, sets cwd, disables editor and browser launch, initializes the original engine, then opens its versioned loopback URL. Artwork preparation remains the original flow and requires network for initial downloads.

## Deliberate constraints

- Debug PoC only. No release signing or public APK distribution. Check upstream permission and artwork rights before distribution (ATTRIBUTION.md).
- Android wheel candidates differ from upstream (NumPy 1.26.2 vs 2.5.1; aiohttp 3.10.10); do not change desktop requirements. Revisit security and API compatibility before production.
- Existing game UI is unchanged. Android lifecycle, save/resume, bundle upgrades, and graceful shutdown are not implemented. The process must be restarted after engine failure.
- App bundle extraction is first-install only; reinstalling without clearing data will retain the old code. Use a disposable emulator/app profile for PoC iterations; clearing data destroys saves/artwork.
- Verify server binding and authentication before multiplayer use. This PoC is intended for localhost only, not LAN exposure. No untrusted custom card scripts.
- First game target: Spider-Man vs Rhino; then airplane mode after artwork preparation.

## Acceptance gates

1. Gradle debug APK resolves all native wheels.
2. Device logs show imports and local HTTP/WS probe passing.
3. Engine initialization, artwork gate and main menu work.
4. Solo game completes; compare replay and save semantics with desktop.
5. Add touch UX, process-death recovery and upstream sync tests.

Build and device results must be recorded separately; source scaffolding alone does not establish that any gate passed.
