# Charity Coin

Charity Coin is a deflationary ERC-20 token on Base that channels a portion of every transaction toward verified charitable causes. Each token transfer automatically splits a 5% fee to fund charity donations, deepen liquidity, and sustain operations -- all on-chain and fully transparent.

## Architecture Overview

Charity Coin is built as a monorepo containing smart contracts, a web frontend, and a backend API. The smart contracts handle token logic, fee distribution, and automated USDC conversion. The frontend provides a dashboard for users to track donations, vote on causes, and manage their tokens. The API serves off-chain data, handles indexing, and coordinates charity disbursements.

```
charity-coin/
├── apps/
│   ├── web/              # Next.js frontend (dashboard, voting, analytics)
│   └── api/              # Hono API server (indexing, off-chain coordination)
├── packages/
│   ├── config/           # Shared ESLint, TypeScript, Tailwind configs
│   ├── ui/               # Shared React component library
│   └── types/            # Shared TypeScript type definitions
├── contracts/
│   ├── src/              # Solidity smart contracts
│   ├── test/             # Foundry tests
│   ├── script/           # Deployment and interaction scripts
│   └── lib/              # Foundry dependencies (forge-std, OpenZeppelin)
├── docs/
│   ├── whitepaper/       # Full whitepaper
│   ├── litepaper/        # Condensed litepaper
│   ├── technical/        # Technical specifications
│   ├── user-guides/      # End-user documentation
│   └── legal/            # Legal documents and disclaimers
├── brand/
│   ├── guidelines/       # Brand guidelines
│   ├── assets/           # Logos, icons
│   └── design-tokens/    # Colors, typography, spacing tokens
├── marketing/
│   ├── strategy/         # Go-to-market plans
│   ├── community/        # Community engagement plans
│   └── content/          # Blog posts, social templates
├── governance/           # DAO governance proposals and frameworks
├── project-specs/        # Internal project specifications
└── .github/workflows/    # CI/CD pipelines
```

## Token Economics

Every transfer of Charity Coin incurs a 5% fee, distributed as follows:

| Allocation | Percentage | Purpose |
|------------|------------|---------|
| Charity    | 2.5%       | Donated to the currently active charitable cause |
| Liquidity  | 1.5%       | Added to the Uniswap V3 liquidity pool on Base |
| Operations | 1.0%       | Funds ongoing development and operational costs |

### Deflationary Mechanism

When accumulated charity fees are converted to USDC for donation disbursement, the corresponding Charity Coin tokens are permanently burned. This reduces the total supply over time, creating deflationary pressure that rewards long-term holders.

### Founder Revenue Model

The operations wallet receives its 1.0% share and auto-swaps to USDC via the Uniswap V3 router on Base. This provides a stable revenue stream for the founding team while keeping the mechanism fully on-chain and auditable.

## Tech Stack

- **Blockchain**: Base (Ethereum L2)
- **Smart Contracts**: Solidity, Foundry (forge, cast, anvil)
- **Frontend**: Next.js 14, React, Tailwind CSS, wagmi, viem
- **Backend API**: Hono (TypeScript), PostgreSQL, Redis
- **Testing**: Foundry (Solidity), Vitest (TypeScript)
- **Monorepo**: Turborepo, npm workspaces
- **CI/CD**: GitHub Actions

## Launch Causes

The first five charitable causes supported at launch:

1. **Clean Water Access** -- Funding well construction and water purification in underserved communities.
2. **Childhood Education** -- Providing school supplies, scholarships, and remote learning tools.
3. **Reforestation** -- Planting trees and restoring degraded ecosystems worldwide.
4. **Hunger Relief** -- Supporting food banks and meal programs for families in need.
5. **Medical Aid** -- Funding medical supplies and healthcare access in crisis regions.

## Getting Started

### Prerequisites

- Node.js >= 18
- Foundry (`curl -L https://foundry.paradigm.xyz | bash && foundryup`)
- PostgreSQL
- Redis

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/charity-coin.git
cd charity-coin

# Install dependencies
npm install

# Copy environment variables
cp .env.example .env
# Fill in your .env values

# Build all packages
npm run build

# Run the development servers
npm run dev
```

### Smart Contracts

```bash
cd contracts

# Build contracts
forge build

# Run tests
forge test

# Deploy to Base Sepolia
forge script script/Deploy.s.sol --rpc-url $BASE_SEPOLIA_RPC_URL --broadcast --verify
```

## License

See [LICENSE](./LICENSE) for details.
