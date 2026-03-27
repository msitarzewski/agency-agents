---
name: sprint-plan
description: Prioritise backlog items and produce a committed sprint plan
---

# sprint-plan

Turn a backlog into a sprint with a clear goal, committed work, and explicit deferrals.

## Process
1. List all candidate items from: backlog, bug reports, carry-overs, requests the user provides.
2. Assess each item:
   - **Value**: High / Medium / Low (impact on users or business)
   - **Effort**: S / M / L / XL (roughly: hours / 1-2 days / 3-5 days / week+)
   - **Blocked**: yes/no (depends on something not done yet)
   - **Risk**: known unknowns that could expand scope
3. Priority order: Critical bugs → High value + Small effort → High value + Medium effort → the rest.
4. Fill to ~80% capacity. The remaining 20% absorbs unplanned work. Every sprint has unplanned work.
5. Write the sprint goal — one sentence describing what this sprint achieves for users or the product.

## Output

```
**Sprint Goal**: [One sentence. What does this sprint deliver that matters?]

**Committed**:
| Item | Value | Effort | Notes |
|---|---|---|---|

**Stretch** (only if committed finishes early):
| Item | Value | Effort |
|---|---|---|

**Deferred** (explicit, with reason):
| Item | Reason |
|---|---|

**Risks**: [What could derail this sprint?]
```

## Rules
- A sprint without a goal is a to-do list. Force a goal.
- Never commit 100% of capacity. It always slips.
- Deferred items need a reason — "not this sprint" is a decision, not an oversight.
- If an item is blocked, it cannot be committed regardless of priority.
