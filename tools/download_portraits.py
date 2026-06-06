"""Download hero portrait images from heroes.json URLs into data/portraits/."""
import json
import time
import urllib.request
from pathlib import Path

HEROES_JSON = Path(__file__).parent.parent / "data" / "heroes.json"
PORTRAITS_DIR = Path(__file__).parent.parent / "data" / "portraits"


def portrait_url(hero: dict) -> str:
    if hero.get("portrait"):
        return hero["portrait"]
    slug = hero["name"].lower().replace(" ", "-").replace("'", "")
    return f"https://ayumilove.net/files/games/raid-shadow-legends/hero/{slug}.jpg"


def download_portraits():
    PORTRAITS_DIR.mkdir(parents=True, exist_ok=True)
    heroes = json.loads(HEROES_JSON.read_text(encoding="utf-8"))
    total = len(heroes)
    for i, hero in enumerate(heroes, 1):
        dest = PORTRAITS_DIR / (Path(hero["id"]).name + ".png")
        if dest.exists():
            print(f"[{i}/{total}] skip  {hero['id']}")
            continue
        url = portrait_url(hero)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                dest.write_bytes(resp.read())
            print(f"[{i}/{total}] ok    {hero['id']}")
        except Exception as e:
            print(f"[{i}/{total}] FAIL  {hero['id']}: {e}")
        time.sleep(0.3)


if __name__ == "__main__":
    download_portraits()
