# Agency OS — Claude Code Persistent Context

## Who We Are
**Telcoin Association Marketing Agency** — a dedicated marketing operation embedded inside the Telcoin Association ecosystem. We handle content strategy, campaign execution, social media, community communications, research, and creative production for Telcoin Association and its subsidiaries (Telcoin Network, Telcoin Digital Asset Bank, TELx, Telcoin Wallet).

This file is the agency brain. Read it at the start of every session. It replaces the need for the user to re-brief you.

---

## Active Client

**Telcoin Association**
- Swiss Verein, domiciled Lugano, Switzerland
- Mission: Financial inclusion via blockchain-powered mobile financial services
- Primary products: Telcoin Network (L1 blockchain), Telcoin Wallet (remittance app), eUSD (bank-issued stablecoin), Telcoin Digital Asset Bank (Nebraska charter), TELx (DeFi liquidity platform)
- Full research file: `campaign/research/TELCOIN-RESEARCH.md` — ALWAYS read this before producing any client content

**Key accounts:**
- X/Twitter: @telcoinTAO
- Forum: forum.telcoin.org
- YouTube: youtube.com/@TelcoinTAO
- GitHub: github.com/Telcoin-Association
- Roadmap: roadmap.telcoin.network

---

## Working Branch & Git Protocol

- **Active branch**: `claude/campaign-iLgt5`
- **Always push to**: `git push origin claude/campaign-iLgt5`
- **Never push to main** without explicit user instruction
- Commit messages: concise, imperative, describe the "why"
- Append to every commit message: `https://claude.ai/code/session_01Fpcoo2uktkZj9o2BmubZ3h`

---

## Memory Protocol (How to Use This Repo's Knowledge)

Before acting on ANY client task:
1. Read `campaign/research/TELCOIN-RESEARCH.md` for verified facts, figures, product details, roadmap status
2. Never invent stats, dates, or claims — only use what's in the research file or explicitly provided by the user
3. Roadmap info: use ONLY what's confirmed from roadmap.telcoin.network (documented in research file)
4. When you receive new intel (council recaps, announcements, screenshots): update `TELCOIN-RESEARCH.md` immediately, then proceed to the campaign task

---

## Directory Map

```
/campaign/
  research/         — Verified client intel (source of truth)
  execution/        — Live campaign deliverables (posts, threads, scripts)
  AGENTS.md         — Which agent type to use for which task
  WORKFLOW.md       — Day-to-day agency SOPs

/design/
  DESIGN-TEAM.md    — Full design team guide (agents, pipeline, tools)
  templates/        — Video script + image brief templates
  briefs/           — Active creative briefs
  output/           — Agent-produced scripts, storyboards, image prompts

/agency-agents/     — Agent configuration and persona files (100+ confirmed active)
/marketing/         — Marketing frameworks and templates
/strategy/          — Strategy documents and briefs
/content/           — Long-form content and editorial
/scripts/           — Automation scripts
```

---

## Agent Dispatch — When to Use Which Specialized Agent

Use the Agent tool with these subagent types for specific tasks:

| Task | Agent Type |
|---|---|
| Write tweets, threads, captions, copy | `Content Creator` |
| @telcoinTAO tweets, threads, real-time engagement | `Twitter Engager` |
| Build social media strategy, editorial calendar | `Social Media Strategist` |
| Research competitors, market trends, news | `Trend Researcher` |
| Deep codebase/repo exploration | `Explore` |
| Plan a complex multi-step campaign | `Plan` |
| SEO-optimized web copy, blog posts | `SEO Specialist` |
| Brand voice, consistency review | `Brand Guardian` |
| Community replies, support messaging | `Support Responder` |
| Data analysis, performance metrics | `Analytics Reporter` |
| Developer-facing content, docs | `Technical Writer` |
| **DESIGN — visual narrative, storyboards, video direction** | `Visual Storyteller` |
| **DESIGN — AI image prompts (Midjourney/DALL-E/Flux)** | `Image Prompt Engineer` |
| **DESIGN — human-featuring images (representation-safe)** | `Inclusive Visuals Specialist` |
| **DESIGN — TikTok scripts, hooks, short-form video** | `TikTok Strategist` |
| **DESIGN — Instagram Reels, Stories, visual captions** | `Instagram Curator` |
| **DESIGN — autonomous carousel generate + publish** | `Carousel Growth Engine` |
| **DESIGN — personality, delight, creative edge** | `Whimsy Injector` |
| Campaign execution tracking | `Project Shepherd` |

**Full design team guide**: `design/DESIGN-TEAM.md`
**Templates**: `design/templates/` (video script, image brief)

**Parallelization rule**: launch multiple agents simultaneously for independent subtasks (e.g., write 3 tweet threads for different audiences at the same time).

---

## Tone & Style Rules

**Always:**
- Professional but human — not corporate stiff, not degen hype
- Factual and specific — numbers, milestones, verified achievements
- Forward-looking but grounded — mainnet is upcoming, not "imminent" or "soon™"
- Audience-aware — write differently for crypto natives vs. telecom executives vs. general public

**Never:**
- Invented stats, unverified claims, speculative dates
- Hype language: "moon", "to the moon", "soon", "massive", "100x"
- Vague filler: "exciting times ahead", "revolutionary technology", "game-changer" without specifics
- Use mainnet timing claims without linking to roadmap.telcoin.network

**Voice anchors (reference these when setting tone):**
- Telcoin = infrastructure play, not speculation
- GSMA MNO validators = institutional-grade credibility, not just another L1
- eUSD = first bank-issued on-chain stablecoin — a regulatory milestone, not a product feature
- The mission is financial inclusion for mobile users globally — lead with impact, not technology

---

## Current Campaign Status (update this section as work progresses)

**Research**: Complete — `campaign/research/TELCOIN-RESEARCH.md` fully populated
- Source: telcoin.org, telcoin.network, roadmap screenshots, council recaps (week of Mar 10, 2026)
- Last updated: March 11, 2026

**Active work**: Campaign materials in `campaign/execution/`

**Upcoming triggers**:
- Platform & Treasury Council: March 12, 4PM EST
- TAN Council: March 12, 5PM EST
- TELx Council: March 18, 3PM EST
- Merkl trial going live: ~April 2026
- TANIP-1 target: late March 2026

**Standing instruction**: After each council call recap is shared, update `TELCOIN-RESEARCH.md` first, then flag what campaign content it unlocks.

---

## Session Startup Checklist

On every new session, before doing anything else:
1. Confirm active branch is `claude/campaign-iLgt5` (run `git branch` if unsure)
2. Read `campaign/research/TELCOIN-RESEARCH.md` for current client state
3. Check if user has shared any new intel (council recaps, announcements) — if yes, update research file first
4. Then proceed to the actual task
