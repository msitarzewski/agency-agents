# DreamEngine NEXUS Pipeline

A LangGraph-powered multi-agent development pipeline that orchestrates all 150+ DreamEngine agent specs through a 7-phase NEXUS workflow.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Opus (Supervisor)                  │
│  Plans phases · Routes models · Gates quality               │
└──────────┬──────────────────────────────────┬───────────────┘
           │ plans & verdicts                 │
           ▼                                  ▼
┌──────────────────┐              ┌───────────────────────┐
│   LangGraph FSM  │              │   Ollama (Workers)    │
│                  │   tasks      │                       │
│  discover ─► gate├─────────────►│  qwen2.5:7b    (fast) │
│  strategize─►gate│              │  llama3.1:8b   (fast) │
│  scaffold ─► gate│◄─────────────│  deepseek-v2   (fast) │
│  build    ─► gate│   outputs    │  qwen2.5:32b   (med)  │
│  harden   ─► gate│              │  llama3.1:70b  (med)  │
│  launch   ─► gate│              │  mixtral:8x22b (heavy)│
│  operate  ─► gate│              └───────────────────────┘
│       │          │
│       ▼          │
│   END / HALT     │
└──────────────────┘
```

**Supervisor (Claude Opus)** decides:
- Which agents activate per phase
- What task each agent performs
- Which Ollama model handles each task (cheapest viable)
- Whether a phase passes the quality gate

**Workers (Ollama)** execute the actual work using the DreamEngine agent personas as system prompts.

## Model Tiers (cheapest first)

| Tier | Models | Used For |
|------|--------|----------|
| `free_fast` | qwen2.5:7b, llama3.1:8b, gemma2:9b, phi3:mini, deepseek-coder-v2:16b | Most tasks — code, content, planning |
| `free_medium` | qwen2.5:32b, llama3.1:70b | Complex architecture, deep analysis |
| `free_heavy` | deepseek-coder-v2:236b, mixtral:8x22b | Security audits, heavy reasoning |
| `paid_supervisor` | claude-opus-4-6 | Orchestration decisions only |

## Setup

```bash
# 1. Install dependencies
pip install -r pipeline/requirements.txt

# 2. Pull at least the fast-tier Ollama models
ollama pull qwen2.5:7b
ollama pull llama3.1:8b
ollama pull deepseek-coder-v2:16b

# 3. Set your Anthropic API key (for supervisor)
export ANTHROPIC_API_KEY=sk-ant-...

# 4. Verify Ollama is running
python -m pipeline --check-ollama
```

## Usage

```bash
# Run the full pipeline
python -m pipeline --brief "Build a SaaS task manager with auth, billing, and team features"

# Run specific phases only
python -m pipeline --brief "..." --phases discover,strategize

# Save results to JSON
python -m pipeline --brief "..." --output results.json

# Debug mode
python -m pipeline --brief "..." --verbose

# List all agents by phase
python -m pipeline --list-agents

# List configured models
python -m pipeline --list-models
```

## Pipeline Phases (NEXUS)

| # | Phase | Purpose | Key Agents |
|---|-------|---------|------------|
| 0 | **Discover** | Market/user/tech intelligence | Trend Researcher, UX Researcher, Tool Evaluator |
| 1 | **Strategize** | Architecture & planning | Software Architect, Sprint Prioritizer, UX Architect |
| 2 | **Scaffold** | Foundation setup | DevOps Automator, Frontend/Backend devs |
| 3 | **Build** | Dev ↔ QA continuous loop | All engineering + testing agents |
| 4 | **Harden** | Security, perf, accessibility | Reality Checker, Security Engineer, Benchmarker |
| 5 | **Launch** | Go-to-market | Content, SEO, Social Media, Growth agents |
| 6 | **Operate** | Sustained operations | SRE, Support, Analytics, Compliance agents |

Each phase is followed by a **quality gate** — the supervisor reviews outputs and decides pass/fail. A failed gate halts the pipeline.

## Configuration

Environment variables:
- `ANTHROPIC_API_KEY` — Required for the Claude Opus supervisor
- `OLLAMA_BASE_URL` — Ollama endpoint (default: `http://localhost:11434`)

Edit [config.py](config.py) to add/remove models or adjust the task-strength mappings.

## How Model Routing Works

1. Supervisor receives the project brief + phase + available agents
2. For each agent task, supervisor recommends a tier: `free_fast`, `free_medium`, or `free_heavy`
3. The `pick_model()` function selects the best model within that tier by matching task-type strengths
4. The agent's full DreamEngine persona is used as the system prompt
5. Results flow back to state for downstream phases and quality gates

The supervisor is instructed to **always prefer free_fast** and only escalate when genuinely needed.
