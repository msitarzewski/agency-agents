# NEXUS — Quick-Start Activation Guide

> How to activate NEXUS-Full, NEXUS-Sprint, or NEXUS-Micro, plus the prompt templates for each role.

[← Back to the NEXUS strategy overview](nexus-strategy.md)


---

## 15. Quick-Start Activation Guide

### 15.1 NEXUS-Full Activation (Enterprise)

```bash
# Step 1: Initialize NEXUS pipeline
"Activate Agents Orchestrator in NEXUS-Full mode for [PROJECT NAME].
 Project specification: [path to spec file].
 Execute complete 7-phase pipeline with all quality gates."

# The Orchestrator will:
# 1. Read the project specification
# 2. Activate Phase 0 agents for discovery
# 3. Progress through all phases with quality gates
# 4. Manage Dev↔QA loops automatically
# 5. Report status at each phase boundary
```

### 15.2 NEXUS-Sprint Activation (Feature/MVP)

```bash
# Step 1: Initialize sprint pipeline
"Activate Agents Orchestrator in NEXUS-Sprint mode for [FEATURE/MVP NAME].
 Requirements: [brief description or path to spec].
 Skip Phase 0 (market already validated).
 Begin at Phase 1 with architecture and sprint planning."

# Recommended agent subset (15-25):
# PM: Senior Project Manager, Sprint Prioritizer, Project Shepherd
# Design: UX Architect, UI Designer, Brand Guardian
# Engineering: Frontend Developer, Backend Architect, DevOps Automator
# + AI Engineer or Mobile App Builder (if applicable)
# Testing: Evidence Collector, Reality Checker, API Tester, Performance Benchmarker
# Support: Analytics Reporter, Infrastructure Maintainer
# Specialized: Agents Orchestrator
```

### 15.3 NEXUS-Micro Activation (Targeted Task)

```bash
# Step 1: Direct agent activation
"Activate [SPECIFIC AGENT] for [TASK DESCRIPTION].
 Context: [relevant background].
 Deliverable: [specific output expected].
 Quality check: Evidence Collector to verify upon completion."

# Common NEXUS-Micro configurations:
#
# Bug Fix:
#   Backend Architect → API Tester → Evidence Collector
#
# Content Campaign:
#   Content Creator → Social Media Strategist → Twitter Engager
#   + Instagram Curator + Reddit Community Builder
#
# Performance Issue:
#   Performance Benchmarker → Infrastructure Maintainer → DevOps Automator
#
# Compliance Audit:
#   Legal Compliance Checker → Executive Summary Generator
#
# Market Research:
#   Trend Researcher → Analytics Reporter → Executive Summary Generator
#
# UX Improvement:
#   UX Researcher → UX Architect → Frontend Developer → Evidence Collector
```

### 15.4 Agent Activation Prompt Templates

#### For the Orchestrator (Pipeline Start)
```
You are the Agents Orchestrator running NEXUS pipeline for [PROJECT].

Project spec: [path]
Mode: [Full/Sprint/Micro]
Current phase: [Phase N]

Execute the NEXUS protocol:
1. Read the project specification
2. Activate Phase [N] agents per the NEXUS strategy
3. Manage handoffs using the NEXUS Handoff Template
4. Enforce quality gates before phase advancement
5. Track all tasks with status reporting
6. Run Dev↔QA loops for all implementation tasks
7. Escalate after 3 failed attempts per task

Report format: NEXUS Pipeline Status Report (see template in strategy doc)
```

#### For Developer Agents (Task Implementation)
```
You are [AGENT NAME] working within the NEXUS pipeline.

Phase: [Current Phase]
Task: [Task ID and description from Sprint Prioritizer backlog]
Architecture reference: [path to architecture doc]
Design system: [path to CSS/design tokens]
Brand guidelines: [path to brand doc]

Implement this task following:
1. The architecture specification exactly
2. The design system tokens and patterns
3. The brand guidelines for visual consistency
4. Accessibility standards (WCAG 2.1 AA)

When complete, your work will be reviewed by Evidence Collector.
Acceptance criteria: [specific criteria from task list]
```

#### For QA Agents (Task Validation)
```
You are [QA AGENT] validating work within the NEXUS pipeline.

Phase: [Current Phase]
Task: [Task ID and description]
Developer: [Which agent implemented this]
Attempt: [N] of 3 maximum

Validate against:
1. Task acceptance criteria: [specific criteria]
2. Architecture specification: [path]
3. Brand guidelines: [path]
4. Performance requirements: [specific thresholds]

Provide verdict: PASS or FAIL
If FAIL: Include specific issues, evidence, and fix instructions
Use the NEXUS QA Feedback Loop Protocol format
```
