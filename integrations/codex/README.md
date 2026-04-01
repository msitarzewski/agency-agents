# Codex Integration

Converts Agency agents into Codex skill folders. Each agent becomes a separate
skill in `~/.codex/skills/` and is prefixed with `agency-` to avoid naming
conflicts with existing local skills.

## Install

```bash
# Generate Codex skill folders (required on a fresh clone)
./scripts/convert.sh --tool codex

# Install all skills into ~/.codex/skills/
./scripts/install.sh --tool codex
```

This copies each generated skill directory from `integrations/codex/` to your
local Codex skills directory.

## Activate a Skill

Codex can auto-trigger these skills from their descriptions, or you can invoke
one explicitly:

```
Use $agency-frontend-developer to review this component.
```

Available skill names follow the pattern `agency-<agent-name>`, for example:
- `agency-frontend-developer`
- `agency-backend-architect`
- `agency-code-reviewer`
- `agency-growth-hacker`

## Skill Structure

Each generated skill directory contains:

```
~/.codex/skills/agency-frontend-developer/
|- SKILL.md
`- agents/
   `- openai.yaml
```

`SKILL.md` contains the agent instructions and trigger description.
`agents/openai.yaml` provides Codex UI metadata such as the display name and a
default prompt.

## Regenerate

After modifying source agents:

```bash
./scripts/convert.sh --tool codex
./scripts/install.sh --tool codex
```
