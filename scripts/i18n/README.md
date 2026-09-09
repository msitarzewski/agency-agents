# 🇨🇳 Chinese (zh-CN) Localization

Localize agent `name` and `description` fields in YAML frontmatter to Simplified Chinese. This makes agent names readable in Copilot Chat's agent picker for Chinese-speaking users.

## Files

| File | Description |
|------|-------------|
| `agent-names-zh.json` | Mapping of English agent names → Chinese translations (130+ entries) |
| `localize-agents-zh.ps1` | PowerShell script that reads the JSON and updates installed agent files |

## Usage

After installing agents with `install.sh --tool copilot`:

```powershell
# Localize agent names to Chinese
powershell -ExecutionPolicy Bypass -File scripts/i18n/localize-agents-zh.ps1
```

By default, the script processes:
- `%USERPROFILE%\.github\agents\`
- `%USERPROFILE%\.copilot\agents\`

Pass custom paths if needed:

```powershell
powershell -File scripts/i18n/localize-agents-zh.ps1 -TargetDirs @("C:\custom\path\agents")
```

## How It Works

1. Reads `agent-names-zh.json` (UTF-8 encoded) for the translation map
2. For each `.md` file in the target directories:
   - Extracts the `name:` field from YAML frontmatter
   - Looks up the Chinese translation
   - Replaces `name:` and `description:` fields
   - Writes back as UTF-8

## Result

Before:
```yaml
---
name: Security Engineer
description: Threat modeling, secure code review, security architecture
---
```

After:
```yaml
---
name: 安全工程师
description: 威胁建模、安全代码审查与应用安全架构专家
---
```

## Notes

- Only modifies **installed copies** (in `~/.github/agents/`), not source files
- Re-run after each `install.sh` update (which overwrites with English originals)
- JSON file is the single source of truth for translations — add new agents there
- Script is pure ASCII (avoids PowerShell encoding issues); all Chinese text lives in the JSON
