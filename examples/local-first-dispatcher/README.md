# Local-First Dispatcher

Run any agent in this repo against a **local OpenAI-compatible LLM runtime** (Ollama, LM Studio, llama.cpp, vLLM, Apple MLX, Jan, …) at **$0 inference cost**.

> **TL;DR** — The agent `.md` files in this repo are designed to be loaded as system prompts. Pasting them into a hosted Claude / GPT chat works, but it costs API tokens per dispatch and pins your agent work to a vendor. This dispatcher reads the same files locally, sends them as the `system` message to a local OpenAI-compatible `/v1/chat/completions` endpoint, and streams back the assistant reply. Same agents. $0. Your data never leaves the machine.

---

## Why local-first?

| Concern | Hosted-API agents | Local-first dispatch |
| --- | --- | --- |
| Per-call cost | Real money (tokens × price) | $0 (electricity only) |
| Privacy | Prompts + replies leave the machine | Stays local |
| Outage resilience | Vendor down → agents down | Local runtime up → agents up |
| Multi-vendor | Single vendor lock-in | Any OpenAI-compatible runtime |
| Iteration speed | Network round-trip per turn | Loopback latency |
| Quality ceiling | Frontier models | Bounded by your local model |

The honest tradeoff: a local 7-30B model **will** be weaker than Claude Opus / GPT-4 on the hardest tasks. For ~80% of agent dispatches (advisory, content, marketing, code review, light reasoning) a modern local model produces work indistinguishable from frontier output. Save the frontier APIs for the 20% that actually need them.

---

## Quick start (Ollama, 90 seconds)

```bash
# 1. Install + start Ollama (https://ollama.com)
ollama serve   # background; or run in another terminal
ollama pull llama3.1:8b

# 2. Dispatch an agent — no install, just node + this file
cd examples/local-first-dispatcher
node dispatcher.js \
  --agent ../../engineering/backend-architect \
  --task "Outline a sharded Postgres schema for a multi-tenant SaaS"
```

Done. The agent's full system prompt is loaded from `engineering/backend-architect.md`, sent to Ollama at `http://127.0.0.1:11434/v1/chat/completions`, and the reply prints to stdout.

Python alternative:

```bash
python3 dispatcher.py \
  --agent ../../engineering/backend-architect \
  --task "Outline a sharded Postgres schema for a multi-tenant SaaS"
```

Stdlib only — no `pip install` step.

---

## Supported runtimes

Any OpenAI-compatible `/v1/chat/completions` endpoint will work. We've verified these:

| Runtime | Default URL | Setup guide |
| --- | --- | --- |
| **Ollama** | `http://127.0.0.1:11434/v1` | [runtimes/ollama.md](runtimes/ollama.md) |
| **LM Studio** | `http://127.0.0.1:1234/v1` | [runtimes/lmstudio.md](runtimes/lmstudio.md) |
| **Apple MLX** (`mlx_lm.server` / `mlx_vlm.server`) | `http://127.0.0.1:8080/v1` | [runtimes/mlx.md](runtimes/mlx.md) |
| **vLLM** | `http://127.0.0.1:8000/v1` | [runtimes/vllm.md](runtimes/vllm.md) |
| **llama.cpp server** | `http://127.0.0.1:8080/v1` | configure with `--port` and use the same flags |
| **Jan / Local AI / OpenLLM** | varies | any OpenAI-compatible URL works |

Pick a runtime that fits your hardware. On a 16 GB Mac, Ollama with `llama3.1:8b` is the easy default. On a 64 GB+ workstation, MLX or vLLM with a 30-70B model approaches frontier quality on most agency tasks.

---

## CLI usage

```text
dispatcher.js — Local-First Dispatcher for Agency Agents

Required:
  --agent PATH         Path to agent .md file (or directory containing one)
  --task TEXT          The task to send the agent

Optional:
  --base-url URL       OpenAI-compatible base URL
                       (default: $AGENCY_BASE_URL or Ollama on :11434)
  --model NAME         Model identifier
                       (default: $AGENCY_MODEL or "llama3.1:8b")
  --temperature FLOAT  Sampling temperature (default: 0.3)
  --max-tokens INT     Cap on response tokens (default: 2048)
  --json               Output the full response payload as JSON
  --list DIR           List agent files under DIR (no dispatch)
  --help, -h           Show this message

Environment:
  AGENCY_BASE_URL      Default base URL
  AGENCY_MODEL         Default model
  AGENCY_API_KEY       Optional bearer (some runtimes ignore)
```

The Python CLI takes the same flags.

---

## Programmatic use

### Node.js

```js
import { loadAgent, dispatchAgent } from './dispatcher.js';

const agent = loadAgent('../../engineering/backend-architect');
const result = await dispatchAgent({
  agent,
  task: 'Sketch a CDN cache invalidation strategy for a global SaaS',
  baseUrl: 'http://127.0.0.1:11434/v1',
  model: 'llama3.1:8b',
  temperature: 0.3,
});

console.log(result.content);
```

### Python

```python
from dispatcher import load_agent, dispatch_agent

agent = load_agent("../../engineering/backend-architect")
result = dispatch_agent(
    agent=agent,
    task="Sketch a CDN cache invalidation strategy for a global SaaS",
    base_url="http://127.0.0.1:11434/v1",
    model="llama3.1:8b",
    temperature=0.3,
)
print(result["content"])
```

Both return the same shape:

```json
{
  "ok": true,
  "agent": "Backend Architect",
  "content": "<assistant reply>",
  "finish_reason": "stop",
  "model": "llama3.1:8b",
  "usage": { "prompt_tokens": 8420, "completion_tokens": 612, "total_tokens": 9032 },
  "latency_ms": 11200
}
```

On failure `ok` is `false` and you get `error` (a stable code) plus an optional `detail`.

---

## Discovering agents

```bash
# List all agents in a category
node dispatcher.js --list ../../engineering

# Or walk the whole repo
for d in ../../*/; do
  echo "=== $(basename $d) ==="
  node dispatcher.js --list "$d" 2>/dev/null
done
```

---

## Common patterns

### Pattern 1 — Routing by intent

```js
const ROUTES = {
  schema:    '../../engineering/backend-architect',
  copy:      '../../marketing/content-creator',
  bug:       '../../engineering/code-reviewer',
  research:  '../../product/trend-researcher',
};

async function smartDispatch(intent, task) {
  const agent = loadAgent(ROUTES[intent] || ROUTES.research);
  return dispatchAgent({ agent, task });
}
```

### Pattern 2 — Reflexion (3-pass self-critique loop)

```js
async function dispatchReflexive({ agent, task, opts = {} }) {
  // Pass 1 — first answer
  const r1 = await dispatchAgent({ agent, task, ...opts });
  if (!r1.ok) return r1;

  // Pass 2 — agent critiques its own draft
  const critique = await dispatchAgent({
    agent, ...opts,
    temperature: (opts.temperature ?? 0.3) + 0.2,
    task: [
      'Review your prior response. List concrete weaknesses + the specific',
      'improvement each needs. Do NOT rewrite. Output a numbered list.',
      '', '--- ORIGINAL TASK ---', task,
      '', '--- RESPONSE TO REVIEW ---', r1.content,
    ].join('\n'),
  });
  if (!critique.ok) return critique;

  // Pass 3 — re-answer incorporating the critique
  return dispatchAgent({
    agent, ...opts,
    task: [
      'Re-answer the original task, addressing every concrete weakness.',
      'Output ONLY the improved final answer — no meta commentary.',
      '', '--- ORIGINAL TASK ---', task,
      '', '--- YOUR FIRST DRAFT ---', r1.content,
      '', '--- CRITIQUE NOTES ---', critique.content,
    ].join('\n'),
  });
}
```

3× cost, $0. Closes most of the gap between a 7B local model and Opus on hard tasks.

### Pattern 3 — Multi-agent workflow

```js
const sprint = await dispatchAgent({
  agent: loadAgent('../../project-management/sprint-prioritizer'),
  task: 'Break this MVP into 4 weekly sprints: <project brief>',
});

const arch = await dispatchAgent({
  agent: loadAgent('../../engineering/backend-architect'),
  task: `Given this sprint plan, design the API + data model:\n${sprint.content}`,
});

const ui = await dispatchAgent({
  agent: loadAgent('../../engineering/frontend-developer'),
  task: `Build a React component for sprint 1 deliverable: ${sprint.content}`,
});
```

See [`../workflow-local-first-dispatch.md`](../workflow-local-first-dispatch.md) for a worked example.

---

## Tests

```bash
# Smoke tests for the loader (no LLM call required)
node test/loader.test.js
python3 test/test_loader.py

# Live dispatch test (requires a runtime up at $AGENCY_BASE_URL)
node test/dispatch.test.js
python3 test/test_dispatch.py
```

The loader tests are deterministic — they exercise frontmatter parsing, slug
resolution, and error paths against fixture files in `test/fixtures/`. The
dispatch tests will skip cleanly if no runtime is reachable.

---

## Performance notes

- **Cold start** — first dispatch after the runtime boots pays a model-load cost (5-30s on Apple MLX, 1-5s on Ollama). Subsequent dispatches are warm.
- **Concurrency** — most local runtimes serialize requests. If you need parallel agent dispatches, run multiple model processes on different ports OR use a runtime that supports batching (vLLM, Ollama with `OLLAMA_NUM_PARALLEL`).
- **System prompt size** — the agent files in this repo are 8-15 KB. Most local runtimes prefill that in 1-3 seconds; subsequent turns are fast.

---

## License

MIT — same as the parent repo.

## Acknowledgments

Pattern shipped to production at [EDHAT Studios](https://edhat.studio) where 254 agency-prefix and native agents are dispatched daily through this exact flow. ~$0 monthly inference cost across the entire agent layer.
