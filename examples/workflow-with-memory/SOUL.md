# Principles and Boundaries

## Key Patterns
1. **Tag everything with the project name**: This is what makes recall work. Every memory gets tagged with `retroboard` (or whatever your project is).
2. **Tag deliverables for the receiving agent**: When the Backend Architect finishes an API spec, it tags the memory with `frontend-developer` so the Frontend Developer finds it on recall.
3. **Reality Checker gets full visibility**: Because all agents store their work in memory, the Reality Checker can recall everything for the project without you compiling it.
4. **Rollback replaces manual undo**: When something fails, roll back to the last checkpoint instead of trying to figure out what changed.

## Tips and Constraints
- You don't need to modify every agent at once. Start by adding Memory Integration to the agents you use most and expand from there.
- The memory instructions are prompts, not code. The LLM interprets them and calls the MCP tools as needed. You can adjust the wording to match your style.
- Any MCP-compatible memory server that supports `remember`, `recall`, `rollback`, and `search` tools will work with this workflow.

## Decision Priorities
- Prefer automatic recall over manual copy-paste.
- Preserve consistent tags for every deliverable so agents can find what they need.
