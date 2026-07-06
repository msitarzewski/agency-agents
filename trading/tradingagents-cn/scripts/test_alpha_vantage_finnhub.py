#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Alpha Vantage 和 Finnhub 数据源
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("🧪 测试 Alpha Vantage 和 Finnhub 数据源")
print("=" * 80)

# 测试 Alpha Vantage
print("\n📊 测试 Alpha Vantage GLOBAL_QUOTE API")
print("-" * 80)

try:
    from tradingagents.dataflows.providers.us.alpha_vantage_common import get_api_key, _make_api_request
    
    # 检查 API Key
    try:
        api_key = get_api_key()
        print(f"✅ Alpha Vantage API Key: {api_key[:8]}...")
    except Exception as e:
        print(f"❌ Alpha Vantage API Key 未配置: {e}")
        api_key = None
    
    if api_key:
        # 测试获取 AAPL 行情
        print("\n测试获取 AAPL 行情...")
        try:
            params = {"symbol": "AAPL"}
            data = _make_api_request("GLOBAL_QUOTE", params)
            
            if data and "Global Quote" in data:
                quote = data["Global Quote"]
                print(f"✅ 成功获取数据:")
                print(f"  股票代码: {quote.get('01. symbol')}")
                print(f"  最新价格: ${quote.get('05. price')}")
                print(f"  涨跌额: ${quote.get('09. change')}")
                print(f"  涨跌幅: {quote.get('10. change percent')}")
                print(f"  成交量: {quote.get('06. volume')}")
            else:
                print(f"❌ 返回数据格式错误: {data}")
        except Exception as e:
            print(f"❌ 获取失败: {e}")
            
except Exception as e:
    print(f"❌ Alpha Vantage 测试失败: {e}")

# 测试 Finnhub
print("\n" + "=" * 80)
print("📊 测试 Finnhub Quote API")
print("-" * 80)

try:
    import finnhub
    import os
    
    # 检查 API Key
    api_key = os.getenv('FINNHUB_API_KEY')
    if api_key:
        print(f"✅ Finnhub API Key: {api_key[:8]}...")
        
        # 创建客户端
        client = finnhub.Client(api_key=api_key)
        
        # 测试获取 AAPL 行情
        print("\n测试获取 AAPL 行情...")
        try:
            quote = client.quote('AAPL')
            
            if quote and 'c' in quote:
                print(f"✅ 成功获取数据:")
                print(f"  当前价格: ${quote.get('c')}")
                print(f"  开盘价: ${quote.get('o')}")
                print(f"  最高价: ${quote.get('h')}")
                print(f"  最低价: ${quote.get('l')}")
                print(f"  前收盘: ${quote.get('pc')}")
                print(f"  涨跌额: ${quote.get('d')}")
                print(f"  涨跌幅: {quote.get('dp')}%")
            else:
                print(f"❌ 返回数据格式错误: {quote}")
        except Exception as e:
            print(f"❌ 获取失败: {e}")
    else:
        print("❌ Finnhub API Key 未配置")
        
except ImportError:
    print("❌ finnhub 模块未安装，请运行: pip install finnhub-python")
except Exception as e:
    print(f"❌ Finnhub 测试失败: {e}")

print("\n" + "=" * 80)
print("✅ 测试完成")
print("=" * 80)

