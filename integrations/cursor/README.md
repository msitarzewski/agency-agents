# Cursor Integration

Converts all Agency agents into Cursor `.mdc` rule files following the
[standard Cursor rules format](https://docs.cursor.com/context/rules).
Rules are **project-scoped** -- install them from your project root.

## Install

```bash
# Run from your project root
cd /your/project
/path/to/agency-agents/scripts/install.sh --tool cursor
```

This creates `.cursor/rules/<agent-slug>.mdc` files in your project.

## Activate a Rule

In Cursor, reference an agent in your prompt:

```
@frontend-developer Review this React component for performance issues.
```

Or enable a rule as always-on by editing its frontmatter:

```yaml
---
description: Expert frontend developer...
globs: "**/*.tsx,**/*.ts"
alwaysApply: true
---
```

## Rule Format

Each generated `.mdc` file follows the standard Cursor rule format with
YAML frontmatter:

```yaml
---
description: Expert frontend developer specializing in modern web technologies...
globs: ""
alwaysApply: false
---
```

- **description** -- shown in the Cursor rule picker to help identify the agent
- **globs** -- file patterns that auto-activate the rule (empty = manual activation)
- **alwaysApply** -- set to `true` to apply the rule to every conversation

After installing, customize `globs` and `alwaysApply` per-agent to match
your project needs. For example, set the Frontend Developer rule to activate
on `**/*.tsx,**/*.ts` files.

## Regenerate

After modifying agents, regenerate the rule files:

```bash
./scripts/convert.sh --tool cursor
```
