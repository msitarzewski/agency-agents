# 🎭 The Agency：助力工作流转型的 AI 专家库

> **触手可及的完整 AI 代理机构** —— 从前端奇才到 Reddit 社区忍者，从趣味注入器到现实检查员。每位智能体都是具备独立人格、专业流程和可靠交付物的领域专家。

[![GitHub stars](https://img.shields.io/github/stars/msitarzewski/agency-agents?style=social)](https://github.com/msitarzewski/agency-agents)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://makeapullrequest.com)
[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-pink?logo=github)](https://github.com/sponsors/msitarzewski)

---

## 🚀 这是什么？

源自 Reddit 帖子并经过数月的迭代，**The Agency** 是一个不断增长的任务交付型 AI 智能体人格合集。每位智能体都具备：

- **🎯 专业化**：在其领域拥有深厚的专业知识（而非通用的提示词模板）
- **🧠 人格驱动**：拥有独特的语气、沟通风格和处理方式
- **📋 交付导向**：产出真实的代码、流程和可衡量的成果
- **✅ 生产就绪**：经过实战检验的工作流和成功指标

**你可以把它看作**：组建你的梦想团队，只不过他们是永不疲倦、从不抱怨且使命必达的 AI 专家。

---

## ⚡ 快速入门

### 选项 1：配合 Claude Code 使用（推荐）

```bash
# 将智能体复制到你的 Claude Code 目录
cp -r agency-agents/* ~/.claude/agents/

# 现在可以在 Claude Code 会话中激活任何智能体：
# “嘿 Claude，激活前端开发模式，帮我构建一个 React 组件”
```

### 选项 2：作为参考使用

每个智能体文件包含：
- 身份与人格特质
- 核心使命与工作流
- 带有代码示例的技术交付物
- 成功指标与沟通风格

Browse the agents below and copy/adapt the ones you need!
浏览下方的智能体列表，复制或改编你需要的角色！

### 选项 3：配合其他工具使用 (Cursor, Aider, Windsurf, Gemini CLI, OpenCode)

```bash
# 第 1 步 —— 为所有受支持的工具生成集成文件
./scripts/convert.sh

# 第 2 步 —— 交互式安装（自动检测你已安装的工具）
./scripts/install.sh

# 或者直接安装到特定工具
./scripts/install.sh --tool cursor
./scripts/install.sh --tool aider
./scripts/install.sh --tool windsurf
```

详见下方的 [多工具集成](#-多工具集成) 章节。

---

## 🎨 智能体阵容 (The Agency Roster)

### 💻 工程部门 (Engineering Division)

每一行提交都在构建未来。

| 智能体 | 核心专长 | 适用场景 |
|-------|-----------|-------------|
| 🎨 [前端开发工程师](engineering/engineering-frontend-developer.md) | React/Vue/Angular，UI 实现，性能优化 | 现代 Web 应用，像素级 UI，Core Web Vitals 优化 |
| 🏗️ [后端架构师](engineering/engineering-backend-architect.md) | API 设计，数据库架构，可扩展性 | 服务端系统，微服务，云基础设施 |
| 📱 [移动端开发者](engineering/engineering-mobile-app-builder.md) | iOS/Android，React Native，Flutter | 原生及跨平台移动应用 |
| 🤖 [AI 工程师](engineering/engineering-ai-engineer.md) | ML 模型，部署，AI 集成 | 机器学习功能，数据流水线，AI 驱动的应用 |
| 🚀 [DevOps 自动化专家](engineering/engineering-devops-automator.md) | CI/CD，基础设施自动化，云运维 | 流水线开发，部署自动化，监控系统 |
| ⚡ [快速原型构建者](engineering/engineering-rapid-prototyper.md) | 快速 POC 开发，MVP 构建 | 快速概念验证，黑客松项目，快速迭代 |
| 💎 [高级开发工程师](engineering/engineering-senior-developer.md) | Laravel/Livewire，高级模式 | 复杂实现，架构决策 |
| 🔒 [安全工程师](engineering/engineering-security-engineer.md) | 威胁建模，安全代码审计，安全架构 | 应用安全，漏洞评估，安全 CI/CD |

### 🎨 设计部门 (Design Division)

让应用变得美观、易用且令人愉悦。

| 智能体 | 核心专长 | 适用场景 |
|-------|-----------|-------------|
| 🎯 [UI 设计师](design/design-ui-designer.md) | 视觉设计，组件库，设计系统 | 界面创建，品牌一致性，组件设计 |
| 🔍 [UX 研究员](design/design-ux-researcher.md) | 用户测试，行为分析，调研 | 理解用户，可用性测试，设计洞察 |
| 🏛️ [UX 架构师](design/design-ux-architect.md) | 技术架构，CSS 系统，落地实现 | 开发者友好型基础，实现指导 |
| 🎭 [品牌守护者](design/design-brand-guardian.md) | 品牌识别，一致性，定位 | 品牌战略，识别开发，准则制定 |
| 📖 [视觉讲故事的人](design/design-visual-storyteller.md) | 视觉叙事，多媒体内容 | 引人入胜的视觉故事，品牌叙事 |
| ✨ [趣味注入器](design/design-whimsy-injector.md) | 个性化，惊喜感，趣味交互 | 增加乐趣，微交互，彩蛋，品牌人格 |
| 📷 [图像提示词工程师](design/design-image-prompt-engineer.md) | AI 图像生成提示词，摄影 | 适用于 Midjourney, DALL-E, Stable Diffusion 的提示词 |

### 📢 营销部门 (Marketing Division)

通过每一次真实的互动来增长受众。

| 智能体 | 核心专长 | 适用场景 |
|-------|-----------|-------------|
| 🚀 [增长黑客](marketing/marketing-growth-hacker.md) | 快速获客，病毒循环，实验优化 | 爆发式增长，用户获取，转化率优化 |
| 📝 [内容创作者](marketing/marketing-content-creator.md) | 多平台内容，内容日历 | 内容战略，文案创作，品牌叙事 |
| 🐦 [Twitter 互动员](marketing/marketing-twitter-engager.md) | 实时互动，意见领袖 (Thought Leadership) | Twitter 战略，LinkedIn 活动，职场社交 |
| 📱 [TikTok 战略家](marketing/marketing-tiktok-strategist.md) | 病毒内容，算法优化 | TikTok 增长，爆款内容，面向 Z 世代/千禧一代受众 |
| 📸 [Instagram 策划](marketing/marketing-instagram-curator.md) | 视觉叙事，社区建设 | Instagram 战略，审美开发，视觉内容 |
| 🤝 [Reddit 社区建设者](marketing/marketing-reddit-community-builder.md) | 真实互动，价值驱动内容 | Reddit 战略，社区信任，品牌心智 |
| 📱 [应用商店优化专家](marketing/marketing-app-store-optimizer.md) | ASO，转化优化，发现度 | 应用营销，应用商店优化，应用增长 |
| 🌐 [社交媒体战略家](marketing/marketing-social-media-strategist.md) | 跨平台策略，营销活动 | 整体社交媒体策略，多平台联动 |
| 📕 [小红书专家](marketing/marketing-xiaohongshu-specialist.md) | 生活方式内容，趋势驱动策略 | 小红书增长，审美叙事，面向 Z 世代受众 |
| 💬 [微信公众号经理](marketing/marketing-wechat-official-account.md) | 订阅者互动，内容营销 | 微信公众号策略，社区建设，转化优化 |
| 🧠 [知乎战略家](marketing/marketing-zhihu-strategist.md) | 意见领袖，知识驱动互动 | 知乎权威塑造，问答策略，潜在客户获取 |

### 📊 产品部门 (Product Division)

在正确的时间构建正确的产品。

| 智能体 | 核心专长 | 适用场景 |
|-------|-----------|-------------|
| 🎯 [冲刺优先级排序员](product/product-sprint-prioritizer.md) | 敏捷规划，功能优先级排序 | 冲刺规划，资源分配，待办事项管理 |
| 🔍 [趋势研究员](product/product-trend-researcher.md) | 市场情报，竞争分析 | 市场调研，机会评估，趋势识别 |
| 💬 [反馈合成器](product/product-feedback-synthesizer.md) | 用户反馈分析，洞察提取 | 反馈分析，用户洞察，产品优先级定义 |

### 🎬 项目管理部门 (Project Management Division)

确保项目准时（且不超支）运行。

| 智能体 | 核心专长 | 适用场景 |
|-------|-----------|-------------|
| 🎬 [工坊制作人](project-management/project-management-studio-producer.md) | 高层级编排，项目组合管理 | 多项目监管，战略对齐，资源分配 |
| 🐑 [项目牧羊人](project-management/project-management-project-shepherd.md) | 跨职能协调，时间线管理 | 端到端项目协调，利益相关者管理 |
| ⚙️ [工坊运作专家](project-management/project-management-studio-operations.md) | 日常效率，流程优化 | 卓越运营，团队支持，生产力提升 |
| 🧪 [实验追踪专家](project-management/project-management-experiment-tracker.md) | A/B 测试，假设验证 | 实验管理，数据驱动决策，测试执行 |
| 👔 [高级项目经理](project-management/project-manager-senior.md) | 现实的任务规模评估，任务转化 | 规格书转化为任务，范围管理 |

### 🧪 测试部门 (Testing Division)

在问题到达用户之前发现它们。

| 智能体 | 核心专长 | 适用场景 |
|-------|-----------|-------------|
| 📸 [证据收集者](testing/testing-evidence-collector.md) | 基于截图的 QA，视觉证据 | UI 测试，视觉验证，缺陷记录 |
| 🔍 [现实检查员](testing/testing-reality-checker.md) | 基于证据的认证，质量关卡 | 生产就绪评估，质量审批，发布认证 |
| 📊 [测试结果分析师](testing/testing-test-results-analyzer.md) | 测试评估，指标分析 | 测试输出分析，质量洞察，覆盖率报告 |
| ⚡ [性能基准测试员](testing/testing-performance-benchmarker.md) | 性能测试，优化 | 速度测试，压力测试，性能调优 |
| 🔌 [API 测试员](testing/testing-api-tester.md) | API 验证，集成测试 | API 测试，端点验证，集成 QA |
| 🛠️ [工具评估员](testing/testing-tool-evaluator.md) | 技术评估，工具选型 | 工具评估，软件推荐，技术决策 |
| 🔄 [工作流优化专家](testing/testing-workflow-optimizer.md) | 流程分析，工作流改进 | 流程优化，效率提升，自动化机会识别 |
| ♿ [无障碍审计员](testing/testing-accessibility-auditor.md) | WCAG 审计，辅助技术测试 | 无障碍合规，屏幕阅读器测试，包容性设计验证 |

### 🛟 支持部门 (Support Division)

运营的坚实后盾。

| 智能体 | 核心专长 | 适用场景 |
|-------|-----------|-------------|
| 💬 [支持响应员](support/support-support-responder.md) | 客户服务，问题解决 | 客户支持，用户体验，支持运营 |
| 📊 [数据分析汇报员](support/support-analytics-reporter.md) | 数据分析，仪表盘，洞察提取 | 商业智能，KPI 追踪，数据可视化 |
| 💰 [财务追踪专家](support/support-finance-tracker.md) | 财务规划，预算管理 | 财务分析，现金流管理，业务绩效评估 |
| 🏗️ [基础设施维护员](support/support-infrastructure-maintainer.md) | 系统可靠性，性能优化 | 基础设施管理，系统运维，监控 |
| ⚖️ [法律合规检查员](support/support-legal-compliance-checker.md) | 合规性，法规，法律审查 | 法律合规，监管要求，风险管理 |
| 📑 [执行摘要生成器](support/support-executive-summary-generator.md) | C-suite 沟通，战略总结 | 高管汇报，战略沟通，决策支持 |

### 🥽 空间计算部门 (Spatial Computing Division)

构建沉浸式的未来。

| 智能体 | 核心专长 | 适用场景 |
|-------|-----------|-------------|
| 🏗️ [XR 界面架构师](spatial-computing/xr-interface-architect.md) | 空间交互设计，沉浸式 UX | AR/VR/XR 界面设计，空间计算 UX |
| 💻 [macOS 空间/Metal 工程师](spatial-computing/macos-spatial-metal-engineer.md) | Swift, Metal, 高性能 3D | macOS 空间计算，Vision Pro 原生应用 |
| 🌐 [XR 沉浸式开发](spatial-computing/xr-immersive-developer.md) | WebXR, 基于浏览器的 AR/VR | 浏览器沉浸式体验，WebXR 应用 |
| 🎮 [XR 座舱交互专家](spatial-computing/xr-cockpit-interaction-specialist.md) | 基于座舱的控制，沉浸式系统 | 座舱控制系统，沉浸式控制界面 |
| 🍎 [visionOS 空间工程师](spatial-computing/visionos-spatial-engineer.md) | Apple Vision Pro 开发 | Vision Pro 应用，空间计算体验 |
| 🔌 [终端集成专家](spatial-computing/terminal-integration-specialist.md) | 终端集成，命令行工具 | CLI 工具，终端工作流，开发工具 |

### 🎯 专项部门 (Specialized Division)

不被常规定义的一流专家。

| 智能体 | 核心专长 | 适用场景 |
|-------|-----------|-------------|
| 🎭 [智能体编排者](specialized/agents-orchestrator.md) | 多智能体协作，工作流管理 | 需要多智能体协同的复杂项目 |
| 📊 [数据分析汇报员](specialized/data-analytics-reporter.md) | 商业智能，数据洞察 | 深度数据分析，业务指标，战略洞察 |
| 🔍 [LSP/索引工程师](specialized/lsp-index-engineer.md) | 语言服务协议 (LSP)，代码智能 | 代码智能系统，LSP 实现，语义索引 |
| 📥 [销售数据提取智能体](specialized/sales-data-extraction-agent.md) | Excel 监控，销售指标提取 | 销售数据摄取，MTD/YTD/年终指标 |
| 📈 [数据汇总智能体](specialized/data-consolidation-agent.md) | 销售数据聚合，仪表盘报告 | 领地摘要，代表绩效，流水线快照 |
| 📬 [报告分发智能体](specialized/report-distribution-agent.md) | 自动化报告交付 | 基于领地的报告分发，计划发送 |
| 🔐 [代理身份与信任架构师](specialized/agentic-identity-trust.md) | 智能体身份，认证，信任验证 | 多智能体身份系统，智能体授权，审计跟踪 |

---

## 🎯 现实应用场景 (Real-World Use Cases)

### 场景 1：构建初创公司 MVP

**你的团队**：
1. 🎨 **前端开发工程师** - 构建 React 应用
2. 🏗️ **后端架构师** - 设计 API 和数据库
3. 🚀 **增长黑客** - 制定获客计划
4. ⚡ **快速原型构建者** - 快速迭代周期
5. 🔍 **现实检查员** - 发布前确保质量

**结果**：在每个阶段都拥有专业知识的支持，从而更高效地交付。

---

### 场景 2：营销活动发布

**你的团队**：
1. 📝 **内容创作者** - 开发营销内容
2. 🐦 **Twitter 互动员** - 执行 Twitter 策略
3. 📸 **Instagram 策划** - 视觉内容与故事
4. 🤝 **Reddit 社区建设者** - 真实的社区互动
5. 📊 **数据分析汇报员** - 追踪并优化表现

**结果**：多渠道协同发力，并在各平台发挥专业优势。

---

### 场景 3：企业级功能开发

**你的团队**：
1. 👔 **高级项目经理** - 范围定义与任务规划
2. 💎 **高级开发工程师** - 复杂实现
3. 🎨 **UI 设计师** - 设计系统与组件
4. 🧪 **实验追踪专家** - A/B 测试规划
5. 📸 **证据收集者** - 质量验证
6. 🔍 **现实检查员** - 生产就绪确认

**结果**：以齐全的质量关卡和文档，实现企业级的交付标准。

---

### 场景 4：全代理机构产品发现 (Discovery)

**你的团队**：8 个部门在同一使命下同步开展工作。

详见 **[Nexus 空间发现练习 (Nexus Spatial Discovery Exercise)](examples/nexus-spatial-discovery.md)** —— 一个完整的案例：8 位智能体（产品趋势研究员、后端架构师、品牌守护者、增长黑客、支持响应员、UX 研究员、项目牧羊人和 XR 界面架构师）同时部署，评估软件机会并产出统一的产品计划，涵盖市场验证、技术架构、品牌战略、进入市场、支持系统、UX 研究、项目执行及空间 UI 设计。

**结果**：在单个会话中产生全面且跨职能的产品蓝图。[查看更多案例 (More examples)](examples/)。

---

## 🤝 参与贡献

我们欢迎各位的贡献！你可以通过以下方式协助：

### 添加新智能体

1. Fork 本仓库
2. 在相应类别下创建新的智能体文件
3. 遵循智能体模板结构：
   - 带有名称、描述和颜色的 Frontmatter
   - 身份与记忆（Identity & Memory）部分
   - 核心使命（Core Mission）
   - 关键规则（领域特定）
   - 带有示例的技术交付物
   - 工作流程
   - 成功指标
4. 提交包含新智能体的 Pull Request (PR)

### 改进现有智能体

- 添加现实世界案例
- 优化代码示例
- 更新成功指标
- 改进工作流

### 分享你的成功案例

你是否成功使用了这些智能体？请在 [Discussions](https://github.com/msitarzewski/agency-agents/discussions) 中分享你的故事！

---

## 📖 智能体设计哲学

每位智能体的设计都基于：

1. **🎭 强大的人格**：不仅是模板，更是拥有性格和语气的真实角色
2. **📋 明确的交付物**：具体的产出，而非模糊的建议
3. **✅ 成功指标**：可衡量的成果和质量标准
4. **🔄 经证实的流程**：切实可行的循序渐进流程
5. **💡 学习记忆**：模式识别与持续改进能力

---

## 🎁 有什么特别之处？

### 不同于通用的 AI 提示词：
- ❌ 通用的“扮演一名开发者”提示词
- ✅ 具备人格与流程的深度专业化

### 不同于提示词库：
- ❌ 一次性的提示词合集
- ✅ 包含工作流和交付物的完整智能体系统

### 不同于 AI 工具：
- ❌ 无法自定义的黑盒工具
- ✅ 透明、可 fork、可改编的智能体人格

---

## 🎨 智能体人格亮点

> “我不只是测试你的代码 —— 我默认会找出 3-5 个问题，并且每件事都要求提供视觉证据。”
>
> -- **证据收集者** (测试部门)

> “你不是在 Reddit 上做营销 —— 你正在成为一名有价值的社区成员，而刚好你代表着某个品牌。”
>
> -- **Reddit 社区建设者** (营销部门)

> “每个趣味元素都必须具备功能性或情感目的。设计的乐趣应增强而非干扰体验。”
>
> -- **趣味注入器** (设计部门)

> “让我添加一段庆祝动画，这能缓解 40% 的任务完成焦虑。”
>
> -- **趣味注入器** (在一次 UX 评审中)

---

## 📊 数据统计

- 🎭 **61 位专业智能体**，分布在 9 个部门
- 📝 **10,000+ 行**人格定义、流程及代码示例
- ⏱️ **数月的迭代**，源自现实场景的使用
- 🌟 **实战检验**，适用于生产环境
- 💬 **发布 12 小时内**在 Reddit 获取 50+ 份请求

---

## 🔌 多工具集成

The Agency 原生支持 Claude Code，并提供转换与安装脚本，让你可以在所有主流代理式编程工具中使用相同的智能体。

### 受支持的工具

- **[Claude Code](https://claude.ai/code)** — 原生支持 `.md` 智能体，无需转换 → `~/.claude/agents/`
- **[Antigravity](https://github.com/google-gemini/antigravity)** — 每个智能体一个 `SKILL.md` → `~/.gemini/antigravity/skills/`
- **[Gemini CLI](https://github.com/google-gemini/gemini-cli)** — 扩展 + `SKILL.md` 文件 → `~/.gemini/extensions/agency-agents/`
- **[OpenCode](https://opencode.ai)** — `.md` 智能体文件 → `.opencode/agent/`
- **[Cursor](https://cursor.sh)** — `.mdc` 规则文件 → `.cursor/rules/`
- **[Aider](https://aider.chat)** — 单个 `CONVENTIONS.md` → `./CONVENTIONS.md`
- **[Windsurf](https://codeium.com/windsurf)** — 单个 `.windsurfrules` → `./.windsurfrules`

---

### ⚡ 快速安装

**第 1 步 —— 生成集成文件：**
```bash
./scripts/convert.sh
```

**第 2 步 —— 安装（交互式，自动检测你的工具）：**
```bash
./scripts/install.sh
```

安装程序会扫描你系统中已安装的工具，显示复选框界面，让你选择需要安装的内容：

```
  +------------------------------------------------+
  |   The Agency -- 工具安装程序                   |
  +------------------------------------------------+

  系统扫描：[*] = 已在本机检测到

  [x]  1)  [*]  Claude Code     (claude.ai/code)
  [x]  2)  [*]  Antigravity     (~/.gemini/antigravity)
  [ ]  3)  [ ]  Gemini CLI      (gemini extension)
  [ ]  4)  [ ]  OpenCode        (opencode.ai)
  [x]  5)  [*]  Cursor          (.cursor/rules)
  [ ]  6)  [ ]  Aider           (CONVENTIONS.md)
  [ ]  7)  [ ]  Windsurf        (.windsurfrules)

  [1-7] 切换状态   [a] 全部   [n] 无   [d] 已检测
  [Enter] 安装     [q] 退出
```

**或者直接安装特定工具：**
```bash
./scripts/install.sh --tool cursor
./scripts/install.sh --tool opencode
./scripts/install.sh --tool antigravity
```

**非交互式安装（用于 CI/脚本）：**
```bash
./scripts/install.sh --no-interactive --tool all
```

---

### 工具专用说明

<details>
<summary><strong>Claude Code</strong></summary>

智能体可以直接从仓库复制到 `~/.claude/agents/` —— 无需转换。

```bash
./scripts/install.sh --tool claude-code
```

然后在 Claude Code 中激活：
```
Use the Frontend Developer agent to review this component.
```

详见 [integrations/claude-code/README.md](integrations/claude-code/README.md)。
</details>

<details>
<summary><strong>Antigravity (Gemini)</strong></summary>

每位智能体都会成为 `~/.gemini/antigravity/skills/agency-<slug>/` 下的一个技能。

```bash
./scripts/install.sh --tool antigravity
```

在 Antigravity 支撑的 Gemini 中激活：
```
@agency-frontend-developer review this React component
```

详见 [integrations/antigravity/README.md](integrations/antigravity/README.md)。
</details>

<details>
<summary><strong>Gemini CLI</strong></summary>

安装为具有 61 个技能和一份 manifest 的 Gemini CLI 扩展。

```bash
./scripts/install.sh --tool gemini-cli
```

详见 [integrations/gemini-cli/README.md](integrations/gemini-cli/README.md)。
</details>

<details>
<summary><strong>OpenCode</strong></summary>

智能体会被放置在项目根目录的 `.opencode/agent/` 下（项目范围）。

```bash
cd /your/project
/path/to/agency-agents/scripts/install.sh --tool opencode
```

或者全局安装：
```bash
mkdir -p ~/.config/opencode/agent
cp integrations/opencode/agent/*.md ~/.config/opencode/agent/
```

Activate in OpenCode:
```
Use the Backend Architect agent to design this API.
```

详见 [integrations/opencode/README.md](integrations/opencode/README.md)。
</details>

<details>
<summary><strong>Cursor</strong></summary>

每位智能体都会成为项目 `.cursor/rules/` 下的一个 `.mdc` 规则文件。

```bash
cd /your/project
/path/to/agency-agents/scripts/install.sh --tool cursor
```

当 Cursor 在项目中检测到规则时会自动应用。也可以显式引用：
```
Use the @security-engineer rules to review this code.
```

详见 [integrations/cursor/README.md](integrations/cursor/README.md)。
</details>

<details>
<summary><strong>Aider</strong></summary>

所有智能体会合并为一个单一的 `CONVENTIONS.md` 文件，Aider 会自动读取。

```bash
cd /your/project
/path/to/agency-agents/scripts/install.sh --tool aider
```

然后引用智能体：
```
Use the Frontend Developer agent to refactor this component.
```

详见 [integrations/aider/README.md](integrations/aider/README.md)。
</details>

<details>
<summary><strong>Windsurf</strong></summary>

所有智能体会合并为项目根目录下的 `.windsurfrules`。

```bash
cd /your/project
/path/to/agency-agents/scripts/install.sh --tool windsurf
```

在 Windsurf's Cascade 中引用智能体：
```
Use the Reality Checker agent to verify this is production ready.
```

详见 [integrations/windsurf/README.md](integrations/windsurf/README.md)。
</details>

---

### 修改后重新生成

当你添加新智能体或编辑现有智能体后，需重新生成所有集成文件：

```bash
./scripts/convert.sh        # 全部重新生成
./scripts/convert.sh --tool cursor   # 仅重新生成特定工具
```

---

## 🗺️ 路线图

- [ ] 交互式智能体选择 Web 工具
- [x] 多智能体工作流示例 —— 见 [examples/](examples/)
- [x] 多工具集成脚本 (Claude Code, Antigravity, Gemini CLI, OpenCode, Cursor, Aider, Windsurf)
- [ ] 智能体设计视频教程
- [ ] 社区智能体市场
- [ ] 用于项目匹配的智能体“性格测试”
- [ ] “本周之星智能体”展示丛书
- [ ] 用于项目匹配的“智能体性格测试”

---

## 🌐 社区翻译与本地化

由社区维护的翻译和区域适配版。这些由第三方独立维护 —— 覆盖范围和版本兼容性请参考各自仓库。

| 语言 | 维护者 | 链接 | 备注 |
|----------|-----------|------|-------|
| 🇨🇳 简体中文 (zh-CN) | [@jnMetaCode](https://github.com/jnMetaCode) | [agency-agents-zh](https://github.com/jnMetaCode/agency-agents-zh) | 26 个已翻译智能体 + 4 个中国市场专属智能体 |

想要添加翻译？请开启一个 Issue，我们会在此列出。

---

## 📜 许可证

MIT 许可证 - 自由使用，不论是商业还是个人用途。如果能注明出处我们将不胜感激，但非强制要求。

---

## 🙏 致谢

源自 Reddit 上关于 AI 智能体专项化的讨论。感谢社区提供的反馈、请求和灵感。

特别感谢在发布前 12 小时内提出请求的 50 多位 Reddit 用户 —— 你们证明了市场对于真实且专项化的 AI 智能体系统的需求。

---

## 💬 社区

- **GitHub Discussions**: [分享你的成功案例](https://github.com/msitarzewski/agency-agents/discussions)
- **Issues**: [报告 Bug 或请求功能](https://github.com/msitarzewski/agency-agents/issues)
- **Reddit**: 加入 r/ClaudeAI 的讨论
- **Twitter/X**: 在分享时带上话题 #TheAgency

---

## 🚀 开启旅程

1. **浏览**上方的智能体并寻找符合你需求的专家
2. **复制**智能体到 `~/.claude/agents/` 以集成到 Claude Code
3. **激活**智能体，在 Claude 对话中引用他们
4. **自定义**智能体人格和工作流，以满足你的特定需求
5. **分享**你的成果并回馈社区

---

<div align="center">

**🎭 The Agency：你的 AI 梦想团队正待命 🎭**

[⭐ Star 此仓库](https://github.com/msitarzewski/agency-agents) • [🍴 Fork 仓库](https://github.com/msitarzewski/agency-agents/fork) • [🐛 报告问题](https://github.com/msitarzewski/agency-agents/issues) • [❤️ 赞助](https://github.com/sponsors/sitarzewski)

由社区倾力打造，服务于社区

</div>
