import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import yaml from 'js-yaml';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export interface DivisionMeta {
  id: string;
  label: string;
  icon: string;
  color: string;
  agentCount: number;
}

export interface AgentSummary {
  slug: string;
  division: string;
  name: string;
  description: string;
  color?: string;
  emoji?: string;
  vibe?: string;
}

export interface AgentDetail extends AgentSummary {
  filepath: string;
  content: string;
  rawFrontmatter: Record<string, any>;
}

export interface RouteRecommendation {
  agent: AgentSummary;
  score: number;
  matchReason: string;
}

export class AgentCatalog {
  private rootDir: string;
  private divisionsMap: Map<string, DivisionMeta> = new Map();
  private agentsMap: Map<string, AgentDetail> = new Map(); // key: "division/slug" or "slug"
  private loaded = false;

  constructor(customRootDir?: string) {
    if (customRootDir) {
      this.rootDir = path.resolve(customRootDir);
    } else if (process.env.AGENCY_AGENTS_ROOT) {
      this.rootDir = path.resolve(process.env.AGENCY_AGENTS_ROOT);
    } else {
      // Default: integrations/mcp-server/dist/ -> root dir is 3 levels up
      this.rootDir = path.resolve(__dirname, '../../../');
    }
  }

  public async init(): Promise<void> {
    if (this.loaded) return;

    const divisionsPath = path.join(this.rootDir, 'divisions.json');
    if (!fs.existsSync(divisionsPath)) {
      throw new Error(`divisions.json not found at ${divisionsPath}. Make sure AGENCY_AGENTS_ROOT points to agency-agents repository.`);
    }

    const divisionsRaw = JSON.parse(fs.readFileSync(divisionsPath, 'utf-8'));
    const divisionsObj = divisionsRaw.divisions || {};

    for (const [id, meta] of Object.entries<any>(divisionsObj)) {
      this.divisionsMap.set(id, {
        id,
        label: meta.label,
        icon: meta.icon,
        color: meta.color,
        agentCount: 0
      });
    }

    // Scan each division directory for markdown agent files
    for (const divisionId of this.divisionsMap.keys()) {
      const divisionDir = path.join(this.rootDir, divisionId);
      if (!fs.existsSync(divisionDir) || !fs.statSync(divisionDir).isDirectory()) {
        continue;
      }

      const files = fs.readdirSync(divisionDir);
      let count = 0;

      for (const file of files) {
        if (!file.endsWith('.md')) continue;

        const filepath = path.join(divisionDir, file);
        const fileContent = fs.readFileSync(filepath, 'utf-8');

        // Parse frontmatter
        const parsed = this.parseMarkdownFile(fileContent);
        if (!parsed) continue;

        const slug = file.replace(/\.md$/, '');
        const detail: AgentDetail = {
          slug,
          division: divisionId,
          name: parsed.frontmatter.name || slug,
          description: parsed.frontmatter.description || '',
          color: parsed.frontmatter.color,
          emoji: parsed.frontmatter.emoji,
          vibe: parsed.frontmatter.vibe,
          filepath,
          content: parsed.content,
          rawFrontmatter: parsed.frontmatter
        };

        this.agentsMap.set(`${divisionId}/${slug}`, detail);
        this.agentsMap.set(slug, detail); // allow lookup by slug alone if unique
        count++;
      }

      const divMeta = this.divisionsMap.get(divisionId);
      if (divMeta) {
        divMeta.agentCount = count;
      }
    }

    this.loaded = true;
  }

  private parseMarkdownFile(fileContent: string): { frontmatter: Record<string, any>; content: string } | null {
    const frontmatterRegex = /^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/;
    const match = fileContent.match(frontmatterRegex);

    if (!match) {
      return null;
    }

    try {
      const frontmatter = yaml.load(match[1]) as Record<string, any>;
      return {
        frontmatter: frontmatter || {},
        content: match[2].trim()
      };
    } catch {
      return null;
    }
  }

  public getDivisions(): DivisionMeta[] {
    return Array.from(this.divisionsMap.values());
  }

  public getAgents(divisionId?: string): AgentSummary[] {
    const results: AgentSummary[] = [];
    const seen = new Set<string>();

    for (const [key, agent] of this.agentsMap.entries()) {
      if (key.includes('/')) { // only process canonical division/slug keys
        if (!divisionId || agent.division === divisionId) {
          if (!seen.has(agent.slug)) {
            seen.add(agent.slug);
            results.push({
              slug: agent.slug,
              division: agent.division,
              name: agent.name,
              description: agent.description,
              color: agent.color,
              emoji: agent.emoji,
              vibe: agent.vibe
            });
          }
        }
      }
    }

    return results;
  }

  public getAgent(identifier: string): AgentDetail | undefined {
    return this.agentsMap.get(identifier);
  }

  public searchAgents(query: string, limit = 10): AgentSummary[] {
    const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
    if (terms.length === 0) return this.getAgents().slice(0, limit);

    const scored: { agent: AgentSummary; score: number }[] = [];
    const seen = new Set<string>();

    for (const [key, agent] of this.agentsMap.entries()) {
      if (!key.includes('/')) continue;
      if (seen.has(agent.slug)) continue;
      seen.add(agent.slug);

      let score = 0;
      const name = agent.name.toLowerCase();
      const desc = agent.description.toLowerCase();
      const vibe = (agent.vibe || '').toLowerCase();
      const div = agent.division.toLowerCase();
      const content = agent.content.toLowerCase();

      for (const term of terms) {
        if (name === term) score += 50;
        else if (name.includes(term)) score += 20;

        if (div === term) score += 15;

        if (desc.includes(term)) score += 10;
        if (vibe.includes(term)) score += 5;
        if (content.includes(term)) score += 1;
      }

      if (score > 0) {
        scored.push({
          agent: {
            slug: agent.slug,
            division: agent.division,
            name: agent.name,
            description: agent.description,
            color: agent.color,
            emoji: agent.emoji,
            vibe: agent.vibe
          },
          score
        });
      }
    }

    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, limit).map((s) => s.agent);
  }

  public routeTask(taskDescription: string, limit = 5): RouteRecommendation[] {
    const terms = taskDescription.toLowerCase().split(/\s+/).filter(Boolean);
    const scored: RouteRecommendation[] = [];
    const seen = new Set<string>();

    for (const [key, agent] of this.agentsMap.entries()) {
      if (!key.includes('/')) continue;
      if (seen.has(agent.slug)) continue;
      seen.add(agent.slug);

      let score = 0;
      const matchedTerms: string[] = [];

      const name = agent.name.toLowerCase();
      const desc = agent.description.toLowerCase();
      const vibe = (agent.vibe || '').toLowerCase();
      const content = agent.content.toLowerCase();

      for (const term of terms) {
        if (term.length < 3) continue; // skip tiny words

        if (name.includes(term)) {
          score += 15;
          matchedTerms.push(`name match '${term}'`);
        }
        if (desc.includes(term)) {
          score += 8;
          matchedTerms.push(`description match '${term}'`);
        }
        if (vibe.includes(term)) {
          score += 5;
          matchedTerms.push(`vibe match '${term}'`);
        }
        if (content.includes(term)) {
          score += 1;
        }
      }

      if (score > 0) {
        const uniqueReasons = Array.from(new Set(matchedTerms)).slice(0, 3).join(', ');
        scored.push({
          agent: {
            slug: agent.slug,
            division: agent.division,
            name: agent.name,
            description: agent.description,
            color: agent.color,
            emoji: agent.emoji,
            vibe: agent.vibe
          },
          score,
          matchReason: uniqueReasons || 'Relevant capability match in operational instructions'
        });
      }
    }

    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, limit);
  }
}
