#!/usr/bin/env python3
"""
完整基本面分析流程测试
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_full_fundamentals_flow():
    """测试完整的基本面分析流程"""
    print("\n🔍 完整基本面分析流程测试")
    print("=" * 80)
    
    # 测试分众传媒 002027
    test_ticker = "002027"
    print(f"📊 测试股票代码: {test_ticker} (分众传媒)")
    
    try:
        # 设置日志级别
        from tradingagents.utils.logging_init import get_logger
        logger = get_logger("default")
        logger.setLevel("INFO")
        
        print(f"\n🔧 步骤1: 初始化LLM和工具包...")
        
        # 导入必要的模块
        from tradingagents.agents.analysts.fundamentals_analyst import create_fundamentals_analyst
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.llm_adapters import get_llm

        # 获取LLM实例
        llm = get_llm()
        print(f"✅ LLM初始化完成: {type(llm).__name__}")

        # 创建工具包
        toolkit = Toolkit()
        print(f"✅ 工具包初始化完成")
        
        print(f"\n🔧 步骤2: 创建基本面分析师...")
        
        # 创建基本面分析师
        fundamentals_analyst = create_fundamentals_analyst(llm, toolkit)
        print(f"✅ 基本面分析师创建完成")
        
        print(f"\n🔧 步骤3: 准备分析状态...")
        
        # 创建分析状态
        state = {
            "company_of_interest": test_ticker,
            "trade_date": "2025-07-15",
            "messages": []
        }
        
        print(f"✅ 分析状态准备完成")
        print(f"   - 股票代码: {state['company_of_interest']}")
        print(f"   - 交易日期: {state['trade_date']}")
        print(f"   - 消息数量: {len(state['messages'])}")
        
        print(f"\n🔧 步骤4: 执行基本面分析...")
        
        # 执行基本面分析
        result = fundamentals_analyst(state)
        
        print(f"\n✅ 基本面分析执行完成")
        print(f"📊 返回结果类型: {type(result)}")
        
        # 检查返回结果
        if isinstance(result, dict):
            if 'fundamentals_report' in result:
                report = result['fundamentals_report']
                print(f"📄 基本面报告长度: {len(report) if report else 0}")
                
                # 检查报告中的股票代码
                if report:
                    print(f"\n🔍 最终检查报告中的股票代码...")
                    if "002027" in report:
                        print("✅ 报告中包含正确的股票代码 002027")
                        count_002027 = report.count("002027")
                        print(f"   002027 出现次数: {count_002027}")
                    else:
                        print("❌ 报告中不包含正确的股票代码 002027")
                        
                    if "002021" in report:
                        print("⚠️ 报告中包含错误的股票代码 002021")
                        count_002021 = report.count("002021")
                        print(f"   002021 出现次数: {count_002021}")
                        
                        # 找出错误代码的位置
                        import re
                        positions = [m.start() for m in re.finditer("002021", report)]
                        print(f"   002021 出现位置: {positions}")
                        
                        # 显示错误代码周围的文本
                        for pos in positions[:3]:  # 只显示前3个位置
                            start = max(0, pos - 100)
                            end = min(len(report), pos + 100)
                            context = report[start:end]
                            print(f"   位置 {pos} 周围文本: ...{context}...")
                    else:
                        print("✅ 报告中不包含错误的股票代码 002021")
                        
                    # 显示报告的前1000字符
                    print(f"\n📄 报告前1000字符:")
                    print("-" * 80)
                    print(report[:1000])
                    print("-" * 80)
            else:
                print("❌ 返回结果中没有 fundamentals_report")
                print(f"   返回结果键: {list(result.keys())}")
        else:
            print(f"❌ 返回结果类型不正确: {type(result)}")
            if hasattr(result, 'content'):
                print(f"   内容: {result.content[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始完整基本面分析流程测试")
    
    # 执行完整流程测试
    success = test_full_fundamentals_flow()
    
    if success:
        print("\n✅ 测试完成")
    else:
        print("\n❌ 测试失败")
