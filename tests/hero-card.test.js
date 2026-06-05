// tests/hero-card.test.js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { renderHeroCard, heroGuideSlug } from '../shared/hero-card.js';

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

test('renderHeroCard: contains guide links', () => {
  const html = renderHeroCard(HERO);
  assert.ok(html.includes('hellhades.com/champions/arbiter/'));
  assert.ok(html.includes('ayumilove.net/raid-shadow-legends-arbiter-skill-mastery-equip-guide/'));
});

test('heroGuideSlug: generates correct slugs', () => {
  assert.equal(heroGuideSlug('Arbiter'), 'arbiter');
  assert.equal(heroGuideSlug("Siphi the Lost Bride"), 'siphi-the-lost-bride');
  assert.equal(heroGuideSlug("Trunda Giltmallet"), 'trunda-giltmallet');
  assert.equal(heroGuideSlug("Warlord"), 'warlord');
});
