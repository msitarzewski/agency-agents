# DeepSeek V4 Flash validation summary

The private Loomloom template completed all three synthetic resume rows without an execution failure. The final audit step checked evidence support, score/tier consistency, protected-attribute leakage, and recommendation strength.

| Candidate | Score | Tier | Must-have status | Audit status | Human review |
| --- | ---: | --- | --- | --- | --- |
| `candidate-strong` | 88 | shortlist | met | corrected | no |
| `candidate-consider` | 55 | reject | partially met | needs human review | yes |
| `candidate-reject` | 15 | reject | not met | corrected | no |

Notable audit behavior:

- The strong profile remained shortlisted, while unsupported risk statements were removed.
- The borderline profile remained rejected because explicit must-have evidence was incomplete; the audit corrected overstatements and required human review.
- The mismatched frontend profile remained rejected; the audit removed speculative wording and kept the recommendation evidence-bound.
- No protected attributes or discriminatory reasoning were identified in the three synthetic test cases.

The full row-level outputs are in `deepseek-v4-flash-test-results.xlsx`. These results are decision support only and require recruiter review before any employment decision.
