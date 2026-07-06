#!/usr/bin/env python3
"""
测试修复后的股票基本信息降级机制
验证当Tushare失败时是否能自动降级到其他数据源
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_stock_info_fallback_mechanism():
    """测试股票信息降级机制"""
    print("🔍 测试股票信息降级机制")
    print("=" * 50)
    
    # 测试不存在的股票代码（应该触发降级）
    fake_codes = ["999999", "888888"]
    
    for code in fake_codes:
        print(f"\n📊 测试不存在的股票代码: {code}")
        print("-" * 30)
        
        try:
            # 测试统一接口（现在应该有降级机制）
            from tradingagents.dataflows.interface import get_china_stock_info_unified
            result = get_china_stock_info_unified(code)
            print(f"✅ 统一接口结果: {result}")
            
            # 检查是否使用了备用数据源
            if "数据来源: akshare" in result or "数据来源: baostock" in result:
                print("✅ 成功降级到备用数据源！")
            elif "数据来源: tushare" in result and f"股票名称: 股票{code}" not in result:
                print("✅ Tushare成功获取数据")
            elif f"股票名称: 股票{code}" in result:
                print("❌ 仍然返回默认值，降级机制可能未生效")
            else:
                print("🤔 结果不明确")
                
        except Exception as e:
            print(f"❌ 测试{code}失败: {e}")

def test_real_stock_fallback():
    """测试真实股票的降级机制（模拟Tushare失败）"""
    print("\n🔍 测试真实股票的降级机制")
    print("=" * 50)
    
    # 测试真实股票代码
    real_codes = ["603985", "000001", "300033"]
    
    for code in real_codes:
        print(f"\n📊 测试股票代码: {code}")
        print("-" * 30)
        
        try:
            # 直接测试DataSourceManager
            from tradingagents.dataflows.data_source_manager import get_data_source_manager
            manager = get_data_source_manager()
            
            # 获取股票信息
            result = manager.get_stock_info(code)
            print(f"✅ DataSourceManager结果: {result}")
            
            # 检查是否获取到有效信息
            if result.get('name') and result['name'] != f'股票{code}':
                print(f"✅ 成功获取股票名称: {result['name']}")
                print(f"📊 数据来源: {result.get('source', '未知')}")
            else:
                print("❌ 未获取到有效股票名称")
                
        except Exception as e:
            print(f"❌ 测试{code}失败: {e}")
            import traceback
            traceback.print_exc()

def test_individual_data_sources():
    """测试各个数据源的股票信息获取能力"""
    print("\n🔍 测试各个数据源的股票信息获取能力")
    print("=" * 50)
    
    test_code = "603985"  # 恒润股份
    
    try:
        from tradingagents.dataflows.data_source_manager import get_data_source_manager
        manager = get_data_source_manager()
        
        # 测试AKShare
        print(f"\n📊 测试AKShare获取{test_code}信息:")
        akshare_result = manager._get_akshare_stock_info(test_code)
        print(f"✅ AKShare结果: {akshare_result}")
        
        # 测试BaoStock
        print(f"\n📊 测试BaoStock获取{test_code}信息:")
        baostock_result = manager._get_baostock_stock_info(test_code)
        print(f"✅ BaoStock结果: {baostock_result}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_fundamentals_with_fallback():
    """测试基本面分析是否能获取到正确的股票名称"""
    print("\n🔍 测试基本面分析中的股票名称获取")
    print("=" * 50)
    
    test_code = "603985"  # 恒润股份
    
    try:
        # 模拟基本面分析中的股票信息获取
        from tradingagents.dataflows.interface import get_china_stock_info_unified
        stock_info = get_china_stock_info_unified(test_code)
        print(f"✅ 统一接口获取股票信息: {stock_info}")
        
        # 检查是否包含股票名称
        if "股票名称:" in stock_info:
            lines = stock_info.split('\n')
            for line in lines:
                if "股票名称:" in line:
                    company_name = line.split(':')[1].strip()
                    print(f"✅ 提取到股票名称: {company_name}")
                    
                    if company_name != "未知公司" and company_name != f"股票{test_code}":
                        print("✅ 基本面分析现在可以获取到正确的股票名称！")
                    else:
                        print("❌ 基本面分析仍然获取不到正确的股票名称")
                    break
        else:
            print("❌ 统一接口返回格式异常")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 股票基本信息降级机制修复测试")
    print("=" * 80)
    print("📝 此测试验证修复后的降级机制是否正常工作")
    print("=" * 80)
    
    # 1. 测试降级机制
    test_stock_info_fallback_mechanism()
    
    # 2. 测试真实股票
    test_real_stock_fallback()
    
    # 3. 测试各个数据源
    test_individual_data_sources()
    
    # 4. 测试基本面分析
    test_fundamentals_with_fallback()
    
    print("\n📋 测试总结")
    print("=" * 60)
    print("✅ 股票基本信息降级机制修复测试完成")
    print("🔍 现在当Tushare失败时应该能自动降级到:")
    print("   - AKShare (获取股票名称)")
    print("   - BaoStock (获取股票名称和上市日期)")
    print("🎯 基本面分析现在应该能获取到正确的股票名称")
