# Charity Coin -- Technical Architecture

**Version 1.0 | March 2026**

---

## Table of Contents

1. [Smart Contract Architecture](#1-smart-contract-architecture)
2. [Contract Interactions and Data Flow](#2-contract-interactions-and-data-flow)
3. [Security Considerations](#3-security-considerations)
4. [Gas Optimization Strategies](#4-gas-optimization-strategies)
5. [API Architecture](#5-api-architecture)
6. [Frontend Architecture](#6-frontend-architecture)

---

## 1. Smart Contract Architecture

### 1.1 System Diagram

```
+------------------------------------------------------------------+
|                      Charity Coin Protocol                        |
+------------------------------------------------------------------+
|                                                                    |
|  +---------------------+       +-----------------------------+    |
|  |    CharityCoin       |       |    CharityCoinGovernor      |    |
|  |    (CHA Token)       |       |    (DAO Voting)             |    |
|  |---------------------|       |-----------------------------|    |
|  | ERC20 + Burnable    |       | GovernorSettings            |    |
|  | ERC20Permit         |       | GovernorCountingSimple      |    |
|  | AccessControl       |       | GovernorVotes               |    |
|  | Pausable            |       | GovernorVotesQuorumFraction |    |
|  | MAX_SUPPLY: 1B      |       | GovernorTimelockControl     |    |
|  +---------------------+       +-------------|---------------+    |
|           |                                   |                    |
|           |                                   v                    |
|           |                    +-----------------------------+    |
|           |                    |   CharityCoinTimelock        |    |
|           |                    |   (2-day delay)              |    |
|           |                    |-----------------------------|    |
|           |                    | minDelay: 172800s            |    |
|           |                    | Proposer: Governor           |    |
|           |                    | Executor: anyone             |    |
|           |                    +-----------------------------+    |
|           |                                                        |
|           v                                                        |
|  +---------------------+       +-----------------------------+    |
|  |  ConversionEngine   |<----->|    CauseTokenFactory        |    |
|  |---------------------|       |-----------------------------|    |
|  | convert()           |       | EIP-1167 Clones.clone()     |    |
|  | 5% fee, 95% burn    |       | createCause()               |    |
|  | ReentrancyGuard     |       | CAUSE_CREATOR_ROLE          |    |
|  | Pausable            |       | isCause() registry          |    |
|  | AccessControl       |       +-------------|---------------+    |
|  +---------|----------+                      |                    |
|            |                                  v                    |
|            v                   +-----------------------------+    |
|  +---------------------+      |    CauseToken (Clone N)      |    |
|  |     FeeRouter       |      |-----------------------------|    |
|  |---------------------|      | ERC20 (no cap)               |    |
|  | 50% -> Charity      |      | initialize() (one-time)      |    |
|  | 30% -> Liquidity    |      | MINTER_ROLE: Engine          |    |
|  | 20% -> Ops (USDC)   |      | causeName, charityWallet     |    |
|  | ReentrancyGuard     |      +-----------------------------+    |
|  | Uniswap V3 swap     |                                         |
|  +---------------------+      +-----------------------------+    |
|            |                   |    CauseToken (Clone N+1)    |    |
|            v                   |-----------------------------|    |
|  +---------------------+      | (same structure, diff data)  |    |
|  | Uniswap V3 Router   |      +-----------------------------+    |
|  | (CHA -> USDC swap)  |                                         |
|  +---------------------+      +-----------------------------+    |
|                                |    CauseToken (Clone N+2)    |    |
|                                |-----------------------------|    |
|                                | ...                          |    |
|                                +-----------------------------+    |
+------------------------------------------------------------------+
```

### 1.2 Contract Summary

| Contract | Source | Purpose |
|----------|--------|---------|
| CharityCoin | `src/token/CharityCoin.sol` | Primary ERC-20 token. 1B hard cap, burnable, pausable, EIP-2612 permit. |
| CauseToken | `src/token/CauseToken.sol` | Per-cause ERC-20. Deployed as EIP-1167 clone. No supply cap. Stores cause metadata. |
| CauseTokenFactory | `src/factory/CauseTokenFactory.sol` | Deploys CauseToken clones. Maintains cause registry. Role-gated creation. |
| ConversionEngine | `src/engine/ConversionEngine.sol` | Core conversion logic. Burns CHA, routes fees, mints Cause Tokens. |
| FeeRouter | `src/fees/FeeRouter.sol` | Splits and distributes fees to charity, liquidity, and operations. |
| CharityCoinGovernor | `src/governance/CharityCoinGovernor.sol` | OpenZeppelin v5 Governor. DAO voting for protocol changes. |
| CharityCoinTimelock | `src/governance/CharityCoinTimelock.sol` | TimelockController. 2-day delay on executed proposals. |

### 1.3 Role Architecture

```
DEFAULT_ADMIN_ROLE (deployer, then timelock)
    |
    +-- CharityCoin
    |     +-- MINTER_ROLE:  deployer (initial mint)
    |     +-- PAUSER_ROLE:  deployer / timelock
    |
    +-- ConversionEngine
    |     +-- DEFAULT_ADMIN_ROLE: deployer / timelock
    |
    +-- FeeRouter
    |     +-- DEFAULT_ADMIN_ROLE: deployer / timelock
    |
    +-- CauseTokenFactory
    |     +-- CAUSE_CREATOR_ROLE: deployer / timelock
    |
    +-- CauseToken (each clone)
          +-- DEFAULT_ADMIN_ROLE: ConversionEngine
          +-- MINTER_ROLE:        ConversionEngine
```

---

## 2. Contract Interactions and Data Flow

### 2.1 Conversion Flow

The following sequence describes a complete CHA-to-CauseToken conversion:

```
User                ConversionEngine      CharityCoin       FeeRouter         CauseToken
  |                       |                    |                |                  |
  |-- approve(engine) --->|                    |                |                  |
  |                       |                    |                |                  |
  |-- convert(cause, amt) |                    |                |                  |
  |                       |                    |                |                  |
  |                       |-- isCause(cause) --|--------------->|  (via Factory)   |
  |                       |<---- true ---------|                |                  |
  |                       |                    |                |                  |
  |                       |  fee = amt * 5%    |                |                  |
  |                       |  burn = amt - fee  |                |                  |
  |                       |                    |                |                  |
  |                       |-- transferFrom --->|                |                  |
  |                       |   (user -> engine) |                |                  |
  |                       |                    |                |                  |
  |                       |-- burn(burnAmt) -->|                |                  |
  |                       |                    | (tokens gone)  |                  |
  |                       |                    |                |                  |
  |                       |-- transfer(fee) -->|-- to router -->|                  |
  |                       |-- distributeFees() |                |                  |
  |                       |                    |                |-- 50% charity    |
  |                       |                    |                |-- 30% liquidity  |
  |                       |                    |                |-- 20% swap->USDC |
  |                       |                    |                |                  |
  |                       |-- mint(user, burn) |                |                  |
  |                       |                    |                |          mint -->|
  |                       |                    |                |                  |
  |<-- Converted event ---|                    |                |                  |
```

### 2.2 Fee Distribution Detail

When the FeeRouter receives CHA from the ConversionEngine:

1. **Charity portion (50%)**: CHA is transferred directly to the `charityWallet` address stored on the CauseToken contract. The router calls `CauseToken(causeToken).charityWallet()` to look up the destination.

2. **Liquidity portion (30%)**: CHA is transferred to the `liquidityManager` address. This address holds CHA intended for manual Uniswap V3 LP provisioning.

3. **Operations portion (20%)**: CHA is swapped to USDC via Uniswap V3 `exactInputSingle`, with the USDC sent directly to the `operationsWallet`. The swap uses a configurable pool fee tier (default: 0.3%) and slippage protection.

### 2.3 Cause Creation Flow

```
Governance (Timelock)     CauseTokenFactory     CauseToken Impl     New Clone
       |                         |                     |                |
       |-- createCause() ------->|                     |                |
       |                         |-- Clones.clone() -->|                |
       |                         |                     |-- deploy ----->|
       |                         |                                      |
       |                         |-- initialize() -------------------->|
       |                         |   (name, symbol, cause metadata,    |
       |                         |    charityWallet, causeId, minter)  |
       |                         |                                      |
       |                         |  causes[causeId] = clone addr        |
       |                         |  _isCause[clone] = true              |
       |                         |                                      |
       |<-- CauseCreated event --|                                      |
```

### 2.4 Governance Flow

```
CHA Holder          Governor              Timelock            Target Contract
    |                   |                     |                      |
    |-- propose() ----->|                     |                      |
    |                   |  (1-day delay)      |                      |
    |                   |                     |                      |
    |-- castVote() ---->|                     |                      |
    |   (5-day period)  |                     |                      |
    |                   |                     |                      |
    |-- queue() ------->|-- schedule() ------>|                      |
    |                   |                     |  (2-day delay)       |
    |                   |                     |                      |
    |-- execute() ----->|-- execute() ------->|--- call() ---------> |
    |                   |                     |                      |
```

---

## 3. Security Considerations

### 3.1 ReentrancyGuard

Both the ConversionEngine and FeeRouter inherit from OpenZeppelin's `ReentrancyGuard`. The `nonReentrant` modifier is applied to:

- `ConversionEngine.convert()` -- Prevents reentrant calls during the burn-transfer-mint sequence.
- `FeeRouter.distributeFees()` -- Prevents reentrant calls during fee distribution and the Uniswap swap.

This is critical because the conversion flow involves multiple external calls (token transfers, burns, mints, and swaps) that could be exploited by a malicious token or callback.

### 3.2 Pausable

Emergency pause functionality is implemented on:

- **CharityCoin**: The `_update` hook enforces `whenNotPaused` on all transfers, mints, and burns. Controlled by `PAUSER_ROLE`.
- **ConversionEngine**: The `convert()` function is gated by `whenNotPaused`. Controlled by `DEFAULT_ADMIN_ROLE`.

Pause capability allows the team (and later, governance) to halt operations in the event of a discovered vulnerability or exploit.

### 3.3 AccessControl

Role-based access control is used throughout the protocol instead of single-owner patterns:

| Role | Contract | Granted To | Capability |
|------|----------|-----------|------------|
| `DEFAULT_ADMIN_ROLE` | CharityCoin | Deployer / Timelock | Manage all roles |
| `MINTER_ROLE` | CharityCoin | Deployer | Mint CHA (up to cap) |
| `PAUSER_ROLE` | CharityCoin | Deployer / Timelock | Pause/unpause transfers |
| `DEFAULT_ADMIN_ROLE` | ConversionEngine | Deployer / Timelock | Set fee rate, pause, update contracts |
| `DEFAULT_ADMIN_ROLE` | FeeRouter | Deployer / Timelock | Set fee shares, slippage, wallets |
| `CAUSE_CREATOR_ROLE` | CauseTokenFactory | Deployer / Timelock | Create new causes |
| `MINTER_ROLE` | CauseToken (each) | ConversionEngine | Mint Cause Tokens |

### 3.4 SafeERC20

All token transfers in the ConversionEngine and FeeRouter use OpenZeppelin's `SafeERC20` library (`safeTransfer`, `safeTransferFrom`, `safeIncreaseAllowance`). This guards against:

- Tokens that return `false` instead of reverting on failure.
- Tokens that do not return a boolean value at all (non-standard ERC-20).

### 3.5 Zero-Address Checks

All constructors and initialization functions validate that no critical address parameter is the zero address. This prevents accidental misconfiguration that could lock funds or break the protocol.

### 3.6 Supply Cap Enforcement

The `CharityCoin.mint()` function checks `totalSupply() + amount > MAX_SUPPLY` before every mint and reverts with `MaxSupplyExceeded()` if exceeded. The cap is defined as an immutable constant (`1_000_000_000 * 10 ** 18`), ensuring it cannot be modified after deployment.

### 3.7 Clone Initialization Guard

The CauseToken implementation contract marks itself as `_initialized = true` in its constructor, preventing anyone from calling `initialize()` on the implementation itself. Each clone can only be initialized once; subsequent calls revert with `AlreadyInitialized()`.

### 3.8 Slippage Protection

The FeeRouter's `_swapToStablecoin()` function uses Uniswap V3's `exactInputSingle` with a configurable `maxSlippageBps` (default 1%, maximum 5%). In the current MVP, `amountOutMinimum` is set to 0 with plans to integrate a TWAP oracle in a future version for production-grade slippage protection.

---

## 4. Gas Optimization Strategies

### 4.1 EIP-1167 Minimal Proxy Clones

The CauseTokenFactory uses OpenZeppelin's `Clones.clone()` to deploy new CauseToken instances. Each clone is a 45-byte proxy contract that delegates all calls to a shared implementation. Compared to deploying full contract bytecode:

| Metric | Full Deployment | EIP-1167 Clone |
|--------|----------------|----------------|
| Deployment gas | ~1,500,000+ gas | ~100,000 gas |
| Bytecode size | Full contract | 45 bytes |
| Gas savings | -- | ~90% |

This is especially impactful for a protocol that may deploy dozens or hundreds of cause tokens over its lifetime.

### 4.2 via_ir Compiler Pipeline

The `foundry.toml` configuration enables the `via_ir` (Yul intermediate representation) compiler pipeline:

```toml
optimizer = true
optimizer_runs = 200
via_ir = true
```

The `via_ir` pipeline applies additional optimization passes that the legacy pipeline cannot perform, including:

- Cross-function stack optimization
- Improved memory layout
- More aggressive inlining
- Better constant folding

Trade-off: compilation times increase significantly, but runtime gas costs decrease.

### 4.3 Solidity 0.8.24 + Cancun EVM

The contracts target Solidity 0.8.24 with the `cancun` EVM version, enabling access to the latest EVM opcodes and gas schedule optimizations available on Base.

### 4.4 Remainder-Based Fee Calculation

Both the ConversionEngine and FeeRouter use a "remainder to ops" pattern to avoid rounding dust:

```solidity
uint256 charityAmount = (feeAmount * charityShareBps) / BPS_DENOMINATOR;
uint256 liquidityAmount = (feeAmount * liquidityShareBps) / BPS_DENOMINATOR;
uint256 opsAmount = feeAmount - charityAmount - liquidityAmount; // Remainder
```

This avoids an additional multiplication and division, and ensures that all fee tokens are accounted for without rounding errors leaving dust in the contract.

### 4.5 Unchecked Increments

OpenZeppelin v5 contracts use unchecked increments in loops where overflow is impossible (e.g., the `getAllCauses()` function iterates over a bounded array), saving gas on overflow checks.

---

## 5. API Architecture

### 5.1 Stack Overview

```
+-------------------------------------------------+
|              Hono API Server                     |
|  (TypeScript, @hono/node-server)                |
|-------------------------------------------------|
|                                                  |
|  Middleware:    CORS, Logger, Cache, AdminAuth   |
|                                                  |
|  Routes:                                         |
|    /api/causes/*        Cause data + analytics  |
|    /api/analytics/*     Platform-wide metrics   |
|    /api/user/*          User portfolios         |
|    /api/admin/*         Admin operations        |
|    /api/health          Health check            |
|                                                  |
+-------------------------------------------------+
         |                    |
         v                    v
+----------------+   +----------------+
|   PostgreSQL   |   |     Redis      |
|   (Drizzle ORM)|   |   (Cache)      |
|                |   |                |
| Tables:        |   | TTL-based      |
|  - causes      |   | response cache |
|  - conversions |   | (15-60s)       |
|  - users       |   |                |
+----------------+   +----------------+
         ^
         |
+----------------+
|  On-Chain      |
|  Event Indexer |
|  (Background)  |
|                |
| Watches:       |
| - Converted    |
| - CauseCreated |
| - FeesDistrib. |
+----------------+
```

### 5.2 Key Components

**Hono Framework**: A lightweight, high-performance web framework for TypeScript. Routes are organized into separate modules (`causes.ts`, `analytics.ts`, `user.ts`, `admin.ts`) and mounted on the main app.

**Drizzle ORM**: Type-safe SQL query builder for PostgreSQL. Used for all database operations with schema-defined tables (`causes`, `conversions`, `users`).

**Redis Cache**: Response caching middleware with configurable TTL per route group:
- Causes routes: 30-second TTL
- Analytics routes: 60-second TTL
- User routes: 15-second TTL
- Admin routes: no cache

**On-Chain Indexer**: A background service (`startIndexer()`) that watches for on-chain events (Converted, CauseCreated, FeesDistributed) and syncs them into PostgreSQL. Started automatically when the API server boots.

**Admin Authentication**: Admin routes are protected by API key authentication via the `adminAuth` middleware.

### 5.3 Data Models

**causes**: Stores cause metadata including `causeId`, `tokenAddress`, `name`, `symbol`, `description`, `charityWallet`, `isActive`, and timestamps.

**conversions**: Stores individual conversion events including `userAddress`, `causeTokenAddress`, `chaAmount`, `causeTokenAmount`, `feeAmount`, `txHash`, `blockNumber`, and `timestamp`.

**users**: Stores aggregated user statistics including `address`, `totalChaConverted`, `totalCausesSupported`, `firstConversionAt`, and `lastConversionAt`.

---

## 6. Frontend Architecture

### 6.1 Stack Overview

```
+----------------------------------------------------+
|              Next.js 14 Application                 |
|  (App Router, React Server Components)              |
|----------------------------------------------------|
|                                                      |
|  Pages:                                              |
|    /              Home (hero, stats, featured)      |
|    /causes        Browse and filter causes          |
|    /causes/:id    Cause detail + leaderboard        |
|    /convert       Conversion interface              |
|    /portfolio     User dashboard                    |
|    /governance    DAO proposals + voting             |
|                                                      |
|  UI Layer:                                           |
|    Tailwind CSS + shared component library          |
|    lucide-react icons                                |
|                                                      |
|  Web3 Layer:                                         |
|    wagmi (React hooks for Ethereum)                 |
|    viem (TypeScript Ethereum library)               |
|    RainbowKit (wallet connection UI)                |
|                                                      |
+----------------------------------------------------+
         |                    |
         v                    v
+----------------+   +---------------------+
|  Charity Coin  |   |    Base Network      |
|  API Server    |   |    (via RPC)         |
|  (/api/*)      |   |                     |
+----------------+   | Contract calls via  |
                      | wagmi useReadContract|
                      | useWriteContract    |
                      +---------------------+
```

### 6.2 Key Design Decisions

**Server Components**: Next.js 14 App Router enables React Server Components for pages that do not require client-side interactivity (e.g., the home page hero, static content). Interactive components (wallet connection, conversion forms) use the `"use client"` directive.

**wagmi + viem**: wagmi provides React hooks for reading and writing to smart contracts, managing wallet state, and watching for on-chain events. viem is the underlying TypeScript Ethereum library that handles ABI encoding, transaction formatting, and RPC communication.

**RainbowKit**: Provides a polished wallet connection modal supporting MetaMask, Coinbase Wallet, WalletConnect, and other popular wallets. Handles chain switching to Base automatically.

**Shared Component Library**: The `packages/ui/` workspace contains reusable React components (Button, Card, etc.) shared between the web app and any future frontends. Built with Tailwind CSS and exported as a workspace package.

### 6.3 Data Fetching Strategy

- **On-chain data** (balances, allowances, conversion previews): Fetched directly from the blockchain via wagmi hooks (`useReadContract`, `useBalance`). These provide real-time data without depending on the API server.
- **Off-chain data** (analytics, leaderboards, history): Fetched from the Charity Coin API server. This data is pre-aggregated and cached, making it faster to serve than raw on-chain queries.
- **Hybrid approach**: The frontend combines both sources. For example, the conversion page reads the current fee rate from the ConversionEngine contract on-chain while loading historical conversion data from the API.

---

*For API endpoint documentation, see [API Reference](./api-reference.md). For deployment instructions, see [Deployment Guide](./deployment-guide.md).*
