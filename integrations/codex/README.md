# Codex Integration

This integration exports The Agency as a local Codex plugin.

## What gets generated

- `.codex-plugin/plugin.json`
- `skills/<agent-slug>/SKILL.md`
- `references/AGENTS-MANIFEST.md`
- `assets/agency-agents.svg`

## Generate

```bash
./scripts/convert.sh --tool codex
```

## Install

```bash
./scripts/install.sh --tool codex
```

By default the plugin is installed to:

```text
~/.codex/plugins/agency-agents/
```

If `CODEX_HOME` is set, the installer targets:

```text
$CODEX_HOME/plugins/agency-agents/
```

## Usage

In Codex, route tasks through the manifest at:

```text
references/AGENTS-MANIFEST.md
```

Then open the matching imported skill in:

```text
skills/<agent-slug>/SKILL.md
```

## Important note

This format exposes Agency Agents as Codex skills inside a local plugin.
It does **not** claim native Codex subagent parity with the OpenClaw runtime format.
