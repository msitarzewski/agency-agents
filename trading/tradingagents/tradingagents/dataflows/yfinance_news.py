"""yfinance-based news data fetching functions."""

import contextlib
from datetime import datetime

import yfinance as yf
from dateutil.relativedelta import relativedelta

from .config import get_config
from .stockstats_utils import yf_retry
from .symbol_utils import normalize_symbol


def _extract_article_data(article: dict) -> dict:
    """Extract article data from yfinance news format (handles nested 'content' structure)."""
    # Handle nested content structure
    if "content" in article:
        content = article["content"]
        title = content.get("title", "No title")
        summary = content.get("summary", "")
        provider = content.get("provider", {})
        publisher = provider.get("displayName", "Unknown")

        # Get URL from canonicalUrl or clickThroughUrl
        url_obj = content.get("canonicalUrl") or content.get("clickThroughUrl") or {}
        link = url_obj.get("url", "")

        # Get publish date
        pub_date_str = content.get("pubDate", "")
        pub_date = None
        if pub_date_str:
            with contextlib.suppress(ValueError, AttributeError):
                pub_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))

        return {
            "title": title,
            "summary": summary,
            "publisher": publisher,
            "link": link,
            "pub_date": pub_date,
        }
    else:
        # Fallback for flat structure. Parse the epoch publish time so flat
        # articles are date-filterable too (otherwise they bypass the
        # historical window and leak future news, #992/#1007).
        pub_date = None
        ts = article.get("providerPublishTime")
        if ts:
            with contextlib.suppress(ValueError, OSError, TypeError):
                pub_date = datetime.fromtimestamp(ts)
        return {
            "title": article.get("title", "No title"),
            "summary": article.get("summary", ""),
            "publisher": article.get("publisher", "Unknown"),
            "link": article.get("link", ""),
            "pub_date": pub_date,
        }


def _in_news_window(pub_date, start_dt, end_dt) -> bool:
    """Whether an article belongs in the [start_dt, end_dt] window.

    Dated articles are kept only if they fall in the window. An undated article
    is kept only when the window reaches the present (live run) — in a
    historical/backtest window it's excluded, since we can't prove it isn't
    future news (look-ahead safety, #992/#1007).
    """
    if pub_date is not None:
        naive = pub_date.replace(tzinfo=None) if hasattr(pub_date, "replace") else pub_date
        return start_dt <= naive <= end_dt + relativedelta(days=1)
    return end_dt >= datetime.now() - relativedelta(days=1)


def get_news_yfinance(
    ticker: str,
    start_date: str,
    end_date: str,
) -> str:
    """
    Retrieve news for a specific stock ticker using yfinance.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format

    Returns:
        Formatted string containing news articles
    """
    article_limit = get_config()["news_article_limit"]
    # Query Yahoo with the canonical symbol, like every other yfinance path —
    # a raw broker/forex/crypto alias (XAUUSD, BTCUSD) otherwise silently
    # returns no news. Keep the user's ticker in the report header.
    canonical = normalize_symbol(ticker)
    resolved = "" if canonical == ticker else f" (resolved to {canonical})"
    try:
        stock = yf.Ticker(canonical)
        news = yf_retry(lambda: stock.get_news(count=article_limit))

        if not news:
            return f"No news found for {ticker}{resolved}"

        # Parse date range for filtering
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        news_str = ""
        filtered_count = 0

        for article in news:
            data = _extract_article_data(article)

            # Keep only articles within the requested window (look-ahead safe).
            if not _in_news_window(data["pub_date"], start_dt, end_dt):
                continue

            news_str += f"### {data['title']} (source: {data['publisher']})\n"
            if data["summary"]:
                news_str += f"{data['summary']}\n"
            if data["link"]:
                news_str += f"Link: {data['link']}\n"
            news_str += "\n"
            filtered_count += 1

        if filtered_count == 0:
            return f"No news found for {ticker}{resolved} between {start_date} and {end_date}"

        return f"## {ticker}{resolved} News, from {start_date} to {end_date}:\n\n{news_str}"

    except Exception as e:
        return f"Error fetching news for {ticker}: {str(e)}"


def get_global_news_yfinance(
    curr_date: str,
    look_back_days: int | None = None,
    limit: int | None = None,
) -> str:
    """
    Retrieve global/macro economic news using yfinance Search.

    Args:
        curr_date: Current date in yyyy-mm-dd format
        look_back_days: Number of days to look back. ``None`` falls back to
            ``global_news_lookback_days`` from the active config.
        limit: Maximum number of articles to return. ``None`` falls back to
            ``global_news_article_limit`` from the active config.

    Returns:
        Formatted string containing global news articles
    """
    config = get_config()
    if look_back_days is None:
        look_back_days = config["global_news_lookback_days"]
    if limit is None:
        limit = config["global_news_article_limit"]
    search_queries = config["global_news_queries"]

    all_news = []
    seen_titles = set()

    try:
        for query in search_queries:
            search = yf_retry(lambda q=query: yf.Search(
                query=q,
                news_count=limit,
                enable_fuzzy_query=True,
            ))

            if search.news:
                for article in search.news:
                    # Handle both flat and nested structures
                    if "content" in article:
                        data = _extract_article_data(article)
                        title = data["title"]
                    else:
                        title = article.get("title", "")

                    # Deduplicate by title
                    if title and title not in seen_titles:
                        seen_titles.add(title)
                        all_news.append(article)

            if len(all_news) >= limit:
                break

        if not all_news:
            return f"No global news found for {curr_date}"

        # Calculate date range
        curr_dt = datetime.strptime(curr_date, "%Y-%m-%d")
        start_dt = curr_dt - relativedelta(days=look_back_days)
        start_date = start_dt.strftime("%Y-%m-%d")

        news_str = ""
        kept = 0
        for article in all_news[:limit]:
            # Extract uniformly (flat + nested) and apply the same look-ahead-safe
            # window filter, so flat articles can't leak future news (#1007).
            data = _extract_article_data(article)
            if not _in_news_window(data["pub_date"], start_dt, curr_dt):
                continue
            news_str += f"### {data['title']} (source: {data['publisher']})\n"
            if data["summary"]:
                news_str += f"{data['summary']}\n"
            if data["link"]:
                news_str += f"Link: {data['link']}\n"
            news_str += "\n"
            kept += 1

        # All candidates fell outside the window -> say so rather than return an
        # empty-bodied report (#993).
        if kept == 0:
            return f"No global news found between {start_date} and {curr_date}"

        return f"## Global Market News, from {start_date} to {curr_date}:\n\n{news_str}"

    except Exception as e:
        return f"Error fetching global news: {str(e)}"
