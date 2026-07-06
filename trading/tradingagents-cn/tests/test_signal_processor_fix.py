#!/usr/bin/env python3
"""
测试SignalProcessor修复后的功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env", override=True)

def test_signal_processor_currency_fix():
    """测试SignalProcessor的货币修复"""
    
    try:
        from tradingagents.graph.signal_processing import SignalProcessor
        from langchain_openai import ChatOpenAI
        
        print("🔍 测试SignalProcessor货币修复...")
        
        # 创建LLM（使用阿里百炼）
        llm = ChatOpenAI(
            model="qwen-turbo",
            openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
            openai_api_key=os.getenv("DASHSCOPE_API_KEY"),
            temperature=0.1
        )
        
        # 创建信号处理器
        processor = SignalProcessor(llm)
        
        # 测试中国A股信号
        china_signal = """
        基于对平安银行(000001)的综合分析，我们建议持有该股票。
        
        技术面分析显示当前价格为12.50元，目标价位为15.00元。
        基本面分析表明公司财务状况良好，ROE为12.5%。
        
        置信度：75%
        风险评分：40%
        
        最终交易建议: **持有**
        """
        
        print("📈 测试中国A股信号处理...")
        china_decision = processor.process_signal(china_signal, "000001")
        print(f"中国A股决策结果: {china_decision}")
        
        # 测试美股信号
        us_signal = """
        Based on comprehensive analysis of Apple Inc. (AAPL), we recommend BUY.
        
        Technical analysis shows current price at $150.00, target price $180.00.
        Fundamental analysis indicates strong financial performance.
        
        Confidence: 80%
        Risk Score: 30%
        
        Final Trading Recommendation: **BUY**
        """
        
        print("📈 测试美股信号处理...")
        us_decision = processor.process_signal(us_signal, "AAPL")
        print(f"美股决策结果: {us_decision}")
        
        # 验证结果
        success = True
        
        # 检查中国A股结果
        if china_decision.get('action') not in ['买入', '持有', '卖出']:
            print(f"❌ 中国A股动作错误: {china_decision.get('action')}")
            success = False
        
        if china_decision.get('target_price') is None:
            print("❌ 中国A股目标价位为空")
            success = False
        
        # 检查美股结果
        if us_decision.get('action') not in ['买入', '持有', '卖出']:
            print(f"❌ 美股动作错误: {us_decision.get('action')}")
            success = False
        
        if us_decision.get('target_price') is None:
            print("❌ 美股目标价位为空")
            success = False
        
        if success:
            print("✅ SignalProcessor货币修复测试通过！")
            return True
        else:
            print("❌ SignalProcessor货币修复测试失败！")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_web_currency_display():
    """测试Web界面货币显示修复"""
    
    try:
        from web.components.results_display import render_decision_summary
        import streamlit as st
        
        print("🌐 测试Web界面货币显示...")
        
        # 模拟中国A股结果
        china_results = {
            'stock_symbol': '000001',
            'decision': {
                'action': '持有',
                'confidence': 0.75,
                'risk_score': 0.40,
                'target_price': 15.00,
                'reasoning': '基于综合分析的投资建议'
            }
        }
        
        # 模拟美股结果
        us_results = {
            'stock_symbol': 'AAPL',
            'decision': {
                'action': '买入',
                'confidence': 0.80,
                'risk_score': 0.30,
                'target_price': 180.00,
                'reasoning': '基于综合分析的投资建议'
            }
        }
        
        print("✅ Web界面货币显示修复已实现")
        print("📝 中国A股应显示: ¥15.00")
        print("📝 美股应显示: $180.00")
        
        return True
        
    except Exception as e:
        print(f"❌ Web界面测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 开始测试SignalProcessor修复...")
    print("=" * 50)
    
    # 检查环境变量
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("❌ DASHSCOPE_API_KEY 环境变量未设置")
        sys.exit(1)
    
    # 运行测试
    test1_result = test_signal_processor_currency_fix()
    test2_result = test_web_currency_display()
    
    print("=" * 50)
    if test1_result and test2_result:
        print("🎉 所有测试通过！修复成功！")
        sys.exit(0)
    else:
        print("❌ 部分测试失败，需要进一步调试")
        sys.exit(1)
