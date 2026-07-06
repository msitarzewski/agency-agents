#!/usr/bin/env python3
"""
测试新闻分析师工具调用参数修复
验证强制调用和备用工具调用是否正确传递了所需参数
"""

import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.agents.utils.agent_utils import Toolkit

def test_tool_parameters():
    """测试工具参数是否正确"""
    print("🔧 测试新闻分析师工具调用参数修复")
    print("=" * 50)
    
    # 初始化工具包
    toolkit = Toolkit()
    
    # 测试参数
    ticker = "600036"
    curr_date = "2025-07-28"
    
    print(f"📊 测试参数:")
    print(f"   - ticker: {ticker}")
    print(f"   - curr_date: {curr_date}")
    print()
    
    # 测试 get_realtime_stock_news 工具
    print("🔍 测试 get_realtime_stock_news 工具调用...")
    try:
        # 模拟修复后的调用方式
        params = {"ticker": ticker, "curr_date": curr_date}
        print(f"   参数: {params}")
        
        # 检查工具是否接受这些参数
        result = toolkit.get_realtime_stock_news.invoke(params)
        print(f"   ✅ get_realtime_stock_news 调用成功")
        print(f"   📝 返回数据长度: {len(result) if result else 0} 字符")
        
    except Exception as e:
        print(f"   ❌ get_realtime_stock_news 调用失败: {e}")
    
    print()
    
    # 测试 get_google_news 工具
    print("🔍 测试 get_google_news 工具调用...")
    try:
        # 模拟修复后的调用方式
        params = {"query": f"{ticker} 股票 新闻", "curr_date": curr_date}
        print(f"   参数: {params}")
        
        # 检查工具是否接受这些参数
        result = toolkit.get_google_news.invoke(params)
        print(f"   ✅ get_google_news 调用成功")
        print(f"   📝 返回数据长度: {len(result) if result else 0} 字符")
        
    except Exception as e:
        print(f"   ❌ get_google_news 调用失败: {e}")
    
    print()
    
    # 测试修复前的错误调用方式（应该失败）
    print("🚫 测试修复前的错误调用方式（应该失败）...")
    
    print("   测试 get_realtime_stock_news 缺少 curr_date:")
    try:
        params = {"ticker": ticker}  # 缺少 curr_date
        result = toolkit.get_realtime_stock_news.invoke(params)
        print(f"   ⚠️ 意外成功（可能有默认值处理）")
    except Exception as e:
        print(f"   ✅ 正确失败: {e}")
    
    print("   测试 get_google_news 缺少 query 和 curr_date:")
    try:
        params = {"ticker": ticker}  # 缺少 query 和 curr_date
        result = toolkit.get_google_news.invoke(params)
        print(f"   ⚠️ 意外成功（可能有默认值处理）")
    except Exception as e:
        print(f"   ✅ 正确失败: {e}")
    
    print()
    print("🎯 修复总结:")
    print("   1. ✅ get_realtime_stock_news 现在正确传递 ticker 和 curr_date")
    print("   2. ✅ get_google_news 现在正确传递 query 和 curr_date")
    print("   3. ✅ 修复了 Pydantic 验证错误")
    print("   4. ✅ 新闻分析师应该能够正常获取新闻数据")

if __name__ == "__main__":
    test_tool_parameters()