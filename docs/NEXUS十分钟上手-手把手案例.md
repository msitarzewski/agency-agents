# NEXUS「十分钟跑通第一次」手把手案例教程

本文档是 [NEXUS全管线教程.md](./NEXUS全管线教程.md) **第 2 节**的展开版：用**一个写好的虚构项目**，带你从打开文档到发出第一条 NEXUS 启动提示，并核对模型回复是否「像 Orchestrator」。

- **预计时间**：准备约 3 分钟 + 第一条对话约 2–5 分钟 + 核对与纠偏约 3 分钟（合计约 10–15 分钟）。
- **本案例选用的模式**：**NEXUS-Sprint**（功能迭代，跳过 Phase 0）。若你只想更短闭环，文末附有 **NEXUS-Micro** 微型案例。
- **你需要**：已克隆本仓库；任意支持长上下文的对话式 AI（Cursor、Claude、ChatGPT 等均可）；**不必**先跑完 `install.sh`。

---

## 案例背景（已替你填好占位符）

| 字段 | 本案例取值 |
|------|------------|
| 项目 / 功能名 | **TeamPulse**：团队任务看板（已有 Web 版） |
| 本次迭代 | 新增 **「逾期任务邮件提醒」**：每日定时扫描 `due_date < today` 且未完成的任务，向负责人发摘要邮件 |
| 技术约束 | 后端已有 **Node.js + PostgreSQL**；邮件用 **SMTP**；定时用 **cron 或队列 worker**（由实现阶段再定） |
| 周期 | **3 周内**可上线灰度 |
| 市场假设 | 内部工具，**跳过 Phase 0**（不重新做大规模市场调研） |

下文所有「可复制提示」里的英文角色名与仓库内智能体文件名一致，便于你对照 `strategy/QUICKSTART.md`。

---

## 第一步：打开权威模板（1 分钟）

1. 在本地仓库中打开：[strategy/QUICKSTART.md](../strategy/QUICKSTART.md)。
2. 定位到 **「NEXUS-Sprint: Build a Feature or MVP」** 小节。
3. 你会看到一段用三反引号包起来的英文提示模板——**不要只抄标题**，要复制**整块**模板（从 `Activate Agents Orchestrator` 到 `Reality Checker approval required before launch.`）。

> 说明：本案例用 Sprint 而不是 Full，是因为第一次上手时阶段更清晰、角色数量更可控；掌握同样流程后，把模板换成 QUICKSTART 里的 **NEXUS-Full** 即可。

---

## 第二步：把占位符换成案例里的真值（2 分钟）

在复制出来的英文模板中，手工替换：

| 原文占位符 | 替换为 |
|------------|--------|
| `[DESCRIBE WHAT YOU'RE BUILDING]` | `TeamPulse: overdue-task email digest for assignees. Daily job scans PostgreSQL for tasks where due_date < today AND status != done, aggregates by assignee, sends SMTP email summary. Stack: existing Node.js API + PostgreSQL.` |
| `[TARGET WEEKS]` | `3` |

确认模板里仍然包含这些**硬性句子**（不要删）：

- `Skip Phase 0 (market already validated).`
- `Begin at Phase 1 with architecture and sprint planning.`
- `Run Dev↔QA loops for all implementation tasks.`
- `Reality Checker approval required before launch.`

---

## 第三步：追加「中文输出 + 第一条必须交付物」（1 分钟）

在英文模板**末尾**另起一段，粘贴下面这段（可一字不改）：

```
Additional instructions for this session:
1. Respond to me in Chinese for all user-visible explanations and summaries. Keep agent names in English as in the template.
2. In your FIRST reply, do NOT start implementing code. Instead, output ALL of the following sections:
   (A) Current NEXUS mode and why Sprint fits this task
   (B) Phase list from Phase 1 through Phase 6 (one line each, Chinese OK)
   (C) For Phase 1 only: which agents you will activate first, in order, and what each produces
   (D) The first quality gate: name, criteria (bullet points), and what evidence is required before moving to Phase 2
3. Enforce: quality gates between phases; evidence-based QA; max 3 retries per task before escalation.
```

这样你就完成了主教程第 2 节里的步骤 3–4（替换占位符 + 追加约束）。

---

## 第四步：第一条完整消息（直接整段复制使用）

把 **第二步改好的 Sprint 模板** 与 **第三步的中文追加** 拼成**一条用户消息**发送。若你希望零拼装，可直接复制下面这一整段（已内含本案例占位符与中文约束）：

```
Activate Agents Orchestrator in NEXUS-Sprint mode.

Feature/MVP: TeamPulse — overdue-task email digest for assignees. Daily job scans PostgreSQL for tasks where due_date < today AND status != done, aggregates by assignee, sends SMTP email summary. Existing stack: Node.js API + PostgreSQL.
Timeline: 3 weeks
Skip Phase 0 (market already validated).

Sprint team:
- PM: Senior Project Manager, Sprint Prioritizer
- Design: UX Architect, Brand Guardian
- Engineering: Frontend Developer, Backend Architect, DevOps Automator
- QA: Evidence Collector, Reality Checker, API Tester
- Support: Analytics Reporter

Begin at Phase 1 with architecture and sprint planning.
Run Dev↔QA loops for all implementation tasks.
Reality Checker approval required before launch.

Additional instructions for this session:
1. Respond to me in Chinese for all user-visible explanations and summaries. Keep agent names in English as in the template.
2. In your FIRST reply, do NOT start implementing code. Instead, output ALL of the following sections:
   (A) Current NEXUS mode and why Sprint fits this task
   (B) Phase list from Phase 1 through Phase 6 (one line each, Chinese OK)
   (C) For Phase 1 only: which agents you will activate first, in order, and what each produces
   (D) The first quality gate: name, criteria (bullet points), and what evidence is required before moving to Phase 2
3. Enforce: quality gates between phases; evidence-based QA; max 3 retries per task before escalation.
```

---

## 第五步：核对第一条回复是否「跑通」

对照下面清单，在模型回复上打勾。**满足绝大多数即算十分钟目标达成**。

| 检查项 | 说明 |
|--------|------|
| 明确写出 **NEXUS-Sprint** 或与 Sprint 等价的表述 | 说明它理解模式 |
| **Phase 1→6** 均有提及，且顺序合理 | Phase 0 应被跳过或标注 N/A |
| Phase 1 中点到 **Senior Project Manager、Sprint Prioritizer、UX Architect、Brand Guardian、Backend Architect** 等模板中的角色 | 不必一个不漏，但 PM + 架构/设计主干要有 |
| **第一个质量门**单独成段 | 应包含：通过条件 + **证据**（例如架构文档、API 草图、邮件模板与隐私说明等） |
| **没有**直接开始写大量代码或贴完整实现 | 若写了，说明未遵守你的「FIRST reply」约束，见下一节纠偏 |

---

## 若第一条回复不合格：三条纠偏提示（复制即用）

**情况 A：一上来就写代码**  

```
Stop implementation. Retry your first reply: only sections (A)(B)(C)(D) in Chinese as requested. No code blocks.
```

**情况 B：没有质量门或没有「证据」**  

```
Add section (D) again: name the Phase 1→2 quality gate, list pass criteria, and explicitly list what artifacts count as evidence (docs, diagrams, API contract, etc.).
```

**情况 C：角色混乱或阶段只有两三行**  

```
Re-output (B) as a table: Phase number, phase name, primary agents, main deliverable. Then re-output (C) for Phase 1 only as a numbered sequence.
```

---

## 第六步（可选）：第二条消息——进入 Phase 1 的「简报形态」

当你确认第一条回复结构正确后，可以用下面提示**开启真正的编排**（仍不强制写代码，只要结构化产出）：

```
Assume Phase 1 has started. As Agents Orchestrator, produce:
1) A one-page architecture outline (Chinese) for the daily job + DB query + idempotency + email batching + failure handling
2) A sprint backlog table: ID, user story, owner agent (English name), definition of done, suggested QA agent
3) The Phase 1→2 gate checklist copied into a markdown checklist so I can tick items manually
Do not write production code yet unless I say "开始实现".
```

这样你就完成了一次**从「启动 NEXUS」到「Phase 1 可执行简报」**的端到端演练。

---

## 附录：更短的 NEXUS-Micro 案例（约 5 分钟）

对应 QUICKSTART 里 **Fix a Bug** 模板。下面是一条已填好的**中文约束 + 英文角色链**的完整消息：

```
You are coordinating NEXUS-Micro. Respond in Chinese.

Activate Backend Architect to investigate and fix: In TeamPulse API, GET /tasks returns 500 when query param `overdue_only=true` (PostgreSQL). Hypothesis: SQL fragment bug.
After fix, activate API Tester to verify the fix with example requests.
Then activate Evidence Collector to confirm no visual regressions on the task list page.

Rules: evidence-based verification; max 3 fix attempts then escalate with a short incident-style summary.

In your first reply, only output: (1) ordered agent steps (2) what evidence each step must produce (3) done criteria.
```

**合格回复特征**：三步顺序正确；每步有**可验证证据**（日志、curl 输出、截图说明等）；完成标准明确。

---

## 与主教程的对应关系

| 主教程 [§2](./NEXUS全管线教程.md#2-初级十分钟跑通第一次) 步骤 | 本案例中的位置 |
|---------------------------------------------------------------|----------------|
| 打开 QUICKSTART | [第一步](#第一步打开权威模板1-分钟) |
| 复制整块模板 | [第一步](#第一步打开权威模板1-分钟) |
| 替换占位符 | [第二步](#第二步把占位符换成案例里的真值2-分钟) |
| 追加约束 | [第三步](#第三步追加中文输出--第一条必须交付物1-分钟) |
| 发送并索要模式/阶段/角色/质量门 | [第四步](#第四步第一条完整消息直接整段复制使用) 与 [第五步](#第五步核对第一条回复是否跑通) |

---

## 相关链接

- [NEXUS全管线教程.md](./NEXUS全管线教程.md)  
- [strategy/QUICKSTART.md](../strategy/QUICKSTART.md)  
- [strategy/coordination/handoff-templates.md](../strategy/coordination/handoff-templates.md)（下一步学交接时可打开）  
- Orchestrator 智能体源文件：[specialized/agents-orchestrator.md](../specialized/agents-orchestrator.md)  
