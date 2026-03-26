---
name: user-story
description: Write user stories with acceptance criteria a QA engineer can test
---

# user-story

Write stories that define behaviour precisely enough to build and test from.

## Process
1. Identify the user types involved in the feature.
2. For each meaningful interaction, write a story.
3. Add acceptance criteria that a QA engineer can execute without asking questions.
4. Flag stories that are too large (should be split) or too small (should be merged into another).

## Output

For each story:

```
**Story**: As a [user type], I want [capability] so that [benefit].

**Acceptance Criteria**:
- Given [initial context], when [user action], then [system response].
- Given [initial context], when [user action], then [system response].

**Notes**: [edge cases, dependencies, explicit out-of-scope]
```

## Rules
- Acceptance criteria must be binary: pass or fail. Not "the page loads fast" — "the page responds within 2 seconds on a 3G connection."
- The benefit in "so that [benefit]" must be real. "So that I can do it" is not a benefit.
- If you don't know the user type or benefit, ask before writing.
- Stories are units of delivery, not requirements lists. One story = one deployable behaviour.
