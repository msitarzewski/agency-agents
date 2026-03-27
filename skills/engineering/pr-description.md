---
name: pr-description
description: Write a clear, useful pull request description from the git diff
---

# pr-description

Write a PR description that tells reviewers what matters, not what git log already shows.

## Process
1. Run `git log main..HEAD --oneline` and `git diff main...HEAD` to see all changes in the branch.
2. Identify: what changed, why it changed, what the reviewer needs to know that isn't obvious from the diff.
3. Note any breaking changes, required migrations, deployment steps, or environment variable changes.

## Output

```
## What
[2–4 sentences. What does this PR do? Intent and outcome, not a summary of commits.]

## Why
[1–3 sentences. What problem does this solve? Link to issue/ticket if one exists.]

## How
[Optional. Only include if the approach is non-obvious or has a meaningful tradeoff worth explaining.]

## Testing
[How was this tested? What should the reviewer verify manually?]

## Notes
[Breaking changes, migration steps, follow-up work, known issues. Omit if none.]
```

## Rules
- "What" is for humans, not git log. Summarise intent, not mechanics.
- If there are no breaking changes or migration steps, omit the Notes section entirely.
- Keep it under 300 words. If it needs more, the PR is probably too large.
- Don't pad with filler ("This PR addresses the issue of..."). Start with the substance.
