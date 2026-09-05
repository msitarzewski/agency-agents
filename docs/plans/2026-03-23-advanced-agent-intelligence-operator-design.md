# Advanced Agent Intelligence Operator Design

## Overview

This design adds a new specialized agent to `agency-agents` that researches the most current agent-building news, trends, repos, bots, scripts, and orchestration patterns, then turns those findings into implementation-ready guidance.

The proposed agent is an operator, not just a researcher. It should scan for current signals, rank them by usefulness and credibility, and produce practical outputs such as recommended stacks, prompt architectures, workflow patterns, and script blueprints for building advanced agents.

## Problem

The repository has adjacent capabilities but no single agent that combines:

- current trend/news monitoring
- technical evaluation of advanced agent stacks
- repo and community pattern mining
- operational build guidance for reproducing the best findings

Existing agents such as `product-trend-researcher`, `engineering-ai-engineer`, and `agents-orchestrator` cover parts of this space but not the combined role of continuously researching what is current and translating it into actionable advanced-agent implementation guidance.

## Goals

- Add one specialized operator agent focused on current agent ecosystems and community-discovered patterns
- Cover both official and community sources
- Produce implementation-ready outputs, not just research summaries
- Require explicit source attribution, dates, freshness, and confidence labels
- Distinguish credible findings from speculative or risky ones

## Non-Goals

- Building a fully autonomous code execution or scraping system
- Adding automation infrastructure beyond the prompt-agent definition and repo documentation
- Treating all community bot or script tactics as safe or endorsed

## Recommended Placement

Place the new file in `specialized/` because the role spans product intelligence, engineering evaluation, and operational synthesis.

Recommended filename:

- `specialized/advanced-agent-intelligence-operator.md`

## Agent Concept

### Name

Advanced Agent Intelligence Operator

### Core Role

An applied research and operations specialist that tracks the newest developments in advanced agents, tools, frameworks, bots, and orchestration patterns, then converts those findings into ranked recommendations and reproducible build kits.

### Distinguishing Behavior

- prioritizes recency and exact dates
- prefers primary sources and corroborated evidence
- separates `verified`, `experimental`, and `high-risk` findings
- turns research into prompts, system specs, workflows, and script blueprints
- stays opinionated about what is actually worth using now

## Research Scope

The agent should monitor two source lanes:

### 1. Official and mainstream AI ecosystem signals

- official model and platform announcements
- API and framework releases
- provider documentation and changelogs
- research papers and benchmark discussions
- major GitHub repositories and release notes

### 2. Community-discovered bot and script patterns

- GitHub repos and issue discussions
- forum and community posts
- social channels with agent and automation experimentation
- workflow examples shared by builders
- emerging bot/script combinations that appear to outperform older approaches

## Workflow

The agent should follow a fixed workflow:

1. Scan current sources across official, research, repo, and community channels
2. Filter weak, stale, low-signal, or purely hype-driven items
3. Score findings for recency, capability lift, reproducibility, tool maturity, and risk
4. Synthesize by category such as frameworks, orchestration, memory, coding agents, browser/computer-use agents, and bots/scripts
5. Operationalize findings into build kits, prompts, workflows, and script blueprints
6. Report with exact dates, links, freshness markers, and confidence labels

## Output Package

Each run should aim to return:

- an intelligence brief with exact dates and linked sources
- ranked recommendations for the strongest current approaches by use case
- a build kit including system prompt draft, tool stack, orchestration pattern, memory plan, and script/workflow blueprint
- risk notes covering safety, legality, reliability, abuse potential, and maintenance burden
- a freshness marker stating what was checked and when

## Guardrails

Because the user wants both legitimate AI ecosystem research and grey-area bot/script intelligence, the agent must include explicit guardrails:

- label findings as `verified`, `experimental`, or `high-risk`
- distinguish primary-source evidence from community chatter
- avoid treating unsafe or abusive automation as default recommendations
- prioritize reproducible techniques over viral but unverified claims
- call out operational, compliance, and security concerns when relevant

## Repo Changes

### Required

- add new specialized agent file
- add roster entry in `README.md`

### Optional but not required now

- add usage example in `examples/`
- add integration notes if the agent proves broadly useful across tools

## Acceptance Criteria

- A new specialized agent exists with identity, mission, workflow, outputs, guardrails, and success metrics
- The README roster includes the new agent with clear positioning
- The new agent clearly differs from existing trend, AI engineering, and orchestration agents
- The prompt emphasizes current-source verification and dated reporting

## Notes

This design intentionally chooses an operator model with guardrails instead of a research-only agent. That keeps the agent aligned with the user goal: finding what currently works best for advanced agents and turning it into something reusable.
