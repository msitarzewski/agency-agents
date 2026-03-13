# Antigravity 集成

将全部 61 位 Agency 智能体安装为 Antigravity 技能。每位智能体均以 `agency-` 为前缀，以避免与现有技能冲突。

## 安装

```bash
./scripts/install.sh --tool antigravity
```

这将把文件从 `integrations/antigravity/` 复制到 `~/.gemini/antigravity/skills/`。

## 激活技能

在 Antigravity 中，通过其标识符 (Slug) 激活智能体：

```
Use the agency-frontend-developer skill to review this component.
```

可用的标识符遵循 `agency-<agent-name>` 模式，例如：
- `agency-frontend-developer`
- `agency-backend-architect`
- `agency-reality-checker`
- `agency-growth-hacker`

## 重新生成

修改智能体后，重新生成技能文件：

```bash
./scripts/convert.sh --tool antigravity
```

## 文件格式

每个技能都是一个包含 Antigravity 兼容 Frontmatter 的 `SKILL.md` 文件：

```yaml
---
name: agency-frontend-developer
description: 专家级前端开发工程师，专注于...
risk: low
source: community
date_added: '2026-03-08'
---
```
