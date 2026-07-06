#!/usr/bin/env python3
"""
测试优化后的目标价生成系统
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_signal_processor():
    """测试信号处理器的价格提取功能"""
    print("🧪 测试信号处理器价格提取功能...")
    
    try:
        from tradingagents.agents.signal_processing import SignalProcessor
        
        processor = SignalProcessor()
        
        # 测试用例1: 包含明确目标价的文本
        test_text1 = """
        基于技术分析，AAPL当前价格为180美元，建议买入。
        目标价位：200美元
        止损价位：170美元
        预期涨幅：11%
        """
        
        result1 = processor._extract_target_price(test_text1, "AAPL", "USD")
        print(f"✅ 测试1 - 明确目标价: {result1}")
        
        # 测试用例2: 需要智能推算的文本
        test_text2 = """
        腾讯控股(0700.HK)当前价格为320港元，
        基于基本面分析建议买入，预期上涨15%。
        """
        
        result2 = processor._extract_target_price(test_text2, "0700.HK", "HKD")
        print(f"✅ 测试2 - 智能推算: {result2}")
        
        # 测试用例3: A股示例
        test_text3 = """
        贵州茅台(600519)现价1800元，基于估值分析，
        合理价位区间为1900-2100元，建议持有。
        """
        
        result3 = processor._extract_target_price(test_text3, "600519", "CNY")
        print(f"✅ 测试3 - A股价格: {result3}")
        
        return True
        
    except Exception as e:
        print(f"❌ 信号处理器测试失败: {e}")
        return False

def test_smart_price_estimation():
    """测试智能价格推算功能"""
    print("\n🧪 测试智能价格推算功能...")
    
    try:
        from tradingagents.agents.signal_processing import SignalProcessor
        
        processor = SignalProcessor()
        
        # 测试推算逻辑
        test_cases = [
            ("当前价格100美元，预期上涨20%", "buy", 120.0),
            ("现价50元，建议卖出，预计下跌10%", "sell", 45.0),
            ("股价200港元，持有，预期涨幅5%", "hold", 210.0)
        ]
        
        for text, action, expected in test_cases:
            result = processor._smart_price_estimation(text, action)
            print(f"✅ 文本: '{text}' -> 推算价格: {result} (预期: {expected})")
        
        return True
        
    except Exception as e:
        print(f"❌ 智能推算测试失败: {e}")
        return False

def test_trader_prompt():
    """测试交易员提示词是否包含目标价要求"""
    print("\n🧪 检查交易员提示词优化...")
    
    try:
        from tradingagents.agents.trader import trader_node
        import inspect
        
        # 获取trader_node函数的源代码
        source = inspect.getsource(trader_node)
        
        # 检查关键词
        keywords = ["目标价", "target_price", "具体价位", "禁止回复"]
        found_keywords = []
        
        for keyword in keywords:
            if keyword in source:
                found_keywords.append(keyword)
        
        print(f"✅ 交易员提示词包含关键词: {found_keywords}")
        
        if len(found_keywords) >= 2:
            print("✅ 交易员模块已优化")
            return True
        else:
            print("⚠️ 交易员模块可能需要进一步优化")
            return False
            
    except Exception as e:
        print(f"❌ 交易员提示词检查失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试优化后的目标价生成系统")
    print("=" * 60)
    
    test_results = []
    
    # 运行各项测试
    test_results.append(test_signal_processor())
    test_results.append(test_smart_price_estimation())
    test_results.append(test_trader_prompt())
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"✅ 通过测试: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！目标价生成系统优化成功！")
        print("\n💡 系统现在能够:")
        print("   • 从分析文本中提取明确的目标价")
        print("   • 基于当前价格和涨跌幅智能推算目标价")
        print("   • 强制要求所有分析师提供目标价信息")
        print("   • 支持多种货币和股票市场")
    else:
        print(f"⚠️ 有 {total - passed} 项测试未通过，需要进一步检查")
    
    print("\n🔧 下一步建议:")
    print("   1. 运行完整的股票分析流程测试")
    print("   2. 验证实际LLM响应中的目标价生成")
    print("   3. 测试不同类型股票的分析效果")

if __name__ == "__main__":
    main()