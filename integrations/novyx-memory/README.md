# Novyx Memory Integration

> Give any agent persistent memory across sessions. Agents remember what they've done, share context during handoffs, and roll back when things go wrong.

## What It Does

By default, agents in The Agency start every session from scratch. Context is passed manually via copy-paste between agents and sessions. Novyx Memory changes that:

- **Cross-session memory**: An agent remembers decisions, deliverables, and context from previous sessions
- **Handoff continuity**: When one agent hands off to another, the receiving agent can recall exactly what was done — no copy-paste required
- **Rollback on failure**: When a QA check fails or an architecture decision turns out wrong, roll back to a known-good state instead of starting over
- **Offline-first**: Uses a local SQLite database by default. No API key, no network, no configuration.

## Setup

### Local Mode (recommended to start)

```bash
pip install novyx-mcp
```

That's it. `novyx-mcp` stores memories locally in `~/.novyx/local.db`. No account, no API key, no network required.

### Cloud Mode (for teams and persistence across machines)

Set a Novyx API key to sync memories to the cloud:

```bash
export NOVYX_API_KEY="nram_your_key_here"
```

Get a free key at [novyxlabs.com](https://novyxlabs.com). The free tier works for individual use. Paid tiers add higher limits, audit trails, and team sharing.

### Configure Your MCP Client

Add `novyx-mcp` to your MCP client config (Claude Code, Cursor, etc.):

```json
{
  "mcpServers": {
    "novyx-memory": {
      "command": "uvx",
      "args": ["novyx-mcp"]
    }
  }
}
```

## How to Add Memory to Any Agent

To enhance an existing agent with persistent memory, add a **Memory Integration** section to the agent's prompt. This section instructs the agent to use novyx-mcp tools at key moments.

### The Pattern

```markdown
## Memory Integration

When you start a session:
- Recall relevant context from previous sessions using your role and the current project as search terms
- Review any memories tagged with your agent name to pick up where you left off

When you make key decisions or complete deliverables:
- Remember the decision or deliverable with descriptive tags (your agent name, the project, the topic)
- Include enough context that a future session — or a different agent — can understand what was done and why

When handing off to another agent:
- Remember your deliverables tagged for the receiving agent
- Include the handoff metadata: what you completed, what's pending, and what the next agent needs to know

When something fails and you need to recover:
- Search for the last known-good state
- Use rollback to restore to that point rather than rebuilding from scratch
```

### What the Agent Does With This

The LLM will use `novyx-mcp` tools automatically when given these instructions:

- `nx.remember()` — store a decision, deliverable, or context snapshot with tags
- `nx.recall()` — search for relevant memories by keyword, tag, or semantic similarity
- `nx.rollback()` — revert to a previous state when something goes wrong
- `nx.search()` — find specific memories across sessions and agents

No code changes to the agent files. No API calls to write. The MCP tools handle everything.

## Example: Enhancing the Backend Architect

See [backend-architect-with-memory.md](backend-architect-with-memory.md) for a complete example — the standard Backend Architect agent with a Memory Integration section added.

## Example: Memory-Powered Workflow

See [../../examples/workflow-with-memory.md](../../examples/workflow-with-memory.md) for the Startup MVP workflow enhanced with Novyx memory, showing how agents pass context through memory instead of copy-paste.

## Tips

- **Start local**: No reason to set up cloud until you need cross-machine sync or team sharing
- **Tag consistently**: Use the agent name and project name as tags on every memory. This makes recall reliable.
- **Let the LLM decide what's important**: The memory instructions are guidance, not rigid rules. The LLM will figure out when to remember and what to recall.
- **Rollback is the killer feature**: When a Reality Checker fails a deliverable, the original agent can roll back to its last checkpoint instead of trying to manually undo changes
