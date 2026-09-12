# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Overview

xct-agents (The Agency) is a collection of 184 AI agent personalities across 15 domains, designed for use with Claude Code and 10+ other agentic tools. Each agent is a Markdown file with YAML frontmatter defining its identity, mission, workflow, and communication style. The repo also includes a FastAPI gateway for LiteLLM integration.

## Tech Stack

- **Agent Definitions**: Markdown with YAML frontmatter
- **Scripts**: Bash (install, convert, lint)
- **Gateway**: Python + FastAPI + uvicorn (integrations/litellm/gateway/)
- **Container**: Docker (for LiteLLM gateway deployment)
- **Deployment**: Railway (via railway.json)
- **CI/CD**: GitHub Actions (lint-agents workflow)

## Commands

```bash
# Install agents to local tools
./scripts/install.sh [--tool <name>]
# Supported tools: claude-code, copilot, antigravity, gemini-cli, opencode,
#                  cursor, aider, windsurf, openclaw, qwen, kimi

# Convert agents to tool-specific formats
./scripts/convert.sh [--tool <name>]

# Validate agent markdown files
./scripts/lint-agents.sh [file ...]

# LiteLLM Gateway
cd integrations/litellm/gateway && ./start.sh        # Start gateway
cd integrations/litellm && python generate_config.py  # Generate LiteLLM config
cd integrations/litellm && python register_agents.py  # Register agents in LiteLLM
```

## Directory Structure

```
# Agent categories (184 agents across 15 domains)
academic/              # Academic specialists
design/                # UI/UX and design
engineering/           # 30+ software engineering specialists
finance/               # Financial planning
game-development/      # Game dev (Blender, Godot, Roblox, Unity, Unreal)
marketing/             # Growth, content, social, platform-specific
paid-media/            # PPC, search, programmatic
product/               # Product management
project-management/    # Coordination, operations
sales/                 # Sales strategy, discovery
spatial-computing/     # AR/VR/XR
specialized/           # 30+ unique specialists (blockchain, compliance, etc.)
strategy/              # Strategic planning
support/               # Operations, infrastructure
testing/               # QA, performance

# Integration & tooling
integrations/          # 14 tool integrations
  litellm/gateway/     # FastAPI A2A gateway (main.py, Dockerfile, railway config)
scripts/               # Bash automation (install, convert, lint, i18n)
examples/              # Workflow examples (MVP, landing page, etc.)
```

## Agent File Format

Every agent is a Markdown file with this structure:

```markdown
---
name: Agent Name
description: One-line specialty description
color: colorname or "#hexcode"
emoji: (unicode emoji)
vibe: One-line personality hook
services:              # optional
  - name: Service Name
    url: https://...
    tier: free|freemium|paid
---
# Agent Name
## Identity & Memory
## Core Mission
## Critical Rules
## Technical Deliverables
## Workflow Process
## Communication Style
## Learning & Memory
## Success Metrics
## Advanced Capabilities
```

**Linting requirements**:
- Required frontmatter: `name`, `description`, `color`
- Recommended sections: Identity, Core Mission, Critical Rules
- Minimum body content: 50+ words

## Environment Variables

For the LiteLLM gateway:
```bash
LITELLM_API_BASE=http://localhost:4000   # LiteLLM proxy base URL
LITELLM_API_KEY=sk-1234                  # API key for LiteLLM
DEFAULT_MODEL=deepseek-v3.2              # LLM model to use
AGENTS_REPO_PATH=                        # Path to xct-agents repo (auto-detected)
PORT=9000                                # Gateway port (Railway env var)
```

## Deployment

**LiteLLM Gateway** has two integration approaches:

**Approach A — Model List** (simple, agents as models):
```bash
python generate_config.py --approach model --model claude-3-5-sonnet-20241022
# Merge litellm_agents.yaml into proxy config
# Call: {"model": "xct-frontend-developer"}
```

**Approach B — A2A Gateway** (full, OpenAI-compatible API):
```bash
python generate_config.py --approach agent --gateway-base http://localhost:9000
uvicorn main:app --host 0.0.0.0 --port 9000
# Call: {"model": "a2a/xct-frontend-developer"}
```

**Docker/Railway**: `Dockerfile.railway` bakes agents into image for production. Healthcheck at `/health`.

## Contributing

- Follow the agent file format strictly; CI lints on PR
- Map sections to SOUL (persona) or AGENTS (operations) categories
- No secrets in agent definitions
- See CONTRIBUTING.md for full guidelines
