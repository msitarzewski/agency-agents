import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadAgentsFromDir, slugify } from './loader.js';
import type { Agent, AgentCategory } from './types.js';

// ---------------------------------------------------------------------------
// Package-root detection
// ---------------------------------------------------------------------------
// Resolve the repository root relative to this compiled file so the registry
// works both from the source tree and from a published npm package.
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// dist/registry.js  →  go up one level to reach repo root
const PACKAGE_ROOT = path.resolve(__dirname, '..');

// ---------------------------------------------------------------------------
// Registry
// ---------------------------------------------------------------------------

/** Cache map: resolved rootDir → loaded agents array. */
const _cache = new Map<string, Agent[]>();

/**
 * Return the resolved root directory used to load agents.
 * Exported for testing purposes.
 */
export function getPackageRoot(): string {
  return PACKAGE_ROOT;
}

/**
 * Load all agents from disk (or return the cached list on subsequent calls).
 *
 * @param rootDir  Override the default package root. Useful in tests.
 */
export function loadAgents(rootDir?: string): Agent[] {
  const resolvedRoot = rootDir !== undefined ? rootDir : PACKAGE_ROOT;
  const cached = _cache.get(resolvedRoot);
  if (cached !== undefined) {
    return cached;
  }
  const agents = loadAgentsFromDir(resolvedRoot);
  _cache.set(resolvedRoot, agents);
  return agents;
}

/**
 * Retrieve a single agent by **name** (case-insensitive) or **slug**.
 * Returns `undefined` when no match is found.
 *
 * @example
 *   getAgent('frontend-developer')
 *   getAgent('Frontend Developer')
 */
export function getAgent(nameOrSlug: string, rootDir?: string): Agent | undefined {
  const normalised = slugify(nameOrSlug);
  return loadAgents(rootDir).find(
    (a) =>
      a.slug === normalised ||
      a.name.toLowerCase() === nameOrSlug.toLowerCase(),
  );
}

/**
 * Return all agents, optionally filtered by category.
 *
 * @example
 *   listAgents()                        // all agents
 *   listAgents('engineering')           // engineering agents only
 */
export function listAgents(category?: AgentCategory, rootDir?: string): Agent[] {
  const all = loadAgents(rootDir);
  if (category === undefined) return all;
  return all.filter((a) => a.category === category);
}

/**
 * Return all unique category names that have at least one agent loaded.
 */
export function listCategories(rootDir?: string): AgentCategory[] {
  const cats = new Set(loadAgents(rootDir).map((a) => a.category));
  return [...cats];
}

/**
 * Reset the internal cache. Call between tests or when agents are mutated.
 * @internal
 */
export function _resetCache(): void {
  _cache.clear();
}
