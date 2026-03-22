# Charity Coin (CHA)

**Convert Value. Create Impact.**

Charity Coin is a deflationary ERC-20 token on Base. Users convert CHA into Cause Tokens tied to charitable causes. On every conversion, 95% of CHA is permanently burned and Cause Tokens are minted 1:1. A 5% fee is split: 2.5% to charity, 1.5% to liquidity, and 1.0% auto-swapped to USDC for operations.

## Quick Start

```bash
# Clone and enter the project
git clone <repo-url>
cd charity-coin

# Automated setup (installs deps, starts DB/Redis, seeds data)
./scripts/setup.sh

# Start everything
make dev
```

This will start:
- **Web app** at http://localhost:3000
- **API server** at http://localhost:3001
- **PostgreSQL** at localhost:5432
- **Redis** at localhost:6379

### Prerequisites

- [Node.js](https://nodejs.org) >= 18
- [Docker](https://docs.docker.com/get-docker/) (for PostgreSQL and Redis)
- [Foundry](https://book.getfoundry.sh/getting-started/installation) (optional, for smart contract development)

```bash
# Install Foundry (optional)
curl -L https://foundry.paradigm.xyz | bash && foundryup
```

## Manual Setup

If you prefer to set things up step by step:

```bash
# 1. Install dependencies
npm install

# 2. Copy environment files
cp .env.example .env
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env.local

# 3. Start PostgreSQL and Redis
docker compose up -d postgres redis

# 4. Push database schema
cd apps/api && npx drizzle-kit push && cd ../..

# 5. Seed sample data
cd apps/api && npx tsx src/db/seed.ts && cd ../..

# 6. Start development servers
make dev
```

## Development Commands

```bash
make help              # Show all available commands
make dev               # Start everything (infra + API + web)
make dev-infra         # Start only PostgreSQL + Redis
make dev-stop          # Stop infrastructure
make test              # Run all tests (contracts + lint)
make test-contracts    # Run smart contract tests only
make build             # Build all packages
make db-push           # Push schema changes to DB
make db-seed           # Seed database with sample data
make clean             # Clean build artifacts
```

### Running Individual Services

```bash
# API server (port 3001)
cd apps/api && npm run dev

# Web frontend (port 3000)
cd apps/web && npm run dev

# Smart contracts
cd contracts && forge build && forge test
```

## Architecture

```
charity-coin/
├── apps/
│   ├── web/           # Next.js 14 frontend (React, Tailwind, wagmi, RainbowKit)
│   └── api/           # Hono API server (Drizzle ORM, PostgreSQL, Redis)
├── contracts/         # Foundry/Solidity smart contracts
│   ├── src/
│   │   ├── token/     # CharityCoin (ERC20Votes) + CauseToken
│   │   ├── engine/    # ConversionEngine (burn + mint)
│   │   ├── fees/      # FeeRouter (charity/liquidity/ops split)
│   │   ├── factory/   # CauseTokenFactory (EIP-1167 clones)
│   │   └── governance/# Governor + Timelock (DAO)
│   └── test/          # Unit, integration, fuzz, invariant tests
├── scripts/           # Setup and utility scripts
├── docs/              # Whitepaper, litepaper, technical docs
├── brand/             # Brand guidelines, design tokens
├── marketing/         # GTM strategy, content calendar
├── governance/        # DAO framework and proposal templates
└── legal/             # Terms of service, privacy policy
```

## Token Economics

| Flow | Amount | Destination |
|------|--------|-------------|
| Burn | 95% | Permanently destroyed (deflationary) |
| Charity | 2.5% | Cause's charity wallet (as CHA) |
| Liquidity | 1.5% | Liquidity manager (for Uniswap V3 LP) |
| Operations | 1.0% | Auto-swapped CHA to USDC via Uniswap |

### Conversion Flow

```
User converts 1000 CHA → HEALTH Cause Token:
  ├── 950 CHA burned permanently
  ├── 950 HEALTH tokens minted to user
  └── 50 CHA fee split:
      ├── 25 CHA → charity wallet
      ├── 15 CHA → liquidity manager
      └── 10 CHA → swapped to USDC → ops wallet
```

## Smart Contracts

| Contract | Purpose |
|----------|---------|
| `CharityCoin.sol` | ERC-20 with ERC20Votes, burnable, pausable, 1B max supply |
| `CauseToken.sol` | Lightweight per-cause ERC-20 (EIP-1167 clones) |
| `CauseTokenFactory.sol` | Deploys minimal proxy cause tokens |
| `ConversionEngine.sol` | CHA burn + cause token mint + fee routing |
| `FeeRouter.sol` | 3-way fee split with Uniswap V3 auto-swap |
| `CharityCoinGovernor.sol` | OpenZeppelin Governor (4% quorum, 5-day voting) |
| `CharityCoinTimelock.sol` | 2-day delay before execution |

### Running Contract Tests

```bash
cd contracts

forge test              # Run all tests
forge test -vvv         # Verbose output
forge test --gas-report # With gas report
forge coverage          # Coverage report
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check (DB + Redis) |
| GET | `/api/causes` | List all causes |
| GET | `/api/causes/:id` | Cause detail with stats |
| GET | `/api/causes/:id/leaderboard` | Top converters for a cause |
| GET | `/api/analytics/overview` | Platform-wide analytics |
| GET | `/api/user/:address/portfolio` | User holdings and history |
| POST | `/api/admin/causes` | Create cause (admin only) |

## Frontend Pages

| Route | Description |
|-------|-------------|
| `/` | Landing page with hero, stats, featured causes |
| `/causes` | Browse all charitable causes |
| `/causes/[slug]` | Cause detail with conversion widget |
| `/convert` | Main conversion interface |
| `/portfolio` | User dashboard (balances, history, impact) |
| `/governance` | DAO proposals and voting |
| `/admin` | Cause management (admin only) |

## Environment Variables

### API (`apps/api/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | API server port | `3001` |
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | Required |
| `ADMIN_API_KEY` | Admin authentication key | Required |
| `BASE_RPC_URL` | Base RPC endpoint | `https://mainnet.base.org` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:3000` |

### Web (`apps/web/.env.local`)

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID` | WalletConnect project ID | Optional |
| `NEXT_PUBLIC_API_URL` | API base URL | `http://localhost:3001/api` |
| `NEXT_PUBLIC_BASE_RPC_URL` | Base RPC for frontend | `https://mainnet.base.org` |

## Launch Causes

1. **Global Health (HEALTH)** -- Medical research, healthcare access, disease prevention
2. **Education (EDU)** -- Scholarships, learning resources, school supplies
3. **Environment (ENV)** -- Ecosystem protection, climate action, sustainability
4. **Clean Water (WATER)** -- Well construction, water purification, sanitation
5. **Zero Hunger (HUNGER)** -- Food aid, sustainable agriculture, nutrition programs

## Tech Stack

- **Chain**: Base (Coinbase L2)
- **Contracts**: Solidity 0.8.24, Foundry, OpenZeppelin v5
- **Frontend**: Next.js 14, React 18, Tailwind CSS, wagmi v2, RainbowKit v2
- **Backend**: Hono 4, Drizzle ORM, PostgreSQL 16, Redis 7
- **Monorepo**: Turborepo, npm workspaces
- **CI/CD**: GitHub Actions

## License

See [LICENSE](./LICENSE) for details.
