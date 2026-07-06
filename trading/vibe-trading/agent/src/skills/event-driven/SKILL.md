---
name: event-driven
description: Event-driven strategy based on sentiment-scored signals from news, announcements, and macro events. The LLM acts as the NLP engine, and event data follows a CSV schema.
category: strategy
---
# Event-Driven Strategy

## Purpose

Uses event information such as news, announcements, and macro policy updates. The LLM analyzes sentiment and impact magnitude to generate event-driven trading signals. Event data is managed in CSV format, and technical signals are combined with event signals through weighted aggregation to form the final trading decision.

## Workflow

1. **Data collection**: use the `read_url` tool to fetch the full text of news and announcements
2. **LLM analysis**: the LLM reads the news and scores it from `-1.0` to `1.0` with a standardized prompt (extremely bearish to extremely bullish)
3. **Generate the event CSV**: write data in the `date,event_type,score,source,summary` schema
4. **Signal aggregation**: `signal_engine.py` reads the event CSV, applies time decay, and combines it with the technical signal

**Key principle: the event CSV is the data layer, and `signal_engine.py` is the logic layer. Keep them decoupled.**

## Event CSV Schema

```csv
date,event_type,score,source,summary
2024-01-15,earnings,0.8,read_url,Q4 revenue beat expectations by 30%
2024-01-20,macro,-0.5,read_url,Central bank raised rates by 25bp
2024-02-01,policy,0.3,read_url,New-energy subsidies extended
2024-02-10,sentiment,-0.7,read_url,Bearish sentiment surged on social media
2024-03-05,insider,0.4,read_url,CEO bought 5 million shares
```

Field descriptions:

| Field | Type | Description |
|------|------|------|
| date | str (`YYYY-MM-DD`) | Date when the event became knowable (publication date, not occurrence date. If released after market close → use the next trading day) |
| event_type | str | `earnings / macro / policy / sentiment / insider / technical_break` |
| score | float | `-1.0 ~ 1.0` (standardized LLM score) |
| source | str | Data-source tag (such as `read_url`) |
| summary | str | Event summary (one sentence, no commas) |

## Event Type Details

| Type | Meaning | Typical Impact | Duration |
|------|------|---------|---------|
| earnings | Earnings release | Short-term shock | 1-5 days |
| macro | Macro data / central-bank policy | Medium-term impact | 5-20 days |
| policy | Industry policy / regulatory change | Long-term impact | 20-60 days |
| sentiment | Market sentiment / public opinion | Short-term shock | 1-3 days |
| insider | Insider trading / block trade | Medium-term signal | 5-10 days |
| technical_break | Break of a key technical level | Short-term catalyst | 1-5 days |

## Signal Aggregation

### Time Decay of Event Signals

Event impact decays exponentially over time:

```python
import numpy as np
import pandas as pd


def compute_event_signal(event_df: pd.DataFrame, dates: pd.DatetimeIndex,
                         decay_lambda: float = 0.1,
                         min_score_threshold: float = 0.2,
                         event_lookback: int = 30) -> pd.Series:
    """Compute an event-driven signal with time decay.

    Args:
        event_df: DataFrame loaded from the event CSV, with date/event_type/score/source/summary columns.
        dates: Backtest date sequence (DatetimeIndex).
        decay_lambda: Decay coefficient. Higher values decay faster. Default 0.1 (decays to ~37% in about 10 days).
        min_score_threshold: Minimum score threshold. Events with |score| below this value are ignored.
        event_lookback: Event lookback window in days. Events older than this are excluded.

    Returns:
        Event signal Series aligned with dates, with value range [-1.0, 1.0].
    """
    event_df = event_df[event_df["score"].abs() >= min_score_threshold].copy()
    event_df["date"] = pd.to_datetime(event_df["date"])

    signal = pd.Series(0.0, index=dates)

    for trade_date in dates:
        # Only consider events published on or before trade_date (avoid look-ahead)
        mask = (event_df["date"] <= trade_date) & \
               (event_df["date"] >= trade_date - pd.Timedelta(days=event_lookback))
        relevant = event_df[mask]

        if relevant.empty:
            continue

        days_since = (trade_date - relevant["date"]).dt.days.values
        scores = relevant["score"].values
        # Exponential decay: score * exp(-lambda * days)
        decayed = scores * np.exp(-decay_lambda * days_since)
        # Sum multiple events and clip to [-1, 1]
        signal[trade_date] = np.clip(decayed.sum(), -1.0, 1.0)

    return signal
```

### Weighted Combination of Technical and Event Signals

```python
def combine_signals(tech_signal: pd.Series, event_signal: pd.Series,
                    alpha: float = 0.6) -> pd.Series:
    """Combine technical and event signals with weights.

    Args:
        tech_signal: Technical signal, range [-1.0, 1.0].
        event_signal: Event-driven signal, range [-1.0, 1.0].
        alpha: Weight of the technical signal, default 0.6 (technical primary, event secondary).

    Returns:
        Combined signal, range [-1.0, 1.0].
    """
    combined = alpha * tech_signal + (1 - alpha) * event_signal
    return combined.clip(-1.0, 1.0)
```

Default `alpha = 0.6`: technical signal 60%, event signal 40%.

## Parameters

| Parameter | Default | Description |
|------|--------|------|
| alpha | 0.6 | Weight of the technical signal (`1-alpha` is the event weight) |
| decay_lambda | 0.1 | Decay coefficient (higher values decay faster; `0.1` ≈ decays to 37% in 10 days) |
| event_lookback | 30 | Event lookback window in days (older events are excluded) |
| min_score_threshold | 0.2 | Minimum score threshold (events with |score| below this are ignored) |

## LLM Scoring Prompt Template

After fetching news with `read_url`, use the following standardized prompt to keep scoring consistent:

```
You are a financial event analyst. Read the following news / announcement and score its impact on the stock price.

Scoring scale:
- 1.0: extremely bullish (for example, earnings far above expectations, major favorable policy)
- 0.5: moderately bullish (for example, earnings slightly above expectations, favorable industry news)
- 0.2: mildly bullish
- 0.0: neutral (no obvious impact)
- -0.2: mildly bearish
- -0.5: moderately bearish (for example, earnings below expectations, tighter industry regulation)
- -1.0: extremely bearish (for example, accounting fraud, major violations, black-swan event)

Score strictly on the scale above. Output one number only. Do not explain.

News content:
{news_content}

Score:
```

## Common Pitfalls

1. **Look-ahead bias**: the `date` in the event CSV must be the "knowable date" — announcements released after market close should use the next trading day, not the same day. In backtests, strictly enforce `event_date <= trade_date`
2. **Duplicate event scoring**: the same event may appear from multiple news sources and generate multiple rows. Deduplicate by `(date, event_type)` or average the scores
3. **Sentiment drift**: the LLM scoring standard can drift as the prompt or model version changes. Fix the prompt template and recalibrate regularly
4. **Event sparsity**: most trading days have no events, so the event signal is 0 and the final signal is mainly driven by technicals. This is normal; do not fabricate data just to "fill gaps"
5. **Event data in backtests**: historical backtests require a fully prepared historical event CSV in advance; you cannot fetch it in real time. It is recommended to maintain separate event files per instrument
6. **Commas in the `summary` field**: a common reason for CSV parsing errors — avoid commas in `summary`, or read with `pd.read_csv(quoting=csv.QUOTE_ALL)`
7. **Decay parameter sensitivity**: overly large `decay_lambda` makes event impact disappear too quickly, while overly small values keep stale events active for too long. In theory, different event types should use different decay profiles, but the default simplifies all of them to `0.1`

## Dependencies

```bash
pip install pandas numpy
```

No additional dependencies. LLM analysis is handled by the Agent itself, and the `read_url` tool is built in.

## Signal Convention

- Pure event signal: `[-1.0, 1.0]` (computed from event score + time decay)
- Combined signal: `alpha * tech_signal + (1 - alpha) * event_signal`, clipped to `[-1.0, 1.0]`
- When no event exists, `event_signal = 0`, so the combined signal collapses to the pure technical signal
