# Twitch Extension — Raid Shadow Legends Interactive Guide

**Date:** 2026-05-25
**Status:** Approved

## Overview

Twitch Panel extension for Raid Shadow Legends streamers. Provides an interactive hero/skill reference for both streamers and viewers. Simultaneously serves as an OBS Browser Source overlay for YouTube and dual-platform streams.

## Decisions

| Question | Decision |
|----------|----------|
| Extension type | Twitch Panel (below video) |
| Theme | Neutral Dark (black/grey, white accents) |
| UI layout | Two tabs: Heroes + Effects |
| Hero card content | Skills + cooldowns only (stats = phase 2) |
| OBS source mode | Popup-on-demand via localStorage |
| Tech stack | Vanilla JS, ES modules, no framework |
| Data source | StaticRaidExtraction → filtered heroes.json |
| Hero scope | Legendary + Mythical only (MVP) |
| Language | English |
| Backend (EBS) | None — fully static |

## Architecture

Two independent entry points share a common module layer:

```
twitch-extension/
├── panel/
│   ├── panel.html          # Twitch Panel entry point
│   ├── panel.js
│   └── panel.css
├── obs/
│   ├── obs.html            # OBS Browser Source entry point
│   ├── obs.js
│   └── obs.css
├── shared/
│   ├── data.js             # heroes.json loader + effects index builder
│   ├── hero-card.js        # hero detail renderer
│   ├── effects-list.js     # effects tab renderer
│   └── styles.css          # CSS variables + base styles
├── data/
│   └── heroes.json         # pre-filtered Legendary + Mythical
└── assets/
    └── icons/              # affinity + faction icons
```

No build tools. ES modules via `type="module"`. No external script dependencies (Twitch Extension policy compliance).

## Data Schema

`data/heroes.json` — array of hero objects:

```json
{
  "id": "arbiter",
  "name": "Arbiter",
  "rarity": "Legendary",
  "faction": "Undead Hordes",
  "affinity": "Force",
  "role": "Support",
  "skills": [
    {
      "name": "Fate's Decree",
      "description": "Fills Turn Meters of all allies by 30%. Places a [Speed] buff on all allies for 2 turns.",
      "cooldown": 4,
      "effects": ["turn_meter_boost", "speed_buff"]
    }
  ]
}
```

- `effects` array on each skill enables reverse-lookup from Effects tab
- `stats` field reserved for phase 2 (HP/ATK/DEF/SPD — live battle fetch TBD)
- Effects index built in-memory at startup: `{ effect_slug: [{ hero, skill }, ...] }`

### Data Pipeline (one-time setup)

1. Clone [StaticRaidExtraction](https://github.com/zerfl/StaticRaidExtraction)
2. Filter `hero_types.json` by `rarity: "Legendary" | "Mythical"`
3. Map to schema above, manually annotate `skills[].effects` slugs
4. Save as `data/heroes.json`

Skill effect slugs are hand-curated (no reliable auto-extraction from text descriptions).

## Panel UI (Twitch)

### Tab: Heroes

- Search input at top — real-time filter by hero name
- 2-column grid of hero cards (name, faction, affinity badge)
- Click hero → accordion detail expands below card (no navigation)
- Detail shows: name, rarity/faction/affinity, skill list with descriptions and cooldowns
- Effect tags in skill descriptions are clickable → switch to Effects tab with that effect pre-selected

### Tab: Effects

- Search input at top — real-time filter by effect name
- Alphabetical list of all effect slugs (human-readable: "Turn Meter Boost", "Poison", etc.)
- Click effect → expands list of heroes + specific skill that applies it
- Click hero in expanded list → switch to Heroes tab, open that hero's card

### State

In-memory only (JS variables). No persistence between sessions. Each panel open starts fresh.

### Cross-tab navigation

Both tabs link to each other:
- Effect tag on hero skill → Effects tab (pre-filtered)
- Hero name in effect list → Heroes tab (hero expanded)

## OBS Browser Source

`obs.html` renders with `background: transparent` — OBS composites it over the video.

`obs.html` is both the control interface and the display — the streamer uses OBS's built-in **"Interact"** button to open the browser source and interact with it. Everything runs within OBS's single Chromium context, so `localStorage` works correctly without a separate server.

### Streamer workflow

1. Add `obs.html` as Browser Source in OBS
2. Click OBS "Interact" → browser source opens as interactive panel
3. Streamer selects hero or effect — card renders in the same page
4. Card is visible on stream (OBS composites the transparent page over video)
5. Card auto-dismisses after configurable timeout (default: 8s), or streamer clicks to dismiss
6. Streamer can also hide entirely via OBS Show/Hide hotkey

### Constraints

- Streamer interaction via OBS "Interact" only (not a separate browser window)
- OBS built-in browser is Chromium — `localStorage` and ES modules supported
- Card position: fixed, bottom-right corner, 320px wide, semi-transparent dark background
- Control UI (hero/effect selector) hidden from stream capture via CSS — only the card overlay is composited

### Card content (OBS)

Same hero card as Panel variant A: hero name, faction/affinity, skills with descriptions and cooldowns. Compact layout optimised for overlay readability.

## Phase 2 (out of scope for MVP)

- Hero base stats (HP/ATK/DEF/SPD) — investigate live battle data fetch
- Localisation (Ukrainian + other languages)
- Streamer-triggered sync: show same hero to all Twitch viewers simultaneously via EBS + PubSub
