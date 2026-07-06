#!/usr/bin/env python3
"""
基本面分析股票代码追踪测试
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_fundamentals_analyst():
    """测试基本面分析师的股票代码处理"""
    print("\n🔍 基本面分析师股票代码追踪测试")
    print("=" * 80)
    
    # 测试分众传媒 002027
    test_ticker = "002027"
    print(f"📊 测试股票代码: {test_ticker} (分众传媒)")
    
    try:
        # 设置日志级别
        from tradingagents.utils.logging_init import get_logger
        logger = get_logger("default")
        logger.setLevel("INFO")
        
        # 创建模拟状态
        state = {
            "company_of_interest": test_ticker,
            "trade_date": "2025-07-15",
            "messages": []
        }
        
        print(f"\n🔧 开始调用基本面分析师...")
        
        # 导入基本面分析师
        from tradingagents.agents.analysts.fundamentals_analyst import fundamentals_analyst
        from tradingagents.agents.utils.agent_utils import AgentUtils
        
        # 创建工具包
        toolkit = AgentUtils()
        
        # 调用基本面分析师
        result = fundamentals_analyst(state, toolkit)
        
        print(f"\n✅ 基本面分析师调用完成")
        print(f"📊 返回状态类型: {type(result)}")
        
        # 检查返回的状态
        if isinstance(result, dict):
            if 'fundamentals_report' in result:
                report = result['fundamentals_report']
                print(f"📄 基本面报告长度: {len(report) if report else 0}")
                
                # 检查报告中的股票代码
                if report:
                    print(f"\n🔍 检查报告中的股票代码...")
                    if "002027" in report:
                        print("✅ 报告中包含正确的股票代码 002027")
                    else:
                        print("❌ 报告中不包含正确的股票代码 002027")
                        
                    if "002021" in report:
                        print("⚠️ 报告中包含错误的股票代码 002021")
                    else:
                        print("✅ 报告中不包含错误的股票代码 002021")
                        
                    # 显示报告的前500字符
                    print(f"\n📄 报告前500字符:")
                    print("-" * 60)
                    print(report[:500])
                    print("-" * 60)
            else:
                print("❌ 返回状态中没有 fundamentals_report")
        else:
            print(f"❌ 返回结果类型不正确: {type(result)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_unified_tool_direct():
    """直接测试统一基本面工具"""
    print("\n🔧 直接测试统一基本面工具")
    print("=" * 80)
    
    test_ticker = "002027"
    
    try:
        # 设置日志级别
        from tradingagents.utils.logging_init import get_logger
        logger.setLevel("INFO")
        
        # 导入工具包
        from tradingagents.agents.utils.agent_utils import AgentUtils
        
        # 创建工具包实例
        toolkit = AgentUtils()
        
        print(f"\n🔧 调用统一基本面工具...")
        
        # 直接调用统一基本面工具
        result = toolkit.get_stock_fundamentals_unified.invoke({
            'ticker': test_ticker,
            'start_date': '2025-06-01',
            'end_date': '2025-07-15',
            'curr_date': '2025-07-15'
        })
        
        print(f"\n✅ 统一基本面工具调用完成")
        print(f"📊 返回结果长度: {len(result) if result else 0}")
        
        # 检查结果中的股票代码
        if result:
            print(f"\n🔍 检查结果中的股票代码...")
            if "002027" in result:
                print("✅ 结果中包含正确的股票代码 002027")
            else:
                print("❌ 结果中不包含正确的股票代码 002027")
                
            if "002021" in result:
                print("⚠️ 结果中包含错误的股票代码 002021")
            else:
                print("✅ 结果中不包含错误的股票代码 002021")
                
            # 显示结果的前500字符
            print(f"\n📄 结果前500字符:")
            print("-" * 60)
            print(result[:500])
            print("-" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始基本面分析股票代码追踪测试")
    
    # 测试1: 直接测试统一工具
    success1 = test_unified_tool_direct()
    
    # 测试2: 测试基本面分析师
    success2 = test_fundamentals_analyst()
    
    if success1 and success2:
        print("\n✅ 所有测试通过")
    else:
        print("\n❌ 部分测试失败")
