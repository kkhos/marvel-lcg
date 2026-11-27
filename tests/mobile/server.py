"""CI-only launcher: real game engine, deterministic synthetic card artwork.

Do not bundle this file into the APK. Production artwork checks are unchanged.
"""
import hashlib
import io
import os
import sys
from pathlib import Path
from functools import lru_cache

ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
sys.argv = ["main.py", "-no_editor", "-no_open_browser_on_startup", "-no_statistics"]

from engine import Engine
from engine.file import Cache
from PIL import Image, ImageDraw


@lru_cache(maxsize=4096)
def fixture_image(card_id):
    key = str(card_id)
    digest = hashlib.sha256(key.encode()).digest()
    img = Image.new("RGB", (140, 194), tuple(55 + x % 150 for x in digest[:3]))
    draw = ImageDraw.Draw(img)
    draw.rectangle((3, 3, 136, 190), outline="white", width=3)
    draw.rectangle((9, 120, 130, 181), fill="#eeeeee")
    draw.text((12, 130), key[-18:], fill="black")
    draw.text((12, 150), "CI ARTWORK", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# Only this test process bypasses the artwork preparation gate.
Cache.InitializeArtwork = staticmethod(lambda: None)
Cache.GetArtworkStatus = staticmethod(lambda: {
    "state": "ready", "ready": True, "can_play": True, "release_ready": True,
    "completed_cards": 1, "total_cards": 1, "completed_packs": 1, "total_packs": 1,
})
Cache.ArtworkReadyForSelection = staticmethod(lambda kind, payload: payload is not None)
Cache.ArtworkReadyFor = staticmethod(lambda ids: True)
Cache.LoadImage = staticmethod(fixture_image)
Cache.GetImageState = staticmethod(lambda card_id: "ready")
Cache.GetImageRetrySeconds = staticmethod(lambda card_id: None)

if __name__ == "__main__":
    if not Engine.Initialize():
        raise RuntimeError("Game engine initialization failed")
    try:
        Engine.EngineRun()
    finally:
        Engine.Shutdown()
