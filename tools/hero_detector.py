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
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        if self._loop and not self._loop.is_closed():
            self._loop.close()
        self._loop = None
        self._thread = None
        self._clients.clear()


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
            self._httpd = None
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None


import cv2
import numpy as np
import imagehash
from pathlib import Path
from PIL import Image


STANDARD_PORTRAIT = (140, 182)   # (width, height) for NCC comparison


def _circularity(contour: np.ndarray) -> float:
    """Isoperimetric quotient: 1.0 for a perfect circle, ~0.20 for wide rectangles."""
    area = cv2.contourArea(contour)
    perim = cv2.arcLength(contour, True)
    return float(4 * np.pi * area / (perim * perim)) if perim > 0 else 0.0


class HeroDatabase:
    """Loads portrait images; provides pHash-ranked candidate lists."""

    def __init__(self, portraits_path: str):
        self._portraits_path = Path(portraits_path)
        self.portraits: dict = {}   # hero_id -> {phash, img_gray}

    def load(self):
        self._load_portraits()

    def _load_portraits(self):
        for png in self._portraits_path.glob("*.png"):
            pil = Image.open(png).convert("RGB")
            self.portraits[png.stem] = {
                "phash": imagehash.phash(pil),
                "img_gray": cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2GRAY),
            }

    def top_portrait_candidates(self, query_hash, n: int = 10) -> list[str]:
        ranked = sorted(self.portraits.items(), key=lambda x: query_hash - x[1]["phash"])
        return [hid for hid, _ in ranked[:n]]


from PIL import ImageGrab

try:
    import mss as _mss_module
    _MSS_AVAILABLE = True
except ImportError:
    _MSS_AVAILABLE = False


def capture_screen() -> np.ndarray | None:
    """Capture primary monitor. Uses mss (DXGI) for fullscreen DX games, PIL fallback."""
    if _MSS_AVAILABLE:
        try:
            with _mss_module.mss() as sct:
                monitor = sct.monitors[1]  # primary monitor
                img = sct.grab(monitor)
                return cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)
        except Exception:
            pass
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
    _log=None,
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

    if _log:
        _log(f"[hero-detector] roster best={best_id} score={best_score:.3f} threshold={threshold:.3f}")

    return best_id if best_score >= threshold else None


_GREEN_LO = np.array([55, 150, 150], dtype=np.uint8)
_GREEN_HI = np.array([75, 255, 255], dtype=np.uint8)
_RED_LO1  = np.array([0,  150, 150], dtype=np.uint8)
_RED_HI1  = np.array([10, 255, 255], dtype=np.uint8)
_RED_LO2  = np.array([170, 150, 150], dtype=np.uint8)
_RED_HI2  = np.array([180, 255, 255], dtype=np.uint8)
_CIRCLE_MIN_AREA = 500
# Exclude only extreme edges (< 6% or > 92%): keeps turn queue bar portraits (~13%)
# and battle health circles while filtering the very top/bottom chrome.
_CIRCLE_Y_MIN_FRAC = 0.06
_CIRCLE_Y_MAX_FRAC = 0.92
# Turn queue bar occupies roughly the top 3–15% of the battle screen.
# Circles here get priority over larger health-bar fills lower on screen.
_TURN_QUEUE_Y_MAX_FRAC = 0.15
_TURN_PORTRAIT_HALF_FRAC = 0.055  # half-size of crop around circle center (fraction of h)
# Ground ring circularity filter: health-bar fills are wide rectangles (~0.20);
# the actual ground ring under the active hero is roughly circular (>0.35).
_BATTLE_RING_MIN_CIRC = 0.35
# Search strip above ring for health-bar portrait icon.
# RSL perspective view: icon floats above hero head, hundreds of pixels above ring.
_HB_SEARCH_Y_ABOVE_FRAC = 0.55   # search up to 55% of frame height above the ring
_HB_SEARCH_Y_SKIP_FRAC  = 0.04   # skip the 4% immediately above ring (glow/feet area)
_HB_SEARCH_X_HALF_FRAC  = 0.20   # horizontal half-width of search strip


def find_active_circle(frame_bgr: np.ndarray) -> tuple[int, int, str] | None:
    """Detect glowing active-turn circle. Returns (cx, cy, 'player'|'enemy') or None.

    Priority 1 — turn queue bar (top 3–15%): small green/red bordered portraits.
    Priority 2 — full screen fallback (for VS/selection screens with large bordered cards).
    Health-bar fills lower on screen are larger blobs and would otherwise always win,
    so the top-bar priority pass is essential for in-battle turn detection.
    """
    h = frame_bgr.shape[0]
    y_min = int(h * _CIRCLE_Y_MIN_FRAC)
    y_max = int(h * _CIRCLE_Y_MAX_FRAC)
    tq_y_max = int(h * _TURN_QUEUE_Y_MAX_FRAC)
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    mask_green = cv2.inRange(hsv, _GREEN_LO, _GREEN_HI)
    mask_red = cv2.bitwise_or(
        cv2.inRange(hsv, _RED_LO1, _RED_HI1),
        cv2.inRange(hsv, _RED_LO2, _RED_HI2),
    )

    def centroid_in(mask: np.ndarray, team: str,
                    row_min: int, row_max: int,
                    min_circularity: float = 0.0) -> tuple[int, int, str] | None:
        clipped = mask.copy()
        clipped[:row_min] = 0
        clipped[row_max:] = 0
        contours, _ = cv2.findContours(clipped, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        valid = [c for c in contours if cv2.contourArea(c) >= _CIRCLE_MIN_AREA]
        if not valid:
            return None
        if min_circularity > 0:
            circular = [c for c in valid if _circularity(c) >= min_circularity]
            if circular:
                valid = circular
        largest = max(valid, key=cv2.contourArea)
        M = cv2.moments(largest)
        if M["m00"] == 0:
            return None
        cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
        if not (row_min <= cy < row_max):
            return None
        return cx, cy, team

    # Priority: turn queue bar at top (no circularity filter — portrait borders may be irregular)
    result = (centroid_in(mask_green, "player", y_min, tq_y_max) or
              centroid_in(mask_red, "enemy", y_min, tq_y_max))
    if result:
        return result
    # Fallback: full screen with circularity filter to prefer the ground ring over health-bar fills.
    # Health-bar fills are wide rectangles (~0.20 circularity); the ground ring is ~circular (>0.35).
    return (centroid_in(mask_green, "player", y_min, y_max, _BATTLE_RING_MIN_CIRC) or
            centroid_in(mask_red,   "enemy",  y_min, y_max, _BATTLE_RING_MIN_CIRC))


class BattleCache:
    """Maps screen positions to hero IDs within one battle. Cleared between battles.

    A position must produce the same hero_id for min_hits consecutive ticks before
    it is confirmed, preventing noisy UI elements from polluting the cache.
    """

    def __init__(self, position_tolerance: int = 50, min_hits: int = 3):
        self._tolerance = position_tolerance
        self._min_hits = min_hits
        self._entries: list[tuple[int, int, str]] = []
        self._pending: dict[tuple[int, int], tuple[str, int]] = {}

    def _pending_key(self, cx: int, cy: int) -> tuple[int, int] | None:
        for (px, py) in self._pending:
            if abs(cx - px) <= self._tolerance and abs(cy - py) <= self._tolerance:
                return (px, py)
        return None

    def lookup(self, cx: int, cy: int) -> str | None:
        for ex, ey, hero_id in self._entries:
            if abs(cx - ex) <= self._tolerance and abs(cy - ey) <= self._tolerance:
                return hero_id
        return None

    def store(self, cx: int, cy: int, hero_id: str):
        """Accumulate hit; confirms entry after min_hits consecutive same-hero detections."""
        key = self._pending_key(cx, cy)
        if key is None:
            key = (cx, cy)
            self._pending[key] = (hero_id, 0)
        prev_id, count = self._pending[key]
        if prev_id != hero_id:
            self._pending[key] = (hero_id, 1)
            count = 1
        else:
            count += 1
            self._pending[key] = (hero_id, count)
        if count >= self._min_hits:
            self._entries.append((cx, cy, hero_id))
            del self._pending[key]

    def clear(self):
        self._entries.clear()
        self._pending.clear()


def detect_battle_hero(
    frame_bgr: np.ndarray,
    cx: int,
    cy: int,
    db: HeroDatabase,
    cache: BattleCache,
    threshold: float = 0.80,
    _log=None,
) -> str | None:
    """Identify active hero by portrait-matching the health-bar icon above the ground ring.

    The circle detector finds the green/red ground ring at the active hero's feet (cx, cy).
    RSL battle has no portrait images at ground level — the health-bar portrait icon floats
    hundreds of pixels above. We search a generous vertical strip above (cx, cy) and pick
    the sub-window with the highest average brightness (most portrait-like content).
    """
    cached = cache.lookup(cx, cy)
    if cached:
        return cached

    if not db.portraits:
        return None

    h, w = frame_bgr.shape[:2]
    skip_px  = int(h * _HB_SEARCH_Y_SKIP_FRAC)
    above_px = int(h * _HB_SEARCH_Y_ABOVE_FRAC)
    x_half   = int(w * _HB_SEARCH_X_HALF_FRAC)

    strip_y1 = max(cy - above_px, 0)
    strip_y2 = max(cy - skip_px, 0)
    strip_x1 = max(cx - x_half, 0)
    strip_x2 = min(cx + x_half, w)
    strip = frame_bgr[strip_y1:strip_y2, strip_x1:strip_x2]
    if strip.size == 0:
        return None

    crop = _best_portrait_crop(strip)

    if _log:
        _log(f"[hero-detector] battle strip=({strip_x1},{strip_y1},{strip_x2},{strip_y2}) crop={crop.shape}")

    try:
        query_hash = imagehash.phash(Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)))
        candidates = db.top_portrait_candidates(query_hash, n=10)

        best_id, best_score = None, 0.0
        for hero_id in candidates:
            score = match_portrait(crop, db.portraits[hero_id]["img_gray"])
            if score > best_score:
                best_score, best_id = score, hero_id

        if _log:
            _log(f"[hero-detector] battle best={best_id} score={best_score:.3f} threshold={threshold:.3f}")
    except Exception as exc:
        if _log:
            _log(f"[hero-detector] battle error: {exc}")
        return None

    if best_score >= threshold and best_id:
        cache.store(cx, cy, best_id)
        return cache.lookup(cx, cy)  # None until min_hits reached
    return None



# ── OBS Python bindings ────────────────────────────────────────────────────
# Executed only when loaded inside OBS. All imports and globals are scoped
# to this try/except block so pytest can import this file without OBS.

try:
    import obspython as obs
    obs.script_log(obs.LOG_INFO, "[hero-detector] script file parsed OK v=RING-ONLY-3")

    _server: DetectorServer | None = None
    _overlay: OverlayServer | None = None
    _db: HeroDatabase | None = None
    _cache: BattleCache = BattleCache()
    _last_hero_id: str | None = None

    _S_PORTRAITS   = "portraits_path"
    _S_PORT        = "ws_port"
    _S_INTERVAL    = "interval_ms"
    _S_P_THRESH    = "portrait_threshold"
    _S_M_THRESH    = "model_threshold"
    _S_OVERLAY_DIR = "overlay_dir"
    _S_HTTP_PORT   = "http_port"

    _portraits_path     = ""
    _ws_port            = 7182
    _interval_ms        = 1500
    _portrait_threshold = 0.82
    _model_threshold    = 0.80
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
        obs.obs_data_set_default_int(   settings, _S_PORT,        7182)
        obs.obs_data_set_default_int(   settings, _S_INTERVAL,    1500)
        obs.obs_data_set_default_double(settings, _S_P_THRESH,    0.82)
        obs.obs_data_set_default_double(settings, _S_M_THRESH,    0.80)

    def script_update(settings):
        global _portraits_path, _ws_port, _interval_ms
        global _portrait_threshold, _model_threshold, _overlay_dir, _http_port
        _overlay_dir        = obs.obs_data_get_string(settings, _S_OVERLAY_DIR)
        _http_port          = obs.obs_data_get_int(   settings, _S_HTTP_PORT)
        _portraits_path     = obs.obs_data_get_string(settings, _S_PORTRAITS)
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
        _db = HeroDatabase(_portraits_path)
        try:
            _db.load()
            obs.script_log(obs.LOG_INFO,
                f"[hero-detector] Loaded {len(_db.portraits)} portraits")
        except Exception as e:
            obs.script_log(obs.LOG_WARNING, f"[hero-detector] DB load failed: {e}")
            return
        obs.timer_add(_detect_tick, _interval_ms)

    def script_unload():
        global _server, _overlay, _db, _last_hero_id
        obs.timer_remove(_detect_tick)
        if _server:
            _server.stop()
            _server = None
        if _overlay:
            _overlay.stop()
            _overlay = None
        _db = None
        _last_hero_id = None
        import gc
        gc.collect()

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
        _dbg = lambda m: obs.script_log(obs.LOG_INFO, m) if _tick_count % 5 == 0 else None
        hero_id = detect_roster_hero(frame, _db, threshold=_portrait_threshold, _log=_dbg)

        if hero_id is None:
            circle = find_active_circle(frame)
            if _tick_count % 5 == 0:
                if circle:
                    obs.script_log(obs.LOG_INFO,
                        f"[hero-detector] circle={circle}")
                else:
                    obs.script_log(obs.LOG_INFO,
                        f"[hero-detector] tick={_tick_count} no roster, no circle, frame={frame.shape}")
            if circle:
                cx, cy, _team = circle
                hero_id = detect_battle_hero(frame, cx, cy, _db, _cache,
                                             threshold=_model_threshold,
                                             _log=lambda m: obs.script_log(obs.LOG_INFO, m))
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
