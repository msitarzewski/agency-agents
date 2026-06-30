# Grok Integration

Packages Agency agents as Grok skills. Each source agent becomes one
`SKILL.md` file under `integrations/grok/agency-<slug>/`.

Grok discovers skills from `~/.grok/skills/` and project-local `.grok/skills/`.
This integration only installs local skill files; it does not use the xAI API
or require an API key.

## Generate

```bash
./scripts/convert.sh --tool grok
```

## Install

Install user-wide:

```bash
./scripts/install.sh --tool grok
```

Install into a project-local `.grok/skills` directory:

```bash
cd /your/project
/path/to/agency-agents/scripts/install.sh --tool grok --path .grok/skills
```

## Usage

Reference an installed skill by name in Grok:

```text
Use the agency-backend-architect skill to review this API design.
```

If Grok was already running, restart the session so it discovers newly installed
skills.
