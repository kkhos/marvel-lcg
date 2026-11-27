"""Android-only bootstrap. Never import the game before setting cwd and argv."""
import asyncio
import importlib
import os
import sys
import threading
import traceback
import time
from pathlib import Path
from urllib.parse import quote

HOST = "127.0.0.1"
PORT = 2345
_status = "Not started"
_url = ""
_lock = threading.Lock()
_started = False
_stopping = threading.Event()
_engine = None


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
    global _status, _url, _engine
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
        _engine = engine
        from engine.network.net_lib import NetLib
        _status = "Waiting for local server port"
        deadline = time.monotonic() + 5
        while not NetLib.IsPortAvailable(HOST, PORT):
            if _stopping.is_set():
                return
            if time.monotonic() >= deadline:
                raise RuntimeError(f"Local port {HOST}:{PORT} is still in use. Stop the other listener and restart the app.")
            time.sleep(.2)
        if _stopping.is_set():
            return
        _status = "Initializing cards, artwork and server"
        initialized = engine.Initialize()
        if not initialized:
            raise RuntimeError("Engine.Initialize returned False")
        # Publish the URL only after this engine's own listener has bound.
        servers = [s for s in engine.device_manager.httpds if s.ip == HOST and s.port == PORT]
        if len(servers) != 1:
            raise RuntimeError(f"Expected one local game server at {HOST}:{PORT}")
        server = servers[0]
        if not server.startup_event.wait(15):
            raise RuntimeError("Local game server did not start within 15 seconds")
        if server.startup_error is not None:
            raise RuntimeError(f"Local game server failed at {HOST}:{PORT}: {server.startup_error}") from server.startup_error
        if _stopping.is_set():
            return
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


def stop_listening():
    """Bounded best-effort listener shutdown; the Activity then ends the process."""
    global _url
    _stopping.set()
    _url = ""
    manager = getattr(_engine, "device_manager", None)
    for server in getattr(manager, "httpds", []):
        try:
            server.StopListening(timeout=.6)
        except Exception:
            pass


def status():
    return _status


def url():
    return _url
