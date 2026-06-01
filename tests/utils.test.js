// tests/utils.test.js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { escapeHtml, slugToLabel } from '../shared/utils.js';

test('escapeHtml: escapes & < > " \'', () => {
  assert.equal(escapeHtml("a & b < c > d \"e\" f 'g'"), 'a &amp; b &lt; c &gt; d &quot;e&quot; f &#39;g&#39;');
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
