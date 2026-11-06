# NEXUS — Handoff & Escalation Protocols

> Templates for agent-to-agent handoffs, QA feedback loops, and escalation after retry exhaustion.

[← Back to the NEXUS strategy overview](nexus-strategy.md)


---

## 11. Handoff Protocols

### 11.1 Standard Handoff Template

Every agent-to-agent handoff must include:

```markdown
## NEXUS Handoff Document

### Metadata
- **From**: [Agent Name] ([Division])
- **To**: [Agent Name] ([Division])
- **Phase**: [Current NEXUS Phase]
- **Task Reference**: [Task ID from Sprint Prioritizer backlog]
- **Priority**: [Critical / High / Medium / Low]
- **Timestamp**: [ISO 8601]

### Context
- **Project**: [Project name and brief description]
- **Current State**: [What has been completed so far]
- **Relevant Files**: [List of files/artifacts to review]
- **Dependencies**: [What this work depends on]

### Deliverable Request
- **What is needed**: [Specific, measurable deliverable]
- **Acceptance criteria**: [How success will be measured]
- **Constraints**: [Technical, timeline, or resource constraints]
- **Reference materials**: [Links to specs, designs, previous work]

### Quality Expectations
- **Must pass**: [Specific quality criteria]
- **Evidence required**: [What proof of completion looks like]
- **Handoff to next**: [Who receives the output and what they need]
```

### 11.2 QA Feedback Loop Protocol

When a task fails QA, the feedback must be actionable:

```markdown
## QA Failure Feedback

### Task: [Task ID and description]
### Attempt: [1/2/3] of 3 maximum
### Verdict: FAIL

### Specific Issues Found
1. **[Issue Category]**: [Exact description with screenshot reference]
   - Expected: [What should happen]
   - Actual: [What actually happens]
   - Evidence: [Screenshot filename or test output]

2. **[Issue Category]**: [Exact description]
   - Expected: [...]
   - Actual: [...]
   - Evidence: [...]

### Fix Instructions
- [Specific, actionable fix instruction 1]
- [Specific, actionable fix instruction 2]

### Files to Modify
- [file path 1]: [what needs to change]
- [file path 2]: [what needs to change]

### Retry Expectations
- Fix the above issues and re-submit for QA
- Do NOT introduce new features — fix only
- Attempt [N+1] of 3 maximum
```

### 11.3 Escalation Protocol

When a task exceeds 3 retry attempts:

```markdown
## Escalation Report

### Task: [Task ID]
### Attempts Exhausted: 3/3
### Escalation Level: [To Agents Orchestrator / To Studio Producer]

### Failure History
- Attempt 1: [Summary of issues and fixes attempted]
- Attempt 2: [Summary of issues and fixes attempted]
- Attempt 3: [Summary of issues and fixes attempted]

### Root Cause Analysis
- [Why the task keeps failing]
- [What systemic issue is preventing resolution]

### Recommended Resolution
- [ ] Reassign to different developer agent
- [ ] Decompose task into smaller sub-tasks
- [ ] Revise architecture/approach
- [ ] Accept current state with known limitations
- [ ] Defer to future sprint

### Impact Assessment
- **Blocking**: [What other tasks are blocked by this]
- **Timeline Impact**: [How this affects the overall schedule]
- **Quality Impact**: [What quality compromises exist]
```
