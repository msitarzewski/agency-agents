# Local NEXUS-Sprint Template Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the first practical local NEXUS-Sprint template so users can run a real sprint on their machine using the repository’s existing agent and strategy assets.

**Architecture:** Add a single document-first template under `docs/` that ties together Quick Start, agent activation prompts, handoff templates, and the existing full-utilization guide. Add a focused repo test so discoverability and core sections do not regress.

**Tech Stack:** Markdown docs, Bash verification test, existing NEXUS strategy documents

---

### Task 1: Write the failing test

**Files:**
- Create: `tests/test_local_nexus_sprint_template.sh`

**Step 1: Write the failing test**
- Assert `docs/local-nexus-sprint-template.md` exists.
- Assert the template references key NEXUS source files.
- Assert `docs/full-utilization-guide.md` links to the new template.
- Assert `README.md` references the new template.

**Step 2: Run the test to verify it fails**
Run: `bash tests/test_local_nexus_sprint_template.sh`
Expected: FAIL because the template and references do not exist yet.

### Task 2: Implement the template document

**Files:**
- Create: `docs/local-nexus-sprint-template.md`

**Step 1: Write the template**
Include:
- use cases and prerequisites
- local folder conventions
- sprint input/spec template
- orchestrator kickoff prompt
- recommended agent roster
- execution sequence by phase
- PASS/FAIL/escalation usage guidance
- end-of-sprint checklist

**Step 2: Verify content references real repo assets**
Reference:
- `strategy/QUICKSTART.md`
- `strategy/nexus-strategy.md`
- `strategy/coordination/agent-activation-prompts.md`
- `strategy/coordination/handoff-templates.md`
- `specialized/agents-orchestrator.md`
- `testing/testing-evidence-collector.md`
- `testing/testing-reality-checker.md`

### Task 3: Improve discoverability

**Files:**
- Modify: `docs/full-utilization-guide.md`
- Modify: `README.md`

**Step 1: Link from full-utilization guide**
Add a short subsection pointing readers to the ready-to-run local sprint template.

**Step 2: Link from README**
Add the template to the Full Utilization Workflow area or nearby docs navigation.

### Task 4: Run verification

**Files:**
- Verify only

**Step 1: Run focused test**
Run: `bash tests/test_local_nexus_sprint_template.sh`
Expected: PASS.

**Step 2: Run broader repo validation**
Run: `bash tests/test_full_utilization_suite.sh && ./scripts/lint-all.sh`
Expected: PASS.
