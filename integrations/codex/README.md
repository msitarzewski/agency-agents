# Codex Integration

All Agency agents are consolidated into a single `AGENTS.md` file.
Codex can read this file when it is present in your project root.

## Install

```bash
# Run from your project root
cd /your/project
/path/to/agency-agents/scripts/install.sh --tool codex
```

## Activate an Agent

In your Codex session, reference the agent by name:

```
Use the Frontend Developer agent to refactor this component.
```

```
Apply the Reality Checker agent to verify this is production-ready.
```

## Regenerate

```bash
./scripts/convert.sh --tool codex
```
