---
name: social-media-intelligence
description: "Social media intelligence: financial signal extraction from Twitter/X, Telegram, Discord, and Reddit for sentiment-driven trading strategies."
category: tool
---

# Social Media Intelligence

> This skill integrates financial-intelligence collection methods and quantitative applications across Twitter/X, Telegram, Discord, and Reddit.
> Inspired by `himself65/finance-skills` modules such as `discord-reader`, `telegram-reader`, and `twitter-reader`.

---

## 1. Overview of the Four Major Financial Social Platforms

### 1.1 Twitter/X — The FinTwit Ecosystem

**Core roles**

| Role Type | Representative Account Traits | Signal Value |
|---------|------------|---------|
| Sell-side analyst | Institutional backing, dense posting around earnings | Medium, somewhat lagging |
| Fund manager | Holdings views, industry judgment | High, but mixed with subjective opinion |
| Macro commentator | Fed interpretation, macro-data reaction | High, a good sentiment barometer |
| Crypto KOL | On-chain interpretation, project endorsement | Highly volatile, high manipulation risk |
| Retail noise | Meme spread, herd sentiment | Contrarian signal value at extremes |

**Core FinTwit circles**
- `$TICKER` cashtag system directly maps discussion to the asset
- Earnings-season sentiment patterns before and after reports
- Real-time reaction speed to policy / macro events, often 15-60 minutes ahead of traditional media

---

### 1.2 Telegram — The Core Venue for Crypto Intelligence

**Channel types**

| Channel Type | Content Traits | How to Use |
|---------|---------|---------|
| Signal channels | Specific buy/sell levels, stop-loss / take-profit | Use as a sentiment thermometer, not for blind copy-trading |
| Research push channels | Institutional PDF reports, on-chain data | Aggregate information and extract key numbers |
| Macro flash channels | Real-time interpretation of FOMC, CPI, etc. | Event-driven signals |
| Official project channels | Tokenomics updates, partnership announcements | Potential alpha, but requires filtering |
| Whale alert channels | Large on-chain transfer alerts | Capital-flow signal |

---

### 1.3 Discord — Quant Communities and Project Ecosystems

**Important community types**
- Quant / DeFi research communities such as Degen Spartan and Messari Research
- Official crypto project Discords with governance discussion and development progress
- Trader communities focused on options flow and on-chain analysis
- NFT / GameFi projects with floor-price alerts and activity monitoring

**Distinctive value of Discord**
- Community activity directly reflects project health
- Developer channels such as `#dev` and `#build` show implementation activity
- Governance participation indicates the willingness of token holders to stay involved

---

### 1.4 Reddit — A Barometer of Retail Sentiment

**Core subreddits**

| Subreddit | Core User Base | Main Signal |
|-------|---------|---------|
| r/wallstreetbets | Retail options traders | Meme-stock heat, abnormal options chatter |
| r/investing | Value-oriented retail investors | Long-horizon sentiment, ETF flow |
| r/cryptocurrency | Crypto retail | BTC / ETH cycle sentiment |
| r/stocks | General stock discussants | Earnings-season sentiment |
| r/options | Options-strategy community | Unusual IV-related topics |

---

## 2. Data Collection Methods

### 2.1 Twitter/X Data Collection

**Tooling options**

```python
# Option A: Official API v2 (paid, basic tier starts at $100/month)
# Best for: production environments where compliance is the priority
from tweepy import Client

client = Client(bearer_token=os.getenv("TWITTER_BEARER_TOKEN"))

# Search tweets discussing a cashtag over the last 7 days
def fetch_cashtag_tweets(ticker: str, max_results: int = 100) -> list[dict]:
    """Collect Twitter discussion data for a given ticker.

    Args:
        ticker: Ticker symbol such as AAPL or BTC
        max_results: Max number of returned tweets, between 10 and 100

    Returns:
        List of tweets, each containing id / text / created_at / public_metrics
    """
    query = f"${ticker} -is:retweet lang:en"
    tweets = client.search_recent_tweets(
        query=query,
        max_results=max_results,
        tweet_fields=["created_at", "public_metrics", "author_id"],
    )
    return [t.data for t in tweets.data or []]


# Option B: ntscraper (unofficial, free, rate-limited)
# Best for: research / historical backtesting
# pip install ntscraper
from ntscraper import Nitter

scraper = Nitter()
tweets = scraper.get_tweets("$AAPL", mode="term", number=50)
```

**Data schema (Twitter JSON Schema)**

```json
{
  "platform": "twitter",
  "collected_at": "2026-03-29T08:00:00Z",
  "query": "$AAPL",
  "items": [
    {
      "id": "tweet_id_string",
      "text": "tweet text",
      "created_at": "ISO8601 timestamp",
      "author": {
        "id": "user_id",
        "username": "handle",
        "followers_count": 50000,
        "verified": false
      },
      "metrics": {
        "like_count": 120,
        "retweet_count": 45,
        "reply_count": 23,
        "quote_count": 8
      },
      "sentiment_score": null,
      "tags": ["$AAPL", "#earnings"]
    }
  ]
}
```

**Suggested collection frequency**
- Earnings season / major events: real time, poll every 5 minutes
- Routine monitoring: hourly
- Historical backfill: daily batch

---

### 2.2 Telegram Data Collection

**Tooling**

```python
# Telethon — official MTProto client, requires API_ID + API_HASH
# pip install telethon
from telethon.sync import TelegramClient
from telethon import functions

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")

async def fetch_channel_messages(
    channel_username: str,
    limit: int = 200,
    offset_date: datetime | None = None,
) -> list[dict]:
    """Collect historical messages from a Telegram channel.

    Args:
        channel_username: Channel username without @, e.g. "whale_alert"
        limit: Maximum number of messages
        offset_date: Start time to backtrack from

    Returns:
        List of messages containing id / text / date / views / forwards
    """
    async with TelegramClient("session", API_ID, API_HASH) as client:
        messages = []
        async for msg in client.iter_messages(
            channel_username, limit=limit, offset_date=offset_date
        ):
            if msg.text:
                messages.append({
                    "id": msg.id,
                    "text": msg.text,
                    "date": msg.date.isoformat(),
                    "views": getattr(msg, "views", 0),
                    "forwards": getattr(msg, "forwards", 0),
                })
        return messages
```

**Data schema (Telegram JSON Schema)**

```json
{
  "platform": "telegram",
  "channel": "whale_alert",
  "collected_at": "2026-03-29T08:00:00Z",
  "items": [
    {
      "id": 12345,
      "text": "message text",
      "date": "ISO8601 timestamp",
      "views": 85000,
      "forwards": 320,
      "has_media": false,
      "reply_to_msg_id": null,
      "sentiment_score": null
    }
  ]
}
```

**Suggested collection frequency**
- Whale-alert / flash channels: real-time push, webhook mode
- Signal channels: every 30 minutes
- Research channels: daily

---

### 2.3 Discord Data Collection

**Tooling**

```python
# discord.py — official Bot API, requires Bot Token + server invitation permission
# pip install discord.py
import discord
from discord.ext import commands

async def fetch_channel_history(
    channel_id: int,
    limit: int = 500,
    after: datetime | None = None,
) -> list[dict]:
    """Collect message history from a Discord channel.

    Args:
        channel_id: Discord channel ID
        limit: Maximum number of messages, capped at 500 per request
        after: Start timestamp to backtrack from

    Returns:
        List of messages containing id / content / timestamp / author / reactions
    """
    bot = commands.Bot(command_prefix="!")
    messages = []

    @bot.event
    async def on_ready():
        channel = bot.get_channel(channel_id)
        async for msg in channel.history(limit=limit, after=after):
            messages.append({
                "id": str(msg.id),
                "content": msg.content,
                "timestamp": msg.created_at.isoformat(),
                "author": {
                    "id": str(msg.author.id),
                    "name": msg.author.name,
                    "bot": msg.author.bot,
                },
                "reaction_count": sum(r.count for r in msg.reactions),
                "attachments": len(msg.attachments),
            })
        await bot.close()

    await bot.start(os.getenv("DISCORD_BOT_TOKEN"))
    return messages
```

**Data schema (Discord JSON Schema)**

```json
{
  "platform": "discord",
  "guild_id": "server_id_string",
  "channel_id": "channel_id_string",
  "channel_name": "general-trading",
  "collected_at": "2026-03-29T08:00:00Z",
  "items": [
    {
      "id": "message_id_string",
      "content": "message text",
      "timestamp": "ISO8601 timestamp",
      "author": {
        "id": "user_id_string",
        "name": "username#1234",
        "roles": ["Member", "Whale"],
        "bot": false
      },
      "reaction_count": 42,
      "thread_count": 3,
      "sentiment_score": null
    }
  ]
}
```

**Suggested collection frequency**
- Active trading communities: hourly
- Official project channels: every 4 hours
- Governance channels: daily

---

### 2.4 Reddit Data Collection

**Tooling**

```python
# PRAW — official Reddit Python wrapper, free API
# pip install praw
import praw

def fetch_subreddit_posts(
    subreddit_name: str,
    mode: str = "hot",
    limit: int = 100,
    time_filter: str = "day",
) -> list[dict]:
    """Collect hot posts and related metadata from a subreddit.

    Args:
        subreddit_name: Subreddit name, e.g. "wallstreetbets"
        mode: Sort mode: "hot" / "new" / "top" / "rising"
        limit: Maximum number of posts
        time_filter: Time filter for top mode, e.g. "hour" / "day" / "week"

    Returns:
        List of posts containing id / title / score / comments / created_utc
    """
    reddit = praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent="vibe-trading/1.0",
    )
    subreddit = reddit.subreddit(subreddit_name)
    posts = []

    fetch_fn = {
        "hot": subreddit.hot,
        "new": subreddit.new,
        "top": lambda limit: subreddit.top(time_filter=time_filter, limit=limit),
        "rising": subreddit.rising,
    }[mode]

    for post in fetch_fn(limit=limit):
        posts.append({
            "id": post.id,
            "title": post.title,
            "selftext": post.selftext[:500],  # truncated body
            "score": post.score,
            "upvote_ratio": post.upvote_ratio,
            "num_comments": post.num_comments,
            "created_utc": post.created_utc,
            "url": post.url,
            "flair": post.link_flair_text,
        })
    return posts
```

**Data schema (Reddit JSON Schema)**

```json
{
  "platform": "reddit",
  "subreddit": "wallstreetbets",
  "collected_at": "2026-03-29T08:00:00Z",
  "items": [
    {
      "id": "post_id",
      "title": "post title",
      "selftext": "body summary (500 chars)",
      "score": 12500,
      "upvote_ratio": 0.94,
      "num_comments": 847,
      "created_utc": 1743206400.0,
      "flair": "YOLO",
      "mentioned_tickers": ["GME", "AMC"],
      "sentiment_score": null
    }
  ]
}
```

**Suggested collection frequency**
- r/wallstreetbets around the market open: every 30 minutes
- r/investing / r/stocks: every 4 hours
- r/cryptocurrency: hourly

---

### 2.5 Compliance and Privacy Notes

**Must comply with**
- Twitter API terms: do not resell data to third parties; obey rate limits such as the basic-tier 500,000 tweets/month allowance
- Telegram personal messages must not be collected; only public channels / groups are in scope
- Discord must be accessed through the official Bot API; self-bots violate ToS and may get banned
- Reddit PRAW rate limit: 60 requests/minute for authenticated users

**Data storage rules**
- Store user IDs in masked form such as hashes; do not retain raw usernames
- Store raw text locally only and do not expose it through public APIs
- Periodically purge raw data older than 30 days and keep only aggregated metrics

---

## 3. Sentiment Quantification Methodology

### 3.1 Text Sentiment Scoring

#### Option A: VADER (Lightweight, English, Good for Short Social Posts)

```python
# pip install vaderSentiment
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def vader_score(text: str) -> dict:
    """Score the sentiment of social-media text using VADER.

    Args:
        text: Raw social-media text such as a tweet, post, or message

    Returns:
        {'pos': float, 'neg': float, 'neu': float, 'compound': float}
        compound is in [-1, 1], where > 0.05 is positive and < -0.05 is negative
    """
    analyzer = SentimentIntensityAnalyzer()
    return analyzer.polarity_scores(text)
```

**Characteristics**: No GPU required, suitable for high-frequency batch processing; weaker on finance-specific slang such as "bull" or "moon".

#### Option B: FinBERT (Finance-Specific BERT)

```python
# pip install transformers torch
from transformers import pipeline

_finbert = None

def get_finbert():
    """Lazily load the FinBERT model. First call takes roughly 1-2 seconds."""
    global _finbert
    if _finbert is None:
        _finbert = pipeline(
            "text-classification",
            model="ProsusAI/finbert",
            tokenizer="ProsusAI/finbert",
        )
    return _finbert

def finbert_score(text: str) -> dict:
    """Classify sentiment in finance text using FinBERT.

    Args:
        text: Finance-related text, truncated to 512 tokens

    Returns:
        {'label': 'positive'|'negative'|'neutral', 'score': float}
    """
    result = get_finbert()(text[:512])[0]
    score_map = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
    return {
        "label": result["label"],
        "score": score_map[result["label"]] * result["score"],
    }
```

**Characteristics**: Stronger understanding of finance terms such as earnings, guidance, beat/miss; GPU acceleration is preferred for large batches.

#### Option C: LLM-Based (Highest Precision, Best for Long and Complex Text)

```python
def llm_sentiment(text: str, ticker: str | None = None) -> dict:
    """Use an LLM to analyze sentiment in complex finance text.

    Args:
        text: Raw text such as a report summary or Discord thread
        ticker: Related asset symbol, if available

    Returns:
        {'score': float[-1,1], 'label': str, 'reason': str}

    Note:
        Each call consumes roughly 500 tokens.
        Use only on samples where VADER / FinBERT confidence is below 0.6.
    """
    context = f"Ticker: {ticker}\n" if ticker else ""
    prompt = f"""{context}Analyze the sentiment of the following finance text and return JSON:
{{"score": <float from -1 to 1>, "label": <"bullish"|"bearish"|"neutral">, "reason": <one-sentence explanation>}}

Text: {text[:1000]}"""
    # Call the current agent's LLM interface
    from src.providers.base import get_llm
    response = get_llm().invoke(prompt)
    import json
    return json.loads(response.content)
```

**Recommendation by scenario**

| Scenario | Recommended Method | Reason |
|-----|---------|------|
| Real-time Twitter / Reddit batch processing | VADER | Low latency, no GPU required |
| Earnings-related text | FinBERT | Strong finance-term understanding |
| Telegram research summaries | LLM-based | Better on long-form and nuanced meaning |
| Multi-turn Discord discussion | FinBERT + LLM | Good balance of precision and cost |

---

### 3.2 Discussion-Buzz Metrics

```python
import pandas as pd
import numpy as np

def compute_buzz_metrics(df: pd.DataFrame, window: str = "1H") -> pd.DataFrame:
    """Compute time-series discussion-buzz metrics.

    Args:
        df: Message DataFrame containing timestamp / platform / ticker columns
        window: Aggregation window, such as "1H" / "4H" / "1D"

    Returns:
        Time-series DataFrame with:
        - msg_count: message volume
        - unique_authors: count of distinct active users
        - topic_freq: topic frequency as ticker volume / total message volume
        - engagement_score: weighted interaction count
        - buzz_zscore: message-volume Z-score for anomaly detection
    """
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp").sort_index()

    result = df.resample(window).agg(
        msg_count=("text", "count"),
        unique_authors=("author_id", "nunique"),
        total_engagement=("engagement", "sum"),
    )

    # Topic frequency, i.e. relative buzz.
    total = df.resample(window)["text"].count()
    result["topic_freq"] = result["msg_count"] / total.replace(0, np.nan)

    # Z-score anomaly detection using a 30-window rolling baseline.
    roll_mean = result["msg_count"].rolling(30, min_periods=5).mean()
    roll_std = result["msg_count"].rolling(30, min_periods=5).std()
    result["buzz_zscore"] = (result["msg_count"] - roll_mean) / roll_std.replace(0, np.nan)

    return result
```

**Key buzz metrics**
- `msg_count`: raw message count, measures absolute attention
- `unique_authors`: distinct users, reduces bot / spam distortion
- `buzz_zscore > 2.0`: abnormal buzz, triggers alerts
- `topic_freq`: relative buzz, controls for broad market-wide sentiment amplification

---

### 3.3 Sentiment Extremes (Fear / Greed Indicator)

```python
def compute_fear_greed_index(
    sentiment_series: pd.Series,
    buzz_series: pd.Series,
    lookback: int = 30,
) -> pd.Series:
    """Construct a CNN-style fear-and-greed index.

    Args:
        sentiment_series: Daily average sentiment in [-1, 1]
        buzz_series: Daily message-volume series
        lookback: Historical window in days used for percentile ranking

    Returns:
        Fear-and-greed index in [0, 100]
        0-20: extreme fear
        20-40: fear
        40-60: neutral
        60-80: greed
        80-100: extreme greed

    Note:
        Extreme greed (>80) is often a short-term top signal.
        Extreme fear (<20) is often a short-term bottom signal.
    """
    # Normalize sentiment by percentile rank.
    sentiment_rank = sentiment_series.rolling(lookback).rank(pct=True) * 100

    # Normalize buzz by percentile rank.
    buzz_rank = buzz_series.rolling(lookback).rank(pct=True) * 100

    # Weighted combination: 60% sentiment + 40% buzz.
    fear_greed = 0.6 * sentiment_rank + 0.4 * buzz_rank

    return fear_greed.clip(0, 100)
```

**Extreme-sentiment thresholds**

| Range | State | Historical Meaning | Trading Interpretation |
|---------|-----|---------|---------|
| 0-20 | Extreme fear | Panic selling, liquidity stress | Contrarian long candidate |
| 20-40 | Fear | Pessimism spreading | Wait and watch for stabilization |
| 40-60 | Neutral | Balanced sentiment | Let fundamentals lead |
| 60-80 | Greed | Optimism dominant | Candidate for trimming risk |
| 80-100 | Extreme greed | FOMO-driven retail influx | Contrarian short candidate |

---

### 3.4 Retail vs Institutional Sentiment

```python
def classify_author_type(author: dict) -> str:
    """Classify an account as retail / institutional / KOL using profile traits.

    Args:
        author: Dict containing followers_count / verified / account_age_days /
                tweet_count / following_count

    Returns:
        'institutional': institutional account
        'kol': high-impact KOL
        'retail': retail user
        'bot_risk': suspected bot

    Note:
        Institutional sentiment should carry more weight than KOL,
        and KOL more than retail. Retail extremes often have contrarian value.
    """
    followers = author.get("followers_count", 0)
    verified = author.get("verified", False)
    age_days = author.get("account_age_days", 0)
    tweet_count = author.get("tweet_count", 0)

    # Bot-risk detection
    if age_days < 30 and tweet_count > 1000:
        return "bot_risk"
    if tweet_count > 0 and (tweet_count / max(age_days, 1)) > 50:
        return "bot_risk"

    # Institutional characteristics: verified plus large audience
    if verified and followers > 100_000:
        return "institutional"

    # KOL: large following but not necessarily verified
    if followers > 10_000:
        return "kol"

    return "retail"


def weighted_sentiment(
    df: pd.DataFrame,
    weights: dict | None = None,
) -> pd.Series:
    """Compute weighted sentiment by author category.

    Args:
        df: DataFrame containing sentiment_score / author_type / timestamp
        weights: Optional category weights, defaults to institutional:3, kol:2, retail:1

    Returns:
        Daily weighted sentiment time series
    """
    if weights is None:
        weights = {"institutional": 3.0, "kol": 2.0, "retail": 1.0, "bot_risk": 0.0}

    df["weight"] = df["author_type"].map(weights).fillna(1.0)
    df["weighted_sentiment"] = df["sentiment_score"] * df["weight"]

    return (
        df.groupby(df["timestamp"].dt.date)
        .apply(lambda g: g["weighted_sentiment"].sum() / g["weight"].sum())
        .rename("weighted_sentiment")
    )
```

---

## 4. Using Social Signals as Factors

### 4.1 Social-Sentiment Factor Construction and IC / ICIR Testing

```python
import pandas as pd
import numpy as np
from scipy.stats import spearmanr

def compute_ic(
    factor_series: pd.Series,
    forward_return: pd.Series,
    method: str = "spearman",
) -> float:
    """Compute one-period factor IC (information coefficient).

    Args:
        factor_series: Cross-sectional factor values, e.g. same-day sentiment by ticker
        forward_return: Matching forward N-day returns
        method: "spearman" for rank correlation or "pearson"

    Returns:
        IC in [-1, 1]. |IC| > 0.05 is useful and > 0.1 is strong.
    """
    aligned = pd.concat([factor_series, forward_return], axis=1).dropna()
    if len(aligned) < 5:
        return np.nan

    if method == "spearman":
        ic, _ = spearmanr(aligned.iloc[:, 0], aligned.iloc[:, 1])
    else:
        ic = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
    return ic


def compute_icir(ic_series: pd.Series) -> float:
    """Compute ICIR, the information ratio of IC.

    Args:
        ic_series: Time series of IC values

    Returns:
        ICIR = mean(IC) / std(IC), where > 0.5 is useful and > 1.0 is strong
    """
    return ic_series.mean() / ic_series.std() if ic_series.std() > 0 else np.nan


# Example factor-construction workflow
def build_sentiment_factor(
    raw_data: pd.DataFrame,
    forward_days: int = 5,
) -> dict:
    """Build a complete social-sentiment factor and test its effectiveness.

    Args:
        raw_data: Raw data containing date / ticker / sentiment_score / author_type
        forward_days: Forward return horizon in days

    Returns:
        {'factor': DataFrame, 'ic_series': Series, 'icir': float}
    """
    # 1. Cross-sectional standardization
    factor = (
        raw_data.groupby("date")["sentiment_score"]
        .transform(lambda x: (x - x.mean()) / (x.std() + 1e-8))
    )

    # 2. Compute period-by-period IC
    ic_list = []
    dates = raw_data["date"].unique()
    for date in sorted(dates)[:-forward_days]:
        fwd_date = dates[dates > date][:forward_days][-1]
        f = raw_data[raw_data["date"] == date].set_index("ticker")["sentiment_norm"]
        r = raw_data[raw_data["date"] == fwd_date].set_index("ticker")["return"]
        ic_list.append((date, compute_ic(f, r)))

    ic_series = pd.Series(dict(ic_list))
    return {
        "factor": factor,
        "ic_series": ic_series,
        "ic_mean": ic_series.mean(),
        "icir": compute_icir(ic_series),
    }
```

**IC / ICIR grading**

| Metric | Weak | Useful | Strong |
|-----|----|----|---|
| \|IC\| | < 0.03 | 0.03-0.08 | > 0.08 |
| ICIR | < 0.3 | 0.3-0.8 | > 0.8 |
| IC positive-rate | < 50% | 50-60% | > 60% |

---

### 4.2 Orthogonalization Against Traditional Factors

```python
def orthogonalize_sentiment(
    sentiment_factor: pd.Series,
    traditional_factors: pd.DataFrame,
) -> pd.Series:
    """Orthogonalize the sentiment factor against traditional factors.

    Args:
        sentiment_factor: Raw sentiment factor after cross-sectional normalization
        traditional_factors: Matrix of traditional factors such as size / momentum / valuation

    Returns:
        Pure sentiment factor after removing shared components, i.e. the residual

    Note:
        Orthogonalization often lowers IC, but improves factor independence
        and reduces double-counting in multi-factor portfolios.
    """
    from sklearn.linear_model import LinearRegression
    import numpy as np

    # Regress on the traditional factors and keep the residual.
    X = traditional_factors.fillna(0).values
    y = sentiment_factor.fillna(0).values

    reg = LinearRegression(fit_intercept=True).fit(X, y)
    residual = y - reg.predict(X)

    return pd.Series(residual, index=sentiment_factor.index)
```

---

### 4.3 Cross-Platform Sentiment Aggregation Weights

```python
PLATFORM_WEIGHTS = {
    # Weight basis: historical IC contribution + information quality
    "twitter_institutional": 0.35,
    "twitter_kol": 0.20,
    "telegram_signal": 0.15,
    "telegram_research": 0.15,
    "discord_community": 0.10,
    "reddit_wsb": 0.05,
}

def aggregate_platform_sentiment(platform_scores: dict[str, float]) -> float:
    """Aggregate sentiment scores from multiple platforms using weights.

    Args:
        platform_scores: Dict of {platform_key: sentiment_score} with scores in [-1, 1]

    Returns:
        Aggregated sentiment score in [-1, 1]
    """
    total_weight = 0.0
    weighted_sum = 0.0

    for platform, score in platform_scores.items():
        weight = PLATFORM_WEIGHTS.get(platform, 0.05)
        weighted_sum += score * weight
        total_weight += weight

    return weighted_sum / total_weight if total_weight > 0 else 0.0
```

---

### 4.4 Sentiment-Reversal Signals

```python
def detect_sentiment_reversal(
    fg_index: pd.Series,
    price_series: pd.Series,
    extreme_threshold: float = 80.0,
    fear_threshold: float = 20.0,
    confirmation_days: int = 3,
) -> pd.DataFrame:
    """Detect reversal signals from sentiment extremes.

    Args:
        fg_index: Fear-and-greed index in [0, 100]
        price_series: Corresponding price series
        extreme_threshold: Extreme-greed threshold, default 80
        fear_threshold: Extreme-fear threshold, default 20
        confirmation_days: Number of days required for confirmation

    Returns:
        DataFrame containing signal / direction / strength
        signal = 1: short signal due to sustained extreme greed
        signal = -1: long signal due to sustained extreme fear
        signal = 0: no signal

    Note:
        Sentiment reversals usually lag the exact top or bottom,
        but can still lead by roughly 3-10 trading days.
        Use together with price momentum or volume anomalies.
    """
    signals = pd.DataFrame(index=fg_index.index)
    signals["fg"] = fg_index
    signals["signal"] = 0
    signals["direction"] = ""
    signals["strength"] = 0.0

    # Sustained extreme greed → short signal
    greed_mask = (fg_index > extreme_threshold).rolling(confirmation_days).sum() == confirmation_days
    signals.loc[greed_mask, "signal"] = 1
    signals.loc[greed_mask, "direction"] = "short"
    signals.loc[greed_mask, "strength"] = (fg_index - extreme_threshold).clip(0) / 20

    # Sustained extreme fear → long signal
    fear_mask = (fg_index < fear_threshold).rolling(confirmation_days).sum() == confirmation_days
    signals.loc[fear_mask, "signal"] = -1
    signals.loc[fear_mask, "direction"] = "long"
    signals.loc[fear_mask, "strength"] = (fear_threshold - fg_index).clip(0) / 20

    return signals
```

---

## 5. Platform-Specific Analysis

### 5.1 Twitter: KOL Influence Tracking + Earnings Sentiment

**KOL influence quantification**

```python
def compute_kol_influence_score(author: dict, recent_tweets: list[dict]) -> float:
    """Quantify the market influence of a Twitter KOL.

    Args:
        author: Account metadata including follower count, verification, and age
        recent_tweets: Most recent 20 tweets including engagement metrics

    Returns:
        Influence score in [0, 100]

    Note:
        KOLs with scores above 70 tend to lift 1-hour realized volatility
        of the related asset by roughly 15% after posting.
    """
    # Follower-quality score, using log follower count
    follower_score = min(np.log10(max(author["followers_count"], 1)) / 7, 1.0) * 40

    # Engagement rate = recent average engagement / follower count
    avg_engagement = np.mean([
        t["metrics"]["like_count"] + t["metrics"]["retweet_count"] * 2
        for t in recent_tweets
    ])
    engagement_rate = avg_engagement / max(author["followers_count"], 1)
    engagement_score = min(engagement_rate * 1000, 1.0) * 30

    # Account-age credibility score
    age_score = min(author["account_age_days"] / 1825, 1.0) * 20  # full score at 5 years

    # Verification bonus
    verified_bonus = 10 if author["verified"] else 0

    return follower_score + engagement_score + age_score + verified_bonus
```

**Pre/post-earnings sentiment shift**

```python
def analyze_earnings_sentiment_shift(
    ticker: str,
    earnings_date: str,
    sentiment_df: pd.DataFrame,
    window_days: int = 5,
) -> dict:
    """Analyze Twitter sentiment changes before and after earnings.

    Args:
        ticker: Stock ticker
        earnings_date: Earnings date in YYYY-MM-DD
        sentiment_df: Daily time series containing date / sentiment_score
        window_days: Observation window on each side of the earnings date

    Returns:
        {
          'pre_sentiment': float,
          'post_sentiment': float,
          'shift': float,
          'signal': str  # 'beat_expected' / 'miss_expected' / 'neutral'
        }
    """
    ed = pd.Timestamp(earnings_date)
    pre = sentiment_df[
        (sentiment_df.index >= ed - pd.Timedelta(days=window_days)) &
        (sentiment_df.index < ed)
    ]["sentiment_score"].mean()
    post = sentiment_df[
        (sentiment_df.index > ed) &
        (sentiment_df.index <= ed + pd.Timedelta(days=window_days))
    ]["sentiment_score"].mean()

    shift = post - pre
    signal = "neutral"
    if shift > 0.2:
        signal = "beat_expected"
    elif shift < -0.2:
        signal = "miss_expected"

    return {"pre_sentiment": pre, "post_sentiment": post, "shift": shift, "signal": signal}
```

---

### 5.2 Telegram: Crypto Project Alpha + Airdrop / IDO Buzz

**Alpha-signal quality filter**

Signal quality varies widely across crypto Telegram channels. Filter with rules like the following:

```python
ALPHA_QUALITY_RULES = {
    # Low-quality signals to filter out directly
    "spam_patterns": [
        r"100x guaranteed",
        r"private sale",
        r"limited spots",
        r"DM me",
        r"pump incoming",
    ],
    # High-quality signals that deserve extra weight
    "quality_signals": [
        r"on-chain data",
        r"tokenomics analysis",
        r"team background",
        r"audit report",
        r"TVL growing",
    ],
}

def score_telegram_alpha(message: str) -> dict:
    """Score the quality of alpha in Telegram crypto-channel messages.

    Args:
        message: Raw channel message

    Returns:
        {'quality_score': int[0-10], 'is_spam': bool, 'alpha_type': str}
    """
    import re
    text_lower = message.lower()

    # Spam detection
    for pattern in ALPHA_QUALITY_RULES["spam_patterns"]:
        if re.search(pattern, text_lower):
            return {"quality_score": 0, "is_spam": True, "alpha_type": "spam"}

    # Quality score
    score = 5
    for pattern in ALPHA_QUALITY_RULES["quality_signals"]:
        if re.search(pattern, text_lower):
            score += 1

    alpha_type = "research" if score >= 7 else "signal" if score >= 5 else "noise"
    return {"quality_score": min(score, 10), "is_spam": False, "alpha_type": alpha_type}
```

**Airdrop / IDO buzz tracking**

- Monitor keyword frequency for tags such as `#airdrop`, `#IDO`, and `#whitelist`
- Buzz peaks where topic frequency exceeds 3× baseline often lead token-price moves by 2-5 days
- Important caveat: high-buzz IDOs often face heavy Day-1 sell pressure from participants taking quick profits

---

### 5.3 Discord: Community Activity → Project Health

**Project health index**

```python
def compute_project_health_index(
    discord_stats: dict,
    lookback_days: int = 30,
) -> dict:
    """Build a project-community health index from Discord statistics.

    Args:
        discord_stats: {
            'daily_messages': list[int],
            'daily_active_users': list[int],
            'new_members': list[int],
            'dev_commits': list[int],
        }
        lookback_days: Historical window used as the baseline

    Returns:
        {
            'health_score': float[0-100],
            'trend': 'growing'|'stable'|'declining',
            'flags': list[str]
        }
    """
    msgs = np.array(discord_stats["daily_messages"][-lookback_days:])
    users = np.array(discord_stats["daily_active_users"][-lookback_days:])
    members = np.array(discord_stats["new_members"][-lookback_days:])

    # Component scores
    msg_trend = np.polyfit(range(len(msgs)), msgs, 1)[0]
    user_trend = np.polyfit(range(len(users)), users, 1)[0]

    msg_score = min(50 + msg_trend / max(msgs.mean(), 1) * 500, 100)
    user_score = min(50 + user_trend / max(users.mean(), 1) * 500, 100)
    retention = (users.mean() / max(members[-7:].sum(), 1)) * 20

    health_score = 0.4 * msg_score + 0.4 * user_score + 0.2 * min(retention, 100)

    # Warning flags
    flags = []
    if msgs[-7:].mean() < msgs[-30:].mean() * 0.5:
        flags.append("Message volume has collapsed: 7-day average is below 50% of the 30-day average")
    if users[-3:].mean() < users[-30:].mean() * 0.3:
        flags.append("Active users have plunged: possible project-abandonment warning")

    trend = "growing" if msg_trend > 0 and user_trend > 0 else \
            "declining" if msg_trend < 0 and user_trend < 0 else "stable"

    return {"health_score": health_score, "trend": trend, "flags": flags}
```

**Whale-discussion monitoring**

- Monitor channels such as `#whale-watch` and `#large-transactions`
- Keywords to watch: `whale alert`, `large transfer`, `moved X BTC`
- Cross-check with Whale Alert Telegram bot data

---

### 5.4 Reddit: WSB Meme-Stock Buzz + Options-Flow Abnormalities

**Meme-stock momentum detection**

```python
def detect_meme_stock_momentum(
    wsb_posts: list[dict],
    top_n: int = 10,
) -> pd.DataFrame:
    """Detect meme-stock momentum on WSB and identify short-squeeze candidates.

    Args:
        wsb_posts: List of WSB posts collected through PRAW
        top_n: Number of top hot tickers to return

    Returns:
        DataFrame containing ticker / mention_count / avg_score / option_buzz

    Note:
        mention_count > 200 in one day plus sentiment > 0.5 is one early short-squeeze warning condition.
        A full squeeze setup still requires short interest above 20%.
    """
    import re
    from collections import defaultdict

    ticker_stats = defaultdict(lambda: {"count": 0, "scores": [], "option_buzz": 0})

    # Common U.S. ticker regex: 2-5 uppercase letters
    ticker_pattern = re.compile(r"\b([A-Z]{2,5})\b")
    option_keywords = ["calls", "puts", "options", "IV", "yolo", "FDs"]

    for post in wsb_posts:
        text = f"{post['title']} {post['selftext']}"
        tickers_found = ticker_pattern.findall(text)

        # Filter common non-ticker words
        stop_words = {"THE", "FOR", "AND", "BUT", "NOT", "ARE", "YOU", "ALL", "CAN"}
        tickers_found = [t for t in tickers_found if t not in stop_words]

        has_options = any(kw.lower() in text.lower() for kw in option_keywords)

        for ticker in set(tickers_found):
            ticker_stats[ticker]["count"] += 1
            ticker_stats[ticker]["scores"].append(post["score"])
            if has_options:
                ticker_stats[ticker]["option_buzz"] += 1

    rows = []
    for ticker, stats in ticker_stats.items():
        rows.append({
            "ticker": ticker,
            "mention_count": stats["count"],
            "avg_score": np.mean(stats["scores"]),
            "option_buzz": stats["option_buzz"],
        })

    df = pd.DataFrame(rows).sort_values("mention_count", ascending=False)
    return df.head(top_n)
```

**WSB short-squeeze checklist**

| Condition | Data Source | Threshold |
|-----|---------|-----|
| WSB mentions | Reddit PRAW | > 200 per day |
| WSB options-discussion heat | Reddit PRAW | option_buzz > 30% |
| Short interest (SI) | Finviz / IEX | > 20% |
| Borrow tightness | Securities-lending data | CTB > 5% |
| Unusual options open interest | Option-chain data | OI day-over-day change > 50% |

---

## 6. Data-Pipeline Integration

### 6.1 Unified Data Collection Interface

```python
# Reference implementation: agent/src/tools/social_media_tool.py

from dataclasses import dataclass
from enum import Enum

class Platform(str, Enum):
    TWITTER = "twitter"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    REDDIT = "reddit"

@dataclass
class SocialMediaQuery:
    """Social-media query parameters."""
    platform: Platform
    query: str
    limit: int = 100
    start_time: str | None = None
    include_sentiment: bool = True

def collect_social_signals(query: SocialMediaQuery) -> dict:
    """Unified entrypoint for collecting social-media data.

    Args:
        query: Query parameters including platform, keyword, time window, and limit

    Returns:
        Standardized JSON data containing platform / items / metadata

    Raises:
        ValueError: Unsupported platform or invalid parameters
        RuntimeError: API call failed, with retry guidance attached
    """
    collectors = {
        Platform.TWITTER: _collect_twitter,
        Platform.TELEGRAM: _collect_telegram,
        Platform.DISCORD: _collect_discord,
        Platform.REDDIT: _collect_reddit,
    }
    collector = collectors.get(query.platform)
    if not collector:
        raise ValueError(f"Unsupported platform: {query.platform}")

    raw_data = collector(query)

    if query.include_sentiment:
        raw_data = _enrich_with_sentiment(raw_data)

    return raw_data
```

### 6.2 Environment Variables

```bash
# Add the following to .env
TWITTER_BEARER_TOKEN=xxx
TELEGRAM_API_ID=xxx
TELEGRAM_API_HASH=xxx
DISCORD_BOT_TOKEN=xxx
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx

# Sentiment model selection: vader / finbert / llm
SENTIMENT_MODEL=finbert
```

### 6.3 Factor Storage Schema

```sql
-- Social-sentiment factor table (DuckDB / SQLite)
CREATE TABLE social_sentiment_factors (
    date        DATE NOT NULL,
    ticker      VARCHAR(20) NOT NULL,
    platform    VARCHAR(20) NOT NULL,
    sentiment   FLOAT,           -- [-1, 1]
    buzz_zscore FLOAT,           -- Buzz Z-score
    fear_greed  FLOAT,           -- [0, 100]
    msg_count   INTEGER,
    author_type VARCHAR(20),     -- institutional / kol / retail
    PRIMARY KEY (date, ticker, platform)
);
```

---

## 7. Caveats and Limitations

1. **Limited lead value**: Social sentiment usually has IC around 0.03-0.06 on broad indices. It works best as a supporting factor, not a primary one.
2. **Manipulation risk**: Telegram and Discord signal channels in crypto contain many paid signal groups and pump rings. Source-quality scoring is mandatory.
3. **Language bias**: VADER and FinBERT are mainly built for English. Chinese social platforms such as Xueqiu or Guba need separate model adaptation.
4. **API cost control**: Twitter API v2 basic tier allows 500,000 tweets/month, and upgrading from $100 to $5000/month changes economics significantly. Budget collection volume explicitly.
5. **Latency vs quality trade-off**: Real-time collection is noisier, while daily aggregation gives cleaner signals. Choose based on the strategy horizon.
6. **Factor decay**: Social-sentiment factor effectiveness decays as more market participants exploit the same signal. Re-test IC regularly.

---

*Version: v1.0 | Created: 2026-03-29 | Scope: quantitative research / factor mining (not for direct live-trading signals)*
