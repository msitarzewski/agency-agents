# Examples

This directory contains example outputs demonstrating how the agency's agents can be orchestrated together to tackle real-world tasks.

## Why This Exists

The agency-agents repo defines dozens of specialized agents across engineering, design, marketing, product, support, spatial computing, and project management. But agent definitions alone don't show what happens when you **deploy them all at once** on a single mission.

These examples answer the question: *"What does it actually look like when the full agency collaborates?"*

## Contents

### [nexus-spatial-discovery.md](./nexus-spatial-discovery.md)

**What:** A complete product discovery exercise where 8 agents worked in parallel to evaluate a software opportunity and produce a unified plan.

**The scenario:** Web research identified an opportunity at the intersection of AI agent orchestration and spatial computing. The entire agency was then deployed simultaneously to produce:

- Market validation and competitive analysis
- Technical architecture (8-service system design with full SQL schema)
- Brand strategy and visual identity
- Go-to-market and growth plan
- Customer support operations blueprint
- UX research plan with personas and journey maps
- 35-week project execution plan with 65 sprint tickets
- Spatial interface architecture specification

**Agents used:**
| Agent | Role |
|-------|------|
| Product Trend Researcher | Market validation, competitive landscape |
| Backend Architect | System architecture, data model, API design |
| Brand Guardian | Positioning, visual identity, naming |
| Growth Hacker | GTM strategy, pricing, launch plan |
| Support Responder | Support tiers, onboarding, community |
| UX Researcher | Personas, journey maps, design principles |
| Project Shepherd | Phase plan, sprints, risk register |
| XR Interface Architect | Spatial UI specification |

**Key takeaway:** All 8 agents ran in parallel and produced coherent, cross-referencing plans without coordination overhead. The output demonstrates the agency's ability to go from "find an opportunity" to "here's the full blueprint" in a single session.

### [workflow-local-first-dispatch.md](./workflow-local-first-dispatch.md)

**What:** Worked example of dispatching agency agents through a **local OpenAI-compatible LLM runtime** (Ollama, LM Studio, MLX, vLLM, llama.cpp) at **$0 inference cost**. Uses the [`local-first-dispatcher/`](./local-first-dispatcher/) reference implementation — Node + Python, stdlib-only, ~300 LOC each. Same agent files, no API tokens spent, prompts never leave the machine. Includes a Reflexion 3-pass critique pattern that closes most of the gap to frontier models on harder tasks.

**The scenario:** Build a small SaaS side project (kanban tool) using Backend Architect → Frontend Developer → Content Creator → Reality Checker. Total dispatch cost: $0. Total wall time: ~1-2 minutes on a 16 GB Mac running an 8B model.

**Agents used:**
| Agent | Role |
|-------|------|
| Backend Architect | Postgres schema + REST endpoints |
| Frontend Developer | React component tree + state ownership |
| Content Creator | Launch tweets (3 angles) |
| Reality Checker | Adversarial cross-artifact review |

**Key takeaway:** The agent `.md` files in this repo work as system prompts against ANY OpenAI-compatible runtime. You get the same outputs you'd get from a hosted Claude / GPT run, at $0/dispatch, with no vendor lock-in. The reference implementation is ~300 LOC of stdlib-only code in [`local-first-dispatcher/`](./local-first-dispatcher/) with setup guides for 4 popular runtimes (Ollama, LM Studio, MLX, vLLM) and a 24-test suite that validates against a live local LLM.

## Adding New Examples

If you run an interesting multi-agent exercise, consider adding it here. Good examples show:

- Multiple agents collaborating on a shared objective
- The breadth of the agency's capabilities
- Real-world applicability of the agent definitions
