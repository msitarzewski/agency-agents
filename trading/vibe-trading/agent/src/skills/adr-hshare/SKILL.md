---
name: adr-hshare
description: ADR/H-share/A-share cross-listing premium analysis — track pricing gaps between US-listed ADRs, HK-listed H-shares, and A-shares for arbitrage signals, dual-listing valuation, and delisting risk assessment.
category: flow
---
# ADR / H-Share / A-Share Cross-Listing Analysis

## Overview

Many Chinese companies are listed on multiple exchanges — A-shares in Shanghai/Shenzhen, H-shares in Hong Kong, and ADRs in the US. Pricing gaps between these listings create arbitrage opportunities and reveal market-specific sentiment differences. This skill provides frameworks for analyzing cross-listing premiums, identifying arbitrage signals, and assessing delisting risk for US-listed Chinese ADRs.

## Core Concepts

### 1. Cross-Listing Structures

| Structure | Description | Examples |
|-----------|-------------|---------|
| A + H dual-listed | Same company listed on both A-share and HK exchange | PetroChina (601857.SH / 0857.HK), ICBC (601398.SH / 1398.HK) |
| H + ADR dual-listed | HK-listed with US ADR | Alibaba (9988.HK / BABA), JD.com (9618.HK / JD) |
| A + H + ADR triple-listed | All three markets | China Life (601628.SH / 2628.HK / LFC) |
| HK primary + US secondary | Primary listing in HK, secondary ADR | Tencent (0700.HK / TCEHY OTC) |
| US primary → HK secondary | Originally US, added HK listing | Alibaba (BABA → 9988.HK), Baidu (BIDU → 9888.HK) |

### 2. AH Premium Analysis

**AH Premium = (A-share price / H-share price in CNY terms - 1) × 100%**

```python
def calculate_ah_premium(a_price_cny, h_price_hkd, usdcny, usdhkd):
    """Calculate AH premium for a dual-listed stock."""
    h_price_cny = h_price_hkd * (usdcny / usdhkd)  # Convert HKD to CNY
    ah_premium = (a_price_cny / h_price_cny - 1) * 100
    return ah_premium

# Example: PetroChina
# A-share: 8.50 CNY, H-share: 6.20 HKD
# USDCNY: 7.25, USDHKD: 7.82
# H in CNY: 6.20 * (7.25/7.82) = 5.75 CNY
# AH Premium: (8.50/5.75 - 1) * 100 = 47.8%
```

**AH Premium signal interpretation:**

| Premium Level | Interpretation | Action |
|--------------|----------------|--------|
| >50% | Extreme A-share premium; A-share speculative bubble or H-share extreme undervaluation | Strong: buy H, sell/avoid A |
| 30-50% | Elevated premium; normal for high-retail-participation names | Moderate: favor H if fundamentals same |
| 10-30% | Normal range for most AH pairs | Neutral; no strong arbitrage signal |
| 0-10% | Compressed premium; A-shares relatively cheap | Unusual; investigate catalyst |
| <0% | H-share premium over A-share | Very rare; usually near-term event-driven |

**Structural drivers of AH premium:**
1. **Liquidity premium**: A-shares have much higher retail participation and turnover → liquidity premium
2. **Access premium**: A-shares were historically hard for foreigners to access → scarcity premium
3. **Currency expectations**: CNY depreciation expectations widen the premium
4. **Regulatory arbitrage**: different trading rules (T+1 in A-shares vs T+0 in HK)
5. **Investor composition**: A-share retail speculative premium vs HK institutional valuation discipline

### 3. ADR Premium/Discount Analysis

**ADR premium = (ADR price in USD / HK equivalent in USD - 1) × 100%**

```python
def calculate_adr_premium(adr_price_usd, hk_price_hkd, adr_ratio, usdhkd):
    """
    Calculate ADR premium over HK listing.
    adr_ratio: number of HK shares per 1 ADR (e.g., BABA: 1 ADR = 8 HK shares)
    """
    hk_equivalent_usd = (hk_price_hkd * adr_ratio) / usdhkd
    premium = (adr_price_usd / hk_equivalent_usd - 1) * 100
    return premium

# Example: Alibaba
# BABA ADR: $85.00, 9988.HK: HKD 82.50
# ADR ratio: 1 ADR = 8 HK shares
# HK equivalent: (82.50 * 8) / 7.82 = $84.40
# ADR premium: (85.00/84.40 - 1) * 100 = 0.71%
```

**Key ADR conversion ratios:**

| Company | ADR Ticker | HK Ticker | ADR Ratio (HK:ADR) | ADR Exchange |
|---------|-----------|-----------|---------------------|--------------|
| Alibaba | BABA | 9988.HK | 8:1 | NYSE |
| JD.com | JD | 9618.HK | 2:1 | NASDAQ |
| Baidu | BIDU | 9888.HK | 8:1 | NASDAQ |
| Bilibili | BILI | 9626.HK | 1:1 | NASDAQ |
| NIO | NIO | 9866.HK | 1:1 | NYSE |
| XPeng | XPEV | 9868.HK | 2:1 | NYSE |
| Li Auto | LI | 2015.HK | 2:1 | NASDAQ |
| NetEase | NTES | 9999.HK | 5:1 | NASDAQ |
| Trip.com | TCOM | 9961.HK | 1:1 | NASDAQ |
| Pinduoduo | PDD | N/A (US-only) | N/A | NASDAQ |

**ADR premium drivers:**
- US trading hours sentiment (earnings releases, macro data during US hours)
- US-specific regulatory events (SEC, PCAOB audits)
- Liquidity premium (ADR often more liquid for global funds)
- Time zone gap: ADR closes at HK's open → overnight gap creates premium/discount

### 4. Delisting Risk Assessment

**HFCAA (Holding Foreign Companies Accountable Act) framework:**

Since 2022, PCAOB gained access to audit workpapers of Chinese companies. Key risks:

| Risk Level | Criteria | Impact |
|------------|----------|--------|
| Low | PCAOB inspection completed, no issues | ADR status stable |
| Medium | PCAOB inspection completed, deficiencies noted | Monitor for resolution |
| High | PCAOB access revoked or restricted | 3-year delisting countdown activated |
| Critical | On SEC "identified issuer" list for 3 consecutive years | Forced delisting |

**Delisting risk indicators:**
```python
delisting_risk_factors = {
    "pcaob_status": "inspected",     # inspected / pending / blocked
    "sec_identified_years": 0,        # 0, 1, 2, or 3 (3 = delist)
    "has_hk_listing": True,           # Backup listing reduces impact
    "hk_listing_type": "primary",     # primary (can be in Connect) vs secondary
    "vie_structure": True,            # Variable Interest Entity adds legal risk
    "state_owned": False,             # SOE status adds geopolitical risk
}

# Companies with HK primary listing (BABA, JD, BIDU, NTES, etc.) have
# a safety net if US delisting occurs → fungible conversion ADR → HK shares
# Companies with US-only listing (PDD until HK listing) face higher risk
```

### 5. Cross-Listing Arbitrage Strategies

**Strategy 1: AH Premium Mean-Reversion**
```python
# When AH premium for a specific stock diverges significantly from its historical average
ah_premium_current = 45  # current premium
ah_premium_mean_12m = 35  # 12-month average
ah_premium_std = 8        # standard deviation

z_score = (ah_premium_current - ah_premium_mean_12m) / ah_premium_std

if z_score > 2.0:
    signal = "fade_premium"  # A-share overvalued vs H; buy H, avoid A
elif z_score < -2.0:
    signal = "buy_premium"   # A-share undervalued vs H; buy A, avoid H
else:
    signal = "neutral"
```

**Strategy 2: ADR-HK Intraday Arbitrage**
- During overlapping trading hours (HK morning = US pre-market via ADR), price gaps can appear
- Professional arbitrageurs use ADR↔HK fungible conversion to capture these gaps
- For research purposes: tracking ADR premium trend indicates which market is leading sentiment

**Strategy 3: Event-Driven Cross-Listing**
- New HK listing announcement (US→HK): ADR typically dips 2-5% on dilution fear, then recovers
- MSCI / FTSE index inclusion of HK listing: triggers passive fund buying in HK
- Stock Connect inclusion (HK primary listing eligible): triggers mainland institutional buying

## Data Access

```python
import yfinance as yf

# Fetch ADR and HK prices simultaneously
baba_adr = yf.download("BABA", start="2025-01-01", end="2026-03-30", progress=False)
baba_hk = yf.download("9988.HK", start="2025-01-01", end="2026-03-30", progress=False)

# For A+H pairs
petrochina_a = yf.download("601857.SS", start="2025-01-01", end="2026-03-30", progress=False)
petrochina_h = yf.download("0857.HK", start="2025-01-01", end="2026-03-30", progress=False)

# FX rates for premium calculation
cny = yf.download("CNY=X", start="2025-01-01", end="2026-03-30", progress=False)  # USD/CNY
hkd = yf.download("HKD=X", start="2025-01-01", end="2026-03-30", progress=False)  # USD/HKD

# AH Premium Index (HSAHP)
# Not directly on yfinance; use Hang Seng website or Tushare
```

## Output Format

```
## Cross-Listing Analysis — [Company Name]

### Listing Structure
- **A-share**: [code] @ [price CNY]
- **H-share**: [code] @ [price HKD]
- **ADR**: [ticker] @ [price USD] (ratio: X HK shares = 1 ADR)

### Premium/Discount
- **AH Premium**: [X%] (12m avg: X%, z-score: X.X)
- **ADR-HK Premium**: [X%] (5d avg: X%)
- **Direction**: [AH premium widening / narrowing / stable]

### Valuation Comparison
| Metric | A-share | H-share | ADR |
|--------|---------|---------|-----|
| PE (TTM) | XX.X | XX.X | XX.X |
| PB | X.X | X.X | X.X |
| Dividend yield | X.X% | X.X% | X.X% |

### Delisting Risk (ADR)
- **PCAOB status**: [inspected / pending]
- **SEC identified years**: [0/1/2/3]
- **HK backup**: [yes-primary / yes-secondary / no]
- **Risk level**: [low / medium / high / critical]

### Arbitrage Signal
- **AH premium z-score**: [X.X] → [fade premium / neutral / buy premium]
- **Best market to buy**: [A / H / ADR] — rationale
- **Catalyst**: [index inclusion, Connect eligibility, earnings]

### Investment Implication
- **Preferred listing**: [H-share / ADR / A-share] for new position
- **Risk**: [delisting, FX, regulatory, liquidity]
```

## Notes

- AH premium arbitrage is not freely executable: A-shares and H-shares are NOT fungible (no direct conversion), so true arbitrage requires separate capital pools
- ADR↔HK conversion IS possible for most dual-listed names (via depositary bank), but takes 2-3 business days and involves fees
- Currency risk (CNY, HKD, USD) is a major driver of cross-listing premiums; always hedge or account for FX when comparing
- VIE (Variable Interest Entity) structure adds a layer of legal risk for many Chinese ADRs; this is a structural risk, not a trading signal
- Stock Connect eligibility requirements mean not all HK-listed Chinese companies are accessible to mainland investors
- This framework is for research purposes only and does not constitute investment advice
