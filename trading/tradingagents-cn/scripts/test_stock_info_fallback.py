#!/usr/bin/env python3
"""
测试股票基本信息获取的降级机制
验证当Tushare失败时是否有备用方案
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_tushare_stock_info_failure():
    """测试Tushare股票信息获取失败的情况"""
    print("🔍 测试Tushare股票信息获取失败情况")
    print("=" * 50)
    
    # 测试不存在的股票代码
    fake_codes = ["999999", "888888", "777777"]
    
    for code in fake_codes:
        print(f"\n📊 测试不存在的股票代码: {code}")
        print("-" * 30)
        
        try:
            # 1. 测试Tushare直接获取
            print(f"🔍 步骤1: 测试Tushare直接获取...")
            from tradingagents.dataflows.interface import get_china_stock_info_tushare
            tushare_result = get_china_stock_info_tushare(code)
            print(f"✅ Tushare结果: {tushare_result}")
            
            # 2. 测试统一接口
            print(f"🔍 步骤2: 测试统一接口...")
            from tradingagents.dataflows.interface import get_china_stock_info_unified
            unified_result = get_china_stock_info_unified(code)
            print(f"✅ 统一接口结果: {unified_result}")
            
            # 3. 检查是否有降级机制
            if "❌" in tushare_result and "❌" in unified_result:
                print("❌ 确认：没有降级到其他数据源")
            elif "❌" in tushare_result and "❌" not in unified_result:
                print("✅ 有降级机制：统一接口成功获取数据")
            else:
                print("🤔 结果不明确")
                
        except Exception as e:
            print(f"❌ 测试{code}失败: {e}")

def test_akshare_stock_info():
    """测试AKShare是否支持股票基本信息获取"""
    print("\n🔍 测试AKShare股票基本信息获取能力")
    print("=" * 50)
    
    test_codes = ["603985", "000001", "300033"]
    
    for code in test_codes:
        print(f"\n📊 测试股票代码: {code}")
        print("-" * 30)
        
        try:
            # 直接测试AKShare
            import akshare as ak
            
            # 尝试获取股票基本信息
            try:
                # 方法1: 股票信息
                stock_info = ak.stock_individual_info_em(symbol=code)
                print(f"✅ AKShare个股信息: {stock_info.head() if not stock_info.empty else '空数据'}")
            except Exception as e:
                print(f"❌ AKShare个股信息失败: {e}")
            
            try:
                # 方法2: 股票基本信息
                stock_basic = ak.stock_zh_a_spot_em()
                stock_data = stock_basic[stock_basic['代码'] == code]
                if not stock_data.empty:
                    print(f"✅ AKShare基本信息: {stock_data[['代码', '名称', '涨跌幅', '现价']].iloc[0].to_dict()}")
                else:
                    print(f"❌ AKShare基本信息: 未找到{code}")
            except Exception as e:
                print(f"❌ AKShare基本信息失败: {e}")
                
        except Exception as e:
            print(f"❌ AKShare测试失败: {e}")

def test_baostock_stock_info():
    """测试BaoStock是否支持股票基本信息获取"""
    print("\n🔍 测试BaoStock股票基本信息获取能力")
    print("=" * 50)
    
    test_codes = ["sh.603985", "sz.000001", "sz.300033"]
    
    try:
        import baostock as bs
        
        # 登录BaoStock
        lg = bs.login()
        if lg.error_code != '0':
            print(f"❌ BaoStock登录失败: {lg.error_msg}")
            return
        
        print("✅ BaoStock登录成功")
        
        for code in test_codes:
            print(f"\n📊 测试股票代码: {code}")
            print("-" * 30)
            
            try:
                # 获取股票基本信息
                rs = bs.query_stock_basic(code=code)
                if rs.error_code == '0':
                    data_list = []
                    while (rs.error_code == '0') & rs.next():
                        data_list.append(rs.get_row_data())
                    
                    if data_list:
                        print(f"✅ BaoStock基本信息: {data_list[0]}")
                    else:
                        print(f"❌ BaoStock基本信息: 无数据")
                else:
                    print(f"❌ BaoStock查询失败: {rs.error_msg}")
                    
            except Exception as e:
                print(f"❌ BaoStock测试失败: {e}")
        
        # 登出
        bs.logout()
        
    except ImportError:
        print("❌ BaoStock未安装")
    except Exception as e:
        print(f"❌ BaoStock测试失败: {e}")

def analyze_current_fallback_mechanism():
    """分析当前的降级机制"""
    print("\n🔍 分析当前降级机制")
    print("=" * 50)
    
    try:
        from tradingagents.dataflows.data_source_manager import DataSourceManager
        
        # 检查DataSourceManager的方法
        manager = DataSourceManager()
        
        print("📊 DataSourceManager可用方法:")
        methods = [method for method in dir(manager) if not method.startswith('_')]
        for method in methods:
            print(f"   - {method}")
        
        # 检查是否有股票信息的降级方法
        if hasattr(manager, '_try_fallback_sources'):
            print("✅ 有_try_fallback_sources方法 (用于历史数据)")
        else:
            print("❌ 没有_try_fallback_sources方法")
        
        if hasattr(manager, '_try_fallback_stock_info'):
            print("✅ 有_try_fallback_stock_info方法 (用于基本信息)")
        else:
            print("❌ 没有_try_fallback_stock_info方法")
        
        # 检查get_stock_info方法的实现
        import inspect
        source = inspect.getsource(manager.get_stock_info)
        print(f"\n📝 get_stock_info方法源码:")
        print(source)
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")

if __name__ == "__main__":
    print("🧪 股票基本信息降级机制测试")
    print("=" * 80)
    print("📝 此测试检查当Tushare失败时是否有备用数据源")
    print("=" * 80)
    
    # 1. 测试Tushare失败情况
    test_tushare_stock_info_failure()
    
    # 2. 测试AKShare能力
    test_akshare_stock_info()
    
    # 3. 测试BaoStock能力
    test_baostock_stock_info()
    
    # 4. 分析当前机制
    analyze_current_fallback_mechanism()
    
    print("\n📋 测试总结")
    print("=" * 60)
    print("🔍 如果发现没有降级机制，需要:")
    print("   1. 为get_stock_info添加降级逻辑")
    print("   2. 实现AKShare/BaoStock的股票信息获取")
    print("   3. 确保基本面分析能获取到股票名称")
