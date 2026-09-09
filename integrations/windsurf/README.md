# Windsurf Integration

The full Agency roster is consolidated into a single `.windsurfrules` file.
Rules are **project-scoped** — install them from your project root.

## Install

```bash
# Run from your project root
cd /your/project
/path/to/agency-agents/scripts/install.sh --tool windsurf
```

## Activate an Agent

In Windsurf, reference an agent by name in your prompt:

```
Use the Frontend Developer agent to build this component.
```

## Regenerate

```bash
./scripts/convert.sh --tool windsurf
```
