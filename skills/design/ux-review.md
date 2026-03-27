---
name: ux-review
description: Critique UI/UX for real usability issues, prioritised by user impact
---

# ux-review

Find usability problems that would cause real users to fail or struggle. Not preferences — problems.

## Process
1. Review against core heuristics:
   - **Clarity**: Is the purpose of each element immediately obvious to a new user?
   - **Feedback**: Does the system communicate state — loading, success, error, empty — at every moment?
   - **Efficiency**: Can users complete key tasks with the minimum steps? Are common actions easy to reach?
   - **Error prevention**: Does the design prevent mistakes before they happen? Is destructive action hard to trigger accidentally?
   - **Consistency**: Are patterns, labels, and interactions consistent throughout? Does it match platform conventions?
   - **Accessibility**: Sufficient contrast ratios, touch targets ≥44px, keyboard navigable, screen reader labels present?
2. Identify the top 3-5 issues by user impact. Don't list everything — prioritise ruthlessly.
3. For each issue, propose a specific, actionable fix.
4. Note what is working well — fixes should preserve the good.

## Output

Issues ranked by user impact:

| # | Where | Problem | Why it matters | Fix |
|---|---|---|---|---|

Then one paragraph on what's working well.

## Rules
- Be specific. "The button is confusing" is useless. "The primary CTA says 'Submit' but there's no indication what is being submitted or what happens next" is actionable.
- Distinguish usability problems (users fail or struggle) from preferences (you'd do it differently). Only flag the former.
- Don't redesign outside the scope the user asks about. Fix the thing, don't reimagine the product.
