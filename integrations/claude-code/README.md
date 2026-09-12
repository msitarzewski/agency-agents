# Claude Code Integration

The Agency was built for Claude Code. No conversion needed — agents work
natively with the existing `.md` + YAML frontmatter format.

## Install

```bash
# Copy all agents to your Claude Code agents directory
./scripts/install.sh --tool claude-code

# Or manually copy a category
cp engineering/*.md ~/.claude/agents/
```

## Activate an Agent

In any Claude Code session, reference an agent by name:

```
Activate Frontend Developer and help me build a React component.
```

```
Use the Reality Checker agent to verify this feature is production-ready.
```

## Agent Directory

Agents are organized into divisions. See the [main README](../../README.md) for
the full Agency roster.

## Install as Skills (Marketplace)

Instead of copying agents, you can install each division as a skills plugin from
the Agency's [plugin marketplace](../plugin-marketplace/README.md):

```
/plugin marketplace add Marinski/agency-agents#plugins
/plugin install agency-engineering@agency-agents
/reload-plugins
```

Specialists install as skills named by their agent files (e.g.
`agency-engineering:engineering-frontend-developer`), are invocable by name or
by task description, and auto-update as the roster changes.
