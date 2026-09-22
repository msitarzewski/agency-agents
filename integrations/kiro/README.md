# Kiro Integration

Converts all Agency agents into [Kiro IDE](https://kiro.dev) custom agent files.
Each agent becomes a `.md` file with YAML frontmatter that Kiro loads from
`~/.kiro/agents/` (global) or `.kiro/agents/` (project-scoped).

## Installation

### Prerequisites

- [Git Bash](https://git-scm.com/downloads) or WSL (Windows), or any bash shell on macOS/Linux

### Generate + install

```bash
# Step 1 — generate integration files (required on fresh clone)
./scripts/convert.sh --tool kiro

# Step 2 — install to ~/.kiro/agents/
./scripts/install.sh --tool kiro
```

### Regenerate after updates

```bash
./scripts/convert.sh --tool kiro
```

## Usage

1. Open Kiro IDE
2. In the chat panel, click the agent picker (the current agent name in the header)
3. Select any Agency agent from the list
4. The full agent persona and workflow loads automatically

## Agent structure

Each agent is a single `.md` file with YAML frontmatter:

```
~/.kiro/agents/
├── frontend-developer.md
├── backend-architect.md
└── ...
```

```markdown
---
name: 'frontend-developer'
description: 'Expert frontend developer specializing in React/Vue/Angular...'
tools: ["read", "write", "shell", "web"]
---

# Frontend Developer

<full agent persona and instructions>
```

## Scopes

| Location | Scope |
|----------|-------|
| `~/.kiro/agents/<slug>.md` | Global — available in every workspace |
| `.kiro/agents/<slug>.md` | Project — local to one project only |

## Troubleshooting

### Agent not appearing in Kiro

- Confirm the file is in `~/.kiro/agents/` or `.kiro/agents/`
- Reload the Kiro window (`Ctrl+Shift+P` → **Reload Window**)
- Check the file has valid YAML frontmatter (the `---` delimiters must be present)

### convert.sh not found / permission denied

```bash
chmod +x scripts/convert.sh
./scripts/convert.sh --tool kiro
```
