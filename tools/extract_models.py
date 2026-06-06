"""Semi-automated 3D model screenshot capture.

Usage:
  python tools/extract_models.py

For each hero without a model PNG, prints the hero name and waits for
ENTER (while you navigate to that hero in-game). Then captures a
screenshot, crops the model region, and saves data/models/{hero_id}.png.
Press 's'+ENTER to skip; 'q'+ENTER to quit.
"""
import json
import cv2
import numpy as np
from pathlib import Path
from PIL import ImageGrab

HEROES_JSON = Path(__file__).parent.parent / "data" / "heroes.json"
MODELS_DIR  = Path(__file__).parent.parent / "data" / "models"

# Fraction of screen to crop for the hero model (left, top, right, bottom).
# Calibrate once for your resolution by examining a full-screen screenshot.
MODEL_ROI = (0.30, 0.05, 0.70, 0.90)


def crop_model(bgr: np.ndarray) -> np.ndarray:
    h, w = bgr.shape[:2]
    x1, y1 = int(w * MODEL_ROI[0]), int(h * MODEL_ROI[1])
    x2, y2 = int(w * MODEL_ROI[2]), int(h * MODEL_ROI[3])
    crop = bgr[y1:y2, x1:x2]
    if crop.size == 0:
        raise ValueError(f"MODEL_ROI {MODEL_ROI} produced empty crop for frame {w}x{h}")
    return crop


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    heroes = json.loads(HEROES_JSON.read_text(encoding="utf-8"))
    todo = [h for h in heroes if not (MODELS_DIR / (Path(h["id"]).name + ".png")).exists()]
    print(f"{len(todo)} heroes need model screenshots ({len(heroes)} total)\n")

    for i, hero in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] Navigate to '{hero['name']}' in the game roster.")
        cmd = input("  ENTER=capture  s=skip  q=quit: ").strip().lower()
        if cmd == "q":
            print("Stopped.")
            break
        if cmd == "s":
            print("  Skipped.")
            continue
        try:
            frame = cv2.cvtColor(np.array(ImageGrab.grab()), cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"  Capture failed: {e}. Try again.")
            continue
        dest = MODELS_DIR / (Path(hero["id"]).name + ".png")
        if not cv2.imwrite(str(dest), crop_model(frame)):
            print(f"  Write failed: {dest}")
        else:
            print(f"  Saved {dest}")


if __name__ == "__main__":
    main()
