# MCP Memory Integration

> Give any agent persistent memory across sessions using the Model Context Protocol (MCP).

## What It Does

By default, agents in The Agency start every session from scratch. Context is passed manually via copy-paste between agents and sessions. An MCP memory server changes that:

- **Cross-session memory**: An agent remembers decisions, deliverables, and context from previous sessions
- **Handoff continuity**: When one agent hands off to another, the receiving agent can recall exactly what was done — no copy-paste required
- **Rollback on failure**: When a QA check fails or an architecture decision turns out wrong, roll back to a known-good state instead of starting over

## Setup

You need an MCP server that provides memory tools: `remember`, `recall`, `rollback`, and `search`. Add it to your MCP client config (Claude Code, Cursor, etc.):

```json
{
  "mcpServers": {
    "memory": {
      "command": "your-mcp-memory-server",
      "args": []
    }
  }
}
```

Any MCP server that exposes `remember`, `recall`, `rollback`, and `search` tools will work. Check the [MCP ecosystem](https://modelcontextprotocol.io) for available implementations.

## How to Add Memory to Any Agent

To enhance an existing agent with persistent memory, add a **Memory Integration** section to the agent's prompt. This section instructs the agent to use MCP memory tools at key moments.

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

The LLM will use MCP memory tools automatically when given these instructions:

- `remember` — store a decision, deliverable, or context snapshot with tags
- `recall` — search for relevant memories by keyword, tag, or semantic similarity
- `rollback` — revert to a previous state when something goes wrong
- `search` — find specific memories across sessions and agents

No code changes to the agent files. No API calls to write. The MCP tools handle everything.

## Example: Enhancing the Backend Architect

See [backend-architect-with-memory.md](backend-architect-with-memory.md) for a complete example — the standard Backend Architect agent with a Memory Integration section added.

## Example: Memory-Powered Workflow

See [../../examples/workflow-with-memory.md](../../examples/workflow-with-memory.md) for the Startup MVP workflow enhanced with persistent memory, showing how agents pass context through memory instead of copy-paste.

## Tips

- **Tag consistently**: Use the agent name and project name as tags on every memory. This makes recall reliable.
- **Let the LLM decide what's important**: The memory instructions are guidance, not rigid rules. The LLM will figure out when to remember and what to recall.
- **Rollback is the killer feature**: When a Reality Checker fails a deliverable, the original agent can roll back to its last checkpoint instead of trying to manually undo changes.
