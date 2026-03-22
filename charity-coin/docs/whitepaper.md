# Charity Coin Whitepaper

**Version 1.0 | March 2026**

---

## Table of Contents

1. [Abstract](#1-abstract)
2. [Problem Statement](#2-problem-statement)
3. [Solution: The Charity Coin Protocol](#3-solution-the-charity-coin-protocol)
4. [Tokenomics](#4-tokenomics)
5. [Technical Architecture](#5-technical-architecture)
6. [Governance](#6-governance)
7. [Launch Causes](#7-launch-causes)
8. [Roadmap](#8-roadmap)
9. [Team](#9-team)
10. [Legal Disclaimer](#10-legal-disclaimer)

---

## 1. Abstract

Charity Coin (CHA) is a deflationary ERC-20 token deployed on Base (Ethereum L2) that transforms charitable giving into an on-chain, transparent, and self-sustaining mechanism. Every conversion of CHA into a cause-specific token permanently burns the majority of the CHA involved while directing a fee toward verified charitable organizations, protocol liquidity, and ongoing operations. The result is a protocol where charitable impact and token value reinforcement are structurally aligned: the more people give, the scarcer CHA becomes, and the more value accrues to the remaining supply.

Charity Coin removes the opacity, overhead, and intermediary friction that plague traditional charitable giving. By encoding donation logic directly into smart contracts on a public blockchain, every dollar raised, every token burned, and every fee distributed is fully auditable by anyone, in real time.

---

## 2. Problem Statement

### 2.1 Inefficiency in Traditional Charitable Giving

The global charitable sector moves hundreds of billions of dollars annually, yet it remains burdened by systemic inefficiencies:

- **Opacity**: Donors rarely have visibility into how their contributions are allocated. Reporting cycles are slow, and financial disclosures are often incomplete or difficult to interpret.
- **Administrative overhead**: Traditional nonprofits spend a significant portion of their budgets on fundraising, administration, and compliance rather than direct program delivery. Industry averages suggest that 20-35% of funds never reach the intended cause.
- **Intermediary friction**: Payment processors, fiscal sponsors, banking partners, and currency conversion services each extract fees before funds reach their destination.
- **Trust deficits**: High-profile fraud cases and mismanagement scandals erode public trust in charitable organizations, discouraging participation.
- **Lack of donor engagement**: Once a donation is made, donors are largely disconnected from its impact. There is no persistent, verifiable record of their contribution tied to measurable outcomes.

### 2.2 The Opportunity

Blockchain technology provides the primitives to solve each of these problems: immutable ledgers for transparency, smart contracts for automated and trustless fund distribution, and tokenization for persistent proof of contribution. What has been missing is a protocol that combines these primitives into a cohesive, user-friendly system with built-in economic incentives for participation.

---

## 3. Solution: The Charity Coin Protocol

Charity Coin introduces a **deflationary conversion mechanism** that aligns charitable giving with sound token economics. The core loop operates as follows:

1. **Acquire CHA**: Users purchase Charity Coin (CHA) tokens on a decentralized exchange (DEX) on Base.
2. **Choose a cause**: Users select from a curated set of verified charitable causes, each represented by a dedicated Cause Token (e.g., chHEALTH, chEDU, chENV).
3. **Convert**: Users convert their CHA into Cause Tokens via the ConversionEngine smart contract. During conversion:
   - **95% of the CHA is permanently burned**, reducing total supply forever.
   - **5% is collected as a fee** and distributed automatically by the FeeRouter contract.
4. **Cause Tokens are minted**: The user receives Cause Tokens 1:1 with the amount of CHA burned, serving as a permanent, transferable proof of their charitable contribution.

### 3.1 Key Properties

- **Deflationary**: Every conversion permanently removes CHA from circulation. There is no mechanism to re-mint burned tokens.
- **Transparent**: All fund flows, burns, and distributions are executed on-chain and verifiable by anyone.
- **Automated**: Fee splitting and distribution are handled entirely by smart contracts with no manual intervention.
- **Non-custodial**: Users retain control of their assets at all times. The protocol never holds user funds beyond the duration of a single transaction.
- **Governance-controlled**: Key protocol parameters (fee rates, fee distribution shares, new causes) are managed by a DAO with a timelock for safety.

---

## 4. Tokenomics

### 4.1 Supply Parameters

| Parameter | Value |
|-----------|-------|
| Token name | CharityCoin |
| Ticker | CHA |
| Standard | ERC-20 (with ERC-20Permit / EIP-2612) |
| Chain | Base (Ethereum L2) |
| Maximum supply | 1,000,000,000 (1 billion) CHA |
| Decimals | 18 |
| Mintable | Yes, via MINTER_ROLE (role-gated) |
| Burnable | Yes, via ERC20Burnable |

The 1 billion maximum supply is a hard cap enforced at the smart contract level. The `mint` function reverts with `MaxSupplyExceeded()` if any mint operation would push total supply beyond this cap.

### 4.2 Burn Mechanics

When a user converts CHA to a Cause Token:

- The ConversionEngine calculates a 5% total fee (500 basis points, configurable up to a maximum of 10%).
- The remaining 95% of the CHA is permanently burned via the `burn()` function inherited from OpenZeppelin's `ERC20Burnable`.
- Burned tokens are sent to the zero address and can never be recovered or re-minted.
- The cumulative burn total is tracked on-chain via the `totalChaBurned` state variable in the ConversionEngine.

**Example**: A user converts 1,000 CHA to chHEALTH.
- 950 CHA is burned permanently.
- 50 CHA is sent to the FeeRouter for distribution.
- 950 chHEALTH tokens are minted to the user.

### 4.3 Fee Distribution

The 5% conversion fee is split by the FeeRouter contract according to configurable basis-point shares:

| Recipient | Default Share | Purpose |
|-----------|---------------|---------|
| Charity | 50% (5,000 bps) | CHA sent directly to the cause's designated charity wallet |
| Liquidity | 30% (3,000 bps) | CHA sent to the liquidity manager for Uniswap V3 LP provisioning |
| Operations | 20% (2,000 bps) | CHA auto-swapped to USDC via Uniswap V3 and sent to the operations wallet |

In absolute terms relative to the original conversion amount:

| Recipient | Effective Rate |
|-----------|---------------|
| Burn (permanent) | 95.0% |
| Charity wallet | 2.5% |
| Liquidity pool | 1.5% |
| Operations (as USDC) | 1.0% |

Fee shares are adjustable via governance. The total of all three shares must always equal 10,000 basis points (100%). The operations portion is automatically swapped from CHA to USDC through the Uniswap V3 SwapRouter, providing the founding team with cost-basis-stable revenue.

### 4.4 Deflationary Dynamics

Because 95% of every conversion is burned, the CHA supply is monotonically decreasing over time. This creates several positive dynamics:

- **Scarcity premium**: As supply decreases, all else being equal, each remaining CHA token represents a larger share of the total ecosystem.
- **Holder alignment**: Long-term holders benefit from the deflationary pressure created by active community participation in charitable causes.
- **Virtuous cycle**: As the token appreciates, each conversion carries more real-world value for the charity, incentivizing further participation.

### 4.5 Cause Tokens

Cause Tokens are uncapped ERC-20 tokens minted 1:1 with the CHA burned during conversion. They serve as:

- **Proof of impact**: A persistent, on-chain record of a user's charitable contribution.
- **Community identity**: Holders of a specific Cause Token form a community around that cause.
- **Governance signal**: Cause Token holdings may be used in future governance mechanisms to weight cause prioritization.

Each Cause Token stores metadata including the cause name, description, charity wallet address, and a unique `causeId`.

---

## 5. Technical Architecture

### 5.1 Chain Selection: Base L2

Charity Coin deploys on Base, Coinbase's Ethereum L2 built on the OP Stack. This choice is driven by:

- **Low transaction costs**: Sub-cent gas fees make small conversions economically viable, lowering the barrier to charitable participation.
- **Ethereum security**: Base inherits Ethereum's security guarantees via optimistic rollup proofs.
- **Ecosystem access**: Native integration with Coinbase infrastructure, USDC, and Uniswap V3 deployments on Base.
- **EVM compatibility**: Full compatibility with Solidity, OpenZeppelin, and the broader Ethereum tooling ecosystem.

### 5.2 Smart Contract Architecture

The protocol consists of six core contracts:

**CharityCoin (CHA)** -- The primary ERC-20 token. Features a hard-capped 1B supply, role-based minting and pausing, EIP-2612 permit for gasless approvals, and OpenZeppelin v5 `_update` hook for pausable behavior.

**CauseToken** -- A lightweight ERC-20 deployed as an EIP-1167 minimal proxy clone. Each cause gets its own CauseToken instance that stores cause metadata and designates the ConversionEngine as its sole minter.

**CauseTokenFactory** -- Deploys new CauseToken instances using the EIP-1167 clone pattern. Only addresses with `CAUSE_CREATOR_ROLE` (typically the governance timelock) can create new causes. The factory maintains a registry of all causes and provides lookup and enumeration functions.

**ConversionEngine** -- The core business logic contract. Accepts CHA from users, calculates fees, burns the non-fee portion, forwards fees to the FeeRouter, and mints Cause Tokens to the user. Protected by `ReentrancyGuard` and `Pausable`.

**FeeRouter** -- Receives CHA fees from the ConversionEngine and distributes them to three recipients: the charity wallet (as CHA), the liquidity manager (as CHA), and the operations wallet (auto-swapped to USDC via Uniswap V3).

**CharityCoinGovernor + CharityCoinTimelock** -- An OpenZeppelin v5 Governor with a 2-day timelock. All protocol parameter changes flow through governance proposals.

### 5.3 EIP-1167 Minimal Proxy Clones

The CauseTokenFactory uses the EIP-1167 minimal proxy standard to deploy new Cause Tokens. Instead of deploying full contract bytecode for each cause, the factory clones a single implementation contract. Each clone is a 45-byte proxy that delegates all calls to the shared implementation. This reduces deployment gas by approximately 90% compared to full deployments.

The implementation contract's constructor marks itself as initialized (`_initialized = true`) to prevent direct use. Each clone is initialized exactly once via the `initialize()` function, which sets the ERC-20 metadata, cause metadata, and minter role.

### 5.4 Compiler Optimizations

The protocol uses Solidity 0.8.24 compiled with the `via_ir` pipeline and 200 optimizer runs. The `via_ir` flag enables the Yul-based intermediate representation optimizer, which produces more gas-efficient bytecode at the cost of longer compilation times. The EVM version target is `cancun`.

### 5.5 Off-Chain Infrastructure

**API Server**: A Hono-based TypeScript API server provides off-chain data indexing, analytics aggregation, and administrative functions. It uses Drizzle ORM for PostgreSQL database access and Redis for response caching. An on-chain event indexer runs as a background process to sync blockchain events into the database.

**Frontend**: A Next.js 14 application with React, Tailwind CSS, wagmi (for wallet connectivity), and RainbowKit (for wallet UI). The frontend provides a dashboard for viewing causes, initiating conversions, tracking personal impact, and participating in governance.

---

## 6. Governance

### 6.1 DAO Structure

Charity Coin is governed by a DAO implemented via the CharityCoinGovernor contract. CHA token holders can propose, vote on, and execute protocol changes through an on-chain governance process.

### 6.2 Governance Parameters

| Parameter | Value |
|-----------|-------|
| Voting delay | 1 day (~7,200 blocks at 12s/block on Base) |
| Voting period | 5 days (~36,000 blocks) |
| Proposal threshold | 100,000 CHA |
| Quorum | 4% of total supply |
| Timelock delay | 2 days (172,800 seconds) |
| Voting mechanism | Simple counting (For / Against / Abstain) |

### 6.3 Governance Scope

The following protocol parameters are managed through governance:

- **Fee rate**: The total conversion fee (default 5%, maximum 10%).
- **Fee distribution shares**: The percentage split between charity, liquidity, and operations.
- **New causes**: Creation of new charitable causes via the CauseTokenFactory.
- **Wallet updates**: Changes to the operations wallet, liquidity manager, or cause charity wallets.
- **Contract upgrades**: Updating the FeeRouter or CauseTokenFactory addresses on the ConversionEngine.
- **Emergency actions**: Pausing and unpausing the ConversionEngine or CharityCoin token.

### 6.4 Proposal Lifecycle

1. **Proposal**: A CHA holder with at least 100,000 CHA creates a proposal specifying target contracts, calldata, and a description.
2. **Voting delay**: A 1-day waiting period allows the community to review and discuss the proposal.
3. **Voting period**: CHA holders vote For, Against, or Abstain over a 5-day window. Voting power is based on CHA balance at the snapshot block.
4. **Queueing**: If the proposal passes (majority For, 4% quorum met), it is queued in the timelock.
5. **Timelock delay**: A 2-day delay provides a safety window for the community to react before execution.
6. **Execution**: After the timelock delay, anyone can execute the proposal.

---

## 7. Launch Causes

Charity Coin launches with five charitable causes, each represented by a dedicated Cause Token:

### 7.1 Global Health Initiative (chHEALTH)

Supporting healthcare access and medical research worldwide. Funds are directed toward medical supplies, healthcare infrastructure, and crisis-region medical aid.

### 7.2 Education For All (chEDU)

Funding educational programs and scholarships globally. This cause supports school supplies, remote learning tools, teacher training, and scholarship programs for underserved communities.

### 7.3 Environmental Protection (chENV)

Fighting climate change and protecting natural ecosystems. Funds support reforestation projects, ecosystem restoration, and conservation initiatives worldwide.

### 7.4 Clean Water Access (chWATER)

Providing clean drinking water to underserved communities. This cause funds well construction, water purification systems, and sanitation infrastructure.

### 7.5 End Hunger (chHUNGER)

Combating food insecurity and supporting sustainable agriculture. Funds are directed toward food banks, meal programs, agricultural training, and sustainable farming initiatives.

Each cause has a designated charity wallet that receives the charity share of conversion fees. New causes can be added through the governance process.

---

## 8. Roadmap

### Phase 1: Launch (Q1-Q2 2026)

- Deploy core smart contracts on Base mainnet.
- Launch web application with conversion dashboard.
- Deploy the five initial charitable causes.
- Establish initial USDC/CHA liquidity pool on Uniswap V3.
- Launch API server with indexing and analytics.
- Begin community building and initial marketing.

### Phase 2: Partnerships (Q3-Q4 2026)

- Partner with established charitable organizations for cause verification and fund disbursement.
- Integrate with additional DEXs and aggregators for CHA liquidity.
- Launch cause-specific impact reporting dashboards.
- Introduce referral and ambassador programs.
- Onboard additional causes through governance proposals.
- Integrate fiat on-ramps for non-crypto-native donors.

### Phase 3: Cross-Chain Expansion (Q1-Q2 2027)

- Deploy Charity Coin on additional EVM chains (Arbitrum, Optimism, Polygon).
- Implement cross-chain bridging for CHA and Cause Tokens.
- Launch multi-chain analytics and unified dashboard.
- Explore interoperability with non-EVM chains.

### Phase 4: Impact NFTs and Beyond (Q3 2027+)

- Introduce Impact NFTs: soulbound or transferable NFTs minted to users who reach conversion milestones.
- Launch impact verification oracles that bring real-world outcomes on-chain.
- Explore integration with decentralized identity (DID) solutions for donor profiles.
- Develop SDK and API for third-party integrations.
- Investigate institutional giving and corporate social responsibility (CSR) partnerships.

---

## 9. Team

Charity Coin is developed by a team of blockchain engineers, product designers, and nonprofit professionals committed to using technology for social good. The founding team brings experience across smart contract development, DeFi protocol design, frontend engineering, and charitable program management.

The project is designed to progressively decentralize. Initial administrative roles (DEFAULT_ADMIN_ROLE) will be transferred to the governance timelock as the DAO matures, ensuring that the community ultimately controls all protocol parameters.

---

## 10. Legal Disclaimer

This whitepaper is provided for informational purposes only and does not constitute financial advice, investment advice, legal advice, or a solicitation to purchase any token or cryptocurrency. Charity Coin (CHA) and all associated Cause Tokens are utility tokens designed to facilitate charitable giving and do not represent equity, ownership, or any claim on revenue or profits.

**No guarantee of value**: The value of CHA and Cause Tokens may fluctuate and could decrease to zero. Past performance is not indicative of future results.

**Regulatory uncertainty**: The regulatory landscape for digital assets varies by jurisdiction and is subject to change. Users are responsible for understanding and complying with the laws and regulations applicable in their jurisdiction.

**Smart contract risk**: While the protocol's smart contracts are developed using industry-standard libraries (OpenZeppelin v5) and best practices, no software is free from bugs. Users interact with the protocol at their own risk.

**No fiduciary obligation**: The Charity Coin team and DAO do not have a fiduciary obligation to token holders. Governance participants act in their own capacity.

**Charitable distributions**: While the protocol automates fee distribution to designated charity wallets, the Charity Coin protocol does not control how recipient organizations use the funds. Users should conduct their own due diligence on supported causes.

**Forward-looking statements**: This whitepaper contains forward-looking statements regarding the project's roadmap, features, and partnerships. These statements are based on current expectations and are subject to change without notice.

By interacting with the Charity Coin protocol, users acknowledge and accept the risks described herein.

---

*Charity Coin -- Convert Value. Create Impact.*
