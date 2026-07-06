"""
Alpha Vantage 新闻数据提供者

提供高质量的市场新闻和情感分析数据

参考原版 TradingAgents 实现
"""

from typing import Annotated, Dict, Any
import json
from datetime import datetime

from .alpha_vantage_common import _make_api_request, format_datetime_for_api, format_response_as_string

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')


def get_news(
    ticker: Annotated[str, "Stock symbol for news articles"],
    start_date: Annotated[str, "Start date for news search, YYYY-MM-DD"],
    end_date: Annotated[str, "End date for news search, YYYY-MM-DD"]
) -> str:
    """
    获取股票相关的新闻和情感分析数据
    
    返回来自全球主要新闻媒体的实时和历史市场新闻及情感数据。
    涵盖股票、加密货币、外汇以及财政政策、并购、IPO等主题。
    
    Args:
        ticker: 股票代码
        start_date: 开始日期，格式 YYYY-MM-DD
        end_date: 结束日期，格式 YYYY-MM-DD
        
    Returns:
        格式化的新闻数据字符串（JSON格式）
        
    Example:
        >>> news = get_news("AAPL", "2024-01-01", "2024-01-31")
    """
    try:
        logger.info(f"📰 [Alpha Vantage] 获取新闻: {ticker}, {start_date} 至 {end_date}")
        
        # 构建请求参数
        params = {
            "tickers": ticker.upper(),
            "time_from": format_datetime_for_api(start_date),
            "time_to": format_datetime_for_api(end_date),
            "sort": "LATEST",
            "limit": "50",  # 最多返回50条新闻
        }
        
        # 发起 API 请求
        data = _make_api_request("NEWS_SENTIMENT", params)
        
        # 格式化响应
        if isinstance(data, dict):
            # 提取关键信息
            feed = data.get("feed", [])
            
            if not feed:
                return f"# No news found for {ticker} between {start_date} and {end_date}\n"
            
            # 构建格式化输出
            result = f"# News and Sentiment for {ticker.upper()}\n"
            result += f"# Period: {start_date} to {end_date}\n"
            result += f"# Total articles: {len(feed)}\n"
            result += f"# Retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # 添加每条新闻
            for idx, article in enumerate(feed, 1):
                result += f"## Article {idx}\n"
                result += f"**Title**: {article.get('title', 'N/A')}\n"
                result += f"**Source**: {article.get('source', 'N/A')}\n"
                result += f"**Published**: {article.get('time_published', 'N/A')}\n"
                result += f"**URL**: {article.get('url', 'N/A')}\n"
                
                # 情感分析
                sentiment = article.get('overall_sentiment_label', 'N/A')
                sentiment_score = article.get('overall_sentiment_score', 'N/A')
                result += f"**Sentiment**: {sentiment} (Score: {sentiment_score})\n"
                
                # 摘要
                summary = article.get('summary', 'N/A')
                if len(summary) > 200:
                    summary = summary[:200] + "..."
                result += f"**Summary**: {summary}\n"
                
                # 相关股票的情感
                ticker_sentiment = article.get('ticker_sentiment', [])
                for ts in ticker_sentiment:
                    if ts.get('ticker', '').upper() == ticker.upper():
                        result += f"**Ticker Sentiment**: {ts.get('ticker_sentiment_label', 'N/A')} "
                        result += f"(Score: {ts.get('ticker_sentiment_score', 'N/A')}, "
                        result += f"Relevance: {ts.get('relevance_score', 'N/A')})\n"
                        break
                
                result += "\n---\n\n"
            
            logger.info(f"✅ [Alpha Vantage] 成功获取 {len(feed)} 条新闻")
            return result
        else:
            return format_response_as_string(data, f"News for {ticker}")
            
    except Exception as e:
        logger.error(f"❌ [Alpha Vantage] 获取新闻失败 {ticker}: {e}")
        return f"Error retrieving news for {ticker}: {str(e)}"


def get_insider_transactions(
    symbol: Annotated[str, "Ticker symbol, e.g., IBM"]
) -> str:
    """
    获取内部人交易数据
    
    返回关键利益相关者（创始人、高管、董事会成员等）的最新和历史内部人交易数据。
    
    Args:
        symbol: 股票代码
        
    Returns:
        格式化的内部人交易数据字符串（JSON格式）
        
    Example:
        >>> transactions = get_insider_transactions("AAPL")
    """
    try:
        logger.info(f"👔 [Alpha Vantage] 获取内部人交易: {symbol}")
        
        # 构建请求参数
        params = {
            "symbol": symbol.upper(),
        }
        
        # 发起 API 请求
        data = _make_api_request("INSIDER_TRANSACTIONS", params)
        
        # 格式化响应
        if isinstance(data, dict):
            transactions = data.get("data", [])
            
            if not transactions:
                return f"# No insider transactions found for {symbol}\n"
            
            # 构建格式化输出
            result = f"# Insider Transactions for {symbol.upper()}\n"
            result += f"# Total transactions: {len(transactions)}\n"
            result += f"# Retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # 添加每笔交易
            for idx, txn in enumerate(transactions[:20], 1):  # 限制显示前20笔
                result += f"## Transaction {idx}\n"
                result += f"**Insider**: {txn.get('insider_name', 'N/A')}\n"
                result += f"**Title**: {txn.get('insider_title', 'N/A')}\n"
                result += f"**Transaction Type**: {txn.get('transaction_type', 'N/A')}\n"
                result += f"**Date**: {txn.get('transaction_date', 'N/A')}\n"
                result += f"**Shares**: {txn.get('shares_traded', 'N/A')}\n"
                result += f"**Price**: ${txn.get('price_per_share', 'N/A')}\n"
                result += f"**Value**: ${txn.get('transaction_value', 'N/A')}\n"
                result += f"**Shares Owned After**: {txn.get('shares_owned_after_transaction', 'N/A')}\n"
                result += "\n---\n\n"
            
            logger.info(f"✅ [Alpha Vantage] 成功获取 {len(transactions)} 笔内部人交易")
            return result
        else:
            return format_response_as_string(data, f"Insider Transactions for {symbol}")
            
    except Exception as e:
        logger.error(f"❌ [Alpha Vantage] 获取内部人交易失败 {symbol}: {e}")
        return f"Error retrieving insider transactions for {symbol}: {str(e)}"


def get_market_news(
    topics: Annotated[str, "News topics, e.g., 'technology,earnings'"] = None,
    start_date: Annotated[str, "Start date, YYYY-MM-DD"] = None,
    end_date: Annotated[str, "End date, YYYY-MM-DD"] = None,
    limit: Annotated[int, "Number of articles to return"] = 50
) -> str:
    """
    获取市场整体新闻（不限定特定股票）
    
    Args:
        topics: 新闻主题，多个主题用逗号分隔（可选）
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
        limit: 返回文章数量，默认50
        
    Returns:
        格式化的新闻数据字符串
        
    Example:
        >>> news = get_market_news(topics="technology,earnings", limit=20)
    """
    try:
        logger.info(f"📰 [Alpha Vantage] 获取市场新闻: topics={topics}")
        
        # 构建请求参数
        params = {
            "sort": "LATEST",
            "limit": str(limit),
        }
        
        if topics:
            params["topics"] = topics
        
        if start_date:
            params["time_from"] = format_datetime_for_api(start_date)
        
        if end_date:
            params["time_to"] = format_datetime_for_api(end_date)
        
        # 发起 API 请求
        data = _make_api_request("NEWS_SENTIMENT", params)
        
        # 格式化响应（类似 get_news）
        if isinstance(data, dict):
            feed = data.get("feed", [])
            
            if not feed:
                return "# No market news found\n"
            
            result = f"# Market News\n"
            if topics:
                result += f"# Topics: {topics}\n"
            if start_date and end_date:
                result += f"# Period: {start_date} to {end_date}\n"
            result += f"# Total articles: {len(feed)}\n"
            result += f"# Retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            for idx, article in enumerate(feed, 1):
                result += f"## Article {idx}\n"
                result += f"**Title**: {article.get('title', 'N/A')}\n"
                result += f"**Source**: {article.get('source', 'N/A')}\n"
                result += f"**Published**: {article.get('time_published', 'N/A')}\n"
                result += f"**Sentiment**: {article.get('overall_sentiment_label', 'N/A')} "
                result += f"(Score: {article.get('overall_sentiment_score', 'N/A')})\n"
                
                summary = article.get('summary', 'N/A')
                if len(summary) > 200:
                    summary = summary[:200] + "..."
                result += f"**Summary**: {summary}\n\n"
                result += "---\n\n"
            
            logger.info(f"✅ [Alpha Vantage] 成功获取 {len(feed)} 条市场新闻")
            return result
        else:
            return format_response_as_string(data, "Market News")
            
    except Exception as e:
        logger.error(f"❌ [Alpha Vantage] 获取市场新闻失败: {e}")
        return f"Error retrieving market news: {str(e)}"

