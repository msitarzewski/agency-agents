# NEXUS 全管线教程：从入门到进阶

> **NEXUS**（Network of EXperts, Unified in Strategy）把 The Agency 仓库里的众多智能体，组织成**有阶段、有质量门、有交接协议**的多智能体流水线。**全管线**指从 Phase 0（发现）到 Phase 6（运营）的完整七阶段闭环；你可以按项目规模选用 **NEXUS-Full**、**NEXUS-Sprint** 或 **NEXUS-Micro**，原理相同，只是激活范围与时长不同。

本文档面向已克隆 [agency-agents](https://github.com/agency-ai/agency-agents) 的使用者，与官方英文快速指南 [strategy/QUICKSTART.md](../strategy/QUICKSTART.md) 互补：这里用中文讲清**怎么选模式、怎么对话里驱动、怎么进阶到 playbook 与 runbook**。

---

## 目录

1. [你需要先具备什么](#1-你需要先具备什么)
2. [初级：十分钟跑通第一次](#2-初级十分钟跑通第一次)
3. [初级：三种模式怎么选](#3-初级三种模式怎么选)
4. [中级：七阶段与核心机制](#4-中级七阶段与核心机制)
5. [中级：交接与质量门实操](#5-中级交接与质量门实操)
6. [进阶：Playbook 与并行工作流](#6-进阶playbook-与并行工作流)
7. [进阶：Runbook 场景化部署](#7-进阶runbook-场景化部署)
8. [进阶：编排、状态报告与裁剪](#8-进阶编排状态报告与裁剪)
9. [常见问题与排错](#9-常见问题与排错)
10. [文档地图（自学路径）](#10-文档地图自学路径)

---

## 1. 你需要先具备什么

### 1.1 仓库与智能体安装（任选其一）

- **最小用法**：不安装脚本，直接在仓库里打开各智能体 `.md`，把角色说明复制进对话。
- **推荐用法**：按 [用户使用文档](./用户使用文档.md) 执行 `./scripts/convert.sh` 与 `./scripts/install.sh`，把智能体同步到 Cursor、Claude Code 等工具，便于 `@` 规则或按名称引用。

NEXUS 的「控制器」角色是 **Agents Orchestrator**（在 `specialized/` 下）。全管线对话里应**明确让模型扮演 Orchestrator**，并声明模式（Full / Sprint / Micro）。

### 1.2 心理预期

- NEXUS 是**部署教义（doctrine）**：约定谁在什么阶段出场、如何交接、如何验收；不是自动运行的 CI。
- 质量靠你（和模型）**坚持模板**：证据、重试上限、阶段门——若对话中跳过这些，效果会退回「单点拼盘智能体」。

---

## 2. 初级：十分钟跑通第一次

**目标**：在同一段对话里，用一段「启动提示」让模型进入 NEXUS 语境，并说出接下来会按哪些阶段推进。

### 步骤

1. 打开 [strategy/QUICKSTART.md](../strategy/QUICKSTART.md)。
2. 根据目标复制 **NEXUS-Full**、**NEXUS-Sprint** 或 **NEXUS-Micro** 中**整块**提示模板。
3. 替换占位符：
   - `[YOUR PROJECT NAME]` / `[FEATURE/MVP NAME]` → 你的项目或功能名；
   - `Specification` / 需求描述 → 一两段背景 + 链接或路径（若有 PRD/仓库路径可写上）。
4. 在消息中**追加**你的约束，例如：技术栈、截止日期、必须跳过的阶段（如 Sprint 常写「Skip Phase 0」）。
5. 发送后，要求 Orchestrator **先输出**：当前模式、阶段列表、本阶段将激活的角色名、第一个质量门是什么。

**验收**：你能看到对方按「阶段 + 质量门 + 角色」组织回答，而不是零散闲聊。

**手把手案例（已填好项目名与可复制提示）**：[NEXUS十分钟上手-手把手案例.md](./NEXUS十分钟上手-手把手案例.md)

> 英文原版模板与角色列表以 QUICKSTART 为准；下文高级部分会指向各 Phase 的详细 playbook。

---

## 3. 初级：三种模式怎么选

| 你的目标 | 模式 | 大致智能体规模 | 典型周期 |
|----------|------|----------------|----------|
| 从 0 到完整产品生命周期 | **NEXUS-Full** | 全部分部按需上场 | 约 12–24 周（按项目） |
| 功能、MVP、迭代交付 | **NEXUS-Sprint** | 约 15–25 个角色 | 约 2–6 周 |
| 修 Bug、单次活动、审计、专项研究 | **NEXUS-Micro** | 约 5–10 个角色 | 约 1–5 天 |

**实用建议**：

- 第一次用 NEXUS，可先选 **NEXUS-Micro**（例如「修一个 Bug」模板）感受 **Dev→QA→证据** 的闭环。
- 已有明确需求文档、要做可演示增量时，用 **NEXUS-Sprint**。
- 战略级、多部门长期并行，用 **NEXUS-Full**；同时要有耐心维护 [状态报告](#8-进阶编排状态报告与裁剪) 与阶段门记录。

---

## 4. 中级：七阶段与核心机制

七阶段在 [strategy/nexus-strategy.md](../strategy/nexus-strategy.md) 中有完整定义，下面是**中文理解版**：

| 阶段 | 名称（意译） | 你在管什么 |
|------|----------------|------------|
| **Phase 0** | 情报与发现 | 市场、用户、竞品、数据、合规与工具选型等输入 |
| **Phase 1** | 战略与架构 | 产品叙事、路线图、技术架构、品牌与财务边界 |
| **Phase 2** | 基础与脚手架 | CI/CD、骨架代码、设计体系、可观测性等「能跑起来」 |
| **Phase 3** | 构建与迭代 | **Dev↔QA 循环**：逐项实现、逐项验收 |
| **Phase 4** | 质量与加固 | 性能、安全与合规、现实检验（Reality Checker）等 |
| **Phase 5** | 发布与增长 | GTM、内容、投放与发布工程 |
| **Phase 6** | 运营与演进 | 数据、支持、基础设施与持续改进 |

**四条可并行轨道**（在 Phase 3 等阶段常被强调）：**核心产品**、**增长**、**质量与运维**、**品牌与体验**。进阶时读 `phase-3-build.md` 里的轨道划分，可减少「所有人都串行等一个角色」的浪费。

### 四个「30 秒概念」（务必记住）

1. **质量门（Quality Gate）**：阶段推进前必须满足约定标准，且**要有证据**（日志、截图、测试报告等），不能凭口头「已完成」。
2. **Dev↔QA 循环**：每个任务：实现 → QA → **PASS** 才进入下一任务；**FAIL** 则反馈修改，通常约定**最多 3 次**重试后升级（escalation）。
3. **交接（Handoff）**：上游向下游传递**结构化上下文**，避免「下一个智能体从零猜」。
4. **证据优于断言（Evidence over claims）**：Reality Checker、Evidence Collector 等角色的价值在于**倒逼可验证产出**。

---

## 5. 中级：交接与质量门实操

### 5.1 交接模板在哪里

打开 [strategy/coordination/handoff-templates.md](../strategy/coordination/handoff-templates.md)，其中包含：

- 通用 **NEXUS Handoff Document**
- **QA PASS / FAIL** 格式
- **升级（Escalation）** 报告
- **阶段门（Phase Gate）**、**Sprint**、**事故** 等交接变体

**用法**：每当切换「主要责任智能体」时，让模型**先填一份 handoff**，再开始下一段工作；你只需复制模板到对话并说：「按 NEXUS Handoff 格式输出。」

### 5.2 各角色的「激活提示」

[strategy/coordination/agent-activation-prompts.md](../strategy/coordination/agent-activation-prompts.md) 提供 Orchestrator、前后端、UX、品牌、Evidence Collector、API Tester 等**可复制提示**。中级用户应学会：**同一项目里统一引用同一份架构路径、设计 token 路径、品牌规范路径**，便于 QA 按同一标准验收。

### 5.3 质量门在 playbook 里会写细

每个阶段的可交付物与门槛，在对应 playbook 中展开，例如 Phase 2 会列出 CI、数据库、前端骨架、监控等**阈值与证据类型**。阅读时不必一次读完：进行到哪一 Phase 就只读哪一份。

---

## 6. 进阶：Playbook 与并行工作流

`strategy/playbooks/` 下是每个阶段的「作战手册」：

| 文件 | 内容焦点 |
|------|-----------|
| [phase-0-discovery.md](../strategy/playbooks/phase-0-discovery.md) | 发现阶段产出与情报类角色协作 |
| [phase-1-strategy.md](../strategy/playbooks/phase-1-strategy.md) | 战略、架构与规划类交付 |
| [phase-2-foundation.md](../strategy/playbooks/phase-2-foundation.md) | 脚手架、DevOps、并行工作流与 Phase 2 质量门 |
| [phase-3-build.md](../strategy/playbooks/phase-3-build.md) | Dev↔QA、按任务类型分派开发者/QA、并行构建轨道 |
| [phase-4-hardening.md](../strategy/playbooks/phase-4-hardening.md) | 加固、测试与发布前质量 |
| [phase-5-launch.md](../strategy/playbooks/phase-5-launch.md) | 上市与增长动作 |
| [phase-6-operate.md](../strategy/playbooks/phase-6-operate.md) | 长期运营与再激活 NEXUS 循环 |

**进阶练习**（建议顺序）：

1. 只读 **当前阶段** playbook 的目录与小标题，让 Orchestrator **对照 playbook 列一份检查清单**。
2. 在 Phase 2–3 **显式要求**并行轨道：例如「Track A 基础设施 + Track B 应用骨架」由谁负责、何时汇合。
3. 在 Phase 3 为每个任务指定 **Developer + QA** 对（见 nexus-strategy 中的任务类型表），避免所有测试都堆给同一个 QA 角色。

---

## 7. 进阶：Runbook 场景化部署

`strategy/runbooks/` 提供**按场景裁剪过的 NEXUS 变体**（含建议模式与周期）：

| Runbook | 典型模式与周期（见文件抬头） |
|---------|------------------------------|
| [scenario-startup-mvp.md](../strategy/runbooks/scenario-startup-mvp.md) | MVP / 创业场景 |
| [scenario-enterprise-feature.md](../strategy/runbooks/scenario-enterprise-feature.md) | 企业级功能 |
| [scenario-marketing-campaign.md](../strategy/runbooks/scenario-marketing-campaign.md) | 市场活动 |
| [scenario-incident-response.md](../strategy/runbooks/scenario-incident-response.md) | 线上事故响应 |

**用法**：先读 runbook 的 **Mode / Duration / Agents** 建议，把其中角色序列合并进你的 Orchestrator 启动提示；runbook 本质是**经裁剪的 NEXUS-Sprint/Micro**，更贴近真实项目类型。

---

## 8. 进阶：编排、状态报告与裁剪

### 8.1 Pipeline Status Report

在 [strategy/nexus-strategy.md](../strategy/nexus-strategy.md) **Appendix B** 有 **NEXUS Pipeline Status Report** 模板（阶段进度表、当前任务、QA 重试次数、风险登记等）。

**建议**：长会话每完成一个阶段门或每半天，让 Orchestrator **按该模板输出一次快照**，便于人类监督与续聊时「冷启动」。

### 8.2 与中文智能体目录联动

仓库内 [智能体全目录与组合流程.md](./智能体全目录与组合流程.md) 按业务场景列出**推荐角色组合**；可与 NEXUS 阶段叠加使用：阶段决定「节奏与门」，中文目录决定「这一公司里具体点名哪些角色」。

### 8.3 高管视角与对外汇报

若需要一页纸说清「为什么这样组织智能体」，可读 [strategy/EXECUTIVE-BRIEF.md](../strategy/EXECUTIVE-BRIEF.md)（英文），把其中结论转写进你的内部立项材料。

### 8.4 全管线示例输出

多智能体协作的**完整示例**见 [examples/nexus-spatial-discovery.md](../examples/nexus-spatial-discovery.md) 与 [examples/README.md](../examples/README.md)：适合观察「多角色并行 discovery」类会话的长输出形态（与空间计算主题相关，但结构可类比到其他领域）。

---

## 9. 常见问题与排错

**Q：模型不按阶段执行，总是跳过 QA。**  
A：在每条大任务前重复三条硬规则：**Dev↔QA**、**最多 3 次重试**、**无证据不过门**；并要求先输出 QA 验收标准再允许实现。

**Q：角色太多，上下文装不下。**  
A：改用 **NEXUS-Sprint / Micro**，或分会话运行：上一会话结尾用 **Handoff + Status Report** 冻结状态，下一会话用 Orchestrator 提示「Resume Phase N」并粘贴报告。

**Q：中文项目，智能体定义是英文。**  
A：在系统或首条消息中说明「对用户可见输出用中文，专有名词可保留英文」；角色名仍用仓库中的英文名称以便和文件对应。

**Q：strategy/ 下的 md 没有出现在 convert 后的规则里？**  
A：按 [开发文档](./开发文档.md) 说明，`strategy/` **不是** `convert.sh` 默认扫描的智能体根目录；策略文檔以**人工打开 + 复制提示**为主，或与 Orchestrator 提示内联摘要。

**Q：和「只点名单个专家」有什么区别？**  
A：单专家适合小任务；NEXUS 全管线的增量价值在于**阶段门 + 交接 + 可重复的状态报告**，适合多人格、长周期、强验收项目。

---

## 10. 文档地图（自学路径）

| 顺序 | 文档 | 用途 |
|------|------|------|
| 1 | [用户使用文档](./用户使用文档.md) | 安装与引用智能体 |
| 2 | [strategy/QUICKSTART.md](../strategy/QUICKSTART.md) | 英文可复制启动模板（权威原文） |
| 3 | [strategy/nexus-strategy.md](../strategy/nexus-strategy.md) | 完整教义、协调矩阵、附录模板 |
| 4 | `strategy/playbooks/phase-*.md` | 分阶段 deep dive |
| 5 | `strategy/runbooks/scenario-*.md` | 按场景裁剪 |
| 6 | [coordination/handoff-templates.md](../strategy/coordination/handoff-templates.md) | 交接与 QA 格式 |
| 7 | [coordination/agent-activation-prompts.md](../strategy/coordination/agent-activation-prompts.md) | 单角色激活短文 |
| 8 | [智能体全目录与组合流程.md](./智能体全目录与组合流程.md) | 中文场景与角色组合参考 |

---

**一句话总结**：先用 **QUICKSTART** 选模式并粘贴启动提示，再用 **playbook** 管阶段细节，用 **handoff + Status Report** 管上下文与质量，用 **runbook** 对齐真实项目形状——这就是 NEXUS 全管线的完整用法。
