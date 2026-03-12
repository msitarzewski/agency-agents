# Kiro CLI Integration

Installs all Agency agents as Kiro CLI skills. Each agent is prefixed
with `agency-` to avoid conflicts with existing skills.

## Install

```bash
./scripts/install.sh --tool kiro
```

This copies files from `integrations/kiro/skills/` to
`~/.kiro/skills/`.

## Activate a Skill

In Kiro CLI, skills are automatically available. Reference an agent by name:

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
./scripts/convert.sh --tool kiro
```

## File Format

Each skill is a `SKILL.md` file in `~/.kiro/skills/<skill-name>/`:

```yaml
---
name: agency-frontend-developer
description: Expert frontend developer specializing in...
---
```
