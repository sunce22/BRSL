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


from PIL import ImageGrab


def capture_screen() -> np.ndarray | None:
    """Capture full screen. Returns BGR numpy array or None on failure."""
    try:
        return cv2.cvtColor(np.array(ImageGrab.grab()), cv2.COLOR_RGB2BGR)
    except Exception:
        return None


def match_portrait(roi_bgr: np.ndarray, template_gray: np.ndarray) -> float:
    """Normalized cross-correlation between roi_bgr and template_gray. Returns 0.0–1.0."""
    roi_gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
    roi_r = cv2.resize(roi_gray, STANDARD_PORTRAIT).astype(np.float32) / 255.0
    tmpl_r = cv2.resize(template_gray, STANDARD_PORTRAIT).astype(np.float32) / 255.0
    roi_std, tmpl_std = roi_r.std(), tmpl_r.std()
    if roi_std < 1e-6 and tmpl_std < 1e-6:
        # Both constant — identical if means are very close, else no match
        diff = abs(float(roi_r.mean()) - float(tmpl_r.mean()))
        return 1.0 if diff < 1e-4 else 0.0
    if roi_std < 1e-6 or tmpl_std < 1e-6:
        return 0.0
    ncc = float(np.mean((roi_r - roi_r.mean()) * (tmpl_r - tmpl_r.mean())) / (roi_std * tmpl_std))
    return (ncc + 1.0) / 2.0


def _best_portrait_crop(roi_bgr: np.ndarray) -> np.ndarray:
    """Return the sub-crop of roi_bgr most likely to contain a portrait.

    Strategy: find the first non-black STANDARD_PORTRAIT-sized window by scanning
    a coarse grid; fall back to the whole ROI resized if nothing stands out.
    """
    ph, pw = STANDARD_PORTRAIT[1], STANDARD_PORTRAIT[0]  # height, width
    rh, rw = roi_bgr.shape[:2]
    if rh <= ph and rw <= pw:
        return roi_bgr

    # Coarse scan: stride = portrait size // 2
    stride_x = max(pw // 2, 1)
    stride_y = max(ph // 2, 1)
    best_crop = roi_bgr[:ph, :pw]
    best_mean = 0.0
    for gy in range(0, rh - ph + 1, stride_y):
        for gx in range(0, rw - pw + 1, stride_x):
            crop = roi_bgr[gy:gy + ph, gx:gx + pw]
            m = float(crop.mean())
            if m > best_mean:
                best_mean = m
                best_crop = crop
    return best_crop


def detect_roster_hero(
    frame_bgr: np.ndarray,
    db: HeroDatabase,
    threshold: float = 0.82,
) -> str | None:
    """Detect hero portrait in the roster detail panel. Returns hero_id or None."""
    if not db.portraits:
        return None
    h, w = frame_bgr.shape[:2]
    x1, y1 = int(w * 0.60), int(h * 0.10)
    x2, y2 = int(w * 0.85), int(h * 0.70)
    roi = frame_bgr[y1:y2, x1:x2]

    crop = _best_portrait_crop(roi)
    query_hash = imagehash.phash(Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)))
    candidates = db.top_portrait_candidates(query_hash, n=10)

    best_id, best_score = None, 0.0
    for hero_id in candidates:
        score = match_portrait(crop, db.portraits[hero_id]["img_gray"])
        if score > best_score:
            best_score, best_id = score, hero_id

    return best_id if best_score >= threshold else None
