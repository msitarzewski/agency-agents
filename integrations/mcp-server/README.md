# MCP Server Integration

> Query, search, and compose teams from The Agency's 160+ AI specialist agents via the Model Context Protocol.

## What It Does

Turns the static agent markdown files into a live, queryable agent registry that any MCP-compatible client (Cursor, Claude Code, Claude Desktop, etc.) can use dynamically — no shell scripts, no file copying.

## Tools

| Tool | Description |
|------|-------------|
| `list_agents` | Browse all agents, optionally filtered by division |
| `get_agent` | Load the full agent prompt by slug or name |
| `search_agents` | Find the right specialist by keyword |
| `compose_team` | Assemble a recommended team for a project objective |
| `list_divisions` | See all divisions with agent counts |

## Resources

| URI | Description |
|-----|-------------|
| `agency://catalog` | Full agent catalog as JSON |
| `agency://divisions` | Division summary with agent counts and names |

## Prerequisites

One of the following runtimes:

- [Bun](https://bun.sh) v1.0+ (recommended)
- [Node.js](https://nodejs.org) v18+ with `tsx` (`npm install -g tsx`)

## Install

```bash
cd integrations/mcp-server
bun install
```

## Configure

Add to your MCP client configuration.

### Cursor (`~/.cursor/mcp.json`)

**With Bun:**
```json
{
  "mcpServers": {
    "agency-agents": {
      "command": "bun",
      "args": ["run", "/absolute/path/to/agency-agents/integrations/mcp-server/src/index.ts"]
    }
  }
}
```

**With Node.js:**
```json
{
  "mcpServers": {
    "agency-agents": {
      "command": "npx",
      "args": ["tsx", "/absolute/path/to/agency-agents/integrations/mcp-server/src/index.ts"]
    }
  }
}
```

### Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "agency-agents": {
      "command": "bun",
      "args": ["run", "/absolute/path/to/agency-agents/integrations/mcp-server/src/index.ts"]
    }
  }
}
```

### Custom repo path

If the server can't auto-detect the repo root, set `AGENCY_AGENTS_PATH`:

```json
{
  "mcpServers": {
    "agency-agents": {
      "command": "bun",
      "args": ["run", "/path/to/integrations/mcp-server/src/index.ts"],
      "env": {
        "AGENCY_AGENTS_PATH": "/absolute/path/to/agency-agents"
      }
    }
  }
}
```

## Usage Examples

Once configured, use natural language from any MCP client. The AI will call the right tool automatically.

### Search for a specialist

**You say:**
```
Search for agents that can help with API security.
```

**Tool returns:**
```
# Search results for "API security" (2 matches)

- ⚡ Autonomous Optimization Architect [engineering] — Intelligent system governor
  that continuously shadow-tests APIs for performance while enforcing strict financial
  and security guardrails.
- 🔒 Security Engineer [engineering] — Expert application security engineer
  specializing in threat modeling, vulnerability assessment, secure code review,
  security architecture design, and incident response for modern web, API, and
  cloud-native applications.
```

### Compose a team

**You say:**
```
Compose a team for building a SaaS MVP with React frontend and Node API.
```

**Tool returns:**
```
# Recommended Team for: SaaS MVP with React frontend and Node API

**Team size**: 4 agents

### 1. ⚡ Rapid Prototyper
- Division: engineering
- Slug: engineering-rapid-prototyper
- Why: Specialized in ultra-fast proof-of-concept development and MVP creation

### 2. 🗺️ Workflow Architect
- Division: specialized
- Slug: specialized-workflow-architect
- Why: Maps complete workflow trees before a single line is written

### 3. 🎛️ Agents Orchestrator
- Division: specialized
- Slug: agents-orchestrator
- Why: Autonomous pipeline manager that orchestrates the entire dev workflow

### 4. 🖥️ Frontend Developer
- Division: engineering
- Slug: engineering-frontend-developer
- Why: Modern web technologies, React/Vue/Angular, UI implementation

---
Use get_agent with any slug above to load the full agent prompt.
```

### Load an agent

**You say:**
```
Get the full prompt for the Security Engineer agent.
```

**Tool returns the complete agent personality file** — identity, mission, workflows, deliverables, success metrics — ready to activate.

### Browse by division

**You say:**
```
List all agents in the engineering division.
```

**Tool returns all 26 engineering agents** with names, emojis, and descriptions.

## Development

```bash
bun run dev     # watch mode
bun run start   # single run
```
