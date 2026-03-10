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

### [workflow-content-engine.md](./workflow-content-engine.md)

**What:** A repeatable weekly multi-platform content production pipeline using 8 marketing agents.

**The scenario:** A B2B SaaS brand needs a sustainable content engine — from keyword research to cross-platform publishing to analytics-driven iteration. The full cycle runs in about a week and gets smarter every cycle.

**Agents used:**
| Agent | Role |
|-------|------|
| SEO Specialist | Keyword research, topic validation, on-page optimization |
| Growth Hacker | Audience intelligence, distribution analysis, end-of-cycle analytics |
| Content Creator | Editorial calendar, long-form pillar content |
| Twitter Engager | Thread and standalone tweet packages |
| Instagram Curator | Carousel and Reel concepts |
| TikTok Strategist | Short-form video scripts and hooks |
| Reddit Community Builder | Community distribution and engagement |
| Social Media Strategist | Cross-platform publishing calendar |

**Key takeaway:** Research runs in parallel, platform adaptation runs in parallel, and the analytics review at the end feeds directly back into the next cycle — compounding the engine's effectiveness over time.

**For ongoing weekly operation** with self-optimization and human approval gates, use `marketing-content-engine-weekly-runner.md` with the `content-engine-state.md` config file. The runner reads last week's performance, generates an optimized plan for user review, executes on approval, and writes results back to state — closing the loop automatically each week.

### [content-engine-state.md](./content-engine-state.md)

**What:** The persistent state file for the content engine. Stores brand config, performance benchmarks, weekly cycle logs, cumulative learnings, and approval history.

**How to use:** Copy this file into your project root, fill in Brand Configuration and Benchmarks, then reference it in every Content Engine Weekly Runner activation. The runner appends to it automatically each cycle — you never lose your optimization history.

## Adding New Examples

If you run an interesting multi-agent exercise, consider adding it here. Good examples show:

- Multiple agents collaborating on a shared objective
- The breadth of the agency's capabilities
- Real-world applicability of the agent definitions
