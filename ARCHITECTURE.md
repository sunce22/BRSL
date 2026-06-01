# RSL Hero Guide — Architecture

## Overview

Browser-based hero and skill reference for Raid: Shadow Legends streamers. Runs as a Twitch Panel extension (shown below the video for viewers) and as an OBS Browser Source overlay (popup-on-demand for the streamer). No backend — fully static files. No build tools — vanilla ES modules loaded directly by the browser. Hero scope: Legendary + Mythical only.

---

## Entry Points

| File | Purpose | When used |
|------|---------|-----------|
| `panel/panel.html` | Twitch Panel — tabbed hero/effects browser, lang toggle, support modal | Loaded by Twitch inside the panel iframe |
| `obs/obs.html` | OBS Browser Source — control panel (hidden via crop) + card overlay (visible on stream) | Added as Browser Source in OBS/Streamlabs |
| `obs/obs-guest.js` | Alternate OBS entry for guest-mode without control panel | Niche / experimental |

---

## Module Map

```
panel/panel.html          obs/obs.html
      |                         |
panel/panel.js           obs/obs.js
      |   \_____________________|
      |           shared/
      |   ┌───────────────────────────────────┐
      |   │ data.js          — fetch + index  │
      |   │ hero-card.js     — HTML renderer  │
      |   │ effects-list.js  — effect rows    │
      |   │ i18n.js          — lang + t()     │
      |   │ effect-descriptions.js — highlights│
      |   │ feedback.js      — CF Worker form │
      |   │ utils.js         — escapeHtml etc │
      |   └───────────────────────────────────┘
      |
      └── data/heroes.json
          i18n/heroes-uk.json
          i18n/ui-uk.json
```

All imports use relative paths. The `?v=N` cache-bust suffix is appended on imports in `obs.js`.

---

## Data Flow

**Heroes list:**
1. `panel.js` / `obs.js` call `loadHeroes('../data/heroes.json')` (shared/data.js).
2. `buildEffectsIndex(heroes)` inverts the data into `{ slug → [{hero, skill}] }`.
3. On hero click, `translateHero(hero)` (i18n.js) overlays UK strings if lang=uk.
4. `renderHeroCard(hero, skillIdx)` (hero-card.js) produces an HTML string — no framework, no virtual DOM.
5. The string is set as `innerHTML` on a container div.

**Effects tab:**
1. `buildEffectsList(effectsIndex)` produces a sorted `[{slug, label}]` array.
2. `renderEffectItem` renders each row; clicking one shows the matching hero list via `renderHeroCard`.

**i18n toggle:**
- `getLang()` / `setLang()` read/write `localStorage['rsl-lang']`.
- On switch to UK, `loadTranslations()` fetches `heroes-uk.json` + `ui-uk.json` once (Promise-cached in `_loading`).
- `t(key)` returns the UK string from `_uiTr` or falls back to the `UI_EN` hardcoded map.
- `translateHero(hero)` merges per-hero name/skill strings from `_heroTr[hero.id]` at render time — the base `heroes` array is never mutated.
- `updateLangButtons()` syncs the `.lang-btn--active` class on all EN/UA buttons in the document.

---

## Key Data Files

| File | Format | Size hint | Purpose | How regenerated |
|------|--------|-----------|---------|-----------------|
| `data/heroes.json` | JSON array | ~600 KB | Source of truth — all Legendary + Mythical heroes, skills, effects | Manual curation / `tools/read-static-data.py` extraction |
| `i18n/heroes-uk.json` | JSON object `{id: {name, skills[]}}` | ~400 KB | Ukrainian hero name + skill text | `python tools/build-heroes-uk.py` |
| `i18n/ui-uk.json` | JSON object `{key: string}` | <5 KB | Ukrainian UI labels (tabs, badges, etc.) | Hand-edited |
| `data/skill-multipliers.json` | JSON | ~200 KB | Raw skill formula data (phase 2 / reference) | `tools/extract-skill-multipliers.py` |

---

## Tools (scripts in tools/)

| Script | Purpose | When to run | Prerequisites |
|--------|---------|-------------|---------------|
| `build-heroes-uk.py` | Build `i18n/heroes-uk.json` from game localization | After game update or new heroes added | RSLHelper at `D:/RSL_Helper_V6/rslSim.dat` **or** live memory dump `tools/l10n-from-memory.json` (preferred) |
| `read-static-data.py` | Dump `StaticDataLocalization` from RSL process via `ReadProcessMemory` into `tools/l10n-from-memory.json` | Before `build-heroes-uk.py` when rslSim.dat is stale | Raid running, admin rights, Windows only |
| `extract-skill-multipliers.py` | Extract skill formula multipliers from Il2Cpp dump | When rebuilding `data/skill-multipliers.json` | `tools/il2cpp-dump/` artifacts |
| `scrape-ayumilove.mjs` | Scrape portrait URLs from ayumilove.net | On-demand portrait discovery | Node.js |
| `package-extension.sh` | Zip files for Twitch Developer Console upload | Before submitting a new extension version | bash / Git Bash |
| `cf-feedback-worker/worker.js` | Cloudflare Worker — receives feedback form POST, forwards to Discord | Deploy once; no routine re-run | `wrangler deploy` from `tools/cf-feedback-worker/` |

---

## i18n System

End-to-end translation pipeline for Ukrainian:

```
Raid process memory
       |
read-static-data.py   (ReadProcessMemory → StaticDataLocalization dictionary)
       |
tools/l10n-from-memory.json    (raw {key: string} cp1251 localization dump)
       |
build-heroes-uk.py    (cross-references heroes.json hero IDs, extracts name + skill text)
       |
i18n/heroes-uk.json   ({heroId: {name, skills: [{name, description}]}})

hand-edited
       |
i18n/ui-uk.json       ({key: label} for all UI strings)

       ↓  runtime
i18n.js loadTranslations()   (fetches both files once, stores in _heroTr / _uiTr)
       |
t(key)           → UI label with EN fallback
effectLabel(slug)→ effect badge label
translateHero()  → returns shallow-merged hero object for rendering
```

Translations are lazy-loaded: fetch only happens when the user selects UK. EN mode requires no fetch (all EN strings are hardcoded in `UI_EN` inside `i18n.js`).

---

## Extension Structure (Twitch)

**Hosting:** All files are static. They must be served from a single HTTPS origin whitelisted in the Twitch Developer Console (`whitelisted_panel_urls` in `manifest.json`). No EBS (Extension Backend Service) is used.

**CSP:** Twitch enforces strict CSP. Constraints that affect this codebase:
- No inline `<script>` — all JS is in external `.js` files loaded as ES modules.
- No `eval` / `new Function`.
- External image fetch (`ayumilove.net` portraits) requires the domain to be in `img-src` policy; `referrerpolicy="no-referrer"` is set on portrait `<img>` tags.
- The feedback form POSTs to a Cloudflare Worker URL — that origin must be in `connect-src`.

**Deployment steps:**
1. Run `tools/package-extension.sh` — produces a zip of `panel/`, `obs/`, `shared/`, `data/`, `i18n/`, `assets/`.
2. Upload zip in [Twitch Developer Console](https://dev.twitch.tv/console/extensions) under the extension version.
3. Set panel viewer URL to `panel/panel.html`, height `500`.
4. Whitelist the hosting domain in `whitelisted_panel_urls`.
5. Submit for review; activate after approval.

**OBS usage** (no Twitch account needed): add `obs/obs.html` as a Browser Source (1920×1080). The control panel is positioned top-left and hidden from the stream via OBS source crop. The card overlay appears bottom-right when a hero is selected.
