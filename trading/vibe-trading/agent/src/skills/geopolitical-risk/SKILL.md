---
name: geopolitical-risk
description: "Geopolitical risk analysis: quantify crisis signals, identify precursors, and build event-driven strategies for war, sanctions, and supply disruption scenarios."
category: tool
---

# Geopolitical Risk Analysis

## Overview

Quantify geopolitical risk signals, identify crisis precursors, and build event-driven strategies that convert narratives such as "war / conflict / sanctions / supply disruption" into actionable multi-asset allocation decisions.

---

## Core Analytical Framework

### 1. Risk Layering Model

```
Layer 1: Structural risk (long-lasting, slow-moving)
  └── Great-power rivalry, alliance structures, nuclear deterrence balance

Layer 2: Situational risk (cyclical escalation, monthly / quarterly scale)
  └── Military exercises, election cycles, sanctions escalation, diplomatic friction

Layer 3: Event risk (sudden shocks, daily / hourly scale)
  └── Military action, assassination, sanctions announcements, nuclear tests
```

### 2. Five Dimensions of Risk Assessment

| Dimension | Description | Quantitative Proxy |
|------|------|-------------|
| **Intensity** | Severity of conflict / sanctions | GPR Index percentile |
| **Persistence** | Expected duration of the crisis | Futures curve contango / backwardation |
| **Transmission** | Spillover into supply chains / finance | CDS spread widening, VIX jump magnitude |
| **Predictability** | Whether the event is already priced in | Option implied volatility skew |
| **Reversibility** | Whether the situation can be resolved through negotiation | Speed of reversal in news sentiment |

---

## Monitoring the Six Major Global Geopolitical Hotspots

### 1. Strait of Hormuz — Oil Transport Chokepoint

**Strategic significance**
- Roughly 20% of global oil supply (about 17 million barrels/day) and 20% of LNG passes through it
- Iran has the ability to disrupt the strait through mines, naval assets, and shore-based missiles
- It is the only export route for Gulf states such as Saudi Arabia, the UAE, Kuwait, and Iraq

**Risk triggers**
- Escalation in U.S.-Iran tensions, such as failed nuclear talks or tighter sanctions
- Tankers being seized or attacked
- Iranian blockade drills during military exercises

**Key monitoring indicators**
```python
# Proxy indicators
- Brent-WTI spread widening (signal of regional supply stress)
- Persian Gulf tanker insurance rates (Lloyd's H&M quotes)
- UAE dirham NDF (depreciates under stress)
- Israeli shekel volatility
- Relative strength of VanEck Oil Services ETF (OIH) vs XLE
```

**Asset impact direction**
- Bullish: crude oil, LNG, shipping stocks (BDRY/FRO), defense stocks (LMT/RTX)
- Bearish: airlines (DAL/UAL), petrochemical refiners, emerging-market importers such as INR and KRW

---

### 2. Taiwan Strait — Core of the Semiconductor Supply Chain

**Strategic significance**
- TSMC accounts for roughly 90% of global advanced-node capacity below 5nm
- Taiwan produces about 65% of the world's semiconductors
- It sits on the main southbound route linking Northeast Asia and Southeast Asia

**Risk triggers**
- Larger-scale Chinese military exercises, especially blockade drills
- U.S. arms sales to Taiwan or high-level official visits
- Major policy changes in cross-strait relations

**Key monitoring indicators**
```python
# Proxy indicators
- Abnormal weakness in the Philadelphia Semiconductor Index (SOX)
- TSM ADR (TSM) premium / discount in the U.S. market
- Taiwan CDS spreads
- TWD NDF depreciation under stress
- KOSPI, given Korea's semiconductor linkage
- U.S.-listed Chinese ADRs / Hong Kong Hang Seng Tech Index
```

**Asset impact direction**
- Bullish: Intel / GlobalFoundries as substitute capacity providers, defense stocks, JPY as a haven
- Bearish: Apple / NVIDIA / AMD / Qualcomm as TSMC clients, TSM ADR, Samsung Electronics
- Extreme scenario: global semiconductor shortage leading to collapse across auto and consumer-electronics supply chains

**Supply chain substitution timeline**
```
3-6 months: inventory drawdown, sharp price spikes
6-18 months: partial substitution by Samsung / Intel IDM advanced capacity
2-4 years: ramp-up from TSMC Arizona and Kumamoto Japan
5+ years: Mainland China's independent advanced process catch-up, with major uncertainty
```

---

### 3. Red Sea / Suez Canal — Europe-Asia Trade Artery

**Strategic significance**
- The Suez Canal carries about 12% of global trade volume and 30% of container shipping
- The alternative route around the Cape of Good Hope adds 10-14 days and raises cost by 15-25%
- Houthi forces in Yemen threaten the Bab el-Mandeb chokepoint

**Risk triggers** (already validated by the 2024 Houthi attacks)
- Intensified attacks on merchant vessels by Houthi forces
- Israel-Gaza escalation spilling across the region
- Political instability in Eritrea or Somalia

**Key monitoring indicators**
```python
# Proxy indicators
- Daily changes in the Baltic Dry Index (BDI)
- SCFI Shanghai Containerized Freight Index
- Share prices of Maersk and other container shipping companies
- Share of AIS-tracked vessels rerouting via the Cape of Good Hope (>30% is high alert)
- European TTF natural gas prices, given Red Sea LNG exposure
```

**Asset impact direction**
- Bullish: shipping stocks (ZIM/MAERSK/COSCO), tankers rerouting around the Cape (FRO/STNG)
- Bearish: European manufacturers facing supply-chain delays, inflation-sensitive sectors
- Lag effect: higher freight rates → higher global CPI → tighter rate expectations

---

### 4. Russia-Ukraine Conflict — Energy and Food Security

**Strategic significance**
- Russia is the world's largest natural gas exporter and second-largest crude exporter
- Ukraine is a major global grain exporter (wheat / corn / sunflower oil)
- The war has already driven a permanent restructuring of Europe's energy mix

**Ongoing risk points**
- Escalation in nuclear rhetoric, a major tail-risk driver
- Sanctions expanding to third parties, forcing countries like China and India to choose sides
- Continued attacks on Ukrainian infrastructure such as the power grid and ports

**Key monitoring indicators**
```python
# Proxy indicators
- European TTF natural gas futures
- Ukrainian sovereign CDS spreads
- RUB/USD exchange rate under sanctions pressure
- Chicago wheat futures (ZW)
- European power prices, e.g. Germany EEX Baseload
- Russian ETF trading status (RSX liquidated; use substitutes)
```

**Sanctions transmission-chain analysis**
```
Sanctions announcement
  ├── Financial sanctions → SWIFT cutoff → cross-border settlement disruption → emerging-market debt crisis
  ├── Energy sanctions → European gas spike → industrial energy costs → eurozone recession
  ├── Export controls → Russia semiconductor / military shortages → weaker war sustainability
  └── Grain blockade → Middle East / Africa food stress → political instability → migration pressure
```

---

### 5. South China Sea — Shipping Lanes and Rare-Earth Competition

**Strategic significance**
- Around one-third of global trade value, roughly USD 3.4 trillion annually, passes through the South China Sea
- China controls about 60% of global rare-earth supply, even more in refining
- Territorial frictions between China and the Philippines / Vietnam persist

**Risk triggers**
- China declaring an Air Defense Identification Zone (ADIZ)
- Clashes around flashpoints such as Sabina Shoal or Scarborough Shoal
- Rare-earth export bans or quota cuts as a technology retaliation tool against the U.S.

**Key monitoring indicators**
```python
# Proxy indicators
- Chinese rare-earth futures prices (permanent magnets / praseodymium-neodymium oxide)
- Philippine peso volatility
- Vietnam industrial park REITs / ETFs
- MP Materials (MP) share price as a substitute rare-earth beneficiary
- Share prices of Chinese shipping companies
```

**Asset impact direction**
- Bullish: rare-earth miners such as MP Materials and Australia's Lynas, Japanese trading houses with inventories
- Bearish: EV / permanent-magnet motor supply chains, Chinese ADRs

---

### 6. Korean Peninsula — Regional Security Shock Source

**Strategic significance**
- North Korea possesses nuclear weapons and ICBMs, making it a non-trivial tail risk
- Strategic cooperation among China, Russia, and North Korea has deepened, including artillery supply during the Russia-Ukraine war
- South Korea is a major global exporter of semiconductors, shipbuilding, and autos

**Risk triggers**
- Nuclear or missile tests, especially ICBM launches
- North Korea announcing strategic changes such as "nuclear sharing"
- Political crises in South Korea affecting U.S. force deployment

**Key monitoring indicators**
```python
# Proxy indicators
- KRW/USD volatility spike
- KOSPI decline
- South Korean CDS spreads
- JPY safe-haven inflows (JPY/USD strength)
- ADR prices of Samsung / SK Hynix
```

---

## Quantitative Framework for Geopolitical Risk

### GPR Index (Caldara & Iacoviello)

**Definition and source**
- Built by Fed economists Dario Caldara and Matteo Iacoviello
- Computed from war / terror / military-related word frequency in major newspapers globally
- Monthly data back to 1900, covering global and country-specific series
- Official data: https://www.matteoiacoviello.com/gpr.htm

**Index taxonomy**
```
GPR: overall geopolitical risk
GPRT: geopolitical threats (forward-looking)
GPRA: geopolitical acts (events already realized)
GPR_country: country-level sub-index
```

**Python example**
```python
import pandas as pd
import requests

def load_gpr_index():
    """Load the official GPR Index data.

    Returns:
        pd.DataFrame: Monthly GPR data with columns such as GPR, GPRT, and GPRA.
    """
    url = "https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls"
    df = pd.read_excel(url, index_col=0, parse_dates=True)
    return df

def gpr_signal(df, window=12, threshold=1.5):
    """Generate abnormal GPR signals.

    Args:
        df: DataFrame containing GPR data
        window: Rolling mean window in months
        threshold: Z-score trigger threshold in standard deviations

    Returns:
        pd.Series: Boolean signal where True means high-risk state
    """
    gpr = df["GPR"]
    rolling_mean = gpr.rolling(window).mean()
    rolling_std = gpr.rolling(window).std()
    z_score = (gpr - rolling_mean) / rolling_std
    return z_score > threshold
```

---

### Calculating War Risk Premiums

**Oil war premium**
```python
def oil_war_premium(spot_price, mean_5y_price, supply_disruption_prob,
                    disruption_magnitude_pct):
    """Estimate the war-risk premium embedded in crude oil.

    Method:
        A simplified model based on expected supply-disruption value.

    Args:
        spot_price: Current spot price in USD/bbl
        mean_5y_price: Five-year average price as the "no-risk" baseline
        supply_disruption_prob: Probability of supply disruption in [0, 1]
        disruption_magnitude_pct: Price impact of disruption in [0, 1]

    Returns:
        float: Estimated war premium in USD/bbl
    """
    expected_disruption_premium = (
        mean_5y_price * disruption_magnitude_pct * supply_disruption_prob
    )
    observed_premium = spot_price - mean_5y_price
    return max(0, min(observed_premium, expected_disruption_premium))
```

**Gold safe-haven premium**
```python
def gold_geopolitical_premium(gold_price, real_yield_10y, usd_index):
    """Decompose the geopolitical premium component in gold prices.

    Args:
        gold_price: Spot gold price in USD/oz
        real_yield_10y: 10-year real yield in percent
        usd_index: DXY index

    Returns:
        float: Geopolitical premium as the residual component
    """
    import numpy as np
    # Gold fundamentals: real rates (negative) + USD (negative)
    # Linear approximation:
    # Gold ≈ α - β1*RealYield - β2*DXY + ε (geopolitical premium)
    # β1 ≈ 800, β2 ≈ 15 are rough historical estimates that should be updated
    fundamental_value = 2000 - 800 * real_yield_10y - 15 * (usd_index - 100)
    return gold_price - fundamental_value
```

---

### Supply-Chain Disruption Probability Assessment

**Bayesian update framework**
```python
def update_disruption_probability(prior_prob, new_event_severity, base_rate=0.05):
    """Update supply-chain disruption probability using a new event.

    This is a simplified Bayesian update that adjusts the prior
    using the severity of the new event.

    Args:
        prior_prob: Prior disruption probability
        new_event_severity: Event severity in [0, 1]
            0.0 = diplomatic friction
            0.3 = military standoff
            0.6 = local conflict
            1.0 = full-scale war
        base_rate: Historical annualized baseline disruption rate

    Returns:
        float: Updated disruption probability
    """
    # Likelihood ratio: how much more likely the event is before a real disruption
    # than in a non-disruption state
    likelihood_ratio = 1 + 9 * new_event_severity  # 1x ~ 10x
    posterior = (prior_prob * likelihood_ratio) / (
        prior_prob * likelihood_ratio + (1 - prior_prob)
    )
    return posterior
```

---

### Quantifying Sanctions Transmission Chains

**Sanctions intensity scorecard**

| Sanction Type | Intensity Score | Typical Asset Shock | Expected Duration |
|----------|--------|-------------|-------------|
| Targeted sanctions on people / entities | 1-2 | <0.5% | Short-lived |
| Sector-level export controls | 3-4 | 1-3% | Several months |
| SWIFT cutoff | 7-8 | 5-15% | Long-lasting |
| Full-scale economic sanctions | 9-10 | 10-30% | Structural |
| Oil embargo | 8-9 | Crude +10-30% | Medium-term |

---

## Asset-Class Impact Mapping

### Energy

| Asset | Hormuz | Russia-Ukraine | Red Sea | Notes |
|------|---------|------|------|------|
| Brent crude | +++ shock | ++ persistent | + mild | Primary geopolitical-risk asset |
| WTI crude | ++ shock | ++ persistent | + mild | Widens against Brent |
| Europe TTF gas | ++ | +++ | + | Cost of replacing Russian gas |
| LNG futures | +++ | ++ | ++ | Red Sea disruption matters for Asian LNG |
| Relevant ETFs | XLE, OIH, UNG | | | |

### Precious Metals (Safe Haven Function)

```
Gold (GLD/GC): geopolitical shock → immediate rally, but persistence depends on real-rate direction
Silver (SLV/SI): industrial exposure dilutes safe-haven behavior and raises volatility
Palladium / platinum: Russia is a major producer, so sanctions hit supply directly
```

**Empirical patterns (2001-2024)**
- A 1-standard-deviation rise in GPR implies about +1.2% expected gold return over a 1-month window
- On day one of major shocks such as Pearl Harbor, 9/11, or Russia-Ukraine, gold rose roughly 3-8%
- Within 60 days, around 50-70% of the geopolitical premium mean-reverts

### Agriculture

| Asset | Russia-Ukraine Conflict | South China Sea Blockade | Driver |
|------|---------|---------|---------|
| Wheat (ZW) | +++ | + | Russia + Ukraine account for about 30% of exports |
| Corn (ZC) | ++ | + | Ukraine is a major exporter |
| Sunflower oil | +++ | - | Ukraine accounts for roughly 50% globally |
| Soybeans (ZS) | + | + | China import demand |

### Semiconductors / Technology

```
Estimated impact under a Taiwan Strait crisis:
- Mild military tension (drills): SOX -5% to -10%
- Blockade drill (1 month): SOX -15% to -25%
- Actual military conflict: SOX -40% to -60% (no true historical analogue)

Beneficiaries through substitution:
- Intel (INTC): IDM model with U.S.-based capacity
- GlobalFoundries (GFS): U.S. / Europe / Singapore capacity
- Samsung, though Korea itself is also a geopolitical risk zone
```

### Shipping / Logistics

```
Key ETFs and stocks:
- BDRY: bulk-shipping freight ETF tracking BDI, highly sensitive to Red Sea / Hormuz shocks
- ZIM: Israeli container shipper, directly exposed to Red Sea risk
- FRO (Frontline): tanker beneficiary of Hormuz risk
- STNG (Scorpio Tankers): benefits from rerouting around the Red Sea
- MAERSK.B: container-shipping leader that benefits from freight spikes during crises
```

### Defense

```
U.S. defense ETFs: ITA (iShares), XAR (SPDR)

Single-stock beneficiaries of geopolitical risk:
- LMT (Lockheed Martin): F-35, missile systems
- RTX (Raytheon): air-defense systems such as Patriot
- NOC (Northrop Grumman): B-21 bomber, nuclear systems
- BA (Boeing): military exposure, though commercial aviation can be hurt by geopolitics

Historical pattern:
Higher geopolitical risk → faster defense budget approvals → effect shows up with a 6-12 month lag
```

### FX (Safe-Haven Currencies)

```
Capital flows during crises:
Risk currencies (AUD/NZD/MXN/KRW/BRL) → outflows
Safe-haven currencies (JPY/CHF/USD) ← inflows

JPY:
- Net-creditor-nation status + repatriation effect
- Historical crisis moves: +1% to +3% vs USD

CHF:
- Neutral country + European financial center
- Major crises: +2% to +5% vs EUR

USD:
- Global reserve currency and final safe haven during crises
- But if the U.S. homeland is directly attacked, USD can weaken instead

Note: High-carry funding currencies such as TRY and ARS tend to suffer the most when global risk aversion rises
```

---

## Event-Driven Strategy Framework

### Phase 1: Positioning Before the Crisis (Early-Warning Signal Detection)

**Signal classification system**

```python
SIGNAL_LEVELS = {
    "GREEN": {
        "desc": "Normal geopolitical risk level",
        "gpr_percentile": (0, 50),
        "action": "Standard allocation, no special hedge required"
    },
    "YELLOW": {
        "desc": "Risk rising, watch for escalation",
        "gpr_percentile": (50, 75),
        "action": "Small long-gold position, reduce high-risk asset exposure by 10%"
    },
    "ORANGE": {
        "desc": "High-risk state, potential shock approaching",
        "gpr_percentile": (75, 90),
        "action": "Add safe-haven assets, buy OTM protective options, bullish on oil"
    },
    "RED": {
        "desc": "Extreme risk, crisis may break out",
        "gpr_percentile": (90, 100),
        "action": "Maximize defensive positioning, hold cash / gold / Treasuries, short high-risk assets"
    }
}
```

**Early-warning checklist**
```
Diplomatic:
  [ ] Embassy closures / downgrades
  [ ] Diplomat expulsions
  [ ] UN emergency meeting called
  [ ] Escalation in joint statements by multiple countries

Military:
  [ ] Large-scale exercises (>50,000 personnel)
  [ ] Carrier strike group forward deployment
  [ ] Higher readiness announcements
  [ ] Missile / nuclear system release orders

Financial:
  [ ] Target-country CDS spread breaks historical highs
  [ ] Exchange rate devaluation >3% in one week
  [ ] Sharp decline in FX reserves
  [ ] Accelerating capital flight
```

---

### Phase 2: Trading During the Crisis

**Volatility trading framework**
```python
def crisis_vol_strategy(underlying, option_chain):
    """Volatility trading framework during crises.

    Crisis outbreaks usually cause:
    1. A short-term VIX spike (long VIX futures / options)
    2. Inversion in the IV term structure (front month > back month)
    3. Steeper put skew

    Args:
        underlying: Underlying asset ticker
        option_chain: Option chain data

    Returns:
        dict: Recommended strategies and sizing guidance
    """
    strategies = {
        "long_vix_futures": {
            "instrument": "Front-month VX futures",
            "trigger": "VIX < 20 and GPR > 75th percentile",
            "target": "VIX spikes to 35-50",
            "stop": "VIX falls 15% below entry"
        },
        "backspread": {
            "instrument": f"Buy OTM Put + sell ATM Put on {underlying}",
            "trigger": "Implied volatility is at a historical low",
            "profit_zone": "Large drop > 10%"
        },
        "calendar_spread": {
            "instrument": "Sell near-month ATM + buy far-month ATM",
            "trigger": "Exit when term-structure inversion becomes excessive",
            "profit_zone": "Volatility mean reversion"
        }
    }
    return strategies
```

**Crisis allocation matrix**
```
Crisis type        | Gold | Oil | Defense | JPY | Treasuries | EM
Energy conflict    | ++   | +++ | ++      | +   | +          | ---
Nuclear escalation | +++  | +   | +       | +++ | +++        | ---
Sanctions / trade  | +    | +   | +       | +   | +          | --
Food crisis        | +    | 0   | 0       | 0   | +          | -- (importers)
Sea blockade       | +    | ++  | +       | +   | +          | -
```

---

### Phase 3: Mean Reversion After the Crisis

**Recovery time of historical events**

| Event | S&P 500 Max Drawdown | Days to Recover Prior High | Max Oil Rally | Max Gold Rally |
|------|----------------|--------------|-------------|-------------|
| 9/11 attacks (2001) | -11.6% | 31 days | -35% (demand collapse) | +5% |
| Iraq War (2003) | -3% | <30 days | +40% (within 1 year) | +15% |
| Russia-Georgia War (2008) | <-5% | <30 days | Overlapped with financial crisis | +10% |
| Crimea (2014) | -1% | 7 days | -5% | +3% |
| Full invasion of Ukraine (2022) | -3% briefly | <20 days | +40% (within 3 months) | +5% |

**Core patterns**
```
1. The initial equity shock from geopolitical events usually recovers within 30 days unless recession hits simultaneously
2. Energy / commodities effects last longer because supply-side changes are structural
3. Go long the most damaged assets once the crisis de-escalates and mean reversion starts
4. Sell safe-haven assets that exploded during the crisis, especially gold after tension fades
```

**Mean-reversion signals**
```python
REVERSION_SIGNALS = [
    "Ceasefire agreement signed / negotiations announced",
    "Energy / grain exports resume, confirmed by shipping data",
    "Target-country CDS spreads retrace >20% from the peak",
    "GPR Index falls >30% from the peak",
    "VIX drops below 20 after peaking",
    "Safe-haven currencies such as JPY / CHF begin weakening"
]
```

---

## Data Sources and APIs

### 1. GPR Index (Most Important Quantitative Dataset)

```python
# Official download, free, monthly updates
GPR_DATA_URL = "https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls"

# High-frequency daily GPR based on Twitter / news
# Access request required: https://www.policyuncertainty.com/gpr_daily.html

# Related paper:
# Caldara & Iacoviello (2022), "Measuring Geopolitical Risk"
# American Economic Review, 112(4): 1194-1225
```

### 2. GDELT Global Event Database (Free)

```python
# GDELT 2.0 provides global news-event data updated every 15 minutes
# Includes the CAMEO event code system for military / diplomatic / conflict classification

def query_gdelt_events(country_code, event_type, start_date, end_date):
    """Query GDELT geopolitical event data.

    GDELT BigQuery table: gdelt-bq.gdeltv2.events
    CAMEO root codes: 14=protest, 18=assault, 19=fight, 20=mass violence

    Args:
        country_code: FIPS country code, e.g. 'CH' for China, 'RS' for Russia
        event_type: CAMEO root code
        start_date: Start date in YYYY-MM-DD
        end_date: End date in YYYY-MM-DD

    Returns:
        pd.DataFrame: Event records
    """
    from google.cloud import bigquery
    client = bigquery.Client()

    query = f"""
    SELECT SQLDATE, Actor1CountryCode, Actor2CountryCode,
           EventCode, GoldsteinScale, NumMentions, AvgTone
    FROM `gdelt-bq.gdeltv2.events`
    WHERE (Actor1CountryCode = '{country_code}'
           OR Actor2CountryCode = '{country_code}')
      AND EventRootCode = '{event_type}'
      AND SQLDATE BETWEEN '{start_date.replace('-','')}'
                      AND '{end_date.replace('-','')}'
    ORDER BY SQLDATE DESC
    """
    return client.query(query).to_dataframe()
```

### 3. ACLED Armed Conflict Location & Event Data

```python
# Armed Conflict Location & Event Data Project
# https://acleddata.com/
# Covers 100+ countries and is free for approved academic access

ACLED_API_BASE = "https://api.acleddata.com/acled/read"

def fetch_acled_events(country, start_date, end_date, api_key):
    """Fetch ACLED armed-conflict event data.

    Args:
        country: Country name in English
        start_date: Start date in YYYY-MM-DD
        end_date: End date in YYYY-MM-DD
        api_key: ACLED API key

    Returns:
        pd.DataFrame: Conflict event data
    """
    import requests
    import pandas as pd

    params = {
        "key": api_key,
        "email": "your@email.com",
        "country": country,
        "event_date": f"{start_date}|{end_date}",
        "event_date_where": "BETWEEN",
        "export_type": "json"
    }
    resp = requests.get(ACLED_API_BASE, params=params)
    return pd.DataFrame(resp.json()["data"])
```

### 4. Real-Time News Sentiment Analysis

```python
# Option A: Use the Jina Reader API integrated in the project through read_url
def analyze_geopolitical_news(query: str) -> dict:
    """Read news through Jina and analyze geopolitical-risk sentiment.

    Use together with the agent's read_url tool.

    Args:
        query: Search keywords

    Returns:
        dict: Sentiment-analysis result
    """
    # Recommended news sources:
    news_sources = [
        "https://www.reuters.com/world/",
        "https://www.bloomberg.com/politics",
        "https://www.ft.com/world",
        "https://www.foreignpolicy.com/"
    ]
    # Use read_url to fetch content, then pass it to the LLM to extract risk events

# Option B: Event Registry API (paid, structured news)
# https://eventregistry.org/
# Supports filtering by country / topic / time and returns standardized events

# Option C: VADER / FinBERT sentiment analysis
# Score geopolitical news sentiment and build high-frequency signals
```

### 5. Other Practical Data Sources

```python
DATA_SOURCES = {
    "oil_tanker_tracking": {
        "desc": "Crude oil / LNG vessel AIS tracking",
        "source": "MarineTraffic API (paid) / VesselFinder (limited free)",
        "use_case": "Real-time monitoring of traffic through Hormuz / the Red Sea"
    },
    "un_vote_data": {
        "desc": "UN General Assembly / Security Council voting records",
        "source": "UN Data API (free)",
        "use_case": "Track changes in great-power alignment"
    },
    "arms_transfer": {
        "desc": "Arms transfers and military aid data",
        "source": "SIPRI Arms Transfers Database (free)",
        "use_case": "Estimate conflict-escalation probability"
    },
    "nuclear_risk": {
        "desc": "Real-time nuclear-risk assessment",
        "source": "Bulletin of the Atomic Scientists Doomsday Clock",
        "use_case": "Tail-risk monitoring"
    },
    "commodity_futures": {
        "desc": "Commodity futures prices, including geopolitical premium",
        "source": "Integrated in this project: Tushare commodity futures / OKX crypto",
        "use_case": "Estimate war premium"
    }
}
```

---

## Application Scenarios

### Scenario 1: Geopolitical Risk Dashboard (Monthly Refresh)

```
Run at the start of each month:
1. Download the latest GPR Index data
2. Calculate CDS spread changes for each hotspot country
3. Analyze tanker insurance rates
4. Summarize counts of high-intensity GDELT conflict events
5. Output a composite risk score (0-100) plus allocation guidance
```

### Scenario 2: Rapid Event Shock Assessment

```
Trigger:
Major geopolitical event breaks out, such as a missile strike or sanctions announcement

Execution flow:
1. Identify the event type and intensity (0-10)
2. Map the affected asset classes
3. Estimate the short-term price shock range
4. Identify hedging instruments (options / futures / ETFs)
5. Set stop-loss rules and position size
```

### Scenario 3: Quarterly Risk Stress Testing

```python
# Geopolitical scenario stress tests for a portfolio
SCENARIOS = {
    "hormuz_blockade_30d": {
        "oil_price_shock": +40,
        "gold_shock": +8,
        "equity_shock": -12,
        "usd_shock": +3,
        "description": "30-day Strait of Hormuz blockade scenario"
    },
    "taiwan_conflict_mild": {
        "semioconductor_shock": -25,
        "gold_shock": +5,
        "equity_shock": -15,
        "jpy_shock": +8,
        "description": "Mild Taiwan Strait military conflict scenario"
    },
    "russia_gas_cutoff": {
        "eu_natgas_shock": +80,
        "eu_equity_shock": -20,
        "eur_shock": -8,
        "gold_shock": +6,
        "description": "Russia fully cuts off gas to Europe"
    }
}

def portfolio_stress_test(portfolio_weights, scenarios=SCENARIOS):
    """Run geopolitical scenario stress tests on a portfolio.

    Args:
        portfolio_weights: dict mapping asset ticker to weight
        scenarios: Scenario-definition dictionary

    Returns:
        pd.DataFrame: Expected portfolio PnL under each scenario
    """
    results = {}
    for scenario_name, shocks in scenarios.items():
        portfolio_pnl = sum(
            portfolio_weights.get(asset, 0) * shock / 100
            for asset, shock in shocks.items()
            if asset != "description"
        )
        results[scenario_name] = {
            "portfolio_return": portfolio_pnl,
            "description": shocks["description"]
        }
    return results
```

### Scenario 4: Backtest of a GPR-Driven Dynamic Hedge

```python
# Strategy logic:
# When GPR > 75th percentile, hold 5% gold + 5% oil calls
# When GPR < 25th percentile, revert to standard allocation
# Historical backtests suggest a roughly 30-40% reduction in tail losses
# across major crises from 2001-2023

def gpr_dynamic_hedge_backtest(returns_data, gpr_data,
                                hedge_assets=["GLD", "USO"],
                                hedge_weight=0.05):
    """Backtest a GPR-driven dynamic hedge strategy.

    Args:
        returns_data: pd.DataFrame of daily asset returns
        gpr_data: pd.Series of monthly GPR Index values
        hedge_assets: List of hedge assets
        hedge_weight: Allocation weight per hedge asset

    Returns:
        pd.DataFrame: Return comparison before and after hedging
    """
    import pandas as pd

    # Map monthly GPR to daily frequency.
    gpr_daily = gpr_data.resample("D").ffill()
    gpr_threshold = gpr_daily.quantile(0.75)

    hedge_signal = gpr_daily > gpr_threshold

    base_return = returns_data.drop(columns=hedge_assets, errors="ignore").mean(axis=1)
    hedge_return = returns_data[hedge_assets].mean(axis=1) if hedge_assets else 0

    hedged_return = base_return.copy()
    hedged_return[hedge_signal] = (
        base_return[hedge_signal] * (1 - len(hedge_assets) * hedge_weight) +
        hedge_return[hedge_signal] * len(hedge_assets) * hedge_weight
    )

    return pd.DataFrame({
        "base": base_return,
        "hedged": hedged_return,
        "hedge_active": hedge_signal.astype(int)
    })
```

---

## References and Further Reading

```
Academic papers:
- Caldara & Iacoviello (2022), "Measuring Geopolitical Risk", AER
- Apergis et al. (2021), "Geopolitical Risks and Asset Prices"
- Mueller & Rauh (2018), "The Hard Problem of Prediction for Conflict Prevention"

Data resources:
- GPR Index: https://www.matteoiacoviello.com/gpr.htm
- GDELT: https://www.gdeltproject.org/
- ACLED: https://acleddata.com/
- SIPRI: https://www.sipri.org/databases

Market-analysis tools:
- BDI (Baltic Dry Index): https://www.balticexchange.com/
- CDS spread data: Bloomberg / Refinitiv (paid) / FRED (partially free)
- Vessel AIS tracking: MarineTraffic.com
```
