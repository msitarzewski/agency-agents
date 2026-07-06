#!/usr/bin/env python3
"""
测试新闻获取超时修复

这个测试程序验证新闻获取超时修复的有效性，特别是在一个新闻源失败时能否正确轮询到下一个新闻源。
"""

import sys
import os
import time
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入需要测试的模块
from tradingagents.dataflows.realtime_news_utils import get_realtime_stock_news
from tradingagents.dataflows.googlenews_utils import getNewsData, make_request
from tradingagents.dataflows.akshare_utils import get_stock_news_em


class TestNewsTimeoutFix(unittest.TestCase):
    """测试新闻获取超时修复"""

    def setUp(self):
        """测试前的准备工作"""
        self.ticker = "600036.SH"  # 招商银行
        self.curr_date = datetime.now().strftime("%Y-%m-%d")

    def test_make_request_timeout(self):
        """测试make_request函数的超时处理"""
        # 模拟请求超时
        with patch('requests.get') as mock_get:
            # 设置mock抛出超时异常
            import requests
            from tenacity import RetryError
            mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
            
            # 测试make_request函数
            with self.assertRaises(RetryError):
                make_request("https://www.google.com", {})
                
            # 验证重试机制
            self.assertEqual(mock_get.call_count, 5)  # 应该尝试5次

    def test_news_source_fallback(self):
        """测试新闻源轮询机制"""
        # 模拟实时新闻聚合器失败
        with patch('tradingagents.dataflows.realtime_news_utils.RealtimeNewsAggregator.get_realtime_stock_news') as mock_aggregator:
            mock_aggregator.side_effect = Exception("模拟实时新闻聚合器失败")
            
            # 模拟Google新闻获取失败
            with patch('tradingagents.dataflows.interface.get_google_news') as mock_google_news:
                mock_google_news.side_effect = Exception("模拟Google新闻获取失败")
                
                # 模拟东方财富新闻获取成功
                with patch('tradingagents.dataflows.akshare_utils.get_stock_news_em') as mock_em_news:
                    # 创建一个模拟的DataFrame作为返回值
                    mock_df = pd.DataFrame({
                        '标题': ['测试新闻1', '测试新闻2'],
                        '时间': ['2023-01-01 12:00:00', '2023-01-01 13:00:00'],
                        '内容': ['测试内容1', '测试内容2'],
                        '链接': ['http://example.com/1', 'http://example.com/2']
                    })
                    mock_em_news.return_value = mock_df
                    
                    # 调用测试函数
                    result = get_realtime_stock_news(self.ticker, self.curr_date)
                    
                    # 验证结果
                    self.assertIn("东方财富新闻报告", result)
                    self.assertIn("测试新闻1", result)
                    self.assertIn("测试新闻2", result)
                    
                    # 验证调用顺序
                    mock_aggregator.assert_called_once()
                    mock_google_news.assert_called_once()
                    mock_em_news.assert_called_once()

    def test_all_news_sources_fail(self):
        """测试所有新闻源都失败的情况"""
        # 模拟所有新闻源都失败
        with patch('tradingagents.dataflows.realtime_news_utils.RealtimeNewsAggregator.get_realtime_stock_news') as mock_aggregator:
            mock_aggregator.side_effect = Exception("模拟实时新闻聚合器失败")
            
            with patch('tradingagents.dataflows.interface.get_google_news') as mock_google_news:
                mock_google_news.side_effect = Exception("模拟Google新闻获取失败")
                
                with patch('tradingagents.dataflows.akshare_utils.get_stock_news_em') as mock_em_news:
                    mock_em_news.side_effect = Exception("模拟东方财富新闻获取失败")
                    
                    # 调用测试函数
                    result = get_realtime_stock_news(self.ticker, self.curr_date)
                    
                    # 验证结果
                    self.assertIn("实时新闻获取失败", result)
                    self.assertIn("所有可用的新闻源都未能获取到相关新闻", result)
                    
                    # 验证调用顺序
                    mock_aggregator.assert_called_once()
                    mock_google_news.assert_called_once()
                    mock_em_news.assert_called_once()


if __name__ == "__main__":
    unittest.main()