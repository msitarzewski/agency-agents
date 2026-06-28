# ZCode Integration

Converts The Agency's agents into ZCode **Skills** — native, project-scoped or user-scoped rules that ZCode discovers and invokes automatically based on conversation context.

## Install

### Option 1: Project-scoped (recommended for team sharing)

```bash
# From your project root
cd /path/to/your/project
/path/to/agency-agents/scripts/install.sh --tool zcode
```

This creates `.zcode/skills/<agent-name>/SKILL.md` files in your project.

### Option 2: User-scoped (personal skills everywhere)

```bash
# Install to your home directory
/path/to/agency-agents/scripts/install.sh --tool zcode --scope user
```

This creates `~/.agents/skills/<agent-name>/SKILL.md` files.

## How It Works

ZCode discovers skills in these directories (highest priority first):

- `<project>/.zcode/skills/<name>/SKILL.md`
- `<project>/.agents/skills/<name>/SKILL.md`
- `~/.zcode/skills/<name>/SKILL.md`
- `~/.agents/skills/<name>/SKILL.md`

Each skill is a directory containing a `SKILL.md` with YAML frontmatter and markdown body:

```yaml
---
name: backend-architect
description: Senior backend architect specializing in scalable system design...
---

## 🧠 Your Identity & Memory
...
```

## Triggering

Unlike Cursor's `@agent-name` or Claude Code's explicit activation, **ZCode skills trigger automatically** via semantic matching on the `description` field.

When you say:
- "帮我设计一个高并发系统" → ZCode loads `backend-architect`
- "帮我写一个React组件" → ZCode loads `frontend-developer`
- "检查这个API的安全性" → ZCode loads `security-appsec-engineer`

No manual activation needed — ZCode matches your intent to the right agent.

## Regenerate

```bash
./scripts/convert.sh --tool zcode
```

Output goes to `integrations/zcode/skills/`.

## Format Details

| Field | Source | Notes |
|-------|--------|-------|
| `name` | slugified agent `name` | Must match directory name (kebab-case) |
| `description` | agent `description` | Primary trigger signal for ZCode |
| body | agent body (minus frontmatter) | Full identity, mission, rules, deliverables |

Color, emoji, and vibe fields from the source are **not used** in ZCode's skill format (they can be added to the body if desired).

## Differences from Other Tools

| | ZCode | Cursor | Claude Code |
|---|---|---|---|
| **Activation** | Automatic (semantic match) | `@agent-name` or `alwaysApply` | Explicit request |
| **Scope** | Project or user | Project only | User only |
| **Format** | `SKILL.md` in directory | `.mdc` file | `.md` file |
| **Trigger** | `description` field | `globs` + `alwaysApply` | Manual invocation |

## Support

- [agency-agents issues](https://github.com/msitarzewski/agency-agents/issues)
- [ZCode documentation](https://zcode.ai)
