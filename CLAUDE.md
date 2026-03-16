# The Agency — CLAUDE.md

> **The complete reference for understanding, navigating, and extending this repository.**
> Updated: 2026-03-10 · Branch policy: develop on `claude/*` branches, merge to `master`.

---

## What This Repo Is

**The Agency** is a curated library of 106+ specialized AI agent definition files — each one a complete persona, workflow, and deliverable specification for a domain expert. Agents are written in plain Markdown with YAML frontmatter and work with **any AI coding tool** (Claude Code, Cursor, Windsurf, Aider, Gemini CLI, OpenCode, GitHub Copilot).

The repository also ships:
- **NEXUS** — a 7-phase multi-agent orchestration doctrine for complete product builds
- **Conversion scripts** — auto-generate tool-specific formats from the source Markdown
- **Integration guides** — per-tool installation instructions

There is **no application code**, no runtime, and no build pipeline required to use the agents.

---

## Repository Structure

```
AGENCY-AGENTS-MAIN/
│
├── CLAUDE.md                      ← You are here
├── README.md                      ← Public-facing overview
├── CONTRIBUTING.md                ← How to add agents
├── LICENSE                        ← MIT
│
├── design/                        (8 agents)  Visual, UX, brand specialists
├── engineering/                   (16 agents) Frontend, backend, DevOps, security…
├── game-development/              (19 agents) + per-engine subdirectories
│   ├── godot/                     (3 agents)
│   ├── unity/                     (4 agents)
│   ├── unreal-engine/             (4 agents)
│   └── roblox-studio/             (3 agents)
├── marketing/                     (17 agents) Growth, social, SEO, regional platforms
├── product/                       (4 agents)  PM, feedback, trends, behavioral design
├── project-management/            (6 agents)  Producer, shepherd, ops, Jira, experiments
├── spatial-computing/             (6 agents)  XR, visionOS, Metal, WebXR
├── specialized/                   (15 agents) Orchestration, finance, compliance, blockchain
├── support/                       (6 agents)  Analytics, legal, finance, infra, exec
├── testing/                       (8 agents)  QA, evidence, performance, accessibility
│
├── strategy/
│   ├── nexus-strategy.md          ← Full NEXUS doctrine (55 KB)
│   ├── EXECUTIVE-BRIEF.md         ← C-suite summary
│   ├── QUICKSTART.md              ← 5-minute activation guide
│   ├── playbooks/                 ← Per-phase execution guides (phases 0–6)
│   ├── runbooks/                  ← Scenario-specific runbooks
│   └── coordination/              ← Handoff templates, activation prompts
│
├── integrations/
│   ├── README.md                  ← Master integration guide
│   ├── aider/
│   ├── antigravity/
│   ├── claude-code/
│   ├── cursor/
│   ├── gemini-cli/
│   ├── github-copilot/
│   ├── mcp-memory/
│   ├── opencode/
│   └── windsurf/
│
├── examples/
│   ├── workflow-startup-mvp.md
│   ├── workflow-landing-page.md
│   ├── workflow-with-memory.md
│   └── nexus-spatial-discovery.md (40 KB end-to-end example)
│
├── scripts/
│   ├── convert.sh                 ← Convert agents → tool-specific formats
│   ├── install.sh                 ← Auto-detect + install agents into tools
│   └── lint-agents.sh             ← Validate agent file format (CI/CD)
│
└── docs/
    ├── index.html                 ← Visual agent dashboard (GitHub Pages)
    └── .nojekyll
```

---

## Agent File Format

Every agent file is a Markdown file with **required YAML frontmatter** followed by a structured body.

### Frontmatter Spec

```yaml
---
name: Frontend Developer          # Display name (required)
description: Expert frontend...   # One-sentence description (required)
color: cyan                       # Brand color: named or hex (required)
tools: WebFetch, Read, Write      # Optional: tool access hints for the AI
---
```

**Valid color values:** named CSS colors (`cyan`, `blue`, `green`, `purple`, `red`, `orange`, `pink`, `gold`, `teal`, `indigo`, `violet`, `amber`, `gray`) or hex codes (`"#FF4500"`).

### Body Sections (Recommended)

| Section | Purpose |
|---------|---------|
| `## 🧠 Your Identity & Memory` | Persona, personality, communication style |
| `## 🎯 Your Core Mission` | Primary objectives and success criteria |
| `## 🚨 Critical Rules You Must Follow` | Non-negotiable constraints and guardrails |
| `## 📋 Your Deliverables` | Concrete outputs with examples |
| `## 💬 Your Communication Style` | Tone, format, and interaction patterns |
| `## ✅ Success Metrics` | How good work is measured |

The lint script validates the frontmatter and warns on missing recommended sections.

---

## Division Reference

| Division | Count | Purpose | Path |
|----------|------:|---------|------|
| Engineering | 16 | Full-stack, DevOps, security, embedded, AI/ML | `engineering/` |
| Marketing | 17 | Growth, social (global + Chinese), SEO, content | `marketing/` |
| Game Development | 19 | Cross-engine + Godot/Unity/Unreal/Roblox specialists | `game-development/` |
| Specialized | 15 | Orchestration, finance, compliance, blockchain, ZK | `specialized/` |
| Design | 8 | UI/UX, brand, inclusive design, AI image prompts | `design/` |
| Testing | 8 | QA, accessibility, performance, reality-checking | `testing/` |
| Support | 6 | Analytics, legal, finance, infrastructure, exec comms | `support/` |
| Project Management | 6 | Producer, shepherd, ops, Jira, experiments, PM | `project-management/` |
| Spatial Computing | 6 | XR, visionOS, Metal, WebXR, terminal integration | `spatial-computing/` |
| Product | 4 | Sprint planning, trends, feedback, behavioral nudges | `product/` |
| **Total** | **106+** | | |

---

## Complete Agent Roster

### Engineering (16)
| File | Agent | Color | Description |
|------|-------|-------|-------------|
| `engineering-ai-engineer.md` | AI Engineer | blue | ML model development, deployment, LLM integration |
| `engineering-autonomous-optimization-architect.md` | Autonomous Optimization Architect | #673AB7 | Shadow-tests APIs, enforces financial & security guardrails |
| `engineering-backend-architect.md` | Backend Architect | blue | Scalable system design, databases, APIs, cloud |
| `engineering-data-engineer.md` | Data Engineer | orange | ETL/ELT, Spark, dbt, lakehouse architectures |
| `engineering-devops-automator.md` | DevOps Automator | orange | CI/CD pipelines, infrastructure automation |
| `engineering-embedded-firmware-engineer.md` | Embedded Firmware Engineer | orange | ESP32, ARM Cortex-M, FreeRTOS, Zephyr |
| `engineering-frontend-developer.md` | Frontend Developer | cyan | React/Vue/Angular, UI implementation, performance |
| `engineering-incident-response-commander.md` | Incident Response Commander | #e63946 | Production incidents, SLO/SLI, post-mortems |
| `engineering-mobile-app-builder.md` | Mobile App Builder | purple | iOS/Android, React Native, Flutter |
| `engineering-rapid-prototyper.md` | Rapid Prototyper | green | Ultra-fast POC and MVP development |
| `engineering-security-engineer.md` | Security Engineer | red | Threat modeling, secure code review, AppSec |
| `engineering-senior-developer.md` | Senior Developer | green | Laravel/Livewire/FluxUI, advanced CSS, Three.js |
| `engineering-solidity-smart-contract-engineer.md` | Solidity Smart Contract Engineer | orange | EVM contracts, DeFi, gas optimization |
| `engineering-technical-writer.md` | Technical Writer | teal | Developer docs, API references, READMEs |
| `engineering-threat-detection-engineer.md` | Threat Detection Engineer | #7b2d8e | SIEM rules, MITRE ATT&CK, detection-as-code |
| `engineering-wechat-mini-program-developer.md` | WeChat Mini Program Developer | green | WXML/WXSS, WeChat APIs, payment systems |

### Design (8)
| File | Agent | Color | Description |
|------|-------|-------|-------------|
| `design-brand-guardian.md` | Brand Guardian | blue | Brand identity, consistency, strategic positioning |
| `design-image-prompt-engineer.md` | Image Prompt Engineer | amber | AI image generation prompt crafting |
| `design-inclusive-visuals-specialist.md` | Inclusive Visuals Specialist | #4DB6AC | Defeats AI bias, culturally accurate imagery |
| `design-ui-designer.md` | UI Designer | purple | Design systems, component libraries, pixel-perfect UI |
| `design-ux-architect.md` | UX Architect | purple | CSS systems, implementation guidance, foundations |
| `design-ux-researcher.md` | UX Researcher | green | Usability testing, user behavior analysis |
| `design-visual-storyteller.md` | Visual Storyteller | purple | Visual narratives, multimedia, brand storytelling |
| `design-whimsy-injector.md` | Whimsy Injector | pink | Personality, delight, playful brand moments |

### Marketing (17)
| File | Agent | Color | Description |
|------|-------|-------|-------------|
| `marketing-app-store-optimizer.md` | App Store Optimizer | blue | ASO, conversion rate, app discoverability |
| `marketing-baidu-seo-specialist.md` | Baidu SEO Specialist | blue | Chinese search, ICP compliance, Baidu ecosystem |
| `marketing-bilibili-content-strategist.md` | Bilibili Content Strategist | pink | UP主 growth, danmaku culture, B站 algorithm |
| `marketing-carousel-growth-engine.md` | Carousel Growth Engine | #FF0050 | TikTok/Instagram carousel automation pipeline |
| `marketing-china-ecommerce-operator.md` | China E-Commerce Operator | red | Taobao, Tmall, Pinduoduo, live commerce |
| `marketing-content-creator.md` | Content Creator | teal | Multi-platform content strategy, editorial calendars |
| `marketing-growth-hacker.md` | Growth Hacker | green | Viral loops, conversion funnels, acquisition |
| `marketing-instagram-curator.md` | Instagram Curator | #E4405F | Visual storytelling, community, multi-format content |
| `marketing-kuaishou-strategist.md` | Kuaishou Strategist | orange | Short-video, lower-tier cities, live commerce |
| `marketing-reddit-community-builder.md` | Reddit Community Builder | #FF4500 | Authentic community engagement, Reddit culture |
| `marketing-seo-specialist.md` | SEO Specialist | #4285F4 | Technical SEO, link authority, organic growth |
| `marketing-social-media-strategist.md` | Social Media Strategist | blue | LinkedIn, Twitter, cross-platform campaigns |
| `marketing-tiktok-strategist.md` | TikTok Strategist | #000000 | Viral content, algorithm optimization |
| `marketing-twitter-engager.md` | Twitter Engager | #1DA1F2 | Real-time engagement, thought leadership, threads |
| `marketing-wechat-official-account.md` | WeChat Official Account Manager | #09B83E | WeChat OA content, subscriber engagement |
| `marketing-xiaohongshu-specialist.md` | Xiaohongshu Specialist | #FF1B6D | Lifestyle content, micro-content, viral growth |
| `marketing-zhihu-strategist.md` | Zhihu Strategist | #0084FF | Thought leadership, Q&A credibility building |

### Product (4)
| File | Agent | Color | Description |
|------|-------|-------|-------------|
| `product-behavioral-nudge-engine.md` | Behavioral Nudge Engine | #FF8A65 | Psychology-driven interaction design |
| `product-feedback-synthesizer.md` | Feedback Synthesizer | blue | Multi-channel feedback → actionable product insights |
| `product-sprint-prioritizer.md` | Sprint Prioritizer | green | Agile sprint planning, feature prioritization |
| `product-trend-researcher.md` | Trend Researcher | purple | Market intelligence, competitive analysis |

### Project Management (6)
| File | Agent | Color | Description |
|------|-------|-------|-------------|
| `project-management-experiment-tracker.md` | Experiment Tracker | purple | A/B tests, hypothesis validation, experiment design |
| `project-management-jira-workflow-steward.md` | Jira Workflow Steward | orange | Jira-linked Git workflows, traceable commits |
| `project-management-project-shepherd.md` | Project Shepherd | blue | Cross-functional coordination, timeline management |
| `project-management-studio-operations.md` | Studio Operations | green | Day-to-day efficiency, process optimization |
| `project-management-studio-producer.md` | Studio Producer | gold | Portfolio orchestration, creative/business alignment |
| `project-manager-senior.md` | Senior Project Manager | blue | Spec-to-task conversion, scope management |

### Testing (8)
| File | Agent | Color | Description |
|------|-------|-------|-------------|
| `testing-accessibility-auditor.md` | Accessibility Auditor | #0077B6 | WCAG audits, assistive tech testing |
| `testing-api-tester.md` | API Tester | purple | API validation, performance testing, QA |
| `testing-evidence-collector.md` | Evidence Collector | orange | Screenshot-obsessed QA, visual proof required |
| `testing-performance-benchmarker.md` | Performance Benchmarker | orange | System performance measurement and optimization |
| `testing-reality-checker.md` | Reality Checker | red | Evidence-based certification, stops fantasy approvals |
| `testing-test-results-analyzer.md` | Test Results Analyzer | indigo | Test result evaluation, quality metrics |
| `testing-tool-evaluator.md` | Tool Evaluator | teal | Technology assessment, tool recommendations |
| `testing-workflow-optimizer.md` | Workflow Optimizer | green | Process improvement, workflow automation |

### Support (6)
| File | Agent | Color | Description |
|------|-------|-------|-------------|
| `support-analytics-reporter.md` | Analytics Reporter | teal | Dashboards, statistical analysis, KPI tracking |
| `support-executive-summary-generator.md` | Executive Summary Generator | purple | McKinsey/BCG/Bain frameworks for C-suite comms |
| `support-finance-tracker.md` | Finance Tracker | green | Financial planning, budget management, cash flow |
| `support-infrastructure-maintainer.md` | Infrastructure Maintainer | orange | System reliability, performance, cost efficiency |
| `support-legal-compliance-checker.md` | Legal Compliance Checker | red | Multi-jurisdiction compliance, data handling |
| `support-support-responder.md` | Support Responder | blue | Customer support, issue resolution, CX optimization |

### Specialized (15)
| File | Agent | Color | Description |
|------|-------|-------|-------------|
| `accounts-payable-agent.md` | Accounts Payable Agent | green | Vendor payments across crypto/fiat/stablecoins |
| `agentic-identity-trust.md` | Agentic Identity & Trust Architect | #2d5a27 | Auth and trust systems for multi-agent environments |
| `agents-orchestrator.md` | Agents Orchestrator | cyan | Autonomous pipeline manager, NEXUS lead |
| `blockchain-security-auditor.md` | Blockchain Security Auditor | red | Smart contract audits, exploit analysis |
| `compliance-auditor.md` | Compliance Auditor | orange | SOC 2, ISO 27001, HIPAA, PCI-DSS audits |
| `data-analytics-reporter.md` | Data Analytics Reporter | indigo | Data → insights, dashboards, KPIs |
| `data-consolidation-agent.md` | Data Consolidation Agent | #38a169 | Sales data → live reporting dashboards |
| `identity-graph-operator.md` | Identity Graph Operator | #C5A572 | Canonical entity resolution for multi-agent systems |
| `lsp-index-engineer.md` | LSP/Index Engineer | orange | Language Server Protocol, semantic indexing |
| `report-distribution-agent.md` | Report Distribution Agent | #d69e2e | Automated report distribution by territory |
| `sales-data-extraction-agent.md` | Sales Data Extraction Agent | #2b6cb0 | Excel monitoring, MTD/YTD/Year-End extraction |
| `specialized-cultural-intelligence-strategist.md` | Cultural Intelligence Strategist | #FFA000 | Defeats invisible exclusion, cross-cultural CQ |
| `specialized-developer-advocate.md` | Developer Advocate | purple | Developer communities, DX, platform adoption |
| `specialized-model-qa.md` | Model QA Specialist | #B22222 | ML model audits, calibration, replication |
| `zk-steward.md` | ZK Steward | teal | Zettelkasten knowledge base, atomic notes, cross-domain |

### Spatial Computing (6)
| File | Agent | Color | Description |
|------|-------|-------|-------------|
| `macos-spatial-metal-engineer.md` | macOS Spatial/Metal Engineer | metallic-blue | Swift, Metal, 3D rendering, Vision Pro |
| `terminal-integration-specialist.md` | Terminal Integration Specialist | green | Terminal emulation, SwiftTerm, text rendering |
| `visionos-spatial-engineer.md` | visionOS Spatial Engineer | indigo | visionOS, SwiftUI volumetric, Liquid Glass |
| `xr-cockpit-interaction-specialist.md` | XR Cockpit Interaction Specialist | orange | Cockpit control systems for XR |
| `xr-immersive-developer.md` | XR Immersive Developer | neon-cyan | WebXR, browser-based AR/VR/XR |
| `xr-interface-architect.md` | XR Interface Architect | neon-green | Spatial interaction design for AR/VR/XR |

### Game Development (19)

**Cross-engine (5):**
| File | Agent | Color | Description |
|------|-------|-------|-------------|
| `game-audio-engineer.md` | Game Audio Engineer | indigo | FMOD/Wwise, adaptive music, spatial audio |
| `game-designer.md` | Game Designer | yellow | GDD, player psychology, economy balancing |
| `level-designer.md` | Level Designer | teal | Layout theory, pacing, environmental narrative |
| `narrative-designer.md` | Narrative Designer | red | Branching dialogue, lore, story systems |
| `technical-artist.md` | Technical Artist | pink | Shaders, VFX, LOD pipelines, cross-engine assets |

**Godot (3):** Gameplay Scripter (purple), Multiplayer Engineer (violet), Shader Developer (purple)

**Unity (4):** Architect (blue), Editor Tool Developer (gray), Multiplayer Engineer (blue), Shader Graph Artist (cyan)

**Unreal Engine (4):** Multiplayer Architect (red), Systems Engineer (orange), Technical Artist (orange), World Builder (green)

**Roblox Studio (3):** Avatar Creator (fuchsia), Experience Designer (lime), Systems Scripter (rose)

---

## NEXUS Orchestration System

**NEXUS** (Network of EXperts, Unified in Strategy) is the multi-agent coordination doctrine in `strategy/`.

### Three Modes

| Mode | Scope | Agents | Duration |
|------|-------|--------|---------|
| **NEXUS-Full** | Complete product from zero | All agents | 12–24 weeks |
| **NEXUS-Sprint** | Feature or MVP | 15–25 agents | 2–6 weeks |
| **NEXUS-Micro** | Single task (bug fix, campaign) | 5–10 agents | 1–5 days |

### Seven Phases

| Phase | Name | Key Agents |
|-------|------|-----------|
| 0 | Discovery | Trend Researcher, UX Researcher, Analytics Reporter, Legal Compliance |
| 1 | Strategy | Studio Producer, Senior PM, Sprint Prioritizer, UX Architect, Brand Guardian |
| 2 | Foundation | DevOps Automator, Frontend Dev, Backend Architect, Infrastructure Maintainer |
| 3 | Build | Dev↔QA loops (all engineering + Evidence Collector) — max 3 retries per task |
| 4 | Hardening | Reality Checker, Performance Benchmarker, API Tester, Legal Compliance |
| 5 | Launch | Growth Hacker, Content Creator, all marketing agents, DevOps Automator |
| 6 | Operate | Analytics Reporter, Infrastructure Maintainer, Support Responder |

### Key Principles
- **Quality gates between every phase** — evidence required, no fantasy approvals
- **Dev↔QA loop** catches 95% of defects before integration (max 3 retries)
- **Parallel workstreams** (Core Product, Growth, Quality, Brand) compress timelines 40–60%
- **Handoff templates** in `strategy/coordination/` maintain context continuity

### Scenario Runbooks
- `scenario-startup-mvp.md` — Zero to launched MVP
- `scenario-enterprise-feature.md` — Feature inside existing enterprise product
- `scenario-incident-response.md` — Production fire response
- `scenario-marketing-campaign.md` — Full campaign from brief to live

---

## Scripts Reference

### `scripts/convert.sh` — Generate tool-specific formats

```bash
# Convert all agents for all tools
./scripts/convert.sh

# Convert for a specific tool
./scripts/convert.sh --tool cursor
./scripts/convert.sh --tool windsurf
./scripts/convert.sh --tool aider
./scripts/convert.sh --tool gemini-cli
./scripts/convert.sh --tool opencode
./scripts/convert.sh --tool antigravity
```

**Output paths (gitignored, regenerated each run):**
- `integrations/cursor/rules/` — `.mdc` rule files
- `integrations/windsurf/.windsurfrules` — single combined file
- `integrations/aider/CONVENTIONS.md` — single combined file
- `integrations/gemini-cli/skills/` — `.md` skill files + `gemini-extension.json`
- `integrations/opencode/agent/` — `.md` agent files
- `integrations/antigravity/agency-*/` — `SKILL.md` per agent

### `scripts/install.sh` — Install into detected tools

```bash
# Interactive: auto-detects installed tools and installs
./scripts/install.sh

# Install into a specific tool
./scripts/install.sh --tool cursor
./scripts/install.sh --tool copilot
./scripts/install.sh --tool aider
./scripts/install.sh --tool windsurf
./scripts/install.sh --tool claude-code
```

### `scripts/lint-agents.sh` — Validate agent files

```bash
# Lint all agents (run by CI on every PR)
./scripts/lint-agents.sh

# Lint specific files
./scripts/lint-agents.sh engineering/engineering-frontend-developer.md
```

**Checks:** frontmatter existence, required fields (`name`, `description`, `color`), recommended sections, minimum content length.

---

## Integration Guide

### Claude Code (native — no conversion needed)
```bash
cp -r engineering/ marketing/ design/ ~/.claude/agents/
# Then activate: "activate Frontend Developer mode"
```

### Cursor
```bash
./scripts/convert.sh --tool cursor
./scripts/install.sh --tool cursor
# Installs to .cursor/rules/ in current project
```

### Windsurf
```bash
./scripts/convert.sh --tool windsurf
./scripts/install.sh --tool windsurf
# Creates .windsurfrules in project root
```

### Aider
```bash
./scripts/convert.sh --tool aider
./scripts/install.sh --tool aider
# Creates CONVENTIONS.md in project root
```

### Gemini CLI
```bash
./scripts/convert.sh --tool gemini-cli
./scripts/install.sh --tool gemini-cli
# Installs to ~/.gemini/extensions/agency-agents/
```

### OpenCode
```bash
./scripts/convert.sh --tool opencode
./scripts/install.sh --tool opencode
```

### GitHub Copilot
```bash
./scripts/install.sh --tool copilot
# Creates .github/copilot-instructions.md
```

### With Memory (MCP)
See `integrations/mcp-memory/` for enhanced agents with persistent memory support.

---

## How to Add a New Agent

1. Choose the appropriate division directory
2. Name the file: `{division}-{agent-name}.md` (kebab-case)
3. Add required frontmatter:

```markdown
---
name: Your Agent Name
description: One sentence describing what this agent specializes in.
color: blue
---

## 🧠 Your Identity & Memory

You are [name], [personality description].

## 🎯 Your Core Mission

[Primary objectives]

## 🚨 Critical Rules You Must Follow

- [Non-negotiable constraint]
- [Another constraint]

## 📋 Your Deliverables

[Concrete outputs with examples]

## 💬 Your Communication Style

[Tone and format]

## ✅ Success Metrics

[How good work is measured]
```

4. Run `./scripts/lint-agents.sh path/to/your-agent.md` to validate
5. Run `./scripts/convert.sh` to regenerate tool-specific formats

---

## Quick Activation Phrases

```
# Single agent
"Activate Frontend Developer mode and help me build a React component"
"You are the Backend Architect. Design a database schema for..."
"Switch to Security Engineer mode and review this code for vulnerabilities"

# NEXUS Full
"Activate Agents Orchestrator in NEXUS-Full mode.
Project: [Name]
Specification: [Description]
Execute the complete NEXUS pipeline."

# NEXUS Sprint
"Activate Agents Orchestrator in NEXUS-Sprint mode.
Goal: Build [Feature] in [Timeframe].
Start with Phase 1 strategy."

# NEXUS Micro
"Activate [Agent Name]. Task: [Specific task]."
```

---

## Key Files to Read First

| If you want to... | Read |
|-------------------|------|
| Understand the full NEXUS system | `strategy/nexus-strategy.md` |
| Start a new project quickly | `strategy/QUICKSTART.md` |
| See a complete real-world example | `examples/nexus-spatial-discovery.md` |
| Learn integration details | `integrations/README.md` |
| Understand handoff protocols | `strategy/coordination/handoff-templates.md` |
| See agent activation prompts | `strategy/coordination/agent-activation-prompts.md` |
| Run an MVP scenario | `strategy/runbooks/scenario-startup-mvp.md` |

---

## Visual Dashboard (GitHub Pages)

The `docs/index.html` file is a self-contained visual dashboard for browsing all agents:

- **Browse** all 106+ agents organized by division
- **Search** agents by name or description
- **Click** any agent to view its full prompt
- **Copy** the prompt to clipboard for use in any AI tool
- **Download** individual `.md` files or bulk export by division
- **Install guides** for every supported tool

**Deploy to GitHub Pages:**
1. Settings → Pages → Source: Deploy from a branch
2. Branch: `main` → Folder: `/docs`
3. Live at: `https://anshmudgil.github.io/AGENCY-AGENTS-MAIN/`
