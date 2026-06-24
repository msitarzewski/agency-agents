# Kiro CLI Integration

Converts all Agency agents into Kiro CLI agent JSON files. Each source agent
becomes one standalone `.json` file containing the required Kiro fields: `name`,
`description`, `prompt`, and `tools`.

## Installation

### Prerequisites

- [Kiro CLI](https://kiro.dev) installed (`kiro` or `kiro-cli` binary)

### Convert And Install

```bash
# Generate integration files (required on fresh clone)
./scripts/convert.sh --tool kiro

# Install agents
./scripts/install.sh --tool kiro
```

This copies generated agent files to `~/.kiro/agents/`.

## Generated Format

Each generated file lives in:

```text
integrations/kiro/agents/<slug>.json
```

The mapping:

- `name` — slug derived from the source frontmatter name
- `description` — copied from source frontmatter unchanged
- `prompt` — full Markdown body as the system prompt
- `tools` — default set of Kiro built-in tools for general-purpose agents

## Usage

After installation, activate agents in Kiro CLI:

```bash
# List installed agents
kiro-cli agent list

# Switch to an agent in chat
/agent swap frontend-developer

# Or set as default
kiro-cli agent set-default frontend-developer
```

## Regenerate

After modifying source agents:

```bash
./scripts/convert.sh --tool kiro
./scripts/install.sh --tool kiro
```

## Troubleshooting

### Kiro integration not found

Generate the Kiro artifacts before installing:

```bash
./scripts/convert.sh --tool kiro
```

### Kiro not detected

Make sure `kiro` or `kiro-cli` is in your PATH, or that `~/.kiro/` already exists:

```bash
which kiro || which kiro-cli
kiro --help
```
