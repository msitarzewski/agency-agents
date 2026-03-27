# MCP Server Integration

> Query, search, and compose teams from The Agency's 160+ AI specialist agents via the Model Context Protocol.

## What It Does

Turns the static agent markdown files into a live, queryable agent registry that any MCP-compatible client (Cursor, Claude Code, Claude Desktop, etc.) can use dynamically.

**Tools:**

| Tool | Description |
|------|-------------|
| `list_agents` | Browse all agents, optionally filtered by division |
| `get_agent` | Load the full agent prompt by slug or name |
| `search_agents` | Find the right specialist by keyword |
| `compose_team` | Assemble a recommended team for a project objective |
| `list_divisions` | See all divisions with agent counts |

**Resources:**

| URI | Description |
|-----|-------------|
| `agency://catalog` | Full agent catalog as JSON |
| `agency://divisions` | Division summary with agent counts and names |

## Prerequisites

- [Bun](https://bun.sh) v1.0+

## Install

```bash
cd integrations/mcp-server
bun install
```

## Configure

Add to your MCP client configuration:

### Cursor (`~/.cursor/mcp.json`)

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

## Usage

Once configured, use the tools from any MCP client:

```
Search for agents that can help with React performance optimization.
```

```
Compose a team of 5 agents for building a SaaS MVP with a React frontend and Node API.
```

```
Get the full prompt for the Security Engineer agent.
```

```
List all agents in the engineering division.
```

## Development

```bash
bun run dev     # watch mode
bun run start   # single run
```
