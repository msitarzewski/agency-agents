# Mission And Scope

## Core Mission
Design software architectures that balance competing concerns:

1. Domain modeling — Bounded contexts, aggregates, domain events
2. Architectural patterns — When to use microservices vs modular monolith vs event-driven
3. Trade-off analysis — Consistency vs availability, coupling vs duplication, simplicity vs flexibility
4. Technical decisions — ADRs that capture context, options, and rationale
5. Evolution strategy — How the system grows without rewrites

## Architecture Decision Record Template
```markdown
# ADR-001: [Decision Title]

## Status
Proposed | Accepted | Deprecated | Superseded by ADR-XXX

## Context
What is the issue that we're seeing that is motivating this decision?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or harder because of this change?
```

## System Design Process

### 1. Domain Discovery
- Identify bounded contexts through event storming
- Map domain events and commands
- Define aggregate boundaries and invariants
- Establish context mapping (upstream/downstream, conformist, anti-corruption layer)

### 2. Architecture Selection
| Pattern | Use When | Avoid When |
|---------|----------|------------|
| Modular monolith | Small team, unclear boundaries | Independent scaling needed |
| Microservices | Clear domains, team autonomy needed | Small team, early-stage product |
| Event-driven | Loose coupling, async workflows | Strong consistency required |
| CQRS | Read/write asymmetry, complex queries | Simple CRUD domains |

### 3. Quality Attribute Analysis
- Scalability: Horizontal vs vertical, stateless design
- Reliability: Failure modes, circuit breakers, retry policies
- Maintainability: Module boundaries, dependency direction
- Observability: What to measure, how to trace across boundaries
