# Cursor Integration

Converts Agency **division Claude agent sources** (`<division>/*.md`) into a
**subagent-first Cursor config pack**. Sources are never `.mdc` files and never
legacy `integrations/cursor/rules/` personas.

## What gets installed

Project-scoped under your project root (`$PWD`):

| Artifact | Path |
|----------|------|
| Subagents (flattened) | `.cursor/agents/<slug>.md` |
| Thin router (only always-on rule) | `.cursor/rules/agency-router.mdc` |
| Optional skills | `.cursor/skills/<slug>/` |
| `/agency` command | `.cursor/commands/agency.md` |
| Catalog | `.cursor/catalog/roster.json` (+ `by-division/`) |
| AGENTS section | `AGENTS.md` (merge markers) |
| **REI overlay** (optional) | `.cursor/` agents/rules/skills/commands/docs from repo `rei/` |

Persona `.mdc` rules are **not** generated. Do not set `alwaysApply: true` on
individual Agency agents — only the Agency router + REI thin rules are always-on.

## Install

```bash
# From agency-agents: regenerate the Agency pack from Claude sources
./scripts/convert.sh --tool cursor

# From your project root — Agency specialists + REI delivery pipeline
cd /your/project
/path/to/agency-agents/scripts/install.sh --tool cursor --with-rei --division engineering,testing,product
```

`--with-rei` merges versioned `rei/` (Planner/Implementer/…, orchestration, workflow skills).
Omit with `--no-rei` for Agency-only. If `rei/` exists, merge is the default.

Single agent (Agency selection; REI still merges when enabled):

```bash
/path/to/agency-agents/scripts/install.sh --tool cursor --with-rei --agent frontend-developer
```

Dry run (shows agents + router + skills/commands + REI plan):

```bash
/path/to/agency-agents/scripts/install.sh --tool cursor --division engineering --dry-run --no-interactive
```

Symlink mode (Git Bash / macOS / Linux):

```bash
/path/to/agency-agents/scripts/install.sh --tool cursor --division engineering --link
```

Env / path overrides (config root = parent of `agents/` / `rules/`):

- `CURSOR_CONFIG_DIR` (preferred)
- Legacy: `CURSOR_AGENTS_DIR` or `CURSOR_RULES_DIR` (normalized to `.cursor` root)
- `--path <dir>` — same meaning (Cursor config root)

## Activate a subagent

In Cursor, use Task / subagents with the agent slug (`name` in frontmatter), e.g.
`frontend-developer`. Or run `/agency` to list/activate from the catalog.

See also the Agency section in `AGENTS.md` after install.

## Migration from persona `.mdc` rules

Older installs copied one `.mdc` rule per agent into `.cursor/rules/`. That path
is retired:

1. Remove old Agency persona rules: delete `.cursor/rules/*.mdc` except
   `agency-router.mdc` (or wipe `rules/` then reinstall).
2. Re-run `convert.sh --tool cursor` then `install.sh --tool cursor` with a
   narrow `--division` / `--agent` selection.
3. Prefer subagents under `.cursor/agents/` over `@rule` references.

Selective reinstall does **not** prune previously installed `.cursor/agents/*`
slugs outside the new selection — remove stale agent files manually if you
narrow the roster.

## Regenerate

```bash
./scripts/convert.sh --tool cursor
```

Output staging layout:

```text
integrations/cursor/
  agents/<division>/<slug>.md
  skills/<division>/<slug>/{SKILL.md,reference.md?}   # conditional
  rules/agency-router.mdc                             # only rule
  commands/agency.md
  catalog/roster.json
  catalog/by-division/<division>.md
  AGENTS.md.template
  README.md
```

## Lint (optional)

```bash
./scripts/check-cursor-pack.sh
```
