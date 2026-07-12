# Stone Catalog Scraper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `tools/scrape_stones.py`, a screen-automation script that walks the RSL "Камені" grid in the live PC client, OCRs each stone's name/rarity/group/description, and saves `data/stones/<tab>/<slug>.png` + `.md` per stone.

**Architecture:** Pure logic (slug generation, OCR-text parsing, grid coordinate math, hash-based diffing, dedupe/file-writing, grid-walk control flow) is factored into small, dependency-injected functions/classes that are unit tested without touching the screen. Screen/mouse/OCR I/O (`mss`, `pyautogui`, `pygetwindow`, `pytesseract`) is wired together only in the CLI entrypoint, verified manually against the live game per the design spec's Testing section.

**Tech Stack:** Python 3.11, `opencv-python`, `numpy`, `imagehash`, `Pillow` (already used by `tools/hero_detector.py`); new: `pyautogui`, `pygetwindow`, `pytesseract` + system Tesseract-OCR binary with the `ukr` language pack.

**Spec:** `docs/superpowers/specs/2026-07-12-stone-catalog-scraper-design.md`

---

## Known limitation (read before Task 10)

The grid uses fixed row/column fractions (approach C from the design spec). Shape-group section headers (e.g. "Трикутні") insert extra vertical space between groups that the fixed row spacing doesn't account for — after crossing a group boundary, row math can drift. This is caught, not prevented: `process_cell`'s panel-diff check skips clicks that land on empty space, and `StoneWriter`'s name dedupe prevents corrupt overwrites. Net effect: worst case is a few missed stones near group boundaries, not crashes or bad data. Spec's manual-verification step (comparing saved count to the in-game count) is how you catch that gap.

---

### Task 1: Ukrainian name slugifier

**Files:**
- Create: `tools/scrape_stones.py`
- Test: `tests/test_scrape_stones.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scrape_stones.py
def test_slugify_uk_transliterates_and_snake_cases():
    from scrape_stones import slugify_uk
    assert slugify_uk("Жахіття босів") == "zhakhittia_bosiv"


def test_slugify_uk_strips_punctuation():
    from scrape_stones import slugify_uk
    assert slugify_uk("Наведений приціл!") == "navedenyi_prytsil"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scrape_stones.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scrape_stones'`

- [ ] **Step 3: Write minimal implementation**

```python
# tools/scrape_stones.py
"""RSL Stones catalog scraper — screen automation + OCR.

Usage:
    python tools/scrape_stones.py --calibrate --tab regular
        Saves data/stones/calibration_debug.png with the computed grid/panel
        boxes overlaid. Compare against the real game window before a real run.

    python tools/scrape_stones.py --tab regular
    python tools/scrape_stones.py --tab live_arena
        Click the matching sub-tab ("Звичайні Камені" / "Камені лайв арени")
        in-game first, then run. The script takes over mouse control.

Install: pip install pyautogui pygetwindow pytesseract opencv-python mss Pillow imagehash
Also install the Tesseract-OCR binary system-wide with the `ukr` language pack
(pytesseract only wraps the binary, it does not ship it).
"""
import re

_UK_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e",
    "є": "ie", "ж": "zh", "з": "z", "и": "y", "і": "i", "ї": "i", "й": "i",
    "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "shch", "ь": "", "ю": "iu", "я": "ia", "'": "", "’": "",
}


def slugify_uk(name: str) -> str:
    """Transliterate a Ukrainian stone name into a filesystem-safe ASCII slug."""
    lowered = name.strip().lower()
    transliterated = "".join(_UK_TRANSLIT.get(ch, ch) for ch in lowered)
    ascii_only = re.sub(r"[^a-z0-9]+", "_", transliterated)
    return ascii_only.strip("_")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scrape_stones.py -v`
Expected: PASS (3 passed) — a 3rd test (curly-apostrophe regression) was added during a
spec-compliance fix round; see git history (`bcf7fc0`) for why.

- [ ] **Step 5: Commit**

```bash
git add tools/scrape_stones.py tests/test_scrape_stones.py
git commit -m "feat: add uk slugifier for stone catalog scraper"
```

---

### Task 2: OCR panel text parser

**Files:**
- Modify: `tools/scrape_stones.py`
- Modify: `tests/test_scrape_stones.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scrape_stones.py (append)
def test_parse_panel_text_extracts_fields():
    from scrape_stones import parse_panel_text
    raw = "Жахіття босів\nМіфічний\nКруглі\nВласник завдає на 10%\nбільше шкоди босам."
    parsed = parse_panel_text(raw)
    assert parsed["name"] == "Жахіття босів"
    assert parsed["rarity"] == "Міфічний"
    assert parsed["group"] == "Круглі"
    assert parsed["description"] == "Власник завдає на 10% більше шкоди босам."


def test_parse_panel_text_handles_empty_ocr():
    from scrape_stones import parse_panel_text
    parsed = parse_panel_text("")
    assert parsed == {"name": "", "rarity": "", "group": "", "description": ""}


def test_parse_panel_text_ignores_blank_lines():
    from scrape_stones import parse_panel_text
    raw = "Жахіття босів\n\nМіфічний\n\nКруглі\nОпис."
    parsed = parse_panel_text(raw)
    assert parsed["name"] == "Жахіття босів"
    assert parsed["description"] == "Опис."
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scrape_stones.py -v`
Expected: FAIL with `ImportError: cannot import name 'parse_panel_text'`

- [ ] **Step 3: Write minimal implementation**

```python
# tools/scrape_stones.py (append)
def parse_panel_text(raw_text: str) -> dict:
    """Parse OCR output of the left detail panel into structured fields.

    Expected line order (blank OCR lines are dropped first): name, rarity
    badge, shape-group label, then the description paragraph (one or more
    lines, joined with spaces). Missing lines default to "".
    """
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    return {
        "name": lines[0] if len(lines) > 0 else "",
        "rarity": lines[1] if len(lines) > 1 else "",
        "group": lines[2] if len(lines) > 2 else "",
        "description": " ".join(lines[3:]) if len(lines) > 3 else "",
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scrape_stones.py -v`
Expected: PASS (6 passed) — 3 from Task 1 (see note above) + 3 new.

- [ ] **Step 5: Commit**

```bash
git add tools/scrape_stones.py tests/test_scrape_stones.py
git commit -m "feat: add OCR panel text parser for stone scraper"
```

---

### Task 3: Grid and panel coordinate math

**Files:**
- Modify: `tools/scrape_stones.py`
- Modify: `tests/test_scrape_stones.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scrape_stones.py (append)
def test_grid_cell_center_first_cell():
    from scrape_stones import grid_cell_center
    x, y = grid_cell_center(0, 0, (0, 0, 1906, 1077))
    assert 690 <= x <= 705
    assert 365 <= y <= 380


def test_grid_cell_center_offsets_by_window_position():
    from scrape_stones import grid_cell_center
    x0, y0 = grid_cell_center(0, 0, (0, 0, 1906, 1077))
    x1, y1 = grid_cell_center(0, 0, (100, 50, 1906, 1077))
    assert x1 == x0 + 100
    assert y1 == y0 + 50


def test_grid_cell_center_columns_step_right():
    from scrape_stones import grid_cell_center
    x0, _ = grid_cell_center(0, 0, (0, 0, 1906, 1077))
    x1, _ = grid_cell_center(0, 1, (0, 0, 1906, 1077))
    assert x1 > x0


def test_grid_cell_center_rows_step_down():
    from scrape_stones import grid_cell_center
    _, y0 = grid_cell_center(0, 0, (0, 0, 1906, 1077))
    _, y1 = grid_cell_center(1, 0, (0, 0, 1906, 1077))
    assert y1 > y0


def test_panel_rect_is_left_side_of_window():
    from scrape_stones import panel_rect
    left, top, width, height = panel_rect((0, 0, 1906, 1077))
    assert left < 1906 * 0.3
    assert width > 0 and height > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scrape_stones.py -v`
Expected: FAIL with `ImportError: cannot import name 'grid_cell_center'`

- [ ] **Step 3: Write minimal implementation**

```python
# tools/scrape_stones.py (append)
# Calibrated from the reference game-window screenshot (1906x1077 client area).
# Re-verify with `--calibrate` if your window size/scaling differs.
GRID_COLS = 6
GRID_ROWS_PER_PAGE = 3
GRID_START_X_FRAC = 0.365
GRID_COL_STEP_FRAC = 0.106
GRID_START_Y_FRAC = 0.345
GRID_ROW_STEP_FRAC = 0.198
PANEL_RECT_FRAC = (0.01, 0.23, 0.26, 0.98)  # x0, y0, x1, y1 (fractions of window rect)
GRID_AREA_FRAC = (0.32, 0.20, 0.95, 0.99)   # x0, y0, x1, y1 — used only for scroll-end detection


def grid_cell_center(row: int, col: int, rect: tuple) -> tuple:
    """rect = (left, top, width, height) of the game window's client area, in screen pixels."""
    left, top, width, height = rect
    x = left + int((GRID_START_X_FRAC + col * GRID_COL_STEP_FRAC) * width)
    y = top + int((GRID_START_Y_FRAC + row * GRID_ROW_STEP_FRAC) * height)
    return x, y


def panel_rect(rect: tuple) -> tuple:
    """Returns (left, top, width, height) of the left detail panel, in screen pixels."""
    left, top, width, height = rect
    x0f, y0f, x1f, y1f = PANEL_RECT_FRAC
    px0 = left + int(x0f * width)
    py0 = top + int(y0f * height)
    px1 = left + int(x1f * width)
    py1 = top + int(y1f * height)
    return px0, py0, px1 - px0, py1 - py0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scrape_stones.py -v`
Expected: PASS (11 passed) — 6 existing + 5 new.

- [ ] **Step 5: Commit**

```bash
git add tools/scrape_stones.py tests/test_scrape_stones.py
git commit -m "feat: add grid/panel coordinate math for stone scraper"
```

---

### Task 4: Perceptual hash diff helpers

**Files:**
- Modify: `tools/scrape_stones.py`
- Modify: `tests/test_scrape_stones.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scrape_stones.py (append)
import numpy as np


def make_pattern_frame(square_origin: tuple, size=(64, 64)) -> "np.ndarray":
    """A frame with a white square at square_origin — phash is a structural/DCT
    hash, so two SOLID-color frames (no internal structure) hash identically
    regardless of color. Use a positioned square, not a flat color, whenever a
    test needs two frames that actually differ perceptually."""
    frame = np.zeros((*size, 3), dtype=np.uint8)
    ox, oy = square_origin
    frame[oy:oy + 16, ox:ox + 16] = (255, 255, 255)
    return frame


def test_panel_changed_true_when_prev_hash_is_none():
    from scrape_stones import panel_changed
    assert panel_changed(None, 123) is True


def test_panel_changed_false_for_identical_hash():
    from scrape_stones import panel_changed
    assert panel_changed(100, 100) is False


def test_panel_changed_true_for_far_apart_hashes():
    from scrape_stones import panel_changed
    assert panel_changed(100, 300) is True


def test_is_scroll_end_true_for_identical_hash():
    from scrape_stones import is_scroll_end
    assert is_scroll_end(100, 100) is True


def test_is_scroll_end_false_for_far_apart_hashes():
    from scrape_stones import is_scroll_end
    assert is_scroll_end(100, 300) is False


def test_frame_hash_identical_frames_match():
    from scrape_stones import frame_hash, is_scroll_end
    frame_a = make_pattern_frame((4, 4))
    frame_b = make_pattern_frame((4, 4))
    assert is_scroll_end(frame_hash(frame_a), frame_hash(frame_b))


def test_frame_hash_different_frames_differ():
    from scrape_stones import frame_hash, is_scroll_end
    frame_a = make_pattern_frame((4, 4))
    frame_b = make_pattern_frame((40, 40))
    assert not is_scroll_end(frame_hash(frame_a), frame_hash(frame_b))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scrape_stones.py -v`
Expected: FAIL with `ImportError: cannot import name 'panel_changed'`

- [ ] **Step 3: Write minimal implementation**

```python
# tools/scrape_stones.py (append, near the top with the other imports)
import cv2
import imagehash
import numpy as np
from PIL import Image


def frame_hash(frame_bgr: "np.ndarray"):
    """Perceptual hash of a BGR frame — supports subtraction for distance comparisons."""
    return imagehash.phash(Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)))


def panel_changed(prev_hash, curr_hash, threshold: int = 6) -> bool:
    """True if curr_hash differs enough from prev_hash to be a different stone's panel."""
    if prev_hash is None:
        return True
    return abs(curr_hash - prev_hash) > threshold


def is_scroll_end(hash_before, hash_after, threshold: int = 3) -> bool:
    """True if a scroll produced no meaningful change — the list has reached its end."""
    return abs(hash_after - hash_before) <= threshold
```

Note: move the `import re` from Task 1 and this task's imports to a single import block at the top of the file when applying this step — don't duplicate imports.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scrape_stones.py -v`
Expected: PASS (18 passed) — 11 existing + 7 new.

- [ ] **Step 5: Commit**

```bash
git add tools/scrape_stones.py tests/test_scrape_stones.py
git commit -m "feat: add perceptual-hash diffing for stone scraper"
```

---

### Task 5: StoneWriter (dedupe + file output)

**Files:**
- Modify: `tools/scrape_stones.py`
- Modify: `tests/test_scrape_stones.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scrape_stones.py (append)
def test_stone_writer_writes_png_and_md(tmp_path):
    from scrape_stones import StoneWriter
    writer = StoneWriter(tmp_path)
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    saved = writer.write("regular", "Жахіття босів", "Міфічний", "Круглі",
                          "Власник завдає на 10% більше шкоди босам.", image)
    assert saved is True
    slug = writer.slug_for("Жахіття босів")
    png_path = tmp_path / "regular" / f"{slug}.png"
    md_path = tmp_path / "regular" / f"{slug}.md"
    assert png_path.exists()
    assert md_path.exists()
    text = md_path.read_text(encoding="utf-8")
    assert 'name: "Жахіття босів"' in text
    assert 'rarity: "Міфічний"' in text
    assert 'group: "Круглі"' in text
    assert 'tab: "regular"' in text
    assert "Власник завдає на 10% більше шкоди босам." in text


def test_stone_writer_dedupes_by_name(tmp_path):
    from scrape_stones import StoneWriter
    writer = StoneWriter(tmp_path)
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    first = writer.write("regular", "Жахіття босів", "Міфічний", "Круглі", "опис", image)
    second = writer.write("regular", "Жахіття босів", "Міфічний", "Круглі", "опис", image)
    assert first is True
    assert second is False


def test_stone_writer_keeps_tabs_separate(tmp_path):
    from scrape_stones import StoneWriter
    writer = StoneWriter(tmp_path)
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    saved = writer.write("live_arena", "Гнівний протест", "Епічний", "Круглі", "опис", image)
    assert saved is True
    assert (tmp_path / "live_arena" / f"{writer.slug_for('Гнівний протест')}.png").exists()


def test_stone_writer_dedupes_by_slug_not_raw_name(tmp_path):
    # Two raw names that transliterate to the same slug must dedupe on the
    # second write instead of silently overwriting each other's files.
    from scrape_stones import StoneWriter
    writer = StoneWriter(tmp_path)
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    first = writer.write("regular", "Жахіття босів", "Міфічний", "Круглі", "опис", image)
    second = writer.write("regular", "Жахіття босів!", "Міфічний", "Круглі", "інший опис", image)
    assert first is True
    assert second is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scrape_stones.py -v`
Expected: FAIL with `ImportError: cannot import name 'StoneWriter'`

- [ ] **Step 3: Write minimal implementation**

```python
# tools/scrape_stones.py (append)
from pathlib import Path


def _yaml_quote(value: str) -> str:
    """Wraps value as a double-quoted YAML scalar — safe regardless of colons,
    leading '#'/'-', etc. inside it, as long as backslashes/quotes are escaped."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


class StoneWriter:
    """Writes one PNG + one Markdown file per unique (tab, stone) pair, deduping repeats."""

    def __init__(self, out_dir):
        self.out_dir = Path(out_dir)
        self._seen = set()

    def slug_for(self, name: str) -> str:
        return slugify_uk(name)

    def write(self, tab: str, name: str, rarity: str, group: str, description: str, image) -> bool:
        slug = self.slug_for(name)
        key = (tab, slug)
        if key in self._seen:
            return False
        self._seen.add(key)
        tab_dir = self.out_dir / tab
        tab_dir.mkdir(parents=True, exist_ok=True)
        if not cv2.imwrite(str(tab_dir / f"{slug}.png"), image):
            raise IOError(f"Failed to write stone image: {tab_dir / f'{slug}.png'}")
        md = (
            "---\n"
            f"name: {_yaml_quote(name)}\n"
            f"rarity: {_yaml_quote(rarity)}\n"
            f"group: {_yaml_quote(group)}\n"
            f"tab: {_yaml_quote(tab)}\n"
            "---\n\n"
            f"{description}\n"
        )
        (tab_dir / f"{slug}.md").write_text(md, encoding="utf-8")
        return True
```

Note: dedup keys on `(tab, slug)` rather than the raw name — this both scopes dedup per
tab and prevents two differently-punctuated raw names that transliterate to the same
slug from silently overwriting each other's files. `cv2.imwrite`'s return value is
checked and raises `IOError` on failure instead of silently reporting success. Frontmatter
values are wrapped in `_yaml_quote` so a field containing a colon or other YAML-special
character doesn't produce broken frontmatter — update the `test_stone_writer_writes_png_and_md`
assertions accordingly (values are now quoted, e.g. `'name: "Жахіття босів"' in text`).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scrape_stones.py -v`
Expected: PASS (22 passed) — 18 existing tests from Tasks 1-4 plus 4 new ones (3 original
StoneWriter tests + the slug-collision regression test) = 22.

- [ ] **Step 5: Commit**

```bash
git add tools/scrape_stones.py tests/test_scrape_stones.py
git commit -m "feat: add StoneWriter for deduped png+md output"
```

---

### Task 6: Grid-walk control flow

**Files:**
- Modify: `tools/scrape_stones.py`
- Modify: `tests/test_scrape_stones.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scrape_stones.py (append)
def test_walk_grid_visits_every_cell_in_row_major_order():
    from scrape_stones import walk_grid
    visited = []
    walk_grid(
        rows_per_page=2, cols=3,
        click_cell=lambda row, col: visited.append((row, col)),
        capture_grid=lambda: 0,
        scroll_page=lambda: None,
    )
    assert visited == [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]


def test_walk_grid_stops_when_scroll_has_no_effect():
    from scrape_stones import walk_grid
    grid_states = iter([1, 1, 2, 2, 2, 2])
    pages = walk_grid(
        rows_per_page=1, cols=1,
        click_cell=lambda row, col: None,
        capture_grid=lambda: next(grid_states),
        scroll_page=lambda: None,
    )
    assert pages == 1


def test_walk_grid_continues_while_scroll_changes_view():
    from scrape_stones import walk_grid
    grid_states = iter([1, 50, 50, 50])
    pages = walk_grid(
        rows_per_page=1, cols=1,
        click_cell=lambda row, col: None,
        capture_grid=lambda: next(grid_states),
        scroll_page=lambda: None,
    )
    assert pages == 2


def test_walk_grid_calls_scroll_page_once_per_page():
    from scrape_stones import walk_grid
    scroll_calls = []
    grid_states = iter([1, 50, 50, 50])
    walk_grid(
        rows_per_page=1, cols=1,
        click_cell=lambda row, col: None,
        capture_grid=lambda: next(grid_states),
        scroll_page=lambda: scroll_calls.append(1),
    )
    assert len(scroll_calls) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scrape_stones.py -v`
Expected: FAIL with `ImportError: cannot import name 'walk_grid'`

- [ ] **Step 3: Write minimal implementation**

```python
# tools/scrape_stones.py (append)
def walk_grid(rows_per_page: int, cols: int, click_cell, capture_grid, scroll_page,
               max_pages: int = 50) -> int:
    """Clicks every cell of every page, scrolling between pages until the view stops
    changing (or max_pages is hit as a hard safety cap). Returns pages walked.

    click_cell(row, col) -- called for each grid position on the current page.
    capture_grid() -- returns a hashable snapshot (e.g. frame_hash(...)) of the grid area.
    scroll_page() -- scrolls the grid down by one page.
    """
    pages_walked = 0
    for _ in range(max_pages):
        for row in range(rows_per_page):
            for col in range(cols):
                click_cell(row, col)
        before = capture_grid()
        scroll_page()
        after = capture_grid()
        pages_walked += 1
        if is_scroll_end(before, after):
            break
    return pages_walked
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scrape_stones.py -v`
Expected: PASS (26 passed) — 22 existing + 4 new.

- [ ] **Step 5: Commit**

```bash
git add tools/scrape_stones.py tests/test_scrape_stones.py
git commit -m "feat: add grid-walk control flow for stone scraper"
```

---

### Task 7: process_cell integration glue

**Files:**
- Modify: `tools/scrape_stones.py`
- Modify: `tests/test_scrape_stones.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scrape_stones.py (append)
def test_process_cell_saves_new_stone(tmp_path):
    from scrape_stones import process_cell, StoneWriter
    writer = StoneWriter(tmp_path)
    image = np.zeros((5, 5, 3), dtype=np.uint8)
    curr_hash, saved = process_cell(
        tab="regular",
        capture_panel=lambda: (image, 100),
        run_ocr=lambda img: "Жахіття босів\nМіфічний\nКруглі\nОпис каменя.",
        writer=writer,
        prev_hash=None,
    )
    assert saved is True
    assert curr_hash == 100


def test_process_cell_skips_unchanged_panel(tmp_path):
    from scrape_stones import process_cell, StoneWriter
    writer = StoneWriter(tmp_path)
    image = np.zeros((5, 5, 3), dtype=np.uint8)
    curr_hash, saved = process_cell(
        tab="regular",
        capture_panel=lambda: (image, 50),
        run_ocr=lambda img: "Should not be called for real stones, but harmless here",
        writer=writer,
        prev_hash=50,
    )
    assert saved is False


def test_process_cell_saves_fallback_when_ocr_fails(tmp_path):
    # Per the design spec's error handling: a changed panel (real icon clicked)
    # with unreadable OCR must still be saved with a manual-fill marker, not
    # silently dropped — dropping would be indistinguishable from a genuine
    # empty grid click and could hide real stones.
    from scrape_stones import process_cell, StoneWriter
    writer = StoneWriter(tmp_path)
    image = np.zeros((5, 5, 3), dtype=np.uint8)
    curr_hash, saved = process_cell(
        tab="regular",
        capture_panel=lambda: (image, 200),
        run_ocr=lambda img: "",
        writer=writer,
        prev_hash=50,
    )
    assert saved is True
    assert curr_hash == 200
    md_path = tmp_path / "regular" / f"{writer.slug_for('unknown_200')}.md"
    assert md_path.exists()
    assert "OCR failed" in md_path.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scrape_stones.py -v`
Expected: FAIL with `ImportError: cannot import name 'process_cell'`

- [ ] **Step 3: Write minimal implementation**

```python
# tools/scrape_stones.py (append)
def process_cell(tab: str, capture_panel, run_ocr, writer: "StoneWriter", prev_hash):
    """Captures the panel after a click, and saves the stone if the panel actually
    changed (a real icon was clicked).

    A changed panel with unreadable OCR still gets saved, under a fallback
    "unknown_<hash>" name with a manual-fill marker — an unchanged panel
    (empty grid click) is the only case that's skipped entirely, since that's
    the only case we can tell apart from "OCR just failed on a real stone".

    capture_panel() -> (image, curr_hash) for the current left-panel state.
    run_ocr(image) -> raw OCR text string.
    Returns (curr_hash, saved: bool) — curr_hash feeds the next call's prev_hash.
    """
    image, curr_hash = capture_panel()
    if not panel_changed(prev_hash, curr_hash):
        return curr_hash, False
    parsed = parse_panel_text(run_ocr(image))
    if not parsed["name"]:
        saved = writer.write(tab, f"unknown_{curr_hash}", parsed["rarity"], parsed["group"],
                              "<!-- OCR failed, fill manually -->", image)
        return curr_hash, saved
    saved = writer.write(tab, parsed["name"], parsed["rarity"], parsed["group"],
                          parsed["description"], image)
    return curr_hash, saved
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scrape_stones.py -v`
Expected: PASS (29 passed) — 26 existing + 3 new.

- [ ] **Step 5: Commit**

```bash
git add tools/scrape_stones.py tests/test_scrape_stones.py
git commit -m "feat: add process_cell glue for stone scraper"
```

---

### Task 8: Calibration overlay renderer

**Files:**
- Modify: `tools/scrape_stones.py`
- Modify: `tests/test_scrape_stones.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scrape_stones.py (append)
def test_render_calibration_overlay_marks_panel_and_grid():
    from scrape_stones import render_calibration_overlay
    frame = np.zeros((1077, 1906, 3), dtype=np.uint8)
    annotated = render_calibration_overlay(frame, (0, 0, 1906, 1077))
    assert annotated.shape == frame.shape
    assert not np.array_equal(frame, annotated)
    # green panel box and red grid-cell markers were both drawn somewhere
    assert (annotated[:, :, 1] == 255).any()
    assert (annotated[:, :, 2] == 255).any()


def test_render_calibration_overlay_does_not_mutate_input():
    from scrape_stones import render_calibration_overlay
    frame = np.zeros((1077, 1906, 3), dtype=np.uint8)
    render_calibration_overlay(frame, (0, 0, 1906, 1077))
    assert not frame.any()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scrape_stones.py -v`
Expected: FAIL with `ImportError: cannot import name 'render_calibration_overlay'`

- [ ] **Step 3: Write minimal implementation**

```python
# tools/scrape_stones.py (append)
def render_calibration_overlay(frame, rect: tuple, rows_per_page: int = GRID_ROWS_PER_PAGE,
                                cols: int = GRID_COLS):
    """Draws the computed panel box (green) and grid-cell centers (red) on a copy
    of frame, for visual --calibrate verification. Does not mutate frame."""
    annotated = frame.copy()
    px, py, pw, ph = panel_rect(rect)
    cv2.rectangle(annotated, (px, py), (px + pw, py + ph), (0, 255, 0), 3)
    for row in range(rows_per_page):
        for col in range(cols):
            cx, cy = grid_cell_center(row, col, rect)
            cv2.circle(annotated, (cx, cy), 10, (0, 0, 255), 3)
    return annotated
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scrape_stones.py -v`
Expected: PASS (31 passed) — 29 existing + 2 new.

- [ ] **Step 5: Commit**

```bash
git add tools/scrape_stones.py tests/test_scrape_stones.py
git commit -m "feat: add calibration overlay renderer for stone scraper"
```

---

### Task 9: WindowController (no unit test — thin OS wrapper)

**Files:**
- Modify: `tools/scrape_stones.py`

- [ ] **Step 1: Add the window controller**

```python
# tools/scrape_stones.py (append)
class WindowController:
    """Locates and focuses the RSL client window; exposes its client-area rect.

    Not unit tested — this is a thin wrapper around pygetwindow with no logic
    of its own. Verified manually: run with the game window open and confirm
    focus_and_get_rect() doesn't raise.
    """

    def __init__(self, title_substring: str = "Raid: Shadow Legends"):
        self.title_substring = title_substring

    def find(self):
        import pygetwindow as gw
        matches = [w for w in gw.getAllWindows() if self.title_substring.lower() in w.title.lower()]
        if not matches:
            raise RuntimeError(
                f"RSL window not found (looked for title containing '{self.title_substring}'). "
                "Open the game and make sure it's not minimized."
            )
        return matches[0]

    def focus_and_get_rect(self) -> tuple:
        win = self.find()
        win.activate()
        return win.left, win.top, win.width, win.height
```

- [ ] **Step 2: Sanity-check the import**

Run: `python -c "import sys; sys.path.insert(0, 'tools'); import scrape_stones"`
Expected: no error (pygetwindow is imported lazily inside `find()`, so this succeeds even before installing it — it only needs to be installed to actually run Task 10).

- [ ] **Step 3: Commit**

```bash
git add tools/scrape_stones.py
git commit -m "feat: add WindowController for RSL client window focus"
```

---

### Task 10: CLI wiring + manual verification

**Files:**
- Modify: `tools/scrape_stones.py`

- [ ] **Step 1: Add the CLI**

```python
# tools/scrape_stones.py (append)
import argparse
import time


def capture_region(sct, left, top, width, height):
    shot = sct.grab({"left": left, "top": top, "width": width, "height": height})
    return cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2BGR)


def run(tab_key: str, out_dir: Path, calibrate: bool):
    import mss

    controller = WindowController()
    rect = controller.focus_and_get_rect()

    with mss.mss() as sct:
        if calibrate:
            frame = capture_region(sct, *rect)
            annotated = render_calibration_overlay(frame, (0, 0, rect[2], rect[3]))
            out_dir.mkdir(parents=True, exist_ok=True)
            debug_path = out_dir / "calibration_debug.png"
            cv2.imwrite(str(debug_path), annotated)
            print(f"Calibration overlay saved to {debug_path}. Compare against the real game window.")
            return

        import pyautogui
        import pytesseract

        writer = StoneWriter(out_dir)

        def capture_grid_hash():
            left, top, width, height = rect
            x0f, y0f, x1f, y1f = GRID_AREA_FRAC
            gx0 = left + int(x0f * width)
            gy0 = top + int(y0f * height)
            gx1 = left + int(x1f * width)
            gy1 = top + int(y1f * height)
            return frame_hash(capture_region(sct, gx0, gy0, gx1 - gx0, gy1 - gy0))

        def capture_panel():
            px, py, pw, ph = panel_rect(rect)
            image = capture_region(sct, px, py, pw, ph)
            return image, frame_hash(image)

        def run_ocr(image) -> str:
            return pytesseract.image_to_string(image, lang="ukr")

        def click_cell_raw(row: int, col: int):
            x, y = grid_cell_center(row, col, rect)
            pyautogui.click(x, y)
            time.sleep(0.4)

        def scroll_page():
            cx, cy = grid_cell_center(1, GRID_COLS // 2, rect)
            pyautogui.moveTo(cx, cy)
            pyautogui.scroll(-600)
            time.sleep(0.4)

        state = {"prev_hash": None, "saved_count": 0}

        def click_and_process(row: int, col: int):
            click_cell_raw(row, col)
            state["prev_hash"], saved = process_cell(
                tab_key, capture_panel, run_ocr, writer, state["prev_hash"])
            if saved:
                state["saved_count"] += 1

        pages = walk_grid(
            rows_per_page=GRID_ROWS_PER_PAGE,
            cols=GRID_COLS,
            click_cell=click_and_process,
            capture_grid=capture_grid_hash,
            scroll_page=scroll_page,
        )
        print(f"Done. {pages} page(s) walked, {state['saved_count']} stone(s) "
              f"saved to {out_dir / tab_key}.")


def main():
    parser = argparse.ArgumentParser(description="Scrape RSL Stones catalog from the live client.")
    parser.add_argument("--tab", choices=["regular", "live_arena"], required=True,
                         help="Which Stones sub-tab to scrape (click it in-game before running).")
    parser.add_argument("--out-dir", default="data/stones", help="Output directory (default: data/stones)")
    parser.add_argument("--calibrate", action="store_true",
                         help="Save a debug overlay image instead of clicking anything.")
    args = parser.parse_args()
    run(args.tab, Path(args.out_dir), args.calibrate)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Install runtime dependencies**

Run: `pip install pyautogui pygetwindow pytesseract opencv-python mss Pillow imagehash`
Expected: all install successfully. Separately install the Tesseract-OCR binary for Windows and add the `ukr` language pack (not a pip package — see https://github.com/UB-Mannheim/tesseract/wiki for the Windows installer).

- [ ] **Step 3: Run the full unit test suite**

Run: `pytest tests/test_scrape_stones.py -v`
Expected: PASS (31 passed) — the CLI code added in this task has no new unit tests (it's I/O wiring), but this confirms nothing broke.

- [ ] **Step 4: Manual calibration check**

With RSL open and the "Камені" screen showing "Звичайні Камені" (diamond tab):

Run: `python tools/scrape_stones.py --calibrate --tab regular`
Expected: `data/stones/calibration_debug.png` is created. Open it and confirm the green box covers the left description panel and the red circles land on the visible stone icons. If they're off, adjust `GRID_START_X_FRAC`, `GRID_COL_STEP_FRAC`, `GRID_START_Y_FRAC`, `GRID_ROW_STEP_FRAC`, `PANEL_RECT_FRAC` in `tools/scrape_stones.py` (Task 3) and re-run `--calibrate` until they line up.

- [ ] **Step 5: Manual live run — regular tab**

Run: `python tools/scrape_stones.py --tab regular`
Expected: script takes over the mouse, clicks through the grid, and prints `Done. N page(s) walked, M stone(s) saved to data/stones/regular.` Spot-check 3-4 `data/stones/regular/*.md` files against what the game actually shows for those stones (per the design spec's Testing section — this is where OCR mistakes or grid drift would surface).

- [ ] **Step 6: Manual live run — live arena tab**

In-game, click the sword sub-tab ("Камені лайв арени"), then:

Run: `python tools/scrape_stones.py --tab live_arena`
Expected: same as Step 5, output under `data/stones/live_arena/`.

- [ ] **Step 7: Commit**

```bash
git add tools/scrape_stones.py
git commit -m "feat: wire up stone scraper CLI (calibrate + live run)"
```

If `data/stones/` output should be committed too (raw scraped screenshots/descriptions), add it explicitly in a follow-up commit — don't bundle scrape output with the code commit above.
