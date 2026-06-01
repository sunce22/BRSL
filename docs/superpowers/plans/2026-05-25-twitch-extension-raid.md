# Raid Shadow Legends Twitch Extension — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Vanilla JS Twitch Panel extension + OBS Browser Source popup for RSL hero/skill reference, backed by a static heroes.json dataset.

**Architecture:** Two entry points (`panel/panel.html`, `obs/obs.html`) import pure-function modules from `shared/`. Static `data/heroes.json` pre-built from StaticRaidExtraction. No backend, no build tools, ES modules throughout. No external runtime dependencies.

**Tech Stack:** Vanilla JS (ES modules), CSS custom properties, Node 18+ built-in test runner (`node:test`), Python `http.server` for local dev.

---

## File Map

```
twitch-extension/
├── package.json                  # "type":"module", test script only
├── .gitignore
├── data/
│   └── heroes.json               # pre-filtered Legendary+Mythical heroes
├── shared/
│   ├── styles.css                # CSS variables + base styles (theme)
│   ├── utils.js                  # escapeHtml, slugToLabel
│   ├── data.js                   # loadHeroes, buildEffectsIndex, filters
│   ├── hero-card.js              # renderHeroCard(hero) => HTML string
│   └── effects-list.js           # renderEffectItem(slug, entries) => HTML string
├── panel/
│   ├── panel.html                # Twitch Panel entry point
│   ├── panel.css                 # panel-specific styles
│   └── panel.js                  # tab state, search, accordion, navigation
├── obs/
│   ├── obs.html                  # OBS Browser Source entry point
│   ├── obs.css                   # overlay + control panel styles
│   └── obs.js                    # control panel, card display, auto-dismiss
├── tests/
│   ├── utils.test.js
│   ├── data.test.js
│   ├── hero-card.test.js
│   └── effects-list.test.js
├── tools/
│   └── build-heroes-json.mjs     # one-time data pipeline script
└── extension/
    └── manifest.json             # Twitch Extension manifest
```

---

## Task 1: Scaffolding

**Files:**
- Create: `package.json`
- Create: `.gitignore`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "raid-twitch-extension",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "test": "node --test tests/*.test.js"
  }
}
```

- [ ] **Step 2: Create .gitignore**

```
node_modules/
.superpowers/
*.zip
```

- [ ] **Step 3: Create directory structure**

```bash
mkdir -p data shared panel obs tests tools extension assets/icons
```

- [ ] **Step 4: Commit**

```bash
git add package.json .gitignore
git commit -m "chore: project scaffolding"
```

---

## Task 2: Seed data/heroes.json

**Files:**
- Create: `data/heroes.json`

This seed covers 5 real Legendary heroes with hand-annotated `effects` arrays. Additional heroes are added via the pipeline in Task 12.

- [ ] **Step 1: Create data/heroes.json**

```json
[
  {
    "id": "arbiter",
    "name": "Arbiter",
    "rarity": "Legendary",
    "faction": "Undead Hordes",
    "affinity": "Force",
    "role": "Support",
    "skills": [
      {
        "name": "Judgment",
        "description": "Attacks 1 enemy. Places a 60% [Decrease DEF] debuff for 2 turns.",
        "cooldown": 0,
        "effects": ["decrease_def"]
      },
      {
        "name": "Fate's Decree",
        "description": "Fills the Turn Meters of all allies by 30%. Places a 30% [Speed] buff on all allies for 2 turns.",
        "cooldown": 4,
        "effects": ["turn_meter_boost", "speed_buff"]
      },
      {
        "name": "Renewal",
        "description": "Revives a dead ally with 50% HP. Fills their Turn Meter by 50%.",
        "cooldown": 6,
        "effects": ["revive", "turn_meter_boost"]
      }
    ]
  },
  {
    "id": "siphi",
    "name": "Siphi the Lost Bride",
    "rarity": "Legendary",
    "faction": "Undead Hordes",
    "affinity": "Void",
    "role": "Support",
    "skills": [
      {
        "name": "Beguile",
        "description": "Attacks 1 enemy. Heals all allies by 10% of the damage inflicted.",
        "cooldown": 0,
        "effects": ["heal"]
      },
      {
        "name": "Abate",
        "description": "Heals all allies by 20% of their MAX HP. Extends the duration of all ally buffs by 1 turn.",
        "cooldown": 4,
        "effects": ["heal", "extend_buffs"]
      },
      {
        "name": "Lullaby",
        "description": "Puts 1 random enemy to Sleep for 2 turns. Revives 2 random dead allies with 50% HP. Fills their Turn Meters by 50%.",
        "cooldown": 6,
        "effects": ["sleep", "revive", "turn_meter_boost"]
      }
    ]
  },
  {
    "id": "lyssandra",
    "name": "Lyssandra",
    "rarity": "Legendary",
    "faction": "High Elves",
    "affinity": "Void",
    "role": "Support",
    "skills": [
      {
        "name": "Twist of Fate",
        "description": "Attacks 1 enemy. Fills this champion's Turn Meter by 15%.",
        "cooldown": 0,
        "effects": ["turn_meter_boost"]
      },
      {
        "name": "Time Lapse",
        "description": "Removes all debuffs from all allies. Fills all allies' Turn Meters by 15%.",
        "cooldown": 5,
        "effects": ["remove_debuffs", "turn_meter_boost"]
      },
      {
        "name": "Temporal Realignment",
        "description": "Fills the Turn Meters of all allies by 100%.",
        "cooldown": 7,
        "effects": ["turn_meter_boost"]
      }
    ]
  },
  {
    "id": "tormin",
    "name": "Tormin the Cold",
    "rarity": "Legendary",
    "faction": "Dwarves",
    "affinity": "Magic",
    "role": "Support",
    "skills": [
      {
        "name": "Cold Snap",
        "description": "Attacks 1 enemy. Has a 50% chance of placing a [Freeze] debuff for 1 turn.",
        "cooldown": 0,
        "effects": ["freeze"]
      },
      {
        "name": "Blizzard",
        "description": "Attacks all enemies. Has a 75% chance of placing a [Freeze] debuff for 1 turn.",
        "cooldown": 3,
        "effects": ["freeze"]
      },
      {
        "name": "Winter's Grasp",
        "description": "Places a [Freeze] debuff and a 30% [Decrease SPD] debuff on all enemies.",
        "cooldown": 5,
        "effects": ["freeze", "decrease_spd"]
      }
    ]
  },
  {
    "id": "coldheart",
    "name": "Coldheart",
    "rarity": "Legendary",
    "faction": "Dark Elves",
    "affinity": "Void",
    "role": "Attack",
    "skills": [
      {
        "name": "Heartpiercer",
        "description": "Attacks 1 enemy. This attack always inflicts a Critical Hit.",
        "cooldown": 0,
        "effects": []
      },
      {
        "name": "Icy Shards",
        "description": "Attacks 1 enemy 3 times. Each hit fills this champion's Turn Meter by 10%.",
        "cooldown": 3,
        "effects": ["turn_meter_boost"]
      },
      {
        "name": "Total Demolish",
        "description": "Attacks 1 enemy. Deals extra damage equal to 25% of the target's MAX HP if the target's Turn Meter is below 50%.",
        "cooldown": 5,
        "effects": ["nuke"]
      }
    ]
  }
]
```

- [ ] **Step 2: Commit**

```bash
git add data/heroes.json
git commit -m "data: seed heroes.json with 5 legendary heroes"
```

---

## Task 3: shared/utils.js

**Files:**
- Create: `shared/utils.js`
- Create: `tests/utils.test.js`

- [ ] **Step 1: Write failing tests**

```js
// tests/utils.test.js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { escapeHtml, slugToLabel } from '../shared/utils.js';

test('escapeHtml: escapes & < > "', () => {
  assert.equal(escapeHtml('a & b < c > d "e"'), 'a &amp; b &lt; c &gt; d &quot;e&quot;');
});

test('escapeHtml: passthrough when no special chars', () => {
  assert.equal(escapeHtml('hello world'), 'hello world');
});

test('escapeHtml: coerces non-string to string', () => {
  assert.equal(escapeHtml(42), '42');
});

test('slugToLabel: converts snake_case to Title Case', () => {
  assert.equal(slugToLabel('turn_meter_boost'), 'Turn Meter Boost');
});

test('slugToLabel: single word', () => {
  assert.equal(slugToLabel('freeze'), 'Freeze');
});

test('slugToLabel: already title-ish slug', () => {
  assert.equal(slugToLabel('decrease_def'), 'Decrease Def');
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
node --test tests/utils.test.js
```

Expected: `ERR_MODULE_NOT_FOUND` or similar — `shared/utils.js` does not exist yet.

- [ ] **Step 3: Implement shared/utils.js**

```js
// shared/utils.js
export function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

export function slugToLabel(slug) {
  return slug
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
node --test tests/utils.test.js
```

Expected: `▶ utils.test.js` with 6 passing subtests, no failures.

- [ ] **Step 5: Commit**

```bash
git add shared/utils.js tests/utils.test.js
git commit -m "feat: add utils (escapeHtml, slugToLabel)"
```

---

## Task 4: shared/data.js

**Files:**
- Create: `shared/data.js`
- Create: `tests/data.test.js`

- [ ] **Step 1: Write failing tests**

```js
// tests/data.test.js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  buildEffectsIndex,
  buildEffectsList,
  filterHeroesByName,
  filterEffects,
} from '../shared/data.js';

const HEROES = [
  {
    id: 'arbiter', name: 'Arbiter', rarity: 'Legendary',
    faction: 'Undead Hordes', affinity: 'Force', role: 'Support',
    skills: [
      { name: "Fate's Decree", description: '...', cooldown: 4, effects: ['turn_meter_boost', 'speed_buff'] },
      { name: 'Renewal',        description: '...', cooldown: 6, effects: ['revive', 'turn_meter_boost'] },
    ],
  },
  {
    id: 'siphi', name: 'Siphi the Lost Bride', rarity: 'Legendary',
    faction: 'Undead Hordes', affinity: 'Void', role: 'Support',
    skills: [
      { name: 'Lullaby', description: '...', cooldown: 6, effects: ['sleep', 'revive', 'turn_meter_boost'] },
    ],
  },
];

test('buildEffectsIndex: groups entries by effect slug', () => {
  const index = buildEffectsIndex(HEROES);
  assert.ok(Array.isArray(index['turn_meter_boost']));
  assert.equal(index['turn_meter_boost'].length, 3);
});

test('buildEffectsIndex: each entry has hero and skill', () => {
  const index = buildEffectsIndex(HEROES);
  const entry = index['revive'][0];
  assert.ok(entry.hero);
  assert.ok(entry.skill);
  assert.equal(entry.hero.id, 'arbiter');
  assert.equal(entry.skill.name, 'Renewal');
});

test('buildEffectsIndex: effect present in only one skill', () => {
  const index = buildEffectsIndex(HEROES);
  assert.equal(index['speed_buff'].length, 1);
  assert.equal(index['sleep'].length, 1);
});

test('buildEffectsList: sorted alphabetically by label', () => {
  const index = buildEffectsIndex(HEROES);
  const list = buildEffectsList(index);
  const labels = list.map(e => e.label);
  assert.deepEqual(labels, [...labels].sort());
});

test('buildEffectsList: each item has slug and label', () => {
  const index = buildEffectsIndex(HEROES);
  const list = buildEffectsList(index);
  for (const item of list) {
    assert.ok(item.slug);
    assert.ok(item.label);
  }
});

test('filterHeroesByName: case-insensitive match', () => {
  const result = filterHeroesByName(HEROES, 'arb');
  assert.equal(result.length, 1);
  assert.equal(result[0].id, 'arbiter');
});

test('filterHeroesByName: empty query returns all', () => {
  assert.equal(filterHeroesByName(HEROES, '').length, 2);
  assert.equal(filterHeroesByName(HEROES, '  ').length, 2);
});

test('filterHeroesByName: no match returns empty array', () => {
  assert.equal(filterHeroesByName(HEROES, 'zzz').length, 0);
});

test('filterEffects: filters by label substring', () => {
  const index = buildEffectsIndex(HEROES);
  const list = buildEffectsList(index);
  const result = filterEffects(list, 'turn');
  assert.ok(result.every(e => e.label.toLowerCase().includes('turn')));
  assert.ok(result.length > 0);
});

test('filterEffects: empty query returns all', () => {
  const index = buildEffectsIndex(HEROES);
  const list = buildEffectsList(index);
  assert.equal(filterEffects(list, '').length, list.length);
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
node --test tests/data.test.js
```

Expected: `ERR_MODULE_NOT_FOUND` — `shared/data.js` does not exist yet.

- [ ] **Step 3: Implement shared/data.js**

```js
// shared/data.js
import { slugToLabel } from './utils.js';

export async function loadHeroes(jsonPath = '../data/heroes.json') {
  const response = await fetch(jsonPath);
  if (!response.ok) throw new Error(`Failed to load heroes: ${response.status}`);
  return response.json();
}

export function buildEffectsIndex(heroes) {
  /** @type {Record<string, Array<{hero: object, skill: object}>>} */
  const index = {};
  for (const hero of heroes) {
    for (const skill of hero.skills) {
      for (const slug of skill.effects) {
        if (!index[slug]) index[slug] = [];
        index[slug].push({ hero, skill });
      }
    }
  }
  return index;
}

export function buildEffectsList(effectsIndex) {
  return Object.keys(effectsIndex)
    .map(slug => ({ slug, label: slugToLabel(slug) }))
    .sort((a, b) => a.label.localeCompare(b.label));
}

export function filterHeroesByName(heroes, query) {
  if (!query.trim()) return heroes;
  const q = query.trim().toLowerCase();
  return heroes.filter(h => h.name.toLowerCase().includes(q));
}

export function filterEffects(effectsList, query) {
  if (!query.trim()) return effectsList;
  const q = query.trim().toLowerCase();
  return effectsList.filter(e => e.label.toLowerCase().includes(q));
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
node --test tests/data.test.js
```

Expected: 10 passing subtests, no failures.

- [ ] **Step 5: Commit**

```bash
git add shared/data.js tests/data.test.js
git commit -m "feat: add data module (index, filters)"
```

---

## Task 5: shared/styles.css

**Files:**
- Create: `shared/styles.css`

No automated tests — verified visually in Tasks 9 and 10.

- [ ] **Step 1: Create shared/styles.css**

```css
/* shared/styles.css */
:root {
  --bg:            #111318;
  --bg-card:       #1e2028;
  --bg-hover:      #282c38;
  --bg-input:      #16181f;
  --text:          #e8e8ea;
  --text-muted:    #888;
  --border:        #2a2d38;
  --accent:        #e8e8ea;
  --tab-active-bg: #e8e8ea;
  --tab-active-fg: #111318;

  --badge-legendary: #f0c040;
  --badge-mythical:  #e040fb;
  --badge-force:     #e05050;
  --badge-magic:     #5080e8;
  --badge-spirit:    #50c050;
  --badge-void:      #a050e8;

  --radius: 4px;
  --font: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

*, *::before, *::after { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: var(--font);
  font-size: 13px;
  line-height: 1.4;
}

/* Tabs */
.tabs {
  display: flex;
  border-bottom: 1px solid var(--border);
}

.tab {
  flex: 1;
  padding: 8px 0;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 13px;
  font-family: var(--font);
  transition: color 0.15s;
}

.tab:hover { color: var(--text); }

.tab--active {
  color: var(--tab-active-fg);
  background: var(--tab-active-bg);
  font-weight: 600;
}

/* Search */
.search-input {
  width: 100%;
  padding: 7px 10px;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  font-size: 12px;
  font-family: var(--font);
  outline: none;
}

.search-input:focus { border-color: var(--accent); }
.search-input::placeholder { color: var(--text-muted); }

/* Hero list item */
.hero-item {
  padding: 8px 10px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  margin-bottom: 4px;
  transition: background 0.1s;
}

.hero-item:hover { background: var(--bg-hover); }
.hero-item--active { border-color: var(--accent); }

.hero-item__name {
  font-weight: 600;
  font-size: 13px;
}

.hero-item__meta {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 3px;
}

.hero-item__faction {
  color: var(--text-muted);
  font-size: 11px;
}

/* Badges */
.badge {
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 10px;
  font-weight: 600;
}

.badge--legendary { color: var(--badge-legendary); border: 1px solid var(--badge-legendary); }
.badge--mythical  { color: var(--badge-mythical);  border: 1px solid var(--badge-mythical); }
.badge--force     { color: var(--badge-force);     border: 1px solid var(--badge-force); }
.badge--magic     { color: var(--badge-magic);     border: 1px solid var(--badge-magic); }
.badge--spirit    { color: var(--badge-spirit);    border: 1px solid var(--badge-spirit); }
.badge--void      { color: var(--badge-void);      border: 1px solid var(--badge-void); }

/* Hero detail (accordion) */
.hero-detail {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-top: none;
  border-radius: 0 0 var(--radius) var(--radius);
  padding: 10px;
  margin-bottom: 4px;
}

.hero-detail[hidden] { display: none; }

/* Skill */
.skill {
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
}

.skill:last-child { border-bottom: none; }

.skill__header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 3px;
}

.skill__name { font-weight: 600; font-size: 12px; }

.skill__cooldown {
  font-size: 10px;
  color: var(--text-muted);
}

.skill__description {
  margin: 0 0 5px;
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.5;
}

.skill__effects {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

/* Effect tags (clickable in hero card) */
.effect-tag {
  font-size: 10px;
  padding: 2px 7px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text-muted);
  cursor: pointer;
  font-family: var(--font);
  transition: color 0.1s, border-color 0.1s;
}

.effect-tag:hover {
  color: var(--text);
  border-color: var(--accent);
}

/* Effects list */
.effect-item {
  padding: 8px 10px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  margin-bottom: 4px;
  transition: background 0.1s;
}

.effect-item:hover { background: var(--bg-hover); }
.effect-item--active { border-color: var(--accent); }

.effect-item__label { font-weight: 600; }

.effect-item__count {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}

/* Effect entries (inside expanded effect) */
.effect-entries {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-top: none;
  border-radius: 0 0 var(--radius) var(--radius);
  padding: 6px 10px;
  margin-bottom: 4px;
}

.effect-entries[hidden] { display: none; }

.effect-entry {
  padding: 5px 0;
  border-bottom: 1px solid var(--border);
}

.effect-entry:last-child { border-bottom: none; }

.effect-entry__hero {
  font-weight: 600;
  font-size: 12px;
  cursor: pointer;
  color: var(--text);
  text-decoration: underline;
  text-underline-offset: 2px;
  background: none;
  border: none;
  padding: 0;
  font-family: var(--font);
}

.effect-entry__hero:hover { color: var(--accent); }

.effect-entry__skill {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}
```

- [ ] **Step 2: Commit**

```bash
git add shared/styles.css
git commit -m "feat: add shared CSS theme (neutral dark)"
```

---

## Task 6: shared/hero-card.js

**Files:**
- Create: `shared/hero-card.js`
- Create: `tests/hero-card.test.js`

- [ ] **Step 1: Write failing tests**

```js
// tests/hero-card.test.js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { renderHeroCard } from '../shared/hero-card.js';

const HERO = {
  id: 'arbiter',
  name: 'Arbiter',
  rarity: 'Legendary',
  faction: 'Undead Hordes',
  affinity: 'Force',
  role: 'Support',
  skills: [
    {
      name: "Fate's Decree",
      description: 'Fills Turn Meters by 30%.',
      cooldown: 4,
      effects: ['turn_meter_boost', 'speed_buff'],
    },
    {
      name: 'Judgment',
      description: 'Attacks 1 enemy.',
      cooldown: 0,
      effects: ['decrease_def'],
    },
  ],
};

test('renderHeroCard: returns a string', () => {
  assert.equal(typeof renderHeroCard(HERO), 'string');
});

test('renderHeroCard: contains hero name', () => {
  assert.ok(renderHeroCard(HERO).includes('Arbiter'));
});

test('renderHeroCard: contains faction and affinity', () => {
  const html = renderHeroCard(HERO);
  assert.ok(html.includes('Undead Hordes'));
  assert.ok(html.includes('Force'));
});

test('renderHeroCard: contains skill names', () => {
  const html = renderHeroCard(HERO);
  assert.ok(html.includes("Fate&#39;s Decree") || html.includes("Fate's Decree") || html.includes('Fate'));
  assert.ok(html.includes('Judgment'));
});

test('renderHeroCard: shows cooldown for skills with cooldown > 0', () => {
  assert.ok(renderHeroCard(HERO).includes('CD: 4'));
});

test('renderHeroCard: no cooldown shown for cooldown = 0', () => {
  const html = renderHeroCard(HERO);
  assert.ok(!html.includes('CD: 0'));
});

test('renderHeroCard: effect tags rendered as buttons', () => {
  const html = renderHeroCard(HERO);
  assert.ok(html.includes('data-effect="turn_meter_boost"'));
  assert.ok(html.includes('data-effect="speed_buff"'));
});

test('renderHeroCard: no effect tags for skill with empty effects', () => {
  const hero = { ...HERO, skills: [{ name: 'X', description: 'Y', cooldown: 0, effects: [] }] };
  const html = renderHeroCard(hero);
  assert.ok(!html.includes('data-effect'));
});

test('renderHeroCard: escapes HTML in name', () => {
  const hero = { ...HERO, name: '<script>alert(1)</script>' };
  assert.ok(!renderHeroCard(hero).includes('<script>'));
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
node --test tests/hero-card.test.js
```

Expected: `ERR_MODULE_NOT_FOUND`.

- [ ] **Step 3: Implement shared/hero-card.js**

```js
// shared/hero-card.js
import { escapeHtml, slugToLabel } from './utils.js';

export function renderHeroCard(hero) {
  const skillsHtml = hero.skills.map(renderSkill).join('');
  return `
<div class="hero-card" data-hero-id="${hero.id}">
  <div class="hero-detail__header" style="margin-bottom:8px">
    <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
      <span class="badge badge--${hero.rarity.toLowerCase()}">${escapeHtml(hero.rarity)}</span>
      <span class="badge badge--${hero.affinity.toLowerCase()}">${escapeHtml(hero.affinity)}</span>
      <span style="color:var(--text-muted);font-size:11px">${escapeHtml(hero.faction)}</span>
    </div>
  </div>
  <div class="hero-card__skills">${skillsHtml}</div>
</div>`.trim();
}

function renderSkill(skill) {
  const cdHtml = skill.cooldown > 0
    ? `<span class="skill__cooldown">CD: ${skill.cooldown}</span>`
    : '';
  const effectTagsHtml = skill.effects.length > 0
    ? `<div class="skill__effects">${skill.effects.map(slug =>
        `<button class="effect-tag" data-effect="${slug}">${slugToLabel(slug)}</button>`
      ).join('')}</div>`
    : '';
  return `
<div class="skill">
  <div class="skill__header">
    <span class="skill__name">${escapeHtml(skill.name)}</span>${cdHtml}
  </div>
  <p class="skill__description">${escapeHtml(skill.description)}</p>
  ${effectTagsHtml}
</div>`.trim();
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
node --test tests/hero-card.test.js
```

Expected: 9 passing subtests.

- [ ] **Step 5: Commit**

```bash
git add shared/hero-card.js tests/hero-card.test.js
git commit -m "feat: add hero-card renderer"
```

---

## Task 7: shared/effects-list.js

**Files:**
- Create: `shared/effects-list.js`
- Create: `tests/effects-list.test.js`

- [ ] **Step 1: Write failing tests**

```js
// tests/effects-list.test.js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { renderEffectItem } from '../shared/effects-list.js';

const EFFECT = { slug: 'turn_meter_boost', label: 'Turn Meter Boost' };

const ENTRIES = [
  {
    hero: { id: 'arbiter', name: 'Arbiter' },
    skill: { name: "Fate's Decree", description: 'Fills TM 30%.', cooldown: 4 },
  },
  {
    hero: { id: 'lyssandra', name: 'Lyssandra' },
    skill: { name: 'Time Lapse', description: 'Remove debuffs.', cooldown: 5 },
  },
];

test('renderEffectItem: returns a string', () => {
  assert.equal(typeof renderEffectItem(EFFECT, ENTRIES), 'string');
});

test('renderEffectItem: contains effect label', () => {
  assert.ok(renderEffectItem(EFFECT, ENTRIES).includes('Turn Meter Boost'));
});

test('renderEffectItem: shows entry count', () => {
  assert.ok(renderEffectItem(EFFECT, ENTRIES).includes('2'));
});

test('renderEffectItem: contains hero names', () => {
  const html = renderEffectItem(EFFECT, ENTRIES);
  assert.ok(html.includes('Arbiter'));
  assert.ok(html.includes('Lyssandra'));
});

test('renderEffectItem: contains hero data-hero-id attributes', () => {
  const html = renderEffectItem(EFFECT, ENTRIES);
  assert.ok(html.includes('data-hero-id="arbiter"'));
  assert.ok(html.includes('data-hero-id="lyssandra"'));
});

test('renderEffectItem: contains skill names', () => {
  const html = renderEffectItem(EFFECT, ENTRIES);
  assert.ok(html.includes('Time Lapse'));
});

test('renderEffectItem: entries hidden by default', () => {
  assert.ok(renderEffectItem(EFFECT, ENTRIES).includes(' hidden'));
});

test('renderEffectItem: entries visible when expanded=true', () => {
  assert.ok(!renderEffectItem(EFFECT, ENTRIES, true).includes(' hidden'));
});

test('renderEffectItem: escapes HTML in skill description', () => {
  const entries = [{
    hero: { id: 'x', name: 'X' },
    skill: { name: '<bad>', description: '<script>', cooldown: 0 },
  }];
  assert.ok(!renderEffectItem(EFFECT, entries).includes('<script>'));
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
node --test tests/effects-list.test.js
```

Expected: `ERR_MODULE_NOT_FOUND`.

- [ ] **Step 3: Implement shared/effects-list.js**

```js
// shared/effects-list.js
import { escapeHtml } from './utils.js';

export function renderEffectItem(effect, entries, expanded = false) {
  const entriesHtml = entries.map(({ hero, skill }) => `
<div class="effect-entry">
  <button class="effect-entry__hero" data-hero-id="${hero.id}">${escapeHtml(hero.name)}</button>
  <div class="effect-entry__skill">
    ${escapeHtml(skill.name)}${skill.cooldown > 0 ? ` · CD: ${skill.cooldown}` : ''}
    <br><span style="font-size:10px">${escapeHtml(skill.description)}</span>
  </div>
</div>`).join('');

  return `
<div class="effect-item" data-effect="${effect.slug}">
  <div class="effect-item__label">${escapeHtml(effect.label)}</div>
  <div class="effect-item__count">${entries.length} hero${entries.length !== 1 ? 'es' : ''}</div>
</div>
<div class="effect-entries" data-effect="${effect.slug}"${expanded ? '' : ' hidden'}>
  ${entriesHtml}
</div>`.trim();
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
node --test tests/effects-list.test.js
```

Expected: 7 passing subtests.

- [ ] **Step 5: Run full test suite**

```bash
node --test tests/*.test.js
```

Expected: all tests pass across all 4 test files.

- [ ] **Step 6: Commit**

```bash
git add shared/effects-list.js tests/effects-list.test.js
git commit -m "feat: add effects-list renderer"
```

---

## Task 8: panel/panel.html + panel/panel.css

**Files:**
- Create: `panel/panel.html`
- Create: `panel/panel.css`

- [ ] **Step 1: Create panel/panel.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RSL Guide</title>
  <link rel="stylesheet" href="../shared/styles.css">
  <link rel="stylesheet" href="panel.css">
</head>
<body>
  <div class="panel">
    <div class="tabs">
      <button class="tab tab--active" id="tab-heroes">Heroes</button>
      <button class="tab" id="tab-effects">Effects</button>
    </div>
    <div id="tab-content" class="tab-content"></div>
  </div>
  <script type="module" src="panel.js"></script>
</body>
</html>
```

- [ ] **Step 2: Create panel/panel.css**

```css
/* panel/panel.css */
html, body { height: 100%; overflow: hidden; }

.panel {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.heroes-tab,
.effects-tab {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.heroes-list,
.effects-list-container {
  display: flex;
  flex-direction: column;
  gap: 0;
}
```

- [ ] **Step 3: Commit**

```bash
git add panel/panel.html panel/panel.css
git commit -m "feat: panel HTML shell and CSS"
```

---

## Task 9: panel/panel.js

**Files:**
- Create: `panel/panel.js`

- [ ] **Step 1: Create panel/panel.js**

```js
// panel/panel.js
import { loadHeroes, buildEffectsIndex, buildEffectsList, filterHeroesByName, filterEffects } from '../shared/data.js';
import { renderHeroCard } from '../shared/hero-card.js';
import { renderEffectItem } from '../shared/effects-list.js';
import { escapeHtml } from '../shared/utils.js';

let heroes = [];
let effectsIndex = {};
let effectsList = [];
let activeTab = 'heroes';
let expandedHeroId = null;
let expandedEffectSlug = null;

async function init() {
  heroes = await loadHeroes('../data/heroes.json');
  effectsIndex = buildEffectsIndex(heroes);
  effectsList = buildEffectsList(effectsIndex);
  renderHeroesTab();
  document.getElementById('tab-heroes').addEventListener('click', () => switchTab('heroes'));
  document.getElementById('tab-effects').addEventListener('click', () => switchTab('effects'));
  document.getElementById('tab-content').addEventListener('click', handleClick);
  document.getElementById('tab-content').addEventListener('input', handleInput);
}

function switchTab(tab, opts = {}) {
  activeTab = tab;
  document.getElementById('tab-heroes').classList.toggle('tab--active', tab === 'heroes');
  document.getElementById('tab-effects').classList.toggle('tab--active', tab === 'effects');
  if (tab === 'heroes') {
    expandedHeroId = opts.heroId ?? null;
    renderHeroesTab();
  } else {
    expandedEffectSlug = opts.effectSlug ?? null;
    renderEffectsTab();
  }
}

function handleClick(e) {
  const heroItem = e.target.closest('.hero-item');
  const effectItem = e.target.closest('.effect-item');
  const effectTag = e.target.closest('.effect-tag');
  const heroLink = e.target.closest('.effect-entry__hero');

  if (effectTag) {
    switchTab('effects', { effectSlug: effectTag.dataset.effect });
    return;
  }
  if (heroLink) {
    switchTab('heroes', { heroId: heroLink.dataset.heroId });
    return;
  }
  if (heroItem) {
    const id = heroItem.dataset.heroId;
    expandedHeroId = expandedHeroId === id ? null : id;
    renderHeroesTab(document.getElementById('search-heroes')?.value ?? '');
    return;
  }
  if (effectItem) {
    const slug = effectItem.dataset.effect;
    expandedEffectSlug = expandedEffectSlug === slug ? null : slug;
    renderEffectsTab(document.getElementById('search-effects')?.value ?? '');
  }
}

function handleInput(e) {
  if (e.target.id === 'search-heroes') renderHeroesTab(e.target.value, true);
  if (e.target.id === 'search-effects') renderEffectsTab(e.target.value, true);
}

function renderHeroesTab(query = '', fromSearch = false) {
  const filtered = filterHeroesByName(heroes, query);
  const content = document.getElementById('tab-content');
  content.innerHTML = `
<div class="heroes-tab">
  <input type="text" id="search-heroes" class="search-input" placeholder="Search heroes..." value="${escapeHtml(query)}">
  <div class="heroes-list">
    ${filtered.map(hero => `
      <div class="hero-item${expandedHeroId === hero.id ? ' hero-item--active' : ''}" data-hero-id="${hero.id}">
        <div class="hero-item__name">${escapeHtml(hero.name)}</div>
        <div class="hero-item__meta">
          <span class="badge badge--${hero.affinity.toLowerCase()}">${escapeHtml(hero.affinity)}</span>
          <span class="hero-item__faction">${escapeHtml(hero.faction)}</span>
        </div>
      </div>
      ${expandedHeroId === hero.id ? `<div class="hero-detail">${renderHeroCard(hero)}</div>` : ''}
    `).join('')}
  </div>
</div>`;
  if (fromSearch) {
    const input = document.getElementById('search-heroes');
    if (input) { input.focus(); input.setSelectionRange(query.length, query.length); }
  }
}

function renderEffectsTab(query = '', fromSearch = false) {
  const filtered = filterEffects(effectsList, query);
  const content = document.getElementById('tab-content');
  content.innerHTML = `
<div class="effects-tab">
  <input type="text" id="search-effects" class="search-input" placeholder="Search effects..." value="${escapeHtml(query)}">
  <div class="effects-list-container">
    ${filtered.map(effect => {
      const entries = effectsIndex[effect.slug] ?? [];
      return renderEffectItem(effect, entries, expandedEffectSlug === effect.slug);
    }).join('')}
  </div>
</div>`;
  if (fromSearch) {
    const input = document.getElementById('search-effects');
    if (input) { input.focus(); input.setSelectionRange(query.length, query.length); }
  }
}

init().catch(err => {
  document.getElementById('tab-content').textContent = `Error loading data: ${err.message}`;
});
```

- [ ] **Step 2: Start local dev server**

```bash
python -m http.server 8080
```

- [ ] **Step 3: Open panel in browser**

Navigate to `http://localhost:8080/panel/panel.html`

- [ ] **Step 4: Manual smoke test — Heroes tab**

Verify:
- Heroes list shows 5 heroes (Arbiter, Siphi, Lyssandra, Tormin, Coldheart)
- Typing "arb" in search filters to Arbiter only
- Clearing search shows all 5 heroes
- Clicking Arbiter expands the detail showing Judgment, Fate's Decree, Renewal skills
- Clicking Arbiter again collapses the detail
- Clicking "Turn Meter Boost" effect tag on Fate's Decree switches to Effects tab, with Turn Meter Boost visible

- [ ] **Step 5: Manual smoke test — Effects tab**

Verify:
- Effects list is alphabetical (Decrease Def, Decrease Spd, Extend Buffs, Freeze, ...)
- Typing "turn" filters to Turn Meter Boost only
- Clicking Turn Meter Boost expands entries showing Arbiter (Fate's Decree), Arbiter (Renewal), Siphi (Lullaby), Lyssandra (Twist of Fate), Lyssandra (Time Lapse), Lyssandra (Temporal Realignment), Coldheart (Icy Shards)
- Clicking Arbiter in the entries switches to Heroes tab with Arbiter expanded

- [ ] **Step 6: Commit**

```bash
git add panel/panel.js
git commit -m "feat: panel tab logic, search, accordion, cross-tab navigation"
```

---

## Task 10: obs/obs.html + obs/obs.css + obs/obs.js

**Files:**
- Create: `obs/obs.html`
- Create: `obs/obs.css`
- Create: `obs/obs.js`

The OBS source is a single transparent page. Bottom-right: card overlay (visible on stream). Top-left: control panel (toggled via keyboard `C`, hidden by default). Streamer uses OBS "Interact" to open control, select hero, card appears on stream.

- [ ] **Step 1: Create obs/obs.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>RSL OBS Overlay</title>
  <link rel="stylesheet" href="../shared/styles.css">
  <link rel="stylesheet" href="obs.css">
</head>
<body>
  <!-- Control panel (top-left, hidden from stream via OBS crop) -->
  <div id="control-panel" class="control-panel control-panel--hidden">
    <div class="control-panel__header">
      <span>RSL Hero Guide</span>
      <button id="close-control" class="control-close">✕</button>
    </div>
    <input type="text" id="obs-search" class="search-input" placeholder="Search heroes...">
    <div id="obs-heroes-list" class="obs-heroes-list"></div>
  </div>

  <!-- Toggle button (always visible top-left corner, small) -->
  <button id="toggle-control" class="toggle-btn" title="Toggle hero selector (C)">☰</button>

  <!-- Card overlay (bottom-right, visible on stream) -->
  <div id="card-overlay" class="card-overlay card-overlay--hidden"></div>

  <script type="module" src="obs.js"></script>
</body>
</html>
```

- [ ] **Step 2: Create obs/obs.css**

```css
/* obs/obs.css */
html, body {
  margin: 0;
  width: 1920px;
  height: 1080px;
  background: transparent;
  overflow: hidden;
}

/* Toggle button */
.toggle-btn {
  position: fixed;
  top: 10px;
  left: 10px;
  width: 32px;
  height: 32px;
  background: rgba(17, 19, 24, 0.85);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.toggle-btn:hover { background: rgba(40, 44, 56, 0.95); }

/* Control panel */
.control-panel {
  position: fixed;
  top: 50px;
  left: 10px;
  width: 300px;
  max-height: 500px;
  background: rgba(17, 19, 24, 0.95);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px;
  z-index: 99;
  overflow: hidden;
}

.control-panel--hidden { display: none; }

.control-panel__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 12px;
}

.control-close {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  font-family: var(--font);
}

.control-close:hover { color: var(--text); }

.obs-heroes-list {
  overflow-y: auto;
  flex: 1;
}

/* Card overlay */
.card-overlay {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 320px;
  background: rgba(17, 19, 24, 0.92);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 10px;
  z-index: 50;
  animation: slide-in 0.2s ease-out;
}

.card-overlay--hidden { display: none; }

@keyframes slide-in {
  from { transform: translateX(20px); opacity: 0; }
  to   { transform: translateX(0);    opacity: 1; }
}

.card-overlay__hero-name {
  font-weight: 700;
  font-size: 14px;
  margin-bottom: 6px;
}

.card-overlay__dismiss {
  position: absolute;
  top: 6px;
  right: 8px;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 12px;
  font-family: var(--font);
}

.card-overlay__dismiss:hover { color: var(--text); }

.card-overlay__timer {
  font-size: 10px;
  color: var(--text-muted);
  text-align: right;
  margin-top: 6px;
}
```

- [ ] **Step 3: Create obs/obs.js**

```js
// obs/obs.js
import { loadHeroes, filterHeroesByName } from '../shared/data.js';
import { renderHeroCard } from '../shared/hero-card.js';
import { escapeHtml } from '../shared/utils.js';

const DISMISS_SECONDS = 8;

let heroes = [];
let dismissTimer = null;
let dismissCountdown = null;

async function init() {
  heroes = await loadHeroes('../data/heroes.json');
  renderHeroesList('');

  document.getElementById('toggle-control').addEventListener('click', toggleControl);
  document.getElementById('close-control').addEventListener('click', closeControl);
  document.getElementById('obs-search').addEventListener('input', e => renderHeroesList(e.target.value));
  document.getElementById('obs-heroes-list').addEventListener('click', handleHeroClick);
  document.getElementById('card-overlay').addEventListener('click', e => {
    if (e.target.closest('.card-overlay__dismiss')) dismissCard();
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'c' || e.key === 'C') toggleControl();
    if (e.key === 'Escape') { closeControl(); dismissCard(); }
  });
}

function toggleControl() {
  const panel = document.getElementById('control-panel');
  const hidden = panel.classList.toggle('control-panel--hidden');
  if (!hidden) document.getElementById('obs-search').focus();
}

function closeControl() {
  document.getElementById('control-panel').classList.add('control-panel--hidden');
}

function renderHeroesList(query) {
  const filtered = filterHeroesByName(heroes, query);
  document.getElementById('obs-heroes-list').innerHTML = filtered.map(hero => `
    <div class="hero-item" data-hero-id="${hero.id}" style="cursor:pointer">
      <div class="hero-item__name">${escapeHtml(hero.name)}</div>
      <div class="hero-item__meta">
        <span class="badge badge--${hero.affinity.toLowerCase()}">${escapeHtml(hero.affinity)}</span>
        <span class="hero-item__faction">${escapeHtml(hero.faction)}</span>
      </div>
    </div>
  `).join('');
}

function handleHeroClick(e) {
  const item = e.target.closest('.hero-item');
  if (!item) return;
  const hero = heroes.find(h => h.id === item.dataset.heroId);
  if (!hero) return;
  showCard(hero);
  closeControl();
}

function showCard(hero) {
  clearTimeout(dismissTimer);
  clearInterval(dismissCountdown);

  const overlay = document.getElementById('card-overlay');
  let remaining = DISMISS_SECONDS;

  overlay.innerHTML = `
    <button class="card-overlay__dismiss">✕</button>
    <div class="card-overlay__hero-name">${escapeHtml(hero.name)}</div>
    ${renderHeroCard(hero)}
    <div class="card-overlay__timer" id="dismiss-timer">Auto-dismiss in ${remaining}s</div>
  `;
  overlay.classList.remove('card-overlay--hidden');

  dismissCountdown = setInterval(() => {
    remaining -= 1;
    const timerEl = document.getElementById('dismiss-timer');
    if (timerEl) timerEl.textContent = `Auto-dismiss in ${remaining}s`;
  }, 1000);

  dismissTimer = setTimeout(() => {
    clearInterval(dismissCountdown);
    dismissCard();
  }, DISMISS_SECONDS * 1000);
}

function dismissCard() {
  clearTimeout(dismissTimer);
  clearInterval(dismissCountdown);
  document.getElementById('card-overlay').classList.add('card-overlay--hidden');
}

init().catch(err => console.error('OBS init error:', err));
```

- [ ] **Step 4: Open OBS source in browser**

```bash
# dev server should still be running from Task 9
# if not: python -m http.server 8080
```

Navigate to `http://localhost:8080/obs/obs.html`

- [ ] **Step 5: Manual smoke test**

Verify:
- Page background is white/default (transparent only works in OBS Chromium; use browser for testing layout)
- Clicking ☰ toggle button opens the control panel
- Typing in search filters heroes in real time
- Clicking a hero closes the control panel and shows the card overlay bottom-right
- Card shows hero name, badges, and skills
- Card auto-dismisses after 8 seconds
- Countdown timer shows remaining seconds
- Clicking ✕ on card dismisses immediately
- Pressing `C` toggles the control panel
- Pressing `Escape` closes control + dismisses card

- [ ] **Step 6: Commit**

```bash
git add obs/obs.html obs/obs.css obs/obs.js
git commit -m "feat: OBS overlay with hero selector and auto-dismiss card"
```

---

## Task 11: Twitch Extension manifest + packaging guide

**Files:**
- Create: `extension/manifest.json`

- [ ] **Step 1: Create extension/manifest.json**

```json
{
  "name": "RSL Interactive Guide",
  "description": "Raid Shadow Legends hero and skill reference for streamers and viewers.",
  "summary": "Interactive hero skill reference for Raid: Shadow Legends. Browse Legendary and Mythical champions, their skills, and effect cross-references.",
  "version": "0.0.1",
  "author": "",
  "panel": {
    "viewer_url": "panel/panel.html",
    "height": 500
  },
  "config": {},
  "bits": { "use_bits_callback": false },
  "capabilities": [],
  "whitelisted_config_urls": [],
  "whitelisted_panel_urls": []
}
```

> Note: Full Twitch manifest fields are set in the Twitch Developer Console UI, not this file. This file is a local reference. See https://dev.twitch.tv/docs/extensions/reference/#manifest for the authoritative spec.

- [ ] **Step 2: Create packaging script**

Create `tools/package-extension.sh`:

```bash
#!/bin/bash
# Creates the extension zip for Twitch upload
# Max size: 5MB uncompressed, all files must be relative paths

OUTPUT="extension-build.zip"
rm -f "$OUTPUT"

zip -r "$OUTPUT" \
  panel/ \
  obs/ \
  shared/ \
  data/ \
  assets/ \
  extension/ \
  --exclude "*.DS_Store" \
  --exclude "*/.gitkeep"

echo "Created $OUTPUT ($(du -sh $OUTPUT | cut -f1))"
```

- [ ] **Step 3: Commit**

```bash
git add extension/manifest.json tools/package-extension.sh
git commit -m "chore: add Twitch manifest and packaging script"
```

---

## Task 12: Data pipeline (tools/build-heroes-json.mjs)

This is a standalone Node.js script, not part of the extension bundle. Run once to regenerate `data/heroes.json` from StaticRaidExtraction data.

**Files:**
- Create: `tools/build-heroes-json.mjs`

- [ ] **Step 1: Clone StaticRaidExtraction data**

```bash
# Download the latest static_data.json
curl -L "https://raw.githubusercontent.com/zerfl/StaticRaidExtraction/main/hero_types.json" -o tools/hero_types_raw.json
```

> If the URL has changed, check https://github.com/zerfl/StaticRaidExtraction for the current file path.

- [ ] **Step 2: Inspect the raw data shape**

```bash
node -e "
const d = JSON.parse(require('fs').readFileSync('tools/hero_types_raw.json'));
const first = Array.isArray(d) ? d[0] : Object.values(d)[0];
console.log(JSON.stringify(first, null, 2).slice(0, 800));
"
```

Note the actual field names for: name, rarity, fraction/faction, element/affinity, role, skills. Update the mapping in Step 3 accordingly.

- [ ] **Step 3: Create tools/build-heroes-json.mjs**

```js
// tools/build-heroes-json.mjs
// Run: node tools/build-heroes-json.mjs
// Reads tools/hero_types_raw.json, outputs data/heroes.json (Legendary + Mythical only)
// The `effects` arrays are left empty — fill them manually after generation.

import { readFileSync, writeFileSync } from 'node:fs';

const raw = JSON.parse(readFileSync('tools/hero_types_raw.json', 'utf8'));

// StaticRaidExtraction may return an array or an object keyed by id.
// Normalise to array:
const entries = Array.isArray(raw) ? raw : Object.values(raw);

const TARGET_RARITIES = new Set(['Legendary', 'Mythical']);

function mapAffinity(element) {
  // StaticRaidExtraction uses: 'Force', 'Magic', 'Spirit', 'Void'
  // Adjust if raw data uses different casing or codes:
  const map = { force: 'Force', magic: 'Magic', spirit: 'Spirit', void: 'Void' };
  return map[String(element).toLowerCase()] ?? element;
}

function mapRarity(rarity) {
  const map = { legendary: 'Legendary', mythical: 'Mythical' };
  return map[String(rarity).toLowerCase()] ?? rarity;
}

const heroes = entries
  .filter(h => TARGET_RARITIES.has(mapRarity(h.rarity ?? h.Rarity ?? '')))
  .map(h => ({
    id: String(h.typeId ?? h.id ?? h.name).toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, ''),
    name: h.name ?? h.Name ?? 'Unknown',
    rarity: mapRarity(h.rarity ?? h.Rarity ?? ''),
    faction: h.fraction ?? h.faction ?? h.Fraction ?? 'Unknown',
    affinity: mapAffinity(h.element ?? h.affinity ?? h.Element ?? ''),
    role: h.role ?? h.Role ?? 'Unknown',
    skills: (h.skills ?? h.Skills ?? []).map(s => ({
      name: s.name ?? s.Name ?? 'Unknown',
      description: s.description ?? s.Description ?? '',
      cooldown: Number(s.cooldown ?? s.Cooldown ?? 0),
      effects: [],  // fill manually after generation
    })),
  }))
  .sort((a, b) => a.name.localeCompare(b.name));

writeFileSync('data/heroes.json', JSON.stringify(heroes, null, 2));
console.log(`Written ${heroes.length} heroes to data/heroes.json`);
console.log('Next step: manually fill in skills[].effects arrays for each hero.');
```

- [ ] **Step 4: Run the pipeline**

```bash
node tools/build-heroes-json.mjs
```

Expected: `Written N heroes to data/heroes.json` where N is the number of Legendary + Mythical heroes found.

- [ ] **Step 5: Verify output shape**

```bash
node -e "
const heroes = JSON.parse(require('fs').readFileSync('data/heroes.json'));
console.log('Count:', heroes.length);
console.log('First hero:', JSON.stringify(heroes[0], null, 2).slice(0, 400));
"
```

Verify: hero has `id`, `name`, `rarity`, `faction`, `affinity`, `role`, `skills`. Skills have `effects: []`.

- [ ] **Step 6: Commit pipeline + update heroes.json**

```bash
git add tools/build-heroes-json.mjs data/heroes.json
git commit -m "feat: data pipeline script; regenerate heroes.json from StaticRaidExtraction"
```

> After this commit, `data/heroes.json` contains all Legendary/Mythical heroes with empty `effects` arrays. Populate the `effects` arrays manually over time. Commit after each batch of annotations.
