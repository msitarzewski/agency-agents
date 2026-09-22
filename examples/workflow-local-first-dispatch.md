# Multi-Agent Workflow: Local-First Dispatch

> A worked example of dispatching agency agents through a local OpenAI-compatible LLM runtime — Ollama, LM Studio, MLX, vLLM, etc. — at $0 inference cost. Same agent files, no API tokens spent, your data never leaves the machine.

## The Scenario

You're building a small SaaS side project. You want to use the agency agents in this repo for advisory + content + light coding work. Hosted Claude / GPT would burn ~$15-30/month for the dispatch volume you have in mind. You'd rather pay zero and keep the prompts local.

This workflow shows how to do that with the [`local-first-dispatcher`](local-first-dispatcher/) reference implementation.

## Agent Team

| Agent | Role in this workflow |
|-------|---------------------|
| Backend Architect | Design the API + data model |
| Frontend Developer | Sketch the UI architecture |
| Content Creator | Draft launch copy |
| Reality Checker | Gate each output before moving on |

## The Workflow

### Step 1 — Stand up a local runtime

Pick the runtime that fits your hardware. For most laptops, [Ollama](local-first-dispatcher/runtimes/ollama.md) with `llama3.1:8b` is the easy default:

```bash
ollama serve                     # background
ollama pull llama3.1:8b
```

Verify it answers:

```bash
curl http://127.0.0.1:11434/v1/models | head
```

### Step 2 — Set defaults

```bash
export AGENCY_BASE_URL=http://127.0.0.1:11434/v1
export AGENCY_MODEL=llama3.1:8b
```

Now every dispatch call uses these defaults — no flag needed.

### Step 3 — Dispatch the Backend Architect

```bash
cd examples/local-first-dispatcher
node dispatcher.js \
  --agent ../../engineering/backend-architect \
  --task "$(cat <<'EOF'
Project: TaskBoard — a Trello-style kanban for personal projects.
Stack: Node 20 + Postgres 16, single-region.
Users: solo at first, will support team sharing in v2.

Design the data model (3-5 tables) and the core API endpoints.
Use Postgres-native features where they fit. Be specific.
EOF
)" > arch.md
```

`arch.md` now contains the agent's response — verbatim, $0, ~10-30 seconds depending on hardware.

### Step 4 — Hand off to the Frontend Developer

```bash
node dispatcher.js \
  --agent ../../engineering/frontend-developer \
  --task "$(cat <<EOF
Given this backend design:

$(cat arch.md)

Sketch the React component tree for v1 (solo user only).
Name the components, describe state ownership, and pick one routing
approach (RR vs Next vs TanStack Router) with reasoning.
EOF
)" > ui.md
```

Each agent dispatch is independent and stateless — you compose them by passing one agent's output into the next agent's task.

### Step 5 — Dispatch the Content Creator for launch copy

```bash
node dispatcher.js \
  --agent ../../marketing/content-creator \
  --task "$(cat <<'EOF'
Project: TaskBoard, a self-hosted Trello-alternative for personal projects.

Write 3 versions of a launch tweet — under 280 chars each.
Tone: builder-to-builder, not marketing-to-buyer.
Anchor each version on a different angle: privacy, simplicity, self-hosting.
EOF
)" > tweets.md
```

### Step 6 — Reality Checker before you ship

```bash
node dispatcher.js \
  --agent ../../specialized/reality-checker \
  --task "$(cat <<EOF
Review this artifact set for our SaaS launch:

ARCHITECTURE:
$(cat arch.md)

UI SKETCH:
$(cat ui.md)

LAUNCH TWEETS:
$(cat tweets.md)

What contradicts? What's missing? What would a senior dev call out as
careless? Be specific. If it's all solid, say so plainly.
EOF
)"
```

The reality-checker is intentionally adversarial — its job is to flag holes before users find them.

## Programmatic version

If you'd rather chain the workflow in code:

```js
import { loadAgent, dispatchAgent } from './examples/local-first-dispatcher/dispatcher.js';

const arch = await dispatchAgent({
  agent: loadAgent('engineering/backend-architect'),
  task: 'Project: TaskBoard...',
});

const ui = await dispatchAgent({
  agent: loadAgent('engineering/frontend-developer'),
  task: `Given this backend design:\n${arch.content}\n\nSketch the React component tree...`,
});

const tweets = await dispatchAgent({
  agent: loadAgent('marketing/content-creator'),
  task: 'Write 3 launch tweets for TaskBoard...',
});

const review = await dispatchAgent({
  agent: loadAgent('specialized/reality-checker'),
  task: `Review:\n\nARCH:\n${arch.content}\n\nUI:\n${ui.content}\n\nTWEETS:\n${tweets.content}\n\n...`,
});

console.log(review.content);
```

Total cost: $0. Total wall time: ~1-2 minutes on a 16 GB Mac running an 8B model.

## When to NOT use local-first

- Tasks that genuinely need frontier reasoning (PhD-level math, complex multi-file refactors of unfamiliar code, deep adversarial security analysis). A 7-30B local model **will** be weaker than Claude Opus or GPT-4 here.
- Latency-critical production with no GPU/spare RAM budget.
- When you specifically want a third-party model card to cite for compliance.

For the other ~80% of agent dispatches in this repo (advisory, content, marketing, code review, light coding, scoping, prioritization), local-first is indistinguishable in output quality from frontier-API and free.

## Reflexion lift for harder tasks

If a task lands somewhere in the middle — local model gives "fine but thin" output — wrap the dispatch in a 3-pass self-critique loop:

```js
import { loadAgent, dispatchAgent } from './examples/local-first-dispatcher/dispatcher.js';

async function dispatchReflexive({ agent, task, opts = {} }) {
  const r1 = await dispatchAgent({ agent, task, ...opts });
  const critique = await dispatchAgent({
    agent, ...opts,
    temperature: (opts.temperature ?? 0.3) + 0.2,
    task: `Review this response. List concrete weaknesses + improvements. Don't rewrite.\n\nTASK: ${task}\n\nRESPONSE: ${r1.content}`,
  });
  return dispatchAgent({
    agent, ...opts,
    task: `Re-answer. Address every weakness. Output ONLY the improved answer.\n\nTASK: ${task}\n\nDRAFT: ${r1.content}\n\nCRITIQUE: ${critique.content}`,
  });
}
```

3× cost, $0. Closes most of the gap to frontier on the harder middle-tier tasks.

## What you've built

By the end of this workflow:

- 4 agent dispatches, 4 markdown artifacts
- 0 dollars spent on inference
- 0 prompts left a server you don't control
- A workflow you can re-run on any project, any runtime, any model

That's local-first.
