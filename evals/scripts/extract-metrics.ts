import fs from "fs";
import path from "path";
import matter from "gray-matter";
import { globSync } from "glob";

export interface AgentMetrics {
  name: string;
  description: string;
  category: string;
  filePath: string;
  successMetrics: string[] | null;
  criticalRules: string[] | null;
  deliverableFormat: string | null;
}

/**
 * Parse a single agent markdown file and extract structured metrics.
 */
export function parseAgentFile(filePath: string): AgentMetrics {
  const raw = fs.readFileSync(filePath, "utf-8");
  const { data: frontmatter, content } = matter(raw);

  const category = path.basename(path.dirname(filePath));

  return {
    name: frontmatter.name || path.basename(filePath, ".md"),
    description: frontmatter.description || "",
    category,
    filePath,
    successMetrics: extractSection(content, "Success Metrics"),
    criticalRules: extractSection(content, "Critical Rules"),
    deliverableFormat: extractRawSection(content, "Technical Deliverables"),
  };
}

/**
 * Extract bullet points from a markdown section by heading text.
 * Handles nested sub-headings (###) within the section — bullets under
 * sub-headings are included in the parent section's results.
 */
function extractSection(content: string, sectionName: string): string[] | null {
  const lines = content.split("\n");
  const bullets: string[] = [];
  let inSection = false;
  let sectionLevel = 0;

  for (const line of lines) {
    const headingMatch = line.match(/^(#{1,4})\s/);

    const headingText = line.replace(/^#{1,4}\s+/, "").replace(/[\p{Emoji_Presentation}\p{Emoji}\uFE0F]/gu, "").trim().toLowerCase();
    if (headingMatch && headingText.includes(sectionName.toLowerCase())) {
      inSection = true;
      sectionLevel = headingMatch[1].length;
      continue;
    }

    if (inSection && headingMatch) {
      const currentLevel = headingMatch[1].length;
      // Stop if we hit a heading at the same level or higher (smaller number)
      if (currentLevel <= sectionLevel) {
        break;
      }
      // Sub-headings within the section: keep going, collect bullets underneath
      continue;
    }

    if (inSection && /^[-*]\s/.test(line.trim())) {
      const bullet = line.trim().replace(/^[-*]\s+/, "").trim();
      if (bullet.length > 0) {
        bullets.push(bullet);
      }
    }
  }

  return bullets.length > 0 ? bullets : null;
}

/**
 * Extract raw text content of a section (for deliverable templates with code blocks).
 */
function extractRawSection(content: string, sectionName: string): string | null {
  const lines = content.split("\n");
  const sectionLines: string[] = [];
  let inSection = false;
  let sectionLevel = 0;

  for (const line of lines) {
    const headingMatch = line.match(/^(#{1,4})\s/);

    const headingText = line.replace(/^#{1,4}\s+/, "").replace(/[\p{Emoji_Presentation}\p{Emoji}\uFE0F]/gu, "").trim().toLowerCase();
    if (headingMatch && headingText.includes(sectionName.toLowerCase())) {
      inSection = true;
      sectionLevel = headingMatch[1].length;
      continue;
    }

    if (inSection && headingMatch) {
      const currentLevel = headingMatch[1].length;
      if (currentLevel <= sectionLevel) {
        break;
      }
    }

    if (inSection) {
      sectionLines.push(line);
    }
  }

  const text = sectionLines.join("\n").trim();
  return text.length > 0 ? text : null;
}

/**
 * Extract metrics from one or more agent files (accepts a glob pattern or single path).
 */
export function extractMetrics(pattern: string): AgentMetrics[] {
  const files = globSync(pattern);
  return files.map(parseAgentFile);
}

// CLI entrypoint
if (require.main === module) {
  const pattern = process.argv[2] || path.resolve(__dirname, "../../*/*.md");
  const results = extractMetrics(pattern);
  console.log(JSON.stringify(results, null, 2));
  console.error(`Extracted metrics for ${results.length} agents`);
}
