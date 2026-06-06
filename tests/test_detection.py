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


def make_textured_portrait(color_bgr: tuple, size=(140, 182)) -> np.ndarray:
    img = make_portrait(color_bgr, size)
    np.random.seed(42)
    noise = np.random.randint(-30, 30, img.shape, dtype=np.int16)
    return np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)


@pytest.fixture
def model_db(tmp_path):
    models = tmp_path / "models"
    models.mkdir()
    for hero_id, color in [("hero_a", (200, 80, 50)), ("hero_b", (50, 200, 80))]:
        cv2.imwrite(str(models / f"{hero_id}.png"), make_textured_portrait(color, size=(200, 350)))
    return str(models)


def test_database_loads_portraits(portrait_db, model_db):
    from hero_detector import HeroDatabase
    db = HeroDatabase(portrait_db, model_db)
    db.load()
    assert len(db.portraits) == 3
    assert "hero_a" in db.portraits
    assert "phash" in db.portraits["hero_a"]
    assert "img_gray" in db.portraits["hero_a"]


def test_database_loads_models(portrait_db, model_db):
    from hero_detector import HeroDatabase
    db = HeroDatabase(portrait_db, model_db)
    db.load()
    assert len(db.models) == 2
    assert db.models["hero_a"]["des"] is not None


def test_top_portrait_candidates_returns_closest(portrait_db, model_db):
    from hero_detector import HeroDatabase
    import imagehash
    db = HeroDatabase(portrait_db, model_db)
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


def test_detect_roster_hero_finds_correct_hero(portrait_db, model_db):
    from hero_detector import HeroDatabase, detect_roster_hero
    db = HeroDatabase(portrait_db, model_db)
    db.load()
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    # Place hero_b portrait inside the roster ROI (60–85% width, 10–70% height)
    x1, y1 = int(1920 * 0.60), int(1080 * 0.10)
    frame[y1:y1+182, x1:x1+140] = make_portrait((50, 200, 80))  # hero_b color
    assert detect_roster_hero(frame, db, threshold=0.90) == "hero_b"


def test_detect_roster_hero_returns_none_for_empty_frame(portrait_db, model_db):
    from hero_detector import HeroDatabase, detect_roster_hero
    db = HeroDatabase(portrait_db, model_db)
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
