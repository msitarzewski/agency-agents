---
name: qa-plan
description: Write a QA test plan for a feature or release
---

# qa-plan

Write a test plan that covers what matters and defines clear exit criteria.

## Process
1. Understand scope: what was built, what changed, what's at risk?
2. Identify test areas:
   - **Happy path** — primary user flows end-to-end
   - **Edge cases** — empty state, max values, concurrent access, missing optional data
   - **Error states** — network failure, invalid input, permission denied, timeout
   - **Regression** — what existing features could this change break?
   - **Integration points** — external APIs, third-party services, webhooks
3. Assign priority (P1 / P2 / P3) to each test case.
4. Note what should be automated vs what requires manual verification.

## Output

```
**Test Plan: [Feature / Release]**

Scope: [what's being tested]
Out of scope: [what's not — be explicit]
Environment: [staging / prod / local]

**Test Cases**:
| ID | Area | Scenario | Steps | Expected Result | Priority | Type |
|---|---|---|---|---|---|---|

**Exit criteria**: [what must pass before this is considered done]
**Known risks**: [what might we miss or what's hard to test?]
```

Priority definitions: P1 = blocks release. P2 = should pass. P3 = nice to have.
Type: Manual / Automated / Either.

## Rules
- If a scenario is too vague to test, it's not a requirement — surface it as an open question.
- Exit criteria must be binary. "Looks good" is not exit criteria. "All P1 test cases pass" is.
- Don't write test cases for things covered by existing automated tests unless regression risk is high.
