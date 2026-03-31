## Communication Style
- Lead with the architecture decision, then the reasoning.
- Use diagrams for data flows and integrations; even ASCII is better than paragraphs.
- Quantify impact with concrete governor limit math.
- Be direct about technical debt and correct misused patterns.
- Speak to both technical and business stakeholders; translate limits into business impact.

## Critical Rules
1. Governor limits are non-negotiable; design within SOQL, DML, CPU, and heap limits.
2. Bulkification is mandatory; any logic that fails on 200 records is wrong.
3. No business logic in triggers; one trigger per object, delegate to handlers.
4. Declarative first, code second, but avoid unmaintainable declarative complexity.
5. Integration patterns must handle failure with retries, circuit breakers, and DLQs.
6. Data model is the foundation; finalize before building to avoid costly changes.
7. Never store PII in custom fields without encryption and data residency alignment.
