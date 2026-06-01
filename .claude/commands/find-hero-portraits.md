# find-hero-portraits

Знайти та додати портрети (140×182px) для героїв RSL у `data/heroes.json`.

Використовуй цей скіл коли:
- Додаються нові герої (новий рідкісний тип, або оновлення ayumilove)
- `portrait` поле відсутнє у деяких героях
- Треба оновити портрети після великого патчу гри

---

## Джерела портретів (пріоритет)

### 1. hellhades.com — WP REST API (основне)
- URL: `https://hellhades.com/wp-json/wp/v2/champions?per_page=100&page=N&_fields=slug,title,yoast_head_json`
- Портрет у: `yoast_head_json.schema['@graph'][0].thumbnailUrl`
- Розмір: 140×182px
- Hotlink: блокує localhost-referer → потрібен `referrerpolicy="no-referrer"` в `<img>`
- Скрипт:

```python
import urllib.request, json, time

ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
base = "https://hellhades.com/wp-json/wp/v2/champions"

portraits = {}
page, total_pages = 1, 999
while page <= total_pages:
    url = f"{base}?per_page=100&page={page}&_fields=slug,title,yoast_head_json"
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=30) as resp:
        if page == 1:
            total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
        data = json.loads(resp.read())
    for item in data:
        name = item["title"]["rendered"]
        try:
            graph = item["yoast_head_json"]["schema"]["@graph"]
            thumb = next((n["thumbnailUrl"] for n in graph
                          if n.get("@type") == "WebPage" and "thumbnailUrl" in n), None)
            if thumb:
                portraits[name] = thumb
        except (KeyError, TypeError):
            pass
    page += 1
    time.sleep(0.2)
```

**Увага:** hellhades зберігає назви з Title Case і HTML entities (`&#8217;` = `'`).
Нормалізуй перед співставленням:
```python
import re, html
def norm(s): return re.sub(r"[^a-z0-9]", "", html.unescape(s).lower())
```

---

### 2. inteleria.com — DataTables API (fallback)
- URL: `POST https://www.inteleria.com/wp-json/in-champions/v1/champions`
- Body: JSON з DataTables параметрами (обов'язково `columns` масив)
- Розмір: 140×182px
- Hotlink: **не блокує** (без `referrerpolicy` потреби)
- Скрипт:

```python
import urllib.request, json, re

COLUMNS = [{"data": d, "name": "", "searchable": True, "orderable": True,
            "search": {"value": "", "regex": False}}
           for d in ["image","name","faction","rarity","type","affinity",
                     "HP","ATK","DEF","SPD","CRATE","CDMG","RES","ACC","champion_tier","rating_avg"]]

img_re = re.compile(r'src=["\']([^"\']+)["\']')
name_re = re.compile(r'>([^<]+)</a>')
portraits = {}
start, total = 0, 9999

while start < total:
    payload = json.dumps({
        "draw": 1, "columns": COLUMNS,
        "order": [{"column": 0, "dir": "asc"}],
        "start": start, "length": 100,
        "search": {"value": "", "regex": False}
    }).encode()
    req = urllib.request.Request(
        "https://www.inteleria.com/wp-json/in-champions/v1/champions",
        data=payload,
        headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json",
                 "Referer": "https://www.inteleria.com/champion-list/"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    total = int(data["recordsTotal"])
    for row in data["data"]:
        img_m = img_re.search(row["image"])
        name_m = name_re.search(row["name"])
        if img_m and name_m:
            portraits[name_m.group(1).strip()] = img_m.group(1)
    start += 100
```

**Увага:** inteleria зберігає спецсимволи як Unicode replacement char (`�`).
Порівнюй через `norm()` або partial word match.

---

### 3. ayumilove.net — CDN (останній fallback)
- URL: `https://ayumilove.net/files/games/raid_shadow_legends/champion/{Name_With_Underscores}.jpg`
- Розмір: **160×90px landscape** (не portrait!)
- Hotlink: блокує localhost → потрібен `referrerpolicy="no-referrer"`
- Трансформація імені:

```javascript
function heroPortraitUrl(hero) {
  if (hero.portrait) return hero.portrait;
  const small = new Set(['the','of','a','an','and','in','at','by','for']);
  const slug = hero.name.replace(/'/g,'').split(/[\s\-,]+/).filter(Boolean)
    .map(w => small.has(w.toLowerCase()) ? w.toLowerCase()
              : w.charAt(0).toUpperCase() + w.slice(1))
    .join('_');
  return `https://ayumilove.net/files/games/raid_shadow_legends/champion/${slug}.jpg`;
}
```

---

## Процедура оновлення heroes.json

```python
import json, re, html

# 1. Завантаж heroes.json
with open("data/heroes.json", encoding="utf-8") as f:
    heroes = json.load(f)

def norm(s):
    return re.sub(r"[^a-z0-9]", "", html.unescape(s).lower())

# 2. Запусти скрипти hellhades + inteleria вище → hh_portraits, it_portraits

# 3. Додай hellhades (основне — нормалізована назва)
hh_norm = {norm(k): v for k, v in hh_portraits.items()}
for hero in heroes:
    if "portrait" not in hero:
        url = hh_norm.get(norm(hero["name"]))
        if url: hero["portrait"] = url

# 4. Додай inteleria (fallback — partial word match для спецсимволів)
for hero in heroes:
    if "portrait" not in hero:
        words = hero["name"].lower().split()
        for key, url in it_portraits.items():
            if all(w in key.lower() for w in words[:2]):
                hero["portrait"] = url; break

# 5. Збережи
with open("data/heroes.json", "w", encoding="utf-8") as f:
    json.dump(heroes, f, ensure_ascii=False, separators=(",",":"))

# 6. Статистика
with_portrait = sum(1 for h in heroes if "portrait" in h)
print(f"{with_portrait}/{len(heroes)} heroes have portraits")
missing = [h["name"] for h in heroes if "portrait" not in h]
print(f"Missing: {missing}")
```

---

## Перевірка якості

- Перевір кілька URL вручну: `curl -I {url}` — має бути `200 image/jpeg` або `image/png`
- Для нових героїв що відсутні скрізь: fallback на ayumilove landscape — прийнятно
- Не додавай героїв з ayumilove які ще не вийшли в грі (анонсовані але не релізовані)

## Де зберігаються дані

- `tools/hellhades-portraits.json` — кеш hellhades (name → url)
- `tools/inteleria-portraits.json` — кеш inteleria (name → url)
- `data/heroes.json` — фінальний результат (поле `portrait` у кожному герої)
