# Telcoin Association & Network — Campaign Research
## Last updated: March 15, 2026
## Sources: telcoin.org, telcoin.network, forum.telcoin.org, CoinMarketCap, Business Wire, Governor of Nebraska, GitHub, web search, council call recap (week of Mar 10), telcoinwiki.com (full site crawl March 15, 2026)

> Roadmap data sourced directly from roadmap.telcoin.network (screenshots, March 10, 2026).
> Developer Notes last updated: **February 19, 2026** per roadmap page.

---

## 1. TELCOIN ASSOCIATION

### Legal Structure
- **Type**: Swiss Verein (non-profit association)
- **Domicile**: Canton Ticino, City of Lugano, Switzerland
- **Swiss Verein notes**: No capital contribution required; members don't share profits/liabilities; governance defined by internal statutes; tax-exempt under certain conditions
- **Website**: telcoin.org
- **X/Twitter**: @telcoinTAO
- **Forum**: forum.telcoin.org
- **GitHub**: github.com/telcoin-association (23 repositories)

### Mission & Vision
- **Mission**: Represent interests of GSMA Mobile Networks and other stakeholders; use blockchain technology to globally support financial inclusion and prosperity
- **Vision**: Decentralized platform bringing blockchain-powered mobile financial services to telecoms and subscribers globally — designed to reach every mobile phone user in the world

### Leadership (Publicly Known)
| Name | Title |
|---|---|
| Paul Neuner | Co-Founder and CEO |
| Parker Spann | EVP Business Development & Strategy; Founder of Telcoin Association; Executive Director of TAO |
| Tim Mahota | General Counsel and Chief Compliance Officer |
| Richard Schendel | VP Banking Operations |
| Rajesh Sabari | Chief Commercial Officer, CFA |

**Advisory Members:**
- Michimasa Naka — 28 years banking experience, CEO Boardwalk Capital
- Toby Hoenisch — Co-founder & CEO TenX
- Matthew McGuire — Former COO Bank of America Merrill Lynch Japan & RBS Japan

### Governance Structure
- **Model**: Polycentric, democratic self-governance (based on Elinor Ostrom's 8 Design Principles for common-pool resources)
- **Four Miner Groups** (equal authority): Validators, Liquidity Miners, Developers, Stakers
- **Miner Assembly**: Collective body with ultimate power over platform governance
- **Council structure**: Constitutional-level governance with specialized councils
- **TELIPs**: Telcoin Improvement Proposals — community-submitted governance proposals
- **Forum**: forum.telcoin.org — active governance discussions, elections, TGIPs

### Recent Governance Activity
- **Y3 TEL Allocation (TELIP)**: 900 million TEL proposed for Year 3 (January 2026) — purpose: platform development, miner incentives, mainnet launch support
- Miner Council elections underway as of Q1 2026

---

## 2. TELCOIN NETWORK

### Architecture
- **Type**: EVM-compatible Layer 1 public blockchain
- **Consensus**: Proof-of-Stake using Narwhal and Bullshark consensus protocol (local DAG-based)
- **Validators**: ONLY GSMA full-member MNOs can validate blocks and earn rewards
- **Native gas token**: TEL
- **Chain ID**: 2017
- **RPC**: https://rpc.telcoin.network
- **Block explorer (testnet)**: scan.telcoin.network
- **Block explorer (alt)**: telscan.io
- **Main site**: telcoin.network

### GSMA Validator Model
- Exclusive right for GSMA Operator Member MNOs to run transaction nodes and earn network fees
- MNOs must meet basic criteria set by Telcoin Association AND stake TEL
- Each new MNO validator = new distribution channel to that telecom's subscriber base
- Creates direct economic alignment: more usage → more fees → MNOs promote Telcoin services

### Adiri Testnet — Status: ACTIVE
Source: roadmap.telcoin.network (March 10, 2026 screenshots)

> "Preparing the Adiri public testnet so partners and MNO validators can exercise the network in a live setting."

#### Phase 1 — ALL COMPLETED ✓
- Pre Cantina competition
- Initial spin up of TAO controlled validator nodes
- Launch block explorer
- Demo PoC
- Feature complete
- 4-week security assessment

#### Phase 2 — IN PROGRESS
**Completed ✓**
- Patch security findings
- Enhance test coverage
- Production harden database read/write strategy
- Improve documentation
- MiCA whitepaper
- Improve async logging for all nodes in the network
- Updates to support open-source contributions
- Parallelize testing infrastructure for faster, more reliable testing

**In Progress ⚡ (active as of Feb 19, 2026)**
- Production harden p2p networking
- Production harden syncing strategy
- Integrate with bridge partner (**LayerZero** — initial scoping document delivered; implementation pending)
- Stress test deployed network in preparation for public release
- Confirming availability of specialist researchers with security partners
- Support p2p streaming for bulk data transfer
- Streamline database infrastructure for production
- Custom TN RPC endpoints
- Harden epoch boundary records for secure syncing
- Better tools for validators to sync, stake, and activate
- Relaunch network

**Queued ⏳**
- Support multiple workers for parallel fee markets
- Deploy new faucet service

#### Phase 3
- **In Progress ⚡**: Integrate with LayerZero — LayerZero's decentralized validator network aligns naturally with the GSMA MNO validator set; initial scoping doc delivered; LayerZero launching own chain does not change partnership plans
- **Queued ⏳**: Decentralize network (onboard MNO Validators)

---

### Mainnet Release — Status: UPCOMING
Source: roadmap.telcoin.network

> "Mainnet launch once Adiri is stable and the final audits and security competition are complete."

**No calendar date given — milestone-based launch.**

#### Mainnet Milestones — All Queued ⏳
- Launch Mainnet
- Cryptography security assessment
- P2P Network security assessment
- Smart contract security assessments
- Execution layer security assessment
- State synchronization security assessment
- Patch security findings

---

### Developer Notes — Updated February 19, 2026
Source: roadmap.telcoin.network "Latest Updates" section

- **Support P2P Streaming for Bulk Data Transfer** — Implement peer-to-peer streaming mechanisms to enable efficient bulk data transfer between nodes, improving sync performance and reducing reliance on centralized distribution.
- **Streamline Database Infrastructure for Production** — Refactor and optimise database architecture to ensure production-grade performance, reliability, and scalability across validators and observers.
- **Custom TN RPC Endpoints** — Develop dedicated Telcoin Network RPC endpoints tailored to ecosystem use cases, improving performance, flexibility, and infrastructure control.
- **Harden Epoch Boundary Records for Secure Syncing** — Improve validation and integrity checks around epoch boundaries for secure syncing. *(description truncated in screenshot)*

### Testnet → Mainnet Infrastructure Sequencing
Source: Platform & Treasury Council recap (week of Mar 10, 2026)

- **Testnet deployment**: Distributed cloud data centers (US east + west coasts) + volunteer nodes globally — tests wide area network latency at geographic scale
- **Mainnet validators**: Private MNO-owned bare-metal data centers running alongside existing telecom packet-switching infrastructure — fiber-optic interconnects capable of streaming tens of gigabits/second; performance characteristics not available in standard cloud
- **Transition requirements**: Validate tooling, latency configs, dynamic firewalls, access controls before deploying into secured MNO data centers
- **Why the sequencing matters**: Getting into MNO data centers requires extensive permissions given their highly secured nature — protocol must reach sufficient maturity first

### Security Assessment Status
Source: Platform & Treasury Council recap (week of Mar 10, 2026)

- All internal BLS cryptographic library findings: **resolved**
- Next external assessments: being scheduled with top EVM security researchers (many identified/approached at ETH Denver)
- Order: BLS library assessment first → comprehensive protocol audits
- Timeline: flexible to match right researcher expertise — "securing the right minds, not rushing checklists" (Grant)
- ~12 PRs closed in this cycle: production hardening, bug patches, security improvements — no feature additions

### Team Expansion Plans (Mar 12 Council)
Source: Platform & Treasury Council #26 (March 12, 2026)
- 2 additional Rust protocol engineers (to be onboarded sequentially)
- Additional smart contract engineering capacity
- Dedicated security engineer
- Stress testing now expanded to community-run nodes

### Active Governance Proposals (as of Mar 12)
- **TIP 11 — Development Process Standardization**: Advancing toward snapshot vote; establishes formal workflows preventing ad hoc Slack/Discord requests; breaks work into discrete trackable parts; defines "done" criteria
- **Unified Web Architecture TIP**: New TIP presented proposing telcoin.network as the single trusted entry point — from solo developers through MNO enterprise partnership onboarding; internal system mapping and audits underway
- **Miner Council elections**: Candidate introductions live, voting opened (Q1 2026)

### TAN Council Budget (Mar 12 Council)
Source: TAN Council recap (March 12, 2026)
- TAN Council carryforward from Y1+Y2 prudent management: **164–165 million TEL**
- Total TEL issued across both prior years (Y1+Y2 combined): approximately **60 million TEL**
- No additional Y3 allocation requested from the Y3 TELIP — carryforward is sufficient to fund TANIP-1
- Developer pitch decks in development for outreach: highlighting Telcoin Network's MNO-validated infrastructure, defined earning mechanisms, and regulatory positioning
- EVM compatibility pitch: build on Base now → redeploy to Telcoin Network at mainnet with minimal friction

### TAN Application Layer — Trading Fee Rebate Program (Passed ~Mar 12, 2026)
Source: forum.telcoin.org/t/tanip-trading-fee-rebate-program/824 — submitted Dec 8, 2025 by TAN Council; snapshot vote passed ~Mar 12, 2026

**What it is**: A replacement of the original TANIP-1 issuance-based reward model with a capped rebate model. Preserves all TANIP-1 infrastructure and mechanics; the ONLY change is a rebate cap.

**Why the change — TANIP-1 findings**:
- Weekly distributions of 3.2M TEL worked reliably; computation framework performed as intended
- But: fee activity during TANIP-1 converged around the issuance amount (fee cycling / "mercenary capital")
- Fees dropped immediately when the program paused → organic demand was not the driver
- Weekly active wallet counts remained flat; new wallets churned rather than accumulated
- Referral flows often became circular (self-referential)

**Rebate Formula**:
- R = calculated issuance from own + referee fees (same as original TANIP-1 formula)
- F = total TEL fees paid by the wallet during the period
- **Final rebate = min(R, F)**
- Result: a wallet cannot earn more TEL than it actually paid in fees → removes the core mercenary incentive

**What stays the same**:
- Stake requirement via StakingModule
- Referral tree logic
- On-chain fee verification (aggregator-to-AmirX transfers)
- Deterministic off-chain calculation
- Weekly batched uploads to TANIssuanceHistory
- Network-agnostic design (future developers can adopt)
- Eligibility rules

**Funding & governance**:
- Funded by existing TAN Council Safe (164–165M TEL carryforward from Y1+Y2)
- Distributed weekly through a **newly deployed** TANIssuanceHistory contract
- TANIssuanceHistory redeployment = **Lifetime TEL issuance resets to zero** for all wallets (unavoidable; flagged in proposal)
- No new app integrations required for stakers

**Implementation path**:
- TAN Council engages TAO to update the off-chain rewards calculation script
- Redeploy TANIssuanceHistory contract
- Activate rebate program; maintain weekly uploads
- Track participation under new model; evaluate return to full issuance model as network matures

**What this is NOT**:
- Not a developer incentive program (that is a future TANIP)
- Does not change referral logic, staking logic, reward computation methods, or eligibility rules

### Open Source Contributions
- **TanguyDeTaxis (Tan Guide)**: Streamlined execution environment, supporting multiple execution environments (avoids writing empty data when no transactions exist, improves performance), future-proofing protocol components

---

## 3. PRODUCTS

### Telcoin Wallet
- **Domain**: telco.in (wallet app) — distinct from telcoin.org (association) and telcoin.network (blockchain)
- **Version**: V5 expected early 2026 (not V4)
- **Platforms**: iOS and Android
- **Networks supported**: Polygon, Base (migrating to Telcoin Network at mainnet)
- **Features**: Hold Digital Cash stablecoins, swap tokens, send remittances to mobile money platforms

**Active Remittance Corridors (16 countries, 23+ platforms):**
| Country | Platform(s) |
|---|---|
| Bangladesh | BKash |
| Ethiopia | HelloCash |
| Fiji | Digicel |
| Ghana | MTN Money |
| Guatemala | Tigo Money |
| Indonesia | Dana, GoPay, LinkAja, OVO |
| Kenya | Equitel Money |
| Sri Lanka | Ez Cash, mCash |
| Malawi | Airtel Money |
| Nepal | eSewa |
| Pakistan | Easy Paisa, Jazz Cash |
| Philippines | Coins |
| El Salvador | Tigo Money |
| Tonga | Digicel |
| Uganda | Airtel Money, MTN Money |
| Samoa | Digicel |

- **Fee target**: 2% or less total (vs. 6–10% Western Union/MoneyGram)

### TELx — DeFi Platform
- **Networks**: Polygon PoS and Base
- **Pools**: Balancer V2 (6 active markets), Uniswap V4 (migrated Nov 5, 2025)
- **Yield**: Liquidity miners earn exchange fees + TEL rewards + governance rights
- **Analytics**: telx.network/pools
- **Staking**: Weekly rewards every Wednesday 00:00 UTC; 3.2 million TEL distributed weekly based on activity
- **TAN Council Safe**: 194.44 million TEL held
- **eXYZ stablecoin pools**: USDC/eUSD pools live on Base (Uniswap) and Solana (Raydium)

#### Merkl Integration Trial — APPROVED
Source: TELx Council recap (week of Mar 10, 2026)

- **Snapshot vote**: Passed unanimously 6/6, closed March 10, 2026 — first successful proposal from council member Tai
- **Model selected**: Per-position gating ($6,000 integration cost vs. $3,000 per-wallet; granularity maintained to match current hook-based structure)
- **Cost**: ~2.175 million TEL over 6 months (~363,000 TEL/month) from TX operational wallet (10M TEL held — untouched; does not reduce existing pool incentives)
- **Timeline**: ~4 weeks from snapshot → live ~April 2026; full analysis targeted mid-May
- **Test setup**: Running in parallel on Base V4 pool (TEL/ETH) — Merkl vs. current hook system, no double rewards
- **Why Merkl**: Dynamic/flexible incentive structures; target active tick liquidity; bounded price ranges; adjust per-pool without hook modifications + security audits; scales for future pool additions
- **Strategic goal**: Shift from fixed equal allocation (6 pools) to formula-based distribution that can rapidly onboard new pools (especially eXYZ stablecoins and Telcoin Holdings corridors)

#### Pool Strategy Notes
- Uniswap V4: Better for volatile pairs (TEL/ETH); recent data shows closer to 1:1 liquidity-to-reward ratio
- Stable pairs: V4 concentrated liquidity creates constant rebalancing burden; most LPs stay in simpler V2/V3 "set and forget" pools
- Balancer V3 Reclaim Pools: Still under evaluation for stable pair infrastructure
- **Base potentially leaving OP Stack**: Monitoring; Uniswap applications not expected to be impacted but backend changes may require retesting (council member Cody has Base/The Block contacts for intel)

#### Operational
- Reward script issues from prior weeks: fully resolved with redundancy in place
- Period 29 distribution: completed quickly after epoch close
- Website fee graph bug: fixed, deploys in next general update
- New manual liquidity withdrawal guide (direct contract access if UI unavailable): in preparation
- TX University: handover to Leo and Storm underway; final licensing + content polish before launch

### eUSD Stablecoin
- **Launch date**: December 26, 2025
- **Issuer**: Telcoin Digital Asset Bank (state-chartered U.S. bank)
- **Backing**: 1:1 backed by USD + short-term U.S. Treasury assets
- **Audits**: Monthly attestations from external auditor
- **Initial mint**: $10 million eUSD
- **Networks**: Ethereum and Polygon (Telcoin Network at mainnet)
- **Access**: Telcoin Wallet V5 (early 2026 onboarding)
- **Distinction**: FIRST bank-issued on-chain stablecoin — issued under U.S. banking law, not by a private company

### Digital Cash Stablecoin Suite
| Token | Currency | Status |
|---|---|---|
| eUSD | US Dollar | Live — Ethereum + Polygon |
| eGBP | British Pound | Live — Polygon |
| eJPY | Japanese Yen | Live — Polygon |
| eSGD | Singapore Dollar | Live — Polygon |
| eZAR | South African Rand | Live — Polygon |
| eEUR | Euro | Planned — MiCA compliant (e-Money Institution) |

- **Mercado Bitcoin**: Listed eUSD and eGBP

### Telcoin Digital Asset Bank
- **Charter type**: Digital Asset Depository Institution (DADI)
- **Charter date**: November 12, 2025
- **Signed by**: Nebraska Governor Jim Pillen
- **Regulator**: Nebraska Department of Banking and Finance
- **Legal framework**: Nebraska Financial Innovation Act + GENIUS Act guidelines
- **Authorized to**: Accept crypto deposits, provide crypto loans, connect to Federal Reserve payment rails, connect customers to DeFi
- **Capitalization**: $25 million secured
- **Operations began**: December 26, 2025 (eUSD launch)
- **Personal/business accounts**: Launch Q1 2026
- **Historic significance**: First-in-nation U.S. digital asset bank charter

---

## 4. TEL TOKEN

### Contract Addresses
| Network | Address |
|---|---|
| Ethereum | `0x467bccd9d29f223bce8043b84e8c8b282827790f` |
| Polygon (Proxy) | `0xdf7837de1f2fa4631d716cf2502f8b230f1dcc32` |
| Polygon (Implementation) | `0x805b70339183f9a98cc7fcb35fcbeb5ac10713ea` |
| Telcoin Network | Native gas token (address TBD — mainnet not live) |

### Tokenomics
- **Max supply**: 100 billion TEL (hard cap)
- **Circulating supply**: ~96.074 billion TEL (96% of max)
- **Issued**: 2017

### Market Data (March 2026)
- **Price**: ~$0.002642 USD
- **24h volume**: ~$1.35M USD
- **Market cap**: ~$253.8M USD
- **CMC rank**: ~#122

### Exchange Listings
- Kraken (listed January 26, 2026 — 13M+ users, 190+ countries)
- Bybit (primary volume, TEL/USDT)
- MEXC
- Coinbase
- Binance
- Balancer V2 (Polygon — DEX)

### Staking
- Deposit TEL via TAN staking contracts in Telcoin Wallet
- Weekly reward distribution: every Wednesday 00:00 UTC
- Weekly pool: **3.2 million TEL** distributed to all stakers based on activity (confirmed — TANIP findings report)
- Reward types: Under active Trading Fee Rebate Program: capped rebate = min(calculated issuance, actual TEL fees paid)

---

## 5. COMMUNITY & SOCIAL

### @telcoinTAO (X/Twitter)
- Primary official account for Telcoin Association
- Bronze Sponsor of DC Blockchain Summit 2026 (March 17–18, Washington DC) — confirmed via summit sponsor page Mar 11, 2026 (Silver in 2025, Bronze in 2026)
- Content: Roadmap updates, governance announcements, network milestones

### Reddit: r/telcoin
- Community exists; historically positive sentiment
- Activity: Variable — not high-volume
- Topics: Technology, partnerships, roadmap, competition

### Forum: forum.telcoin.org
- Active governance discussions (TELIPs, council elections, TGIPs)
- Key recent threads: Y3 TEL allocation TELIP, Miner Council elections

### Council Members & Key Figures (from recap)
- **Grant**: Platform & Treasury Council — leads security strategy, MNO relations, testnet/mainnet sequencing
- **Steve**: Lead on database layer scaling refactor
- **Leo**: TAN Council + TELx Council; TANIP-1 implementation; TX University handover; reward script ops
- **Storm**: TX University handover co-lead
- **Tai**: TELx Council — authored Merkl trial proposal (passed Mar 10)
- **Mike**: TELx Council — Telcoin Holdings coordination on eXYZ pool strategy
- **Cody**: TAN Council member; builder (random square guessing game on Base); Base/The Block ecosystem contacts
- **TanguyDeTaxis (Tan Guide)**: Open-source contributor — execution environment improvements
- **Hodler Vaughn**: Telcoin Magazine contributor, governance analysis
- **Parker Spann**: Executive Director, governance innovation
- **TelcoinFan** (@TelcoinFan): Active community voice on X
- **Telcoin_Juggler** (@Telcoin_Juggler): Active community voice on X

### YouTube
- **Channel**: youtube.com/@TelcoinTAO — full council meeting recordings available

### Builder Ecosystem (TAN Council)
Source: TAN Council recap (week of Mar 10, 2026)

- **Random square guessing game** (Cody): No-loss lottery micro-app; live on Base; ~$1 entry, 10% to TAN treasury, 90% to prize pot; 1-in-10,000 chance; Chainlink VRF integration planned; will migrate to Telcoin Network at mainnet
- **Telcoin Name Service**: .tel human-readable on-chain addresses (e.g. Cody.tel, Dolly.tel) — ENS equivalent native to Telcoin ecosystem; integrates into wallet UX
- **Charity NFT Subscription** (Leo): Revokable NFTs tied to streamed donations; hold NFT while streaming funds to charity wallet; NFT revoked when stream stops; fully on-chain transparency; long-term goal: accumulate substantial TEL in charity wallets → onboard orgs like UNICEF on-chain
- **Strategic philosophy**: Fun, low-friction apps/games/art = fastest path to mass adoption (mirrors Solana playbook); shift away from pure speculation toward genuine utility and public goods

### Developer Onboarding
- Telcoin Network is EVM-compatible — developers can build on Base now, then redeploy to Telcoin Network at mainnet
- Codebase: github.com/Telcoin-Association (fully open-source)
- Contact: Discord, X, or directly to council members for support
- Developer portal + unified web presence: in development (company conducting internal audits + system mapping; targeting single entry point from solo devs → enterprise partnership onboarding)

---

## 6. COMPETITIVE LANDSCAPE

### Direct Remittance Crypto Competitors
| Project | Model | Telcoin Differentiator |
|---|---|---|
| XRP/Ripple | Bank-to-bank B2B, 300+ institution partners | Mobile-first, retail/consumer, MNO validators |
| Stellar (XLM) | Non-profit, emerging markets, anchor model | MNO validators = real infrastructure, not just anchors |
| Celo | Ethereum L2, phone number identity, mobile-first | L1 with bank charter, GSMA-native, regulated |
| Traditional SWIFT | Correspondent banking, 3–5 day settlement | Near-instant, near-zero fees |

### Traditional Remittance Fees (Benchmark)
- Western Union: 3–8% typical
- MoneyGram: 4–6%
- Bank wire: flat $25–$45
- World Bank global average: ~6.3%
- **Telcoin target**: ≤2%

### Telcoin's Moat
1. Only blockchain with GSMA MNO validators (licensed, accountable, globally distributed)
2. Only regulated U.S. digital asset bank with DeFi connection authority
3. Only bank-issued on-chain stablecoin (eUSD)
4. 16-country live remittance network with 23+ mobile money integrations

---

## 7. RECENT NEWS TIMELINE

| Date | Event |
|---|---|
| Nov 12, 2025 | Nebraska Governor signs first-in-nation Digital Asset Depository Institution charter |
| Dec 2025 | Adiri Testnet launches |
| Dec 26, 2025 | Telcoin Digital Asset Bank operations begin; eUSD minted ($10M initial) |
| Jan 26, 2026 | TEL listed on Kraken |
| Mar 2-5, 2026 | Mobile World Congress Barcelona — full team attended; private MNO partner meetings; no public mainnet reveal (intentional); focus on demonstrating new MNO revenue streams |
| Mar 10, 2026 | Merkl trial snapshot vote closes — unanimous 6/6 approval |
| Mar 12, 2026 | Platform & Treasury Council #26 — BLS fully resolved; external audits being scheduled; TIP 11 + unified web arch TIP presented; team expansion announced; Miner Council elections live |
| Mar 12, 2026 | TAN Council — **Trading Fee Rebate Program** (TANIP successor) passed snapshot vote (implementation target late March); 164-165M TEL carryforward confirmed; builder demos: .tel name service, lottery game, charity NFT |
| Mar 18, 2026 | TELx Council meeting (3PM EST, note: DST may affect calendar display) |
| ~April 2026 | Merkl trial goes live on Base V4 TEL/ETH pool |
| ~Late March 2026 | TANIP-1 deployment (target, flexible) |
| Mid-May 2026 | Merkl trial analysis + review |
| Q1 2026 | Telcoin Wallet V5 launch (per research) |
| Q1 2026 | Personal/business bank accounts open |
| Q1 2026 | Miner Council elections ongoing |
| TBD | Mainnet launch — see roadmap.telcoin.network |

---

## 8. TELCOIN WIKI INTELLIGENCE (telcoinwiki.com — crawled March 15, 2026)

> Source: telcoinwiki.com — unofficial community guide authored by community member @BZ_crypto1.
> Site launched recently (per X post from BZ_crypto1 referencing the new site going live).
> Pages: home (/), deep-dive.html, about.html, telx.html, links.html, pools.html, portfolio.html

### Site Overview
TelcoinWiki is an unofficial community guide designed to demystify Telcoin for everyday users. It combines coverage of the RegFi model, carrier-secured blockchain, digital asset bank, and TEL token into one accessible resource. Community-maintained; not affiliated with Telcoin Association officially.

### Key Framing / Narrative Language from the Wiki

**"RegFi" model**: The wiki popularizes this term — Regulated DeFi. Telcoin owns the full stack: U.S.-chartered digital-asset bank + carrier-secured L1 blockchain validated by GSMA-member MNOs + regenerative TEL token that powers transactions and rewards user-generated liquidity. Described as a "triple advantage" for real-world adoption.

**"Internet of Money"**: Core narrative — just as the internet standardized information exchange globally, Telcoin aims to standardize value exchange across mobile networks worldwide. Digital Cash stablecoins are described as the "backbone of the Internet of Money."

**Carrier-secured blockchain**: Wiki's preferred shorthand for the GSMA MNO validator model.

### TEL Token Issuance Mechanics (net-new detail)
- TEL Treasury issues at a rate of approximately **10% annually** of its inventory, redistributed via programmable flows across the platform.
- A portion of all TEL gas fees paid each block are **destroyed and regenerated equally to the TEL Treasury** — tying Telcoin Network blockspace demand to the sustained yield of TEL for future generations of miners. (This is the gas fee burn/regeneration loop.)
- Miner rewards are approximately **200M TEL per year** distributed to miners across all groups.
- Weekly staker pool: **3.2 million TEL per week** — confirmed correct via TANIP findings report (forum, Dec 8, 2025). Earlier research file entry of "3.2 billion" was a unit error; corrected.

### TEL Staker Mechanics (TANIP-1 details)
- Stakers earn up to **42% of referred users' trading fees**.
- Maximum Weekly TEL Issuance Rule: Stakers may mine accrued weekly issuance only if `total staked TEL > (TEL issuance income/lifetime + TEL issuance income/current week)`. Any excess TEL not mined due to insufficient stake is returned to TAN Council safe for reallocation.
- 194.44M TEL held in TAN Council Safe (consistent with research file).

### TAN Council & Developer Incentives
- Developer Incentives (a future TANIP beyond TANIP-1) are in development — will incentivize GSMA member application development on TAN.
- TAN is described as a network of mobile applications integrated with the underlying platform layers, acting as the user interface connecting consumers to digital wallets, asset exchange, remittances, and staking.

### Historical Platform Architecture Context
- **Rivendell**: Earlier name for what is now Telcoin Network — described as an "Ethereum sidechain" in V3 architecture docs. Telcoin used Polygon SDK to build Rivendell. This predecessor became what is now referred to as Telcoin Network (the standalone L1 with Narwhal/Bullshark consensus, no longer a sidechain framing).
- The platform evolved: Telcoin App (application layer) + TELx (liquidity engine) + Rivendell/Telcoin Network (settlement layer). Now described as three-layer: Telcoin Wallet + TELx + Telcoin Network.

### TELx Historical Pool Data (wiki pools.html)
- 2020–2021: 2 markets on Balancer V1 and Uniswap V2 (Ethereum)
- 2021–Pre-TGIP1: 32 markets across three DeFi protocols (Quickswap, DFX, Balancer V2 on Polygon PoS)
- Post-TGIP1: Down to 6 markets on Balancer protocol on Polygon
- Future: Primary location will be Telcoin Network post-mainnet
- Live pool data redirected to telx.network/pools (wiki pools page: data currently unavailable)

### TELx Portfolio Page Notes (wiki portfolio.html)
- Illustrative/design-time view of TEL claimable rewards and LPT stakes
- Key warning: Rewards from deprecated pools stop compounding after sunset date — users advised to restake to active pairs
- Shows "Claim all" interface design for TELx positions

### Governance Detail (from wiki)
- Elinor Ostrom's 8 Design Principles embedded at constitutional level of Telcoin Association governance — explicitly including the 8th principle of "nested enterprise" (nested tiers from lowest level up = bottom-up ecosystem)
- Four Miner Groups share equal authority: Validators (Telcoin Network), Liquidity Miners (TELx), Developers (TAN), Stakers (TAN)
- Improvement proposal naming conventions: TELIPs (platform-wide), TANIPs (TAN application layer), TELxIPs (TELx layer)
- Compliance Council: approves GSMA MNOs before they can become validators (gatekeeping function)
- Validators during alpha-mainnet: no slashing enabled; governance may manually slash or revoke NFT access to participate

### Validator NFT Access
- New detail from wiki: Validator participation access is controlled via **NFTs** that governance can revoke — this is the permissioning mechanism during the alpha-mainnet phase before full decentralization.

### MNO Reach & Adoption Stats (from community sources via wiki)
- Telcoin has counted **over 200 million users** across partner MNO platforms (mobile money account holders through partner MNOs)
- Target: **50+ MNO validators** onboarded (2025 roadmap target)
- Named MNO partners mentioned: Digicel, MTN, Airtel, GCash, Orange, Vodafone, Viettel

### GSMA Membership Note
- Wiki notes Telcoin joined GSMA as an **associate member** (not operator member) — becoming the first telecom-focused crypto to partner with GSMA network operators for distribution
- Validators must be GSMA **Operator Member** MNOs (a more specific, higher-tier GSMA membership than Telcoin Association's own associate membership)
- Year of GSMA membership: 2018

### Remittance Volume Stat (from community sources via wiki)
- Transaction volumes: **$50 million in Q2 2025**, up from $20 million in 2024

### External Validator Infrastructure Detail (via wiki)
- Outbound bridging transactions from Telcoin Network: **7-day wait period**, then second transaction to complete bridging off TN
- TEL exists as ERC-20 on Ethereum; initial block reward balance bridged before genesis via **Axelar** (note: Axelar was the initial bridge; LayerZero is the future bridge partner)

### Links Curated on telcoinwiki.com/links.html
Categories include: official documentation, liquidity tools, regulatory filings, community hubs, staking and yield farming guide, wallet setup, understanding liquidity pools, Nebraska DADI charter news, exchange listings (CoinMarketCap, Coinbase, Gate.com)

---

## 9. THINGS TO VERIFY BEFORE PUBLISHING

- [x] Mainnet timeline/phases — confirmed from roadmap.telcoin.network (March 10, 2026)
- [x] 2026 DC Blockchain Summit sponsorship tier — Bronze (confirmed Mar 11, 2026)
- [ ] Wallet V5 exact launch date
- [ ] Which specific MNOs have committed as mainnet validators
- [ ] Current TVL in TELx (check telx.network/pools)
- [ ] Current follower count on @telcoinTAO
- [ ] Any new corridor/partnership announcements since Jan 2026
- [ ] Personal/business bank account launch status
- [x] Bridge partner — **LayerZero** confirmed (initial scoping doc delivered; Axelar no longer active)
- [x] Verify weekly TEL staker distribution: **3.2 million TEL/week** — confirmed via TANIP findings report (forum.telcoin.org, Dec 8, 2025). Research file previously had "3.2 billion" — corrected.
- [ ] Confirm current active remittance corridor count: research file shows 16 countries/23+ platforms; wiki/community sources cite 20+ countries/40+ e-wallets — may reflect different product versions or time periods; verify against current telco.in
