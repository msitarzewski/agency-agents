# ⚡ NEXUS 快速入门指南 (Quick-Start Guide)

> **从零开始，5 分钟内启动编排好的多智能体流水线。**

---

## 什么是 NEXUS？

**NEXUS** (Network of EXperts, Unified in Strategy，专家网络，统一战略) 将本机构的 AI 专家转化为一个协调的流水线。NEXUS 不会一次只启动一个智能体并寄希望于他们能协作，而是精确定义了谁、在什么时候、做什么，以及每一步如何验证质量。

## 选择你的模式 (Choose Your Mode)

| 我想要... | 使用模式 | 智能体数量 | 时间预期 |
|-------------|-----|--------|------|
| 从头开始构建完整产品 | **NEXUS-Full** | 全员 | 12-24 周 |
| 构建功能或 MVP | **NEXUS-Sprint** | 15-25 位 | 2-6 周 |
| 执行特定任务（修复 Bug、营销活动、审计） | **NEXUS-Micro** | 5-10 位 | 1-5 天 |

---

## 🚀 NEXUS-Full：启动完整项目

**复制此提示词以激活完整流水线：**

```
激活 NEXUS-Full 模式下的智能体编排者 (Agents Orchestrator)。

项目名称：[你的项目名称]
项目规格：[描述你的项目或提供规格链接]

执行完整的 NEXUS 流水线：
- 阶段 0：发现 (Trend Researcher, Feedback Synthesizer, UX Researcher, Analytics Reporter, Legal Compliance Checker, Tool Evaluator)
- 阶段 1：战略 (Studio Producer, Senior Project Manager, Sprint Prioritizer, UX Architect, Brand Guardian, Backend Architect, Finance Tracker)
- 阶段 2：基础 (DevOps Automator, Frontend Developer, Backend Architect, UX Architect, Infrastructure Maintainer)
- 阶段 3：构建 (Dev↔QA 循环 — 所有工程智能体 + Evidence Collector)
- 阶段 4：加固 (Reality Checker, Performance Benchmarker, API Tester, Legal Compliance Checker)
- 阶段 5：发布 (Growth Hacker, Content Creator, 所有营销智能体, DevOps Automator)
- 阶段 6：运营 (Analytics Reporter, Infrastructure Maintainer, Support Responder)

在每个阶段之间设立质量关卡。所有评估均要求提供证据。
每项任务在升级前最多重试 3 次。
```

---

## 🏃 NEXUS-Sprint：构建功能或 MVP

**复制此提示词：**

```
激活 NEXUS-Sprint 模式下的智能体编排者 (Agents Orchestrator)。

功能/MVP：[描述你要构建的内容]
时间线：[目标周数]
跳过阶段 0（市场已验证）。

冲刺团队：
- PM：Senior Project Manager, Sprint Prioritizer
- 设计：UX Architect, Brand Guardian
- 工程：Frontend Developer, Backend Architect, DevOps Automator
- QA：Evidence Collector, Reality Checker, API Tester
- 支持：Analytics Reporter

从阶段 1 架构和冲刺规划开始。
为所有实现任务运行 Dev↔QA 循环。
发布前需获得现实检查员 (Reality Checker) 的批准。
```

---

## 🎯 NEXUS-Micro：执行特定任务

**选择你的场景并复制提示词：**

### 修复 Bug
```
激活后端架构师 (Backend Architect) 调查并修复 [BUG 描述]。
修复后，激活 API 测试员 (API Tester) 验证修复效果。
随后激活证据收集者 (Evidence Collector) 确认无视觉回退。
```

### 运行营销活动
```
激活社交媒体战略家 (Social Media Strategist) 作为 [活动描述] 的活动负责人。
团队成员：Content Creator, Twitter Engager, Instagram Curator, Reddit Community Builder。
所有内容在发布前均需经品牌守护者 (Brand Guardian) 审核。
数据分析汇报员 (Analytics Reporter) 每日追踪效果。
```

### 进行合规审计
```
激活法律合规检查员 (Legal Compliance Checker) 进行全面的合规审计。
范围：[GDPR / CCPA / HIPAA / 全部]
审计后，激活执行摘要生成器 (Executive Summary Generator) 创建利益相关者报告。
```

### 调查性能问题
```
激活性能基准测试员 (Performance Benchmarker) 诊断性能问题。
范围：[API 响应时间 / 页面加载 / 数据库查询 / 全部]
诊断后，激活基础设施维护员 (Infrastructure Maintainer) 进行优化。
```

---

## 📁 战略文档 (Strategy Documents)

| 文档 | 用途 | 路径 |
|----------|---------|----------|
| **主战略 (Master Strategy)** | 完整的 NEXUS 准则 | `strategy/nexus-strategy.md` |
| **阶段 0-6 剧本** | 各阶段分布操作指南 | `strategy/playbooks/phase-X.md` |
| **激活提示词** | 开箱即用的智能体提示词 | `strategy/coordination/agent-activation-prompts.md` |
| **交接模板** | 标准化的交接格式 | `strategy/coordination/handoff-templates.md` |
| **场景运行手册** | MVP、企业功能、营销、事故响应等运行手册 | `strategy/runbooks/scenario-X.md` |

---

## 🔑 30 秒核心概念

1. **质量关卡 (Quality Gates)** —— 没通过带证据的审批，绝不进入下一阶段。
2. **开发-质检循环 (Dev↔QA Loop)** —— 每项任务先构建后测试；通过 (PASS) 则继续，失败 (FAIL) 则重试（最高 3 次）。
3. **交接 (Handoffs)** —— 智能体之间结构化的上下文传递（绝不“冷启动”）。
4. **现实检查员 (Reality Checker)** —— 最终质量权威；默认给出“仍需改进”的结论。
5. **智能体编排者 (Agents Orchestrator)** —— 管理整个流程的流水线控制器。
6. **证据胜过言语** —— 截图、测试结果和数据，而非空口白话。

---

## 🎭 智能体一览

```
工程                 │ 设计               │ 营销
前端开发              │ UI 设计师          │ 增长黑客
后端架构师            │ UX 研究员           │ 内容创作者
移动端开发者          │ UX 架构师           │ Twitter 互动员
AI 工程师             │ 品牌守护者         │ TikTok 战略家
运维自动化专家        │ 视觉讲故事的人      │ Instagram 策划
快速原型构建者        │ 趣味注入器         │ Reddit 社区建设者
高级开发工程师        │ 图像提示词工程师    │ 应用商店优化专家
                    │                    │ 社交媒体战略家
────────────────────┼─────────────────────┼──────────────────────
产品                 │ 项目管理           │ 测试
冲刺优先级排序员      │ 工坊制作人          │ 证据收集者
趋势研究员            │ 项目牧羊人         │ 现实检查员
反馈合成器            │ 工坊运作专家       │ 测试结果分析师
                     │ 实验追踪专家       │ 性能基准测试员
                     │ 高级项目经理       │ API 测试员
                     │                    │ 工具评估员
────────────────────┼─────────────────────┼──────────────────────
支持                 │ 空间计算           │ 专项
支持响应员            │ XR 界面架构师       │ 智能体编排者
数据分析汇报员        │ macOS 空间/Metal    │ 数据分析汇报员
财务追踪专家          │ XR 沉浸式开发       │ LSP/索引工程师
基础设施维护员        │ XR 座舱专家         │ 销售数据提取
法律合规检查          │ visionOS 空间      │ 数据汇总
执行摘要生成          │ 终端集成           │ 报告分发
```

---

<div align="center">

**选择模式。遵循剧本。信任流水线。**

`strategy/nexus-strategy.md` — 完整准则

</div>
