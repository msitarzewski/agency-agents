# Mistral Vibe Integration

Mistral Vibe uses two files per agent:
- A TOML configuration file (`~/.vibe/agents/<slug>.toml`)
- A Markdown prompt file (`~/.vibe/prompts/<slug>.md`)

The generated files come from `scripts/convert.sh --tool vibe`, which writes
one TOML agent configuration and one Markdown prompt file per agency agent
into `integrations/vibe/agents/` and `integrations/vibe/prompts/` respectively.

## Generate

From the repository root:

```bash
./scripts/convert.sh --tool vibe
```

## Install

Run the installer from your target directory:

```bash
cd /your/project && /path/to/agency-agents/scripts/install.sh --tool vibe
```

This copies the generated files into:

```text
~/.vibe/agents/<slug>.toml
~/.vibe/prompts/<slug>.md
```

You can override the destination using the `VIBE_HOME` environment variable:

```bash
VIBE_HOME=~/.config/vibe ./scripts/install.sh --tool vibe
```

## Generated Format

Each generated agent pair lives in:

```text
integrations/vibe/agents/<slug>.toml
integrations/vibe/prompts/<slug>.md
```

### Agent TOML File

The minimal Vibe agent configuration:

```toml
agent_type = "agent"
system_prompt_id = "<slug>"
```

Users can specify `active_model` in their agent TOML files or rely on their
Vibe configuration default model.

### Prompt Markdown File

The prompt file contains:
- A title header with the agent name
- The agent description
- The full Markdown body from the source agent

## Usage

After installation, reference agents in Mistral Vibe by their system prompt ID
(which matches the filename slug).

Example:
```text
Use the Code Reviewer agent to analyze this pull request.
```

## Filtering

Install only specific divisions or agents:

```bash
# Install only agents from Division 1
./scripts/install.sh --tool vibe --division 1

# Install only the code-reviewer agent
./scripts/install.sh --tool vibe --agent code-reviewer
```

## Regenerate

After modifying source agents:

```bash
./scripts/convert.sh --tool vibe
./scripts/install.sh --tool vibe
```

## Troubleshooting

### Mistral Vibe not detected

Make sure `vibe` is in your PATH, or that `~/.vibe/` already exists:

```bash
which vibe
vibe --version
```

### Integration files not generated

Generate the Vibe artifacts before installing:

```bash
./scripts/convert.sh --tool vibe
```
