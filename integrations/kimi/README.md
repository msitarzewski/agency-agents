# Kimi Code CLI Integration

Converts all Agency agents into Kimi Code CLI agent specifications. Each agent
becomes a directory containing `agent.yaml` (agent spec) and `system.md` (system
prompt).

## Installation

### Prerequisites

- [Kimi Code CLI](https://github.com/MoonshotAI/kimi-cli) installed

### Install

```bash
# Generate integration files (required on fresh clone)
./scripts/convert.sh --tool kimi

# Install agents
./scripts/install.sh --tool kimi
```

This copies agents to `~/.config/kimi/agents/`.

## Usage

### Activate an Agent

Use the `--agent-file` flag to load a specific agent:

```bash
kimi --agent-file ~/.config/kimi/agents/frontend-developer/agent.yaml
```

### In a Project

```bash
cd /your/project
kimi --agent-file ~/.config/kimi/agents/frontend-developer/agent.yaml \
     --work-dir /your/project \
     "Review this React component for performance issues"
```

### List Installed Agents

```bash
ls ~/.config/kimi/agents/
```

## Agent Structure

Each agent directory contains:

```
~/.config/kimi/agents/frontend-developer/
├── agent.yaml    # Agent specification (tools, subagents)
└── system.md     # System prompt with personality and instructions
```

### agent.yaml format

```yaml
version: 1
agent:
  name: frontend-developer
  extend: default  # Inherits from Kimi's built-in default agent
  system_prompt_path: ./system.md
  tools:
    - "kimi_cli.tools.shell:Shell"
    - "kimi_cli.tools.file:ReadFile"
    # ... all default tools
```

## Regenerate

After modifying source agents:

```bash
./scripts/convert.sh --tool kimi
./scripts/install.sh --tool kimi
```

## Troubleshooting

### Agent file not found

Ensure you've run `convert.sh` before `install.sh`:

```bash
./scripts/convert.sh --tool kimi
```

### Kimi CLI not detected

Make sure `kimi` is in your PATH:

```bash
which kimi
kimi --version
```

### Invalid YAML

Validate the generated files:

```bash
python3 -c "import yaml; yaml.safe_load(open('integrations/kimi/frontend-developer/agent.yaml'))"
```
