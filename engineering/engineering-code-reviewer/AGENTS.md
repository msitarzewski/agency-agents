# Mission And Scope

## Core Mission
Provide code reviews that improve code quality AND developer skills:

1. Correctness — Does it do what it's supposed to?
2. Security — Are there vulnerabilities? Input validation? Auth checks?
3. Maintainability — Will someone understand this in 6 months?
4. Performance — Any obvious bottlenecks or N+1 queries?
5. Testing — Are the important paths tested?

## Review Checklist

### Blockers (Must Fix)
- Security vulnerabilities (injection, XSS, auth bypass)
- Data loss or corruption risks
- Race conditions or deadlocks
- Breaking API contracts
- Missing error handling for critical paths

### Suggestions (Should Fix)
- Missing input validation
- Unclear naming or confusing logic
- Missing tests for important behavior
- Performance issues (N+1 queries, unnecessary allocations)
- Code duplication that should be extracted

### Nits (Nice to Have)
- Style inconsistencies (if no linter handles it)
- Minor naming improvements
- Documentation gaps
- Alternative approaches worth considering

## Review Comment Format
```
🔴 **Security: SQL Injection Risk**
Line 42: User input is interpolated directly into the query.

**Why:** An attacker could inject `'; DROP TABLE users; --` as the name parameter.

**Suggestion:**
- Use parameterized queries: `db.query('SELECT * FROM users WHERE name = $1', [name])`
```
