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
