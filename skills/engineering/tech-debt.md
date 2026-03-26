---
name: tech-debt
description: Inventory and prioritise technical debt in the codebase
---

# tech-debt

Find the debt that's actually slowing you down. Not everything is debt worth paying.

## Process
1. Read key files: entry points, most-changed files (`git log --stat | head -50`), areas the user flags.
2. Categorise debt:
   - **Rotten** — actively causing bugs or slowing development today (fix now)
   - **Structural** — architectural decisions that constrain future work (plan to fix)
   - **Cosmetic** — naming, formatting, dead code (fix opportunistically)
3. For each item: describe the problem, the blast radius (what breaks or slows down because of it), and the fix.
4. Prioritise by: (impact on dev velocity) × (frequency of being touched). High-touch rotten code first.

## Output

Debt inventory sorted by priority:

| Priority | Type | Location | Problem | Impact | Fix | Effort |
|---|---|---|---|---|---|---|
| 1 | Rotten | `file:line` | ... | ... | ... | S/M/L |

End with: **Top 3 to tackle first** and why.

## Rules
- Don't flag things that aren't causing real pain. "I'd do it differently" is not debt.
- Cosmetic debt goes last unless it's systematically wrong everywhere and causes confusion.
- Be honest about effort: S = hours, M = days, L = weeks. Don't undersell to make the list look manageable.
- Debt that lives in code nobody touches isn't urgent, regardless of how bad it looks.
