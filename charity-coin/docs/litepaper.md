# Charity Coin Litepaper

**Convert Value. Create Impact.**

---

## What is Charity Coin?

Charity Coin (CHA) is a deflationary ERC-20 token on Base that turns every conversion into a charitable donation. When users convert CHA into Cause Tokens, 95% of the CHA is permanently burned and the remaining 5% is split between charity, liquidity, and operations -- all on-chain, all verifiable.

The protocol makes charitable giving transparent, automated, and economically aligned: the more people give, the scarcer CHA becomes, rewarding long-term holders while funding real-world causes.

## How It Works

```
User converts 1,000 CHA to a Cause Token (e.g., chHEALTH)
    |
    +-- 950 CHA burned permanently (95%)
    |
    +-- 50 CHA distributed as fees (5%):
    |     +-- 25 CHA -> Charity wallet (50% of fee)
    |     +-- 15 CHA -> Liquidity pool (30% of fee)
    |     +-- 10 CHA -> Operations as USDC (20% of fee)
    |
    +-- 950 chHEALTH tokens minted to the user
```

1. **Buy CHA** on a DEX on Base.
2. **Choose a cause** from verified charitable organizations (Health, Education, Environment, Water, Hunger).
3. **Convert** CHA to Cause Tokens. The smart contract burns CHA, distributes fees, and mints Cause Tokens in a single transaction.

Cause Tokens serve as permanent, transferable proof of your charitable contribution.

## Tokenomics

| Parameter | Value |
|-----------|-------|
| Max supply | 1,000,000,000 CHA |
| Chain | Base (Ethereum L2) |
| Burn rate | 95% per conversion |
| Total fee | 5% per conversion |
| Fee split | 50% charity / 30% liquidity / 20% operations |

CHA is deflationary by design. Every conversion permanently reduces the total supply. The maximum supply of 1 billion CHA is a hard cap enforced at the contract level; burned tokens can never be re-minted.

## Technical Foundation

- **Smart contracts**: Solidity 0.8.24 on Base, built with OpenZeppelin v5. Contracts include CharityCoin (ERC-20), CauseToken (EIP-1167 clones), ConversionEngine, FeeRouter, and a Governor + Timelock for DAO governance.
- **Security**: ReentrancyGuard on all stateful operations, Pausable emergency stops, AccessControl for role-based permissions, SafeERC20 for all token transfers.
- **Gas efficiency**: EIP-1167 minimal proxies reduce Cause Token deployment costs by ~90%. Compiler optimizations via `via_ir` pipeline.
- **Frontend**: Next.js 14, React, Tailwind CSS, wagmi + RainbowKit for wallet connectivity.
- **Backend**: Hono API server (TypeScript), PostgreSQL, Redis caching, on-chain event indexer.

## Governance

Charity Coin is governed by a DAO via the CharityCoinGovernor contract. CHA holders can propose and vote on protocol changes including fee rates, fee distribution, new causes, and contract upgrades.

| Parameter | Value |
|-----------|-------|
| Voting delay | 1 day |
| Voting period | 5 days |
| Proposal threshold | 100,000 CHA |
| Quorum | 4% of supply |
| Timelock | 2-day delay |

## Launch Causes

| Cause | Token | Focus |
|-------|-------|-------|
| Global Health Initiative | chHEALTH | Healthcare access and medical research |
| Education For All | chEDU | Schools, scholarships, and learning tools |
| Environmental Protection | chENV | Reforestation and ecosystem conservation |
| Clean Water Access | chWATER | Well construction and water purification |
| End Hunger | chHUNGER | Food banks and sustainable agriculture |

New causes are added through governance proposals.

## Roadmap

- **Phase 1 -- Launch** (2026 H1): Core contracts on Base, web dashboard, initial causes and liquidity.
- **Phase 2 -- Partnerships** (2026 H2): Charity partner integrations, impact reporting, fiat on-ramps.
- **Phase 3 -- Cross-Chain** (2027 H1): Multi-chain deployment (Arbitrum, Optimism, Polygon), bridging.
- **Phase 4 -- Impact NFTs** (2027 H2+): Milestone NFTs, impact verification oracles, third-party SDK.

## Disclaimer

This litepaper is for informational purposes only. CHA and Cause Tokens are utility tokens and do not represent equity, ownership, or claims on revenue. Token values may fluctuate and could decrease to zero. Smart contracts carry inherent risk. Users are responsible for compliance with applicable laws in their jurisdiction.

---

*Learn more in the full [Whitepaper](./whitepaper.md) and [Technical Architecture](./technical-architecture.md).*
