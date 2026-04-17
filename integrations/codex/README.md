# Codex Integration

The Agency can be installed into Codex as a collection of skills. Each agent is
converted into its own `SKILL.md` bundle under `~/.codex/skills/agency-<slug>/`.

## Install

From a fresh clone, generate the Codex skill folders first:

```bash
./scripts/convert.sh --tool codex
./scripts/install.sh --tool codex
```

This copies the generated skill folders from `integrations/codex/` into
`~/.codex/skills/`.

## Usage

Restart Codex after installation, then invoke a skill by name in your prompt:

```text
Use the agency-frontend-developer skill to review this React component.
```

You can also ask Codex to pick the closest Agency specialist for a task and
then proceed with that skill’s workflow.

## Regenerate After Changes

If you add or edit agents, regenerate the Codex skill folders:

```bash
./scripts/convert.sh --tool codex
```
