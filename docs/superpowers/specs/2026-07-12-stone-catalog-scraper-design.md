# Stone Catalog Scraper — Design Spec

**Date:** 2026-07-12
**Status:** Approved

---

## Goal

Automate collecting the RSL "Камені" (Stones) section from the live PC game client: for every stone, save a screenshot of its detail card (icon + name + rarity + description) plus its Ukrainian description text, into a per-stone file pair. Covers two tabs: "Звичайні Камені" (regular, diamond icon) and "Камені лайв арени" (Live Arena, sword icon). Out of scope: the "?" (locked) tab and the "Реліквії" (Relics) section.

## Why this exists

`tools/l10n-from-memory.json` only has placeholder item names for stones (e.g. "Stone Skill Rare 4000004"), not real Ukrainian descriptions — insufficient as a data source. The only reliable source is the live client UI, which requires OCR + screen automation.

## Screen layout (reference)

- Top-right: category tabs (Реліквії / Камені) — Камені already selected, out of scope to touch Реліквії.
- Top-left: 3 sub-tab buttons (diamond = regular, sword = live arena, "?" = locked) — only diamond and sword are in scope.
- Left panel: name, rarity badge, shape-group label (e.g. "Круглі"), large icon, description paragraph. Updates on icon click.
- Center/right: scrollable grid of stone icons, 6 per row, grouped into labeled sections by shape (Круглі, Трикутні, ...).

## Architecture

Single script `tools/scrape_stones.py`, following the existing `hero_detector.py` pattern (fraction-based ROIs, `mss` for capture). New dependency: GUI automation + OCR (not needed by `hero_detector.py`, which is passive).

Components:

1. **`WindowController`** — locates and focuses the RSL client window (by title), returns client-area rect in screen coordinates. All click/capture math is expressed as fractions of this rect, not hardcoded pixels, so it tolerates window resizing.
2. **`GridWalker`** — iterates the icon grid: fixed column x-fractions (6 columns), fixed row-height fraction. Clicks each cell top-to-bottom/left-to-right. After finishing a visible page, scrolls the grid by one page height and re-scans. Detects end-of-list by comparing a grid-area screenshot hash before and after a scroll — unchanged means nothing more to scroll, so stop.
3. **`PanelCapture`** — after each click, waits a short fixed delay for the UI to update, then screenshots the left panel region. Diffs this screenshot against the previous panel state (perceptual hash); if unchanged, the click hit empty grid space (short last row) — skip, no save.
4. **`OcrExtractor`** — runs `pytesseract` (lang=`ukr`) over the panel crop. Parses line-by-line: first line = name, second = rarity badge text, third = shape-group label, remaining paragraph = description. Best-effort — OCR noise is expected and handled (see Error handling).
5. **`StoneWriter`** — slugifies the stone name (transliteration uk→lat, e.g. "Жахіття босів" → `zhahittya_bosiv`) for the filename. Dedupes by name: if a name was already written this run (grid overlap from imprecise scroll), skip the repeat. Writes:
   - `data/stones/<tab>/<slug>.png` — the raw panel crop (name+rarity+icon+description as one image, for visual/manual verification)
   - `data/stones/<tab>/<slug>.md` — frontmatter (`name`, `rarity`, `group`, `tab`) + description body

Where `<tab>` is `regular` or `live_arena`.

## Calibration

Grid/panel coordinates are NOT hardcoded from the screenshot shared in chat — the user's actual window size/scaling may differ. The script ships with a `--calibrate` mode: takes one screenshot, overlays the computed grid-cell boxes and panel box as a debug PNG saved to disk, and exits without clicking anything. The user compares this against the real game window and adjusts the fraction constants at the top of the script if they're off. Normal runs skip this step.

## Error handling

- RSL window not found → clear error, abort (don't guess).
- OCR output empty or unparseable → still save the `.png`, write the `.md` with a `<!-- OCR failed, fill manually -->` marker instead of crashing.
- Duplicate stone name in the same run → skip silently (logged), don't overwrite.
- Empty click (no icon under cursor) → detected via panel-diff, skipped, not treated as an error.

## Testing

No automated tests for GUI automation against a live external game client. Verification is manual:
1. Run `--calibrate`, confirm grid/panel boxes visually match the real screen.
2. Run one tab end-to-end, spot-check a handful of `.md` files against what the game actually shows for those stones.
3. Confirm no duplicate/missing stones by comparing saved count against the visible count in-game.

## Dependencies to add

`pyautogui`, `pygetwindow`, `pytesseract` (+ system Tesseract-OCR binary with the `ukr` traineddata installed separately — not pip-installable). `opencv-python`, `mss`, `Pillow` already used by `hero_detector.py`.
