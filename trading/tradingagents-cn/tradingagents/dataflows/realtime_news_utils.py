#!/usr/bin/env python3
"""
实时新闻工具兼容层
为了保持向后兼容性，从 news.realtime_news 模块导出函数
"""

from tradingagents.dataflows.news.realtime_news import (
    get_realtime_stock_news,
    RealtimeNewsAggregator,
    NewsItem
)

__all__ = [
    'get_realtime_stock_news',
    'RealtimeNewsAggregator',
    'NewsItem'
]

