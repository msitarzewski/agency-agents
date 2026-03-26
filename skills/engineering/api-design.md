---
name: api-design
description: Design a clean, consistent API for a feature or service
---

# api-design

Design the API surface before implementation. Get the contract right — it's expensive to change later.

## Process
1. Clarify the use cases: who calls this, with what inputs, expecting what outputs? What error states must be handled?
2. Choose the model:
   - **REST**: identify resources and their CRUD operations; use nouns for paths, HTTP verbs for actions
   - **RPC/GraphQL**: identify operations and their inputs/outputs
3. Define request/response schemas with field names, types, nullability, and validation rules.
4. Design the error model: what can go wrong? Consistent error shape across all endpoints.
5. Address upfront: authentication, pagination (cursor vs offset), versioning strategy, rate limiting signals.

## Output
- **Endpoint list** — method, path (or operation name), one-line description
- **Request/response schemas** — JSON examples or TypeScript types
- **Error codes** — code, HTTP status, meaning, example response
- **Key decisions** — each design choice with the rationale and tradeoff

## Rules
- Be consistent. Naming, casing, error shapes, and pagination must follow one convention throughout.
- Don't expose internal implementation details (database IDs in formats that leak schema, internal service names, stack traces in errors).
- Default to the simplest design that covers the actual use cases. Don't design for hypothetical future callers.
- Boolean fields and nullable fields are API contracts. Be explicit about their meaning and when they're null.
