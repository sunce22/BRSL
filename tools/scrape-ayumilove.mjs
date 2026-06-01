// tools/scrape-ayumilove.mjs
// Scrapes all Legendary + Mythical heroes from ayumilove.net
// Run: node tools/scrape-ayumilove.mjs
// Saves progress to tools/.scrape-cache.json — safe to re-run if interrupted.

import { writeFileSync, readFileSync, existsSync } from 'node:fs';
import { setTimeout as sleep } from 'node:timers/promises';

const LIST_URL = 'https://ayumilove.net/raid-shadow-legends-list-of-champions-by-ranking/';
const DELAY_MS = 800;
const CACHE_FILE = 'tools/.scrape-cache.json';
const OUTPUT_FILE = 'data/heroes.json';

// ---------------------------------------------------------------------------
// Effect auto-detection from skill description text
// ---------------------------------------------------------------------------
const EFFECT_PATTERNS = {
  revive:             [/\bRevives?\b/i],
  heal:               [/\bHeals?\b/i, /Restores? HP/i, /\[Continuous Heal\]/i],
  freeze:             [/\[Freeze\]/i],
  sleep:              [/\[Sleep\]/i],
  stun:               [/\[Stun\]/i],
  provoke:            [/\[Provoke\]/i],
  fear:               [/\[Fear\]/i],
  true_fear:          [/\[True Fear\]/i],
  weaken:             [/\[Weaken\]/i],
  poison:             [/\[Poison\]/i],
  hp_burn:            [/\[HP Burn\]/i],
  burn:               [/\[Burn\]/i],
  hex:                [/\[Hex\]/i],
  bomb:               [/\[Bomb\]/i],
  time_bomb:          [/\[Time Bomb\]/i],
  leech:              [/\[Leech\]/i],
  decrease_def:       [/\[Decrease DEF\]/i],
  decrease_atk:       [/\[Decrease ATK\]/i],
  decrease_spd:       [/\[Decrease SPD\]/i],
  decrease_cr:        [/\[Decrease C\. Rate\]/i],
  decrease_acc:       [/\[Decrease ACC\]/i],
  increase_def:       [/\[Increase DEF\]/i],
  increase_atk:       [/\[Increase ATK\]/i],
  speed_buff:         [/\[Increase SPD\]/i],
  increase_cr:        [/\[Increase C\. Rate\]/i],
  increase_cd:        [/\[Increase C\. DMG\]/i],
  increase_acc:       [/\[Increase ACC\]/i],
  shield:             [/\[Shield\]/i],
  veil:               [/\[Veil\]/i],
  unkillable:         [/\[Unkillable\]/i],
  ally_protect:       [/\[Ally Protect\]/i],
  counterattack:      [/\[Counterattack\]/i],
  reflect_damage:     [/\[Reflect Damage\]/i],
  block_buffs:        [/\[Block Buffs\]/i],
  block_debuffs:      [/\[Block Debuffs\]/i],
  block_damage:       [/\[Block Damage\]/i],
  block_revive:       [/\[Block Revive\]/i],
  necrosis:           [/\[Necrosis\]/i],
  perfect_veil:       [/\[Perfect Veil\]/i],
  decrease_max_hp:    [/\[Decrease MAX HP\]/i],
  sheep:              [/\[Sheep\]/i],
  strengthen:         [/\[Strengthen\]/i],
  increase_res:       [/\[Increase RES\]/i],
  decrease_res:       [/\[Decrease RES\]/i],
  turn_meter_boost:   [/fills?\s+(?:the\s+)?(?:all allies'?\s+)?Turn Meters?/i, /Turn Meter[s]?\s+by\s+\d+%/i],
  turn_meter_decrease:[/[Dd]ecreases?\s+(?:the\s+)?(?:target'?s?\s+)?Turn Meter/i, /empties\s+(?:the\s+)?Turn Meter/i],
  extend_buffs:       [/[Ee]xtends?\s+(?:the\s+)?duration of all(?:\s+ally)?\s+[Bb]uffs/i],
  remove_buffs:       [/[Rr]emoves?\s+all\s+[Bb]uffs/i, /[Rr]emoves?\s+\d+\s+[Bb]uff/i],
  remove_debuffs:     [/[Rr]emoves?\s+all\s+[Dd]ebuffs/i, /[Rr]emoves?\s+\d+\s+[Dd]ebuff/i],
  steal_buffs:        [/[Ss]teals?\s+all\s+[Bb]uffs/i, /[Ss]teals?\s+\d+\s+[Bb]uff/i],
  nuke:               [/extra damage equal to \d+%.*MAX HP/i],
};

function detectEffects(text) {
  const found = [];
  for (const [slug, patterns] of Object.entries(EFFECT_PATTERNS)) {
    if (patterns.some(p => p.test(text))) found.push(slug);
  }
  return found;
}

// ---------------------------------------------------------------------------
// HTML utilities
// ---------------------------------------------------------------------------
function decodeEntities(str) {
  return str
    .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&nbsp;/g, ' ')
    .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
    .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(parseInt(d, 10)));
}

function stripTags(html) {
  return decodeEntities(html.replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim();
}

// ---------------------------------------------------------------------------
// Fetch
// ---------------------------------------------------------------------------
async function fetchHtml(url) {
  const res = await fetch(url, {
    headers: { 'User-Agent': 'Mozilla/5.0 (compatible; rsl-hero-scraper/1.0; +personal-use)' },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.text();
}

// ---------------------------------------------------------------------------
// Parse champion list page → [{name, url, rarity}]
// ---------------------------------------------------------------------------
function parseChampionList(html) {
  const heroes = [];
  // Link text format: "Champion Name (KR-MSF)" where second segment starts with L or M
  // L = Legendary, M = Mythical, E = Epic (skip), etc.
  const seen = new Set();
  const re = /href="(https:\/\/ayumilove\.net\/raid-shadow-legends-[^"]+?-skill-mastery-equip-guide\/)"[^>]*>([^<(]+)\([A-Z]+-([LM])[A-Z]+\)<\/a>/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    if (seen.has(m[1])) continue;
    seen.add(m[1]);
    heroes.push({ name: m[2].trim(), url: m[1], rarity: m[3] === 'M' ? 'Mythical' : 'Legendary' });
  }
  return heroes;
}

// ---------------------------------------------------------------------------
// Parse individual hero page → {faction, affinity, role, rarity, skills}
// ---------------------------------------------------------------------------

function parseSingleSkillBlock(pInnerHtml) {
  const strongMatch = pInnerHtml.match(/<strong[^>]*>([^<]+)<\/strong>/);
  if (!strongMatch) return null;

  let rawName = decodeEntities(strongMatch[1]).trim();
  if (!rawName || rawName.length > 80) return null;

  // Cooldown is in the name: "Skill Name (Cooldown: 5 turns)"
  let cooldown = 0;
  const cdMatch = rawName.match(/\s*\(Cooldown:\s*(\d+)\s*turns?\)/i);
  if (cdMatch) {
    cooldown = parseInt(cdMatch[1], 10);
    rawName = rawName.replace(cdMatch[0], '').trim();
  }

  // Description: lines after </strong> until Level N: or Damage Multiplier:
  const afterStrong = pInnerHtml.slice(pInnerHtml.indexOf('</strong>') + 9);
  const lines = afterStrong
    .replace(/<br[^>]*>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .split('\n')
    .map(l => decodeEntities(l).replace(/\s+/g, ' ').trim())
    .filter(Boolean);

  const descLines = [];
  for (const line of lines) {
    if (/^Level\s+\d+:/i.test(line) || /^Damage Multiplier/i.test(line)) break;
    if (line.length < 8) continue;
    descLines.push(line);
  }

  const description = descLines.join(' ').trim();
  if (!description) return null;

  return { name: rawName, description, cooldown, effects: detectEffects(description) };
}

function parseSkillsFromSection(sectionHtml) {
  const skills = [];
  const pRe = /<p[^>]*>([\s\S]*?)<\/p>/g;
  let m;
  while ((m = pRe.exec(sectionHtml)) !== null) {
    const skill = parseSingleSkillBlock(m[1]);
    if (skill) skills.push(skill);
  }
  return skills;
}

function parseHeroPage(html, fallbackRarity) {
  const faction  = (html.match(/FACTION:\s*<a[^>]+>([^<]+)<\/a>/i)  || [])[1]?.trim() || 'Unknown';
  const rarity   = (html.match(/RARITY:\s*<a[^>]+>([^<]+)<\/a>/i)   || [])[1]?.trim() || fallbackRarity;
  const role     = (html.match(/ROLE:\s*<a[^>]+>([^<]+)<\/a>/i)      || [])[1]?.trim() || 'Unknown';
  const affinity = (html.match(/AFFINITY:\s*<a[^>]+>([^<]+)<\/a>/i)  || [])[1]?.trim() || 'Unknown';

  // Isolate the skills section: <h2>...Skills...</h2> → next <h2>
  const skillsSectionMatch = html.match(/<h2[^>]*>[^<]*Skills[^<]*<\/h2>([\s\S]*?)(?=<h2[^>]*>)/i);
  const skillsHtml = skillsSectionMatch?.[1] ?? '';

  const skills = [];
  const isMythical = rarity === 'Mythical' || fallbackRarity === 'Mythical';

  if (isMythical && skillsHtml) {
    // Three sub-sections: Base Form / Alternate Form / Common Skills
    const h3Re = /<h3[^>]*>[^<]*(Base Form|Alternate Form|Common Skills)[^<]*<\/h3>([\s\S]*?)(?=<h3[^>]*>|$)/gi;
    let h3m;
    while ((h3m = h3Re.exec(skillsHtml)) !== null) {
      const label = h3m[1];
      const form = /base/i.test(label) ? 'base' : /alternate/i.test(label) ? 'alternate' : 'common';
      const formSkills = parseSkillsFromSection(h3m[2]);
      formSkills.forEach(s => { s.form = form; });
      skills.push(...formSkills);
    }
  } else {
    skills.push(...parseSkillsFromSection(skillsHtml || html));
  }

  return { faction, rarity, role, affinity, skills };
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
async function main() {
  const cache = existsSync(CACHE_FILE) ? JSON.parse(readFileSync(CACHE_FILE, 'utf8')) : {};

  console.log('Fetching champion list from ayumilove.net...');
  const listHtml = await fetchHtml(LIST_URL);
  const champions = parseChampionList(listHtml);

  if (champions.length === 0) {
    console.error('No champions found — site structure may have changed. Check LIST_URL.');
    process.exit(1);
  }

  console.log(`Found ${champions.length} Legendary/Mythical champions. Starting scrape...`);
  console.log(`Delay: ${DELAY_MS}ms per request. Estimated time: ~${Math.ceil(champions.length * DELAY_MS / 60000)} min\n`);

  const heroes = [];

  for (let i = 0; i < champions.length; i++) {
    const champ = champions[i];
    const label = `[${i + 1}/${champions.length}] ${champ.name}`;

    if (cache[champ.url]) {
      process.stdout.write(`${label} (cached)\n`);
      heroes.push(cache[champ.url]);
      continue;
    }

    process.stdout.write(`${label} ...`);
    try {
      await sleep(DELAY_MS);
      const html = await fetchHtml(champ.url);
      const pageData = parseHeroPage(html, champ.rarity);

      const hero = {
        id: champ.name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, ''),
        name: champ.name,
        rarity: pageData.rarity,
        faction: pageData.faction,
        affinity: pageData.affinity,
        role: pageData.role,
        skills: pageData.skills,
      };

      cache[champ.url] = hero;
      writeFileSync(CACHE_FILE, JSON.stringify(cache, null, 2));
      heroes.push(hero);
      process.stdout.write(` ${pageData.skills.length} skills\n`);
    } catch (err) {
      process.stdout.write(` ERROR: ${err.message} — skipped\n`);
    }
  }

  heroes.sort((a, b) => a.name.localeCompare(b.name));
  writeFileSync(OUTPUT_FILE, JSON.stringify(heroes, null, 2));
  console.log(`\nDone! Written ${heroes.length} heroes to ${OUTPUT_FILE}`);
  console.log('Review data/heroes.json — effects[] are auto-detected from keywords, verify spot-checks.');
}

main().catch(err => { console.error(err.message); process.exit(1); });
