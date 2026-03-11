# CLAUDE.md

This file provides guidance for AI assistants working with this repository.

## Repository Overview

**The Agency** is a curated collection of 112+ specialized AI agent personalities organized into 11 divisions. Each agent is a complete persona defined in Markdown with YAML frontmatter, covering identity, expertise, deliverables, workflows, and success metrics. The project supports Claude Code as the primary tool and 8+ other AI coding tools via a conversion pipeline.

## Repository Structure

```
design/                    # 8 agents — UI Design, UX, Brand, Visual Storytelling, etc.
engineering/               # 16 agents — Frontend, Backend, Mobile, DevOps, Security, etc.
game-development/          # 19 agents — Cross-engine + Unity, Unreal, Godot, Roblox subdirs
marketing/                 # 17 agents — Growth, Content, Social platforms, SEO, etc.
paid-media/                # 7 agents — PPC, Search, Display, Social, Creative, Tracking
product/                   # 4 agents — Sprint Planning, Trends, Feedback, Behavioral
project-management/        # 6 agents — Studio Producer, PM, Operations, Experiments
testing/                   # 8 agents — QA, Evidence Collection, Performance, API Testing
support/                   # 6 agents — Customer Support, Analytics, Finance, Infrastructure
spatial-computing/         # 6 agents — XR/VR/AR, Vision Pro, WebXR, Spatial UI
specialized/               # 15 agents — Orchestrator, Data, Identity, Blockchain, etc.
strategy/                  # NEXUS orchestration framework with playbooks and runbooks
integrations/              # Tool-specific conversion outputs and installation guides
scripts/                   # convert.sh, install.sh, lint-agents.sh
examples/                  # Real-world multi-agent collaboration examples
```

## Agent File Format

Every agent file is a Markdown document with required YAML frontmatter:

```yaml
---
name: Agent Name
description: One-line specialty description
color: colorname or "#hexcode"
emoji: 🎯
vibe: One-line personality hook
services:                      # Optional — external APIs/services
  - name: Service Name
    url: https://service-url.com
    tier: free|freemium|paid
---
```

**Required frontmatter fields:** `name`, `description`, `color`

The body is organized into two semantic groups:

- **Persona** (who the agent is): Identity & Memory, Communication Style, Critical Rules
- **Operations** (what the agent does): Core Mission, Technical Deliverables, Workflow Process, Success Metrics, Advanced Capabilities

File naming convention: `<division>-<agent-slug>.md` (e.g., `engineering-frontend-developer.md`), using lowercase kebab-case.

## Linting and Validation

Run the linter before submitting changes to agent files:

```bash
./scripts/lint-agents.sh              # Lint all agents
./scripts/lint-agents.sh path/to/file.md  # Lint specific files
```

The linter enforces:
- **ERROR** (blocks merge): YAML frontmatter with `name`, `description`, `color` fields
- **WARN**: Recommended sections — "Identity", "Core Mission", "Critical Rules"
- **WARN**: Body shorter than 50 words

CI runs this automatically on PRs touching any division directory via `.github/workflows/lint-agents.yml`.

## Tool Integration Pipeline

```bash
./scripts/convert.sh    # Convert agents to all supported tool formats
./scripts/install.sh    # Install converted agents to local tool directories
```

`convert.sh` reads `.md` agents from division directories and generates tool-specific files in `integrations/<tool>/`. Generated files under `integrations/` are gitignored — only the scripts and per-tool README files are committed.

Supported tools: Claude Code, Cursor, GitHub Copilot, Antigravity, Aider, Windsurf, OpenCode, Gemini CLI.

## Key Conventions When Editing Agents

1. **Personality over generics** — agents have distinct voices, not "I am a helpful assistant"
2. **Concrete deliverables** — real, runnable code examples with syntax highlighting, not pseudocode
3. **Measurable metrics** — specific numbers like "Page load < 3s on 3G", not "make it faster"
4. **Proven workflows** — step-by-step battle-tested processes
5. **Narrow specialization** — deep expertise in one area, not jack-of-all-trades
6. **Section headers use emojis** for visual scanning (e.g., `## 🧠 Your Identity & Memory`)

## Commit Message Style

Format: `[action] Agent/feature description`

Examples:
- `Add Solidity Smart Contract Engineer - blockchain security`
- `Update README: add 25 missing agents`
- `Fix: update frontmatter validation for emoji/vibe fields`

## What Not to Do

- Do not commit generated integration files (they're gitignored)
- Do not create agents with overly broad scope
- Do not add agents without testing them in real scenarios
- Do not duplicate vendor documentation inside agent files — reference it instead
- Do not strip personality from agents during edits
