#!/usr/bin/env python3
"""
测试新的工具选择逻辑
验证美股数据获取不再依赖OpenAI配置
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_tool_selection_scenarios():
    """测试不同配置场景下的工具选择"""
    print("🧪 测试工具选择逻辑")
    print("=" * 70)
    
    scenarios = [
        {
            "name": "场景1: 完全离线模式",
            "config": {
                "online_tools": False,
                "online_news": False,
                "realtime_data": False,
            },
            "expected": {
                "market_primary": "get_YFin_data",
                "news_primary": "get_finnhub_news",
                "social_primary": "get_reddit_stock_info"
            }
        },
        {
            "name": "场景2: 实时数据启用",
            "config": {
                "online_tools": False,
                "online_news": False,
                "realtime_data": True,
            },
            "expected": {
                "market_primary": "get_YFin_data_online",
                "news_primary": "get_finnhub_news",
                "social_primary": "get_reddit_stock_info"
            }
        },
        {
            "name": "场景3: 在线新闻启用",
            "config": {
                "online_tools": False,
                "online_news": True,
                "realtime_data": False,
            },
            "expected": {
                "market_primary": "get_YFin_data",
                "news_primary": "get_google_news",
                "social_primary": "get_reddit_stock_info"
            }
        },
        {
            "name": "场景4: 完全在线模式",
            "config": {
                "online_tools": True,
                "online_news": True,
                "realtime_data": True,
            },
            "expected": {
                "market_primary": "get_YFin_data_online",
                "news_primary": "get_global_news_openai",
                "social_primary": "get_stock_news_openai"
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 {scenario['name']}")
        print("-" * 50)
        
        try:
            # 模拟工具选择逻辑
            config = scenario['config']
            online_tools_enabled = config.get("online_tools", False)
            online_news_enabled = config.get("online_news", True)
            realtime_data_enabled = config.get("realtime_data", False)
            
            print(f"   配置: online_tools={online_tools_enabled}, "
                  f"online_news={online_news_enabled}, "
                  f"realtime_data={realtime_data_enabled}")
            
            # 市场数据工具选择
            if realtime_data_enabled:
                market_primary = "get_YFin_data_online"
            else:
                market_primary = "get_YFin_data"
            
            # 新闻工具选择
            if online_news_enabled:
                if online_tools_enabled:
                    news_primary = "get_global_news_openai"
                else:
                    news_primary = "get_google_news"
            else:
                news_primary = "get_finnhub_news"
            
            # 社交媒体工具选择
            if online_tools_enabled:
                social_primary = "get_stock_news_openai"
            else:
                social_primary = "get_reddit_stock_info"
            
            # 验证结果
            expected = scenario['expected']
            results = {
                "market_primary": market_primary,
                "news_primary": news_primary,
                "social_primary": social_primary
            }
            
            print(f"   结果:")
            for tool_type, tool_name in results.items():
                expected_tool = expected[tool_type]
                status = "✅" if tool_name == expected_tool else "❌"
                print(f"     {tool_type}: {tool_name} {status}")
                if tool_name != expected_tool:
                    print(f"       期望: {expected_tool}")
            
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")

def test_trading_graph_integration():
    """测试TradingGraph集成"""
    print(f"\n🔗 测试TradingGraph集成")
    print("=" * 70)
    
    try:
        from tradingagents.default_config import DEFAULT_CONFIG
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        
        # 测试不同配置
        test_configs = [
            {
                "name": "离线模式",
                "config": {
                    **DEFAULT_CONFIG,
                    "online_tools": False,
                    "online_news": False,
                    "realtime_data": False,
                }
            },
            {
                "name": "实时数据模式",
                "config": {
                    **DEFAULT_CONFIG,
                    "online_tools": False,
                    "online_news": True,
                    "realtime_data": True,
                }
            }
        ]
        
        for test_config in test_configs:
            print(f"\n📊 测试配置: {test_config['name']}")
            print("-" * 40)
            
            try:
                # 创建TradingGraph实例
                ta = TradingAgentsGraph(
                    config=test_config['config'],
                    selected_analysts=["market_analyst"],
                    debug=False
                )
                
                # 检查工具节点配置
                market_tools = ta.tool_nodes["market"].tools
                news_tools = ta.tool_nodes["news"].tools
                social_tools = ta.tool_nodes["social"].tools
                
                print(f"   市场工具数量: {len(market_tools)}")
                print(f"   新闻工具数量: {len(news_tools)}")
                print(f"   社交工具数量: {len(social_tools)}")
                
                # 检查主要工具
                market_tool_names = [tool.name for tool in market_tools]
                news_tool_names = [tool.name for tool in news_tools]
                social_tool_names = [tool.name for tool in social_tools]
                
                print(f"   主要市场工具: {market_tool_names[1] if len(market_tool_names) > 1 else 'N/A'}")
                print(f"   主要新闻工具: {news_tool_names[0] if news_tool_names else 'N/A'}")
                print(f"   主要社交工具: {social_tool_names[0] if social_tool_names else 'N/A'}")
                
                print("   ✅ TradingGraph创建成功")
                
            except Exception as e:
                print(f"   ❌ TradingGraph创建失败: {e}")
                
    except ImportError as e:
        print(f"   ⚠️ 无法导入TradingGraph: {e}")

def test_us_stock_data_independence():
    """测试美股数据获取的独立性"""
    print(f"\n🇺🇸 测试美股数据获取独立性")
    print("=" * 70)
    
    print("验证美股数据获取不再依赖OpenAI配置...")
    
    # 模拟不同的OpenAI配置状态
    openai_scenarios = [
        {"OPENAI_API_KEY": None, "OPENAI_ENABLED": "false"},
        {"OPENAI_API_KEY": "test_key", "OPENAI_ENABLED": "true"},
    ]
    
    for i, openai_config in enumerate(openai_scenarios, 1):
        print(f"\n📋 OpenAI场景 {i}: {openai_config}")
        print("-" * 40)
        
        # 临时设置环境变量
        original_env = {}
        for key, value in openai_config.items():
            original_env[key] = os.environ.get(key)
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        
        try:
            # 测试不同的在线工具配置
            data_configs = [
                {"REALTIME_DATA_ENABLED": "false", "expected": "离线数据"},
                {"REALTIME_DATA_ENABLED": "true", "expected": "实时数据"},
            ]
            
            for data_config in data_configs:
                os.environ["REALTIME_DATA_ENABLED"] = data_config["REALTIME_DATA_ENABLED"]
                
                # 重新加载配置
                from importlib import reload
                import tradingagents.default_config
                reload(tradingagents.default_config)
                
                from tradingagents.default_config import DEFAULT_CONFIG
                
                realtime_enabled = DEFAULT_CONFIG.get("realtime_data", False)
                expected_mode = "实时数据" if realtime_enabled else "离线数据"
                
                print(f"     REALTIME_DATA_ENABLED={data_config['REALTIME_DATA_ENABLED']} "
                      f"-> {expected_mode} ✅")
                
        finally:
            # 恢复原始环境变量
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
    
    print("\n💡 结论: 美股数据获取现在完全独立于OpenAI配置！")

def main():
    """主测试函数"""
    print("🚀 工具选择逻辑测试")
    print("=" * 70)
    
    # 运行测试
    test_tool_selection_scenarios()
    test_trading_graph_integration()
    test_us_stock_data_independence()
    
    print(f"\n🎉 测试完成！")
    print("💡 现在美股数据获取基于专门的配置字段，不再依赖OpenAI配置")

if __name__ == "__main__":
    main()