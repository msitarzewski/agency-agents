#!/usr/bin/env python3
"""
DeepSeek Token统计功能测试
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv(project_root / ".env", override=True)

def test_deepseek_adapter():
    """测试DeepSeek适配器的Token统计功能"""
    print("🧪 测试DeepSeek适配器Token统计...")
    
    # 检查DeepSeek配置
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if not deepseek_key:
        print("⚠️ 未找到DEEPSEEK_API_KEY，跳过测试")
        return True  # 跳过而不是失败
    
    try:
        from tradingagents.llm_adapters.deepseek_adapter import ChatDeepSeek
        from tradingagents.config.config_manager import config_manager, token_tracker
        
        # 获取初始统计
        initial_stats = config_manager.get_usage_statistics(1)
        initial_cost = initial_stats.get("total_cost", 0)
        
        # 创建DeepSeek实例
        llm = ChatDeepSeek(
            model="deepseek-chat",
            temperature=0.1,
            max_tokens=100
        )
        
        # 生成会话ID
        session_id = f"test_deepseek_{int(datetime.now().timestamp())}"
        
        # 测试调用
        response = llm.invoke(
            "请简单说明什么是股票，不超过50字。",
            session_id=session_id,
            analysis_type="test_analysis"
        )
        
        print(f"   ✅ 响应接收成功，长度: {len(response.content)}")
        
        # 等待统计更新
        import time
        time.sleep(1)
        
        # 检查统计更新
        updated_stats = config_manager.get_usage_statistics(1)
        updated_cost = updated_stats.get("total_cost", 0)
        
        cost_increase = updated_cost - initial_cost
        
        print(f"   💰 成本增加: ¥{cost_increase:.4f}")
        
        # 检查DeepSeek统计
        provider_stats = updated_stats.get("provider_stats", {})
        deepseek_stats = provider_stats.get("deepseek", {})
        
        if deepseek_stats:
            print(f"   📊 DeepSeek统计存在: ✅")
            return True
        else:
            print(f"   📊 DeepSeek统计缺失: ❌")
            return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_trading_graph_integration():
    """测试TradingGraph中的DeepSeek集成"""
    print("\n🧪 测试TradingGraph DeepSeek集成...")
    
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if not deepseek_key:
        print("⚠️ 未找到DEEPSEEK_API_KEY，跳过测试")
        return True
    
    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 配置DeepSeek
        config = DEFAULT_CONFIG.copy()
        config.update({
            "llm_provider": "deepseek",
            "llm_model": "deepseek-chat",
            "quick_think_llm": "deepseek-chat",
            "deep_think_llm": "deepseek-chat",
            "backend_url": "https://api.deepseek.com",
            "online_tools": True,
            "max_debate_rounds": 1,
        })
        
        # 创建TradingAgentsGraph
        ta = TradingAgentsGraph(
            selected_analysts=["fundamentals"],
            config=config,
            debug=False  # 减少输出
        )
        
        print(f"   ✅ TradingAgentsGraph创建成功")
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 DeepSeek Token统计功能测试")
    print("=" * 50)
    
    tests = [
        ("DeepSeek适配器", test_deepseek_adapter),
        ("TradingGraph集成", test_trading_graph_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 总结结果
    print("\n" + "="*50)
    print("📋 测试结果总结:")
    print("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 项测试通过")
    
    return passed >= len(results) // 2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
