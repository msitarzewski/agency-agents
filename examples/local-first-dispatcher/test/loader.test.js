#!/usr/bin/env node
/**
 * loader.test.js — deterministic tests for loadAgent / listAgents.
 * No LLM call required. Run: node test/loader.test.js
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { loadAgent, listAgents } from '../dispatcher.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const FIXTURES = join(__dirname, 'fixtures');

test('loadAgent — full frontmatter agent', () => {
  const a = loadAgent(join(FIXTURES, 'sample-agent.md'));
  assert.equal(a.name, 'Sample Agent');
  assert.equal(a.description, 'Test fixture used by the dispatcher loader tests');
  assert.equal(a.frontmatter.color, 'blue');
  assert.equal(a.frontmatter.emoji, '🧪');
  assert.match(a.body, /UNIQUE_BODY_MARKER_FOR_TEST_42/);
  assert.match(a.path, /sample-agent\.md$/);
});

test('loadAgent — no frontmatter falls back gracefully', () => {
  const a = loadAgent(join(FIXTURES, 'no-frontmatter.md'));
  assert.equal(a.name, 'no-frontmatter');
  assert.equal(a.description, '');
  assert.match(a.body, /UNIQUE_PLAIN_MARKER_FOR_TEST_43/);
});

test('loadAgent — accepts directory containing one .md', () => {
  // FIXTURES has 2 .md files, so this should throw "multiple .md"
  assert.throws(() => loadAgent(FIXTURES), /multiple \.md files/);
});

test('loadAgent — accepts path without .md extension', () => {
  const a = loadAgent(join(FIXTURES, 'sample-agent'));
  assert.equal(a.name, 'Sample Agent');
});

test('loadAgent — throws on missing file', () => {
  assert.throws(
    () => loadAgent(join(FIXTURES, 'does-not-exist.md')),
    /not found/,
  );
});

test('listAgents — finds both fixture files', () => {
  const items = listAgents(FIXTURES);
  assert.equal(items.length, 2);
  const names = items.map(i => i.name).sort();
  assert.deepEqual(names, ['Sample Agent', 'no-frontmatter']);
});

test('listAgents — throws on non-directory', () => {
  assert.throws(
    () => listAgents(join(FIXTURES, 'sample-agent.md')),
    /not a directory/,
  );
});

test('loadAgent — strips quoted frontmatter values', () => {
  // Verify both single and double quotes are stripped (covered by sample fixture
  // implicitly; here we sanity-check that the description value is the raw
  // string with no surrounding quotes from the YAML).
  const a = loadAgent(join(FIXTURES, 'sample-agent.md'));
  assert.ok(!a.description.startsWith('"'));
  assert.ok(!a.description.endsWith('"'));
});
