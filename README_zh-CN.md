# 🎭 The Agency：随时可用的 AI 专家团队

[English](README.md) | 简体中文

> **把一整支 AI 代理团队放进口袋里。** 从前端开发、产品策略、增长营销，到安全审计、GIS、游戏开发与客户支持，每个代理都像一位有明确专长、工作流和交付标准的专家。

[![GitHub stars](https://img.shields.io/github/stars/msitarzewski/agency-agents?style=social)](https://github.com/msitarzewski/agency-agents)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://makeapullrequest.com)
[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-pink?logo=github)](https://github.com/sponsors/msitarzewski)
[![Download the app](https://img.shields.io/github/v/release/msitarzewski/agency-agents-app?label=Download%20app&color=2563eb)](https://github.com/msitarzewski/agency-agents-app/releases/latest)

> ### 🆕 现在也有桌面应用
>
> **[Agency Agents](https://agencyagents.app)** 是适用于 **macOS、Linux 和 Windows** 的原生应用，可以浏览完整代理库，并一键安装到 Claude Code、Cursor、Codex、Gemini、Osaurus 等工具中。无需克隆仓库，也不需要手动运行脚本；应用会自动更新。
>
> **→ [下载最新版本](https://github.com/msitarzewski/agency-agents-app/releases/latest) · [agencyagents.app](https://agencyagents.app)**

---

## 🚀 这是什么？

**The Agency** 是一组持续增长的 AI 专家代理。它们不是泛泛的“角色扮演提示词”，而是带有明确身份、工作方式、质量标准和交付物的可复用代理。

每个代理通常包含：

- **专业领域**：针对具体工作场景设计，而不是通用模板。
- **鲜明性格**：有自己的沟通风格、判断偏好和协作方式。
- **交付导向**：强调真实代码、流程、文档、策略或可衡量结果。
- **可投入生产**：包含经过实践打磨的流程、检查点和成功指标。

你可以把它理解成：为项目临时组建一支 AI 专家小队，每位成员都知道自己负责什么、如何交付，以及什么时候该把问题交给别的专家。

---

## ⚡ 快速开始

### 方式 1：安装桌面应用（推荐）

最简单的方式是直接安装 [**Agency Agents**](https://agencyagents.app)。它会帮你浏览、筛选并安装代理到常见 AI 编程工具中。

**[⬇ 下载最新版本](https://github.com/msitarzewski/agency-agents-app/releases/latest)**

macOS 用户也可以使用 Homebrew：

```bash
brew install --cask msitarzewski/agency-agents/agency-agents
```

### 方式 2：在 Claude Code 中使用

```bash
# 将所有代理安装到 Claude Code 目录
./scripts/install.sh --tool claude-code

# 或者只复制某个分类
cp engineering/*.md ~/.claude/agents/
```

然后在 Claude Code 会话里直接引用代理，例如：

```text
请使用 Frontend Developer 代理帮我构建一个 React 组件。
```

### 方式 3：作为参考库使用

每个代理文件都是普通 Markdown。你可以直接浏览、复制、改写或作为团队内部提示词模板的起点。

代理文件通常包含：

- 身份、性格与沟通方式
- 核心使命与工作流
- 技术交付物和示例
- 成功指标与质量标准

### 方式 4：安装到其他工具

仓库提供转换与安装脚本，支持 Claude Code、GitHub Copilot、Antigravity、Gemini CLI、OpenCode、OpenClaw、Cursor、Aider、Windsurf、Kimi Code、Codex、Qwen、Osaurus 和 Hermes。

```bash
# 生成所有支持工具的集成文件
./scripts/convert.sh

# 交互式安装，会自动检测本机已安装工具
./scripts/install.sh

# 或指定某个工具
./scripts/install.sh --tool codex
./scripts/install.sh --tool cursor
./scripts/install.sh --tool claude-code
```

只安装你需要的团队或代理：

```bash
./scripts/install.sh --tool claude-code --division engineering,security
./scripts/install.sh --tool cursor --agent frontend-developer,ui-designer
./scripts/install.sh --list teams
./scripts/install.sh --tool opencode --division engineering --dry-run
```

> **OpenCode 提示：** OpenCode 当前运行时大约只能注册 119 个代理，超过后可能静默丢弃。安装时可以用 `--division` 选择子集，避免超过限制。

---

## 🧭 代理团队导航

仓库包含 230+ 个专业代理，分布在多个团队与场景中。下面是中文导航；完整代理说明请进入对应目录查看。

| 团队 | 目录 | 适合场景 |
| --- | --- | --- |
| 工程 | [`engineering/`](engineering/) | 前端、后端、DevOps、AI、数据库、SRE、代码审查、移动端、嵌入式等软件工程任务 |
| 设计 | [`design/`](design/) | UI、UX、品牌、视觉叙事、图像提示词、包容性视觉与可用性走查 |
| 产品 | [`product/`](product/) | 产品管理、反馈分析、趋势研究、冲刺优先级与行为引导 |
| 项目管理 | [`project-management/`](project-management/) | 项目推进、会议纪要、Jira 工作流、实验跟踪与团队协调 |
| 测试 | [`testing/`](testing/) | API 测试、可访问性审计、性能基准、证据收集、工具评估与测试结果分析 |
| 安全 | [`security/`](security/) | 应用安全、云安全、渗透测试、威胁情报、检测工程、事件响应与合规 |
| 营销 | [`marketing/`](marketing/) | SEO、社媒、内容、短视频、小红书、知乎、B 站、抖音、跨境电商与增长 |
| 付费媒体 | [`paid-media/`](paid-media/) | PPC、搜索词分析、投放审计、追踪衡量、素材策略与程序化广告 |
| 销售 | [`sales/`](sales/) | 外呼策略、销售发现、交易策略、售前工程、提案、销售教练与管道分析 |
| 支持 | [`support/`](support/) | 客户回复、分析报告、财务追踪、基础设施维护、法务合规与高管摘要 |
| 财务 | [`finance/`](finance/) | 财务分析、FP&A、投资研究、税务策略、记账与控制 |
| GIS | [`gis/`](gis/) | Web GIS、空间数据工程、制图、GeoAI、三维场景、BIM、无人机与地理处理 |
| 游戏开发 | [`game-development/`](game-development/) | Unity、Unreal、Godot、Roblox、关卡设计、叙事设计、技术美术与音频 |
| 空间计算 | [`spatial-computing/`](spatial-computing/) | XR、visionOS、空间界面、沉浸式开发、macOS Metal 与终端集成 |
| 学术 | [`academic/`](academic/) | 心理学、叙事学、历史、地理与人类学等研究型代理 |
| 专门领域 | [`specialized/`](specialized/) | 法务、医疗、招聘、供应链、政府售前、ESG、隐私、培训、身份图谱等垂直场景 |

其他有用入口：

- [`examples/`](examples/)：多代理工作流示例。
- [`strategy/`](strategy/)：跨团队策略、剧本与协作模板。
- [`integrations/`](integrations/)：各工具的安装与使用说明。
- [`scripts/i18n/`](scripts/i18n/)：中文代理名称本地化脚本。

---

## 🧩 多工具集成

The Agency 可以通过脚本安装到多种 AI 编程与代理工具中。

| 工具 | 集成说明 |
| --- | --- |
| Claude Code | [`integrations/claude-code/README.md`](integrations/claude-code/README.md) |
| GitHub Copilot | [`integrations/github-copilot/README.md`](integrations/github-copilot/README.md) |
| Codex | [`integrations/codex/README.md`](integrations/codex/README.md) |
| Cursor | [`integrations/cursor/README.md`](integrations/cursor/README.md) |
| Gemini CLI | [`integrations/gemini-cli/README.md`](integrations/gemini-cli/README.md) |
| OpenCode | [`integrations/opencode/README.md`](integrations/opencode/README.md) |
| OpenClaw | [`integrations/openclaw/README.md`](integrations/openclaw/README.md) |
| Aider | [`integrations/aider/README.md`](integrations/aider/README.md) |
| Windsurf | [`integrations/windsurf/README.md`](integrations/windsurf/README.md) |
| Kimi Code | [`integrations/kimi/README.md`](integrations/kimi/README.md) |
| Antigravity | [`integrations/antigravity/README.md`](integrations/antigravity/README.md) |
| Hermes | [`integrations/hermes/README.md`](integrations/hermes/README.md) |
| MCP Memory | [`integrations/mcp-memory/README.md`](integrations/mcp-memory/README.md) |

常用命令：

```bash
# 转换所有集成文件
./scripts/convert.sh

# 并行转换，适合多核机器
./scripts/convert.sh --parallel

# 只转换某个工具
./scripts/convert.sh --tool codex

# 交互式安装
./scripts/install.sh

# 非交互式安装全部支持工具
./scripts/install.sh --no-interactive --tool all
```

---

## 🇨🇳 中文本地化

仓库已包含简体中文贡献指南和部分中文本地化工具：

- [`CONTRIBUTING_zh-CN.md`](CONTRIBUTING_zh-CN.md)：中文贡献说明。
- [`scripts/i18n/README.md`](scripts/i18n/README.md)：中文代理名称本地化说明。
- [`scripts/i18n/agent-names-zh.json`](scripts/i18n/agent-names-zh.json)：英文代理名到中文名称的映射。
- [`scripts/i18n/localize-agents-zh.ps1`](scripts/i18n/localize-agents-zh.ps1)：将已安装代理的名称与描述本地化为中文的 PowerShell 脚本。

示例：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/i18n/localize-agents-zh.ps1
```

> 该脚本默认修改已安装到 `%USERPROFILE%\.github\agents\` 和 `%USERPROFILE%\.copilot\agents\` 的代理副本，不会改动仓库中的源文件。

---

## 🤝 如何贡献

欢迎贡献新的代理、优化现有代理、补充示例、修正文档或完善本地化。

你可以：

- 添加新的专业代理。
- 为现有代理补充真实场景、代码示例、工作流或成功指标。
- 改进安装脚本、集成说明和文档。
- 分享你使用代理完成项目的案例。
- 提交中文翻译、本地化术语或中文市场相关代理。

中文贡献说明请见 [`CONTRIBUTING_zh-CN.md`](CONTRIBUTING_zh-CN.md)，英文说明请见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。

---

## 🎯 代理设计理念

The Agency 的代理设计强调五件事：

1. **鲜明个性**：不是“一个有用助手”，而是有判断、有风格、有经验的专家。
2. **明确交付物**：输出可以直接使用的代码、文档、模板、分析或决策材料。
3. **成功指标**：用可观察、可衡量的标准定义什么叫“做得好”。
4. **经过验证的工作流**：给出分阶段流程、检查点和质量门槛。
5. **持续学习记忆**：让代理识别成功模式、失败模式和可复用经验。

---

## 📊 项目概览

- **230+ 个专业代理**，覆盖多个职能团队与垂直场景。
- **10,000+ 行** 代理身份、流程、示例和交付标准。
- 支持 Claude Code、Cursor、Codex、Gemini CLI、OpenCode、OpenClaw、GitHub Copilot 等多种工具。
- MIT 许可证，可用于个人、团队和商业场景。

---

## 🔗 相关资源

- [Agency Agents 桌面应用](https://agencyagents.app)
- [最新应用版本](https://github.com/msitarzewski/agency-agents-app/releases/latest)
- [GitHub Discussions](https://github.com/msitarzewski/agency-agents/discussions)
- [Issues](https://github.com/msitarzewski/agency-agents/issues)
- [Sponsor](https://github.com/sponsors/msitarzewski)
- [awesome-openclaw-agents](https://github.com/mergisi/awesome-openclaw-agents)

---

## 📜 许可证

本项目使用 MIT License。你可以自由地在个人、团队或商业项目中使用、复制、修改和分发。

---

<div align="center">

**🎭 The Agency：你的 AI 专家团队，随时待命。**

[⭐ Star this repo](https://github.com/msitarzewski/agency-agents) · [🍴 Fork it](https://github.com/msitarzewski/agency-agents/fork) · [🐛 Report an issue](https://github.com/msitarzewski/agency-agents/issues) · [❤️ Sponsor](https://github.com/sponsors/msitarzewski)

Made with ❤️ by the community, for the community

</div>