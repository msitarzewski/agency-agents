import fs from 'node:fs';
import path from 'node:path';
import type { Agent, AgentCategory } from './types.js';

/** All agent category directory names, in the same order used by bash scripts. */
export const AGENT_CATEGORIES: AgentCategory[] = [
  'design',
  'engineering',
  'game-development',
  'marketing',
  'paid-media',
  'product',
  'project-management',
  'testing',
  'support',
  'spatial-computing',
  'specialized',
];

/**
 * Parse an agent markdown file without relying on a strict YAML library.
 *
 * Many agent files contain colons inside description values (e.g.
 * `description: Zettelkasten. Default: Luhmann`), which violates YAML spec.
 * This parser mirrors the behaviour of the `get_field` awk function in
 * `scripts/lint-agents.sh`: it reads lines inside the frontmatter block and
 * extracts the value after the first `": "` separator on the matching line.
 *
 * @internal
 */
function parseFrontmatter(raw: string): { data: Record<string, string>; body: string } {
  const data: Record<string, string> = {};
  const lines = raw.split('\n');

  // Find opening and closing '---' delimiters
  if (lines[0]?.trimEnd() !== '---') {
    return { data, body: raw };
  }

  let closingIdx = -1;
  for (let i = 1; i < lines.length; i++) {
    if (lines[i]?.trimEnd() === '---') {
      closingIdx = i;
      break;
    }
  }

  if (closingIdx === -1) {
    return { data, body: raw };
  }

  // Extract frontmatter lines
  const fmLines = lines.slice(1, closingIdx);
  for (const line of fmLines) {
    const colonIdx = line.indexOf(': ');
    if (colonIdx !== -1) {
      const key = line.slice(0, colonIdx).trim();
      const value = line.slice(colonIdx + 2).trim();
      data[key] = value;
    } else if (line.includes(':') && !line.includes(': ')) {
      // Handle `key:` with no value (empty string)
      const colonIdx2 = line.indexOf(':');
      const key = line.slice(0, colonIdx2).trim();
      data[key] = '';
    }
  }

  // Body is everything after the closing '---'
  const body = lines.slice(closingIdx + 1).join('\n');
  return { data, body };
}
/**
 * Convert a human-readable agent name to a URL-safe kebab-case slug.
 *
 * @example slugify("Frontend Developer") === "frontend-developer"
 */
export function slugify(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

/**
 * Load and parse a single agent markdown file.
 * Returns `null` when the file is missing required frontmatter fields.
 *
 * @param filePath  Absolute path to the `.md` file.
 * @param category  The agent directory category this file belongs to.
 */
export function loadAgentFile(filePath: string, category: AgentCategory): Agent | null {
  const raw = fs.readFileSync(filePath, 'utf-8');
  const { data, body } = parseFrontmatter(raw);

  if (!data['name'] || !data['description']) {
    return null;
  }

  return {
    name: data['name'],
    slug: slugify(data['name']),
    description: data['description'],
    color: data['color'] ?? 'gray',
    category,
    filePath,
    systemPrompt: body.trim(),
  };
}

/**
 * Scan a repository root directory and return all valid agents found across
 * all known category sub-directories.
 *
 * @param rootDir  Path to the repository root (defaults to the package root).
 */
export function loadAgentsFromDir(rootDir: string): Agent[] {
  const agents: Agent[] = [];

  for (const category of AGENT_CATEGORIES) {
    const categoryDir = path.join(rootDir, category);
    if (!fs.existsSync(categoryDir)) continue;

    const mdFiles = collectMarkdownFiles(categoryDir);

    for (const filePath of mdFiles) {
      const agent = loadAgentFile(filePath, category);
      if (agent !== null) {
        agents.push(agent);
      }
    }
  }

  return agents;
}

/**
 * Recursively collect all `.md` files under a directory, sorted alphabetically.
 *
 * @internal
 */
export function collectMarkdownFiles(dir: string): string[] {
  const results: string[] = [];

  const entries = fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) =>
    a.name.localeCompare(b.name),
  );

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...collectMarkdownFiles(fullPath));
    } else if (entry.isFile() && entry.name.endsWith('.md')) {
      results.push(fullPath);
    }
  }

  return results;
}
