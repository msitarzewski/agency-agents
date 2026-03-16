# Codex Integration

Codex multi-agent support uses project-scoped role definitions in `.codex/`.
The Agency converter generates:

- `.codex/config.toml` with `[features] multi_agent = true`
- one `[agents.<slug>]` registration per agent
- `.codex/agents/<slug>.toml` role files with `developer_instructions`

This matches the official Codex multi-agent configuration model:
https://developers.openai.com/codex/multi-agent/

## Install

```bash
# Run from your project root
cd /your/project
/path/to/agency-agents/scripts/convert.sh --tool codex
/path/to/agency-agents/scripts/install.sh --tool codex
```

If your project does not already have `.codex/config.toml`, the installer
copies the generated config directly.

If `.codex/config.toml` already exists, the installer:

- copies all Agency role files into `.codex/agents/`
- leaves your existing `.codex/config.toml` unchanged
- writes `.codex/agency-agents.snippet.toml` for manual merging

## Generated Format

Example `.codex/config.toml`:

```toml
[features]
multi_agent = true

[agents]

[agents.frontend-developer]
description = "Expert frontend developer specializing in modern web technologies..."
config_file = "agents/frontend-developer.toml"
```

Example `.codex/agents/frontend-developer.toml`:

```toml
developer_instructions = '''
# Frontend Developer Agent Personality

You are **Frontend Developer** ...
'''
```

## Usage

Once installed, ask Codex to use the generated roles explicitly:

```text
Review this branch against main. Use frontend-developer to inspect UI regressions and reality-checker to assess release readiness.
```

You can also ask Codex to fan work out across multiple roles in parallel when
the `multi_agent` feature is enabled.

## Regenerate

```bash
./scripts/convert.sh --tool codex
```
