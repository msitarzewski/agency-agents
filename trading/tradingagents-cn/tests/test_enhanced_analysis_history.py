#!/usr/bin/env python3
"""
测试增强的分析历史功能
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_load_analysis_results():
    """测试加载分析结果功能"""
    try:
        from web.components.analysis_results import load_analysis_results
        
        print("🔍 测试加载分析结果...")
        
        # 测试基本加载
        results = load_analysis_results(limit=10)
        print(f"✅ 成功加载 {len(results)} 个分析结果")
        
        if results:
            # 检查结果结构
            first_result = results[0]
            required_fields = ['analysis_id', 'timestamp', 'stock_symbol', 'status']
            
            for field in required_fields:
                if field in first_result:
                    print(f"✅ 字段 '{field}' 存在")
                else:
                    print(f"❌ 字段 '{field}' 缺失")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_comparison_functions():
    """测试对比功能"""
    try:
        from web.components.analysis_results import (
            calculate_text_similarity,
            get_report_content
        )
        
        print("🔍 测试对比功能...")
        
        # 测试文本相似度计算
        text1 = "这是一个测试文本"
        text2 = "这是另一个测试文本"
        similarity = calculate_text_similarity(text1, text2)
        print(f"✅ 文本相似度计算: {similarity:.2f}")
        
        # 测试报告内容获取
        mock_result = {
            'source': 'file_system',
            'reports': {
                'final_trade_decision': '买入建议'
            }
        }
        
        content = get_report_content(mock_result, 'final_trade_decision')
        print(f"✅ 报告内容获取: {content}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_chart_functions():
    """测试图表功能"""
    try:
        import pandas as pd
        from web.components.analysis_results import (
            render_comprehensive_dashboard,
            render_time_distribution_charts
        )
        
        print("🔍 测试图表功能...")
        
        # 创建模拟数据
        mock_data = []
        for i in range(10):
            mock_data.append({
                'timestamp': datetime.now() - timedelta(days=i),
                'stock_symbol': f'00000{i % 3}',
                'status': 'completed' if i % 2 == 0 else 'failed',
                'analysts_count': 3,
                'research_depth': 5,
                'tags_count': 2,
                'summary_length': 100 + i * 10,
                'date': (datetime.now() - timedelta(days=i)).date(),
                'hour': 10 + i % 12,
                'weekday': i % 7
            })
        
        df = pd.DataFrame(mock_data)
        print(f"✅ 创建模拟数据: {len(df)} 条记录")
        
        # 注意：这里只是测试函数是否可以导入，实际渲染需要Streamlit环境
        print("✅ 图表函数导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def create_test_data():
    """创建测试数据"""
    try:
        print("🔍 创建测试数据...")
        
        # 确保测试数据目录存在
        test_data_dir = project_root / "data" / "analysis_results" / "detailed" / "TEST001"
        test_date_dir = test_data_dir / "2025-07-31" / "reports"
        test_date_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建测试报告
        test_reports = {
            'final_trade_decision.md': '# 测试交易决策\n\n建议买入',
            'fundamentals_report.md': '# 测试基本面分析\n\n公司基本面良好',
            'market_report.md': '# 测试技术分析\n\n技术指标显示上涨趋势'
        }
        
        for filename, content in test_reports.items():
            report_file = test_date_dir / filename
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"✅ 测试数据创建成功: {test_date_dir}")
        return True
        
    except Exception as e:
        print(f"❌ 创建测试数据失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始测试增强的分析历史功能")
    print("=" * 50)
    
    tests = [
        ("创建测试数据", create_test_data),
        ("加载分析结果", test_load_analysis_results),
        ("对比功能", test_comparison_functions),
        ("图表功能", test_chart_functions)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 测试: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} 通过")
        else:
            print(f"❌ {test_name} 失败")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return True
    else:
        print("⚠️ 部分测试失败，请检查代码")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
