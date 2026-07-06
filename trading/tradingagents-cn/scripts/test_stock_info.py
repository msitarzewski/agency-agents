#!/usr/bin/env python3
"""
股票基本信息获取测试脚本
专门测试股票名称、行业等基本信息的获取功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_stock_info_retrieval():
    """测试股票基本信息获取功能"""
    print("🔍 测试股票基本信息获取功能")
    print("=" * 50)
    
    # 测试股票代码
    test_codes = ["603985", "000001", "300033"]
    
    for code in test_codes:
        print(f"\n📊 测试股票代码: {code}")
        print("-" * 30)
        
        try:
            # 1. 测试Tushare股票信息获取
            print(f"🔍 步骤1: 测试Tushare股票信息获取...")
            from tradingagents.dataflows.interface import get_china_stock_info_tushare
            tushare_info = get_china_stock_info_tushare(code)
            print(f"✅ Tushare信息: {tushare_info}")
            
            # 2. 测试统一股票信息获取
            print(f"🔍 步骤2: 测试统一股票信息获取...")
            from tradingagents.dataflows.interface import get_china_stock_info_unified
            unified_info = get_china_stock_info_unified(code)
            print(f"✅ 统一信息: {unified_info}")
            
            # 3. 测试DataSourceManager直接调用
            print(f"🔍 步骤3: 测试DataSourceManager...")
            from tradingagents.dataflows.data_source_manager import get_china_stock_info_unified as manager_info
            manager_result = manager_info(code)
            print(f"✅ Manager结果: {manager_result}")
            
            # 4. 测试TushareAdapter直接调用
            print(f"🔍 步骤4: 测试TushareAdapter...")
            from tradingagents.dataflows.tushare_adapter import get_tushare_adapter
            adapter = get_tushare_adapter()
            adapter_result = adapter.get_stock_info(code)
            print(f"✅ Adapter结果: {adapter_result}")
            
            # 5. 测试TushareProvider直接调用
            print(f"🔍 步骤5: 测试TushareProvider...")
            from tradingagents.dataflows.tushare_utils import TushareProvider
            provider = TushareProvider()
            provider_result = provider.get_stock_info(code)
            print(f"✅ Provider结果: {provider_result}")
            
        except Exception as e:
            print(f"❌ 测试{code}失败: {e}")
            import traceback
            traceback.print_exc()

def test_tushare_stock_basic_api():
    """直接测试Tushare的stock_basic API"""
    print("\n🔍 直接测试Tushare stock_basic API")
    print("=" * 50)
    
    try:
        from tradingagents.dataflows.tushare_utils import get_tushare_provider
        
        provider = get_tushare_provider()
        
        if not provider.connected:
            print("❌ Tushare未连接")
            return
        
        # 测试stock_basic API
        test_codes = ["603985", "000001", "300033"]
        
        for code in test_codes:
            print(f"\n📊 测试股票代码: {code}")
            
            # 转换为Tushare格式
            ts_code = provider._normalize_symbol(code)
            print(f"🔍 转换后的代码: {ts_code}")
            
            # 直接调用API
            try:
                basic_info = provider.api.stock_basic(
                    ts_code=ts_code,
                    fields='ts_code,symbol,name,area,industry,market,list_date'
                )
                
                print(f"✅ API返回数据形状: {basic_info.shape if basic_info is not None else 'None'}")
                
                if basic_info is not None and not basic_info.empty:
                    print(f"📊 返回数据:")
                    print(basic_info.to_dict('records'))
                else:
                    print("❌ API返回空数据")
                    
            except Exception as e:
                print(f"❌ API调用失败: {e}")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_stock_basic_all():
    """测试获取所有股票基本信息"""
    print("\n🔍 测试获取所有股票基本信息")
    print("=" * 50)
    
    try:
        from tradingagents.dataflows.tushare_utils import get_tushare_provider
        
        provider = get_tushare_provider()
        
        if not provider.connected:
            print("❌ Tushare未连接")
            return
        
        # 获取所有A股基本信息
        print("🔍 获取所有A股基本信息...")
        all_stocks = provider.api.stock_basic(
            exchange='',
            list_status='L',
            fields='ts_code,symbol,name,area,industry,market,list_date'
        )
        
        print(f"✅ 获取到{len(all_stocks)}只股票")
        
        # 查找测试股票
        test_codes = ["603985", "000001", "300033"]
        
        for code in test_codes:
            print(f"\n📊 查找股票: {code}")
            
            # 在所有股票中查找
            found_stocks = all_stocks[all_stocks['symbol'] == code]
            
            if not found_stocks.empty:
                stock_info = found_stocks.iloc[0]
                print(f"✅ 找到股票:")
                print(f"   代码: {stock_info['symbol']}")
                print(f"   名称: {stock_info['name']}")
                print(f"   行业: {stock_info['industry']}")
                print(f"   地区: {stock_info['area']}")
                print(f"   市场: {stock_info['market']}")
                print(f"   上市日期: {stock_info['list_date']}")
            else:
                print(f"❌ 未找到股票: {code}")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 股票基本信息获取测试")
    print("=" * 80)
    print("📝 此测试专门检查股票名称、行业等基本信息的获取")
    print("=" * 80)
    
    # 1. 测试股票信息获取链路
    test_stock_info_retrieval()
    
    # 2. 直接测试Tushare API
    test_tushare_stock_basic_api()
    
    # 3. 测试获取所有股票信息
    test_stock_basic_all()
    
    print("\n📋 测试总结")
    print("=" * 60)
    print("✅ 股票基本信息测试完成")
    print("🔍 如果发现问题，请检查:")
    print("   - Tushare API连接状态")
    print("   - 股票代码格式转换")
    print("   - API返回数据解析")
    print("   - 缓存机制影响")
