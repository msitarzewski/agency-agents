---
name: refactor
description: Refactor specified code for clarity and simplicity without changing behaviour
---

# refactor

Refactor the target code to improve readability and maintainability. No behaviour changes.

## Process
1. Read the target file(s) or user-specified scope.
2. Identify what to improve:
   - Functions doing more than one thing → extract
   - Duplicated logic → consolidate
   - Poor names that obscure intent → rename
   - Unnecessary complexity (deep nesting, premature abstraction, magic numbers) → simplify
   - Dead code → remove
3. Apply changes. One concern per pass — don't mix rename + extract + restructure.
4. If tests exist, run them to confirm behaviour is preserved.

## Output
The refactored code, then a brief summary (≤5 bullets) of what changed and why.

## Rules
- Preserve all existing behaviour. No bug fixes or new features unless explicitly asked.
- Do not change public APIs or exported function signatures without explicit approval.
- If scope is ambiguous, ask before touching anything.
- Do not add comments explaining what the code does — improve the code so it doesn't need them.
