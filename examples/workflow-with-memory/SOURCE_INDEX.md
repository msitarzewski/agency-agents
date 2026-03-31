# Source Index

- Source: `/Volumes/disk1/go/src/agency-agents/examples/workflow-with-memory.md`
- Unit count: `52`

| unit_id | source_hash | unit_type | excerpt |
| --- | --- | --- | --- |
| U001 | 46619ac758b8 | heading | # Multi-Agent Workflow: Startup MVP with Persistent Memory |
| U002 | 8b9faee20d4f | paragraph | > The same startup MVP workflow from [workflow-startup-mvp.md](workflow-startup-mvp.md), but with an MCP memory server handling state between agents. No more co |
| U003 | c3037ea840c1 | heading | ## The Problem with Manual Handoffs |
| U004 | dd93aeb28880 | paragraph | In the standard workflow, every agent-to-agent transition looks like this: |
| U005 | ae3a32e6586e | code | ``` Activate Backend Architect. Here's our sprint plan: [paste Sprint Prioritizer output] Here's our research brief: [paste UX Researcher output] Design the API |
| U006 | 0b6147907879 | paragraph | You are the glue. You copy-paste outputs between agents, keep track of what's been done, and hope you don't lose context along the way. It works for small proje |
| U007 | 66b2ee071437 | list | - Sessions time out and you lose the output - Multiple agents need the same context - QA fails and you need to rewind to a previous state - The project spans da |
| U008 | acc724fbde41 | heading | ## The Fix |
| U009 | ee6581760d8f | paragraph | With an MCP memory server installed, agents store their deliverables in memory and retrieve what they need automatically. Handoffs become: |
| U010 | 0e2d9c497b31 | code | ``` Activate Backend Architect. Project: RetroBoard. Recall previous context for this project and design the API and database schema. ``` |
| U011 | 1935542bc7cf | paragraph | The agent searches memory for RetroBoard context, finds the sprint plan and research brief stored by previous agents, and picks up from there. |
| U012 | ae195bf7aba3 | heading | ## Setup |
| U013 | c662ea082a07 | paragraph | Install any MCP-compatible memory server that supports `remember`, `recall`, and `rollback` operations. See [integrations/mcp-memory/README.md](../integrations/ |
| U014 | a1aeb73b6303 | heading | ## The Scenario |
| U015 | 4f09bd4a532c | paragraph | Same as the standard workflow: a SaaS team retrospective tool (RetroBoard), 4 weeks to MVP, solo developer. |
| U016 | 064079aa5f1f | heading | ## Agent Team |
| U017 | 1d86f0d13e68 | paragraph | \| Agent \| Role in this workflow \| \|-------\|---------------------\| \| Sprint Prioritizer \| Break the project into weekly sprints \| \| UX Researcher \| Validate the  |
| U018 | 2ed7cd03c53d | paragraph | Each agent has a Memory Integration section in their prompt (see [integrations/mcp-memory/README.md](../integrations/mcp-memory/README.md) for how to add it). |
| U019 | 263f7c1f685b | heading | ## The Workflow |
| U020 | 78a6f9554c36 | heading | ### Week 1: Discovery + Architecture |
| U021 | eaabb82808e7 | paragraph | **Step 1 — Activate Sprint Prioritizer** |
| U022 | fd37a1854957 | code | ``` Activate Sprint Prioritizer. Project: RetroBoard — a real-time team retrospective tool for remote teams. Timeline: 4 weeks to MVP launch. Core features: use |
| U023 | 125b733f09cf | paragraph | The Sprint Prioritizer produces the sprint plan and stores it in memory tagged with `sprint-prioritizer`, `retroboard`, and `sprint-plan`. |
| U024 | b1cad576161a | paragraph | **Step 2 — Activate UX Researcher (in parallel)** |
| U025 | fc17cd9e51ec | code | ``` Activate UX Researcher. I'm building a team retrospective tool for remote teams (5-20 people). Competitors: EasyRetro, Retrium, Parabol. Run a quick competi |
| U026 | dd48dfaa7d1f | paragraph | The UX Researcher stores the research brief tagged with `ux-researcher`, `retroboard`, and `research-brief`. |
| U027 | 8782b4879b5a | paragraph | **Step 3 — Hand off to Backend Architect** |
| U028 | e2f6eb82cfc0 | code | ``` Activate Backend Architect. Project: RetroBoard. Recall the sprint plan and research brief from previous agents. Stack: Node.js, Express, PostgreSQL, Socket |
| U029 | 89112e30f767 | paragraph | The Backend Architect recalls the sprint plan and research brief from memory automatically. No copy-paste. It stores its schema and API spec tagged with `backen |
| U030 | 9add8c180349 | heading | ### Week 2: Build Core Features |
| U031 | 18a45f578a4c | paragraph | **Step 4 — Activate Frontend Developer + Rapid Prototyper** |
| U032 | 0508880a1075 | code | ``` Activate Frontend Developer. Project: RetroBoard. Recall the API spec and schema from the Backend Architect. Build the RetroBoard React app: - Stack: React, |
| U033 | c22d9f92bbd2 | paragraph | The Frontend Developer pulls the API spec from memory and builds against it. |
| U034 | be2498a94e0a | paragraph | **Step 5 — Reality Check at midpoint** |
| U035 | 21c6ec10231c | code | ``` Activate Reality Checker. Project: RetroBoard. We're at week 2 of a 4-week MVP build. Recall all deliverables from previous agents for this project. Evaluat |
| U036 | a619cf606e24 | paragraph | The Reality Checker has full visibility into everything produced so far — the sprint plan, research brief, schema, API spec, and frontend progress — without you |
| U037 | 9064c7f9f3eb | heading | ### Week 3: Polish + Landing Page |
| U038 | 43c491174dab | paragraph | **Step 6 — Frontend Developer continues, Growth Hacker starts** |
| U039 | 6f78a6d7027f | code | ``` Activate Growth Hacker. Product: RetroBoard — team retrospective tool, launching in 1 week. Target: Engineering managers and scrum masters at remote-first c |
| U040 | aa4aad8270c9 | heading | ### Week 4: Launch |
| U041 | c391c382ac17 | paragraph | **Step 7 — Final Reality Check** |
| U042 | 25862713fcbd | code | ``` Activate Reality Checker. Project: RetroBoard, ready to launch. Recall all project context, previous verdicts, and the launch plan. Evaluate production read |
| U043 | 23031943380d | heading | ### When QA Fails: Rollback |
| U044 | 3bd1beee176d | paragraph | In the standard workflow, when the Reality Checker rejects a deliverable, you go back to the responsible agent and try to explain what went wrong. With memory,  |
| U045 | cf3d170762c9 | code | ``` Activate Backend Architect. Project: RetroBoard. The Reality Checker flagged issues with the API design. Recall the Reality Checker's feedback and your prev |
| U046 | 5a806fb84315 | paragraph | The Backend Architect can see exactly what the Reality Checker flagged, recall its own previous work, roll back to a checkpoint, and produce a fix — all without |
| U047 | a96187abc247 | heading | ## Before and After |
| U048 | 59f098c7744a | paragraph | \| Aspect \| Standard Workflow \| With Memory \| \|--------\|------------------\|-------------\| \| **Handoffs** \| Copy-paste full output between agents \| Agents recall  |
| U049 | fc106c524b8f | heading | ## Key Patterns |
| U050 | 429cd3bc8852 | list | 1. **Tag everything with the project name**: This is what makes recall work. Every memory gets tagged with `retroboard` (or whatever your project is). 2. **Tag  |
| U051 | ea2d093f0e83 | heading | ## Tips |
| U052 | c8e772e6f4e9 | list | - You don't need to modify every agent at once. Start by adding Memory Integration to the agents you use most and expand from there. - The memory instructions a |
