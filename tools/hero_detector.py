"""RSL Hero Auto-Detector — OBS Python script + detection utilities.

All detection logic is importable without OBS.
OBS bindings are at the bottom, guarded by try/except ImportError.
Requires Python 3.10+, opencv-python, Pillow, imagehash, websockets.
"""
import asyncio
import http.server
import json
import socketserver
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
        async with websockets.serve(self._handler, "localhost", self.port,
                                    reuse_address=True):
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
        if self._thread:
            self._thread.join(timeout=2.0)


class OverlayServer:
    """Minimal HTTP server that serves the OBS overlay directory in a daemon thread."""

    def __init__(self, directory: str, port: int = 8765):
        self.directory = directory
        self.port = port
        self._httpd: socketserver.TCPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self):
        directory = self.directory
        class _Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=directory, **kwargs)
            def log_message(self, *args):
                pass  # suppress access logs in OBS Script Log
        self._httpd = socketserver.TCPServer(("localhost", self.port), _Handler)
        self._httpd.allow_reuse_address = True
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        if self._httpd:
            self._httpd.shutdown()


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


_GREEN_LO = np.array([55, 150, 150], dtype=np.uint8)
_GREEN_HI = np.array([75, 255, 255], dtype=np.uint8)
_RED_LO1  = np.array([0,  150, 150], dtype=np.uint8)
_RED_HI1  = np.array([10, 255, 255], dtype=np.uint8)
_RED_LO2  = np.array([170, 150, 150], dtype=np.uint8)
_RED_HI2  = np.array([180, 255, 255], dtype=np.uint8)
_CIRCLE_MIN_AREA = 500
# Ignore circles in UI zones: top 6% (turn queue bar) and bottom 8% (skill bar)
_CIRCLE_Y_MIN_FRAC = 0.06
_CIRCLE_Y_MAX_FRAC = 0.92


def find_active_circle(frame_bgr: np.ndarray) -> tuple[int, int, str] | None:
    """Detect glowing active-turn circle. Returns (cx, cy, 'player'|'enemy') or None."""
    h = frame_bgr.shape[0]
    y_min = int(h * _CIRCLE_Y_MIN_FRAC)
    y_max = int(h * _CIRCLE_Y_MAX_FRAC)
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    mask_green = cv2.inRange(hsv, _GREEN_LO, _GREEN_HI)
    mask_red = cv2.bitwise_or(
        cv2.inRange(hsv, _RED_LO1, _RED_HI1),
        cv2.inRange(hsv, _RED_LO2, _RED_HI2),
    )

    def centroid(mask: np.ndarray, team: str) -> tuple[int, int, str] | None:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) < _CIRCLE_MIN_AREA:
            return None
        M = cv2.moments(largest)
        if M["m00"] == 0:
            return None
        cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
        if not (y_min <= cy <= y_max):
            return None
        return cx, cy, team

    return centroid(mask_green, "player") or centroid(mask_red, "enemy")


def match_model_orb(
    query_gray: np.ndarray,
    query_kp,
    query_des,
    ref_kp,
    ref_des,
    distance_threshold: int = 50,
) -> float:
    """ORB feature match ratio. Returns good_matches / total_query_keypoints (0–1)."""
    if query_des is None or ref_des is None or not query_kp:
        return 0.0
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(query_des, ref_des)
    good = [m for m in matches if m.distance < distance_threshold]
    return len(good) / max(len(query_kp), 1)


class BattleCache:
    """Maps screen positions to hero IDs within one battle. Cleared between battles."""

    def __init__(self, position_tolerance: int = 50):
        self._tolerance = position_tolerance
        self._entries: list[tuple[int, int, str]] = []

    def lookup(self, cx: int, cy: int) -> str | None:
        for ex, ey, hero_id in self._entries:
            if abs(cx - ex) <= self._tolerance and abs(cy - ey) <= self._tolerance:
                return hero_id
        return None

    def store(self, cx: int, cy: int, hero_id: str):
        self._entries.append((cx, cy, hero_id))

    def clear(self):
        self._entries.clear()


def detect_battle_hero(
    frame_bgr: np.ndarray,
    cx: int,
    cy: int,
    db: HeroDatabase,
    cache: BattleCache,
    threshold: float = 0.65,
) -> str | None:
    """Identify hero above circle centroid. Checks cache first, then runs ORB match."""
    cached = cache.lookup(cx, cy)
    if cached:
        return cached

    h, w = frame_bgr.shape[:2]
    crop_w = int(w * 0.10)
    crop_h = int(h * 0.32)
    x1 = max(cx - crop_w // 2, 0)
    y1 = max(cy - crop_h, 0)
    x2 = min(cx + crop_w // 2, w)
    y2 = cy
    crop = frame_bgr[y1:y2, x1:x2]
    if crop.size == 0:
        return None

    crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    query_hash = imagehash.phash(Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)))
    candidates = db.top_model_candidates(query_hash, n=10)

    orb = cv2.ORB_create()
    query_kp, query_des = orb.detectAndCompute(crop_gray, None)

    best_id, best_score = None, 0.0
    for hero_id in candidates:
        m = db.models[hero_id]
        score = match_model_orb(crop_gray, query_kp, query_des, m["kp"], m["des"])
        if score > best_score:
            best_score, best_id = score, hero_id

    if best_score >= threshold and best_id:
        cache.store(cx, cy, best_id)
        return best_id
    return None


# ── OBS Python bindings ────────────────────────────────────────────────────
# Executed only when loaded inside OBS. All imports and globals are scoped
# to this try/except block so pytest can import this file without OBS.

try:
    import obspython as obs
    obs.script_log(obs.LOG_INFO, "[hero-detector] script file parsed OK")

    _server: DetectorServer | None = None
    _overlay: OverlayServer | None = None
    _db: HeroDatabase | None = None
    _cache: BattleCache = BattleCache()
    _last_hero_id: str | None = None

    _S_PORTRAITS   = "portraits_path"
    _S_MODELS      = "models_path"
    _S_PORT        = "ws_port"
    _S_INTERVAL    = "interval_ms"
    _S_P_THRESH    = "portrait_threshold"
    _S_M_THRESH    = "model_threshold"
    _S_OVERLAY_DIR = "overlay_dir"
    _S_HTTP_PORT   = "http_port"

    _portraits_path     = ""
    _models_path        = ""
    _ws_port            = 7182
    _interval_ms        = 1500
    _portrait_threshold = 0.82
    _model_threshold    = 0.65
    _overlay_dir        = ""
    _http_port          = 8765

    def script_description():
        return (
            "<b>RSL Hero Auto-Detector</b><br>"
            "Detects active hero on screen and pushes to OBS overlay via WebSocket.<br>"
            "Add a Browser Source with URL: <b>http://localhost:8765/obs/obs.html</b>"
        )

    def script_properties():
        props = obs.obs_properties_create()
        obs.obs_properties_add_text(props, _S_OVERLAY_DIR, "Overlay directory (twitch-extension repo)", obs.OBS_TEXT_DEFAULT)
        obs.obs_properties_add_int(  props, _S_HTTP_PORT,  "HTTP port (Browser Source)",  1024, 65535, 1)
        obs.obs_properties_add_text(props, _S_PORTRAITS,   "Portraits DB path",           obs.OBS_TEXT_DEFAULT)
        obs.obs_properties_add_text(props, _S_MODELS,      "Models DB path",              obs.OBS_TEXT_DEFAULT)
        obs.obs_properties_add_int(  props, _S_PORT,       "WebSocket port",              1024, 65535, 1)
        obs.obs_properties_add_int(  props, _S_INTERVAL,   "Detection interval (ms)",     500, 10000, 100)
        obs.obs_properties_add_float(props, _S_P_THRESH,   "Portrait confidence threshold", 0.0, 1.0, 0.01)
        obs.obs_properties_add_float(props, _S_M_THRESH,   "Model confidence threshold",    0.0, 1.0, 0.01)
        obs.obs_properties_add_button(props, "clear_cache", "Clear battle cache", _on_clear_cache)
        return props

    def script_defaults(settings):
        _base = Path(__file__).parent.parent / "data"
        _overlay_default = str(Path(__file__).parent.parent.parent / "twitch-extension")
        obs.obs_data_set_default_string(settings, _S_OVERLAY_DIR, _overlay_default)
        obs.obs_data_set_default_int(   settings, _S_HTTP_PORT,   8765)
        obs.obs_data_set_default_string(settings, _S_PORTRAITS,   str(_base / "portraits"))
        obs.obs_data_set_default_string(settings, _S_MODELS,      str(_base / "models"))
        obs.obs_data_set_default_int(   settings, _S_PORT,        7182)
        obs.obs_data_set_default_int(   settings, _S_INTERVAL,    1500)
        obs.obs_data_set_default_double(settings, _S_P_THRESH,    0.82)
        obs.obs_data_set_default_double(settings, _S_M_THRESH,    0.65)

    def script_update(settings):
        global _portraits_path, _models_path, _ws_port, _interval_ms
        global _portrait_threshold, _model_threshold, _overlay_dir, _http_port
        _overlay_dir        = obs.obs_data_get_string(settings, _S_OVERLAY_DIR)
        _http_port          = obs.obs_data_get_int(   settings, _S_HTTP_PORT)
        _portraits_path     = obs.obs_data_get_string(settings, _S_PORTRAITS)
        _models_path        = obs.obs_data_get_string(settings, _S_MODELS)
        _ws_port            = obs.obs_data_get_int(   settings, _S_PORT)
        _interval_ms        = obs.obs_data_get_int(   settings, _S_INTERVAL)
        _portrait_threshold = obs.obs_data_get_double(settings, _S_P_THRESH)
        _model_threshold    = obs.obs_data_get_double(settings, _S_M_THRESH)

    def script_load(settings):
        global _server, _overlay, _db
        script_update(settings)  # ensure paths/ports are read before use
        _overlay = OverlayServer(directory=_overlay_dir, port=_http_port)
        try:
            _overlay.start()
            obs.script_log(obs.LOG_INFO,
                f"[hero-detector] Overlay served at http://localhost:{_http_port}/obs/obs.html")
        except Exception as e:
            obs.script_log(obs.LOG_WARNING, f"[hero-detector] HTTP server failed: {e}")
        _server = DetectorServer(port=_ws_port)
        _server.start()
        _db = HeroDatabase(_portraits_path, _models_path)
        try:
            _db.load()
            obs.script_log(obs.LOG_INFO,
                f"[hero-detector] Loaded {len(_db.portraits)} portraits, {len(_db.models)} models")
        except Exception as e:
            obs.script_log(obs.LOG_WARNING, f"[hero-detector] DB load failed: {e}")
            return
        obs.timer_add(_detect_tick, _interval_ms)

    def script_unload():
        obs.timer_remove(_detect_tick)
        if _server:
            _server.stop()
        if _overlay:
            _overlay.stop()

    def _on_clear_cache(props, prop):
        _cache.clear()
        obs.script_log(obs.LOG_INFO, "[hero-detector] Battle cache cleared")
        return True

    _tick_count = 0

    def _detect_tick():
        global _last_hero_id, _db, _server, _cache, _portrait_threshold, _model_threshold, _tick_count
        if _db is None or _server is None:
            return
        frame = capture_screen()
        if frame is None:
            obs.script_log(obs.LOG_WARNING, "[hero-detector] capture_screen returned None")
            return

        _tick_count += 1
        hero_id = detect_roster_hero(frame, _db, threshold=_portrait_threshold)

        if hero_id is None:
            circle = find_active_circle(frame)
            if _tick_count % 5 == 0:  # log every ~7.5s to avoid spam
                if circle:
                    obs.script_log(obs.LOG_INFO,
                        f"[hero-detector] circle={circle}, models={len(_db.models)}")
                else:
                    obs.script_log(obs.LOG_INFO,
                        f"[hero-detector] tick={_tick_count} no roster, no circle, frame={frame.shape}")
            if circle:
                cx, cy, _team = circle
                hero_id = detect_battle_hero(frame, cx, cy, _db, _cache,
                                             threshold=_model_threshold)
        else:
            if _tick_count % 5 == 0:
                obs.script_log(obs.LOG_INFO, f"[hero-detector] roster candidate: {hero_id}")

        if hero_id and hero_id != _last_hero_id:
            _server.push({"type": "hero", "id": hero_id})
            _last_hero_id = hero_id
        elif not hero_id and _last_hero_id:
            _server.push({"type": "hero", "id": None})
            _last_hero_id = None

except ImportError:
    pass  # Running outside OBS (pytest, etc.)
