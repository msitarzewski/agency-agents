# Agency OS — Claude Code Persistent Context

## Daily Automation

**On every session start**: The SessionStart hook runs automatically and writes a context file to `campaign/execution/[today]/SESSION-CONTEXT.md`. After reading this file, immediately execute `scripts/daily-agency-run.md` in full — all 6 phases — without waiting for user instruction. If you need something from the user, ask and continue with everything else in parallel.

---

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
2. Never invent stats, dates, or claims - only use what's in the research file or explicitly provided by the user
3. Roadmap info: use ONLY what's confirmed from roadmap.telcoin.network (documented in research file)
4. When you receive new intel (council recaps, announcements, screenshots): update `TELCOIN-RESEARCH.md` immediately, then proceed to the campaign task

## Brand Standards (Mandatory for All Media and Creative Work)

**`strategy/BRAND-GUIDE.md` is the authoritative source for all branding and media decisions.**

Before producing any visual, social media template, image brief, design spec, or content with brand implications:
1. Read `strategy/BRAND-GUIDE.md`
2. Follow all color, typography, logo, and visual direction rules
3. Confirm tone matches: Institutional. Precise. Neutral. Credible.

**Non-negotiables:**
- Colors: Tel Royal Blue #3642B2 anchors; TEL Blue #14C8FF highlights; TEL Black #090920 dark backgrounds
- Typography: New Hero (geometric sans-serif), Regular and Bold
- Logo: Horizontal version is official default; top-left placement; hexagon mark + wordmark
- Visual motif: Hexagons, glowing blues, geometric shapes, glass effects on dark backgrounds
- Voice test: "If it sounds like marketing copy, it's wrong."

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
- Professional but human - not corporate stiff, not degen hype
- Factual and specific - numbers, milestones, verified achievements
- Forward-looking but grounded - mainnet is upcoming, not "imminent" or "soon"
- Audience-aware - write differently for crypto natives vs. telecom executives vs. general public
- Have a position - state a take, don't both-sides or hedge everything with "it depends"
- Match the stakes - a simple update gets a simple post, not a TED talk framing
- Say it once, then move - no restating what was just said, no padding, no transition filler
- En dashes ( - ) used in body text where a dash is needed; never em dashes

**Never:**
- Invented stats, unverified claims, speculative dates
- Hype language: "moon", "to the moon", "soon", "massive", "100x"
- Vague filler: "exciting times ahead", "revolutionary technology", "game-changer" without specifics
- Use mainnet timing claims without linking to roadmap.telcoin.network
- False drama: "Here's the thing", "Here's where it gets interesting", "This changes everything", "This is huge", "Buckle up"
- Buzzwords: "ecosystem" used vaguely, "leverage" as a verb, "robust", "holistic", "synergy", "paradigm shift", "navigate" (when not literal), "unpack", "dive deep", "landscape"
- Structural tics: starting paragraphs with "Now,", "So,", "Look,"; bullet-pointing things that should be a sentence; summarizing what the reader just read before responding
- Em dashes - rewrite the sentence or use a regular hyphen instead
- Sycophantic openers: "Great question!", "That's a really interesting point", "I'd be happy to help" - just say the thing

**Content OS rules (apply to all @telcoinTAO posts):**
- Every post (except Tier 1 governance) must include one conversation invitation - institutional, not casual. Examples: "What is your assessment?" "Which approach is preferable, and why?" - never "What do you think?" or "Want to learn more?"
- Conversation prompts must use Neutral Authority framing: no opinions, no personal voice, no emotional framing - just an institutional question that cannot be misread as promotional
- Link handling: lead with the insight, then include the link. Never open a post with a URL. Exception: first-reply link placement is allowed if analytics show it performs better for that format
- Priority posts (Milestones, Votes, Key Education): run the 60-minute launch window after posting - actively reply to early questions, add clarifying context, keep the thread alive for the first hour to maximize out-of-network pickup
- No engagement bait: no giveaways, "tag 3 friends", "like if you agree" - this triggers negative signals

**Tier 1 governance-specific rules:**
- No emojis, no contractions, no enthusiasm language ("excited", "thrilled", "proud")
- No conversation prompts or questions unless directional: "Read the agenda", "View the record", "Observe via Discord"
- Tone: strictly institutional - reads as appropriate in a regulatory newsletter

**Voice anchors (reference these when setting tone):**
- Telcoin = infrastructure play, not speculation
- GSMA MNO validators = institutional-grade credibility, not just another L1
- eUSD = first bank-issued on-chain stablecoin - a regulatory milestone, not a product feature
- The mission is financial inclusion for mobile users globally - lead with impact, not technology

---

## Current Campaign Status (update this section as work progresses)

**Research**: Complete — `campaign/research/TELCOIN-RESEARCH.md` fully populated
- Source: telcoin.org, telcoin.network, roadmap screenshots, council recaps (week of Mar 10, 2026)
- Last updated: March 11, 2026

**Active work**: Campaign materials in `campaign/execution/`

**Learning path status (as of March 16, 2026):**
- LP1 (Governance Fundamentals): Complete - Posts 1-6 published Feb 9 through ~Mar 8
- LP2 (Platform Architecture): In progress - Posts 1-3 published Mar 9-11 (Platform Overview, Telcoin Network, TELx); Posts 4-6 remaining (eUSD/TDAB, Telcoin Wallet, Integration Story)
- LP3 (Differentiation): Not started
- LP4 (Participation): Not started

**Upcoming triggers**:
- TELx Council: March 18, 3PM EST
- Trading Fee Rebate Program deployment: late March 2026
- Merkl trial going live: ~April 2026

**Content OS reference**: `strategy/CONTENT-OS.md`

**Standing instruction**: After each council call recap is shared, update `TELCOIN-RESEARCH.md` first, then flag what campaign content it unlocks.

---

## Session Startup Checklist

On every new session, before doing anything else:
1. Confirm active branch is `claude/campaign-iLgt5` (run `git branch` if unsure)
2. Read `campaign/research/TELCOIN-RESEARCH.md` for current client state
3. Check if user has shared any new intel (council recaps, announcements) — if yes, update research file first
4. Then proceed to the actual task
