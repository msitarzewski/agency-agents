---
name: perf-audit
description: Identify and fix performance bottlenecks in code or system
---

# perf-audit

Find what's actually slow. Don't optimise blindly.

## Process
1. Identify the hot path: where is time or memory actually spent? If profiler output, slow query logs, or traces are available, use them. If not, reason from code structure.
2. Categorise findings:
   - **Algorithmic** — O(n²) where O(n log n) is achievable; nested loops over large datasets; recomputing what could be cached
   - **I/O** — blocking synchronous calls; sequential requests that could be parallel; missing caching layer; chatty APIs (many small calls vs one batch)
   - **Database** — N+1 queries; missing indexes on filtered/sorted columns; selecting all columns when few are needed; no query result caching
   - **Memory** — large unnecessary copies; unbounded caches; leaks (event listeners not removed, closures holding references)
   - **Rendering** — unnecessary re-renders; missing virtualisation on long lists; layout thrashing; unoptimised images
3. Fix the highest-impact issue first. Don't micro-optimise.

## Output
For each bottleneck found:
- What: the specific problem and location
- Why: root cause
- Fix: code change or architectural change
- Expected impact: rough estimate (e.g. "eliminates 12 queries per page load")

## Rules
- Measure before and after where possible. State assumptions when you can't.
- Don't optimise code that isn't on the hot path.
- State the tradeoff for every optimisation (readability, complexity, memory for speed, etc.).
