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
