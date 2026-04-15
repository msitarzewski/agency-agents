# 🔌 Integrations

This directory contains The Agency integrations and converted formats for
supported agentic coding tools.

## Supported Tools

- **[Claude Code](#claude-code)** — `.md` agents, use the repo directly
- **[GitHub Copilot](#github-copilot)** — `.md` agents, use the repo directly
- **[Antigravity](#antigravity)** — `SKILL.md` per agent in `antigravity/`
- **[Gemini CLI](#gemini-cli)** — extension + `SKILL.md` files in `gemini-cli/`
- **[OpenCode](#opencode)** — `.md` agent files in `opencode/`
- **[OpenClaw](#openclaw)** — `SOUL.md` + `AGENTS.md` + `IDENTITY.md` workspaces
- **[Cursor](#cursor)** — `.mdc` rule files in `cursor/`
- **[Aider](#aider)** — `CONVENTIONS.md` in `aider/`
- **[Windsurf](#windsurf)** — `.windsurfrules` in `windsurf/`
- **[Kimi Code](#kimi-code)** — YAML agent specs in `kimi/`
- **[Qwen Code](#qwen-code)** — project-scoped `.md` SubAgents in `.qwen/agents/`

## Quick Install

```bash
# Install for all detected tools automatically
./scripts/install.sh

# Install a specific home-scoped tool
./scripts/install.sh --tool antigravity
./scripts/install.sh --tool copilot
./scripts/install.sh --tool openclaw
./scripts/install.sh --tool claude-code

# Gemini CLI needs generated integration files on a fresh clone
./scripts/convert.sh --tool gemini-cli
./scripts/install.sh --tool gemini-cli

# Qwen Code also needs generated SubAgent files on a fresh clone
./scripts/convert.sh --tool qwen
./scripts/install.sh --tool qwen
```

If you install OpenClaw and the gateway is already running, restart it after installation:

```bash
openclaw gateway restart
```

For project-scoped tools such as OpenCode, Cursor, Aider, Windsurf, and Qwen
Code, run
the installer from your target project root as shown in the tool-specific
sections below.

## Regenerating Integration Files

If you add or modify agents, regenerate all integration files:

```bash
./scripts/convert.sh
```

---

## Claude Code

The Agency was originally designed for Claude Code. Agents work natively
without conversion.

```bash
cp -r <category>/*.md ~/.claude/agents/
# or install everything at once:
./scripts/install.sh --tool claude-code
```

See [claude-code/README.md](claude-code/README.md) for details.

---

## GitHub Copilot

The Agency also works natively with GitHub Copilot. Agents can be copied
directly into `~/.github/agents/` and `~/.copilot/agents/` without conversion.

```bash
./scripts/install.sh --tool copilot
```

See [github-copilot/README.md](github-copilot/README.md) for details.

---

## Antigravity

Skills are installed to `~/.gemini/antigravity/skills/`. Each agent becomes
a separate skill prefixed with `agency-` to avoid naming conflicts.

```bash
./scripts/install.sh --tool antigravity
```

See [antigravity/README.md](antigravity/README.md) for details.

---

## Gemini CLI

Agents are packaged as a Gemini CLI extension with individual skill files.
The extension is installed to `~/.gemini/extensions/agency-agents/`.
Because the Gemini manifest and skill folders are generated artifacts, run
`./scripts/convert.sh --tool gemini-cli` before installing from a fresh clone.

```bash
./scripts/convert.sh --tool gemini-cli
./scripts/install.sh --tool gemini-cli
```

See [gemini-cli/README.md](gemini-cli/README.md) for details.

---

## OpenCode

Each agent becomes a project-scoped `.md` file in `.opencode/agents/`.

```bash
cd /your/project && /path/to/agency-agents/scripts/install.sh --tool opencode
```

See [opencode/README.md](opencode/README.md) for details.

---

## OpenClaw

Each agent becomes an OpenClaw workspace containing `SOUL.md`, `AGENTS.md`,
and `IDENTITY.md`.

Before installing, generate the OpenClaw workspaces:

```bash
./scripts/convert.sh --tool openclaw
```

Then install them:

```bash
./scripts/install.sh --tool openclaw
```

See [openclaw/README.md](openclaw/README.md) for details.

---

## Cursor

Each agent becomes a `.mdc` rule file. Rules are project-scoped — run the
installer from your project root.

```bash
cd /your/project && /path/to/agency-agents/scripts/install.sh --tool cursor
```

See [cursor/README.md](cursor/README.md) for details.

---

## Aider

All agents are consolidated into a single `CONVENTIONS.md` file that Aider
reads automatically when present in your project root.

```bash
cd /your/project && /path/to/agency-agents/scripts/install.sh --tool aider
```

See [aider/README.md](aider/README.md) for details.

---

## Windsurf

All agents are consolidated into a single `.windsurfrules` file for your
project root.

```bash
cd /your/project && /path/to/agency-agents/scripts/install.sh --tool windsurf
```

See [windsurf/README.md](windsurf/README.md) for details.

---

## Kimi Code

Each agent is converted to a Kimi Code CLI agent specification (YAML format with
separate system prompt files). Agents are installed to `~/.config/kimi/agents/`.

Because the Kimi agent files are generated from the source Markdown, run
`./scripts/convert.sh --tool kimi` before installing from a fresh clone.

```bash
./scripts/convert.sh --tool kimi
./scripts/install.sh --tool kimi
```

### Usage

After installation, use an agent with the `--agent-file` flag:

```bash
kimi --agent-file ~/.config/kimi/agents/frontend-developer/agent.yaml
```

Or in a specific project:

```bash
cd /your/project
kimi --agent-file ~/.config/kimi/agents/frontend-developer/agent.yaml \
     --work-dir /your/project
```

See [kimi/README.md](kimi/README.md) for details.

---

## Qwen Code

Each agent becomes a project-scoped `.md` SubAgent file in `.qwen/agents/`.

From a fresh clone, generate the Qwen files first:

```bash
./scripts/convert.sh --tool qwen
```

Then install them from your project root:

```bash
cd /your/project && /path/to/agency-agents/scripts/install.sh --tool qwen
```

See [qwen/README.md](qwen/README.md) for details.
