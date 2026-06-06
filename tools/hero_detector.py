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


import cv2
import numpy as np
import imagehash
from pathlib import Path
from PIL import Image


STANDARD_PORTRAIT = (140, 182)   # (width, height) for NCC comparison


class HeroDatabase:
    """Loads portrait and model images; provides pHash-ranked candidate lists."""

    def __init__(self, portraits_path: str, models_path: str):
        self._portraits_path = Path(portraits_path)
        self._models_path = Path(models_path)
        self.portraits: dict = {}   # hero_id -> {phash, img_gray}
        self.models: dict = {}      # hero_id -> {phash, kp, des}

    def load(self):
        self._load_portraits()
        self._load_models()

    def _load_portraits(self):
        for png in self._portraits_path.glob("*.png"):
            pil = Image.open(png).convert("RGB")
            self.portraits[png.stem] = {
                "phash": imagehash.phash(pil),
                "img_gray": cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2GRAY),
            }

    def _load_models(self):
        orb = cv2.ORB_create()
        for png in self._models_path.glob("*.png"):
            pil = Image.open(png).convert("RGB")
            gray = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2GRAY)
            kp, des = orb.detectAndCompute(gray, None)
            self.models[png.stem] = {
                "phash": imagehash.phash(pil),
                "kp": kp,
                "des": des,
            }

    def top_portrait_candidates(self, query_hash, n: int = 10) -> list[str]:
        ranked = sorted(self.portraits.items(), key=lambda x: query_hash - x[1]["phash"])
        return [hid for hid, _ in ranked[:n]]

    def top_model_candidates(self, query_hash, n: int = 10) -> list[str]:
        ranked = sorted(self.models.items(), key=lambda x: query_hash - x[1]["phash"])
        return [hid for hid, _ in ranked[:n]]
