# Nexus Orchestrator Integration

> Route agency-agent tasks to local LLMs (LM Studio / Ollama) via [nexus-orchestrator](https://github.com/el-j/nexus-orchestrator).

## What It Does

[nexus-orchestrator](https://github.com/el-j/nexus-orchestrator) is a local AI daemon that:

- Routes code-generation tasks to **LM Studio** (`:1234`) or **Ollama** (`:11434`) automatically
- Keeps **per-project session memory** in SQLite so each project has its own conversation history
- Exposes an **HTTP API** (`http://localhost:9999`) and **MCP server** (`http://localhost:9998/mcp`)

The agency-agents package provides the *who* (agent personalities and system prompts).  
nexus-orchestrator provides the *how* (LLM routing, session isolation, task queuing).

Together they give you automatic, consistent orchestration: pick your agents, submit a task — nexus-orchestrator routes it to the best available local LLM.

---

## Prerequisites

1. Install and start the nexus-orchestrator daemon:
   ```bash
   CGO_ENABLED=1 go build -o /usr/local/bin/nexus-daemon ./cmd/nexus-daemon
   nexus-daemon
   # MCP server:  http://localhost:9998/mcp
   # HTTP API:    http://localhost:9999
   ```

2. Have either **LM Studio** running at `http://127.0.0.1:1234/v1` **or** **Ollama** at `http://127.0.0.1:11434`.

---

## TypeScript / Node.js

```bash
npm install agency-agents
```

```typescript
import { getAgent, buildSwarm, listAgents } from 'agency-agents';
import {
  NexusOrchestratorClient,
  agentTaskInstruction,
  swarmTaskInstruction,
} from 'agency-agents/nexus';

const nexus = new NexusOrchestratorClient();
// Optional: use a remote daemon
// const nexus = new NexusOrchestratorClient({ mcpUrl: 'http://myhost:9998/mcp' });

// ── Single-agent task ──────────────────────────────────────────────────────
const agent = getAgent('frontend-developer')!;

const task = await nexus.submitTask({
  projectPath: '/my/project',
  targetFile:  'src/App.tsx',
  instruction: agentTaskInstruction(agent, 'Add a dark-mode toggle using Tailwind'),
});
console.log('Submitted:', task.id, task.status);

// Poll for completion
let result = await nexus.getTask(task.id);
while (result.status === 'queued' || result.status === 'in_progress') {
  await new Promise(r => setTimeout(r, 1000));
  result = await nexus.getTask(task.id);
}
console.log('Output:', result.output);

// ── Swarm task ─────────────────────────────────────────────────────────────
const swarm = buildSwarm(
  [getAgent('frontend-developer')!, getAgent('backend-architect')!],
  { name: 'MVP Team', mission: 'Ship v1 in 4 weeks' },
);

const swarmTask = await nexus.submitTask({
  projectPath: '/my/project',
  targetFile:  'ARCHITECTURE.md',
  instruction: swarmTaskInstruction(swarm, 'Design the initial system architecture'),
});
console.log('Swarm task:', swarmTask.id);
```

### API reference

| Export | Description |
|--------|-------------|
| `NexusOrchestratorClient` | MCP client for the nexus-orchestrator daemon |
| `agentTaskInstruction(agent, request?)` | Build a self-contained instruction from an agent + optional request |
| `swarmTaskInstruction(swarm, request?)` | Build an instruction from a swarm orchestrator prompt + optional request |
| `NexusTask` | Task shape accepted by `submitTask` |
| `NexusTaskResult` | Result / status shape returned by `getTask` |
| `NexusOrchestratorOptions` | Options for `NexusOrchestratorClient` |

All of the above are exported from the separate `agency-agents/nexus` subpath and are **not** included in the main `agency-agents` bundle.

#### `NexusOrchestratorClient` methods

| Method | Description |
|--------|-------------|
| `submitTask(task)` | Submit a new task; returns the created `NexusTaskResult` |
| `getTask(id)` | Poll a task by ID |
| `getQueue()` | List all pending / active tasks |
| `cancelTask(id)` | Cancel a queued task |
| `checkHealth()` | Returns `true` when the daemon is reachable |

---

## GitHub Action

Add the optional `nexus_url` input to your workflow to have the action submit the resolved system prompt directly to a nexus-orchestrator daemon:

```yaml
# .github/workflows/ai-task.yml
jobs:
  ai-task:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Load agent and submit to nexus-orchestrator
        id: agent
        uses: msitarzewski/agency-agents@main
        with:
          agent: backend-architect
          nexus_url: 'http://my-nexus-host:9998/mcp'
          nexus_project_path: ${{ github.workspace }}
          nexus_target_file: 'src/server.ts'
          nexus_request: 'Add rate-limiting middleware'

      - name: Show nexus task ID
        run: echo "Task ID: ${{ steps.agent.outputs.nexus_task_id }}"
```

---

## MCP Server (Claude Desktop / any MCP client)

Point any MCP client at the nexus-orchestrator MCP endpoint and use the `submit_task` tool directly, passing an agency-agents system prompt as the `instruction`:

```json
{
  "mcpServers": {
    "nexusOrchestrator": {
      "url": "http://localhost:9998/mcp"
    }
  }
}
```

Then in your MCP client:

```
tools/call submit_task {
  "projectPath": "/my/project",
  "targetFile": "src/api.ts",
  "instruction": "<paste agency-agent system prompt here>"
}
```

Or use `npx agency-agents get backend-architect --prompt` to retrieve the system prompt and pipe it into the nexus-submit CLI.

---

## Health Check

```typescript
import { NexusOrchestratorClient } from 'agency-agents/nexus';

const nexus = new NexusOrchestratorClient();
if (await nexus.checkHealth()) {
  console.log('nexus-orchestrator is running');
} else {
  console.warn('nexus-orchestrator is not reachable — falling back to direct LLM call');
}
```
