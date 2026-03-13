# 🔌 多工具集成 (Integrations)

本目录包含 The Agency 的 61 位 AI 智能体，并已转换为与主流编程智能体工具兼容的格式。

## 受支持的工具

- **[Claude Code](#claude-code)** — `.md` 智能体，直接使用仓库即可
- **[Antigravity](#antigravity)** — 每个智能体在 `antigravity/` 下对应一个 `SKILL.md`
- **[Gemini CLI](#gemini-cli)** — 在 `gemini-cli/` 下提供扩展及 `SKILL.md` 文件
- **[OpenCode](#opencode)** — 在 `opencode/` 下提供 `.md` 智能体文件
- **[Cursor](#cursor)** — 在 `cursor/` 下提供 `.mdc` 规则文件
- **[Aider](#aider)** — 在 `aider/` 下提供 `CONVENTIONS.md`
- **[Windsurf](#windsurf)** — 在 `windsurf/` 下提供 `.windsurfrules`

## 快速安装

```bash
# 为所有检测到的工具自动安装
./scripts/install.sh

# 为特定工具安装
./scripts/install.sh --tool antigravity
./scripts/install.sh --tool gemini-cli
./scripts/install.sh --tool cursor
./scripts/install.sh --tool aider
./scripts/install.sh --tool windsurf
./scripts/install.sh --tool claude-code
```

## 重新生成集成文件

如果你添加或修改了智能体，请重新生成所有集成文件：

```bash
./scripts/convert.sh
```

---

## Claude Code

The Agency 最初是为 Claude Code 设计的。智能体无需转换即可直接运行。

```bash
cp -r <category>/*.md ~/.claude/agents/
# 或者一次性安装全部：
./scripts/install.sh --tool claude-code
```

详见 [claude-code/README.md](claude-code/README.md)。

---

## Antigravity

技能将安装到 `~/.gemini/antigravity/skills/`。每位智能体都会成为一个独立的技能，并以 `agency-` 为前缀以避免命名冲突。

```bash
./scripts/install.sh --tool antigravity
```

详见 [antigravity/README.md](antigravity/README.md)。

---

## Gemini CLI

智能体被打包为 Gemini CLI 扩展，并包含独立的技能文件。扩展将安装到 `~/.gemini/extensions/agency-agents/`。

```bash
./scripts/install.sh --tool gemini-cli
```

详见 [gemini-cli/README.md](gemini-cli/README.md)。

---

## Cursor

每位智能体都会成为一个 `.mdc` 规则文件。规则是项目范围的 —— 请在你的项目根目录下运行安装程序。

```bash
cd /your/project && /path/to/agency-agents/scripts/install.sh --tool cursor
```

详见 [cursor/README.md](cursor/README.md)。

---

## Aider

所有智能体会合并为一个单一的 `CONVENTIONS.md` 文件，当该文件位于你的项目根目录时，Aider 会自动读取。

```bash
cd /your/project && /path/to/agency-agents/scripts/install.sh --tool aider
```

详见 [aider/README.md](aider/README.md)。

---

## Windsurf

所有智能体会合并为一个单一的 `.windsurfrules` 文件，用于你的项目根目录。

```bash
cd /your/project && /path/to/agency-agents/scripts/install.sh --tool windsurf
```

详见 [windsurf/README.md](windsurf/README.md)。
