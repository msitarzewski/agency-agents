---
name: prd
description: Write a Product Requirements Document for a feature or product
---

# prd

Write a PRD that engineers can build from and stakeholders can sign off on.

## Process
1. Clarify: what problem does this solve, for whom, and why now?
2. Define success: what measurable outcomes does this produce?
3. Document requirements — use the MoSCoW format: must/should/won't (this version).
4. Identify dependencies, risks, and open questions that block the build.

## Output

```
# [Feature Name] — PRD

## Problem
[1–2 paragraphs. What problem exists? Who has it? What's the cost of not solving it?]

## Goals
- [Measurable outcome — e.g. "Reduce time to complete X from Y minutes to Z seconds"]
- [Measurable outcome]

## Non-goals
- [What this explicitly does not address — prevents scope creep]

## User Stories
- As a [user type], I want [capability] so that [benefit].

## Requirements
### Must have (blocks launch)
- [Requirement — testable, specific]

### Should have (important but not blocking)
- [Requirement]

### Won't have in this version
- [Explicitly deferred — with reason]

## Success Metrics
[How will we know this worked? What do we measure, and when?]

## Open Questions
[What must be decided before or during build?]

## Dependencies
[What must exist or be built first?]
```

## Rules
- Requirements must be testable. "Fast" is not a requirement. "P95 latency < 200ms" is.
- Non-goals are as important as goals. Be explicit — it prevents the scope from expanding during build.
- If you don't know the success metric, don't ship — you won't know if it worked.
