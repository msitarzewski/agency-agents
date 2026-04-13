# Zipcode Market Opportunity Operator Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a specialized agent that identifies AI-solvable business opportunities by ZIP code, enriches them with public business and contact data, and exposes the agent in the README roster.

**Architecture:** This is a content-only addition to the prompt catalog. Implementation consists of a new markdown agent definition under `specialized/` plus a README roster entry. The prompt must encode the approved schema, public-signal-first workflow, scoring logic, and enrichment boundaries.

**Tech Stack:** Markdown, repository contribution conventions, existing specialized-agent prompt patterns

---

### Task 1: Add the specialized agent file

**Files:**
- Create: `specialized/zipcode-market-opportunity-operator.md`
- Reference: `specialized/advanced-agent-intelligence-operator.md`
- Reference: `specialized/data-analytics-reporter.md`
- Reference: `CONTRIBUTING.md`

**Step 1: Write the failing test**

```powershell
Test-Path 'specialized\zipcode-market-opportunity-operator.md'
```

**Step 2: Run test to verify it fails**

Run: `Test-Path 'specialized\zipcode-market-opportunity-operator.md'`
Expected: `False`

**Step 3: Write minimal implementation**

Create `specialized/zipcode-market-opportunity-operator.md` with:

- frontmatter
- identity and mission
- public-signal-first rules
- input sources
- scoring model
- opportunity dossier schema
- workflow
- communication style
- success metrics

**Step 4: Run test to verify it passes**

Run: `Test-Path 'specialized\zipcode-market-opportunity-operator.md'`
Expected: `True`

**Step 5: Commit**

```bash
git add specialized/zipcode-market-opportunity-operator.md
git commit -m "Add zipcode market opportunity operator"
```

### Task 2: Add the agent to the README roster

**Files:**
- Modify: `README.md`
- Reference: `specialized/zipcode-market-opportunity-operator.md`

**Step 1: Write the failing test**

```powershell
Select-String -Path 'README.md' -Pattern 'Zipcode Market Opportunity Operator'
```

**Step 2: Run test to verify it fails**

Run: `Select-String -Path 'README.md' -Pattern 'Zipcode Market Opportunity Operator'`
Expected: no matches

**Step 3: Write minimal implementation**

Add a row to the Specialized Division table describing the new agent’s specialty and when to use it.

**Step 4: Run test to verify it passes**

Run: `Select-String -Path 'README.md' -Pattern 'Zipcode Market Opportunity Operator'`
Expected: one or more matches

**Step 5: Commit**

```bash
git add README.md
git commit -m "Document zipcode market opportunity operator"
```

### Task 3: Verify content structure

**Files:**
- Test: `specialized/zipcode-market-opportunity-operator.md`
- Test: `README.md`

**Step 1: Write the failing test**

```powershell
Select-String -Path 'specialized\zipcode-market-opportunity-operator.md' -Pattern '^## '
```

**Step 2: Run test to verify it fails**

Before implementation this should fail due to a missing file.

Run: `Select-String -Path 'specialized\zipcode-market-opportunity-operator.md' -Pattern '^## '`
Expected: file missing or no matches

**Step 3: Write minimal implementation**

Ensure the agent includes sections for:

- identity
- mission
- critical rules
- data inputs
- scoring
- dossier output
- workflow
- communication style
- success metrics

**Step 4: Run test to verify it passes**

Run:

```powershell
Select-String -Path 'specialized\zipcode-market-opportunity-operator.md' -Pattern '^## '
Select-String -Path 'README.md' -Pattern 'zipcode-market-opportunity-operator.md'
```

Expected:

- multiple `##` matches in the new agent file
- one README link match

**Step 5: Commit**

```bash
git add specialized/zipcode-market-opportunity-operator.md README.md
git commit -m "Verify zipcode market opportunity operator content"
```

Plan complete and saved to `docs/plans/2026-03-23-zipcode-market-opportunity-operator.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
