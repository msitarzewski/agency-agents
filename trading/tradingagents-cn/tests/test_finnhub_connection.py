#!/usr/bin/env python3
"""
测试FINNHUB API连接
"""

import sys
import os
sys.path.append('..')

def test_finnhub_api():
    """测试FINNHUB API连接"""
    print("🔍 测试FINNHUB API连接...")
    
    # 检查API密钥
    finnhub_key = os.getenv("FINNHUB_API_KEY")
    if not finnhub_key:
        print("❌ 请设置 FINNHUB_API_KEY 环境变量")
        return False
    
    print(f"✅ FINNHUB API密钥已配置: {finnhub_key[:10]}...")
    
    try:
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 创建配置
        config = DEFAULT_CONFIG.copy()
        config['online_tools'] = True
        
        # 创建工具包
        toolkit = Toolkit()
        toolkit.update_config(config)
        
        # 测试FINNHUB新闻API
        print(f"\n📰 测试FINNHUB新闻API...")
        try:
            news_result = toolkit.get_finnhub_news.invoke({
                'ticker': 'AAPL',
                'start_date': '2025-06-25',
                'end_date': '2025-06-29'
            })
            print(f"✅ FINNHUB新闻API调用成功")
            print(f"新闻数据长度: {len(news_result) if news_result else 0}")
            if news_result and len(news_result) > 100:
                print(f"新闻内容前200字符:")
                print(news_result[:200])
            else:
                print(f"新闻内容: {news_result}")
        except Exception as e:
            print(f"❌ FINNHUB新闻API调用失败: {e}")
        
        # 测试Yahoo Finance数据API
        print(f"\n📊 测试Yahoo Finance数据API...")
        try:
            stock_result = toolkit.get_YFin_data_online.invoke({
                'symbol': 'AAPL',
                'start_date': '2025-06-25',
                'end_date': '2025-06-29'
            })
            print(f"✅ Yahoo Finance API调用成功")
            print(f"股票数据长度: {len(stock_result) if stock_result else 0}")
            if stock_result and len(stock_result) > 100:
                print(f"股票数据前200字符:")
                print(stock_result[:200])
            else:
                print(f"股票数据: {stock_result}")
        except Exception as e:
            print(f"❌ Yahoo Finance API调用失败: {e}")
        
        # 测试OpenAI基本面API
        print(f"\n💼 测试OpenAI基本面API...")
        try:
            fundamentals_result = toolkit.get_fundamentals_openai.invoke({
                'ticker': 'AAPL',
                'curr_date': '2025-06-29'
            })
            print(f"✅ OpenAI基本面API调用成功")
            print(f"基本面数据长度: {len(fundamentals_result) if fundamentals_result else 0}")
            if fundamentals_result and len(fundamentals_result) > 100:
                print(f"基本面数据前200字符:")
                print(fundamentals_result[:200])
            else:
                print(f"基本面数据: {fundamentals_result}")
        except Exception as e:
            print(f"❌ OpenAI基本面API调用失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_china_stock_api():
    """测试中国股票API连接"""
    print("\n" + "="*50)
    print("🔍 测试中国股票API连接...")
    
    try:
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 创建配置
        config = DEFAULT_CONFIG.copy()
        config['online_tools'] = True
        
        # 创建工具包
        toolkit = Toolkit()
        toolkit.update_config(config)
        
        # 测试中国股票数据API
        print(f"\n📊 测试中国股票数据API...")
        try:
            china_result = toolkit.get_china_stock_data.invoke({
                'stock_code': '000001',
                'start_date': '2025-06-25',
                'end_date': '2025-06-29'
            })
            print(f"✅ 中国股票数据API调用成功")
            print(f"股票数据长度: {len(china_result) if china_result else 0}")
            if china_result and len(china_result) > 100:
                print(f"股票数据前200字符:")
                print(china_result[:200])
            else:
                print(f"股票数据: {china_result}")
        except Exception as e:
            print(f"❌ 中国股票数据API调用失败: {e}")
        
        # 测试中国股票基本面API
        print(f"\n💼 测试中国股票基本面API...")
        try:
            china_fundamentals_result = toolkit.get_china_fundamentals.invoke({
                'ticker': '000001',
                'curr_date': '2025-06-29'
            })
            print(f"✅ 中国股票基本面API调用成功")
            print(f"基本面数据长度: {len(china_fundamentals_result) if china_fundamentals_result else 0}")
            if china_fundamentals_result and len(china_fundamentals_result) > 100:
                print(f"基本面数据前200字符:")
                print(china_fundamentals_result[:200])
            else:
                print(f"基本面数据: {china_fundamentals_result}")
        except Exception as e:
            print(f"❌ 中国股票基本面API调用失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始API连接测试")
    print("="*50)
    
    # 测试美股API
    result1 = test_finnhub_api()
    
    # 测试中国股票API
    result2 = test_china_stock_api()
    
    print("\n" + "="*50)
    print("🎯 测试总结:")
    print(f"美股API测试: {'✅ 成功' if result1 else '❌ 失败'}")
    print(f"中国股票API测试: {'✅ 成功' if result2 else '❌ 失败'}")
    
    if result1 and result2:
        print("🎉 所有API连接正常，可以进行股票分析！")
    else:
        print("⚠️ 部分API连接有问题，请检查配置和网络连接。")
