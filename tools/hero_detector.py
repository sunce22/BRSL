"""RSL Hero Auto-Detector — OBS Python script + detection utilities.

All detection logic is importable without OBS.
OBS bindings are at the bottom, guarded by try/except ImportError.
Requires Python 3.10+, opencv-python, Pillow, imagehash, websockets.
"""
import asyncio
import json
import threading
import websockets


class DetectorServer:
    """Asyncio WebSocket server running in a background daemon thread."""

    def __init__(self, port: int = 7182):
        self.port = port
        self._clients: set = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None

    def start(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._serve())

    async def _serve(self):
        async with websockets.serve(self._handler, "localhost", self.port):
            await asyncio.Future()

    async def _handler(self, websocket, path=None):
        self._clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self._clients.discard(websocket)

    def push(self, msg: dict):
        if not self._loop or not self._clients:
            return
        asyncio.run_coroutine_threadsafe(self._broadcast(json.dumps(msg)), self._loop)

    async def _broadcast(self, message: str):
        for ws in list(self._clients):
            try:
                await ws.send(message)
            except Exception:
                self._clients.discard(ws)

    def stop(self):
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
