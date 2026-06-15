# tests/test_detection.py
import cv2
import numpy as np
import pytest
from PIL import Image


def make_portrait(color_bgr: tuple, size=(140, 182)) -> np.ndarray:
    return np.full((*reversed(size), 3), color_bgr, dtype=np.uint8)


@pytest.fixture
def portrait_db(tmp_path):
    portraits = tmp_path / "portraits"
    portraits.mkdir()
    for hero_id, color in [("hero_a", (200, 80, 50)), ("hero_b", (50, 200, 80)), ("hero_c", (80, 50, 200))]:
        cv2.imwrite(str(portraits / f"{hero_id}.png"), make_portrait(color))
    return str(portraits)


def test_database_loads_portraits(portrait_db):
    from hero_detector import HeroDatabase
    db = HeroDatabase(portrait_db)
    db.load()
    assert len(db.portraits) == 3
    assert "hero_a" in db.portraits
    assert "phash" in db.portraits["hero_a"]
    assert "img_gray" in db.portraits["hero_a"]


def test_top_portrait_candidates_returns_closest(portrait_db):
    from hero_detector import HeroDatabase
    import imagehash
    db = HeroDatabase(portrait_db)
    db.load()
    img_a = make_portrait((200, 80, 50))
    query_hash = imagehash.phash(Image.fromarray(cv2.cvtColor(img_a, cv2.COLOR_BGR2RGB)))
    candidates = db.top_portrait_candidates(query_hash, n=2)
    assert candidates[0] == "hero_a"


def test_match_portrait_identical_returns_high_score():
    from hero_detector import match_portrait
    img = make_portrait((200, 80, 50))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    assert match_portrait(img, gray) > 0.95


def test_match_portrait_different_returns_low_score():
    from hero_detector import match_portrait
    img = make_portrait((200, 80, 50))
    other = cv2.cvtColor(make_portrait((50, 200, 80)), cv2.COLOR_BGR2GRAY)
    assert match_portrait(img, other) < 0.70


def test_detect_roster_hero_finds_correct_hero(portrait_db):
    from hero_detector import HeroDatabase, detect_roster_hero
    db = HeroDatabase(portrait_db)
    db.load()
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    # Place hero_b portrait inside the roster ROI (60–85% width, 10–70% height)
    x1, y1 = int(1920 * 0.60), int(1080 * 0.10)
    frame[y1:y1+182, x1:x1+140] = make_portrait((50, 200, 80))  # hero_b color
    assert detect_roster_hero(frame, db, threshold=0.90) == "hero_b"


def test_detect_roster_hero_returns_none_for_empty_frame(portrait_db):
    from hero_detector import HeroDatabase, detect_roster_hero
    db = HeroDatabase(portrait_db)
    db.load()
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    assert detect_roster_hero(frame, db, threshold=0.90) is None


def make_circle_frame(center: tuple, color_bgr: tuple, radius: int = 45) -> np.ndarray:
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    cv2.circle(frame, center, radius, color_bgr, -1)
    return frame


def test_finds_green_circle_as_player():
    from hero_detector import find_active_circle
    frame = make_circle_frame((960, 800), (0, 230, 0))
    result = find_active_circle(frame)
    assert result is not None
    cx, cy, team = result
    assert team == "player"
    assert abs(cx - 960) < 60
    assert abs(cy - 800) < 60


def test_finds_red_circle_as_enemy():
    from hero_detector import find_active_circle
    frame = make_circle_frame((500, 600), (0, 0, 230))
    result = find_active_circle(frame)
    assert result is not None
    assert result[2] == "enemy"


def test_no_circle_in_black_frame():
    from hero_detector import find_active_circle
    assert find_active_circle(np.zeros((1080, 1920, 3), dtype=np.uint8)) is None


def test_tiny_green_speck_does_not_trigger():
    from hero_detector import find_active_circle
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    cv2.circle(frame, (100, 100), 5, (0, 230, 0), -1)   # area < min threshold
    assert find_active_circle(frame) is None


def test_battle_cache_stores_and_retrieves():
    from hero_detector import BattleCache
    cache = BattleCache(position_tolerance=50, min_hits=1)
    cache.store(500, 700, "abbess")
    assert cache.lookup(510, 690) == "abbess"
    assert cache.lookup(600, 800) is None


def test_battle_cache_requires_min_hits():
    from hero_detector import BattleCache
    cache = BattleCache(position_tolerance=50, min_hits=3)
    cache.store(500, 700, "abbess")
    assert cache.lookup(500, 700) is None  # 1/3
    cache.store(500, 700, "abbess")
    assert cache.lookup(500, 700) is None  # 2/3
    cache.store(500, 700, "abbess")
    assert cache.lookup(510, 690) == "abbess"  # confirmed


def test_battle_cache_resets_on_different_hero():
    from hero_detector import BattleCache
    cache = BattleCache(position_tolerance=50, min_hits=3)
    cache.store(500, 700, "abbess")
    cache.store(500, 700, "abbess")
    cache.store(500, 700, "arbiter")  # different hero — resets count
    cache.store(500, 700, "arbiter")
    assert cache.lookup(500, 700) is None  # only 2 hits of arbiter


def test_battle_cache_clears():
    from hero_detector import BattleCache
    cache = BattleCache(position_tolerance=50, min_hits=1)
    cache.store(500, 700, "abbess")
    cache.clear()
    assert cache.lookup(500, 700) is None


def test_detect_battle_hero_matches_portrait_at_circle(portrait_db):
    from hero_detector import HeroDatabase, BattleCache, detect_battle_hero
    db = HeroDatabase(portrait_db)
    db.load()
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    cx, cy = 960, 800
    # Fill a large patch above the ring with hero_b color so that _best_portrait_crop
    # finds a fully-filled scan window (solid-color crop matches solid-color template).
    frame[300:600, 800:1100] = np.full((300, 300, 3), (50, 200, 80), dtype=np.uint8)
    cache = BattleCache(min_hits=1)
    assert detect_battle_hero(frame, cx, cy, db, cache, threshold=0.80) == "hero_b"


def test_detect_battle_hero_returns_cached(portrait_db):
    from hero_detector import HeroDatabase, BattleCache, detect_battle_hero
    db = HeroDatabase(portrait_db)
    db.load()
    cache = BattleCache(min_hits=1)
    cache.store(857, 148, "hero_a")
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    assert detect_battle_hero(frame, 857, 148, db, cache) == "hero_a"


def test_detect_battle_hero_no_portraits_returns_none():
    from hero_detector import HeroDatabase, BattleCache, detect_battle_hero
    db = HeroDatabase("")
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    cache = BattleCache()
    assert detect_battle_hero(frame, 857, 148, db, cache) is None
