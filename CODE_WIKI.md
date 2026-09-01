# 📚 The Agency - Agents Code Wiki

> **项目名称**: The Agency: AI Specialists Ready to Transform Your Workflow
> **仓库地址**: https://github.com/msitarzewski/agency-agents
> **项目类型**: AI Agent 知识库 / 多工具集成平台
> **当前版本**: 共 **273** 个专业 AI Agent，覆盖 **18** 个业务领域，支持 **16** 种 AI 编码工具

---

## 目录

1. [项目概览](#1-项目概览)
2. [整体架构设计](#2-整体架构设计)
3. [目录结构详解](#3-目录结构详解)
4. [Agent 文件格式规范](#4-agent-文件格式规范)
5. [核心模块与脚本说明](#5-核心模块与脚本说明)
6. [配置文件说明](#6-配置文件说明)
7. [工具集成层](#7-工具集成层)
8. [NEXUS 战略与 Runbook 系统](#8-nexus-战略与-runbook-系统)
9. [CI/CD 工作流](#9-cicd-工作流)
10. [关键函数与数据结构](#10-关键函数与数据结构)
11. [项目运行与使用方式](#11-项目运行与使用方式)
12. [贡献指南与开发规范](#12-贡献指南与开发规范)
13. [依赖关系图](#13-依赖关系图)
14. [常见问题与最佳实践](#14-常见问题与最佳实践)

---

## 1. 项目概览

### 1.1 项目定位

**The Agency** 是一个精心打造的 AI 专业 Agent 集合库。每个 Agent 都是一个具有独立个性、领域专长、工作流程和可衡量交付物的虚拟专家。项目的核心理念是：**像组建理想团队一样，按需装配 AI 专家**。

### 1.2 核心特性

| 特性 | 说明 |
|------|------|
| 🎯 **专业化** | 每个 Agent 专注于狭窄而深入的领域，而非通用助手 |
| 🧠 **人格化** | 独特的声音、沟通风格和行事方法 |
| 📋 **交付导向** | 产出真实代码、流程和可量化结果 |
| ✅ **生产就绪** | 经过实战检验的工作流程和成功指标 |
| 🔌 **多工具兼容** | 支持 16 种主流 AI 编码工具的一键安装 |
| 🎮 **可视化安装** | 提供桌面 App (macOS/Linux/Windows) 一键管理 |

### 1.3 统计数据

- **Agent 总数**: 273 个
- **业务部门 (Divisions)**: 18 个
- **支持工具数**: 16 种
- **NEXUS 场景剧本**: 4 个
- **CI 检查流水线**: 5 条

### 1.4 各部门 Agent 分布

| 部门 (Division) | 数量 | 主题色 | 图标 |
|-----------------|------|--------|------|
| Engineering (工程) | 59 | `#3B82F6` | Code |
| Specialized (专项) | 58 | `#6366F1` | Sparkles |
| Marketing (营销) | 36 | `#F97316` | Megaphone |
| Game Development (游戏开发) | 21 | `#A855F7` | Gamepad2 |
| Sales (销售) | 9 | `#10B981` | TrendingUp |
| Testing (测试) | 9 | `#F59E0B` | FlaskConical |
| Security (安全) | 12 | `#EF4444` | ShieldCheck |
| GIS (地理信息) | 13 | `#14B8A6` | Map |
| Design (设计) | 10 | `#EC4899` | PenTool |
| Paid Media (付费媒体) | 7 | `#EAB308` | Target |
| Project Management (项目管理) | 7 | `#0EA5E9` | ClipboardList |
| Spatial Computing (空间计算) | 6 | `#06B6D4` | Boxes |
| Academic (学术) | 6 | `#8B5CF6` | GraduationCap |
| Support (支持) | 6 | `#84CC16` | LifeBuoy |
| Finance (财务) | 5 | `#22C55E` | DollarSign |
| Product (产品) | 5 | `#D946EF` | Box |
| Healthcare (医疗) | 3 | `#0D9488` | Stethoscope |
| Research (研究) | 1 | `#7C3AED` | Search |

---

## 2. 整体架构设计

### 2.1 分层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    消费层 (Consumers)                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐  │
│  │Desktop App│ │Claude Code│ │  Cursor  │ │Copilot   │ │Aider  │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬───┘  │
│       │            │            │            │           │       │
│  ┌────▼────────────▼────────────▼────────────▼───────────▼────┐  │
│  │                    安装层 (Install)                          │  │
│  │            scripts/install.sh (交互式 TUI + CLI)             │  │
│  └──────────────────────────┬───────────────────────────────────┘  │
│                             │                                      │
│  ┌──────────────────────────▼───────────────────────────────────┐  │
│  │                    转换层 (Convert)                           │  │
│  │            scripts/convert.sh (16 种格式转换器)               │  │
│  └──────────────────────────┬───────────────────────────────────┘  │
│                             │                                      │
└─────────────────────────────┼──────────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────────┐
│                       数据层 (Source of Truth)                     │
│                                                                    │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────────┐      │
│  │  divisions.json │  │  tools.json  │  │ runbooks.json    │      │
│  │  (部门定义)     │  │  (工具定义)  │  │ (NEXUS 剧本)     │      │
│  └─────────────────┘  └──────────────┘  └──────────────────┘      │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    Agent 知识库 (18 个目录)                  │  │
│  │  ┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐...     │  │
│  │  │ Eng││Des ││Mkt ││Sec ││Fin ││Sal ││GIS ││GM  │         │  │
│  │  └────┘└────┘└────┘└────┘└────┘└────┘└────┘└────┘         │  │
│  └─────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────────┐
│                     质量保障层 (Quality Gates)                      │
│  ┌───────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │ lint-agents.sh│  │check-divisions│  │check-agent-originality │  │
│  │ (格式与结构)  │  │ (一致性)     │  │  (反抄袭检测)           │  │
│  └───────────────┘  └──────────────┘  └────────────────────────┘  │
│  ┌───────────────┐  ┌──────────────┐                              │
│  │check-tools.sh │  │check-runbooks│                              │
│  │ (工具一致性)  │  │ (剧本有效性) │                              │
│  └───────────────┘  └──────────────┘                              │
└────────────────────────────────────────────────────────────────────┘
```

### 2.2 单一数据源原则 (Single Source of Truth)

此项目架构的核心设计原则是 **SSOT (单一数据源)**：

| 数据源 | 文件 | 消费方 |
|--------|------|--------|
| 部门定义 | `divisions.json` | install.sh, convert.sh, lint-agents.sh, CI, Desktop App |
| 工具定义 | `tools.json` | install.sh, convert.sh, check-tools.sh, Desktop App |
| NEXUS 剧本 | `runbooks.json` | Desktop App, check-runbooks.sh |
| Agent 内容 | `**/*.md` (18 个部门目录) | 所有转换器、安装器、App |

**任何硬编码列表都会被 CI 检查拒绝**，保证列表永远与 `divisions.json` / `tools.json` 一致。

### 2.3 格式转换机制

项目使用三种 **安装机制 (installKind)**：

| installKind | 说明 | 工具示例 | 特点 |
|-------------|------|----------|------|
| `per-agent` | 每个 Agent 生成一个独立文件/目录 | Claude Code, Cursor, Codex, OpenClaw, Qwen, Kimi, ... | 最常见，用户可按需挑选 |
| `roster` | 所有 Agent 合并为一个文件 | Aider, Windsurf | 工具不支持多 Agent，采用合并方式 |
| `plugin` | 构建为插件制品 | Hermes | 需独立构建流程，仅 CLI 可用 |

### 2.4 渲染格式契约 (Renderer Format Contract)

`tools.json` 中的 `format` 字段定义了渲染契约：**相同 `format` 意味着字节级一致的输出**。这避免了重复编写转换器：

| format | 含义 | 共享工具 |
|--------|------|----------|
| `identity` | 原始 Markdown 直接使用 | claude-code, copilot |
| `skill-md` | SKILL.md 技能目录格式 | antigravity, osaurus |
| `qwen-md` / `zcode-md` | YAML frontmatter + body | qwen, zcode |

---

## 3. 目录结构详解

```
/workspace/
├── README.md                     # 项目主页 + 完整 Agent 目录
├── CONTRIBUTING.md               # 贡献指南 (含 Agent 设计规范)
├── CONTRIBUTING_zh-CN.md         # 中文版贡献指南
├── SECURITY.md                   # 安全政策
├── LICENSE                       # MIT 许可证
├── .gitattributes                # LF 行尾规范
├── .gitignore                    # 含 integrations/<tool>/ 生成文件规则
│
├── divisions.json                # SSOT: 18 个部门定义
├── tools.json                    # SSOT: 16 种工具定义
│
├── academic/                     # 学术部 (6 个 Agent)
│   ├── academic-anthropologist.md
│   ├── academic-geographer.md
│   └── ...
│
├── design/                       # 设计部 (10 个 Agent)
│   ├── design-ui-designer.md
│   ├── design-ux-researcher.md
│   ├── design-brand-guardian.md
│   └── ...
│
├── engineering/                  # 工程部 (59 个 Agent)
│   ├── engineering-frontend-developer.md
│   ├── engineering-backend-architect.md
│   ├── engineering-ai-engineer.md
│   ├── engineering-devops-automator.md
│   └── ... (55 个更多)
│
├── finance/                      # 财务部 (5 个 Agent)
├── game-development/             # 游戏开发部 (21 个 Agent)
│   ├── game-designer.md
│   ├── unity/                    # Unity 子分类 (4 个)
│   ├── unreal-engine/            # Unreal 子分类 (4 个)
│   ├── godot/                    # Godot 子分类 (3 个)
│   ├── roblox-studio/            # Roblox 子分类 (3 个)
│   └── blender/                  # Blender 子分类 (1 个)
│
├── gis/                          # GIS 部 (13 个 Agent)
├── healthcare/                   # 医疗部 (3 个 Agent)
├── marketing/                    # 营销部 (36 个 Agent)
├── paid-media/                   # 付费媒体部 (7 个 Agent)
├── product/                      # 产品部 (5 个 Agent)
├── project-management/           # 项目管理部 (7 个 Agent)
├── research/                     # 研究部 (1 个 Agent)
├── sales/                        # 销售部 (9 个 Agent)
├── security/                     # 安全部 (12 个 Agent)
├── spatial-computing/            # 空间计算部 (6 个 Agent)
├── specialized/                  # 专项部 (58 个 Agent)
├── support/                      # 支持部 (6 个 Agent)
├── testing/                      # 测试部 (9 个 Agent)
│
├── strategy/                     # NEXUS 战略系统 (非部门目录)
│   ├── EXECUTIVE-BRIEF.md        # 高管简报
│   ├── QUICKSTART.md             # 快速启动
│   ├── nexus-strategy.md         # NEXUS 方法论
│   ├── runbooks.json             # SSOT: Runbook 清单
│   ├── coordination/             # 协作模板
│   │   ├── agent-activation-prompts.md
│   │   └── handoff-templates.md
│   ├── playbooks/                # 6 阶段执行手册
│   │   ├── phase-0-discovery.md
│   │   ├── phase-1-strategy.md
│   │   ├── phase-2-foundation.md
│   │   ├── phase-3-build.md
│   │   ├── phase-4-hardening.md
│   │   └── phase-5-launch.md
│   │   └── phase-6-operate.md
│   └── runbooks/                 # 4 个场景剧本
│       ├── scenario-startup-mvp.md
│       ├── scenario-enterprise-feature.md
│       ├── scenario-marketing-campaign.md
│       └── scenario-incident-response.md
│
├── integrations/                 # 转换器输出目录 (.gitignore)
│   ├── README.md                 # 集成说明 (唯一追踪文件)
│   ├── claude-code/README.md     # 各工具 README 被追踪
│   ├── copilot/README.md
│   ├── antigravity/README.md
│   ├── gemini-cli/README.md
│   ├── opencode/README.md
│   ├── openclaw/README.md
│   ├── cursor/README.md
│   ├── aider/README.md
│   ├── windsurf/README.md
│   ├── kimi/README.md
│   ├── qwen/README.md
│   ├── zcode/README.md
│   ├── codex/README.md
│   ├── osaurus/README.md
│   ├── hermes/README.md
│   └── vibe/README.md
│
├── examples/                     # 多 Agent 协作示例
│   ├── README.md
│   ├── nexus-spatial-discovery.md
│   ├── workflow-book-chapter.md
│   ├── workflow-landing-page.md
│   ├── workflow-startup-mvp.md
│   └── workflow-with-memory.md
│
├── scripts/                      # 核心脚本目录
│   ├── lib.sh                    # 共享纯 Bash 函数库
│   ├── convert.sh                # Agent → 16 种格式转换器
│   ├── install.sh                # 交互式安装器 (TUI)
│   ├── lint-agents.sh            # Agent 格式/结构检查
│   ├── check-divisions.sh        # divisions.json 一致性检查
│   ├── check-tools.sh            # tools.json 一致性检查
│   ├── check-runbooks.sh         # runbooks.json 有效性检查
│   ├── check-agent-originality.sh # Agent 原创性/反抄袭检测
│   ├── build-hermes-plugin.py    # Hermes 插件构建器
│   ├── check-hermes-plugin.py    # Hermes 插件验证
│   ├── install.sh 对应测试脚本
│   ├── agents-to-install.example # agents-file 示例
│   └── i18n/                     # 国际化脚本
│       ├── README.md
│       ├── agent-names-zh.json
│       └── localize-agents-zh.ps1
│
└── .github/                      # GitHub 配置
    ├── FUNDING.yml
    ├── PULL_REQUEST_TEMPLATE.md
    ├── ISSUE_TEMPLATE/
    │   ├── bug-report.yml
    │   └── new-agent-request.yml
    └── workflows/                # CI 流水线
        ├── lint-agents.yml       # PR: Agent Lint + 原创性检查
        ├── check-divisions.yml   # PR/Push: 部门一致性
        ├── check-tools.yml       # PR/Push: 工具一致性
        ├── check-runbooks.yml    # PR/Push: Runbook 有效性
        └── ...
```

---

## 4. Agent 文件格式规范

### 4.1 Frontmatter 字段定义

每个 Agent `.md` 文件必须以 YAML frontmatter 开头：

```yaml
---
name: Agent Name                          # 必选: 显示名 (lint 必查)
description: One-line description         # 必选: 一句话描述 (lint 必查)
color: colorname or "#RRGGBB"             # 必选: 主题色 (lint 必查)
emoji: 🎯                                  # 推荐: 个性表情
vibe: One-line personality hook            # 推荐: 人格标语
services:                                   # 可选: 依赖外部服务
  - name: Service Name
    url: https://service-url.com
    tier: free                             # free / freemium / paid
tools: "tool_name"                         # 可选: Qwen/ZCode 使用
---
```

**字段规则**:
- `name`: 用于生成 slug（唯一标识符），是 convert/install 的锚点
- `color`: OpenCode 格式会自动将颜色名标准化为 `#RRGGBB`
- `services`: Agent 可依赖 SaaS，但必须能独立工作

### 4.2 Body 标准章节

Agent Body 分为两大语义组，用于 OpenClaw 格式的自动拆分：

#### 🎭 Persona 组 (映射到 SOUL.md)
- **Identity & Memory** — 角色、性格、背景
- **Communication Style** — 语气、声音、沟通方式
- **Critical Rules** — 边界和约束

#### ⚙️ Operations 组 (映射到 AGENTS.md)
- **Core Mission** — 主要职责
- **Technical Deliverables** — 具体输出和模板
- **Workflow Process** — 步骤化方法论
- **Success Metrics** — 可衡量结果
- **Advanced Capabilities** — 专业技巧

### 4.3 完整模板

```markdown
---
name: Agent Name
description: One-line description
color: cyan
emoji: 🎯
vibe: What makes this agent memorable
---

# Agent Name

## 🧠 Your Identity & Memory
- **Role**: Clear role description
- **Personality**: Personality traits
- **Memory**: What the agent remembers
- **Experience**: Domain expertise

## 🎯 Your Core Mission
- Primary responsibility 1 with deliverables
- Primary responsibility 2

## 🚨 Critical Rules You Must Follow
- Domain-specific rules

## 📋 Your Technical Deliverables
- Code samples with real syntax-highlighted blocks
- Templates and frameworks

## 🔄 Your Workflow Process
1. Phase 1: Discovery
2. Phase 2: Planning
3. Phase 3: Execution
4. Phase 4: Review

## 💭 Your Communication Style
- How the agent communicates

## 🎯 Your Success Metrics
- Quantitative metrics (with numbers)

## 🚀 Advanced Capabilities
- Specialized techniques
```

### 4.4 文件命名约定

```
<division>/<division>-<agent-slug>.md
```

**示例**:
- `engineering/engineering-frontend-developer.md` → slug: `engineering-frontend-developer`
- `specialized/agents-orchestrator.md` → slug: `agents-orchestrator`

> **注意**: slug 是从 `name` frontmatter 字段通过 `slugify()` 派生的，**不依赖文件名**。但文件名通常保持与 slug 一致以便查找。

---

## 5. 核心模块与脚本说明

### 5.1 `scripts/lib.sh` — 共享函数库

被 `convert.sh` 和 `install.sh` 同时 source。**零外部依赖**，纯 Bash 3.2+。

**组1: Frontmatter / Slug 工具 (Agent 数据模型)**

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_field` | `<field> <file>` | 提取 YAML frontmatter 中指定字段值 (首次匹配) |
| `get_body` | `<file>` | 去掉 frontmatter 返回正文内容 |
| `slugify` | `<string>` | `"Frontend Developer" → "frontend-developer"`，小写 + 连字符 |
| `agent_slug` | `<file>` | 从文件的 `name:` frontmatter 派生 slug（SSOT） |
| `is_agent_file` | `<file>` | 判断文件是否以 `---` 开头（有效的 Agent 文件） |

**组2: set -e 安全原语**

| 函数 | 签名 | 说明 |
|------|------|------|
| `incr` | `<varname>` | 安全自增（避免 `((x++))` 在 `set -e` 下误退出） |

**组3: 终端能力与 ANSI**

| 函数 | 说明 |
|------|------|
| `supports_color` | 判断是否支持彩色 (TTY + 非 NO_COLOR + 非 dumb) |
| `supports_unicode` | 根据 LANG 环境变量判断 UTF-8 支持 |
| `term_cols` / `term_rows` | 获取终端尺寸，失败回退 80x24 |
| `init_ansi` | 填充 C_* 颜色变量 + 盒绘字符 (UTF-8 or ASCII fallback) |
| `strip_ansi` | 去除 ANSI 转义序列（用于宽度计算） |
| `vis_len` | 可见字符长度（ANSI 已剥离） |

**组4: TUI 原语（install.sh 交互式向导使用）**

| 函数 | 说明 |
|------|------|
| `tui_begin` | 进入 alt screen，关闭回显，设置 raw 模式，安装恢复 trap |
| `tui_end` | 还原终端（idempotent，可从 trap 调用） |
| `read_key` | 读取一次按键，返回 `UP/DOWN/LEFT/RIGHT/ENTER/SPACE/ESC/BACKSPACE/TAB` 或字符 |
| `draw_frame` | 无闪烁重绘：整屏逐行清除至行尾 + 清屏 |

### 5.2 `scripts/convert.sh` — 格式转换器

**功能**: 读取所有部门目录中的 Agent `.md` 文件，为 16 种工具生成对应格式，输出到 `integrations/<tool>/`。

**命令行参数**:
```bash
./scripts/convert.sh [--tool <name>] [--out <dir>] [--parallel] [--jobs N] [--help]
```

**转换器函数列表 (convert_<tool> / accumulate_<tool>)**:

| 工具 | 函数 | 输出格式 | 安装类型 |
|------|------|----------|----------|
| Claude Code | (identity) | 源文件直接拷贝 | per-agent |
| Copilot | (identity) | 源文件直接拷贝 | per-agent |
| Antigravity | `convert_antigravity` | `SKILL.md` + YAML frontmatter + `agency-` 前缀 | per-agent |
| Osaurus | `convert_osaurus` | `SKILL.md` + YAML frontmatter + `agency-` 前缀 | per-agent |
| Gemini CLI | `convert_gemini_cli` | `.md` + YAML frontmatter | per-agent |
| Codex | `convert_codex` | `.toml` (name + description + developer_instructions) | per-agent |
| OpenCode | `convert_opencode` | `.md` + YAML frontmatter (颜色名自动标准化 hex) | per-agent |
| Cursor | `convert_cursor` | `.mdc` + description/globs/alwaysApply frontmatter | per-agent |
| Qwen | `convert_qwen` | `.md` + 最小 frontmatter (tools 字段有条件传递) | per-agent |
| ZCode | `convert_zcode` | `.md` + 最小 frontmatter (与 qwen-md 字节级一致) | per-agent |
| Kimi | `convert_kimi` | `agent.yaml` + 独立 `system.md` (extend: default) | per-agent |
| Vibe | `convert_vibe` | `agents/<slug>.toml` + `prompts/<slug>.md` 双文件 | per-agent |
| OpenClaw | `convert_openclaw` | 三文件拆分: SOUL.md + AGENTS.md + IDENTITY.md | per-agent |
| Aider | `accumulate_aider` | 合并所有 Agent 到单个 `CONVENTIONS.md` | roster |
| Windsurf | `accumulate_windsurf` | 合并所有 Agent 到单个 `.windsurfrules` | roster |
| Hermes | `convert_hermes` | 调用 `build-hermes-plugin.py` 构建插件 | plugin |

**辅助函数**:
- `toml_escape_string()`: TOML 安全编码（控制字符转 Unicode）
- `yaml_quote()`: YAML 单引号标量（保持冒号/反斜杠字面量）
- `resolve_opencode_color()`: 颜色名 → `#RRGGBB` 标准化映射

**OpenClaw 拆分算法**:
1. 逐行扫描 body，按 `## ` 标题分段
2. 用关键词正则匹配 `identity|learning.*memory|communication|style|critical.rule|rules.you.must.follow`
3. 命中的段写入 SOUL.md，其余写入 AGENTS.md
4. IDENTITY.md 由 frontmatter 的 emoji + vibe 或 description 组合生成

### 5.3 `scripts/install.sh` — 交互式安装器

**功能**: 将 `integrations/` 中的转换产物复制/软链到各工具的配置目录。

**命令行参数**:
```
./scripts/install.sh [selection] [mode] [behavior]

选择参数:
  --tool <a,b>          指定工具
  --division <a,b>      指定部门
  --agent <slug,slug>   指定 Agent (slug 或 name)
  --agents-file <path>  从文件读取列表 (每行一个, # 注释)

模式参数:
  --link                软链接替代复制 (更新自动传播)
  --path <dir>          覆盖安装目标目录

行为参数:
  --interactive         启用 TUI 向导 (终端默认)
  --no-interactive      跳过向导, 直接安装
  --no-convert          缺失时不自动 convert
  --dry-run             只打印计划
  --list [tools|teams|agents]  打印清单并退出
  --parallel            并行安装
  --jobs N              并行任务数
```

**核心子系统**:

#### a) 选择引擎 (Selection Engine)
```
build_selection()
  ├── FILTER_DIVISIONS → division_files() → agent_slug()
  ├── FILTER_AGENTS → agent_slug_exists() 验证
  └── AGENTS_FILE → 按行读取 (# 去注释, trim, slugify)
结果存入 _ALLOWED_SLUGS，slug_allowed() 按行 grep 判定
```

#### b) 部门列表来源
```bash
divisions_from_json() {
  # 直接从 divisions.json 解析 (无 jq, 纯 awk/grep/sed)
  awk '/"divisions"[[:space:]]*:[[:space:]]*\{/{f=1; next} f' divisions.json \
    | grep -oE '"[a-z0-9-]+"[[:space:]]*:[[:space:]]*\{' \
    | sed -E 's/"([a-z0-9-]+)".*/\1/'
}
```
> 设计决策：永远不从硬编码列表读取，防止静默漂移（曾有 #655/#668 因硬编码遗漏 healthcare 部门）。

#### c) 自动转换 (Auto Convert)
```bash
ensure_converted() {
  # 当 integrations/<tool>/ 缺失或为空时自动调用 convert.sh
  # claude-code / copilot 例外（它们直接读取源文件，无需转换）
}
```

#### d) 容量警告 (Capacity Warning)
```bash
tool_cap opencode = 119  # 已知上游 bug: OpenCode 静默丢弃超过 ~119 个 Agent
```
选择超过时会打印警告并建议用 `--division` 缩小范围。

#### e) 路径解析优先级
```
--path > 环境变量 (CLAUDE_CONFIG_DIR 等) > 硬编码默认路径
```

#### f) TUI 交互式向导 (3 屏流程)
```
[1/3 Tools] → [2/3 Teams] → [3/3 Review]
  ↓ 选择器 selector()
  ├─ 上下键导航 (UP/DOWN, j/k)
  ├─ 空格切换选中 (SPACE)
  ├─ a 全选 / n 全不选
  ├─ / 进入搜索模式
  ├─ ENTER/RIGHT 下一步 / LEFT 上一步
  └─ ESC 清搜索或退出 / q 退出
```
> 搜索时按键直接追加到 query，ENTER 退出搜索，BACKSPACE 删除字符，ESC 清空搜索。

#### g) TUI 盒绘系统
- 纯 ASCII fallback（当不支持 UTF-8 时）
- C_* 颜色变量 + BX_* 盒绘字符由 `init_ansi()` 初始化
- 固定 52 字符宽的边框 (`BOX_INNER=48`)

### 5.4 `scripts/lint-agents.sh` — Agent Lint 工具

**检查层级**:

| 级别 | 规则 | 触发失败 |
|------|------|----------|
| ERROR | 文件不以 `---` 开头 (无 frontmatter) | ✅ |
| ERROR | frontmatter 为空或格式错误 | ✅ |
| ERROR | 缺少必需字段: `name`, `description`, `color` | ✅ |
| ERROR | CRLF 行尾（仓库标准为 LF） | ✅ |
| WARN | 缺少推荐章节: `Identity`, `Core Mission`, `Critical Rules` | ❌ |
| WARN | 正文 < 50 词 | ❌ |
| WARN | 无 SOUL.md 映射标题 (identity/communication/rules 类) | ❌ |
| WARN | 无 AGENTS.md 映射标题 (mission/deliverables/workflow 类) | ❌ |

**用法**:
```bash
./scripts/lint-agents.sh              # 扫描所有部门
./scripts/lint-agents.sh file1.md ... # 指定文件 (CI 使用)
```

### 5.5 `scripts/check-divisions.sh` — 部门一致性检查

**验证矩阵**: 确保 `divisions.json` 与以下 4 处完全一致：

```
divisions.json (SSOT)
    │
    ├──↔ 磁盘上的部门目录 (git ls-files 去重, 排除 NON_DIVISION_DIRS)
    ├──↔ scripts/convert.sh 中的 AGENT_DIRS=() 数组
    ├──↔ scripts/lint-agents.sh 中的 AGENT_DIRS=() 数组
    └──↔ .github/workflows/lint-agents.yml 中的 PR 路径过滤器
```
**NON_DIVISION_DIRS**: `examples`, `scripts`, `integrations`, `strategy`

**附加验证**:
- 每个 divisions.json 条目必须含 `label`, `icon`, `color`
- 每个部门目录必须至少含一个 frontmatter Agent 文件

### 5.6 `scripts/check-tools.sh` — 工具一致性检查

```
tools.json (SSOT)
    │
    ├──↔ scripts/install.sh 中的 ALL_TOOLS=() (双向完全相等)
    ├──↔ scripts/convert.sh valid_tools (子集: identity 工具无需转换)
    └── 每个工具条目必填: id, label, kebab, format, installKind, dest
        └── installKind ∈ {per-agent, roster, plugin}
```

### 5.7 `scripts/check-agent-originality.sh` — 原创性/反抄袭检测

**算法**:
```
1. 分词: 去 frontmatter → 小写 → 专有名词中性化 (ENTITY 正则)
   ENTITY: 国家/平台名 (china, tiktok, wechat, xiaohongshu, ...) → 替换为空格
   目的: 防止"查找替换换皮"通过检查

2. 8 词 Shingle: 滑动窗口生成连续 8 词组集合
   shingles(words, k=8) = {"w1 w2 ... w8", "w2 w3 ... w9", ...}

3. Jaccard 相似度:
   J(A, B) = |A ∩ B| / |A ∪ B|

4. 阈值:
   WARN ≥ 20% (提醒审查)
   FAIL ≥ 40% (阻断提交, exit 1)
   现有库基线: 最大 ~1.5%, 中位数 0%
```

**依赖**: Python 3（已是 CI 环境标配）

### 5.8 `scripts/check-runbooks.sh` — Runbook 有效性检查

验证 `strategy/runbooks.json`:
- 每个 runbook 必须含 `slug`, `title`, `mode`, `doc`, `roster`
- `slug` 不重复
- `doc` 路径存在
- `agents[]` 中每个 slug 必须解析为真实 Agent 文件（.md 文件名 stem）

**依赖**: Python 3 JSON 解析 + `git ls-files` 取真实文件列表

### 5.9 `scripts/build-hermes-plugin.py` — Hermes 插件构建

Python 3 构建脚本，生成 `agency-agents-router` 插件：
1. 从 `divisions.json` 读取部门列表（再次 SSOT）
2. 解析所有 Agent frontmatter
3. 生成:
   - `plugin.yaml` — 插件声明 (provides_tools)
   - `agents.json` — 全量 Agent 索引（按需懒加载）
   - Router 工具：search/list/load/delegate

---

## 6. 配置文件说明

### 6.1 `divisions.json` — 部门定义

```json
{
  "_note": "说明文档",
  "divisions": {
    "engineering": {
      "label": "Engineering",   // 显示名
      "icon": "Code",           // Lucide 图标 (PascalCase)
      "color": "#3B82F6"        // 品牌色
    },
    // ... 18 个
  }
}
```
> 要新增部门：创建目录 → 加此 JSON → 更新 convert.sh AGENT_DIRS → 更新 lint-agents.sh AGENT_DIRS → 更新 lint-agents.yml 路径 → 运行 check-divisions.sh

### 6.2 `tools.json` — 工具定义

每个工具条目字段说明：

```json
{
  "tools": {
    "claude-code": {
      "id": "claudeCode",             // 程序化标识 (camelCase)
      "label": "Claude Code",         // UI 显示名
      "short": "Claude",              // 缩写
      "kebab": "claude-code",         // kebab-case (与键相同)
      "accent": "#D97757",            // 品牌强调色
      "icon": "claudecode",           // Desktop App 图标名, 无则 null
      "order": 1,                     // UI 显示排序
      "scope": {"user": true, "project": true},  // 支持 user 级 / project 级安装
      "detect": {                     // 检测已安装
        "dirs": [".claude"],          // 存在的目录
        "agentsDir": ".claude/agents" // 安装目录 (可 null)
      },
      "version": {                    // 版本检测命令
        "bin": "claude",
        "args": ["--version"]
      },
      "format": "identity",           // 渲染格式契约
      "installKind": "per-agent",     // per-agent / roster / plugin
      "slugFrom": "source",           // slug 来源: source/name/null
      "slugPrefix": "agency-",        // 可选: 前缀 (antigravity/osaurus 使用)
      "dest": {
        "user": [".claude/agents/{slug}.md"],      // user 级安装路径
        "project": [".claude/agents/{slug}.md"]    // project 级安装路径
      }
    }
  }
}
```

### 6.3 `strategy/runbooks.json` — NEXUS 剧本定义

```json
{
  "runbooks": [
    {
      "slug": "startup-mvp",
      "title": "Startup MVP Build",
      "mode": "NEXUS-Sprint",         // NEXUS-Full / Sprint / Micro
      "duration": "4-6 weeks",
      "summary": "剧本一句话摘要",
      "doc": "strategy/runbooks/scenario-startup-mvp.md",
      "roster": [
        {
          "group": "Core Team",
          "activation": "always",     // always / week 3+ / post-fix / as needed
          "agents": [                 // 数组元素 = Agent slug
            "agents-orchestrator",
            "engineering-frontend-developer"
          ]
        }
      ]
    }
  ]
}
```

---

## 7. 工具集成层

### 7.1 支持工具一览

| 工具 | 安装路径 | 格式 | installKind | scope |
|------|----------|------|-------------|-------|
| **Claude Code** | `~/.claude/agents/*.md` | identity MD | per-agent | user/project |
| **GitHub Copilot** | `~/.github/agents/*.md` + `~/.copilot/agents/*.md` | identity MD | per-agent | user/project |
| **Cursor** | `.cursor/rules/*.mdc` | MDC rules | per-agent | project |
| **Aider** | `CONVENTIONS.md` | 合并 roster | roster | project |
| **Windsurf** | `.windsurfrules` | 合并 roster | roster | project |
| **Gemini CLI** | `~/.gemini/agents/*.md` | gemini-md | per-agent | user/project |
| **Antigravity** | `~/.gemini/config/skills/agency-<slug>/SKILL.md` | skill-md | per-agent | user/project |
| **Osaurus** | `~/.osaurus/skills/agency-<slug>/SKILL.md` | skill-md | per-agent | user |
| **OpenCode** | `.opencode/agents/*.md` / `~/.config/opencode/agents/*.md` | opencode-md | per-agent | user/project |
| **OpenClaw** | `~/.openclaw/agency-agents/<slug>/{SOUL,AGENTS,IDENTITY}.md` | workspace 三文件 | per-agent | user |
| **Qwen Code** | `~/.qwen/agents/*.md` / `.qwen/agents/*.md` | qwen-md | per-agent | user/project |
| **ZCode** | `~/.zcode/agents/*.md` / `.zcode/agents/*.md` | zcode-md | per-agent | user/project |
| **Kimi Code** | `~/.config/kimi/agents/<slug>/{agent.yaml,system.md}` | YAML + MD | per-agent | user |
| **Codex** | `~/.codex/agents/*.toml` | TOML | per-agent | user/project |
| **Hermes** | `~/.hermes/plugins/agency-agents-router/` | plugin | plugin | user |
| **Vibe** | `~/.vibe/agents/*.toml` + `~/.vibe/prompts/*.md` | TOML + MD | per-agent | user/project |

### 7.2 集成目录管理

- `integrations/` 中的 **生成产物从不提交**（通过 `.gitignore` 规则）
- 每个工具目录下 **只追踪 README.md**（集成说明）
- 用户本地运行 `./scripts/convert.sh` 生成所需文件
- Desktop App 则直接从源码渲染，无需中间步骤

### 7.3 新增工具集成步骤

1. 先开 Discussion 对齐方案（"讨论优先"变更）
2. 新增 5 个文件：
   - `tools.json` 加条目（复用已有的 `format` 优先）
   - `scripts/convert.sh` 加 `convert_<tool>()` 并接入工具列表
   - `scripts/install.sh` 加 `install_<tool>()` + detect_* + `ALL_TOOLS`
   - `.gitignore` 加 `integrations/<tool>/` 规则（极易遗漏）
   - `integrations/<tool>/README.md` 写说明
3. 运行 `./scripts/check-tools.sh`，必须全过

---

## 8. NEXUS 战略与 Runbook 系统

### 8.1 NEXUS 方法论

NEXUS 是多 Agent 协作的部署框架，分三个激活模式：

| 模式 | 适用场景 | 团队规模 |
|------|----------|----------|
| **NEXUS-Full** | 大型项目/转型 | 全部门参与 |
| **NEXUS-Sprint** | 标准交付 | 6-12 周 |
| **NEXUS-Micro** | 紧急响应 | 数分钟/小时 |

### 8.2 6 阶段 Playbook

| 阶段 | 文档 | 核心任务 |
|------|------|----------|
| Phase 0 | Discovery | 机会识别、市场调研、可行性评估 |
| Phase 1 | Strategy | 路线图、资源配置、风险识别 |
| Phase 2 | Foundation | 架构搭建、工具链、团队组建 |
| Phase 3 | Build | 迭代开发、持续集成、每日协作 |
| Phase 4 | Hardening | QA、性能、安全加固、合规 |
| Phase 5 | Launch | 发布计划、营销、用户引导 |
| Phase 6 | Operate | 运维、监控、迭代、扩展 |

### 8.3 4 个预定义场景 Runbook

| Runbook | 模式 | 时长 | 核心 Agent 组 |
|---------|------|------|---------------|
| **Startup MVP Build** | Sprint | 4-6 周 | Core Team (9) + Growth (3) + Support (6) |
| **Enterprise Feature** | Sprint | 6-12 周 | Core Team (15) + Compliance (4) + QA (3) |
| **Marketing Campaign** | Sprint | 2-4 周 | Campaign Core (5) + Platform Specialists (5) + Support (4) |
| **Incident Response** | Micro | 分钟-小时 | P0 Critical Response (6) + Verification & Post-Mortem (4) |

### 8.4 协作模板库

| 文件 | 用途 |
|------|------|
| `coordination/agent-activation-prompts.md` | Agent 激活提示词模板 |
| `coordination/handoff-templates.md` | Agent 间交接模板 |

---

## 9. CI/CD 工作流

### 9.1 工作流清单

| Workflow 文件 | 触发 | 内容 |
|---------------|------|------|
| `lint-agents.yml` | PR (路径匹配: 18 个部门 `**/*.md`) | 1. 获取变更 Agent 文件<br>2. 运行 lint-agents.sh<br>3. 运行 check-agent-originality.sh |
| `check-divisions.yml` | PR + Push(main) | 运行 check-divisions.sh<br>**无路径过滤**（新目录必须被检查到） |
| `check-tools.yml` | PR + Push(main) | 运行 check-tools.sh |
| `check-runbooks.yml` | PR + Push(main) | 运行 check-runbooks.sh |

### 9.2 CI 运行顺序

```
PR 打开
   │
   ├─ lint-agents.yml (仅当部门文件变更)
   │   ├─ 变更文件 diff
   │   ├─ lint-agents.sh → 结构/frontmatter
   │   └─ check-agent-originality.sh → 反抄袭
   │
   ├─ check-divisions.yml (始终运行)
   │   └─ divisions.json ↔ 目录 ↔ convert.sh ↔ lint.sh ↔ PR 路径
   │
   ├─ check-tools.yml (始终运行)
   │   └─ tools.json ↔ install.sh ↔ convert.sh
   │
   └─ check-runbooks.yml (始终运行)
       └─ runbooks.json → 所有 slug 解析到真实 Agent 文件
```

---

## 10. 关键函数与数据结构

### 10.1 Frontmatter 解析流程 (Bash)

```
Agent .md 文件
   │
   ├─ get_field(field, file)          # awk 提取值
   │   算法: 遇第一个 --- 进入 fm=1,
   │          匹配 "^field: " 前缀时截取 value 并 exit
   │
   ├─ get_body(file)                  # awk 提取正文
   │   算法: fm 计数器, 遇两次 --- 后开始 print
   │
   ├─ agent_slug(file)
   │   └─ get_field(name) → slugify()
   │
   └─ is_agent_file(file)
       └─ head -1 == "---"
```

### 10.2 Slugify 算法

```
slugify("Frontend Developer")
    ↓ tr '[:upper:]' '[:lower:]'
    "frontend developer"
    ↓ sed 's/[^a-z0-9]/-/g'
    "frontend-developer"
    ↓ sed 's/--*/-/g; s/^-//; s/-$//'
    "frontend-developer" ✓
```

### 10.3 convert.sh 管道

```
for division in AGENT_DIRS:
    for file in division/*.md:
        if is_agent_file(file):
            for tool in valid_tools:
                convert_tool(file)
                # per-agent: 立即写文件
                # roster: 追加到临时文件 (AIDER_TMP/WINDSURF_TMP)

流程结束后:
    flush AIDER_TMP → integrations/aider/CONVENTIONS.md
    flush WINDSURF_TMP → integrations/windsurf/.windsurfrules
    call build-hermes-plugin.py → integrations/hermes/ (plugin 型)
```

### 10.4 install.sh 管道

```
参数解析 → usage / --list
    │
    ├─ 交互模式 (tty)
    │   ├─ tui_begin → screen_tools → screen_teams → screen_review
    │   └─ 生成 SELECTION_TOOLS[] + SELECTION_DIVISIONS[]
    │
    └─ 非交互模式
        └─ build_selection() → FILTER → _ALLOWED_SLUGS

for tool in selected_tools:
    ensure_converted(tool)
    capacity_warn(tool, count)
    install_tool(tool) → 遍历 selected_agents
        ├─ per-agent: 对每个 slug 调用 install_file(src → dest)
        ├─ roster:  单文件 → 项目根目录
        └─ plugin:  整个插件目录拷贝
```

### 10.5 Agent 对象数据结构

Hermes / Python 构建器中的 Agent 对象：

```python
Agent = {
    "slug": "frontend-developer",           # agent_slug() 结果
    "name": "Frontend Developer",           # frontmatter name
    "description": "...",                   # frontmatter description
    "division": "engineering",              # 相对路径第一层
    "color": "cyan",                        # frontmatter color
    "emoji": "🖥️",                           # frontmatter emoji
    "vibe": "Builds responsive...",         # frontmatter vibe
    "source_path": "engineering/engineering-frontend-developer.md",
    "body": "..."                           # 完整正文
}
```

### 10.6 OpenClaw 三文件数据模型

```
Frontend Developer Agent
    │
    ├── SOUL.md (Persona)
    │   ├── ## 🧠 Your Identity & Memory
    │   ├── ## 🚨 Critical Rules You Must Follow
    │   ├── ## 💭 Your Communication Style
    │   └── ## 🔄 Learning & Memory
    │
    ├── AGENTS.md (Operations)
    │   ├── ## 🎯 Your Core Mission
    │   ├── ## 📋 Your Technical Deliverables
    │   ├── ## 🔄 Your Workflow Process
    │   ├── ## 🎯 Your Success Metrics
    │   └── ## 🚀 Advanced Capabilities
    │
    └── IDENTITY.md (名片)
        └── # 🖥️ Frontend Developer
            Builds responsive, accessible web apps with pixel-perfect precision.
```

---

## 11. 项目运行与使用方式

### 11.1 环境要求

| 组件 | 最低版本 | 用途 |
|------|----------|------|
| Bash | 3.2+ | 所有脚本 (macOS 自带版本够用) |
| Python | 3.x | check-agent-originality.sh, check-runbooks.sh, build-hermes-plugin.py |
| coreutils | - | Linux/macOS 自带 (awk/grep/sed/find/sort/tr/wc) |
| git | - | check-divisions.sh check-runbooks.sh 使用 git ls-files |
| perl | - | convert.sh toml_escape_string 使用 |

> **零 npm / pip / gem 依赖**。所有核心功能纯 Bash + Python 标准库。

### 11.2 快速开始（推荐路径）

#### 方式 A: Desktop App（最推荐）

1. 从 [agencyagents.app](https://agencyagents.app) 下载
2. macOS Homebrew: `brew install --cask msitarzewski/agency-agents/agency-agents`
3. 打开 App → 浏览 Agent → 一键安装到目标工具

#### 方式 B: 命令行交互式安装

```bash
# 克隆仓库
git clone https://github.com/msitarzewski/agency-agents.git
cd agency-agents

# 运行交互式安装器 (自动检测已安装的工具 + 让你选部门)
./scripts/install.sh
# 进入 TUI:
#   [1/3] 空格选择工具
#   [2/3] 空格选择部门
#   [3/3] 回车确认安装
```

#### 方式 C: 直接用于 Claude Code

```bash
# 无需 convert，直接复制源文件
cp engineering/*.md ~/.claude/agents/
```

#### 方式 D: 项目级安装（Cursor / Aider / Windsurf / OpenCode / Qwen）

```bash
cd your-project/
# 只安装工程 + 设计 + 测试部门到 Cursor
/path/to/agency-agents/scripts/install.sh \
  --tool cursor \
  --division engineering,design,testing
```

### 11.3 常见组合命令

```bash
# 查看所有可用内容
./scripts/install.sh --list          # 工具+部门概览
./scripts/install.sh --list agents   # 所有 Agent slug
./scripts/install.sh --list teams    # 每部门 Agent 数

# Dry-run 预览计划（不写盘）
./scripts/install.sh --tool claude-code --division engineering --dry-run

# 用文件指定 Agent 列表
cat > my-agents.txt <<EOF
# 我的核心团队
engineering-frontend-developer
engineering-backend-architect
product-manager
marketing-growth-hacker
EOF
./scripts/install.sh --agents-file my-agents.txt --tool cursor

# 软链接安装（更新自动传播）
./scripts/install.sh --tool claude-code --link

# 并行转换所有工具（更快）
./scripts/convert.sh --parallel --jobs 8
```

### 11.4 质量检查（贡献前运行）

```bash
# 1. Lint 你的新 Agent
./scripts/lint-agents.sh engineering/engineering-my-new-agent.md

# 2. 原创性检查（防抄袭）
./scripts/check-agent-originality.sh engineering/engineering-my-new-agent.md

# 3. 一致性全套检查
./scripts/check-divisions.sh
./scripts/check-tools.sh
./scripts/check-runbooks.sh
```

---

## 12. 贡献指南与开发规范

### 12.1 贡献类型速查

| 贡献类型 | 流程 |
|----------|------|
| 新增单个 Agent | Fork → 在对应部门创建 `.md` → 跑 lint + 原创性 → PR |
| 改进现有 Agent | Fork → 修改内容 → PR（批量改内容需先开 Discussion） |
| 新增部门 | 新建目录 → 修改 divisions.json → 修改 convert.sh AGENT_DIRS → 修改 lint-agents.sh AGENT_DIRS → 改 lint-agents.yml 路径 → check-divisions.sh |
| 新增工具 | 先开 Discussion → 按第 7.3 节 5 步流程 |
| 架构/CI 变更 | 先开 Discussion 对齐 |

### 12.2 优秀 Agent 标准

✅ **通过**:
- 狭窄而深入的专业领域
- 鲜明而独特的人格与声音
- 至少 2-3 段真实可运行代码示例
- 可衡量的成功指标（带数字）
- 步骤化的工作流程
- 真实场景测试过

❌ **避免**:
- 通用"乐于助人助手"语气
- 模糊的"我可以帮你做..."描述
- 零代码示例
- 范围太广（万金油）
- 纯理论、未经实践的方法

### 12.3 新增工具集成的"讨论优先"原则

任何新平台/新格式集成属于跨多文件架构变更，必须先在 GitHub Discussions 对齐。直接 PR 会被引导回讨论区。

### 12.4 永远会被关闭的 PR

- **提交了生成产物**: `integrations/<tool>/` 下除 README.md 外的所有文件必须在 `.gitignore` 中
- **未先讨论就批量修改现有 Agent**（即便是善意的格式化也会产生大量合并冲突）
- **近重复"换皮" Agent**（只做查找替换，比如换个国家或平台名）

---

## 13. 依赖关系图

### 13.1 脚本依赖关系

```
                    ┌─────────────────────┐
                    │    divisions.json   │── SSOT for 部门
                    │      tools.json     │── SSOT for 工具
                    │    runbooks.json    │── SSOT for 剧本
                    └─────────┬───────────┘
                              │
            ┌─────────────────┼──────────────────┐
            │                 │                   │
            ▼                 ▼                   ▼
    ┌──────────────┐  ┌──────────────┐   ┌──────────────────┐
    │  convert.sh  │  │  install.sh  │   │ check-*.sh 系列  │
    │  (16 转换器) │  │ (TUI + CLI)  │   │ 5 个质量脚本     │
    └──────┬───────┘  └──────┬───────┘   └─────────┬────────┘
           │                 │                      │
           │ source          │ source               │ source
           ▼                 ▼                      ▼
    ┌──────────────────────────────────────────────────────────┐
    │                     scripts/lib.sh                       │
    │  get_field()  get_body()  slugify()  agent_slug()       │
    │  is_agent_file()  incr()  init_ansi()                   │
    │  tui_begin/end()  read_key()  draw_frame()              │
    └──────────────────────────────────────────────────────────┘
```

### 13.2 数据流向

```
       ┌─────────────────────────────┐
       │  Agent 源文件 (18 个目录)   │
       └──────────────┬──────────────┘
                      │ (frontmatter + markdown body)
                      ▼
       ┌──────────────────────────────┐
       │   convert.sh  (per-tool 渲染)│
       │  identity / toml / mdc / ... │
       └──────────────┬───────────────┘
                      │ (integrations/<tool>/*)
                      ▼
       ┌──────────────────────────────┐
       │     install.sh (分发)        │
       │  copy / symlink              │
       │  user-scope / project-scope │
       └──────────────┬───────────────┘
                      ▼
┌───────────────────────────────────────────────┐
│  本地工具配置目录 (~/.claude, .cursor, etc.)  │
└───────────────────────────────────────────────┘
```

### 13.3 CI 触发关系

```
          Pull Request
               │
    ┌──────────┼──────────┬───────────────┬──────────────┐
    ▼          ▼          ▼               ▼              ▼
lint-agents  check-     check-        check-         (更多)
(.yml)       divisions  tools         runbooks
    │          │          │               │
    ▼          ▼          ▼               ▼
┌────────┐ ┌─────────┐ ┌──────────┐ ┌─────────────┐
│lint    │ │check-   │ │check-    │ │check-       │
│-agents ││divisions│ │-tools    │ │-runbooks    │
│+       │ │.sh      │ │.sh       │ │.sh          │
│origin  │ └────┬────┘ └────┬─────┘ └──────┬──────┘
│-ality │      │            │               │
└───┬────┘      ▼            ▼               ▼
    │     divisions.json tools.json   runbooks.json
    │     ↔ dirs            ↔ install.sh ↔ Agent slugs
    │     ↔ convert.sh      ↔ convert.sh ↔ doc 路径
    │     ↔ lint-agents.sh
    │     ↔ lint-agents.yml
    │
    ▼
  Agent 文件
   ├ frontmatter 必需字段
   ├ CRLF/LF 行尾
   └ 原创性 (8-word shingle Jaccard)
```

---

## 14. 常见问题与最佳实践

### Q1: 为什么 integrations/ 下的文件不被提交？

A: 这是设计决策。生成产物应该由用户本地或 CI 在需要时重新生成，避免与源文件漂移。只有 README 被追踪作为集成说明。新增工具时，**必须**在 `.gitignore` 中添加对应规则。

### Q2: 为什么 divisions.json / tools.json 是唯一来源？

A: 历史上出现过多次因硬编码列表导致"静默漂移"的 bug（如 healthcare 部门被遗漏）。CI 的 check-divisions.sh / check-tools.sh 强制所有引用与 SSOT 一致，彻底杜绝此问题。**永远不要在任何脚本中硬编码部门或工具列表**。

### Q3: OpenClaw 的 SOUL/AGENTS 拆分如何工作？

A: 基于标题关键词分类。`identity|communication|critical.*rule` 等进入 SOUL，其余（mission, deliverables, workflow, metrics, advanced）进入 AGENTS。未匹配标题的默认归入 AGENTS。lint-agents.sh 会检查 Agent 是否同时有两类标题（不然会有 SOUL 或 AGENTS 为空的警告）。

### Q4: 如何新增 Agent 而不触发原创性 FAIL？

A: 原创性检测使用了 **专有名词中性化**：国家和平台名被替换为空白后再比较。这意味着"把 TikTok 换成抖音然后复制粘贴"这种换皮会被高分命中。如果是市场本地化，必须让平台策略、示例、数据结构等真正不同。

### Q5: 为什么有 3 种 installKind？

A: 对应不同工具 Agent 机制的实现差异：
- `per-agent`：工具原生支持多 Agent 分别加载（最理想）
- `roster`：工具只有一个全局约定文件入口，只能合并
- `plugin`：工具提供插件扩展点，构建时打包 + 动态分发

### Q6: convert.sh 和 install.sh 的关系？

A: **分离关注点**：
- `convert.sh` 只负责：源 Agent → 工具特定格式的字节级渲染 → 写入 `integrations/`（仓库相对输出，不碰用户目录）
- `install.sh` 只负责：已有渲染产物 → 复制/软链到对应工具的正确位置 + 交互式选择 + 容量警告

这样 convert.sh 可单独跑、单独测试，install.sh 在发现缺失时会自动补跑 convert.sh（除非 `--no-convert`）。

### Q7: slugFrom 字段的三种取值？

A: 不同工具对 Agent 标识来源有不同要求：
- `source`: 从源文件名派生（claude-code/copilot — identity 工具）
- `name`: 从 frontmatter 的 `name:` 字段经 slugify() 派生（所有 per-agent 转换器）
- `null`: roster/plugin 型，无 per-agent slug

---

## 附录 A: 格式映射速查表

| Tool | format | installKind | frontmatter 保留 | 正文处理 |
|------|--------|-------------|-----------------|----------|
| Claude Code | identity | per-agent | 原样 | 原样 |
| Copilot | identity | per-agent | 原样 | 原样 |
| Gemini CLI | gemini-md | per-agent | name(→slug), description | 原样 |
| Antigravity | skill-md | per-agent | name(→slug+agency-), description | 原样 |
| Osaurus | skill-md | per-agent | name(→slug+agency-), description | 原样 |
| Codex | codex-toml | per-agent | name, description → TOML | developer_instructions |
| OpenCode | opencode-md | per-agent | name, description, color(→hex) | 原样 |
| Cursor | cursor-mdc | per-agent | description, globs="", alwaysApply=false | 原样 |
| Qwen | qwen-md | per-agent | name(→slug), description, tools(可选) | 原样 |
| ZCode | zcode-md | per-agent | (字节级同 qwen) | 原样 |
| Kimi | kimi-agent | per-agent | name(→slug), description → agent.yaml + system.md | 原样 |
| Vibe | vibe-toml | per-agent | name(→slug) → TOML, → prompt .md | 原样 |
| OpenClaw | openclaw-workspace | per-agent | emoji, vibe → IDENTITY.md | 按标题拆 SOUL/AGENTS |
| Aider | aider-conventions | roster | name, description → H2 标题 | 合并追加 |
| Windsurf | windsurf-rules | roster | name, description → H2 标题 | 合并追加 |
| Hermes | hermes-router-plugin | plugin | 全字段编入 JSON 索引 | 按需加载 |

## 附录 B: 关键脚本 Exit Code 语义

| 脚本 | exit 0 | exit 1 | exit 2 |
|------|--------|--------|--------|
| convert.sh | 全部成功 | 错误 | - |
| install.sh | 安装成功 | 选择/参数/路径错误 | - |
| lint-agents.sh | 0 错误 (可含警告) | ≥1 错误 | - |
| check-divisions.sh | 通过 | ≥1 不一致 | - |
| check-tools.sh | 通过 | ≥1 不一致 | - |
| check-runbooks.sh | 通过 | ≥1 无效引用 | 缺 python3 |
| check-agent-originality.sh | 全部 <FAIL 阈值 | ≥1 ≥FAIL 阈值 | 缺 python3 |

---

**文档版本**: 1.0
**生成日期**: 2026-09-01
**项目快照**: 273 Agents · 18 Divisions · 16 Tools · 4 Runbooks
