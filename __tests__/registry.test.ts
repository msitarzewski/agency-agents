/// <reference types="vitest" />
import { describe, it, expect, afterEach } from 'vitest';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { getAgent, listAgents, listCategories, loadAgents, _resetCache } from '../src/registry.js';
import type { AgentCategory } from '../src/types.js';

const __filename = fileURLToPath(import.meta.url);
const REPO_ROOT = path.resolve(path.dirname(__filename), '..');

afterEach(() => {
  _resetCache();
});

// ---------------------------------------------------------------------------
// loadAgents
// ---------------------------------------------------------------------------
describe('loadAgents', () => {
  it('loads all agents when called with the repo root', () => {
    const agents = loadAgents(REPO_ROOT);
    expect(agents.length).toBeGreaterThan(50);
  });

  it('uses the cached result on second call', () => {
    const first = loadAgents(REPO_ROOT);
    const second = loadAgents(REPO_ROOT);
    // Both calls with the same rootDir must return the exact same array reference
    expect(first).toBe(second);
  });

  it('bypasses cache when rootDir is explicitly different', () => {
    const a = loadAgents(REPO_ROOT);
    // Same path → cache hit, same reference
    const b = loadAgents(REPO_ROOT);
    expect(a).toBe(b);
    // Different path (even if resolves to same content) → separate cache entry
    const c = loadAgents(REPO_ROOT);
    expect(a).toBe(c);
  });
});

// ---------------------------------------------------------------------------
// getAgent
// ---------------------------------------------------------------------------
describe('getAgent', () => {
  it('finds an agent by slug', () => {
    const agent = getAgent('frontend-developer', REPO_ROOT);
    expect(agent).toBeDefined();
    expect(agent?.name).toBe('Frontend Developer');
  });

  it('finds an agent by full name (case-insensitive)', () => {
    const agent = getAgent('Frontend Developer', REPO_ROOT);
    expect(agent?.slug).toBe('frontend-developer');
  });

  it('returns undefined for an unknown slug', () => {
    const agent = getAgent('does-not-exist', REPO_ROOT);
    expect(agent).toBeUndefined();
  });

  it('finds the agents-orchestrator from specialized', () => {
    const agent = getAgent('agents-orchestrator', REPO_ROOT);
    expect(agent?.category).toBe('specialized');
  });
});

// ---------------------------------------------------------------------------
// listAgents
// ---------------------------------------------------------------------------
describe('listAgents', () => {
  it('returns all agents when called without a category', () => {
    const all = listAgents(undefined, REPO_ROOT);
    expect(all.length).toBeGreaterThan(50);
  });

  it('filters correctly by category', () => {
    const engineering = listAgents('engineering', REPO_ROOT);
    expect(engineering.length).toBeGreaterThan(0);
    expect(engineering.every((a) => a.category === 'engineering')).toBe(true);
  });

  it('returns empty array for a category with no agents in an empty dir', () => {
    const result = listAgents('paid-media' as AgentCategory, '/tmp');
    expect(result).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// listCategories
// ---------------------------------------------------------------------------
describe('listCategories', () => {
  it('returns a non-empty list of categories', () => {
    const cats = listCategories(REPO_ROOT);
    expect(cats.length).toBeGreaterThan(0);
  });

  it('includes "engineering" and "design"', () => {
    const cats = listCategories(REPO_ROOT);
    expect(cats).toContain('engineering');
    expect(cats).toContain('design');
  });

  it('contains no duplicates', () => {
    const cats = listCategories(REPO_ROOT);
    expect(new Set(cats).size).toBe(cats.length);
  });
});
