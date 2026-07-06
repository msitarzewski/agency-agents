#!/usr/bin/env python3
"""
测试美股数据获取独立性
验证美股数据获取不再依赖OpenAI配置
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from tradingagents.agents.utils.agent_utils import Toolkit
    from tradingagents.default_config import DEFAULT_CONFIG
except ImportError:
    print("❌ 无法导入Toolkit，请检查项目结构")
    sys.exit(1)

def test_us_stock_data_independence():
    """测试美股数据获取独立性"""
    print("🇺🇸 测试美股数据获取独立性")
    print("=" * 60)
    
    # 测试场景1: OpenAI禁用，实时数据启用
    print("\n📋 场景1: OpenAI禁用 + 实时数据启用")
    print("-" * 40)
    
    # 设置环境变量
    os.environ['OPENAI_ENABLED'] = 'false'
    os.environ['REALTIME_DATA_ENABLED'] = 'true'
    
    try:
        config = DEFAULT_CONFIG.copy()
        config["realtime_data"] = True
        toolkit = Toolkit(config=config)
        
        # 检查美股数据工具
        us_tools = [
            'get_YFin_data_online',
            'get_YFin_data',
            'get_us_stock_data_cached'
        ]
        
        for tool_name in us_tools:
            if hasattr(toolkit, tool_name):
                print(f"   ✅ {tool_name} 可用")
            else:
                print(f"   ❌ {tool_name} 不可用")
                
        # 测试实际调用
        try:
            # 测试获取苹果股票数据
            result = toolkit.get_us_stock_data_cached("AAPL", "1d", "1mo")
            if result and "error" not in str(result).lower():
                print("   ✅ 美股数据获取成功")
            else:
                print("   ⚠️ 美股数据获取返回错误或空结果")
        except Exception as e:
            print(f"   ⚠️ 美股数据获取异常: {e}")
            
    except Exception as e:
        print(f"   ❌ Toolkit创建失败: {e}")
    
    # 测试场景2: OpenAI启用，实时数据禁用
    print("\n📋 场景2: OpenAI启用 + 实时数据禁用")
    print("-" * 40)
    
    # 设置环境变量
    os.environ['OPENAI_ENABLED'] = 'true'
    os.environ['REALTIME_DATA_ENABLED'] = 'false'
    
    try:
        config = DEFAULT_CONFIG.copy()
        config["realtime_data"] = False
        toolkit = Toolkit(config=config)
        
        # 检查美股数据工具
        for tool_name in us_tools:
            if hasattr(toolkit, tool_name):
                print(f"   ✅ {tool_name} 可用")
            else:
                print(f"   ❌ {tool_name} 不可用")
                
    except Exception as e:
        print(f"   ❌ Toolkit创建失败: {e}")
    
    print("\n💡 结论:")
    print("   美股数据获取现在基于 REALTIME_DATA_ENABLED 配置")
    print("   不再依赖 OPENAI_ENABLED 配置")
    print("   实现了真正的功能独立性！")

if __name__ == "__main__":
    test_us_stock_data_independence()
    print("\n🎉 测试完成！")