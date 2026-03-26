---
name: debug
description: Systematically diagnose the root cause of a bug and apply the minimal fix
---

# debug

Find and fix the root cause. Don't treat symptoms.

## Process
1. State the symptom clearly: actual behaviour vs expected behaviour. What error, if any?
2. Form a hypothesis — the most likely cause — before reading any code.
3. Trace the execution path relevant to the bug. Read the actual code; don't assume.
4. Confirm or disprove the hypothesis. If wrong, form the next one.
5. Apply the minimal fix that addresses the root cause.
6. Verify: if tests exist, run them. If not, describe how to reproduce the fix.

## Output
- Root cause (1-2 sentences)
- Fix applied (diff or precise description)
- How to verify it's fixed

## Rules
- State your hypothesis before investigating. This prevents random shotgun changes.
- Fix the root cause, not the symptom.
- If the root cause is unclear after thorough tracing, say so and ask for more context rather than guessing.
- Apply the minimum change needed — don't refactor unrelated code while fixing a bug.
