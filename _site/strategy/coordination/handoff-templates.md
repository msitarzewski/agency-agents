# 📋 NEXUS Handoff Templates

> Standardized templates for every type of agent-to-agent handoff in the NEXUS pipeline. Consistent handoffs prevent context loss — the #1 cause of multi-agent coordination failure.

---

## 1. Standard Handoff Template

Use for any agent-to-agent work transfer.

```markdown
# NEXUS Handoff Document

## Metadata
| Field | Value |
|-------|-------|
| **From** | [Agent Name] ([Division]) |
| **To** | [Agent Name] ([Division]) |
| **Phase** | Phase [N] — [Phase Name] |
| **Task Reference** | [Task ID from Sprint Prioritizer backlog] |
| **Priority** | [Critical / High / Medium / Low] |
| **Timestamp** | [YYYY-MM-DDTHH:MM:SSZ] |

## Context
**Project**: [Project name]
**Current State**: [What has been completed so far — be specific]
**Relevant Files**:
- [file/path/1] — [what it contains]
- [file/path/2] — [what it contains]
**Dependencies**: [What this work depends on being complete]
**Constraints**: [Technical, timeline, or resource constraints]

## Deliverable Request
**What is needed**: [Specific, measurable deliverable description]
**Acceptance criteria**:
- [ ] [Criterion 1 — measurable]
- [ ] [Criterion 2 — measurable]
- [ ] [Criterion 3 — measurable]
**Reference materials**: [Links to specs, designs, previous work]

## Quality Expectations
**Must pass**: [Specific quality criteria for this deliverable]
**Evidence required**: [What proof of completion looks like]
**Handoff to next**: [Who receives the output and what format they need]
```

---

## 2. QA Feedback Loop — PASS

Use when Evidence Collector or other QA agent approves a task.

```markdown
# NEXUS QA Verdict: PASS ✅

## Task
| Field | Value |
|-------|-------|
| **Task ID** | [ID] |
| **Task Description** | [Description] |
| **Developer Agent** | [Agent Name] |
| **QA Agent** | [Agent Name] |
| **Attempt** | [N] of 3 |
| **Timestamp** | [YYYY-MM-DDTHH:MM:SSZ] |

## Verdict: PASS

## Evidence
**Screenshots**:
- Desktop (1920x1080): [filename/path]
- Tablet (768x1024): [filename/path]
- Mobile (375x667): [filename/path]

**Functional Verification**:
- [x] [Acceptance criterion 1] — verified
- [x] [Acceptance criterion 2] — verified
- [x] [Acceptance criterion 3] — verified

**Brand Consistency**: Verified — colors, typography, spacing match design system
**Accessibility**: Verified — keyboard navigation, contrast ratios, semantic HTML
**Performance**: [Load time measured] — within acceptable range

## Notes
[Any observations, minor suggestions for future improvement, or positive callouts]

## Next Action
→ Agents Orchestrator: Mark task complete, advance to next task in backlog
```

---

## 3. QA Feedback Loop — FAIL

Use when Evidence Collector or other QA agent rejects a task.

```markdown
# NEXUS QA Verdict: FAIL ❌

## Task
| Field | Value |
|-------|-------|
| **Task ID** | [ID] |
| **Task Description** | [Description] |
| **Developer Agent** | [Agent Name] |
| **QA Agent** | [Agent Name] |
| **Attempt** | [N] of 3 |
| **Timestamp** | [YYYY-MM-DDTHH:MM:SSZ] |

## Verdict: FAIL

## Issues Found

### Issue 1: [Category] — [Severity: Critical/High/Medium/Low]
**Description**: [Exact description of the problem]
**Expected**: [What should happen according to acceptance criteria]
**Actual**: [What actually happens]
**Evidence**: [Screenshot filename or test output]
**Fix instruction**: [Specific, actionable instruction to resolve]
**File(s) to modify**: [Exact file paths]

### Issue 2: [Category] — [Severity]
**Description**: [...]
**Expected**: [...]
**Actual**: [...]
**Evidence**: [...]
**Fix instruction**: [...]
**File(s) to modify**: [...]

[Continue for all issues found]

## Acceptance Criteria Status
- [x] [Criterion 1] — passed
- [ ] [Criterion 2] — FAILED (see Issue 1)
- [ ] [Criterion 3] — FAILED (see Issue 2)

## Retry Instructions
**For Developer Agent**:
1. Fix ONLY the issues listed above
2. Do NOT introduce new features or changes
3. Re-submit for QA when all issues are addressed
4. This is attempt [N] of 3 maximum

**If attempt 3 fails**: Task will be escalated to Agents Orchestrator
```

---

## 4. Escalation Report

Use when a task exceeds 3 retry attempts.

```markdown
# NEXUS Escalation Report 🚨

## Task
| Field | Value |
|-------|-------|
| **Task ID** | [ID] |
| **Task Description** | [Description] |
| **Developer Agent** | [Agent Name] |
| **QA Agent** | [Agent Name] |
| **Attempts Exhausted** | 3/3 |
| **Escalation To** | [Agents Orchestrator / Studio Producer] |
| **Timestamp** | [YYYY-MM-DDTHH:MM:SSZ] |

## Failure History

### Attempt 1
- **Issues found**: [Summary]
- **Fixes applied**: [What the developer changed]
- **Result**: FAIL — [Why it still failed]

### Attempt 2
- **Issues found**: [Summary]
- **Fixes applied**: [What the developer changed]
- **Result**: FAIL — [Why it still failed]

### Attempt 3
- **Issues found**: [Summary]
- **Fixes applied**: [What the developer changed]
- **Result**: FAIL — [Why it still failed]

## Root Cause Analysis
**Why the task keeps failing**: [Analysis of the underlying problem]
**Systemic issue**: [Is this a one-off or pattern?]
**Complexity assessment**: [Was the task properly scoped?]

## Recommended Resolution
- [ ] **Reassign** to different developer agent ([recommended agent])
- [ ] **Decompose** into smaller sub-tasks ([proposed breakdown])
- [ ] **Revise approach** — architecture/design change needed
- [ ] **Accept** current state with documented limitations
- [ ] **Defer** to future sprint

## Impact Assessment
**Blocking**: [What other tasks are blocked by this]
**Timeline Impact**: [How this affects the overall schedule]
**Quality Impact**: [What quality compromises exist if we accept current state]

## Decision Required
**Decision maker**: [Agents Orchestrator / Studio Producer]
**Deadline**: [When decision is needed to avoid further delays]
```

---

## 5. Phase Gate Handoff

Use when transitioning between NEXUS phases.

```markdown
# NEXUS Phase Gate Handoff

## Transition
| Field | Value |
|-------|-------|
| **From Phase** | Phase [N] — [Name] |
| **To Phase** | Phase [N+1] — [Name] |
| **Gate Keeper(s)** | [Agent Name(s)] |
| **Gate Result** | [PASSED / FAILED] |
| **Timestamp** | [YYYY-MM-DDTHH:MM:SSZ] |

## Gate Criteria Results
| # | Criterion | Threshold | Result | Evidence |
|---|-----------|-----------|--------|----------|
| 1 | [Criterion] | [Threshold] | ✅ PASS / ❌ FAIL | [Evidence reference] |
| 2 | [Criterion] | [Threshold] | ✅ PASS / ❌ FAIL | [Evidence reference] |
| 3 | [Criterion] | [Threshold] | ✅ PASS / ❌ FAIL | [Evidence reference] |

## Documents Carried Forward
1. [Document name] — [Purpose for next phase]
2. [Document name] — [Purpose for next phase]
3. [Document name] — [Purpose for next phase]

## Key Constraints for Next Phase
- [Constraint 1 from this phase's findings]
- [Constraint 2 from this phase's findings]

## Agent Activation for Next Phase
| Agent | Role | Priority |
|-------|------|----------|
| [Agent 1] | [Role in next phase] | [Immediate / Day 2 / As needed] |
| [Agent 2] | [Role in next phase] | [Immediate / Day 2 / As needed] |

## Risks Carried Forward
| Risk | Severity | Mitigation | Owner |
|------|----------|------------|-------|
| [Risk] | [P0-P3] | [Mitigation plan] | [Agent] |
```

---

## 6. Sprint Handoff

Use at sprint boundaries.

```markdown
# NEXUS Sprint Handoff

## Sprint Summary
| Field | Value |
|-------|-------|
| **Sprint** | [Number] |
| **Duration** | [Start date] → [End date] |
| **Sprint Goal** | [Goal statement] |
| **Velocity** | [Planned] / [Actual] story points |

## Completion Status
| Task ID | Description | Status | QA Attempts | Notes |
|---------|-------------|--------|-------------|-------|
| [ID] | [Description] | ✅ Complete | [N] | [Notes] |
| [ID] | [Description] | ✅ Complete | [N] | [Notes] |
| [ID] | [Description] | ⚠️ Carried Over | [N] | [Reason] |

## Quality Metrics
- **First-pass QA rate**: [X]%
- **Average retries**: [N]
- **Tasks completed**: [X/Y]
- **Story points delivered**: [N]

## Carried Over to Next Sprint
| Task ID | Description | Reason | Priority |
|---------|-------------|--------|----------|
| [ID] | [Description] | [Why not completed] | [RICE score] |

## Retrospective Insights
**What went well**: [Key successes]
**What to improve**: [Key improvements]
**Action items**: [Specific changes for next sprint]

## Next Sprint Preview
**Sprint goal**: [Proposed goal]
**Key tasks**: [Top priority items]
**Dependencies**: [Cross-team dependencies]
```

---

## 7. Incident Handoff

Use during incident response.

```markdown
# NEXUS Incident Handoff

## Incident
| Field | Value |
|-------|-------|
| **Severity** | [P0 / P1 / P2 / P3] |
| **Detected by** | [Agent or system] |
| **Detection time** | [Timestamp] |
| **Assigned to** | [Agent Name] |
| **Status** | [Investigating / Mitigating / Resolved / Post-mortem] |

## Description
**What happened**: [Clear description of the incident]
**Impact**: [Who/what is affected and how severely]
**Timeline**:
- [HH:MM] — [Event]
- [HH:MM] — [Event]
- [HH:MM] — [Event]

## Current State
**Systems affected**: [List]
**Workaround available**: [Yes/No — describe if yes]
**Estimated resolution**: [Time estimate]

## Actions Taken
1. [Action taken and result]
2. [Action taken and result]

## Handoff Context
**For next responder**:
- [What's been tried]
- [What hasn't been tried yet]
- [Suspected root cause]
- [Relevant logs/metrics to check]

## Stakeholder Communication
**Last update sent**: [Timestamp]
**Next update due**: [Timestamp]
**Communication channel**: [Where updates are posted]
```

---

## Usage Guide

| Situation | Template to Use |
|-----------|----------------|
| Assigning work to another agent | Standard Handoff (#1) |
| QA approves a task | QA PASS (#2) |
| QA rejects a task | QA FAIL (#3) |
| Task exceeds 3 retries | Escalation Report (#4) |
| Moving between phases | Phase Gate Handoff (#5) |
| End of sprint | Sprint Handoff (#6) |
| System incident | Incident Handoff (#7) |
