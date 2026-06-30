# Antelope + WAX Blockchain Agent Team

A complete team of specialized AI agents for Antelope/WAX blockchain development, grounded in official WAX dev docs, FuckYea, VeRT, Context7 (CDT, WharfKit, antelope-dev-book, reference contracts), and the official `waxteam/waxdev` Docker workflow.

---

## 📁 Directory Structure

All agents live flat in this `antelope/` directory. They split into a chain-agnostic
**core/engineering** group (works on EOS/Vaulta, WAX, Telos, UX) and a **WAX-specific** group.

```
antelope/
│  # ── Core / Engineering (chain-agnostic + WAX-compatible) ──────────────
├── antelope-smart-contract-architect.md
├── antelope-cdt-developer.md
├── antelope-security-auditor.md
├── antelope-token-defi-specialist.md
├── antelope-node-operator-devops.md
├── antelope-backend-api-developer.md
├── antelope-reference-contracts-specialist.md
├── antelope-testing-qa-engineer.md
├── antelope-nft-gaming-specialist.md        ← non-WAX chains: SimpleAssets, commit-reveal
├── antelope-game-economy-designer.md        ← faucet/sink + tokenomics modeling
├── antelope-project-shepherd.md
│
│  # ── WAX-specific ─────────────────────────────────────────────────────
├── wax-local-testnet-docker.md              ← Stage 2: local Docker chain environment
├── wax-frontend-wharfkit-developer.md       ← the single WharfKit frontend agent (WAX-first, multi-chain capable)
├── wax-atomicassets-nft-specialist.md
├── wax-game-developer.md                     ← farming/staking/blending + WAX RNG flow
├── wax-rng-oracle-specialist.md             ← orng.wax deep dive + RNG v3.x capacity
└── wax-onboarding-resource-provider.md      ← WCW onboarding + CPU/NET resource provider
```

---

## 🔧 Engineering Team (11 Agents)

| Agent | Role | Key Tools |
|---|---|---|
| **Smart Contract Architect** | C++ contract design, multi-index tables, auth patterns | CDT, eosio.hpp |
| **CDT Developer** | Compilation, WASM optimization, ABI, build tooling | cdt-cpp, CMake, FuckYea build |
| **Security Auditor** | Vulns, fake notifications, auth bypass, RAM drain | Manual review + adversarial tests |
| **Token & DeFi Specialist** | eosio.token, staking, AMM, vesting | C++, lazy reward math |
| **Node Operator & DevOps** | Production nodeos config, BP infra, snapshots, monitoring | Docker Compose, Prometheus |
| **Backend API Developer** | Server-side Antelope, tx relay, table watchers | Node.js, WharfKit |
| **Reference Contracts Specialist** | System contracts, msig, permissions, resources | cleos, eosio.system |
| **Testing & QA Engineer** | Full 4-stage test pipeline (VeRT → local → testnet → mainnet) | FuckYea, VeRT, cleos |
| **NFT & Gaming Specialist** | Non-WAX NFTs: SimpleAssets, custom contracts, commit-reveal RNG | C++, EOS/Telos/UX |
| **Game Economy & Tokenomics Designer** | Faucet/sink modeling, emission schedules, NFT supply/rarity, anti-bot economy | Simulation, sink design |
| **Project Shepherd** | Architecture, sprint planning, launch checklists | ADRs, multi-sig runbooks |

---

## 🟠 WAX Team (6 Agents)

| Agent | Role | Key Tools |
|---|---|---|
| **WAX Local Testnet & Docker** | Stage 2 local chain: nodeos startup, keosd, accounts, deploy, reset | `waxteam/waxdev`, cleos, keosd |
| **WAX Frontend & WharfKit Developer** | The team's single WharfKit frontend (WAX-first, multi-chain capable): React dApps, MyCloudWallet first, SessionKit/ContractKit, session management | WharfKit, WalletPluginCloudWallet |
| **WAX AtomicAssets NFT Specialist** | Collections, schemas, templates, minting, mutable data | atomicassets contract, AtomicAssets API |
| **WAX Game Developer** | Farming, NFT staking, WAX RNG flow, blending, quests, economy | orng.wax, atomicassets.hpp, ReactJS |
| **WAX RNG Oracle Specialist** | orng.wax deep dive, unbiased extraction, callback security, RNG v3.x staking/capacity | orng.wax, Signidice/RSA, Hyperion |
| **WAX Onboarding & Resource-Provider Specialist** | WCW onboarding, CPU/NET/RAM for casual gamers, fee delegation | WCW, Resource Provider plugin, PowerUp |

---

## 🧪 The 4-Stage Testing Pipeline

Every WAX contract goes through all four stages. No skipping.

```
Stage 1: VeRT Unit Tests
──────────────────────────────────────────────────────────
Tool:    npx fuckyea test --build
Network: NONE (in-process WASM emulator)
Speed:   Seconds
Owner:   Testing & QA Engineer
Tests:   Logic, auth, table state, boundaries
         Every require_auth → expectToThrow

Stage 2: Local Docker nodeos Integration Tests
──────────────────────────────────────────────────────────
Tool:    waxteam/waxdev container → nodeos + keosd + cleos
Network: Local (http://127.0.0.1:8888)
Speed:   Minutes
Owner:   WAX Local Testnet & Docker agent
Tests:   Account creation, deploy, inline actions,
         eosio.code permission, multi-contract flows
         ⚠️  WAX RNG and AtomicAssets NOT available here

Stage 3: WAX Public Testnet (waxsweden.org)
──────────────────────────────────────────────────────────
Tool:    cleos -u https://testnet.waxsweden.org
Network: WAX sw/eden testnet
Speed:   Hours
Owner:   Testing & QA Engineer
Tests:   WAX RNG (orng.wax), AtomicAssets, WCW wallet,
         real resource model, ecosystem contracts

Stage 4: WAX Mainnet
──────────────────────────────────────────────────────────
Network: WAX mainnet (wax.greymass.com)
Gate:    Stages 1–3 ✅ + security audit ✅ + multi-sig ✅
```

---

## 🗺️ Scenarios

### WAX NFT Farming Game (with RNG pack opening)
```
Game Economy & Tokenomics   → faucet/sink model + emission schedule BEFORE contracts
WAX Game Developer          → farming loop, staking, blending, RNG request/callback wiring
WAX RNG Oracle Specialist   → orng.wax integration, unbiased rolls, callback security, capacity
WAX AtomicAssets Specialist → collection/schema/template/mint
Smart Contract Architect    → table design, authorization model
CDT Developer               → compile with FuckYea build inside waxteam/waxdev
WAX Local Testnet & Docker  → Stage 2: local chain, account setup, contract deploy
Security Auditor            → auth checks, fake on_notify, RNG callback review
Testing & QA Engineer       → VeRT → local nodeos → WAX testnet (RNG) → mainnet
WAX Frontend Developer      → React + WCW + Anchor
WAX Onboarding & Resources  → WCW onboarding, Resource Provider so zero-CPU players can play
Project Shepherd            → sprint planning, launch checklist
```

### New WAX Contract (Generic)
```
Smart Contract Architect    → design
CDT Developer               → compile
WAX Local Testnet & Docker  → Stage 2: deploy and test locally
Testing & QA Engineer       → all 4 stages
```

### Non-WAX Antelope NFT Game (EOS, Telos, UX)
```
Antelope NFT & Gaming Specialist → SimpleAssets or custom NFT + commit-reveal RNG
Smart Contract Architect         → table design
CDT Developer                    → compile + fuckyea test
Testing & QA Engineer            → VeRT → local nodeos → Jungle4 testnet
WAX Frontend & WharfKit Developer → multi-chain capable: SessionKit + Anchor wallet (swap chain id/RPC for EOS/Vaulta/Telos/UX)
```

### Production Node / Block Producer
```
Node Operator & DevOps      → production nodeos config, BP signing keys, monitoring
Reference Contracts         → BP registration, voting, resource management
Project Shepherd            → launch runbook, multi-sig upgrade procedures
```

---

## 🔑 Universal Rules

1. **VeRT first** — `fuckyea test` before touching any network
2. **Local nodeos second** — `waxteam/waxdev` before any public network
3. **WAX RNG needs testnet+** — `orng.wax` not available in VeRT or local nodeos
4. **8-decimal WAX precision** — `1.00000000 WAX` always
5. **MyCloudWallet first** — primary wallet for WAX users (formerly "WAX Cloud Wallet"; WharfKit plugin is still `@wharfkit/wallet-plugin-cloudwallet` / `WalletPluginCloudWallet`)
6. **eosio dev key = LOCAL ONLY** — the same key for every developer on earth; never ship it
7. **Add-code for inline actions** — `cleos set account permission <account> active --add-code`
8. **AtomicAssets schema is permanent** — fields cannot be deleted after creation
9. **Multi-sig on all mainnet upgrades** — no single-key production changes

---

## 🌐 WAX Network Reference

| | Mainnet | Testnet | Local |
|---|---|---|---|
| API | `https://wax.greymass.com` | `https://testnet.waxsweden.org` | `http://127.0.0.1:8888` |
| Chain ID | `1064487b3cd1a897ce03ae5b6a865651747e2e152090f99c1d19d44e01aea5a4` | `f16b1833c747c43682f4386fca9cbb327929334a762755ebec17f6f23c9b8a12` | — |
| Explorer | https://waxblock.io | https://local.bloks.io/?nodeUrl=testnet.waxsweden.org | — |
| Testnet accounts | — | https://waxsweden.org/testnet/ | `cleos create account eosio ...` |
| AtomicAssets API | `https://wax.api.atomicassets.io` | `https://test.wax.api.atomicassets.io` | ❌ deploy locally |
| WAX RNG | ✅ `orng.wax` | ✅ `orng.wax` | ❌ not available |
| Public API list | https://validate.eosnation.io/wax/reports/endpoints.html | — | — |
