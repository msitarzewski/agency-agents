# 🔌 @agency-agents/mcp-server

Official **Model Context Protocol (MCP)** Server for **The Agency** (`msitarzewski/agency-agents`).

Transform the 230+ AI specialist roster into a dynamic, zero-footprint runtime service for any MCP host (Claude Code, Cursor, Antigravity, OpenCode, Zed, Claude Desktop, etc.).

---

## ⚡ Features

* **Zero Footprint**: No need to manually copy hundreds of `.md`/`.toml`/`.mdc` files into local configuration folders.
* **On-Demand Discovery**: Query agent personas dynamically by keyword, role, or task domain.
* **Always in Sync**: Reads directly from `divisions.json` and agent Markdown files in the root repository.
* **5 Key Tools**:
  * `list_divisions`: Returns all 17 active divisions and metadata.
  * `list_agents`: Returns agent summaries (optionally filtered by division).
  * `search_agents`: Performs keyword/relevance match across agent capabilities.
  * `get_agent`: Fetches complete persona instructions, critical rules, workflow, and code deliverables.
  * `route_task`: Recommends optimal agent specialist teams for complex task prompts.
* **Dynamic Resources**:
  * `agency://divisions`
  * `agency://agents/{division}/{slug}`

---

## 🚀 Quick Start & Installation

### Option 1: Direct Execution (Node.js / npx)

Build the server once or run directly from source:

```bash
cd integrations/mcp-server
npm install
npm run build
```

### Option 2: Integration with Claude Desktop / Claude Code

Add the following entry to your `mcpServers` configuration (e.g. `claude_desktop_config.json` or `~/.claude/mcp.json`):

```json
{
  "mcpServers": {
    "agency-agents": {
      "command": "node",
      "args": [
        "/path/to/agency-agents/integrations/mcp-server/dist/index.js"
      ],
      "env": {
        "AGENCY_AGENTS_ROOT": "/path/to/agency-agents"
      }
    }
  }
}
```

### Option 3: Integration with Cursor / Antigravity / Zed

In your tool's MCP settings, add a Stdio server command:

* **Command**: `node`
* **Args**: `/path/to/agency-agents/integrations/mcp-server/dist/index.js`
* **Env**: `AGENCY_AGENTS_ROOT=/path/to/agency-agents`

---

## 🛠️ Provided MCP Tools

### 1. `list_divisions`
Returns all 17 divisions (`engineering`, `design`, `security`, `marketing`, etc.) with labels, icons, colors, and total count of specialists.

### 2. `list_agents`
Lists all available agent specialists, with an optional `division` argument to filter results.

### 3. `search_agents`
Searches agents by query string.
```json
{
  "query": "PostgreSQL query tuning",
  "limit": 5
}
```

### 4. `get_agent`
Retrieves full markdown persona prompt for a given agent.
```json
{
  "identifier": "engineering-frontend-developer"
}
```

### 5. `route_task`
Analyzes a complex task prompt and returns recommended agent teams with match scores and rationales.
```json
{
  "task": "Build a secure React frontend with WebAssembly crypto and WCAG accessibility"
}
```

---

## 📄 License
MIT License. Part of [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents).
