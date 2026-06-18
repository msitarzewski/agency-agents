# Pi Coding Agent Integration

Installs the full Agency roster as Pi skills. Each agent is prefixed
with `agency-` to avoid conflicts with existing skills.

## Install

```bash
./scripts/install.sh --tool pi
```

This copies files from `integrations/pi/` to
`~/.pi/agent/skills/`.

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

Each skill is a `SKILL.md` file with standard frontmatter:

```yaml
---
name: agency-frontend-developer
description: Expert frontend developer specializing in...
---
```

## Skill Locations

Pi discovers skills from several locations:

- **Global (user-level):** `~/.pi/agent/skills/`
- **Project-level:** `.pi/skills/`

The installer copies skills to the global location by default. Set the
`PI_SKILLS_DIR` environment variable to override the destination path.
