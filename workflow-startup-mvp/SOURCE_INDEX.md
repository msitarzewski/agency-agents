# Source Index

- Source: `/Volumes/disk1/go/src/agency-agents-worktrees/openclaw-normalize-20260325/examples/workflow-startup-mvp.md`
- Unit count: `29`

| unit_id | source_hash | unit_type | excerpt |
| --- | --- | --- | --- |
| U001 | cc3b9e1f893d | heading | # Multi-Agent Workflow: Startup MVP |
| U002 | c8fac22fdf6c | paragraph | > A step-by-step example of how to coordinate multiple agents to go from idea to shipped MVP. |
| U003 | a1aeb73b6303 | heading | ## The Scenario |
| U004 | 1111c087881e | paragraph | You're building a SaaS MVP — a team retrospective tool for remote teams. You have 4 weeks to ship a working product with user signups, a core feature, and a lan |
| U005 | 064079aa5f1f | heading | ## Agent Team |
| U006 | 1d86f0d13e68 | paragraph | \| Agent \| Role in this workflow \| \|-------\|---------------------\| \| Sprint Prioritizer \| Break the project into weekly sprints \| \| UX Researcher \| Validate the  |
| U007 | 263f7c1f685b | heading | ## The Workflow |
| U008 | 78a6f9554c36 | heading | ### Week 1: Discovery + Architecture |
| U009 | eaabb82808e7 | paragraph | **Step 1 — Activate Sprint Prioritizer** |
| U010 | 662a5c79da85 | code | ``` Activate Sprint Prioritizer. Project: RetroBoard — a real-time team retrospective tool for remote teams. Timeline: 4 weeks to MVP launch. Core features: use |
| U011 | b1cad576161a | paragraph | **Step 2 — Activate UX Researcher (in parallel)** |
| U012 | ac31cada6c3a | code | ``` Activate UX Researcher. I'm building a team retrospective tool for remote teams (5-20 people). Competitors: EasyRetro, Retrium, Parabol. Run a quick competi |
| U013 | 8782b4879b5a | paragraph | **Step 3 — Hand off to Backend Architect** |
| U014 | d583b6506505 | code | ``` Activate Backend Architect. Here's our sprint plan: [paste Sprint Prioritizer output] Here's our research brief: [paste UX Researcher output] Design the API |
| U015 | 9add8c180349 | heading | ### Week 2: Build Core Features |
| U016 | 18a45f578a4c | paragraph | **Step 4 — Activate Frontend Developer + Rapid Prototyper** |
| U017 | 59176dec6520 | code | ``` Activate Frontend Developer. Here's the API spec: [paste Backend Architect output] Build the RetroBoard React app: - Stack: React, TypeScript, Tailwind, Soc |
| U018 | be2498a94e0a | paragraph | **Step 5 — Reality Check at midpoint** |
| U019 | 597e84b0f506 | code | ``` Activate Reality Checker. We're at week 2 of a 4-week MVP build for RetroBoard. Here's what we have so far: - Database schema: [paste] - API endpoints: [pas |
| U020 | 9064c7f9f3eb | heading | ### Week 3: Polish + Landing Page |
| U021 | 43c491174dab | paragraph | **Step 6 — Frontend Developer continues, Growth Hacker starts** |
| U022 | fc172bbefa72 | code | ``` Activate Growth Hacker. Product: RetroBoard — team retrospective tool, launching in 1 week. Target: Engineering managers and scrum masters at remote-first c |
| U023 | aa4aad8270c9 | heading | ### Week 4: Launch |
| U024 | c391c382ac17 | paragraph | **Step 7 — Final Reality Check** |
| U025 | 54ae3fac9a94 | code | ``` Activate Reality Checker. RetroBoard is ready to launch. Evaluate production readiness: - Live URL: [url] - Test accounts created: yes - Error monitoring: S |
| U026 | fc106c524b8f | heading | ## Key Patterns |
| U027 | 180aff2d32f0 | list | 1. **Sequential handoffs**: Each agent's output becomes the next agent's input 2. **Parallel work**: UX Researcher and Sprint Prioritizer can run simultaneously |
| U028 | ea2d093f0e83 | heading | ## Tips |
| U029 | 44b47fec1029 | list | - Copy-paste agent outputs between steps — don't summarize, use the full output - If a Reality Checker flags an issue, loop back to the relevant specialist to f |
