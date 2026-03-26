---
name: test-gen
description: Generate tests for a function, module, or feature using the project's existing framework
---

# test-gen

Write tests that verify behaviour, not implementation.

## Process
1. Read the code under test. Understand its contract: inputs, outputs, side effects, thrown errors.
2. Identify test cases:
   - **Happy path** — normal expected usage, expected return value
   - **Edge cases** — empty/null input, zero, max values, boundary conditions, empty collections
   - **Error cases** — invalid input, missing required data, dependency failures
   - **Regression** — if a specific bug was reported, add a test that would have caught it
3. Write tests using the project's existing test framework. Match the file structure and naming conventions already in use.
4. Ensure tests are deterministic and independent. No shared mutable state between tests.

## Output
Test code, ready to run. Brief comment on each test describing what it verifies.

## Rules
- Match the existing test framework — don't introduce new ones.
- Mock external dependencies (network, database, filesystem) unless integration tests are explicitly requested.
- Test behaviour, not implementation. Tests should not break when implementation changes but output is the same.
- Don't test framework code or language built-ins.
