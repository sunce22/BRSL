"""
Build i18n/heroes-uk.json from D:/RSL_Helper_V6/rslSim.dat.

Primary source: rslSim.dat (RSLHelper, cp1251 JSON, 37MB)
Contains: StaticDataLocalization + HeroData.HeroTypes

Run: python tools/build-heroes-uk.py
Requires: RSLHelper installed at D:/RSL_Helper_V6/
"""
import json, sys, re
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT       = Path(__file__).parent.parent
SIM_PATH   = Path("D:/RSL_Helper_V6/rslSim.dat")
HEROES_PATH = ROOT / "data" / "heroes.json"
OUTPUT_PATH = ROOT / "i18n" / "heroes-uk.json"

MEMORY_L10N = Path(__file__).parent / "l10n-from-memory.json"

with open(HEROES_PATH, encoding="utf-8") as f:
    heroes = json.load(f)

# Prefer live memory dump; fall back to rslSim.dat
if MEMORY_L10N.exists():
    with open(MEMORY_L10N, encoding="utf-8") as f:
        l10n = json.load(f)
    print(f"Using live memory l10n: {len(l10n)} entries")
elif SIM_PATH.exists():
    with open(SIM_PATH, encoding="cp1251", errors="replace") as f:
        sim = json.load(f)
    l10n = sim["StaticDataLocalization"]
    print(f"Using rslSim.dat l10n: {len(l10n)} entries")
else:
    sys.exit("ERROR: No l10n source found. Run read-static-data.py or install RSLHelper.")

if not SIM_PATH.exists():
    sys.exit("ERROR: D:/RSL_Helper_V6/rslSim.dat not found for HeroTypes. Install RSLHelper.")

with open(SIM_PATH, encoding="cp1251", errors="replace") as f:
    sim = json.load(f)
hero_types = sim["HeroData"]["HeroTypes"]

def get_l10n(key: str) -> str:
    v = l10n.get(key, "")
    v = re.sub(r"<color=[^>]+>", "", v)
    v = re.sub(r"</color>", "", v)
    return v.strip()

def sanitize(s: str) -> str:
    # Store raw text in JSON — JS escapeHtml() handles HTML encoding at render time.
    # Only strip null bytes and control chars that could break JSON parsing.
    return s.replace("\x00", "").replace("\r", "").strip()

def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())

def extract_base_id(key: str):
    m = re.search(r"\?id=(\d+)#", key)
    return int(m.group(1)) if m else None

# Build EN name -> {name_key, base_typeid}
# Prefer entries where Id == base_typeid (base form, not awakened variant)
en_to_info: dict[str, dict] = {}
for h in hero_types:
    en = h["Name"]["DefaultValue"].lower()
    base_id = extract_base_id(h["Name"]["Key"])
    if base_id is None:
        continue
    if en not in en_to_info or h["Id"] == base_id:
        en_to_info[en] = {"name_key": h["Name"]["Key"], "base_typeid": base_id}

def fuzzy_match(name: str, threshold: float = 0.78):
    n = norm(name)
    best, best_s = None, 0
    for en_low, info in en_to_info.items():
        m = norm(en_low)
        common = sum(1 for a, b in zip(n, m) if a == b)
        score = common / max(len(n), len(m), 1)
        if score > best_s and score >= threshold:
            best_s, best = score, info
    return best

result   = {}
stats    = {"direct": 0, "fuzzy": 0, "missing": 0}

for hero in heroes:
    hid  = hero["id"]
    info = en_to_info.get(hero["name"].lower())
    if not info:
        info = fuzzy_match(hero["name"])
        if info:
            stats["fuzzy"] += 1
        else:
            stats["missing"] += 1
            continue
    else:
        stats["direct"] += 1

    ua_name = get_l10n(info["name_key"])
    if not ua_name:
        stats["missing"] += 1
        continue

    hero_num  = info["base_typeid"] // 10
    skills_uk = []
    for idx, skill in enumerate(hero["skills"], 1):
        skill_id = hero_num * 100 + idx
        uk_name = get_l10n(f"l10n:skill/name?id={skill_id}#static") or skill["name"]
        uk_desc = get_l10n(f"l10n:skill/description?id={skill_id}#static") or skill["description"]
        skills_uk.append({
            "name":        sanitize(uk_name),
            "description": sanitize(uk_desc),
        })

    result[hid] = {"name": sanitize(ua_name), "skills": skills_uk}

OUTPUT_PATH.write_text(
    json.dumps(result, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

total = len(heroes)
print(f"heroes-uk.json: {len(result)}/{total} heroes translated")
print(f"  Direct:  {stats['direct']}")
print(f"  Fuzzy:   {stats['fuzzy']}")
print(f"  Missing: {stats['missing']}")
print(f"\nSource: {SIM_PATH} ({SIM_PATH.stat().st_mtime:.0f})")
print(f"Output: {OUTPUT_PATH}")
