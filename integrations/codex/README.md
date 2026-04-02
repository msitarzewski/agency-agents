# Codex Integration

Agency agents are converted into Codex skills (`SKILL.md`) and installed to:

`~/.codex/skills/agency-<slug>/SKILL.md`

## Install

```bash
# Generate Codex skill files (required on fresh clone)
./scripts/convert.sh --tool codex

# Install to ~/.codex/skills/
./scripts/install.sh --tool codex
```

## Usage

In Codex, call the installed skill by name:

```text
Use the agency-frontend-developer skill to review this component.
```
