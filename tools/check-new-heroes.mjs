// tools/check-new-heroes.mjs
// Fetch AyumiLove champion list and diff against data/heroes.json.
// Reports missing heroes (not yet in DB) — does NOT modify any files.
//
// Run: node tools/check-new-heroes.mjs

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join, dirname } from 'node:path';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const LIST_URL = 'https://ayumilove.net/raid-shadow-legends-list-of-champions-by-ranking/';

// Heroes that exist on AyumiLove but are NOT real in-game champions.
// Confirmed fake/placeholder entries — skip permanently.
const BLOCKLIST = new Set([
  'tikthaa_blackscale', // empty placeholder, does not exist in-game
]);

function toId(name) {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/, '');
}

async function fetchHtml(url) {
  const res = await fetch(url, {
    headers: { 'User-Agent': 'Mozilla/5.0 (compatible; rsl-hero-checker/1.0; +personal-use)' },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.text();
}

function parseChampionList(html) {
  const seen = new Set();
  const heroes = [];
  const re = /href="(https:\/\/ayumilove\.net\/raid-shadow-legends-[^"]+?-skill-mastery-equip-guide\/)"[^>]*>([^<(]+)\([A-Z]+-([LM])[A-Z]+\)<\/a>/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    if (seen.has(m[1])) continue;
    seen.add(m[1]);
    const name = m[2].trim();
    heroes.push({ name, id: toId(name), rarity: m[3] === 'M' ? 'Mythical' : 'Legendary', url: m[1] });
  }
  return heroes;
}

async function main() {
  // Load current DB
  const db = JSON.parse(readFileSync(join(ROOT, 'data/heroes.json'), 'utf8'));
  const dbIds = new Set(db.map(h => h.id));

  console.log(`Current DB: ${db.length} heroes\n`);
  console.log(`Fetching champion list from AyumiLove...`);

  const html = await fetchHtml(LIST_URL);
  const ayumi = parseChampionList(html);

  if (ayumi.length === 0) {
    console.error('No champions found — AyumiLove page structure may have changed.');
    process.exit(1);
  }

  console.log(`AyumiLove: ${ayumi.length} Legendary/Mythical heroes\n`);

  // Heroes in AyumiLove but not in DB (skip blocklisted fake entries)
  const missing = ayumi.filter(h => !dbIds.has(h.id) && !BLOCKLIST.has(h.id));
  // Heroes in DB but not in AyumiLove (manual or brand-new before AyumiLove adds them)
  const ayumiIds = new Set(ayumi.map(h => h.id));
  const onlyInDb = db.filter(h => !ayumiIds.has(h.id));

  if (missing.length === 0) {
    console.log('DB is up-to-date — no missing heroes.');
  } else {
    console.log(`MISSING from DB (${missing.length}):`);
    for (const h of missing) {
      console.log(`  [${h.rarity}] ${h.name}`);
      console.log(`    id: ${h.id}`);
      console.log(`    url: ${h.url}`);
    }
    console.log(`\nTo add: node tools/scrape-ayumilove.mjs`);
    console.log(`(scraper uses cache — only fetches missing heroes)\n`);
  }

  if (onlyInDb.length > 0) {
    console.log(`In DB but not on AyumiLove yet (${onlyInDb.length}) — manual entries:`);
    for (const h of onlyInDb) {
      console.log(`  [${h.rarity}] ${h.name} (${h.id})`);
    }
  }
}

main().catch(err => { console.error(err.message); process.exit(1); });
