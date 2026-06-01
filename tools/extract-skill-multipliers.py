"""
Extract skill formulas (multipliers) from RSL game static-data file.
Outputs: data/skill-multipliers.json
On re-run: prints changed/added rows as a diff.

Usage:
  python tools/extract-skill-multipliers.py [--path PATH]

Optional:
  --path PATH   Override default static-data search path
"""
import argparse
import io
import json
import re
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    import msgpack
except ImportError:
    sys.exit("ERROR: msgpack not installed. Run: pip install msgpack")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_STATIC_DATA_ROOT = Path(
    r"C:\Users\Roman\AppData\LocalLow\Plarium\Raid_ Shadow Legends\static-data"
)
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "skill-multipliers.json"
MARKDOWN_PATH = Path(__file__).parent.parent / "data" / "skill-multipliers.md"

HEROES_JSON_PATH = Path(__file__).parent.parent / "data" / "heroes.json"

_STAT = rb"(?:ATK|DEF|HP|SPD|TRG_HP|TRG_DEF|TRG_ATK)"
FORMULA_PAT_BYTES = re.compile(rb"[\d.]+\*" + _STAT + rb"(?:\+[\d.]+\*" + _STAT + rb")*")
# Strict: a clean formula component must match the full fixstr (no trailing garbage)
FORMULA_STRICT_PAT = re.compile(
    r"^[\d.]+\*(?:ATK|DEF|HP|SPD|TRG_HP|TRG_DEF|TRG_ATK)"
    r"(?:(?:[+\-][\d.]+(?:\*(?:ATK|DEF|HP|SPD|TRG_HP|TRG_DEF|TRG_ATK))?)|(?:\s*\+\s*\d+))*$"
)
# Detect buff-count / conditional formulas in raw blob bytes
BUFF_PAT_BYTES = re.compile(rb"BUFF_COUNT|CHANGED_STAMINA|alliesWithout|TRG_HP_PERC")
SKILL_L10N_PAT = re.compile(rb"l10n:skill/name\?id=(\d+)#static")
HERO_TYPE_L10N_PAT = re.compile(rb"l10n:hero-type/name\?id=(\d+)#static")
LANG_CODES = {"d", "e", "r", "b", "en", "uk", "de", "fr"}

# Human-readable notes for formula notation used in data/skill-multipliers.json
FORMULA_NOTATION_NOTES = {
    "ATK": "caster's Attack stat",
    "DEF": "caster's Defence stat",
    "HP": "caster's max HP stat",
    "SPD": "caster's Speed stat",
    "TRG_HP": "target's current HP (damage scales with target HP)",
    "TRG_DEF": "target's Defence stat",
    "TRG_ATK": "target's Attack stat",
    "BUFF_COUNT": (
        "number of active buffs on caster or target (damage increases per buff — "
        "these heroes become significantly stronger with buff stacking)"
    ),
    "TRG_HP_PERC": "conditional: applies only when target HP is below a threshold",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_static_data_file(root: Path) -> Path:
    candidates = [
        f for f in root.rglob("*")
        if f.is_file() and not f.suffix and f.stat().st_size > 500_000
    ]
    if not candidates:
        sys.exit(f"ERROR: No static-data file found under {root}")
    return max(candidates, key=lambda f: f.stat().st_mtime)


def decode_stream(blob: bytes) -> list:
    """Decode msgpack stream from blob bytes, stopping at first error."""
    upk = msgpack.Unpacker(raw=True, strict_map_key=False)
    upk.feed(blob)
    objs = []
    try:
        for obj in upk:
            objs.append(obj)
    except Exception:
        pass
    return objs


def to_str(x) -> str:
    if isinstance(x, bytes):
        try:
            return x.decode("utf-8")
        except UnicodeDecodeError:
            return x.decode("latin-1", errors="replace")
    return str(x) if x is not None else ""


def scan_skill_lists(blob: bytes) -> list:
    """
    Scan raw bytes for fixarray patterns containing uint16 skill IDs.
    Returns list of (offset, skill_ids, hero_numeric_id).
    Only accepts arrays where all IDs share the same hero prefix (id // 100).
    """
    results = []
    i = 0
    while i < len(blob):
        b = blob[i]
        if 0x91 <= b <= 0x9F:  # fixarray, 1-15 elements
            arr_len = b & 0x0F
            pos = i + 1
            ids = []
            ok = True
            for _ in range(arr_len):
                if pos >= len(blob):
                    ok = False
                    break
                cb = blob[pos]
                if cb == 0xCD:  # uint16
                    if pos + 2 >= len(blob):
                        ok = False
                        break
                    val = struct.unpack(">H", blob[pos + 1 : pos + 3])[0]
                    ids.append(val)
                    pos += 3
                elif cb == 0xCE:  # uint32
                    if pos + 4 >= len(blob):
                        ok = False
                        break
                    val = struct.unpack(">I", blob[pos + 1 : pos + 5])[0]
                    ids.append(val)
                    pos += 5
                else:
                    ok = False
                    break
            if ok and arr_len >= 2 and all(1000 <= v <= 9_999_999 for v in ids):
                hero_num = ids[0] // 100
                if all(v // 100 == hero_num for v in ids):
                    results.append((i, ids, hero_num))
        i += 1
    return results


# ---------------------------------------------------------------------------
# Phase 1: build hero_numeric_id -> hero_name map
# ---------------------------------------------------------------------------

def build_hero_name_map(outer: list, heroes_json: list) -> dict:
    """
    Returns dict: str(hero_numeric_id) -> hero_name.

    Two strategies:
    A) l10n:hero-type/name?id=N#static  →  hero_name, hero_numeric_id = N // 10
    B) Blob raw search: find hero name bytes, take first skill-list AFTER the name
    """
    mapping = {}

    # Strategy A: l10n entries
    for item in outer:
        if not isinstance(item, bytes):
            continue
        if not HERO_TYPE_L10N_PAT.search(item):
            continue
        objs = decode_stream(item)
        for j, obj in enumerate(objs):
            if not isinstance(obj, bytes):
                continue
            m = HERO_TYPE_L10N_PAT.match(obj)
            if not m:
                continue
            hero_type_id = int(m.group(1))
            hero_num = hero_type_id // 10
            if j + 1 >= len(objs):
                continue
            v1 = objs[j + 1]
            if not isinstance(v1, bytes):
                continue
            s = to_str(v1)
            if s in LANG_CODES:
                if j + 2 < len(objs):
                    v2 = objs[j + 2]
                    if isinstance(v2, bytes) and len(to_str(v2)) >= 2:
                        mapping[str(hero_num)] = to_str(v2)
            elif len(s) >= 2:
                mapping[str(hero_num)] = s

    # Strategy B: name bytes in blob + first skill list after it
    for item in outer:
        if not isinstance(item, bytes) or len(item) < 200:
            continue
        skill_lists = scan_skill_lists(item)
        if not skill_lists:
            continue

        for hero in heroes_json:
            nb = hero["name"].encode("ascii", errors="ignore")
            if len(nb) < 5 or nb not in item:
                continue

            search_from = 0
            while True:
                pos = item.find(nb, search_from)
                if pos == -1:
                    break
                # First skill list AFTER this position
                after = [sl for sl in skill_lists if sl[0] > pos]
                if after:
                    hero_num = after[0][2]
                    key = str(hero_num)
                    # Strategy A entries take priority
                    if key not in mapping:
                        mapping[key] = hero["name"]
                search_from = pos + 1

    return mapping


# ---------------------------------------------------------------------------
# Phase 2: extract formulas from formula blobs
# ---------------------------------------------------------------------------

def extract_formulas(outer: list) -> tuple[dict, set]:
    """
    Returns (formula_dict, buff_skill_ids):
      formula_dict: skill_id (int) -> formula_string
      buff_skill_ids: set of skill_ids whose blob contains buff/conditional patterns
    Collects ALL formula components per blob (stored as separate fixstr fields)
    and joins them with '+' to reconstruct the full multi-component formula.
    """
    results = {}
    buff_skill_ids: set = set()

    for blob in outer:
        if not isinstance(blob, bytes):
            continue
        if not FORMULA_PAT_BYTES.search(blob):
            continue

        # Get skill IDs from l10n pattern
        skill_ids = [int(m.group(1)) for m in SKILL_L10N_PAT.finditer(blob)]
        if not skill_ids:
            continue

        has_buff_pattern = bool(BUFF_PAT_BYTES.search(blob))

        # Collect all formula components from raw bytes (fixstr-prefixed)
        components = []
        seen = set()
        for m in FORMULA_PAT_BYTES.finditer(blob):
            start = m.start()
            candidate = None
            if start > 0 and 0xA0 <= blob[start - 1] <= 0xBF:
                slen = blob[start - 1] & 0x1F
                end = start + slen
                if end <= len(blob):
                    s = blob[start:end].decode("utf-8", errors="replace")
                    # Only use full fixstr if it's a clean formula (no garbage bytes)
                    if FORMULA_STRICT_PAT.match(s):
                        candidate = s
            if candidate is None:
                # Fallback: use only the regex-matched portion (always clean)
                candidate = m.group().decode("ascii", errors="replace")
            if candidate not in seen:
                seen.add(candidate)
                components.append(candidate)

        if not components:
            continue

        # Join multi-component formulas (e.g. '4.85*ATK' + '0.23*HP' -> '4.85*ATK+0.23*HP')
        formula = "+".join(components)

        for sid in skill_ids:
            if sid not in results:
                results[sid] = formula
            if has_buff_pattern:
                buff_skill_ids.add(sid)

    return results, buff_skill_ids


# ---------------------------------------------------------------------------
# Phase 3: assemble and save
# ---------------------------------------------------------------------------

def assemble_entries(formula_dict: dict, hero_map: dict, heroes_json: list, buff_skill_ids: set) -> list:
    """
    Combine formula_dict + hero_map + heroes_json + buff_skill_ids into final entries.
    Each entry: {hero_numeric_id, hero_name, skill_id, skill_index, skill_name, formula,
                 buff_dependent (bool)}
    """
    # Build heroes.json lookup: hero_name -> skills list
    hero_skills_by_name = {h["name"]: h["skills"] for h in heroes_json}

    entries = []
    for skill_id, formula in sorted(formula_dict.items()):
        hero_num = skill_id // 100
        skill_idx = skill_id % 100  # 1-indexed

        hero_name = hero_map.get(str(hero_num), f"HERO_{hero_num}")

        skill_name = None
        skills = hero_skills_by_name.get(hero_name)
        if skills and 1 <= skill_idx <= len(skills):
            skill_name = skills[skill_idx - 1]["name"]

        # Detect target-stat scaling directly from formula string
        uses_target_stat = any(t in formula for t in ("TRG_HP", "TRG_DEF", "TRG_ATK"))

        entry: dict = {
            "hero_numeric_id": hero_num,
            "hero_name": hero_name,
            "skill_id": skill_id,
            "skill_index": skill_idx,
            "skill_name": skill_name or f"SKILL_{skill_idx}",
            "formula": formula,
        }
        if skill_id in buff_skill_ids:
            entry["buff_dependent"] = True
        if uses_target_stat:
            entry["target_stat_scaling"] = True
        entries.append(entry)
    return entries


def save_output(entries: list, game_version: str) -> None:
    output = {
        "extracted_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "game_version": game_version,
        "count": len(entries),
        "formula_notation": FORMULA_NOTATION_NOTES,
        "entries": entries,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


def _formula_flags(e: dict) -> str:
    flags = []
    if e.get("target_stat_scaling"):
        flags.append("target HP/stat")
    if e.get("buff_dependent"):
        flags.append("buff-dependent")
    return ", ".join(flags)


def save_markdown(entries: list, game_version: str) -> None:
    named = [e for e in entries if not e["hero_name"].startswith("HERO_")]
    unnamed = [e for e in entries if e["hero_name"].startswith("HERO_")]
    extracted_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines = [
        f"# RSL Skill Multipliers",
        f"",
        f"Extracted: {extracted_at} | Game version: {game_version} | "
        f"{len(entries)} entries ({len(named)} named)",
        f"",
        f"## Formula Notation",
        f"",
        f"| Token | Meaning |",
        f"|-------|---------|",
    ]
    for token, meaning in FORMULA_NOTATION_NOTES.items():
        lines.append(f"| `{token}` | {meaning} |")

    lines += [
        f"",
        f"**Multi-component formulas** (e.g. `4.85*ATK+0.23*HP`) — damage adds all components. "
        f"Each component is `coefficient * stat`. "
        f"Sites like hellhades.com often show only the primary (first) component.",
        f"",
        f"---",
        f"",
        f"## Named Heroes ({len(named)})",
        f"",
        f"| Hero | Skill | Index | Formula | Notes |",
        f"|------|-------|-------|---------|-------|",
    ]
    for e in sorted(named, key=lambda x: (x["hero_name"], x["skill_index"])):
        flags = _formula_flags(e)
        lines.append(
            f"| {e['hero_name']} | {e['skill_name']} | {e['skill_index']} "
            f"| `{e['formula']}` | {flags} |"
        )

    lines += [
        f"",
        f"---",
        f"",
        f"## All Entries ({len(entries)} total)",
        f"",
        f"Unnamed heroes shown as `HERO_NNN` where NNN is the internal numeric ID.",
        f"",
        f"| Hero ID | Skill | Index | Formula | Notes |",
        f"|---------|-------|-------|---------|-------|",
    ]
    for e in entries:
        flags = _formula_flags(e)
        lines.append(
            f"| {e['hero_name']} | {e['skill_name']} | {e['skill_index']} "
            f"| `{e['formula']}` | {flags} |"
        )

    MARKDOWN_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MARKDOWN_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def compute_diff(old_entries: list, new_entries: list) -> list:
    """Return list of change dicts for added or changed rows."""
    old_map = {e["skill_id"]: e for e in old_entries}
    new_map = {e["skill_id"]: e for e in new_entries}
    changes = []

    for sid, new_e in new_map.items():
        old_e = old_map.get(sid)
        if old_e is None:
            changes.append({"type": "added", **new_e})
        elif old_e["formula"] != new_e["formula"]:
            changes.append(
                {
                    "type": "changed",
                    "old_formula": old_e["formula"],
                    **new_e,
                }
            )

    for sid in old_map:
        if sid not in new_map:
            changes.append({"type": "removed", **old_map[sid]})

    return sorted(changes, key=lambda c: (c["type"], c["hero_name"], c["skill_id"]))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Extract RSL skill formulas from game static-data")
    parser.add_argument("--path", help="Path to static-data root directory")
    args = parser.parse_args()

    static_root = Path(args.path) if args.path else DEFAULT_STATIC_DATA_ROOT
    data_file = find_static_data_file(static_root)
    game_version = data_file.parent.name  # e.g. "11.50.1"

    print(f"Reading: {data_file}")
    print(f"Game version: {game_version}")

    with open(data_file, "rb") as f:
        raw_bytes = f.read()

    print(f"File size: {len(raw_bytes) / 1024:.1f} KB")
    outer = msgpack.unpackb(raw_bytes, raw=True, strict_map_key=False)
    print(f"Blobs: {len(outer) - 1}")

    # Load heroes.json for name/skill lookup
    heroes_json = []
    if HEROES_JSON_PATH.exists():
        with open(HEROES_JSON_PATH, encoding="utf-8") as f:
            heroes_json = json.load(f)
        print(f"heroes.json: {len(heroes_json)} heroes loaded")
    else:
        print(f"WARNING: heroes.json not found at {HEROES_JSON_PATH}")

    # Build mappings
    print("\nBuilding hero name map...")
    hero_map = build_hero_name_map(outer, heroes_json)
    print(f"  Resolved: {len(hero_map)} hero names")

    print("Extracting skill formulas...")
    formula_dict, buff_skill_ids = extract_formulas(outer)
    print(f"  Found: {len(formula_dict)} skill formulas")
    print(f"  Buff/conditional: {len(buff_skill_ids)} skills")

    # Assemble entries
    entries = assemble_entries(formula_dict, hero_map, heroes_json, buff_skill_ids)
    named = sum(1 for e in entries if not e["hero_name"].startswith("HERO_"))
    skill_named = sum(1 for e in entries if not e["skill_name"].startswith("SKILL_"))
    print(f"\nTotal entries: {len(entries)}")
    print(f"  With hero name: {named}/{len(entries)}")
    print(f"  With skill name: {skill_named}/{len(entries)}")

    # Load previous data for diff
    old_entries = []
    if OUTPUT_PATH.exists():
        try:
            with open(OUTPUT_PATH, encoding="utf-8") as f:
                prev = json.load(f)
            old_entries = prev.get("entries", [])
            old_version = prev.get("game_version", "unknown")
            print(f"\nPrevious data: {len(old_entries)} entries (version {old_version})")
        except Exception:
            pass

    # Show diff
    if old_entries:
        changes = compute_diff(old_entries, entries)
        if changes:
            print(f"\n=== CHANGES ({len(changes)}) ===")
            for c in changes:
                t = c["type"].upper()
                hero = c["hero_name"]
                skill = c["skill_name"]
                formula = c["formula"]
                if t == "CHANGED":
                    print(f"  [{t}] {hero} / {skill}: {c['old_formula']} -> {formula}")
                elif t == "ADDED":
                    print(f"  [{t}] {hero} / {skill}: {formula}")
                else:
                    print(f"  [{t}] {hero} / {skill}")
        else:
            print("\nNo changes since last run.")
    else:
        print("\nFirst run — no previous data to diff.")

    # Save
    save_output(entries, game_version)
    save_markdown(entries, game_version)
    print(f"\nSaved: {OUTPUT_PATH}")
    print(f"Saved: {MARKDOWN_PATH}")

    # Print sample of named entries
    named_entries = [e for e in entries if not e["hero_name"].startswith("HERO_")]
    if named_entries:
        print(f"\nSample named entries ({len(named_entries)} total):")
        for e in named_entries[:15]:
            print(f"  {e['hero_name']} / {e['skill_name']}: {e['formula']}")

    # Print special-mechanic entries
    buff_entries = [e for e in entries if e.get("buff_dependent")]
    trg_entries = [e for e in entries if e.get("target_stat_scaling")]
    if buff_entries:
        print(f"\nBuff-dependent skills ({len(buff_entries)}) — damage scales with active buff count:")
        for e in buff_entries[:10]:
            print(f"  {e['hero_name']} / {e['skill_name']}: {e['formula']}")
    if trg_entries:
        print(f"\nTarget-stat scaling skills ({len(trg_entries)}) — damage uses target's own stats:")
        for e in trg_entries[:10]:
            print(f"  {e['hero_name']} / {e['skill_name']}: {e['formula']}")


if __name__ == "__main__":
    main()
