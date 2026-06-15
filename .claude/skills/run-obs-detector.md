---
name: run-obs-detector
description: Use when asked to run, launch, start, or test the OBS hero auto-detector for the RSL Hero Guide project. Covers OBS Studio location, loading the Python script, configuring paths, adding the Browser Source, and verifying the overlay works.
---

# Run OBS Hero Detector

## Prerequisites

| Item | Value |
|------|-------|
| OBS Studio | `D:\OBS\obs-studio\bin\64bit\obs64.exe` |
| Python | 3.11 — already configured in OBS |
| Script | `tools/hero_detector.py` (relative to repo root) |
| Portraits | `data/portraits/` |
| Overlay dir | repo root (e.g. `D:\projects\twitch-extension-private`) |

## Launch Steps

### 1. Open OBS Studio

```powershell
Start-Process "D:\OBS\obs-studio\bin\64bit\obs64.exe"
```

Or launch manually from `D:\OBS\obs-studio\bin\64bit\obs64.exe`.

### 2. Load the Python Script

1. **Tools → Scripts** → click **+**
2. Navigate to `tools/hero_detector.py` → **Open**
3. Python 3.11 is already set — no Python Settings change needed

### 3. Configure Script Settings

In the Scripts panel, select `hero_detector.py`:

| Setting | Value |
|---------|-------|
| Overlay directory | path to repo root (e.g. `D:\projects\twitch-extension-private`) |
| HTTP port (Browser Source) | `8765` |
| Portraits DB path | `D:\projects\twitch-extension-private\data\portraits` |
| WebSocket port | `7182` |
| Detection interval (ms) | `1500` |
| Portrait confidence threshold | `0.82` |
| Battle detection threshold | `0.80` |

Defaults auto-populate from `script_defaults()` — check that portrait path resolves correctly.

### 4. Add Browser Source to Scene

1. In OBS scene → **+** → **Browser**
2. URL: `http://localhost:8765/obs/obs.html`
3. Width: `1920`, Height: `1080` (or match stream resolution)
4. Uncheck "Shutdown source when not visible"

For guest overlay: `http://localhost:8765/obs/obs-guest.html`

### 5. Verify Everything Running

Check OBS **Script Log** (Tools → Scripts → Script Log) for:
```
[hero-detector] script file parsed OK v=RING-ONLY-3
[hero-detector] Overlay served at http://localhost:8765/obs/obs.html
[hero-detector] Loaded N portraits
```

Open `http://localhost:8765/obs/obs.html` in a browser to confirm overlay loads.

WS server on port `7182` — browser overlay auto-connects.

## Detection Flow

```
_detect_tick() every 1500ms
  ├── detect_roster_hero()  → portrait match in right panel (60-85% w, 10-70% h)
  └── find_active_circle()  → green/red HSV ring at hero feet
        └── detect_battle_hero() → portrait match above ring (health-bar strip)
              └── BattleCache → confirms after 3 consecutive hits
```

WS push to overlay: `{"type": "hero", "id": "hero_slug"}` or `{"type": "hero", "id": null}` on clear.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| "DB load failed" in log | Check portraits path — must point to `data/portraits/` with .png files |
| Overlay blank | Confirm HTTP port 8765 not blocked; check URL in Browser Source |
| No detection in battle | Circle detector needs green/red HSV ring visible on screen; check `_CIRCLE_Y_MIN_FRAC` zone |
| Screen capture returns None | `mss` should handle fullscreen DX — check `pip install mss` in OBS Python env |
| Port conflict on restart | `reuse_address=True` set; if still conflicting, wait ~10s or restart OBS |
| Hero misidentified | Use "Clear battle cache" button in script settings; lower threshold if needed |

## Data Refresh

```powershell
# Re-download portraits
cd D:\projects\twitch-extension-private
python tools/download_portraits.py

# Capture new 3D model crops (interactive)
python tools/extract_models.py
```

## Notes

- `data/` is gitignored (portraits + models are local assets). Only `data/heroes.json` is tracked.
- MODEL_ROI in `extract_models.py` is hardcoded for 1920×1080 — TODO: make configurable per screen diagonal.
- Debug logging fires every 5th tick to OBS Script Log — normal, not an error.
