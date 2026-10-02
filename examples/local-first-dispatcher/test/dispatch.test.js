#!/usr/bin/env node
/**
 * dispatch.test.js — live dispatch test against a local OpenAI-compatible
 * runtime. Skips cleanly if no runtime is reachable so the test suite stays
 * green in environments without a local LLM.
 *
 * Configure via env:
 *   AGENCY_BASE_URL  (default http://127.0.0.1:11434/v1 — Ollama)
 *   AGENCY_MODEL     (default llama3.1:8b)
 *
 * Run: node test/dispatch.test.js
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { loadAgent, dispatchAgent } from '../dispatcher.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const FIXTURES = join(__dirname, 'fixtures');

const BASE_URL = process.env.AGENCY_BASE_URL || 'http://127.0.0.1:11434/v1';
const MODEL = process.env.AGENCY_MODEL || 'llama3.1:8b';

async function runtimeReachable() {
  try {
    const r = await fetch(`${BASE_URL.replace(/\/+$/, '')}/models`, {
      signal: AbortSignal.timeout(3000),
    });
    return r.ok;
  } catch {
    return false;
  }
}

test('dispatch — sample agent against live runtime', async (t) => {
  if (!(await runtimeReachable())) {
    t.skip(`runtime not reachable at ${BASE_URL} — set AGENCY_BASE_URL/AGENCY_MODEL`);
    return;
  }

  const agent = loadAgent(join(FIXTURES, 'sample-agent.md'));
  const result = await dispatchAgent({
    agent,
    task: 'Say only the word "OK" and stop.',
    baseUrl: BASE_URL,
    model: MODEL,
    maxTokens: 8,
  });

  assert.equal(result.ok, true, `dispatch failed: ${JSON.stringify(result)}`);
  assert.equal(result.agent, 'Sample Agent');
  assert.ok(result.content.length > 0, 'expected non-empty content');
  assert.ok(result.latency_ms > 0, 'expected latency_ms > 0');
});

test('dispatch — empty task returns ok:false with stable error', async () => {
  const agent = loadAgent(join(FIXTURES, 'sample-agent.md'));
  const result = await dispatchAgent({ agent, task: '', baseUrl: BASE_URL, model: MODEL });
  assert.equal(result.ok, false);
  assert.match(result.error, /task required/);
});

test('dispatch — missing agent returns ok:false', async () => {
  const result = await dispatchAgent({ agent: null, task: 'hi', baseUrl: BASE_URL, model: MODEL });
  assert.equal(result.ok, false);
  assert.match(result.error, /agent required/);
});

test('dispatch — unreachable URL returns runtime_unreachable', async (t) => {
  const agent = loadAgent(join(FIXTURES, 'sample-agent.md'));
  const result = await dispatchAgent({
    agent,
    task: 'hi',
    baseUrl: 'http://127.0.0.1:1/v1',  // port 1 should be closed
    model: MODEL,
    timeoutMs: 2000,
  });
  assert.equal(result.ok, false);
  assert.match(result.error, /unreachable|http_/);
});
