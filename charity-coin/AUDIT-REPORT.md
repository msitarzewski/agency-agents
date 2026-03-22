# Charity Coin Platform -- Comprehensive Audit Report

**Date:** 2026-03-22
**Scope:** Full-stack audit covering smart contracts, backend API, frontend, database, security, architecture, UX, brand, UI design, and legal compliance.
**Auditors:** 11 specialist AI agents (Backend Architect, Database Optimizer, Solidity Auditor, Blockchain Security Auditor, Frontend Developer, Security Engineer, Software Architect, Brand Guardian, UI Designer, UX Researcher, Legal Compliance Advisor)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Critical Findings -- Must Fix Before Launch](#2-critical-findings)
3. [Smart Contract Security](#3-smart-contract-security)
4. [Backend API & Database](#4-backend-api--database)
5. [Frontend & UX](#5-frontend--ux)
6. [Architecture & Code Quality](#6-architecture--code-quality)
7. [Brand & Design System](#7-brand--design-system)
8. [Legal & Compliance](#8-legal--compliance)
9. [Prioritized Remediation Roadmap](#9-prioritized-remediation-roadmap)

---

## 1. Executive Summary

The Charity Coin platform is a well-structured monorepo with a compelling vision: a deflationary ERC-20 token on Base where conversions burn CHA and fund charitable causes. The technical foundation is sound -- OpenZeppelin contracts, Hono API, Next.js frontend, Drizzle ORM, and Foundry tooling.

However, the audit identified **5 critical security vulnerabilities**, **12 high-priority issues**, and **50+ medium/low findings** across all layers. The platform is **not production-ready** in its current state. The most urgent issues are:

1. **Smart contract fund theft vectors** (FeeRouter access control, zero slippage protection)
2. **Governance system is non-functional** (CharityCoin missing ERC20Votes)
3. **Deployment script is broken** (address(0) passed to constructor that rejects it)
4. **No KYC/AML program** and **no charitable solicitation registration**
5. **Securities law risk** from investment-return language in whitepaper

**Overall Readiness: 35/100** -- Significant work required before any production deployment.

---

## 2. Critical Findings

### CRIT-1: FeeRouter.distributeFees() Has No Access Control -- Fund Theft

**File:** `contracts/src/fees/FeeRouter.sol:119`

`distributeFees` is callable by anyone. An attacker can call it with a malicious `causeToken` address whose `charityWallet()` returns the attacker's address, stealing any CHA balance held by the FeeRouter.

**Fix:** Add `DISTRIBUTOR_ROLE` restricted to ConversionEngine only:
```solidity
bytes32 public constant DISTRIBUTOR_ROLE = keccak256("DISTRIBUTOR_ROLE");
function distributeFees(address causeToken, uint256 feeAmount)
    external nonReentrant onlyRole(DISTRIBUTOR_ROLE) { ... }
```

### CRIT-2: Zero Slippage Protection in Uniswap Swap -- Sandwich Attack

**File:** `contracts/src/fees/FeeRouter.sol:205`

`amountOutMinimum` is hardcoded to `0` and `sqrtPriceLimitX96` is `0`. The `maxSlippageBps` storage variable exists but is never used. Every conversion's fee swap is vulnerable to MEV sandwich attacks, allowing attackers to extract 100% of the operations fee value.

**Fix:** Integrate a TWAP oracle or at minimum use the existing `maxSlippageBps`:
```solidity
uint256 expectedOut = _getExpectedOutput(chaAmount);
uint256 amountOutMinimum = (expectedOut * (BPS_DENOMINATOR - maxSlippageBps)) / BPS_DENOMINATOR;
```

### CRIT-3: CharityCoin Missing ERC20Votes -- Governance Non-Functional

**File:** `contracts/src/token/CharityCoin.sol`

The Governor constructor requires `IVotes(address(chaToken))`, but CharityCoin does not extend `ERC20Votes`. `getPastVotes()` and `getPastTotalSupply()` will revert, making the entire governance system inoperable.

**Fix:** Add `ERC20Votes` to CharityCoin's inheritance chain and override `_update()` and `nonces()`.

### CRIT-4: Deployment Script Is Broken

**File:** `contracts/script/Deploy.s.sol:77`

Constructor has `require(factory_ != address(0))`, but Deploy.s.sol passes `address(0)` as factory. Deployment will revert. Additionally, `proposers[0] = address(0)` grants the timelock's PROPOSER_ROLE to address(0), meaning **anyone can propose** operations on the timelock, and this is never revoked.

**Fix:** Restructure deployment order (deploy factory first with temp minter, then engine, then update factory minter). Revoke address(0) proposer role after granting it to the governor.

### CRIT-5: Admin Roles Never Transferred to Governance

**File:** `contracts/script/Deploy.s.sol`

The deployer retains `DEFAULT_ADMIN_ROLE` on all contracts (CharityCoin, CauseTokenFactory, ConversionEngine, FeeRouter, TimelockController) and never renounces. This means the deployer can:
- Mint unlimited CHA
- Pause/unpause all transfers
- Change fee rates and wallets
- Replace factory and fee router with malicious contracts
- Bypass the timelock entirely

**Fix:** Transfer all admin roles to timelock and renounce deployer's admin at end of deployment script.

---

## 3. Smart Contract Security

### High Severity

| ID | Finding | File |
|----|---------|------|
| H-1 | ISwapRouter interface missing `deadline` field -- transactions can be held indefinitely | `contracts/src/interfaces/ISwapRouter.sol` |
| H-2 | CauseToken has no supply cap -- unbounded minting if engine compromised | `contracts/src/token/CauseToken.sol:136` |
| H-3 | ConversionEngine admin can swap factory/feeRouter to malicious contracts | `contracts/src/engine/ConversionEngine.sol:169-179` |
| H-4 | No minimum conversion amount -- 1 wei produces 0 fee, bypassing fee mechanism | `contracts/src/engine/ConversionEngine.sol:95` |

### Medium Severity

| ID | Finding | File |
|----|---------|------|
| M-1 | Missing events on admin state changes (setFeeRouter, setFactory, setMinter, setLiquidityManager, setPoolFee) | Multiple contracts |
| M-2 | CauseToken clone gives DEFAULT_ADMIN_ROLE to minter (ConversionEngine) | `CauseToken.sol:110` |
| M-3 | getAllCauses() unbounded loop may exceed gas limit | `CauseTokenFactory.sol:112` |
| M-4 | safeIncreaseAllowance accumulates stale allowance on SwapRouter | `FeeRouter.sol:198` |
| M-5 | No poolFee validation (Uniswap only supports 100/500/3000/10000) | `FeeRouter.sol:186` |
| M-6 | FeeRouter doesn't validate causeToken is a real cause via factory | `FeeRouter.sol:119` |
| M-7 | String require() instead of custom errors (gas waste, inconsistency) | `ConversionEngine.sol:78-81` |

### Test Coverage Gaps

- No fuzz tests on any function
- No invariant tests
- No governance tests (Governor, Timelock)
- No reentrancy attack scenarios
- No edge case tests (1 wei conversion, MAX_SUPPLY boundary, zero fee)
- FeeRouter tests don't validate access control (because none exists)

---

## 4. Backend API & Database

### Security Issues

| Priority | Finding | File |
|----------|---------|------|
| P0 | CORS fully open (`cors()` with no arguments) | `apps/api/src/index.ts:16` |
| P0 | No rate limiting on any route | All routes |
| P0 | Admin auth uses timing-vulnerable string comparison | `apps/api/src/middleware/auth.ts:20` |
| P0 | No input validation on address/ID route params | `routes/user.ts`, `routes/causes.ts` |
| P1 | No request ID tracking for debugging | Global |
| P1 | No request body size limit | Global |
| P1 | Error responses lack consistent structure | Global |

### Database Issues

| Priority | Finding | Impact |
|----------|---------|--------|
| P0 | `LOWER()` on indexed columns defeats all indexes | Every analytics/cause query does full-table scan |
| P0 | N+1 query in cause listing (N separate `getCauseStats()` calls) | `routes/causes.ts:25-38` |
| P0 | N+1 query in user history enrichment | `routes/user.ts:118-135` |
| P1 | Indexer state stored in memory variable (lost on restart) | `services/indexer.ts:27` |
| P1 | FeesDistributed events logged to console only, not persisted | `services/indexer.ts:168` |
| P1 | Missing composite indexes (cause_token+timestamp, user+timestamp) | `db/schema.ts` |
| P2 | Redis `KEYS` command blocks entire keyspace | `middleware/cache.ts:70` |
| P2 | No graceful shutdown handler | `index.ts` |

### Missing Tables

- `indexer_state` (persistent checkpoint)
- `fee_distributions` (audit trail)
- `notifications` (user alerts)
- `audit_logs` (admin action tracking)

---

## 5. Frontend & UX

### Ship Blockers

| ID | Finding | File |
|----|---------|------|
| F-1 | `useConversion` doesn't await approval before converting (will fail) | `hooks/useConversion.ts:74` |
| F-2 | No wrong-network detection or switch prompt | Global |
| F-3 | No global error boundary | Global |
| F-4 | MAX button hardcodes "1000" instead of actual balance | `conversion-widget.tsx:123` |
| F-5 | No balance display on conversion widget | `conversion-widget.tsx` |
| F-6 | No Open Graph / Twitter Card meta tags | `app/layout.tsx` |
| F-7 | Dead footer links (Documentation, Whitepaper, Audits all link to `#`) | `layout/footer.tsx:12-17` |
| F-8 | `Math.random()` in admin page causes hydration mismatch | `admin/page.tsx:185-188` |

### Accessibility Issues

| ID | Finding | File |
|----|---------|------|
| A-1 | ImpactMeter progress bar has no ARIA attributes | `ui/impact-meter.tsx:33` |
| A-2 | Form inputs lack `id`/`htmlFor` associations | Multiple files |
| A-3 | Color contrast fails WCAG AA (`text-gray-400` on white = 2.9:1) | Multiple files |
| A-4 | No skip-to-content link for keyboard users | `app/layout.tsx` |
| A-5 | Mobile menu lacks `aria-expanded` | `layout/header.tsx:56` |
| A-6 | No `prefers-reduced-motion` handling for animations | `globals.css` |

### UX Concerns

- No wallet setup guidance for crypto newcomers
- Conversion flow has no step indicator (approve -> convert is confusing)
- Cause selector is a bare `<select>` with no visual preview
- No input validation feedback (disabled button with no explanation)
- Stats bar uses hardcoded placeholder data, not real on-chain reads
- No social sharing after successful conversion
- No impact equivalencies (e.g., "~19 medical kits funded")
- Governance voting buttons have no onClick handlers (entirely static)
- Admin page has no access control and form buttons do nothing

---

## 6. Architecture & Code Quality

### Critical Architecture Issues

1. **Event signature mismatch:** The indexer's `CONVERTED_EVENT` has 5 params, the Solidity contract has 6, and the frontend ABI has 5 with different names. **The indexer will fail to decode events from the deployed contract.**

2. **Package manager conflict:** `pnpm-workspace.yaml` exists but `package.json` declares `"packageManager": "npm@10.0.0"` and `Makefile` runs `npm ci`.

3. **Empty shared packages:** `packages/config/`, `packages/types/`, `packages/ui/` contain no files. Zero code sharing between frontend and API.

4. **Frontend doesn't call the API at all.** No fetch calls, no API client, no `NEXT_PUBLIC_API_URL`. The frontend reads directly from blockchain with placeholder data.

5. **Indexer runs in-process with the API server.** If the API crashes, indexing stops. If indexing hangs, API responsiveness suffers.

### Missing Infrastructure

- No API versioning (routes at `/api/` with no version prefix)
- No structured logging (all `console.log` with string concatenation)
- No health check depth (returns `{ status: "ok" }` without checking DB/Redis/RPC)
- No security headers on Next.js (no CSP, X-Frame-Options, HSTS)

---

## 7. Brand & Design System

### Brand Violations

| Issue | Location | Fix |
|-------|----------|-----|
| "$" prefix on token symbols (violates "use CHA not $CHA") | `cause-card.tsx`, `conversion-widget.tsx`, `causes/[slug]` | Remove `$` prefix |
| "Buy CHA" uses purchase/investment language | `page.tsx:27,67` | Change to "Get CHA" |
| "increasing scarcity and value for holders" = financial advice | `page.tsx:133-134` | Rewrite to remove value language |
| "making remaining supply more valuable" = financial advice | `page.tsx:212` | Change to "scarcer" |
| Network mismatch: press kit says "Ethereum", frontend says "Base" | `brand/press-kit.md` vs `app/layout.tsx` | Update press kit |
| Step 3 uses red colors (reserved for Health cause) | `page.tsx:93-94` | Use amber (secondary) |
| Raw Tailwind colors bypass design token system | Multiple pages | Use `bg-primary-*` etc. |

### Design System Gaps

- **Component library: 3/10** -- Only 4 UI primitives exist. Missing: Modal, Toast, Tooltip, Input, Select, Skeleton, Tabs, Pagination, Badge, StatCard, EmptyState
- **Dark mode: 1/10** -- CSS variables defined but never consumed; all components hardcoded to light mode
- **Data visualization: 1/10** -- Only a basic progress bar; no charts, sparklines, or live feeds
- **Form components: 2/10** -- Raw HTML everywhere; no reusable input component
- **Design token usage: 4/10** -- Colors mostly aligned but typography, shadows, spacing, animation tokens unused

### Missing Brand Assets

- No favicon, OG image, or logo files exist in the repository
- No email templates
- No one-pager PDF

---

## 8. Legal & Compliance

### CRITICAL Risks

| Area | Issue |
|------|-------|
| **Securities Law** | Whitepaper language about "scarcity premium," "value accrues to remaining supply," and "virtuous cycle" creates material Howey test risk despite utility token disclaimers |
| **Charitable Solicitation** | No state/federal registration. ~40 US states require registration before soliciting charitable contributions |
| **KYC/AML** | No KYC/AML program documented. No wallet screening against OFAC SDN list. No transaction monitoring |
| **Tax Documentation** | No guidance that CHA-to-CauseToken conversions are likely taxable events. No cost basis tracking |
| **DAO Legal Wrapper** | No legal entity for the DAO. Governance participants may face unlimited personal liability |

### HIGH Risks

| Area | Issue |
|------|-------|
| **Money Transmission** | FeeRouter's CHA-to-USDC swap may trigger MSB registration with FinCEN |
| **Privacy (CCPA)** | Privacy policy missing CCPA-specific provisions (opt-out, authorized agents) |
| **Legal Documents** | All three documents (ToS, Privacy Policy, Risk Disclosure) have unfilled placeholder fields throughout |
| **Charity Transparency** | No vetting process documented for charity wallet recipients. No donation receipts. No impact reporting requirements |

### Required Before Launch

1. Obtain formal securities law opinion on CHA token classification
2. Remove/rewrite all investment-return language from whitepaper and frontend
3. Establish legal entity structure (operating entity + potential nonprofit)
4. Register for charitable solicitation in applicable states
5. Implement OFAC wallet screening
6. Complete all placeholder fields in legal documents
7. Create dedicated tax information documentation
8. Establish DAO legal wrapper

---

## 9. Prioritized Remediation Roadmap

### Phase 0: Security Blockers (Week 1-2)

These must be fixed before any deployment, including testnet:

- [ ] Fix FeeRouter access control (CRIT-1)
- [ ] Add slippage protection to Uniswap swap (CRIT-2)
- [ ] Add ERC20Votes to CharityCoin (CRIT-3)
- [ ] Fix deployment script (CRIT-4)
- [ ] Transfer admin roles to timelock (CRIT-5)
- [ ] Add ISwapRouter deadline field (H-1)
- [ ] Fix timing-safe admin auth comparison
- [ ] Lock down CORS to known origins
- [ ] Add rate limiting

### Phase 1: Functional Correctness (Week 2-3)

- [ ] Fix event signature mismatch between indexer, frontend, and contracts
- [ ] Fix useConversion to await approval before converting
- [ ] Add minimum conversion amount to contract
- [ ] Fix deployment script address(0) proposer revocation
- [ ] Remove LOWER() from all SQL queries
- [ ] Fix N+1 queries (cause listing, user history)
- [ ] Add missing events on admin state changes
- [ ] Persist indexer checkpoint to database
- [ ] Validate address/ID route parameters

### Phase 2: Production Readiness (Week 3-5)

- [ ] Add global error boundary and per-route error.tsx files
- [ ] Add wrong-network detection and switch prompt
- [ ] Wire MAX button to actual wallet balance
- [ ] Add Open Graph / Twitter Card meta tags
- [ ] Fix dead footer links
- [ ] Add security headers to Next.js
- [ ] Add request ID tracking middleware
- [ ] Add graceful shutdown handler
- [ ] Replace Redis KEYS with SCAN
- [ ] Add composite database indexes
- [ ] Resolve package manager conflict (pick npm or pnpm)
- [ ] Populate shared packages (types, config)

### Phase 3: Legal & Compliance (Parallel with Phase 1-2)

- [ ] Engage securities law counsel
- [ ] Revise whitepaper to remove investment-return language
- [ ] Complete legal document placeholder fields
- [ ] Establish legal entity structure
- [ ] Implement OFAC wallet screening
- [ ] Create tax information documentation
- [ ] Register for charitable solicitation

### Phase 4: UX & Polish (Week 5-7)

- [ ] Build core UI components (Modal, Toast, Input, Skeleton)
- [ ] Add accessibility fixes (ARIA attributes, skip nav, contrast)
- [ ] Add conversion flow step indicator
- [ ] Add loading skeletons for all routes
- [ ] Replace hardcoded stats with on-chain reads
- [ ] Create favicon, OG image, logo assets
- [ ] Fix brand violations (remove $, "Buy" -> "Get", investment language)
- [ ] Implement dark mode or remove dead CSS variables

### Phase 5: Testing & Audit (Week 7-9)

- [ ] Add fuzz tests for all contract functions
- [ ] Add invariant tests
- [ ] Add governance lifecycle tests
- [ ] Add edge case tests (1 wei, zero fee, max supply)
- [ ] Commission professional smart contract audit
- [ ] Set up Immunefi bug bounty program
- [ ] Add integration tests for API routes
- [ ] Add E2E tests for conversion flow

---

## Appendix: Agent Coverage Summary

| Agent | Status | Key Findings |
|-------|--------|-------------|
| Backend Architect | Complete | 26 findings (P0-P5) |
| Database Optimizer | Complete | 9 categories of optimization |
| Solidity Contract Auditor | Complete | 8 priority levels, 20+ findings |
| Blockchain Security Auditor | Complete | 1C, 3H, 4M, 4L, 4I findings |
| Frontend Developer | Complete | 30 findings across 7 categories |
| Security Engineer | Complete | 4 critical, 6 high, 8 medium findings |
| Software Architect | Complete | 8 architecture areas, event mismatch discovery |
| Brand Guardian | Complete | 15 brand violations, missing assets |
| UI Designer | Complete | 8 categories, component roadmap |
| UX Researcher | Complete | 8 focus areas with wireframes |
| Legal Compliance | Complete | 10 compliance areas assessed |
| Testing Strategist | Rate limited | -- |
| DevOps/CI-CD | Rate limited | -- |
| SEO/Content | Rate limited | -- |
| Product Manager | Rate limited | -- |
| Growth Hacker | Rate limited | -- |
