# Principles and Boundaries

## Key Patterns
1. **Sequential handoffs**: Each agent's output becomes the next agent's input
2. **Parallel work**: UX Researcher and Sprint Prioritizer can run simultaneously in Week 1
3. **Quality gates**: Reality Checker at midpoint and before launch prevents shipping broken code
4. **Context passing**: Always paste previous agent outputs into the next prompt — agents don't share memory

## Tips
- Copy-paste agent outputs between steps — don't summarize, use the full output
- If a Reality Checker flags an issue, loop back to the relevant specialist to fix it
- Keep the Orchestrator agent in mind for automating this flow once you're comfortable with the manual version
