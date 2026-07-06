"""
测试港股功能
验证港股代码识别、数据获取和处理功能
"""

import sys
import os
import traceback

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_stock_utils():
    """测试股票工具类"""
    print("\n🧪 测试股票工具类...")
    
    try:
        from tradingagents.utils.stock_utils import StockUtils
        
        # 测试港股代码识别
        test_cases = [
            ("0700.HK", "港股"),
            ("9988.HK", "港股"),
            ("3690.HK", "港股"),
            ("000001", "中国A股"),
            ("600036", "中国A股"),
            ("AAPL", "美股"),
            ("TSLA", "美股"),
            ("invalid", "未知市场")
        ]
        
        for ticker, expected in test_cases:
            market_info = StockUtils.get_market_info(ticker)
            print(f"  {ticker}: {market_info['market_name']} ({market_info['currency_name']}) - {'✅' if expected in market_info['market_name'] else '❌'}")
            
            if expected == "港股" and not market_info['is_hk']:
                print(f"❌ {ticker} 应该被识别为港股")
                return False
            elif expected == "中国A股" and not market_info['is_china']:
                print(f"❌ {ticker} 应该被识别为中国A股")
                return False
            elif expected == "美股" and not market_info['is_us']:
                print(f"❌ {ticker} 应该被识别为美股")
                return False
        
        print("✅ 股票工具类测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 股票工具类测试失败: {e}")
        traceback.print_exc()
        return False


def test_hk_stock_provider():
    """测试港股数据提供器"""
    print("\n🧪 测试港股数据提供器...")
    
    try:
        from tradingagents.dataflows.hk_stock_utils import get_hk_stock_provider
        
        provider = get_hk_stock_provider()
        
        # 测试港股代码标准化
        test_symbols = [
            ("0700", "0700.HK"),
            ("0700.HK", "0700.HK"),
            ("9988", "9988.HK"),
            ("3690.HK", "3690.HK")
        ]
        
        for input_symbol, expected in test_symbols:
            normalized = provider._normalize_hk_symbol(input_symbol)
            print(f"  标准化: {input_symbol} -> {normalized} {'✅' if normalized == expected else '❌'}")
            
            if normalized != expected:
                print(f"❌ 港股代码标准化失败: {input_symbol} -> {normalized}, 期望: {expected}")
                return False
        
        print("✅ 港股数据提供器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 港股数据提供器测试失败: {e}")
        traceback.print_exc()
        return False


def test_hk_stock_info():
    """测试港股信息获取"""
    print("\n🧪 测试港股信息获取...")
    
    try:
        from tradingagents.dataflows.hk_stock_utils import get_hk_stock_info
        
        # 测试腾讯港股信息
        hk_symbol = "0700.HK"
        print(f"  获取 {hk_symbol} 信息...")
        
        info = get_hk_stock_info(hk_symbol)
        
        if info and 'symbol' in info:
            print(f"  ✅ 股票代码: {info['symbol']}")
            print(f"  ✅ 股票名称: {info['name']}")
            print(f"  ✅ 货币: {info['currency']}")
            print(f"  ✅ 交易所: {info['exchange']}")
            print(f"  ✅ 数据源: {info['source']}")
            
            # 验证基本字段
            if info['currency'] != 'HKD':
                print(f"⚠️ 港股货币应为HKD，实际为: {info['currency']}")
            
            if info['exchange'] != 'HKG':
                print(f"⚠️ 港股交易所应为HKG，实际为: {info['exchange']}")
            
            print("✅ 港股信息获取测试通过")
            return True
        else:
            print("❌ 港股信息获取失败")
            return False
            
    except Exception as e:
        print(f"❌ 港股信息获取测试失败: {e}")
        traceback.print_exc()
        return False


def test_hk_stock_data():
    """测试港股数据获取（简单测试）"""
    print("\n🧪 测试港股数据获取...")
    
    try:
        from tradingagents.dataflows.hk_stock_utils import get_hk_stock_data
        from datetime import datetime, timedelta
        
        # 设置测试日期范围（最近30天）
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # 测试腾讯港股数据
        hk_symbol = "0700.HK"
        print(f"  获取 {hk_symbol} 数据 ({start_date} 到 {end_date})...")
        
        data_text = get_hk_stock_data(hk_symbol, start_date, end_date)
        
        if data_text and "港股数据报告" in data_text:
            print("  ✅ 港股数据格式正确")
            print(f"  ✅ 数据长度: {len(data_text)}字符")
            
            # 检查关键信息
            if "HK$" in data_text:
                print("  ✅ 包含港币价格信息")
            else:
                print("  ⚠️ 缺少港币价格信息")
            
            if "香港交易所" in data_text:
                print("  ✅ 包含交易所信息")
            
            print("✅ 港股数据获取测试通过")
            return True
        else:
            print("❌ 港股数据获取失败或格式错误")
            print(f"返回数据: {data_text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ 港股数据获取测试失败: {e}")
        traceback.print_exc()
        return False


def test_optimized_us_data_hk_support():
    """测试优化美股数据模块的港股支持"""
    print("\n🧪 测试优化数据模块港股支持...")
    
    try:
        from tradingagents.dataflows.optimized_us_data import get_us_stock_data_cached
        from datetime import datetime, timedelta
        
        # 设置测试日期范围
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # 测试港股数据获取
        hk_symbol = "0700.HK"
        print(f"  通过优化模块获取 {hk_symbol} 数据...")
        
        data_text = get_us_stock_data_cached(
            symbol=hk_symbol,
            start_date=start_date,
            end_date=end_date,
            force_refresh=True
        )
        
        if data_text and "数据分析" in data_text:
            print("  ✅ 数据获取成功")
            
            # 检查港股特有信息
            if "港股" in data_text:
                print("  ✅ 正确识别为港股")
            
            if "HK$" in data_text:
                print("  ✅ 使用港币符号")
            else:
                print("  ⚠️ 未使用港币符号")
            
            print("✅ 优化数据模块港股支持测试通过")
            return True
        else:
            print("❌ 优化数据模块港股支持测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 优化数据模块港股支持测试失败: {e}")
        traceback.print_exc()
        return False


def main():
    """运行所有港股功能测试"""
    print("🇭🇰 开始港股功能测试")
    print("=" * 50)
    
    tests = [
        test_stock_utils,
        test_hk_stock_provider,
        test_hk_stock_info,
        test_hk_stock_data,
        test_optimized_us_data_hk_support
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
    print(f"🇭🇰 港股功能测试完成: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！港股功能正常")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步调试")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
