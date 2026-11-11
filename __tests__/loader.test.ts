/// <reference types="vitest" />
import { describe, it, expect, beforeAll } from 'vitest';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  loadAgentsFromDir,
  loadAgentFile,
  collectMarkdownFiles,
  slugify,
  AGENT_CATEGORIES,
} from '../src/loader.js';

const __filename = fileURLToPath(import.meta.url);
const REPO_ROOT = path.resolve(path.dirname(__filename), '..');

// ---------------------------------------------------------------------------
// slugify
// ---------------------------------------------------------------------------
describe('slugify', () => {
  it('lowercases the input', () => {
    expect(slugify('Frontend Developer')).toBe('frontend-developer');
  });

  it('replaces spaces and special chars with hyphens', () => {
    expect(slugify('UI/UX Designer')).toBe('ui-ux-designer');
  });

  it('strips leading and trailing hyphens', () => {
    expect(slugify('  agent  ')).toBe('agent');
  });

  it('collapses consecutive separators', () => {
    expect(slugify('AI -- Engineer')).toBe('ai-engineer');
  });

  it('handles already-slugified input unchanged', () => {
    expect(slugify('backend-architect')).toBe('backend-architect');
  });
});

// ---------------------------------------------------------------------------
// collectMarkdownFiles
// ---------------------------------------------------------------------------
describe('collectMarkdownFiles', () => {
  it('returns only .md files', () => {
    const files = collectMarkdownFiles(path.join(REPO_ROOT, 'engineering'));
    expect(files.every((f) => f.endsWith('.md'))).toBe(true);
  });

  it('returns a sorted list', () => {
    const files = collectMarkdownFiles(path.join(REPO_ROOT, 'engineering'));
    const sorted = [...files].sort();
    expect(files).toEqual(sorted);
  });

  it('recurses into sub-directories', () => {
    // game-development has sub-directories (unity, unreal-engine, godot, roblox-studio)
    const files = collectMarkdownFiles(path.join(REPO_ROOT, 'game-development'));
    expect(files.length).toBeGreaterThan(4);
  });
});

// ---------------------------------------------------------------------------
// loadAgentFile
// ---------------------------------------------------------------------------
describe('loadAgentFile', () => {
  let engineeringDir: string;
  let firstFile: string;

  beforeAll(() => {
    engineeringDir = path.join(REPO_ROOT, 'engineering');
    const files = collectMarkdownFiles(engineeringDir);
    firstFile = files[0]!;
  });

  it('returns a valid Agent object for a well-formed file', () => {
    const agent = loadAgentFile(firstFile, 'engineering');
    expect(agent).not.toBeNull();
    expect(agent?.name).toBeTruthy();
    expect(agent?.slug).toMatch(/^[a-z0-9-]+$/);
    expect(agent?.description).toBeTruthy();
    expect(agent?.category).toBe('engineering');
    expect(agent?.systemPrompt.length).toBeGreaterThan(0);
  });

  it('filePath on the returned agent matches the input', () => {
    const agent = loadAgentFile(firstFile, 'engineering');
    expect(agent?.filePath).toBe(firstFile);
  });
});

// ---------------------------------------------------------------------------
// loadAgentsFromDir
// ---------------------------------------------------------------------------
describe('loadAgentsFromDir', () => {
  it('loads agents from the repository root', () => {
    const agents = loadAgentsFromDir(REPO_ROOT);
    expect(agents.length).toBeGreaterThan(50);
  });

  it('every returned agent has required fields', () => {
    const agents = loadAgentsFromDir(REPO_ROOT);
    for (const a of agents) {
      expect(a.name).toBeTruthy();
      expect(a.slug).toMatch(/^[a-z0-9-]+$/);
      expect(a.description).toBeTruthy();
      expect(AGENT_CATEGORIES).toContain(a.category);
      expect(a.systemPrompt.length).toBeGreaterThan(0);
    }
  });

  it('returns an empty array for a directory with no agent sub-dirs', () => {
    const agents = loadAgentsFromDir('/tmp');
    expect(agents).toEqual([]);
  });

  it('agent names are unique within the full roster', () => {
    const agents = loadAgentsFromDir(REPO_ROOT);
    const names = agents.map((a) => a.name);
    const unique = new Set(names);
    expect(unique.size).toBe(names.length);
  });
});
