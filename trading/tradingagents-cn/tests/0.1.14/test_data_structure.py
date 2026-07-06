#!/usr/bin/env python3
"""
测试数据结构脚本
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'web'))

def test_data_structure():
    """测试分析结果数据结构"""
    try:
        from web.components.analysis_results import load_analysis_results
        
        print("🔍 测试分析结果数据结构...")
        
        # 加载分析结果
        results = load_analysis_results(limit=5)
        
        print(f"📊 找到 {len(results)} 个分析结果")
        
        if results:
            result = results[0]
            print(f"\n📋 第一个结果的数据结构:")
            print(f"   analysis_id: {result.get('analysis_id', 'missing')}")
            print(f"   source: {result.get('source', 'missing')}")
            print(f"   stock_symbol: {result.get('stock_symbol', 'missing')}")
            print(f"   reports字段存在: {'reports' in result}")
            
            if 'reports' in result:
                reports = result['reports']
                print(f"   reports内容: {list(reports.keys())}")
                
                # 显示第一个报告的前100个字符
                if reports:
                    first_report_key = list(reports.keys())[0]
                    first_report_content = reports[first_report_key]
                    print(f"   {first_report_key} 内容预览:")
                    print(f"   {first_report_content[:200]}...")
            else:
                print("   ❌ reports字段不存在")
                print(f"   可用字段: {list(result.keys())}")
        
        return results
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_data_structure()
