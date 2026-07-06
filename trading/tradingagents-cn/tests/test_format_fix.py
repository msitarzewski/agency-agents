#!/usr/bin/env python3
"""
测试格式化修复
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_format_analysis_results():
    """测试分析结果格式化函数"""
    
    from web.utils.analysis_runner import format_analysis_results
    
    print("🧪 测试分析结果格式化")
    print("=" * 50)
    
    # 测试案例1: decision 是字符串
    print("测试案例1: decision 是字符串")
    results1 = {
        'stock_symbol': 'AAPL',
        'analysis_date': '2025-06-27',
        'analysts': ['market', 'fundamentals'],
        'research_depth': 3,
        'llm_model': 'qwen-plus',
        'state': {
            'market_report': '技术分析报告...',
            'fundamentals_report': '基本面分析报告...'
        },
        'decision': 'BUY',  # 字符串格式
        'success': True,
        'error': None
    }
    
    try:
        formatted1 = format_analysis_results(results1)
        print("✅ 字符串decision格式化成功")
        print(f"  决策: {formatted1['decision']['action']}")
        print(f"  推理: {formatted1['decision']['reasoning']}")
    except Exception as e:
        print(f"❌ 字符串decision格式化失败: {e}")
    
    print()
    
    # 测试案例2: decision 是字典
    print("测试案例2: decision 是字典")
    results2 = {
        'stock_symbol': 'AAPL',
        'analysis_date': '2025-06-27',
        'analysts': ['market', 'fundamentals'],
        'research_depth': 3,
        'llm_model': 'qwen-plus',
        'state': {
            'market_report': '技术分析报告...',
            'fundamentals_report': '基本面分析报告...'
        },
        'decision': {  # 字典格式
            'action': 'SELL',
            'confidence': 0.8,
            'risk_score': 0.4,
            'target_price': 180.0,
            'reasoning': '基于技术分析，建议卖出'
        },
        'success': True,
        'error': None
    }
    
    try:
        formatted2 = format_analysis_results(results2)
        print("✅ 字典decision格式化成功")
        print(f"  决策: {formatted2['decision']['action']}")
        print(f"  置信度: {formatted2['decision']['confidence']}")
        print(f"  推理: {formatted2['decision']['reasoning']}")
    except Exception as e:
        print(f"❌ 字典decision格式化失败: {e}")
    
    print()
    
    # 测试案例3: decision 是其他类型
    print("测试案例3: decision 是其他类型")
    results3 = {
        'stock_symbol': 'AAPL',
        'analysis_date': '2025-06-27',
        'analysts': ['market', 'fundamentals'],
        'research_depth': 3,
        'llm_model': 'qwen-plus',
        'state': {
            'market_report': '技术分析报告...',
            'fundamentals_report': '基本面分析报告...'
        },
        'decision': 123,  # 数字类型
        'success': True,
        'error': None
    }
    
    try:
        formatted3 = format_analysis_results(results3)
        print("✅ 其他类型decision格式化成功")
        print(f"  决策: {formatted3['decision']['action']}")
        print(f"  推理: {formatted3['decision']['reasoning']}")
    except Exception as e:
        print(f"❌ 其他类型decision格式化失败: {e}")
    
    print()
    
    # 测试案例4: 失败的结果
    print("测试案例4: 失败的结果")
    results4 = {
        'stock_symbol': 'AAPL',
        'success': False,
        'error': '分析失败'
    }
    
    try:
        formatted4 = format_analysis_results(results4)
        print("✅ 失败结果格式化成功")
        print(f"  成功: {formatted4['success']}")
        print(f"  错误: {formatted4['error']}")
    except Exception as e:
        print(f"❌ 失败结果格式化失败: {e}")

def main():
    """主测试函数"""
    print("🧪 格式化修复测试")
    print("=" * 60)
    
    test_format_analysis_results()
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main()
