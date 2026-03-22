# Charity Coin -- Partnership Framework

## Overview

Partnerships are central to Charity Coin's mission. Charity partners receive USDC donations from on-chain fee conversion. DeFi partners expand CHA's utility. Media and influencer partners amplify our reach. This framework defines criteria, processes, and templates for each partnership category.

---

## 1. Charity Partner Program

### 1.1 Partner Criteria

All charity partners must meet the following requirements:

| Criterion | Requirement | Verification Method |
|-----------|-------------|---------------------|
| **Legal status** | Registered 501(c)(3) or equivalent in their jurisdiction | Government registration documents |
| **Mission alignment** | Work falls under one of five CHA causes (Health, Education, Environment, Water, Hunger) | Mission statement review, program audit |
| **Financial transparency** | Public financial reports, audited financials preferred | IRS Form 990, annual reports, third-party ratings |
| **Operational capacity** | Ability to receive USDC and convert to operational currency | Bank account + crypto wallet or fiscal sponsor with crypto capability |
| **Impact measurement** | Track and report measurable outcomes | Existing impact reports, monitoring & evaluation framework |
| **Reputation** | No significant controversies, fraud, or mismanagement history | Media review, Charity Navigator / GuideStar check |
| **Communication** | Willing to provide monthly updates and participate in community events | Written agreement |

**Preferred (not required)**:
- Charity Navigator rating of 3+ stars (or equivalent)
- Existing crypto/blockchain experience
- Social media presence with engaged audience
- Geographic diversity (prioritize global representation)

### 1.2 Partner Tiers

| Tier | USDC Allocation | Requirements | Benefits |
|------|----------------|--------------|----------|
| **Launch Partner** | Equal share of cause allocation | Meet all criteria, join before mainnet launch | Logo on site, co-marketing, AMA slots, governance input |
| **Growth Partner** | Proportional share based on governance vote | Meet all criteria, join post-launch | Logo on site, quarterly AMA, impact report features |
| **Micro Partner** | Small fixed allocation from cause pool | Smaller orgs, meet core criteria | Listed on partners page, annual impact feature |

### 1.3 Onboarding Process

```
Step 1: Discovery
  Partner expresses interest OR team identifies prospect
  │
Step 2: Initial Screening (1 week)
  Review against criteria checklist
  │ Pass → proceed | Fail → decline with feedback
  │
Step 3: Due Diligence (2 weeks)
  Financial audit review
  Background check (leadership, legal history)
  Reference check (2 other funders or partners)
  │
Step 4: Alignment Meeting
  Video call with Charity Coin partnerships lead
  Discuss: mission alignment, reporting expectations,
  community participation, USDC receiving setup
  │
Step 5: Agreement
  Sign partnership agreement covering:
  - USDC receiving wallet address
  - Reporting obligations (monthly impact updates)
  - Community participation commitments (1 AMA/quarter minimum)
  - Brand usage guidelines
  - Termination conditions
  │
Step 6: Technical Setup (1 week)
  Configure USDC receiving wallet
  Verify test transaction
  Add to dashboard cause display
  │
Step 7: Public Announcement
  Co-marketing announcement (Twitter, Discord, blog)
  Partner featured in next impact report
  │
Step 8: Ongoing Relationship
  Monthly check-ins with partnerships lead
  Quarterly impact data submission
  Community AMA participation
```

### 1.4 Reporting Requirements

Partners must provide:

| Report | Frequency | Contents |
|--------|-----------|----------|
| **Impact update** | Monthly | How funds were used, beneficiary numbers, photos/stories |
| **Financial summary** | Quarterly | USDC received, conversion details, expenditure breakdown |
| **Outcome report** | Annually | Measurable outcomes tied to CHA donations, year-over-year comparison |

### 1.5 Partner Removal Criteria

A partner may be removed if:
- Failure to submit required reports for 2 consecutive months
- Financial mismanagement or fraud discovered
- Significant reputational incident
- Violation of partnership agreement terms
- Community governance vote to remove (requires supermajority)

Removal process: written notice, 30-day cure period, governance vote if disputed.

---

## 2. DeFi Protocol Integration Opportunities

### 2.1 Integration Targets

| Protocol Type | Integration Value | Priority | Examples |
|---------------|------------------|----------|----------|
| **DEX Aggregators** | Wider swap access, more transactions = more donations | High | Paraswap, 1inch, Odos |
| **Lending Protocols** | CHA as collateral = utility + holding incentive | High | Aave (Base), Compound, Moonwell |
| **Yield Aggregators** | CHA yield strategies = more TVL | Medium | Beefy, Yearn |
| **Portfolio Trackers** | Visibility, holder awareness | Medium | DeBank, Zapper |
| **Bridge Protocols** | Multi-chain expansion prerequisite | Medium | Across, Stargate, LayerZero |
| **NFT Platforms** | Cause-themed NFTs, burn milestone NFTs | Low | Zora, OpenSea (Base) |
| **Payment Processors** | Accept CHA for purchases, auto-donate | Low | Request Network, Sablier |

### 2.2 Integration Proposal Template

When approaching DeFi protocols, use this structure:

```
Subject: Charity Coin (CHA) Integration Proposal -- [Protocol Name]

1. INTRODUCTION
   - Charity Coin overview (1 paragraph)
   - Key metrics: holders, TVL, daily volume, total donated

2. INTEGRATION PROPOSAL
   - Specific integration requested (e.g., listing, collateral, pool)
   - Technical details (contract addresses, token standard, fee structure)
   - NOTE: CHA has a 5% transfer fee -- document how this interacts
     with the protocol's mechanics

3. MUTUAL BENEFITS
   - For the protocol: new users, positive PR, impact narrative
   - For CHA: utility expansion, holder growth, volume increase

4. TECHNICAL DETAILS
   - Contract address (Base): [address]
   - Token standard: ERC-20 with transfer fee
   - Fee structure: 2.5% charity, 1.5% liquidity, 1.0% operations
   - Audit report: [link]
   - GitHub: [link]

5. CO-MARKETING
   - Joint announcement thread
   - Cross-community AMA
   - Shared content calendar for launch week

6. CONTACT
   - Partnerships lead: [name, email, Telegram]
```

### 2.3 Fee Compatibility Considerations

CHA's 5% transfer fee requires special attention when integrating with DeFi protocols:

| Concern | Mitigation |
|---------|------------|
| Fee-on-transfer breaks some DEX routers | Test thoroughly; many modern routers handle FOT tokens |
| Lending protocols may not support FOT tokens | Propose fee-exempt whitelist for protocol contract addresses (requires governance vote) |
| Yield calculations need to account for fees | Provide clear documentation; work with protocol to display net APY |
| Bridge transfers incur fees on both chains | Consider fee exemptions for bridge contracts (governance decision) |

---

## 3. Cross-Chain Expansion Partners

### 3.1 Target Chains

| Chain | Rationale | Timeline | Bridge Partner |
|-------|-----------|----------|----------------|
| **Optimism** | Large DeFi ecosystem, retroPGF alignment, impact narrative fit | Q2 | Across, LayerZero |
| **Arbitrum** | Highest L2 TVL, large user base | Q2-Q3 | Stargate, LayerZero |
| **Polygon** | Low fees, emerging market penetration, large user base | Q3 | Polygon Bridge, LayerZero |
| **Ethereum Mainnet** | Prestige, institutional access (high gas limits use case) | Q4 | Native bridge |

### 3.2 Cross-Chain Architecture Options

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Native deployment** | Deploy CHA contract on each chain independently | Full fee mechanism on each chain | Fragmented liquidity, complex governance |
| **Bridged token** | Bridge CHA from Base to other chains | Unified supply, simpler | Fee mechanism only on Base, bridge risk |
| **Hybrid** | Native on major chains, bridged on minor | Balanced approach | Most complex to manage |

**Recommendation**: Start with bridged tokens for expansion chains, evaluate native deployment based on volume.

### 3.3 Expansion Partner Requirements

Bridge and cross-chain partners must:
- Have completed security audits
- Support fee-on-transfer tokens (or provide exemption path)
- Offer transparent fee structures
- Provide integration support and documentation
- Be willing to co-market the expansion

---

## 4. Media and Influencer Outreach Plan

### 4.1 Media Targets

#### Tier 1 -- Crypto-Native Media (Priority)

| Outlet | Type | Approach |
|--------|------|----------|
| CoinDesk | News + features | Press release, exclusive data, op-eds |
| The Block | News + research | Data-driven pitches, research partnerships |
| Decrypt | News + education | Story pitches, tutorial partnerships |
| Bankless | Podcast + newsletter | Guest appearance pitch, sponsored content |
| The Defiant | DeFi-focused news | DeFi integration stories, impact angle |

#### Tier 2 -- Impact and ESG Media

| Outlet | Type | Approach |
|--------|------|----------|
| Stanford Social Innovation Review | Academic / impact | Op-ed on blockchain philanthropy |
| Impact Alpha | Impact investing | Investor-angle story pitch |
| GreenBiz | Sustainability | Environment cause spotlight |
| Forbes (Impact section) | Mainstream + impact | Founder profile, impact metrics |

#### Tier 3 -- Mainstream Tech

| Outlet | Type | Approach |
|--------|------|----------|
| TechCrunch | Tech news | Fundraise announcements, milestone stories |
| Wired | Long-form tech | Feature pitch on crypto philanthropy |
| Fast Company | Innovation | "World Changing Ideas" nomination |

### 4.2 Influencer Strategy

#### Influencer Tiers

| Tier | Follower Range | Engagement Rate | Compensation | Use Case |
|------|---------------|-----------------|--------------|----------|
| **Mega** | 500K+ | 1-3% | $5,000-$20,000 per post | Launch announcements, milestone events |
| **Macro** | 100K-500K | 3-5% | $2,000-$5,000 per post | Educational threads, AMAs |
| **Micro** | 10K-100K | 5-10% | $500-$2,000 per post or CHA allocation | Ongoing advocacy, cause-specific content |
| **Nano** | 1K-10K | 8-15% | CHA allocation, community perks | Grassroots, authentic testimonials |

#### Influencer Categories

| Category | Why | Example Accounts |
|----------|-----|-----------------|
| **Crypto Educators** | Explain tokenomics, build credibility | DeFi explainers, "crypto for beginners" accounts |
| **Impact / ESG Advocates** | Bridge to impact-investing audience | Sustainability influencers, ESG fund managers |
| **Base Ecosystem Builders** | Ecosystem alignment, cross-promotion | Base-native project founders, Coinbase-adjacent voices |
| **Philanthropy Leaders** | Credibility with traditional donors | Nonprofit leaders with social presence |
| **DeFi Analysts** | Technical credibility, trader audience | On-chain analysts, DeFi strategists |

#### Influencer Outreach Template

```
Subject: Charity Coin -- Transparent Crypto Philanthropy on Base

Hi [Name],

I'm [Your Name] from Charity Coin, a deflationary ERC-20 token on Base
where every transaction automatically donates 2.5% to community-voted
charitable causes. The donated CHA is burned when converted to USDC,
creating deflationary pressure that rewards holders.

Since launch, we have:
- Donated [amount] USDC to [causes]
- Burned [amount] CHA tokens
- Grown to [number] holders

Your content on [specific topic they cover] aligns with our mission
because [specific reason]. We'd love to explore a collaboration:

Option A: Sponsored educational thread on CHA's mechanics
Option B: Co-hosted Twitter Space on [relevant topic]
Option C: Ambassador partnership with ongoing CHA allocation

Would you be open to a quick call this week?

Best,
[Your Name]
[Links: website, Twitter, docs]
```

### 4.3 Press Kit Contents

Maintain an always-updated press kit at `brand/press-kit/`:

| Asset | Format | Description |
|-------|--------|-------------|
| Brand logos | SVG, PNG (light + dark) | Full logo, icon only, wordmark |
| One-pager | PDF | Single-page project summary with key metrics |
| Fact sheet | PDF | Key stats, tokenomics, team bios, partner list |
| Founder bios | Text + headshots | 100-word bios, professional headshots |
| Screenshot pack | PNG | Dashboard, voting UI, burn tracker, cause pages |
| Boilerplate | Text | 50-word and 150-word project descriptions |
| Brand guidelines | PDF | Colors, typography, logo usage rules |
| Contract addresses | Text | Mainnet and testnet addresses |
| Audit reports | PDF | All completed audit reports |

### 4.4 Outreach Cadence

| Activity | Frequency | Owner |
|----------|-----------|-------|
| Press release (milestones, partnerships) | As needed | Marketing lead |
| Media relationship check-ins | Monthly | Partnerships lead |
| Influencer pipeline review | Bi-weekly | Marketing lead |
| Press kit update | Monthly | Content lead |
| Media monitoring (mentions, sentiment) | Daily | Community manager |

---

## 5. Co-Marketing Templates

### 5.1 Charity Partner Announcement

**Twitter Thread (4 tweets)**:

```
Tweet 1:
We are thrilled to announce [Charity Name] as a Charity Coin
[cause] partner!

[Charity description in 1 sentence]. Every CHA transaction now
helps fund their mission.

Thread below on what this means for our community.

Tweet 2:
[Charity Name] works on [specific programs]. With CHA donations,
they plan to [specific use of funds].

Their track record: [key stat, e.g., "served 50,000 meals in 2024"]

Tweet 3:
How it works:
- 2.5% of every CHA transfer goes to the active cause
- Community votes on which cause receives funds each epoch
- USDC is sent directly to [Charity Name]'s verified wallet
- Everything is on-chain and auditable

Tweet 4:
Join us in welcoming [Charity Name] to the Charity Coin family.

AMA with their team: [date/time]
Learn more: [link]

[Charity's Twitter handle]
```

### 5.2 DeFi Integration Announcement

**Twitter Thread (3 tweets)**:

```
Tweet 1:
CHA is now live on [Protocol Name]!

You can now [specific action: lend, borrow, LP, swap] with $CHA
on [protocol], expanding the utility of impact-driven DeFi.

Every interaction still donates 2.5% to charity.

Tweet 2:
What this means for CHA holders:
- [Benefit 1: e.g., "Earn yield while your transactions donate"]
- [Benefit 2: e.g., "More liquidity depth for smoother swaps"]
- [Benefit 3: e.g., "Access to leveraged CHA positions"]

Tutorial: [link]

Tweet 3:
Huge thanks to the [Protocol] team for the collaboration.

Join our co-AMA this [day]: [link]

[Protocol's Twitter handle] x @CharityCoin
```

### 5.3 Cross-Chain Expansion Announcement

**Twitter Thread (4 tweets)**:

```
Tweet 1:
Charity Coin is expanding to [Chain Name]!

Starting [date], you can hold, trade, and donate with $CHA on
[chain] -- bringing transparent crypto philanthropy to
[chain's user count]+ users.

Tweet 2:
Why [Chain Name]?
- [Reason 1: e.g., "Largest DeFi ecosystem among L2s"]
- [Reason 2: e.g., "Sub-cent transactions for maximum impact"]
- [Reason 3: e.g., "Aligned values with retroactive public goods"]

Tweet 3:
How to bridge:
1. Go to [bridge URL]
2. Connect wallet
3. Select CHA, choose amount
4. Bridge from Base to [Chain]

Full guide: [link]

Tweet 4:
Bridge partner: [Bridge Protocol]
Launch partners on [Chain]: [list]

Same mission. More chains. Bigger impact.
```

### 5.4 Milestone Celebration Post

**Single Tweet / Announcement**:

```
[MILESTONE NUMBER] CHA BURNED.

That's [USDC equivalent] donated to [causes].
That's [specific impact: e.g., "1,000 meals served, 50 wells funded"].
That's a supply that only goes down.

Every transaction. Every burn. Every impact.

Thank you to our [holder count] holders.
This is just the beginning.

[Infographic attachment]
```

---

## 6. Partnership Pipeline Management

### 6.1 Pipeline Stages

| Stage | Description | Success Criteria | Typical Duration |
|-------|-------------|------------------|------------------|
| **Prospect** | Identified potential partner | Meets initial criteria check | -- |
| **Outreach** | First contact made | Response received | 1-2 weeks |
| **Discovery** | Exploratory conversation | Mutual interest confirmed | 1 week |
| **Due Diligence** | Vetting and verification | All criteria verified | 2-3 weeks |
| **Negotiation** | Terms discussion | Agreement on terms | 1-2 weeks |
| **Agreement** | Contract signed | Signed agreement | 1 week |
| **Integration** | Technical and marketing setup | Tested and ready | 1-2 weeks |
| **Live** | Partnership active | Public announcement | -- |
| **Maintenance** | Ongoing relationship | Quarterly review passed | Ongoing |

### 6.2 Tracking

Maintain a partnership tracker with:
- Partner name and category (charity, DeFi, media, influencer)
- Pipeline stage and dates
- Primary contact and communication log
- Key terms and obligations
- Performance metrics (for active partnerships)

Review the pipeline weekly in the partnerships standup. Quarterly partnership health reviews with the full team.

---

## 7. Partnership Principles

1. **Mission alignment first**: No partnership that compromises the charitable mission, regardless of financial upside.
2. **Mutual value**: Every partnership must create clear value for both parties. No one-sided deals.
3. **Transparency**: All partnership terms (except confidential financial details) are shared with the community.
4. **Community consent**: Major partnerships (new causes, large allocations) require governance approval.
5. **Diversity**: Seek geographic, cause-area, and organizational diversity across the partner portfolio.
6. **Long-term over transactional**: Prefer ongoing relationships over one-time promotions.
7. **No pay-for-play governance**: Partners do not receive preferential governance weight or cause allocation outside the normal voting process.
