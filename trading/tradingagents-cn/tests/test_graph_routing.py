#!/usr/bin/env python3
"""
测试图路由修复
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv()

def test_graph_routing():
    """测试图路由是否正常工作"""
    print("🔬 测试图路由修复")
    print("=" * 60)
    
    # 检查API密钥
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("❌ 未找到DEEPSEEK_API_KEY，无法测试")
        return False
    
    try:
        from tradingagents.graph.setup import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG
        
        print("🔧 创建交易分析图...")
        
        # 配置DeepSeek
        config = DEFAULT_CONFIG.copy()
        config.update({
            "llm_provider": "deepseek",
            "deep_think_llm": "deepseek-chat",
            "quick_think_llm": "deepseek-chat",
            "max_debate_rounds": 1,  # 减少轮次，快速测试
            "max_risk_discuss_rounds": 1,
            "online_tools": False,  # 关闭在线工具，减少复杂度
            "memory_enabled": False
        })
        
        print(f"📊 配置信息:")
        print(f"   LLM提供商: {config['llm_provider']}")
        print(f"   深度思考模型: {config['deep_think_llm']}")
        print(f"   快速思考模型: {config['quick_think_llm']}")
        
        # 创建图实例
        graph = TradingAgentsGraph(config)
        
        # 设置分析师（只选择市场分析师，减少复杂度）
        print(f"📈 设置分析师...")
        graph.setup_and_compile(selected_analysts=["market"])
        
        print(f"✅ 图设置完成")
        
        # 准备输入
        input_data = {
            "company_of_interest": "AAPL",  # 使用美股，减少复杂度
            "trade_date": "2025-07-08"
        }
        
        print(f"\n📊 开始测试分析: {input_data['company_of_interest']}")
        print(f"📅 交易日期: {input_data['trade_date']}")
        print("\n" + "="*60)
        print("开始图路由测试，观察是否有KeyError...")
        print("="*60)
        
        # 运行分析
        result = graph.run(input_data)
        
        print("="*60)
        print("图路由测试完成！")
        print("="*60)
        
        # 输出结果摘要
        if result and "decision" in result:
            decision = result["decision"]
            print(f"\n📋 分析结果摘要:")
            print(f"   投资建议: {decision.get('action', 'N/A')}")
            print(f"   置信度: {decision.get('confidence', 'N/A')}")
            print(f"   目标价格: {decision.get('target_price', 'N/A')}")
            
            return True
        else:
            print("❌ 未获得有效的分析结果")
            return False
        
    except KeyError as e:
        print(f"❌ 图路由KeyError: {e}")
        print("   这表明节点名称映射仍有问题")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🔬 图路由修复测试")
    print("=" * 80)
    print("📝 这个测试将验证图路由是否正常工作")
    print("📝 主要检查是否还有KeyError: 'Bull Researcher'错误")
    print("=" * 80)
    
    success = test_graph_routing()
    
    if success:
        print("\n🎉 图路由测试成功！")
        print("   KeyError问题已修复")
    else:
        print("\n❌ 图路由测试失败")
        print("   需要进一步调试")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
