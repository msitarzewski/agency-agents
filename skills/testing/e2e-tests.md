---
name: e2e-tests
description: Write end-to-end test scenarios and implementation for a user flow
---

# e2e-tests

Write E2E tests that verify user-visible behaviour across the full stack.

## Process
1. Identify the user journey: start state → user actions → end state.
2. Write scenarios in plain language first (Given / When / Then).
3. Implement using the project's existing E2E framework (Playwright, Cypress, Selenium — match what's already there).
4. Cover: happy path, the most likely error states, mobile viewport if the product has mobile users.
5. Use realistic test data — not `test@test.com` and `password123`.

## Output

Plain-language scenarios first:

```gherkin
Scenario: [name]
  Given [initial state]
  When [user action]
  Then [expected outcome]
```

Then the implementation in the project's framework, matching existing file structure and conventions.

## Rules
- E2E tests verify user-visible behaviour, not implementation. Tests should survive a full refactor if the outcome is the same.
- Each test must be independent. No test relies on state created by another test. Set up and tear down your own state.
- Don't duplicate what unit tests already cover. E2E tests are slow — reserve them for full user flows.
- If the E2E framework isn't established, ask before picking one. Don't introduce new tooling silently.
