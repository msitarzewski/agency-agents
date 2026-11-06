# Kilo Code Integration

> **❌ Don't do this:**
>
> ```bash
> # WRONG — the source frontmatter is not Kilo's agent contract
> cp agency-agents/engineering/*.md .kilo/agents/
> ```
>
> **✅ Do this instead:**
>
> ```bash
> /path/to/agency-agents/scripts/install.sh --tool kilocode
> ```
>
> The installer converts source color names to `#RRGGBB` hex and strips
> incompatible fields automatically.

Kilo Code agents are `.md` files with YAML frontmatter stored in `.kilo/agents/`. The filename (minus
`.md`) becomes the agent name, so `frontend-developer.md` defines the
`frontend-developer` agent. The converter maps named colors to hex codes and adds
`mode: subagent` so agents are invoked on-demand via `@agent-name` or automatic delegation via `task` tool.

## Install

```bash
# Run from your project root
cd /your/project
/path/to/agency-agents/scripts/install.sh --tool kilocode
```

This creates `.kilo/agents/<slug>.md` files in your project directory.

## Activate an Agent

In Kilo Code, invoke a subagent with the `@` prefix:

```
@frontend-developer help build this component.
```

```
@reality-checker review this PR.
```

List what Kilo loaded with `kilo agent list`. After installing in a running session, use `/reload` to reload the installed agents.

## Agent Format

Each generated agent file contains:

```yaml
---
description: Expert frontend developer specializing in modern web technologies...
mode: subagent
color: '#00FFFF'
---
```

- The filename defines the agent name; `name` frontmatter is intentionally omitted.
- **mode: subagent** — agent is available on-demand, not shown as a
  primary agent in the picker
- **color** — hex code (named colors from source files are converted automatically)

## Project vs Global

Agents in `.kilo/agents/` are **project-scoped**. To make them available
globally across all projects, first generate the agent files, then install
with `--path`:

```bash
cd /path/to/agency-agents
./scripts/convert.sh --tool kilocode
./scripts/install.sh --tool kilocode --path "$HOME/.config/kilo/agents"
```

## Regenerate

```bash
./scripts/convert.sh --tool kilocode
```
