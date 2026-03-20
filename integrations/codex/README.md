# Codex Integration

Packages Agency agents as Codex skills (`SKILL.md` per agent) and installs
them to `${CODEX_HOME:-~/.codex}/skills/`.

## Install

```bash
# Generate Codex integration files
./scripts/convert.sh --tool codex

# Install generated skills to Codex
./scripts/install.sh --tool codex
```

## Activate a Skill

In Codex, reference an agent skill by name:

```
Use the $agency-frontend-developer skill to help me build this UI.
```

```
Use the $agency-reality-checker skill to verify this is production-ready.
```

## Generated Structure

```
integrations/codex/skills/
  agency-frontend-developer/SKILL.md
  agency-backend-architect/SKILL.md
  agency-reality-checker/SKILL.md
  ...
```

## Regenerate

```bash
./scripts/convert.sh --tool codex
```
