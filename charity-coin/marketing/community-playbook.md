# Charity Coin -- Community Playbook

## Overview

This playbook defines how we build, manage, and grow the Charity Coin community. Our community is the engine of the project: holders vote on causes, ambassadors spread the mission, and contributors shape governance. Every design decision prioritizes transparency, inclusivity, and genuine impact over hype.

---

## 1. Discord Server Structure

### Channel Architecture

```
CHARITY COIN DISCORD
│
├── WELCOME
│   ├── #welcome              -- Auto-greeter, rules, verify button
│   ├── #rules-and-conduct    -- Community guidelines, CoC
│   ├── #introductions        -- New members introduce themselves
│   └── #faq                  -- Pinned FAQs, quick links
│
├── ANNOUNCEMENTS
│   ├── #announcements        -- Official team updates (read-only)
│   ├── #burn-alerts          -- Automated burn event notifications (read-only)
│   ├── #governance-votes     -- Vote open/close notifications (read-only)
│   └── #impact-reports       -- Monthly donation reports (read-only)
│
├── COMMUNITY
│   ├── #general              -- Main chat
│   ├── #price-talk           -- Price discussion (contained here)
│   ├── #memes                -- Community memes and creative content
│   ├── #show-your-impact     -- Members share personal donation/impact stories
│   └── #off-topic            -- Non-CHA discussion
│
├── CAUSES
│   ├── #health               -- Global Health cause discussion
│   ├── #education            -- Education cause discussion
│   ├── #environment          -- Environment cause discussion
│   ├── #clean-water          -- Clean Water cause discussion
│   └── #zero-hunger          -- Zero Hunger cause discussion
│
├── GOVERNANCE
│   ├── #proposals            -- Discuss upcoming governance proposals
│   ├── #active-votes         -- Current vote discussion
│   ├── #governance-results   -- Vote outcomes and analysis
│   └── #dao-general          -- DAO structure and process discussion
│
├── BUILDERS
│   ├── #dev-discussion       -- Technical discussion
│   ├── #bug-reports          -- Bug reports and triage
│   ├── #feature-requests     -- Community feature ideas
│   ├── #bounties             -- Open bounties and submissions
│   └── #integrations         -- DeFi protocol integration discussion
│
├── PROGRAMS
│   ├── #ambassador-hub       -- Ambassador coordination (role-gated)
│   ├── #cause-champions      -- Cause Champion updates (role-gated)
│   ├── #burn-leaderboard     -- Leaderboard discussion and competition
│   └── #referral-program     -- Referral tracking and rewards
│
├── SUPPORT
│   ├── #help                 -- General support
│   ├── #ticket-create        -- Open a private support ticket
│   └── #tutorials            -- How-to guides and walkthroughs
│
└── VOICE
    ├── #town-hall            -- Weekly AMAs and community calls
    ├── #cause-conversations  -- Deep-dives on specific causes
    └── #hangout              -- Open voice chat
```

### Roles

| Role | Color | Permissions | How to Earn |
|------|-------|-------------|-------------|
| **Core Team** | Gold | All permissions | Team members |
| **Moderator** | Purple | Manage messages, mute, kick, manage threads | Application + team approval |
| **Ambassador** | Blue | Access to ambassador-hub, post in announcements threads | Ambassador program acceptance |
| **Cause Champion** | Green | Access to cause-champion channel, cause-specific mod powers | Nominated by community, approved by team |
| **Verified Holder** | Teal | Access to holder-gated channels, governance channels | Wallet verification via Collab.Land |
| **OG** | Silver | Cosmetic badge, early access to features | Joined before mainnet launch |
| **Contributor** | Orange | Access to builder channels | Merged PR or completed bounty |
| **Member** | Gray | Base permissions | Complete onboarding verification |

### Bots

| Bot | Purpose | Configuration |
|-----|---------|---------------|
| **Collab.Land** | Token-gated role verification | Verify CHA balance for "Verified Holder" role |
| **Carl-bot** | Auto-moderation, reaction roles, logging | Anti-spam, anti-raid, keyword filters |
| **MEE6 / Arcane** | Leveling, engagement tracking | XP for messages, voice time; level milestones unlock perks |
| **Custom Burn Bot** | Post burn events from on-chain data | Webhook from API; posts in #burn-alerts with amount, cause, tx link |
| **Governance Bot** | Vote notifications and reminders | Webhook integration; posts vote open/close/results |
| **Ticket Bot** | Support ticket system | Creates private channels for support requests |

---

## 2. Community Programs

### 2.1 Ambassador Program

**Purpose**: Empower passionate community members to represent Charity Coin in their networks and geographies.

**Structure**:

| Tier | Requirements | Benefits |
|------|-------------|----------|
| **Bronze Ambassador** | 500+ CHA held, 1 month active, pass quiz | Ambassador role, exclusive channel access, monthly CHA airdrop |
| **Silver Ambassador** | 3 months as Bronze, 10+ referrals, 2+ content pieces | Increased CHA airdrop, early feature access, co-host Spaces |
| **Gold Ambassador** | 6 months as Silver, 50+ referrals, led 1+ community event | Governance weight bonus, quarterly stipend, conference tickets |

**Responsibilities**:
- Create at least 2 pieces of educational content per month (threads, videos, articles)
- Actively moderate community channels for 4+ hours per week
- Represent Charity Coin at local crypto meetups when possible
- Report weekly on community sentiment and growth metrics
- Follow brand guidelines and messaging pillars

**Application Process**:
1. Fill out application form (background, motivation, content samples)
2. Hold minimum CHA balance (verified on-chain)
3. Interview with community lead
4. 30-day probation period
5. Monthly performance review

### 2.2 Cause Champions

**Purpose**: Deep-focus advocates for each of the five causes who bridge the gap between the crypto community and real-world impact organizations.

**Structure**:
- 2-3 Champions per cause (10-15 total)
- Each Champion "owns" their cause's Discord channel and content
- Direct communication line with associated charity partners

**Responsibilities**:
- Curate weekly impact news for their cause channel
- Coordinate with charity partner contacts for updates and stories
- Present cause impact data during monthly community calls
- Propose cause-specific initiatives to governance
- Organize cause-themed community events (fundraiser challenges, awareness days)

**Selection**:
- Community nomination (minimum 10 unique nominators)
- Demonstrated passion for the cause (personal statement + evidence)
- Core team approval
- 6-month term with renewal option

### 2.3 Burn Leaderboard

**Purpose**: Gamify and celebrate the deflationary mechanism that makes Charity Coin unique.

**Mechanics**:
- Track cumulative CHA burned attributed to each wallet address (via transaction fees)
- Public leaderboard on the dApp dashboard and Discord
- Monthly, quarterly, and all-time rankings

**Rewards**:

| Rank | Monthly Reward |
|------|---------------|
| #1 | Custom NFT badge + feature in monthly report + 5,000 CHA |
| #2-5 | Custom NFT badge + 2,500 CHA |
| #6-10 | Custom NFT badge + 1,000 CHA |
| #11-25 | Honorable mention + 500 CHA |

**Milestones** (collective):
- 1M CHA burned: Community celebration event, commemorative NFT for all holders
- 10M CHA burned: Charity partner video thank-you, special governance proposal unlocked
- 100M CHA burned: Major milestone event, potential IRL celebration, documentary consideration

---

## 3. Engagement Tactics

### 3.1 Weekly AMAs

| Element | Details |
|---------|---------|
| **Platform** | Discord Voice (#town-hall) + simulcast on Twitter Spaces |
| **Schedule** | Every Thursday at 18:00 UTC |
| **Duration** | 45-60 minutes |
| **Format** | 15 min team updates, 15 min guest speaker, 15-30 min open Q&A |
| **Guest rotation** | Charity partners, DeFi protocol teams, Base ecosystem builders, cause experts |
| **Pre-AMA** | Collect questions in #proposals or via Google Form 24 hours prior |
| **Post-AMA** | Summary thread on Twitter/X, recording posted to YouTube, key takeaways in #announcements |

### 3.2 Monthly Impact Reports

**Published on**: 1st of each month, covering the prior month.

**Contents**:
- Total CHA burned (month + cumulative)
- Total USDC donated (month + cumulative, broken down by cause)
- Charity partner updates (how funds were used, with evidence)
- Governance vote outcomes
- Holder growth metrics
- Burn Leaderboard top 10
- Community highlights (top contributors, best content)

**Distribution**:
- Discord #impact-reports
- Twitter/X thread with key visuals
- Medium/Mirror blog post (full version)
- Email to subscriber list

### 3.3 Governance Participation Rewards

**Objective**: Achieve 30%+ voter participation on all governance proposals.

| Action | Reward |
|--------|--------|
| Vote on a proposal | Small CHA airdrop (claimable via dashboard) |
| Submit a proposal that reaches quorum | Larger CHA reward + "Proposer" NFT badge |
| Vote on 5 consecutive proposals | "Consistent Voter" badge + bonus CHA |
| Vote on all proposals in a quarter | "Governance OG" role + quarterly drawing entry |

### 3.4 Additional Engagement Events

| Event | Frequency | Description |
|-------|-----------|-------------|
| **Cause Spotlight Week** | Monthly | One week dedicated to a single cause; charity partner takeover, educational content, themed challenges |
| **Build in Public Sessions** | Bi-weekly | Dev team streams development progress, takes community input |
| **Impact Challenges** | Monthly | Community-driven challenges (e.g., "donate to a local food bank, post proof, earn CHA") |
| **Meme Contests** | Monthly | Community votes on best Charity Coin memes; winners earn CHA |
| **Trivia Nights** | Bi-weekly | Discord trivia on crypto, charity, and Charity Coin knowledge |

---

## 4. Moderation Guidelines

### 4.1 Code of Conduct

All community members must:
1. **Be respectful**: No harassment, hate speech, doxxing, or personal attacks.
2. **Stay on topic**: Use appropriate channels for discussions.
3. **No scams or spam**: No unsolicited DMs, phishing links, or promotion of unrelated projects.
4. **No financial advice**: Do not present personal opinions as financial advice. CHA is not an investment.
5. **Protect privacy**: Do not share others' personal information.
6. **Follow Discord ToS**: Comply with Discord's Terms of Service and Community Guidelines.
7. **Report issues**: Use the ticket system for concerns rather than public callouts.

### 4.2 Moderation Actions

| Offense | First | Second | Third |
|---------|-------|--------|-------|
| Spam / self-promotion | Warning + message delete | 24-hour mute | Ban |
| Mild toxicity | Warning | 24-hour mute | 7-day ban |
| Hate speech / harassment | Immediate 7-day ban | Permanent ban | -- |
| Scam / phishing links | Immediate permanent ban | -- | -- |
| Doxxing | Immediate permanent ban | -- | -- |
| FUD with false claims | Warning + fact-check reply | 24-hour mute | 7-day ban |
| Price manipulation talk | Warning + redirect to #price-talk | 24-hour mute | 7-day ban |

### 4.3 Moderator Standards

- Moderators must log all actions in a private #mod-log channel
- Decisions should be made by consensus when possible (2+ mods agree)
- Bans over 7 days require core team approval
- Moderators must remain neutral in governance discussions
- Monthly moderator sync calls to discuss patterns and adjust policies
- Moderator burnout check-ins: team lead reviews workload monthly

### 4.4 Anti-Raid Protocol

1. **Detection**: Carl-bot auto-detects mass joins (20+ in 60 seconds)
2. **Response**: Server lockdown (verification level raised to "highest")
3. **Cleanup**: Bulk-remove raid accounts, review recent messages
4. **Recovery**: Post in #announcements explaining the situation, lower verification after 1 hour
5. **Post-mortem**: Document in mod-log, adjust anti-raid settings if needed

---

## 5. Onboarding Flow for New Members

### Step-by-Step Journey

```
Join Server
    │
    ▼
#welcome (auto-DM with welcome message)
    │ Read rules, click verify button
    ▼
Receive "Member" role
    │ Directed to #introductions
    ▼
Post introduction (optional but encouraged)
    │ Bot reacts with emoji, community welcomes
    ▼
Explore #faq and #tutorials
    │ Learn how CHA works, how to buy, how to vote
    ▼
Connect wallet via Collab.Land
    │ If holding CHA → receive "Verified Holder" role
    ▼
Engage in #general, explore cause channels
    │ Find a cause they care about
    ▼
Participate in governance vote
    │ Earn first governance reward
    ▼
Consider Ambassador / Cause Champion programs
```

### Welcome Message Template

```
Welcome to Charity Coin! Every CHA transaction donates 2.5% to a
community-voted cause and burns tokens, making your participation
both generous and deflationary.

Quick start:
1. Read the rules in #rules-and-conduct
2. Say hello in #introductions
3. Check #faq for common questions
4. Connect your wallet to verify as a holder
5. Vote on the current cause in #active-votes

Need help? Open a ticket in #ticket-create.
```

### First-Week Nudge Sequence

| Day | Action |
|-----|--------|
| Day 0 | Welcome DM with quick-start guide |
| Day 1 | Bot reminder: "Have you checked out the five causes we support?" |
| Day 3 | Bot reminder: "A governance vote is live! Have your say in #active-votes" |
| Day 7 | Bot reminder: "You've been here a week! Check out the Ambassador program in #ambassador-hub" |

---

## 6. Crisis Communication Plan

### 6.1 Crisis Severity Levels

| Level | Definition | Examples |
|-------|------------|---------|
| **Level 1 -- Low** | Minor issue, limited community awareness | Small bug report, brief service outage, single negative article |
| **Level 2 -- Medium** | Significant issue, growing community concern | Extended downtime, governance dispute, charity partner controversy |
| **Level 3 -- High** | Major incident, widespread attention | Smart contract vulnerability, regulatory action, major exploit |
| **Level 4 -- Critical** | Existential threat, immediate action required | Active exploit draining funds, legal cease-and-desist, key team departure |

### 6.2 Response Framework

**For all levels**:

| Step | Action | Timeline |
|------|--------|----------|
| 1. Detect | Monitor social channels, on-chain alerts, community reports | Immediate |
| 2. Assess | Core team evaluates severity, scope, and facts | Within 30 minutes |
| 3. Acknowledge | Post brief acknowledgment in #announcements | Within 1 hour of detection |
| 4. Investigate | Technical and/or operational investigation | Ongoing |
| 5. Communicate | Detailed update with facts, actions taken, next steps | Within 4 hours (Level 3-4) or 24 hours (Level 1-2) |
| 6. Resolve | Implement fix, post resolution update | As soon as resolved |
| 7. Post-mortem | Publish transparent post-mortem (Level 2+) | Within 1 week |

### 6.3 Communication Templates

**Acknowledgment (fast, brief)**:
> We are aware of [brief description of issue]. The team is actively investigating. We will provide a detailed update within [timeframe]. Funds are [safe/status]. Please avoid [specific actions if relevant].

**Detailed Update**:
> Update on [issue]: Here is what we know so far: [facts]. Here is what we are doing: [actions]. Here is what you should do: [user actions]. Next update by: [time].

**Resolution**:
> [Issue] has been resolved. Root cause: [explanation]. Actions taken: [list]. Preventive measures: [list]. Full post-mortem will be published by [date].

### 6.4 Channel Priorities During Crisis

1. **Discord #announcements** -- First and primary channel
2. **Twitter/X** -- Simultaneous with Discord for public visibility
3. **Telegram announcements** -- Simultaneous
4. **Medium/blog** -- For detailed post-mortems
5. **Email** -- For registered users if relevant

### 6.5 Rules During Crisis

- **One voice**: Only designated spokespeople post official updates
- **Facts only**: Never speculate publicly; say "we are investigating" if unsure
- **No delete**: Do not delete community questions or criticism (unless rule violations)
- **Moderate, don't censor**: Keep channels open but increase mod presence to manage panic
- **Slow mode**: Enable slow mode in #general during high-traffic crises (30-60 second cooldown)
- **Pin updates**: Pin the latest official update in all relevant channels

---

## 7. Community Health Metrics

Track these metrics weekly to gauge community health:

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Daily active Discord users | 500+ | 200-500 | < 200 |
| Messages per day | 1,000+ | 300-1,000 | < 300 |
| New members per week | 200+ | 50-200 | < 50 |
| Member churn (weekly) | < 5% | 5-10% | > 10% |
| Support tickets resolved < 24h | > 90% | 70-90% | < 70% |
| Governance vote participation | > 30% | 15-30% | < 15% |
| Sentiment (positive:negative ratio) | > 3:1 | 1:1 to 3:1 | < 1:1 |
| Mod actions per day | < 20 | 20-50 | > 50 |

---

## 8. Community Values

These values guide every community decision:

1. **Impact over hype**: We celebrate donations and burns, not price pumps.
2. **Transparency over trust**: We show receipts, not promises.
3. **Inclusion over exclusion**: Every holder has a voice, regardless of bag size.
4. **Education over shilling**: We teach how it works, not why to buy.
5. **Long-term over short-term**: We build for years, not news cycles.
