# Full Utilization Validation Suite Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a fully-utilized validation system for agent assets, strategy assets, and integration assets, plus a practical local usage guide for agency-agents.

**Architecture:** Keep agent lint focused on frontmatter-based agent assets, add a dedicated strategy lint for NEXUS doctrine/playbooks/templates, add an integration lint for generated/installable assets, and expose a single `lint-all.sh` entrypoint. Document how to use both the agent library and NEXUS strategy assets together in a local workflow.

**Tech Stack:** Bash scripts, Markdown docs, grep/find/sed, existing repo structure

---

### Task 1: Write failing repo-level validation test

**Files:**
- Create: `tests/test_full_utilization_suite.sh`

**Step 1: Write the failing test**
- Assert `./scripts/lint-agents.sh` exits successfully.
- Assert `./scripts/lint-strategy.sh` exists and exits successfully.
- Assert `./scripts/lint-integrations.sh` exists and exits successfully.
- Assert `./scripts/lint-all.sh` exists and exits successfully.
- Assert `docs/full-utilization-guide.md` exists.
- Assert `README.md` references the lint suite and local guide.

**Step 2: Run test to verify it fails**
Run: `bash tests/test_full_utilization_suite.sh`
Expected: FAIL because new scripts/docs do not exist and current `lint-agents.sh` errors on `strategy/*`.

### Task 2: Fix agent lint scope

**Files:**
- Modify: `scripts/lint-agents.sh`

**Step 1: Exclude non-agent strategy docs from agent-frontmatter validation**
- Limit agent lint scope to frontmatter-based agent directories only.
- Update comments so scope matches `convert.sh` behavior.

**Step 2: Run targeted verification**
Run: `./scripts/lint-agents.sh`
Expected: exit 0, warnings allowed, no frontmatter errors from `strategy/*`.

### Task 3: Add strategy lint

**Files:**
- Create: `scripts/lint-strategy.sh`

**Step 1: Validate strategy docs as docs, not agents**
- Check required key files exist.
- Check each strategy Markdown file is non-empty and starts with a heading.
- Check repo-relative Markdown links resolve.
- Check QUICKSTART references to strategy docs resolve.

**Step 2: Run targeted verification**
Run: `./scripts/lint-strategy.sh`
Expected: exit 0 on current repo.

### Task 4: Add integration lint

**Files:**
- Create: `scripts/lint-integrations.sh`

**Step 1: Validate distribution assets**
- Check required integration directories exist.
- Check generated outputs expected by install flows exist.
- Check README/integrations README mention supported tools consistently enough for practical use.

**Step 2: Run targeted verification**
Run: `./scripts/lint-integrations.sh`
Expected: exit 0 on current repo.

### Task 5: Add unified entrypoint

**Files:**
- Create: `scripts/lint-all.sh`

**Step 1: Chain all validation layers**
- Run agent, strategy, and integration lint in sequence.
- Propagate failures with a clear summary.

**Step 2: Run targeted verification**
Run: `./scripts/lint-all.sh`
Expected: exit 0.

### Task 6: Add practical local guide and README links

**Files:**
- Create: `docs/full-utilization-guide.md`
- Modify: `README.md`

**Step 1: Document full local usage**
- Explain the 4-layer model: agents, strategy, distribution, proof/examples.
- Explain recommended local setup and NEXUS-Sprint usage.
- Explain new validation suite and when to run each script.

**Step 2: Update README discoverability**
- Link the guide.
- Link/describe the new validation scripts.

**Step 3: Run repo-level validation test**
Run: `bash tests/test_full_utilization_suite.sh`
Expected: PASS.

### Task 7: Fresh verification before completion

**Files:**
- Verify only

**Step 1: Run full validation**
Run: `bash tests/test_full_utilization_suite.sh && ./scripts/lint-all.sh`
Expected: PASS.
