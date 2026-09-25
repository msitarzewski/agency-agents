# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

This is **not a runnable application** — it is a curated collection of AI agent personality files (Markdown with YAML frontmatter) plus shell scripts that convert and install those agents into many third-party agentic tools (Claude Code, Cursor, Aider, Windsurf, OpenCode, OpenClaw, Antigravity, Gemini CLI, Qwen Code, Kimi Code, GitHub Copilot, etc.).

There is no build system, no test suite, no package manifest. The "code" you will edit is almost always a single `.md` agent file.

## Common commands

```bash
# Lint a single agent (or many) — validates YAML frontmatter (name/description/color)
# and warns on missing recommended sections / very short bodies. CI runs this on PRs.
./scripts/lint-agents.sh path/to/agent.md
./scripts/lint-agents.sh                 # scans all configured agent dirs

# Generate all integration outputs into integrations/<tool>/ (does NOT touch ~)
./scripts/convert.sh                     # all tools
./scripts/convert.sh --tool cursor       # one tool: antigravity|gemini-cli|opencode|cursor|aider|windsurf|openclaw|qwen|kimi
./scripts/convert.sh --parallel --jobs 4 # parallel, output buffered per tool

# Install converted files to local agent config dirs (~/.claude/agents, etc.).
# Run from the target project root for project-scoped tools (cursor, opencode, aider, windsurf).
./scripts/install.sh                     # interactive, auto-detects installed tools
./scripts/install.sh --tool claude-code
./scripts/install.sh --no-interactive --tool all

# Regenerate the Chinese catalog at docs/智能体全目录与组合流程.md
# Requires deep-translator; cache lives at docs/.agent-catalog-zh-cache.json (gitignored)
python3 -m venv /tmp/agency-catalog-venv
/tmp/agency-catalog-venv/bin/pip install deep-translator
/tmp/agency-catalog-venv/bin/python3 scripts/generate_agent_catalog_zh.py
```

There is no `npm test` / `pytest` equivalent — `lint-agents.sh` is the only check, and `.github/workflows/lint-agents.yml` is the only CI job.

## Repository layout

```
<category>/<category>-<slug>.md    Source agents (the canonical artifacts)
strategy/                          NEXUS playbooks/runbooks — NOT scanned by convert.sh
examples/                          Multi-agent collaboration sample outputs — NOT agent sources
docs/                              Chinese-language user + developer docs
scripts/                           convert.sh, install.sh, lint-agents.sh, generate_agent_catalog_zh.py
integrations/<tool>/               Generated integration files — mostly gitignored
.cursor/rules/*.mdc                Cursor outputs (this repo dogfoods its own integration)
.github/workflows/lint-agents.yml  CI lint on PRs that touch agent dirs
```

Source agent categories (used by `convert.sh`'s `AGENT_DIRS`): `academic`, `design`, `engineering`, `game-development`, `marketing`, `paid-media`, `sales`, `product`, `project-management`, `testing`, `support`, `spatial-computing`, `specialized`.

`game-development/` is the only category that uses subdirectories (`blender/`, `godot/`, `roblox-studio/`, `unity/`, `unreal-engine/`). All other categories are flat.

## Agent file conventions

Every agent must have YAML frontmatter and follow the path pattern `<category>/<category>-<slug>.md` (or `game-development/<engine>/<slug>.md`):

```yaml
---
name: Agent Name
description: One-line description of specialty and focus
color: cyan                        # named color or #RRGGBB
emoji: 🎯                          # optional, used by openclaw IDENTITY.md
vibe: One-line personality hook    # optional, used by openclaw IDENTITY.md
services:                          # optional, only when external APIs are essential
  - name: ...
    url: ...
    tier: free                     # free | freemium | paid
tools: ...                         # optional, only honored by Qwen converter
---
```

`name`, `description`, `color` are **required** — `lint-agents.sh` errors otherwise. Body should be ≥50 words.

### Section grouping matters for the OpenClaw split

`convert.sh`'s `convert_openclaw` splits the body across `SOUL.md` (persona) vs `AGENTS.md` (operations) by matching `##` header keywords. To stay routable across all targets, keep persona-related sections (Identity, Memory, Communication, Style, Critical Rules) grouped separately from operational sections (Core Mission, Technical Deliverables, Workflow, Success Metrics, Advanced Capabilities). Header keywords that route to SOUL: `identity`, `communication`, `style`, `critical rule`, `rules you must follow`. Everything else falls through to AGENTS.

### Recommended body sections (lint warns if missing)

`Identity`, `Core Mission`, `Critical Rules`. Other sections referenced by the templates: Technical Deliverables, Workflow Process, Communication Style, Success Metrics, Advanced Capabilities.

## Things to know before editing

- **Never commit generated artifacts.** `integrations/<tool>/` outputs (except a small set of hand-written `README.md` files like `integrations/openclaw/README.md`, `integrations/kimi/README.md`) are gitignored on purpose. Users regenerate locally with `convert.sh`. PRs that check in build output will be closed per `CONTRIBUTING.md`.
- **`AGENT_DIRS` differs between scripts.** `convert.sh` scans `academic` and `sales`; `lint-agents.sh`'s `AGENT_DIRS` does not. The CI workflow's path filter and lint scan currently exclude `academic`. If you add files to `academic/` or `sales/`, run lint by passing the file paths explicitly: `./scripts/lint-agents.sh academic/foo.md`.
- **One-agent-per-PR is the merge sweet spot.** Bulk reformatting of existing agents, repo-wide refactors, new tooling, new categories, and new integration formats should start as a GitHub Discussion before code (per `CONTRIBUTING.md`).
- **Color values** can be CSS color names or `#RRGGBB`. The OpenCode converter (`resolve_opencode_color` in `convert.sh`) maps a fixed set of names to hex; unknown strings fall back to `#6B7280`. If you introduce a new named color, add it to that map.
- **Body templating with `${var}`** is supported only in the Qwen output path; other tools render the body as-is. Don't rely on substitution unless you understand each tool's behavior.
- **Aider and Windsurf are single-file outputs** built by accumulation across all agents. Antigravity, Gemini CLI, OpenCode, Cursor, OpenClaw, Qwen, Kimi produce one file (or directory) per agent.
- **`scripts/install.sh` only copies from `integrations/`** — if that tree is missing or stale, run `convert.sh` first. The installer never writes to `~` for project-scoped tools (cursor/opencode/aider/windsurf); run it from the target project root.
- **CI scope.** `.github/workflows/lint-agents.yml` triggers only on PRs that touch the agent category dirs and only lints the changed files. Changes under `scripts/`, `docs/`, `strategy/`, `examples/`, `integrations/` are not gated by CI.
