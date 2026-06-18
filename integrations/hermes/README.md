# Hermes Agent Integration

Converts all Agency agents into Hermes Agent skills. Each source agent becomes
one standalone `SKILL.md` file containing the minimal Hermes-required fields:
`name` and `description`, with the full agent body preserved.

## Installation

### Prerequisites

- [Hermes Agent](https://hermes-agent.nousresearch.com/) installed

### Convert And Install

```bash
# Generate integration files (required on fresh clone)
./scripts/convert.sh --tool hermes

# Install agents as Hermes skills
./scripts/install.sh --tool hermes

# Or install specific divisions only
./scripts/install.sh --tool hermes --division engineering,security
```

This installs agents to `~/.hermes/skills/<division>/<slug>/SKILL.md`.

## Usage in Hermes

Activate any agent as a skill in your Hermes session:

```
/skill frontend-developer
```

Or reference agents by name in your prompt — Hermes auto-matches skills by description:

```
Use the Frontend Developer skill to review this React component.
```

To install selectively:

```bash
# Install only engineering and marketing agents
./scripts/install.sh --tool hermes --division engineering,marketing

# Install specific agents
./scripts/install.sh --tool hermes --agent frontend-developer,backend-architect

# Symlink instead of copy (updates propagate)
./scripts/install.sh --tool hermes --link
```

After installation, run `/reload-skills` in Hermes or restart the agent to
activate new skills.

## Generated Format

Each generated skill lives in:

```text
integrations/hermes/<slug>/SKILL.md
```

The mapping:
- `name` is slugified from the source frontmatter name
- `description` is copied from the source frontmatter unchanged
- The full Markdown body is preserved as the skill instructions

Skills are installed under `~/.hermes/skills/` organized by their source
division (e.g., `~/.hermes/skills/engineering/frontend-developer/SKILL.md`).

## Regenerating

When agents are added or modified, regenerate:

```bash
./scripts/convert.sh --tool hermes
```
