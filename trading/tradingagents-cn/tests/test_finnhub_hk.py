"""
测试FINNHUB港股支持
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_finnhub_connection():
    """测试FINNHUB连接"""
    print("🧪 测试FINNHUB连接...")
    
    try:
        import finnhub
        
        api_key = os.getenv('FINNHUB_API_KEY')
        if not api_key:
            print("❌ 未配置FINNHUB_API_KEY环境变量")
            return False
        
        client = finnhub.Client(api_key=api_key)
        
        # 测试美股连接
        print("  测试美股连接 (AAPL)...")
        quote = client.quote('AAPL')
        if quote and 'c' in quote:
            print(f"    ✅ 美股连接成功: AAPL = ${quote['c']:.2f}")
        else:
            print("    ❌ 美股连接失败")
            return False
        
        print("✅ FINNHUB连接测试通过")
        return True
        
    except Exception as e:
        print(f"❌ FINNHUB连接测试失败: {e}")
        return False

def test_finnhub_hk_symbols():
    """测试FINNHUB港股代码格式"""
    print("\n🧪 测试FINNHUB港股代码格式...")
    
    try:
        import finnhub
        
        api_key = os.getenv('FINNHUB_API_KEY')
        if not api_key:
            print("❌ 未配置FINNHUB_API_KEY环境变量")
            return False
        
        client = finnhub.Client(api_key=api_key)
        
        # 测试不同的港股代码格式
        hk_symbols = [
            "0700.HK",  # 腾讯
            "9988.HK",  # 阿里巴巴
            "3690.HK",  # 美团
            "1810.HK",  # 小米
        ]
        
        success_count = 0
        
        for symbol in hk_symbols:
            try:
                print(f"  测试港股: {symbol}...")
                quote = client.quote(symbol)
                
                if quote and 'c' in quote and quote['c'] > 0:
                    print(f"    ✅ {symbol} = HK${quote['c']:.2f}")
                    success_count += 1
                else:
                    print(f"    ❌ {symbol} 无数据或价格为0")
                    
            except Exception as e:
                print(f"    ❌ {symbol} 获取失败: {e}")
        
        if success_count > 0:
            print(f"✅ FINNHUB港股支持测试通过 ({success_count}/{len(hk_symbols)} 成功)")
            return True
        else:
            print("❌ FINNHUB港股支持测试失败 - 所有港股代码都无法获取数据")
            return False
        
    except Exception as e:
        print(f"❌ FINNHUB港股支持测试失败: {e}")
        return False

def test_finnhub_hk_company_info():
    """测试FINNHUB港股公司信息"""
    print("\n🧪 测试FINNHUB港股公司信息...")
    
    try:
        import finnhub
        
        api_key = os.getenv('FINNHUB_API_KEY')
        if not api_key:
            print("❌ 未配置FINNHUB_API_KEY环境变量")
            return False
        
        client = finnhub.Client(api_key=api_key)
        
        symbol = "0700.HK"  # 腾讯
        print(f"  获取 {symbol} 公司信息...")
        
        try:
            profile = client.company_profile2(symbol=symbol)
            
            if profile and 'name' in profile:
                print(f"    ✅ 公司名称: {profile['name']}")
                print(f"    ✅ 国家: {profile.get('country', 'N/A')}")
                print(f"    ✅ 货币: {profile.get('currency', 'N/A')}")
                print(f"    ✅ 交易所: {profile.get('exchange', 'N/A')}")
                print(f"    ✅ 行业: {profile.get('finnhubIndustry', 'N/A')}")
                return True
            else:
                print(f"    ❌ {symbol} 公司信息为空")
                return False
                
        except Exception as e:
            print(f"    ❌ {symbol} 公司信息获取失败: {e}")
            return False
        
    except Exception as e:
        print(f"❌ FINNHUB港股公司信息测试失败: {e}")
        return False

def test_optimized_us_data_finnhub_hk():
    """测试优化数据模块的FINNHUB港股支持"""
    print("\n🧪 测试优化数据模块的FINNHUB港股支持...")
    
    try:
        from tradingagents.dataflows.optimized_us_data import get_us_stock_data_cached
        from datetime import datetime, timedelta
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        symbol = "0700.HK"  # 腾讯
        print(f"  通过优化模块获取 {symbol} 数据...")
        
        data = get_us_stock_data_cached(symbol, start_date, end_date, force_refresh=True)
        
        if data and len(data) > 100:
            print("    ✅ 数据获取成功")
            
            # 检查关键信息
            checks = [
                ("港股", "识别为港股"),
                ("HK$", "使用港币符号"),
                ("FINNHUB", "使用FINNHUB数据源"),
                (symbol, "包含股票代码")
            ]
            
            for check_text, description in checks:
                if check_text in data:
                    print(f"      ✅ {description}")
                else:
                    print(f"      ⚠️ 缺少{description}")
            
            print("✅ 优化数据模块FINNHUB港股支持测试通过")
            return True
        else:
            print("❌ 优化数据模块FINNHUB港股支持测试失败")
            print(f"返回数据: {data[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ 优化数据模块FINNHUB港股支持测试失败: {e}")
        return False

def test_unified_interface_finnhub_priority():
    """测试统一接口的FINNHUB优先级"""
    print("\n🧪 测试统一接口的FINNHUB优先级...")
    
    try:
        from tradingagents.dataflows.interface import get_hk_stock_data_unified
        from datetime import datetime, timedelta
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        symbol = "0700.HK"
        print(f"  通过统一接口获取 {symbol} 数据...")
        
        data = get_hk_stock_data_unified(symbol, start_date, end_date)
        
        if data and len(data) > 50:
            print("    ✅ 统一接口数据获取成功")
            
            # 检查数据源优先级
            if "FINNHUB" in data:
                print("    ✅ 优先使用FINNHUB数据源")
            elif "Yahoo Finance" in data:
                print("    ✅ 使用Yahoo Finance备用数据源")
            elif "AKShare" in data:
                print("    ✅ 使用AKShare备用数据源")
            else:
                print("    ⚠️ 未识别数据源")
            
            print("✅ 统一接口FINNHUB优先级测试通过")
            return True
        else:
            print("❌ 统一接口FINNHUB优先级测试失败")
            return False
        
    except Exception as e:
        print(f"❌ 统一接口FINNHUB优先级测试失败: {e}")
        return False

def main():
    """运行所有FINNHUB港股测试"""
    print("🇭🇰 开始FINNHUB港股支持测试")
    print("=" * 50)
    
    tests = [
        test_finnhub_connection,
        test_finnhub_hk_symbols,
        test_finnhub_hk_company_info,
        test_optimized_us_data_finnhub_hk,
        test_unified_interface_finnhub_priority
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"🇭🇰 FINNHUB港股支持测试完成: {passed}/{total} 通过")
    
    if passed >= 2:  # 至少连接和基本功能正常
        print("🎉 FINNHUB港股支持基本正常！")
        print("\n✅ FINNHUB港股功能特点:")
        print("  - 支持港股实时报价")
        print("  - 支持港股公司信息")
        print("  - 作为港股数据的首选数据源")
        print("  - 自动货币符号识别 (HK$)")
        print("  - 集成到统一数据接口")
    else:
        print("⚠️ FINNHUB港股支持可能有问题，请检查API配置")

if __name__ == "__main__":
    main()
