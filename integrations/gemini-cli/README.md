# Gemini CLI Integration

Packages all 61 Agency agents as a Gemini CLI extension. The extension
installs to `~/.gemini/extensions/agency-agents/`.

## Install

```bash
# Generate the Gemini CLI integration files first
./scripts/convert.sh --tool gemini-cli

# Then install the extension
./scripts/install.sh --tool gemini-cli
```

## Activate a Skill

In Gemini CLI, reference an agent by name:

```
Use the frontend-developer skill to help me build this UI.
```

## Extension Structure

```
~/.gemini/extensions/agency-agents/
  gemini-extension.json
  skills/
    frontend-developer/SKILL.md
    backend-architect/SKILL.md
    reality-checker/SKILL.md
    ...
```

## Regenerate

```bash
./scripts/convert.sh --tool gemini-cli
```
