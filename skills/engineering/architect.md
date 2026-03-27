---
name: architect
description: Design system or feature architecture — components, interfaces, tradeoffs — before code is written
---

# architect

Design the architecture. Produce a plan that can be handed to an engineer to build from.

## Process
1. Clarify requirements: what problem does this solve, who uses it, what are the constraints (scale, latency, consistency, budget)?
2. Identify the components and their responsibilities. Keep it to the minimum needed.
3. Define the interfaces between components: API contracts, data schemas, event shapes, message formats.
4. Identify the hardest decisions and state the tradeoffs explicitly.
5. Note what is deliberately out of scope.

## Output
- **Component diagram** (ASCII or Mermaid)
- **Data model** — key entities, relationships, key fields
- **API surface** — key endpoints / functions / events with input/output shapes
- **Key decisions** — each decision with the chosen approach and the tradeoff accepted
- **Open questions** — what must be answered before or during build

## Rules
- Don't design for hypothetical scale. Design for 10× current load, not 1000×.
- Flag irreversible decisions explicitly (schema choices, public API shapes, vendor lock-in).
- If the problem is underspecified, ask the two most important clarifying questions before designing.
- Prefer boring, proven technology unless there's a clear reason not to.
