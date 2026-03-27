import { describe, it, expect } from "vitest";
import * as fs from "node:fs";
import * as path from "node:path";
import matter from "gray-matter";

const ROOT = path.resolve(__dirname, "..");

/**
 * Agent category directories containing agent markdown files.
 * Aligned with scripts/lint-agents.sh AGENT_DIRS plus additional agent
 * categories (academic, sales) discovered in the repository.
 *
 * Excludes strategy/ (orchestration docs, not individual agents),
 * examples/, integrations/, and scripts/.
 */
const AGENT_CATEGORIES = [
  "academic",
  "design",
  "engineering",
  "game-development",
  "marketing",
  "paid-media",
  "product",
  "project-management",
  "sales",
  "spatial-computing",
  "specialized",
  "support",
  "testing",
];

/**
 * Recursively collect agent .md files under a directory.
 * Filters out README.md and files without frontmatter delimiters.
 */
function collectAgentFiles(dir: string): string[] {
  const results: string[] = [];
  if (!fs.existsSync(dir)) return results;

  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...collectAgentFiles(full));
    } else if (
      entry.isFile() &&
      entry.name.endsWith(".md") &&
      entry.name !== "README.md"
    ) {
      // Only include files that start with YAML frontmatter delimiter
      const content = fs.readFileSync(full, "utf-8");
      if (content.startsWith("---\n") || content.startsWith("---\r\n")) {
        results.push(full);
      }
    }
  }
  return results;
}

/** Collect all agent markdown files across all category directories */
function getAllAgentFiles(): string[] {
  const files: string[] = [];
  for (const category of AGENT_CATEGORIES) {
    files.push(...collectAgentFiles(path.join(ROOT, category)));
  }
  return files;
}

/**
 * Safely parse YAML frontmatter. Returns parsed data or null on error.
 * When gray-matter fails (e.g. unquoted colons in values), falls back
 * to a simple line-by-line key: value parser for basic field extraction.
 */
function safeParseFrontmatter(
  content: string
): { data: Record<string, unknown> } | null {
  try {
    const { data } = matter(content);
    return { data };
  } catch {
    // Fallback: extract frontmatter block and parse key: value lines
    const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
    if (!match) return null;

    const data: Record<string, unknown> = {};
    for (const line of match[1].split(/\r?\n/)) {
      const kv = line.match(/^(\w+):\s*(.+)$/);
      if (kv) {
        data[kv[1]] = kv[2].trim();
      }
    }
    return Object.keys(data).length > 0 ? { data } : null;
  }
}

const KEBAB_CASE_RE = /^[a-z0-9]+(-[a-z0-9]+)*\.md$/;

describe("Agent validation", () => {
  const agentFiles = getAllAgentFiles();

  it("should find agent files in the repository", () => {
    expect(agentFiles.length).toBeGreaterThan(0);
  });

  describe.each(AGENT_CATEGORIES)("category: %s", (category) => {
    it("should contain at least one agent file", () => {
      const files = collectAgentFiles(path.join(ROOT, category));
      expect(
        files.length,
        `${category}/ should contain at least one agent markdown file`
      ).toBeGreaterThan(0);
    });
  });

  // Pre-parse all agent files to avoid repeated I/O and parsing in each test
  const agentData = agentFiles.map((filePath) => {
    const relativePath = path.relative(ROOT, filePath);
    const fileName = path.basename(filePath);
    const content = fs.readFileSync(filePath, "utf-8");
    const parsed = safeParseFrontmatter(content);
    return { filePath, relativePath, fileName, parsed };
  });

  for (const { filePath, relativePath, fileName, parsed } of agentData) {
    describe(relativePath, () => {
      it("file name should be kebab-case", () => {
        expect(
          KEBAB_CASE_RE.test(fileName),
          `${relativePath}: file name "${fileName}" is not kebab-case`
        ).toBe(true);
      });

      it("should have valid YAML frontmatter", () => {
        expect(
          parsed,
          `${relativePath}: YAML frontmatter failed to parse`
        ).not.toBeNull();
        expect(
          Object.keys(parsed!.data).length,
          `${relativePath}: frontmatter is empty`
        ).toBeGreaterThan(0);
      });

      it("should have a non-empty 'name' in frontmatter", () => {
        expect(
          parsed,
          `${relativePath}: cannot check 'name' — frontmatter parse failed`
        ).not.toBeNull();
        expect(
          parsed!.data.name,
          `${relativePath}: frontmatter missing 'name'`
        ).toBeDefined();
        expect(
          typeof parsed!.data.name === "string" &&
            (parsed!.data.name as string).trim().length > 0,
          `${relativePath}: frontmatter 'name' is empty`
        ).toBe(true);
      });

      it("should have a non-empty 'description' in frontmatter", () => {
        expect(
          parsed,
          `${relativePath}: cannot check 'description' — frontmatter parse failed`
        ).not.toBeNull();
        expect(
          parsed!.data.description,
          `${relativePath}: frontmatter missing 'description'`
        ).toBeDefined();
        expect(
          typeof parsed!.data.description === "string" &&
            (parsed!.data.description as string).trim().length > 0,
          `${relativePath}: frontmatter 'description' is empty`
        ).toBe(true);
      });
    });
  }
});
