# Hermes Agent Integration

Each agent in The Agency becomes a [Hermes Agent](https://github.com/NousResearch/hermes-agent) skill — a `SKILL.md` file with the agent's personality, rules, and workflows baked in.

## How it works

1. **Convert:** `./scripts/convert.sh --tool hermes` generates `SKILL.md` files under `integrations/hermes/<division>/<agent-name>/`
2. **Install:** `./scripts/install.sh --tool hermes` copies them to `~/.hermes/skills/agency-agents/`
3. **Use:** In any Hermes session, `/skill <agent-name>` loads that agent's persona. Or preload at startup: `hermes --skills <agent-name>`

## What's generated

Each agent gets its own directory with `SKILL.md` using Hermes' native skill format — YAML frontmatter (name, description, version, tags) followed by the full agent body.

## Notes

- Hermes skills are self-contained — no registration, no restart needed
- All divisions convert correctly: engineering, marketing, sales, security, design, finance, etc.
- Run `./scripts/convert.sh --tool hermes` to regenerate after adding/modifying agents
