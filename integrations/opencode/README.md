# OpenCode Integration

OpenCode uses the same agent format as Claude Code — `.md` files with YAML
frontmatter stored in `.opencode/agent/`. No conversion is technically
needed, but this integration packages the agents into the correct directory
structure for drop-in use.

## Install

```bash
# Run from your project root
cd /your/project
/path/to/agency-agents/scripts/install.sh --tool opencode
```

This creates `.opencode/agent/<slug>.md` files in your project directory.

## Activate an Agent

In OpenCode, reference an agent by its name or description:

```
Use the Frontend Developer agent to help build this component.
```

```
Activate the Reality Checker agent and review this PR.
```

You can also select agents from the OpenCode UI's agent picker.

## Agent Format

OpenCode agents use the same frontmatter as Claude Code:

```yaml
---
name: Frontend Developer
description: Expert frontend developer specializing in modern web technologies...
color: cyan
---
```

## Project vs Global

Agents in `.opencode/agent/` are **project-scoped**. To make them available
globally across all projects, copy them to your OpenCode config directory:

```bash
mkdir -p ~/.config/opencode/agent
cp integrations/opencode/agent/*.md ~/.config/opencode/agent/
```

## Regenerate

```bash
./scripts/convert.sh --tool opencode
```
