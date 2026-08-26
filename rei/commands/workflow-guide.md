---
description: CMD - ⚡(REI) Route command/workflow selection requests to the Workflow Guide agent for REI-aligned next-step recommendations.
---

CMD - Workflow routing helper for this workspace.

CMD - ⚡(REI) /workflow-guide

Purpose: Thin wrapper that invokes `🏠(REI) Workflow Guide` for command-first routing, with optional direct agent/skill alternatives when appropriate.

## Route

- Agent: `🏠(REI) Workflow Guide`
- File: `.cursor/agents/workflow-guide.md`

## Behavior contract

- Primary recommendation is always a command path first.
- Response must also include one alternative direct agent path and one alternative direct skill path when relevant.
- Missing inputs must be minimal and blocking-only.
- Immediate next action must be explicit.

## Usage examples

- `/workflow-guide I need to add a new lead scoring capability`
- `/workflow-guide The save action started failing after yesterday`
- `/workflow-guide Should I ship this now or prep a PR first?`
- `/workflow-guide Should I run a command, or call an agent/skill directly?`
