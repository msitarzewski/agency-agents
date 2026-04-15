# Multi-Agent Workflow: Startup MVP with Persistent Memory

> The same startup MVP workflow from [workflow-startup-mvp.md](workflow-startup-mvp.md), but with an MCP memory server handling state between agents. No more copy-paste handoffs.

## The Problem with Manual Handoffs

In the standard workflow, every agent-to-agent transition looks like this:

```
Activate Backend Architect.

Here's our sprint plan: [paste Sprint Prioritizer output]
Here's our research brief: [paste UX Researcher output]

Design the API and database schema for RetroBoard.
...
```

You are the glue. You copy-paste outputs between agents, keep track of what's been done, and hope you don't lose context along the way. It works for small projects, but it falls apart when:

- Sessions time out and you lose the output
- Multiple agents need the same context
- QA fails and you need to rewind to a previous state
- The project spans days or weeks across many sessions

## The Fix

With an MCP memory server installed, agents store their deliverables in memory and retrieve what they need automatically. Handoffs become:

```
Activate Backend Architect.

Project: RetroBoard. Recall previous context for this project
and design the API and database schema.
```

The agent searches memory for RetroBoard context, finds the sprint plan and research brief stored by previous agents, and picks up from there.

## Setup

Install any MCP-compatible memory server that supports `remember`, `recall`, and `rollback` operations. See [integrations/mcp-memory/README.md](../integrations/mcp-memory/README.md) for setup.

## The Scenario

Same as the standard workflow: a SaaS team retrospective tool (RetroBoard), 4 weeks to MVP, solo developer.

## Agent Team

| Agent | Role in this workflow |
|-------|---------------------|
| Sprint Prioritizer | Break the project into weekly sprints |
| UX Researcher | Validate the idea with quick user interviews |
| Backend Architect | Design the API and data model |
| Frontend Developer | Build the React app |
| Rapid Prototyper | Get the first version running fast |
| Growth Hacker | Plan launch strategy while building |
| Reality Checker | Gate each milestone before moving on |

Each agent has a Memory Integration section in their prompt (see [integrations/mcp-memory/README.md](../integrations/mcp-memory/README.md) for how to add it).

## The Workflow

### Week 1: Discovery + Architecture

**Step 1 — Activate Sprint Prioritizer**

```
Activate Sprint Prioritizer.

Project: RetroBoard — a real-time team retrospective tool for remote teams.
Timeline: 4 weeks to MVP launch.
Core features: user auth, create retro boards, add cards, vote, action items.
Constraints: solo developer, React + Node.js stack, deploy to Vercel + Railway.

Break this into 4 weekly sprints with clear deliverables and acceptance criteria.
Remember your sprint plan tagged for this project when done.
```

The Sprint Prioritizer produces the sprint plan and stores it in memory tagged with `sprint-prioritizer`, `retroboard`, and `sprint-plan`.

**Step 2 — Activate UX Researcher (in parallel)**

```
Activate UX Researcher.

I'm building a team retrospective tool for remote teams (5-20 people).
Competitors: EasyRetro, Retrium, Parabol.

Run a quick competitive analysis and identify:
1. What features are table stakes
2. Where competitors fall short
3. One differentiator we could own

Output a 1-page research brief. Remember it tagged for this project when done.
```

The UX Researcher stores the research brief tagged with `ux-researcher`, `retroboard`, and `research-brief`.

**Step 3 — Hand off to Backend Architect**

```
Activate Backend Architect.

Project: RetroBoard. Recall the sprint plan and research brief from previous agents.
Stack: Node.js, Express, PostgreSQL, Socket.io for real-time.

Design:
1. Database schema (SQL)
2. REST API endpoints list
3. WebSocket events for real-time board updates
4. Auth strategy recommendation

Remember each deliverable tagged for this project and for the frontend-developer.
```

The Backend Architect recalls the sprint plan and research brief from memory automatically. No copy-paste. It stores its schema and API spec tagged with `backend-architect`, `retroboard`, `api-spec`, and `frontend-developer`.

### Week 2: Build Core Features

**Step 4 — Activate Frontend Developer + Rapid Prototyper**

```
Activate Frontend Developer.

Project: RetroBoard. Recall the API spec and schema from the Backend Architect.

Build the RetroBoard React app:
- Stack: React, TypeScript, Tailwind, Socket.io-client
- Pages: Login, Dashboard, Board view
- Components: RetroCard, VoteButton, ActionItem, BoardColumn

Start with the Board view — it's the core experience.
Focus on real-time: when one user adds a card, everyone sees it.
Remember your progress tagged for this project.
```

The Frontend Developer pulls the API spec from memory and builds against it.

**Step 5 — Reality Check at midpoint**

```
Activate Reality Checker.

Project: RetroBoard. We're at week 2 of a 4-week MVP build.

Recall all deliverables from previous agents for this project.

Evaluate:
1. Can we realistically ship in 2 more weeks?
2. What should we cut to make the deadline?
3. Any technical debt that will bite us at launch?

Remember your verdict tagged for this project.
```

The Reality Checker has full visibility into everything produced so far — the sprint plan, research brief, schema, API spec, and frontend progress — without you having to collect and paste it all.

### Week 3: Polish + Landing Page

**Step 6 — Frontend Developer continues, Growth Hacker starts**

```
Activate Growth Hacker.

Product: RetroBoard — team retrospective tool, launching in 1 week.
Target: Engineering managers and scrum masters at remote-first companies.
Budget: $0 (organic launch only).

Recall the project context and Reality Checker's verdict.

Create a launch plan:
1. Landing page copy (hero, features, CTA)
2. Launch channels (Product Hunt, Reddit, Hacker News, Twitter)
3. Day-by-day launch sequence
4. Metrics to track in week 1

Remember the launch plan tagged for this project.
```

### Week 4: Launch

**Step 7 — Final Reality Check**

```
Activate Reality Checker.

Project: RetroBoard, ready to launch.

Recall all project context, previous verdicts, and the launch plan.

Evaluate production readiness:
- Live URL: [url]
- Test accounts created: yes
- Error monitoring: Sentry configured
- Database backups: daily automated

Run through the launch checklist and give a GO / NO-GO decision.
Require evidence for each criterion.
```

### When QA Fails: Rollback

In the standard workflow, when the Reality Checker rejects a deliverable, you go back to the responsible agent and try to explain what went wrong. With memory, the recovery loop is tighter:

```
Activate Backend Architect.

Project: RetroBoard. The Reality Checker flagged issues with the API design.
Recall the Reality Checker's feedback and your previous API spec.
Roll back to your last known-good schema and address the specific issues raised.
Remember the updated deliverables when done.
```

The Backend Architect can see exactly what the Reality Checker flagged, recall its own previous work, roll back to a checkpoint, and produce a fix — all without you manually tracking versions.

## Before and After

| Aspect | Standard Workflow | With Memory |
|--------|------------------|-------------|
| **Handoffs** | Copy-paste full output between agents | Agents recall what they need automatically |
| **Context loss** | Session timeouts lose everything | Memories persist across sessions |
| **Multi-agent context** | Manually compile context from N agents | Agent searches memory for project tag |
| **QA failure recovery** | Manually describe what went wrong | Agent recalls feedback + rolls back |
| **Multi-day projects** | Re-establish context every session | Agent picks up where it left off |
| **Setup required** | None | Install an MCP memory server |

## Key Patterns

1. **Tag everything with the project name**: This is what makes recall work. Every memory gets tagged with `retroboard` (or whatever your project is).
2. **Tag deliverables for the receiving agent**: When the Backend Architect finishes an API spec, it tags the memory with `frontend-developer` so the Frontend Developer finds it on recall.
3. **Reality Checker gets full visibility**: Because all agents store their work in memory, the Reality Checker can recall everything for the project without you compiling it.
4. **Rollback replaces manual undo**: When something fails, roll back to the last checkpoint instead of trying to figure out what changed.

## Tips

- You don't need to modify every agent at once. Start by adding Memory Integration to the agents you use most and expand from there.
- The memory instructions are prompts, not code. The LLM interprets them and calls the MCP tools as needed. You can adjust the wording to match your style.
- Any MCP-compatible memory server that supports `remember`, `recall`, `rollback`, and `search` tools will work with this workflow.
