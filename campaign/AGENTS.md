# Agent Dispatch Guide
## Telcoin Association Marketing Agency
## All agents confirmed active — definitions in /agency-agents/

All agents below are callable via the Agent tool with the exact `subagent_type` name shown. They map 1:1 to definition files in `/agency-agents/`. Run multiple in parallel for independent tasks.

---

## Primary Agency Agents (Use These Most)

### `Content Creator`
**File**: `agency-agents/marketing-content-creator.md`
**Use for**: Blog posts, forum posts, email copy, press releases, multi-platform campaign copy, editorial calendars
**Example**:
> "Write a forum post for forum.telcoin.org announcing the Merkl trial approval. Audience: TEL holders familiar with DeFi. Facts: [paste from TELCOIN-RESEARCH.md TELx section]."

### `Twitter Engager`
**File**: `agency-agents/marketing-twitter-engager.md`
**Use for**: @telcoinTAO tweets, threads, reply strategy, real-time engagement, thought leadership threads
**This is the primary agent for X/Twitter content — more specialized than Social Media Strategist for Twitter specifically**
**Example**:
> "Write a 6-tweet thread for @telcoinTAO covering the Adiri testnet Phase 2 progress. Audience: crypto-native TEL community. Tone: confident, factual, milestone-focused. No hype. End with CTA to roadmap.telcoin.network."

### `Social Media Strategist`
**File**: `agency-agents/marketing-social-media-strategist.md`
**Use for**: Cross-platform strategy, editorial calendars, campaign planning across channels, engagement frameworks
**Example**:
> "Build a 4-week content calendar for @telcoinTAO covering the period leading up to Merkl trial launch (~April). Mix: technical updates, governance, builder spotlights, community."

### `Growth Hacker`
**File**: `agency-agents/marketing-growth-hacker.md`
**Use for**: Distribution strategy, viral mechanics, community growth, funnel optimization, referral programs
**Example**:
> "Design a growth strategy for TEL holder acquisition around the Kraken listing momentum. Focus on organic Twitter amplification and Reddit presence."

### `Brand Guardian`
**File**: `agency-agents/design-brand-guardian.md`
**Use for**: Voice consistency reviews, messaging audits, checking copy against tone rules in CLAUDE.md
**Example**:
> "Review these 5 draft tweets for brand consistency. Flag hype language, unverified claims, or anything off-tone per the rules in CLAUDE.md."

### `Trend Researcher`
**File**: `agency-agents/product-trend-researcher.md`
**Use for**: Competitive intelligence, market trend monitoring, news analysis, opportunity identification
**Example**:
> "Research how XRP, Stellar, and Celo are positioning their remittance products in Q1 2026. Find messaging gaps Telcoin can own."

### `SEO Specialist`
**File**: `agency-agents/marketing-seo-specialist.md`
**Use for**: Website copy, blog posts targeting search, keyword strategy, meta descriptions
**Example**:
> "Write SEO-optimized copy targeting 'bank-issued stablecoin' for a Telcoin landing page. Use facts from TELCOIN-RESEARCH.md eUSD section."

### `Technical Writer`
**File**: `agency-agents/engineering-technical-writer.md`
**Use for**: Developer docs, GitHub READMEs, API references, onboarding guides for builders
**Example**:
> "Write a developer onboarding guide for Telcoin Network. EVM-compatible, build on Base now, redeploy at mainnet. Link to github.com/Telcoin-Association."

---

## Platform-Specific Agents

### `Instagram Curator`
**File**: `agency-agents/marketing-instagram-curator.md`
**Use for**: Instagram posts, Stories, Reels direction, visual storytelling, caption writing

### `Reddit Community Builder`
**File**: `agency-agents/marketing-reddit-community-builder.md`
**Use for**: r/telcoin strategy, authentic community engagement, AMA planning, value-driven posts

### `TikTok Strategist`
**File**: `agency-agents/marketing-tiktok-strategist.md`
**Use for**: Short-form video concepts, TikTok scripts, trend-native content

### `App Store Optimizer`
**File**: `agency-agents/marketing-app-store-optimizer.md`
**Use for**: Telcoin Wallet V5 App Store listing copy, keywords, screenshots direction

---

## Content & Creative Agents

### `Visual Storyteller`
**File**: `agency-agents/design-visual-storyteller.md`
**Use for**: Visual narrative strategy, infographic direction, data visualization concepts

### `Image Prompt Engineer`
**File**: `agency-agents/design-image-prompt-engineer.md`
**Use for**: AI image generation prompts (Midjourney, Flux, DALL-E) for social graphics, campaign visuals
**Example**:
> "Write 3 image prompts for a Twitter header representing 'telecom-grade blockchain infrastructure'. Dark blue/purple, sleek, credible. No cartoons."

### `Carousel Growth Engine`
**File**: `agency-agents/marketing-carousel-growth-engine.md`
**Use for**: Twitter/Instagram carousel content, multi-slide educational posts

---

## Research & Intelligence

### `Explore` (built-in)
**Use for**: Searching GitHub repos, reading codebases, verifying technical facts before publishing
**Example**:
> "Search github.com/Telcoin-Association for documentation on how MNO validator onboarding works."

### `Analytics Reporter`
**File**: `agency-agents/support-analytics-reporter.md`
**Use for**: Interpreting social metrics, campaign performance reports, council data summaries

### `Feedback Synthesizer`
**File**: `agency-agents/product-feedback-synthesizer.md`
**Use for**: Analyzing community sentiment, synthesizing forum/Reddit/Discord feedback into insights

---

## Strategy & Planning

### `Plan` (built-in)
**Use for**: Designing full campaign architecture, mapping deliverables and dependencies
**Example**:
> "Plan the mainnet announcement campaign. Audiences: MNO partners, crypto investors, telecom press. Deliverables: press release, tweet thread, forum post, email. Map sequence."

### `Project Shepherd`
**File**: `agency-agents/project-management-project-shepherd.md`
**Use for**: Tracking live campaign execution, managing timelines, multi-deliverable coordination

### `Sprint Prioritizer`
**File**: `agency-agents/product-sprint-prioritizer.md`
**Use for**: Deciding what content to prioritize in a given week, backlog management

### `Executive Summary Generator`
**File**: `agency-agents/support-executive-summary-generator.md`
**Use for**: Distilling council recaps or research into tight executive summaries for stakeholder comms

---

## Compliance & Legal

### `Legal Compliance Checker`
**File**: `agency-agents/support-legal-compliance-checker.md`
**Use for**: Checking content for regulatory language issues, stablecoin/banking claims accuracy
**Always run on**: eUSD content, bank charter claims, anything touching SEC/banking regulation

### `Developer Advocate`
**File**: `agency-agents/specialized-developer-advocate.md`
**Use for**: Developer community content, hackathon materials, builder ecosystem messaging

---

## Parallelization Patterns (launch these as a single message)

**Council recap → content sprint:**
- Agent 1 (`Twitter Engager`): Thread on the biggest announcement
- Agent 2 (`Content Creator`): Forum post for governance discussion
- Agent 3 (`Brand Guardian`): Review prior week's published posts for consistency

**New product announcement:**
- Agent 1 (`Twitter Engager`): Announcement thread for @telcoinTAO
- Agent 2 (`Content Creator`): Press release draft
- Agent 3 (`Technical Writer`): Developer-facing blog post
- Agent 4 (`SEO Specialist`): Landing page copy

**Weekly research + planning:**
- Agent 1 (`Trend Researcher`): Competitive snapshot
- Agent 2 (`Social Media Strategist`): Next week's calendar
- Agent 3 (`Analytics Reporter`): Last week's performance summary

---

## How to Invoke Any Agent

In Claude chat, say:
> "Launch a [Agent Name] agent to [task]. Read campaign/research/TELCOIN-RESEARCH.md for verified facts. Audience: [specify]. Tone: per CLAUDE.md rules. Output: [format]."

For parallel launch:
> "Launch these agents simultaneously: [Agent 1] to do X, [Agent 2] to do Y, [Agent 3] to do Z."

---

## Agents NOT Used for This Client (but available if scope expands)

China/APAC platforms (Bilibili, WeChat, Xiaohongshu, Zhihu, Kuaishou, Baidu SEO, China E-Commerce) — available if Telcoin expands campaigns to China markets. All definitions confirmed active in `/agency-agents/`.

Gaming/XR/Unity/Unreal agents — available but out of scope for this engagement.
