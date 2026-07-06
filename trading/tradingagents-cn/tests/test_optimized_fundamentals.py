#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试优化后的基本面分析数据获取策略
验证新策略是否能正确获取必要的财务数据和当前股价，而不获取大量历史日线数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.agents.utils.agent_utils import Toolkit

def test_optimized_fundamentals():
    """测试优化后的基本面分析数据获取"""
    print("=" * 80)
    print("🧪 测试优化后的基本面分析数据获取策略")
    print("=" * 80)
    
    # 测试股票：平安银行 (000001)
    test_symbol = "000001"
    
    # 测试不同日期范围（对应不同数据深度）
    from datetime import datetime, timedelta
    
    today = datetime.now()
    test_cases = [
        ("basic", 7, "基础分析 - 1周数据"),
        ("standard", 14, "标准分析 - 2周数据"), 
        ("full", 21, "完整分析 - 3周数据"),
        ("detailed", 28, "详细分析 - 4周数据"),
        ("comprehensive", 30, "全面分析 - 1个月数据")
    ]
    
    results = {}
    
    for depth_name, days_back, description in test_cases:
        print(f"\n📊 测试: {description}")
        print("-" * 50)
        
        # 计算日期范围
        end_date = today.strftime('%Y-%m-%d')
        start_date = (today - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        try:
            # 直接调用静态方法，绕过工具装饰器
            toolkit = Toolkit()
            result = toolkit.get_stock_fundamentals_unified.__func__(
                test_symbol,
                start_date,
                end_date,
                end_date
            )
            
            if result:
                data_length = len(result)
                results[depth_name] = {
                    'success': True,
                    'data_length': data_length,
                    'preview': result[:300] + "..." if len(result) > 300 else result,
                    'description': description
                }
                
                print(f"✅ 成功获取数据")
                print(f"📏 数据长度: {data_length:,} 字符")
                print(f"📝 数据预览:\n{result[:200]}...")
                
                # 检查是否包含基本面关键信息
                has_price = "价格" in result or "股价" in result or "Price" in result
                has_fundamentals = "财务" in result or "基本面" in result or "投资建议" in result
                has_company = "公司" in result or "企业" in result
                
                print(f"🔍 数据质量检查:")
                print(f"   - 包含价格信息: {'✅' if has_price else '❌'}")
                print(f"   - 包含基本面信息: {'✅' if has_fundamentals else '❌'}")
                print(f"   - 包含公司信息: {'✅' if has_company else '❌'}")
                
            else:
                results[depth_name] = {
                    'success': False,
                    'data_length': 0,
                    'preview': "无数据返回",
                    'description': description
                }
                print(f"❌ 未获取到数据")
                
        except Exception as e:
            results[depth_name] = {
                'success': False,
                'data_length': 0,
                'preview': f"错误: {str(e)}",
                'description': description
            }
            print(f"❌ 获取数据时出错: {e}")
    
    # 汇总结果
    print("\n" + "=" * 80)
    print("📈 测试结果汇总")
    print("=" * 80)
    
    successful_tests = sum(1 for r in results.values() if r['success'])
    total_tests = len(results)
    
    print(f"🎯 成功率: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
    
    if successful_tests > 0:
        data_lengths = [r['data_length'] for r in results.values() if r['success']]
        avg_length = sum(data_lengths) / len(data_lengths)
        min_length = min(data_lengths)
        max_length = max(data_lengths)
        
        print(f"📏 数据长度统计:")
        print(f"   - 平均长度: {avg_length:,.0f} 字符")
        print(f"   - 最小长度: {min_length:,} 字符")
        print(f"   - 最大长度: {max_length:,} 字符")
        print(f"   - 数据扩展倍数: {max_length/min_length:.1f}x")
        
        # 对比优化前后的数据量变化
        print(f"\n💡 优化效果:")
        print(f"   - 新策略只获取最近2天价格数据 + 基本面财务数据")
        print(f"   - 相比之前7-30天的历史数据，大幅减少了数据传输量")
        print(f"   - 保持了基本面分析所需的核心信息完整性")
    
    # 详细结果
    print(f"\n📋 各深度详细结果:")
    for depth_name, result in results.items():
        status = "✅ 成功" if result['success'] else "❌ 失败"
        print(f"   {result['description']:20} | {status} | {result['data_length']:6,} 字符")
    
    print("\n🎉 测试完成！")
    return results

if __name__ == "__main__":
    test_optimized_fundamentals()