import matter from "gray-matter";
import { readdir, readFile } from "node:fs/promises";
import { join, relative, basename, dirname } from "node:path";

export interface AgentMeta {
  slug: string;
  name: string;
  description: string;
  division: string;
  emoji: string;
  color: string;
  vibe: string;
  filePath: string;
  services?: { name: string; url: string; tier: string }[];
}

export interface Agent extends AgentMeta {
  body: string;
}

const AGENT_DIVISIONS = [
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
  "strategy",
  "support",
  "testing",
];

function slugFromPath(filePath: string): string {
  return basename(filePath, ".md");
}

function divisionFromPath(repoRoot: string, filePath: string): string {
  const rel = relative(repoRoot, filePath);
  const parts = rel.split("/");
  return parts[0];
}

async function findAgentFiles(dir: string): Promise<string[]> {
  const files: string[] = [];
  const entries = await readdir(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await findAgentFiles(fullPath)));
    } else if (entry.name.endsWith(".md") && !entry.name.startsWith("README")) {
      files.push(fullPath);
    }
  }

  return files;
}

function parseAgent(filePath: string, repoRoot: string): Agent | null {
  const raw = Bun.file(filePath);

  return null;
}

export async function loadAgents(repoRoot: string): Promise<Agent[]> {
  const agents: Agent[] = [];

  for (const division of AGENT_DIVISIONS) {
    const divDir = join(repoRoot, division);
    let files: string[];
    try {
      files = await findAgentFiles(divDir);
    } catch {
      continue;
    }

    for (const filePath of files) {
      try {
        const content = await readFile(filePath, "utf-8");
        const { data, content: body } = matter(content);

        if (!data.name || !data.description) continue;

        agents.push({
          slug: slugFromPath(filePath),
          name: data.name,
          description: data.description,
          division: divisionFromPath(repoRoot, filePath),
          emoji: data.emoji || "",
          color: data.color || "",
          vibe: data.vibe || "",
          filePath: relative(repoRoot, filePath),
          services: data.services,
          body: body.trim(),
        });
      } catch {
        continue;
      }
    }
  }

  return agents;
}

export function searchAgents(
  agents: Agent[],
  query: string,
  division?: string,
): AgentMeta[] {
  const q = query.toLowerCase();

  let pool = agents;
  if (division) {
    pool = pool.filter((a) => a.division === division.toLowerCase());
  }

  return pool
    .filter((a) => {
      const haystack =
        `${a.name} ${a.description} ${a.division} ${a.vibe} ${a.emoji}`.toLowerCase();
      return q.split(/\s+/).every((term) => haystack.includes(term));
    })
    .map(({ body, ...meta }) => meta);
}

export function getAgentsByDivision(agents: Agent[]): Record<string, AgentMeta[]> {
  const grouped: Record<string, AgentMeta[]> = {};

  for (const agent of agents) {
    if (!grouped[agent.division]) grouped[agent.division] = [];
    const { body, ...meta } = agent;
    grouped[agent.division].push(meta);
  }

  return grouped;
}
