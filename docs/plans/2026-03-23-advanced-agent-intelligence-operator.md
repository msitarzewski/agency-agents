# Advanced Agent Intelligence Operator Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a new specialized agent that researches current advanced-agent trends and operationalizes them into reproducible build guidance, then expose it in the README roster.

**Architecture:** This change is content-driven. The implementation adds one new markdown agent definition in `specialized/` and updates the root `README.md` so the new agent appears in the Specialized Division roster. Verification relies on targeted content checks plus any existing repo validation scripts that apply to agent-file structure.

**Tech Stack:** Markdown, repository conventions in `CONTRIBUTING.md`, existing agent prompt patterns

---

### Task 1: Add the design-approved specialized agent file

**Files:**
- Create: `specialized/advanced-agent-intelligence-operator.md`
- Reference: `CONTRIBUTING.md`
- Reference: `specialized/agents-orchestrator.md`
- Reference: `product/product-trend-researcher.md`

**Step 1: Write the failing test**

Use a file-existence/content check that should fail before the file exists.

```powershell
Test-Path 'specialized\advanced-agent-intelligence-operator.md'
```

**Step 2: Run test to verify it fails**

Run: `Test-Path 'specialized\advanced-agent-intelligence-operator.md'`
Expected: `False`

**Step 3: Write minimal implementation**

Create `specialized/advanced-agent-intelligence-operator.md` with:

- frontmatter (`name`, `description`, `color`)
- identity and mission
- research lanes
- source-quality and freshness rules
- workflow
- output package
- communication style
- success metrics
- guardrails for risky bot/script patterns

**Step 4: Run test to verify it passes**

Run: `Test-Path 'specialized\advanced-agent-intelligence-operator.md'`
Expected: `True`

**Step 5: Commit**

```bash
git add specialized/advanced-agent-intelligence-operator.md
git commit -m "Add advanced agent intelligence operator"
```

### Task 2: Add the new agent to the README roster

**Files:**
- Modify: `README.md`
- Reference: `specialized/advanced-agent-intelligence-operator.md`

**Step 1: Write the failing test**

Check that the README does not yet mention the new agent.

```powershell
Select-String -Path 'README.md' -Pattern 'Advanced Agent Intelligence Operator'
```

**Step 2: Run test to verify it fails**

Run: `Select-String -Path 'README.md' -Pattern 'Advanced Agent Intelligence Operator'`
Expected: no matches

**Step 3: Write minimal implementation**

Add a Specialized Division roster row with:

- linked agent name
- concise specialty description
- clear “when to use” guidance

**Step 4: Run test to verify it passes**

Run: `Select-String -Path 'README.md' -Pattern 'Advanced Agent Intelligence Operator'`
Expected: one or more matches

**Step 5: Commit**

```bash
git add README.md
git commit -m "Document advanced agent intelligence operator"
```

### Task 3: Verify repo-facing outputs

**Files:**
- Test: `specialized/advanced-agent-intelligence-operator.md`
- Test: `README.md`

**Step 1: Write the failing test**

Use a structural/content validation command that would reveal missing required sections.

```powershell
Select-String -Path 'specialized\advanced-agent-intelligence-operator.md' -Pattern '^## '
```

**Step 2: Run test to verify it fails**

Before implementation, this should produce no output because the file does not exist.

Run: `Select-String -Path 'specialized\advanced-agent-intelligence-operator.md' -Pattern '^## '`
Expected: file missing or no matches

**Step 3: Write minimal implementation**

Ensure the agent file includes clearly named sections for:

- identity
- core mission
- critical rules
- workflow
- communication style
- success metrics
- advanced capabilities

**Step 4: Run test to verify it passes**

Run:

```powershell
Select-String -Path 'specialized\advanced-agent-intelligence-operator.md' -Pattern '^## '
Select-String -Path 'README.md' -Pattern 'advanced-agent-intelligence-operator.md'
```

Expected:

- multiple `##` section matches in the new agent file
- one README match linking to the new agent file

**Step 5: Commit**

```bash
git add specialized/advanced-agent-intelligence-operator.md README.md
git commit -m "Verify advanced agent intelligence operator content"
```

Plan complete and saved to `docs/plans/2026-03-23-advanced-agent-intelligence-operator.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
