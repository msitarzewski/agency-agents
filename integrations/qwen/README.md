# Qwen Code Integration

Qwen Code uses project-scoped `.md` SubAgent files in `.qwen/agents/`.

The generated files come from `scripts/convert.sh --tool qwen`, which writes one
SubAgent Markdown file per agency agent into `integrations/qwen/agents/`.

## Generate

From the repository root:

```bash
./scripts/convert.sh --tool qwen
```

## Install

Run the installer from your target project root:

```bash
cd /your/project && /path/to/agency-agents/scripts/install.sh --tool qwen
```

This copies the generated SubAgent files into:

```text
.qwen/agents/
```

## Refresh in Qwen Code

After installation:

- run `/agents manage` in Qwen Code to refresh the agent list, or
- restart the current Qwen Code session

## Notes

- Qwen Code is project-scoped, not home-scoped
- The generated Qwen files use minimal frontmatter: `name`, `description`, and
  optional `tools`
- If you update agents in this repo, regenerate the Qwen output before
  reinstalling
