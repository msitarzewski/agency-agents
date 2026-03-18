# FigJam Mermaid Spec — MNO Opportunity Flowchart
## Telcoin Association — Mobile Financial Services 2.0
### Source: MNO Deck Slides 8–9
### Generated: 2026-03-18

---

## Usage

Paste the Mermaid block below directly into a FigJam diagram node.
To do this in FigJam: Insert > Diagram > Mermaid, then paste the code.

---

## Mermaid Flowchart

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "primaryColor": "#3642B2",
    "primaryTextColor": "#F1F4FF",
    "primaryBorderColor": "#14C8FF",
    "lineColor": "#7393EA",
    "secondaryColor": "#192E58",
    "tertiaryColor": "#090920",
    "background": "#090920",
    "mainBkg": "#192E58",
    "nodeBorder": "#3642B2",
    "clusterBkg": "#0D1A3A",
    "titleColor": "#14C8FF",
    "edgeLabelBackground": "#090920",
    "fontFamily": "Inter, sans-serif"
  }
}}%%

flowchart TD

  %% ── TODAY: What MNOs Already Do ─────────────────────────────
  subgraph TODAY["📡  What MNOs Already Do"]
    direction LR
    CALLS["📞 Switch Calls\n─────────────\nConnect caller to recipient\nvia MNO routing layer"]
    SMS["💬 Route SMS\n─────────────\nDeliver messages\nbetween any two numbers"]
    DATA["🌐 Transfer Data\n─────────────\nRoute IP packets\nacross the internet"]
  end

  %% ── TOMORROW: What MNOs Can Now Do ──────────────────────────
  subgraph TOMORROW["💵  What MNOs Can Now Do"]
    direction LR
    CASH["💵 Switch Digital Cash\n─────────────\neUSD, eMXN, eEUR\nsettled on Telcoin Network"]
    PAYMENTS["⚡ Settle Payments P2P\n─────────────\nDirect consumer-to-merchant\nno correspondent bank"]
    REVENUE["📈 Earn Network Fees\n─────────────\nBlock production rewards\nfrom settlement throughput"]
  end

  %% ── BRIDGE NOTE ──────────────────────────────────────────────
  ANALOGY["🔁  The Same Infrastructure\n─────────────────────────────────\nMNO data centers already sit close\nto every smartphone on Earth.\nKYC infrastructure: ~7B people.\nTrusted, regulated, mission-critical."]

  %% ── QUOTE NODE ───────────────────────────────────────────────
  QUOTE["💬  Paul Neuner — Founder & CEO, Telcoin\n(American Banker)\n───────────────────────────────────────────────\n\"Telecoms around the world run the internet...\nWhy shouldn't they also process blocks\nand, effectively, the settlement layer\nof Digital Cash floating around the\nInternet of Money?\""]

  %% ── OUTCOME ──────────────────────────────────────────────────
  OUTCOME["🏦  MNO Business Model — No Banking License Required\n────────────────────────────────────────────────────────────\nRun the settlement layer → Earn revenue → No custody of funds\nPresent in every country · 2-3 MNOs per market · Already regulated"]

  %% ── FLOWS ────────────────────────────────────────────────────
  TODAY --> ANALOGY
  ANALOGY --> TOMORROW
  TOMORROW --> OUTCOME
  QUOTE -.->|"Validates the thesis"| ANALOGY

  %% ── STYLES ───────────────────────────────────────────────────
  classDef todayNode   fill:#192E58,stroke:#3642B2,stroke-width:2px,color:#F1F4FF,font-size:13px
  classDef tomorrowNode fill:#0D1D40,stroke:#14C8FF,stroke-width:2px,color:#F1F4FF,font-size:13px
  classDef bridgeNode  fill:#0A1228,stroke:#7393EA,stroke-width:1.5px,color:#C9CFED,font-size:12px
  classDef quoteNode   fill:#0A1228,stroke:#524CF8,stroke-width:1.5px,stroke-dasharray:5 4,color:#9aabf0,font-size:11px,font-style:italic
  classDef outcomeNode fill:#0D1A3A,stroke:#14C8FF,stroke-width:2.5px,color:#14C8FF,font-size:13px,font-weight:bold

  class CALLS,SMS,DATA todayNode
  class CASH,PAYMENTS,REVENUE tomorrowNode
  class ANALOGY bridgeNode
  class QUOTE quoteNode
  class OUTCOME outcomeNode
```

---

## Diagram Notes for FigJam Production

### Layout guidance
- The `TODAY` cluster should read left-to-right on a single row.
- The `TOMORROW` cluster mirrors it directly below.
- The `ANALOGY` bridge node sits between them as the visual pivot.
- The `QUOTE` node floats to the right of `ANALOGY`, connected with a dashed line.
- The `OUTCOME` node anchors the bottom as the result state.

### Color application in Figma post-processing
After importing the Mermaid output, apply these manual overrides in FigJam for full brand compliance:

| Element | Fill | Border | Text |
|---|---|---|---|
| TODAY subgraph background | `#0D1A3A` | `#3642B2` (1.5px) | `#F1F4FF` |
| TOMORROW subgraph background | `#071020` | `#14C8FF` (2px) | `#F1F4FF` |
| CALLS / SMS / DATA nodes | `#192E58` | `#3642B2` | `#F1F4FF` |
| CASH / PAYMENTS / REVENUE nodes | `#0A1830` | `#14C8FF` | `#F1F4FF` |
| ANALOGY bridge | `#0A1228` | `#7393EA` (dashed 4px) | `#C9CFED` |
| QUOTE node | `#0A1228` | `#524CF8` (dashed) | `#9aabf0` |
| OUTCOME node | `#0D1A3A` | `#14C8FF` (2.5px) | `#14C8FF` |
| Flow arrows | `#7393EA` | — | — |
| Dashed quote arrow | `#524CF8` | — | — |

### Typography
- Node titles: Inter Bold, 14px
- Node body: Inter Regular, 12px
- Subgraph labels: Inter SemiBold, 13px, uppercase, letter-spacing 0.1em

### Usage context
This diagram is intended for:
- Internal MNO pitch decks (Slide 8 companion)
- Agency visual briefings
- Partner onboarding materials

Not intended for direct social media publication without redesign in Figma.

---

## Extended Version — Market Expansion Layer

Add this second flowchart below the first in the same FigJam board to show the market footprint.

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "primaryColor": "#3642B2",
    "primaryTextColor": "#F1F4FF",
    "primaryBorderColor": "#14C8FF",
    "lineColor": "#7393EA",
    "background": "#090920",
    "mainBkg": "#192E58",
    "fontFamily": "Inter, sans-serif"
  }
}}%%

flowchart LR

  SCALE["3 Billion People\nTargeting H1 2026\n─────────────────\n2.5B with local\nbank account numbers"]

  subgraph TIER1["Tier 1 — Native Digital Cash + Bank Accounts"]
    USA["🇺🇸 USA\nMSB + DADI"]
    EU["🇪🇺 EU/EEA\nVASP + CASP* + EMI*"]
  end

  subgraph TIER2["Tier 2 — Native Digital Cash Rails"]
    CA["🇨🇦 Canada\nMSB + PSP*"]
    SG["🇸🇬 Singapore\nMPI + DPT*"]
    AU["🇦🇺 Australia\nRSP + DCE"]
    MX["🇲🇽 Mexico\nVASP + IEPF*"]
  end

  subgraph TIER3["Tier 3 — Direct Stablecoin Rails"]
    GB["🇬🇧 UK\nCAX*"]
    IN["🇮🇳 India\nVASP*"]
    AR["🇦🇷 Argentina\nVASP"]
    TR["🇹🇷 Turkey\nVASP*"]
    JP["🇯🇵 Japan\nCAES*"]
    KE["🇰🇪 Kenya\nEMI*"]
  end

  SCALE --> TIER1
  SCALE --> TIER2
  SCALE --> TIER3

  classDef scaleNode fill:#0A1830,stroke:#14C8FF,stroke-width:2.5px,color:#14C8FF,font-weight:bold,font-size:14px
  classDef t1node fill:#0D2040,stroke:#14C8FF,stroke-width:2px,color:#F1F4FF,font-size:12px
  classDef t2node fill:#0D1A3A,stroke:#3642B2,stroke-width:2px,color:#F1F4FF,font-size:12px
  classDef t3node fill:#0A1228,stroke:#524CF8,stroke-width:1.5px,color:#C9CFED,font-size:12px

  class SCALE scaleNode
  class USA,EU t1node
  class CA,SG,AU,MX t2node
  class GB,IN,AR,TR,JP,KE t3node
```

### Abbreviation key for market expansion diagram
| Abbr | Full name |
|---|---|
| MSB | Money Services Business |
| DADI | Digital Asset Depository Institution |
| VASP | Virtual Asset Service Provider |
| CASP | Crypto Asset Service Provider |
| EMI | E-money Institution |
| PSP | Payment Service Provider |
| MPI | Major Payment Institution |
| DPT | Digital Payment Tokens |
| RSP | Remittance Service Provider |
| DCE | Digital Currency Exchange |
| IEPF | Institution of Electronic Payment Funds |
| CAX | Crypto Asset Exchange |
| CAES | Crypto-asset Exchange Service |
| * | Application in preparation or processing |

---

*This spec was produced for the Telcoin Association Marketing Agency. For production questions, refer to `design/DESIGN-TEAM.md`.*
