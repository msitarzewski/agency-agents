#!/usr/bin/env bun

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { resolve } from "node:path";
import {
  loadAgents,
  searchAgents,
  getAgentsByDivision,
  type Agent,
  type AgentMeta,
} from "./parser.js";

const REPO_ROOT =
  process.env.AGENCY_AGENTS_PATH || resolve(import.meta.dir, "../../..");

let agents: Agent[] = [];

async function ensureLoaded(): Promise<Agent[]> {
  if (agents.length === 0) {
    agents = await loadAgents(REPO_ROOT);
  }
  return agents;
}

const server = new McpServer({
  name: "agency-agents",
  version: "1.0.0",
});

// ---------------------------------------------------------------------------
// Tool: list_agents
// ---------------------------------------------------------------------------
server.tool(
  "list_agents",
  "List all available AI specialist agents. Optionally filter by division (e.g. engineering, design, marketing). Returns agent name, emoji, description, and division for each match.",
  {
    division: z
      .string()
      .optional()
      .describe(
        "Filter by division name: academic, design, engineering, game-development, marketing, paid-media, product, project-management, sales, spatial-computing, specialized, strategy, support, testing",
      ),
  },
  async ({ division }) => {
    const all = await ensureLoaded();
    let results: AgentMeta[];

    if (division) {
      const d = division.toLowerCase();
      results = all
        .filter((a) => a.division === d)
        .map(({ body, ...meta }) => meta);
    } else {
      results = all.map(({ body, ...meta }) => meta);
    }

    if (results.length === 0) {
      return {
        content: [
          {
            type: "text",
            text: division
              ? `No agents found in division "${division}". Use list_agents without a division to see all available divisions.`
              : "No agents found. Check that AGENCY_AGENTS_PATH points to the repo root.",
          },
        ],
      };
    }

    const grouped = division
      ? { [division]: results }
      : getAgentsByDivision(all);

    const lines: string[] = [`# Agency Agents (${results.length} total)\n`];

    for (const [div, divAgents] of Object.entries(grouped)) {
      lines.push(`## ${div} (${divAgents.length})`);
      for (const a of divAgents) {
        lines.push(`- ${a.emoji} **${a.name}** — ${a.description}`);
      }
      lines.push("");
    }

    return { content: [{ type: "text", text: lines.join("\n") }] };
  },
);

// ---------------------------------------------------------------------------
// Tool: get_agent
// ---------------------------------------------------------------------------
server.tool(
  "get_agent",
  "Get the full prompt content for a specific agent by slug or name. Returns the complete agent personality file including identity, mission, workflows, deliverables, and success metrics. Use this to activate an agent.",
  {
    agent: z
      .string()
      .describe(
        'Agent slug (e.g. "engineering-frontend-developer") or display name (e.g. "Frontend Developer")',
      ),
  },
  async ({ agent }) => {
    const all = await ensureLoaded();
    const q = agent.toLowerCase();

    const match = all.find(
      (a) => a.slug.toLowerCase() === q || a.name.toLowerCase() === q,
    );

    if (!match) {
      const suggestions = searchAgents(all, agent);
      const hint =
        suggestions.length > 0
          ? `\n\nDid you mean:\n${suggestions
              .slice(0, 5)
              .map((s) => `- ${s.emoji} ${s.name} (${s.slug})`)
              .join("\n")}`
          : "";
      return {
        content: [
          {
            type: "text",
            text: `Agent "${agent}" not found.${hint}`,
          },
        ],
        isError: true,
      };
    }

    const header = [
      `# ${match.emoji} ${match.name}`,
      `**Division**: ${match.division}`,
      `**Slug**: ${match.slug}`,
      match.vibe ? `**Vibe**: ${match.vibe}` : "",
      match.services
        ? `**Services**: ${match.services.map((s) => `${s.name} (${s.tier})`).join(", ")}`
        : "",
      `**File**: ${match.filePath}`,
      "",
      "---",
      "",
    ]
      .filter(Boolean)
      .join("\n");

    return {
      content: [{ type: "text", text: header + match.body }],
    };
  },
);

// ---------------------------------------------------------------------------
// Tool: search_agents
// ---------------------------------------------------------------------------
server.tool(
  "search_agents",
  "Search for agents by keyword across name, description, division, and vibe. Use this when you need to find the right specialist for a task but don't know the exact agent name.",
  {
    query: z
      .string()
      .describe(
        'Search query — matches against agent name, description, division, and vibe (e.g. "React performance", "security audit", "brand identity")',
      ),
    division: z
      .string()
      .optional()
      .describe("Narrow search to a specific division"),
  },
  async ({ query, division }) => {
    const all = await ensureLoaded();
    const results = searchAgents(all, query, division);

    if (results.length === 0) {
      return {
        content: [
          {
            type: "text",
            text: `No agents matched "${query}"${division ? ` in division "${division}"` : ""}. Try broader terms or list_agents to browse.`,
          },
        ],
      };
    }

    const lines = [
      `# Search results for "${query}" (${results.length} matches)\n`,
    ];
    for (const a of results) {
      lines.push(
        `- ${a.emoji} **${a.name}** [${a.division}] — ${a.description}`,
      );
      if (a.vibe) lines.push(`  _${a.vibe}_`);
    }

    return { content: [{ type: "text", text: lines.join("\n") }] };
  },
);

// ---------------------------------------------------------------------------
// Tool: compose_team
// ---------------------------------------------------------------------------
server.tool(
  "compose_team",
  "Assemble a team of agents for a specific project or task. Describe what you're building and get a recommended team with roles and rationale. Returns agent slugs you can pass to get_agent.",
  {
    objective: z
      .string()
      .describe(
        'What you are building or trying to accomplish (e.g. "SaaS MVP with React frontend and Node API", "marketing campaign for B2B product launch")',
      ),
    max_agents: z
      .number()
      .min(2)
      .max(12)
      .default(5)
      .describe("Maximum number of agents to recommend (2–12)"),
  },
  async ({ objective, max_agents }) => {
    const all = await ensureLoaded();
    const obj = objective.toLowerCase();

    const scored = all.map((a) => {
      const { body, ...meta } = a;
      const haystack =
        `${a.name} ${a.description} ${a.division} ${a.vibe} ${a.body}`.toLowerCase();
      const words = obj.split(/\s+/).filter((w) => w.length > 2);
      const hits = words.filter((w) => haystack.includes(w)).length;
      const divisionBoost = obj.includes(a.division) ? 2 : 0;
      return { meta, score: hits + divisionBoost };
    });

    scored.sort((a, b) => b.score - a.score);
    const team = scored.slice(0, max_agents).filter((s) => s.score > 0);

    if (team.length === 0) {
      return {
        content: [
          {
            type: "text",
            text: `Could not match agents to objective: "${objective}". Try rephrasing or use search_agents with specific keywords.`,
          },
        ],
      };
    }

    const lines = [
      `# Recommended Team for: ${objective}\n`,
      `**Team size**: ${team.length} agents\n`,
    ];

    for (let i = 0; i < team.length; i++) {
      const { meta, score } = team[i];
      lines.push(
        `### ${i + 1}. ${meta.emoji} ${meta.name}`,
        `- **Division**: ${meta.division}`,
        `- **Slug**: \`${meta.slug}\``,
        `- **Why**: ${meta.description}`,
        meta.vibe ? `- **Vibe**: ${meta.vibe}` : "",
        "",
      );
    }

    lines.push(
      "---",
      "Use `get_agent` with any slug above to load the full agent prompt.",
    );

    return {
      content: [{ type: "text", text: lines.filter(Boolean).join("\n") }],
    };
  },
);

// ---------------------------------------------------------------------------
// Tool: list_divisions
// ---------------------------------------------------------------------------
server.tool(
  "list_divisions",
  "List all agent divisions with agent counts. Use this to understand how the agency is organized before browsing agents.",
  {},
  async () => {
    const all = await ensureLoaded();
    const grouped = getAgentsByDivision(all);

    const lines = [`# Agency Divisions\n`];
    for (const [div, divAgents] of Object.entries(grouped).sort(
      (a, b) => b[1].length - a[1].length,
    )) {
      lines.push(`- **${div}**: ${divAgents.length} agents`);
    }
    lines.push(`\n**Total**: ${all.length} agents across ${Object.keys(grouped).length} divisions`);

    return { content: [{ type: "text", text: lines.join("\n") }] };
  },
);

// ---------------------------------------------------------------------------
// Resource: agent catalog
// ---------------------------------------------------------------------------
server.resource(
  "agent-catalog",
  "agency://catalog",
  async () => {
    const all = await ensureLoaded();
    const catalog = all.map(({ body, ...meta }) => meta);

    return {
      contents: [
        {
          uri: "agency://catalog",
          text: JSON.stringify(catalog, null, 2),
          mimeType: "application/json",
        },
      ],
    };
  },
);

// ---------------------------------------------------------------------------
// Resource: division summary
// ---------------------------------------------------------------------------
server.resource(
  "divisions",
  "agency://divisions",
  async () => {
    const all = await ensureLoaded();
    const grouped = getAgentsByDivision(all);
    const summary = Object.fromEntries(
      Object.entries(grouped).map(([div, agents]) => [
        div,
        { count: agents.length, agents: agents.map((a) => a.name) },
      ]),
    );

    return {
      contents: [
        {
          uri: "agency://divisions",
          text: JSON.stringify(summary, null, 2),
          mimeType: "application/json",
        },
      ],
    };
  },
);

// ---------------------------------------------------------------------------
// Start
// ---------------------------------------------------------------------------
const transport = new StdioServerTransport();
await server.connect(transport);
