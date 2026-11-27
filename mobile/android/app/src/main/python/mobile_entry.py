"""Android-only bootstrap. Never import the game before setting cwd and argv."""
import asyncio
import importlib
import os
import sys
import threading
import traceback
from pathlib import Path
from urllib.parse import quote

HOST = "127.0.0.1"
PORT = 2345
_status = "Not started"
_url = ""
_lock = threading.Lock()
_started = False


def probe():
    """Verify actual native imports and HTTP + WebSocket on a temporary port."""
    versions = [sys.version]
    for name in ("packaging", "PIL", "numpy", "requests", "aiohttp",
                 "typing_extensions", "colorama"):
        mod = importlib.import_module(name)
        versions.append(f"{name}: {getattr(mod, '__version__', 'OK')}")
    import numpy as np
    from PIL import Image
    assert int(np.array([1, 2]).sum()) == 3
    assert Image.new("RGB", (2, 2)).size == (2, 2)
    asyncio.run(_network_probe())
    return "\n".join(versions + ["HTTP / WebSocket: OK"])


async def _network_probe():
    from aiohttp import ClientSession, web

    async def health(request):
        return web.Response(text="ok")

    async def echo(request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        async for msg in ws:
            await ws.send_str(msg.data)
        return ws

    app = web.Application()
    app.router.add_get("/health", health)
    app.router.add_get("/ws", echo)
    runner = web.AppRunner(app)
    await runner.setup()
    try:
        site = web.TCPSite(runner, HOST, 0)
        await site.start()
        port = runner.addresses[0][1]
        async with ClientSession() as client:
            async with client.get(f"http://{HOST}:{port}/health") as resp:
                assert await resp.text() == "ok"
            async with client.ws_connect(f"http://{HOST}:{port}/ws") as ws:
                await ws.send_str("ping")
                assert (await ws.receive(timeout=5)).data == "ping"
    finally:
        await runner.cleanup()


def start(root):
    global _started, _status
    with _lock:
        if _started:
            return
        _started = True
        _status = "Starting game engine"
    threading.Thread(target=_run, args=(root,), name="marvel-engine", daemon=True).start()


def _run(root):
    global _status, _url
    engine = None
    initialized = False
    try:
        root = str(Path(root).resolve())
        os.chdir(root)
        sys.path.insert(0, root)
        sys.argv = ["main.py", "-no_editor", "-no_open_browser_on_startup"]
        _status = "Importing game engine"
        from engine import Engine
        engine = Engine
        _status = "Initializing cards, artwork and server"
        initialized = engine.Initialize()
        if not initialized:
            raise RuntimeError("Engine.Initialize returned False")
        from engine.lib import Ver
        _url = f"http://{HOST}:{PORT}/main?v={quote(Ver.ui_version_str, safe='')}"
        _status = "Engine initialized; waiting for WebView"
        engine.EngineRun()
        _status = "Engine stopped"
    except BaseException:
        _status = traceback.format_exc()
    finally:
        _url = ""
        if initialized:
            try:
                engine.Shutdown()
            except BaseException:
                _status += "\n" + traceback.format_exc()


def status():
    return _status


def url():
    return _url
