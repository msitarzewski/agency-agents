# Pi Integration

Installs the full Agency roster as Pi skills. Each agent is prefixed
with `agency-` to avoid conflicts with existing skills.

## Install

```bash
./scripts/install.sh --tool pi
```

This copies files from `integrations/pi/` to
`~/.pi/agent/skills/` (global).

## Activate a Skill

In Pi, activate an agent by its slug:

```
Use the agency-frontend-developer skill to review this component.
```

Available slugs follow the pattern `agency-<agent-name>`, e.g.:
- `agency-frontend-developer`
- `agency-backend-architect`
- `agency-reality-checker`
- `agency-growth-hacker`

## Regenerate

After modifying agents, regenerate the skill files:

```bash
./scripts/convert.sh --tool pi
```

## File Format

Each skill is a `SKILL.md` file with Pi-compatible frontmatter:

```yaml
---
name: agency-frontend-developer
description: Expert frontend developer specializing in...
---
```

Pi is the coding agent: https://github.com/earendil-works/pi-coding-agent
