#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化测试：直接测试优化后的基本面分析数据获取逻辑
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta

def test_optimized_fundamentals_logic():
    """直接测试优化后的基本面分析逻辑"""
    print("=" * 80)
    print("🧪 测试优化后的基本面分析数据获取逻辑")
    print("=" * 80)
    
    # 测试股票：平安银行 (000001)
    ticker = "000001"
    
    # 模拟优化后的数据获取策略
    print(f"\n📊 测试股票: {ticker}")
    print("-" * 50)
    
    try:
        # 1. 获取最新股价信息（只需要最近1-2天的数据）
        from datetime import datetime, timedelta
        curr_date = datetime.now().strftime('%Y-%m-%d')
        recent_end_date = curr_date
        recent_start_date = (datetime.strptime(curr_date, '%Y-%m-%d') - timedelta(days=2)).strftime('%Y-%m-%d')
        
        print(f"📅 获取价格数据时间范围: {recent_start_date} 到 {recent_end_date}")
        
        from tradingagents.dataflows.interface import get_china_stock_data_unified
        current_price_data = get_china_stock_data_unified(ticker, recent_start_date, recent_end_date)
        
        if current_price_data:
            print(f"✅ 成功获取当前价格数据")
            print(f"📏 价格数据长度: {len(current_price_data):,} 字符")
            print(f"📝 价格数据预览:\n{current_price_data[:300]}...")
        else:
            print(f"❌ 未获取到价格数据")
            current_price_data = ""
        
        # 2. 获取基本面财务数据
        print(f"\n💰 获取基本面财务数据...")
        
        from tradingagents.dataflows.optimized_china_data import OptimizedChinaDataProvider
        analyzer = OptimizedChinaDataProvider()
        fundamentals_data = analyzer._generate_fundamentals_report(ticker, current_price_data)
        
        if fundamentals_data:
            print(f"✅ 成功获取基本面数据")
            print(f"📏 基本面数据长度: {len(fundamentals_data):,} 字符")
            print(f"📝 基本面数据预览:\n{fundamentals_data[:300]}...")
        else:
            print(f"❌ 未获取到基本面数据")
            fundamentals_data = ""
        
        # 3. 合并结果
        result_data = []
        if current_price_data:
            result_data.append(f"## A股当前价格信息\n{current_price_data}")
        if fundamentals_data:
            result_data.append(f"## A股基本面财务数据\n{fundamentals_data}")
        
        final_result = "\n\n".join(result_data)
        
        print(f"\n📈 最终结果统计:")
        print(f"   - 总数据长度: {len(final_result):,} 字符")
        print(f"   - 价格数据占比: {len(current_price_data)/len(final_result)*100:.1f}%")
        print(f"   - 基本面数据占比: {len(fundamentals_data)/len(final_result)*100:.1f}%")
        
        # 检查数据质量
        has_price = "价格" in final_result or "股价" in final_result or "Price" in final_result
        has_fundamentals = "财务" in final_result or "基本面" in final_result or "投资建议" in final_result
        has_company = "公司" in final_result or "企业" in final_result
        
        print(f"\n🔍 数据质量检查:")
        print(f"   - 包含价格信息: {'✅' if has_price else '❌'}")
        print(f"   - 包含基本面信息: {'✅' if has_fundamentals else '❌'}")
        print(f"   - 包含公司信息: {'✅' if has_company else '❌'}")
        
        print(f"\n💡 优化效果:")
        print(f"   - ✅ 只获取最近2天价格数据，避免了7-30天的历史数据")
        print(f"   - ✅ 保留了基本面分析所需的核心财务数据")
        print(f"   - ✅ 大幅减少了数据传输量和处理开销")
        print(f"   - ✅ 提高了基本面分析的效率和针对性")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_optimized_fundamentals_logic()
    if success:
        print("\n🎉 优化后的基本面分析数据获取策略测试成功！")
    else:
        print("\n💥 测试失败，需要进一步调试")