# Cursor Integration

Converts the full Agency roster into Cursor `.mdc` rule files. Rules are
**project-scoped** — install them from your project root.

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

## Regenerate

```bash
./scripts/convert.sh --tool cursor
```
