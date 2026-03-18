# FigJam / Mermaid — Internet of Money Comparison Spec

**File**: `figma-internet-of-money-comparison.md`
**Purpose**: Side-by-side flowchart for FigJam import or Mermaid rendering — Legacy SWIFT hub-and-spoke (The Problem) vs. Internet of Money peer-to-peer network (The Solution).
**Brand reference**: `strategy/BRAND-GUIDE.md`
**Last updated**: 2026-03-18

---

## Rendering Instructions

This spec uses Mermaid `flowchart LR` syntax with `classDef` for brand color treatment.
Paste into any Mermaid-compatible renderer (FigJam, Notion, mermaid.live, VS Code extension).

For FigJam: use the Mermaid plugin → paste the block below → export as SVG or PNG at 2x.

---

## Mermaid Diagram — Full Comparison

```mermaid
%%{
  init: {
    "theme": "base",
    "themeVariables": {
      "background": "#090920",
      "primaryColor": "#192E58",
      "primaryTextColor": "#FFFFFF",
      "primaryBorderColor": "#3642B2",
      "lineColor": "#424761",
      "secondaryColor": "#090920",
      "tertiaryColor": "#090920",
      "fontFamily": "Inter, sans-serif",
      "fontSize": "14px"
    }
  }
}%%

flowchart LR

  %% ─────────────────────────────────────────────────────────────────
  %% LEFT SIDE — THE PROBLEM: Legacy SWIFT Hub-and-Spoke
  %% ─────────────────────────────────────────────────────────────────

  subgraph PROBLEM["❌  THE PROBLEM — Legacy Hub-and-Spoke"]
    direction LR

    P_Consumer["👤 Consumer"]
    P_BoA["🏦 Bank of America\nBaaS Bank"]
    P_WF["🏦 Wells Fargo\nBaaS Bank"]
    P_Visa["💳 Visa\nPayment Processor"]
    P_MC["💳 Mastercard\nPayment Processor"]
    P_Fed["🏛 Federal Reserve\nFedLine Clearing"]
    P_SWIFT["🌐 SWIFT\nGlobal Hub"]
    P_UK["🇬🇧 U.K."]
    P_EU["🇪🇺 Europe"]
    P_CN["🇨🇳 China"]
    P_JP["🇯🇵 Japan"]
    P_BR["🇧🇷 Brazil"]
    P_US["🇺🇸 U.S.A."]
    P_Merchant["🏪 Merchant"]

    P_Consumer -->|"Step 1"| P_BoA
    P_Consumer -->|"Step 1"| P_WF
    P_BoA -->|"Step 2"| P_Visa
    P_WF -->|"Step 2"| P_MC
    P_Visa -->|"Step 3"| P_Fed
    P_MC -->|"Step 3"| P_Fed
    P_Fed -->|"Step 4"| P_SWIFT
    P_SWIFT -->|"Routed"| P_UK
    P_SWIFT -->|"Routed"| P_EU
    P_SWIFT -->|"Routed"| P_CN
    P_SWIFT -->|"Routed"| P_JP
    P_SWIFT -->|"Routed"| P_BR
    P_SWIFT -->|"Routed"| P_US
    P_UK -->|"Step 5"| P_Merchant
    P_EU -->|"Step 5"| P_Merchant
    P_CN -->|"Step 5"| P_Merchant
    P_JP -->|"Step 5"| P_Merchant
    P_BR -->|"Step 5"| P_Merchant
    P_US -->|"Step 5"| P_Merchant
  end

  %% ─────────────────────────────────────────────────────────────────
  %% RIGHT SIDE — THE SOLUTION: Internet of Money Peer-to-Peer
  %% ─────────────────────────────────────────────────────────────────

  subgraph SOLUTION["✅  THE SOLUTION — Internet of Money (Peer-to-Peer)"]
    direction TB

    S_Ledger["🌐 Telcoin Network\nSingle Global Ledger"]

    S_eUSD["🇺🇸 eUSD\nUS Dollar"]
    S_eMXN["🇲🇽 eMXN\nMexican Peso"]
    S_eEUR["🇪🇺 eEUR\nEuro"]
    S_eGBP["🇬🇧 eGBP\nSterling"]
    S_eSGD["🇸🇬 eSGD\nSingapore Dollar"]
    S_eINR["🇮🇳 eINR\nIndian Rupee"]
    S_eBRL["🇧🇷 eBRL\nBrazilian Real"]
    S_eJPY["🇯🇵 eJPY\nJapanese Yen"]

    S_eUSD <-->|"Direct"| S_Ledger
    S_eMXN <-->|"Direct"| S_Ledger
    S_eEUR <-->|"Direct"| S_Ledger
    S_eGBP <-->|"Direct"| S_Ledger
    S_eSGD <-->|"Direct"| S_Ledger
    S_eINR <-->|"Direct"| S_Ledger
    S_eBRL <-->|"Direct"| S_Ledger
    S_eJPY <-->|"Direct"| S_Ledger

    S_eUSD <-->|"P2P"| S_eMXN
    S_eUSD <-->|"P2P"| S_eEUR
    S_eEUR <-->|"P2P"| S_eGBP
    S_eMXN <-->|"P2P"| S_eBRL
    S_eGBP <-->|"P2P"| S_eINR
    S_eSGD <-->|"P2P"| S_eJPY
    S_eBRL <-->|"P2P"| S_eSGD
    S_eINR <-->|"P2P"| S_eJPY
  end

  %% ─────────────────────────────────────────────────────────────────
  %% CLASS DEFINITIONS — Brand colors
  %% ─────────────────────────────────────────────────────────────────

  classDef problem fill:#1A0808,stroke:#EF4444,stroke-width:2px,color:#FFFFFF
  classDef problemHub fill:#2A0A0A,stroke:#EF4444,stroke-width:3px,color:#EF4444,font-weight:bold
  classDef problemCountry fill:#130808,stroke:#EF4444,stroke-width:1.5px,color:#C9CFED
  classDef solution fill:#081A1A,stroke:#14C8FF,stroke-width:2px,color:#FFFFFF
  classDef solutionHub fill:#0A1A2A,stroke:#14C8FF,stroke-width:3px,color:#14C8FF,font-weight:bold
  classDef solutionGreen fill:#081A10,stroke:#10B981,stroke-width:2px,color:#10B981
  classDef subgraphProblem fill:#0D0808,stroke:#EF4444,stroke-width:2px,color:#EF4444
  classDef subgraphSolution fill:#080D0D,stroke:#14C8FF,stroke-width:2px,color:#14C8FF

  %% Assign classes — Problem side
  class P_Consumer,P_BoA,P_WF,P_Visa,P_MC,P_Merchant problem
  class P_Fed,P_SWIFT problemHub
  class P_UK,P_EU,P_CN,P_JP,P_BR,P_US problemCountry

  %% Assign classes — Solution side
  class S_eMXN,S_eEUR,S_eGBP,S_eSGD,S_eINR,S_eBRL,S_eJPY solution
  class S_Ledger solutionHub
  class S_eUSD solutionGreen
```

---

## Key Design Notes for FigJam

**Colors used:**

| Token | Hex | Application |
|---|---|---|
| TEL Black | `#090920` | Canvas background |
| Tel Royal Blue | `#3642B2` | Subgraph borders, primary brand anchors |
| TEL Blue | `#14C8FF` | Solution nodes, connection lines |
| Problem Red | `#EF4444` | Problem nodes, hub nodes, error indicators |
| Solution Green | `#10B981` | eUSD node (Telcoin Digital Asset Bank) |
| Body text | `#C9CFED` | Node labels |
| Muted text | `#424761` | Supporting captions |

**Layout guidance for FigJam manual arrangement:**

After importing via Mermaid plugin:

1. Place the PROBLEM subgraph on the left, SOLUTION subgraph on the right
2. Add a vertical divider bar (`#3642B2`, 2px, full height) between the two halves
3. Add text label at top: "THE PROBLEM" in `#EF4444` / "THE SOLUTION" in `#14C8FF`
4. SWIFT node should be visually largest on the left — apply red outer glow in FigJam
5. Telcoin Network globe should be visually largest on the right — apply TEL Blue outer glow
6. Add frame: 1920 x 1080px, background `#090920`
7. Add hexagon pattern overlay at 4% opacity (brand motif)

**Callout annotations to add manually in FigJam:**

Left side (PROBLEM):
- Sticky note (red): "5-7 intermediaries per cross-border transaction"
- Sticky note (red): "Built on legacy COBOL infrastructure"
- Sticky note (red): "WSJ, Dec 25 2024: 'infrastructure not fit for purpose'"

Right side (SOLUTION):
- Sticky note (green): "Direct peer-to-peer settlement on-chain"
- Sticky note (blue): "Bank-issued stablecoins — regulated, chartered"
- Sticky note (blue): "Rep. Glenn Thompson, Feb 4 2025: 'Internet of value'"

---

## Standalone Left-Side Mermaid (Problem Only)

For use in isolation — presentations, reports, standalone export.

```mermaid
%%{
  init: {
    "theme": "base",
    "themeVariables": {
      "background": "#090920",
      "primaryColor": "#1A0808",
      "primaryTextColor": "#FFFFFF",
      "primaryBorderColor": "#EF4444",
      "lineColor": "#EF4444",
      "fontFamily": "Inter, sans-serif"
    }
  }
}%%

flowchart LR
  Consumer["👤 Consumer"] --> BoA["🏦 Bank of America"]
  Consumer --> WF["🏦 Wells Fargo"]
  BoA --> Visa["💳 Visa"]
  WF --> MC["💳 Mastercard"]
  Visa --> Fed["🏛 Federal Reserve / FedLine"]
  MC --> Fed
  Fed --> SWIFT["🌐 SWIFT"]
  SWIFT --> UK["🇬🇧 U.K."]
  SWIFT --> EU["🇪🇺 Europe"]
  SWIFT --> CN["🇨🇳 China"]
  SWIFT --> JP["🇯🇵 Japan"]
  SWIFT --> BR["🇧🇷 Brazil"]
  SWIFT --> USA["🇺🇸 U.S.A."]
  UK --> Merchant["🏪 Merchant"]
  EU --> Merchant
  CN --> Merchant
  JP --> Merchant
  BR --> Merchant
  USA --> Merchant

  classDef red fill:#1A0808,stroke:#EF4444,stroke-width:2px,color:#FFFFFF
  classDef hub fill:#2A0A0A,stroke:#EF4444,stroke-width:3px,color:#EF4444
  classDef country fill:#130808,stroke:#EF4444,stroke-width:1.5px,color:#C9CFED

  class Consumer,BoA,WF,Visa,MC,Merchant red
  class Fed,SWIFT hub
  class UK,EU,CN,JP,BR,USA country
```

---

## Standalone Right-Side Mermaid (Solution Only)

For use in isolation — presentations, reports, standalone export.

```mermaid
%%{
  init: {
    "theme": "base",
    "themeVariables": {
      "background": "#090920",
      "primaryColor": "#081A1A",
      "primaryTextColor": "#FFFFFF",
      "primaryBorderColor": "#14C8FF",
      "lineColor": "#14C8FF",
      "fontFamily": "Inter, sans-serif"
    }
  }
}%%

flowchart TB
  Ledger["🌐 Telcoin Network\nSingle Global Ledger"]

  eUSD["🇺🇸 eUSD"] <-->|"Direct"| Ledger
  eMXN["🇲🇽 eMXN"] <-->|"Direct"| Ledger
  eEUR["🇪🇺 eEUR"] <-->|"Direct"| Ledger
  eGBP["🇬🇧 eGBP"] <-->|"Direct"| Ledger
  eSGD["🇸🇬 eSGD"] <-->|"Direct"| Ledger
  eINR["🇮🇳 eINR"] <-->|"Direct"| Ledger
  eBRL["🇧🇷 eBRL"] <-->|"Direct"| Ledger
  eJPY["🇯🇵 eJPY"] <-->|"Direct"| Ledger

  eUSD <-->|"P2P"| eMXN
  eUSD <-->|"P2P"| eEUR
  eEUR <-->|"P2P"| eGBP
  eMXN <-->|"P2P"| eBRL
  eSGD <-->|"P2P"| eJPY
  eGBP <-->|"P2P"| eINR

  classDef blue fill:#081A1A,stroke:#14C8FF,stroke-width:2px,color:#FFFFFF
  classDef hub fill:#0A1A2A,stroke:#14C8FF,stroke-width:3px,color:#14C8FF
  classDef green fill:#081A10,stroke:#10B981,stroke-width:2px,color:#10B981

  class eMXN,eEUR,eGBP,eSGD,eINR,eBRL,eJPY blue
  class Ledger hub
  class eUSD green
```

---

## Source References

- Slide content: Telcoin Association investor/stakeholder deck, Slides 3-4
- Research file: `campaign/research/TELCOIN-RESEARCH.md`
- Brand colors: `strategy/BRAND-GUIDE.md`
- WSJ quote: Wall Street Journal, Dec 25 2024
- Thompson quote: U.S. Representative Glenn Thompson, Feb 4 2025
- HTML infographics: `campaign/execution/2026-03-18/infographic-problem-legacy-banking.html` and `infographic-solution-internet-of-money.html`
