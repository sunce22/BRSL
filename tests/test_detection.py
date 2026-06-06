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
