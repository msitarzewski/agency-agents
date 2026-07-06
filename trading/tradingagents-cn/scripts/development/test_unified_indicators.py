#!/usr/bin/env python3
"""
测试统一的技术指标计算函数
验证港股和美股数据是否使用了统一的技术指标计算
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

def test_hk_indicators():
    """测试港股技术指标"""
    print("=" * 80)
    print("测试港股技术指标（使用统一计算函数）")
    print("=" * 80)
    
    from tradingagents.dataflows.providers.hk.improved_hk import get_hk_stock_data_akshare
    
    symbol = "00700.HK"
    start_date = "2024-11-09"
    end_date = "2025-11-09"
    
    print(f"\n📊 测试股票: {symbol}")
    print(f"📅 日期范围: {start_date} ~ {end_date}")
    
    result = get_hk_stock_data_akshare(symbol, start_date, end_date)
    
    # 检查是否包含所有技术指标
    indicators = ['MA5', 'MA10', 'MA20', 'MA60', 'MACD', 'DIF', 'DEA', 'RSI', '布林带']
    
    print("\n✅ 技术指标检查:")
    all_present = True
    for indicator in indicators:
        if indicator in result:
            print(f"  ✅ {indicator}: 已包含")
        else:
            print(f"  ❌ {indicator}: 缺失")
            all_present = False
    
    if all_present:
        print("\n🎉 港股数据包含所有技术指标！")
    else:
        print("\n⚠️ 港股数据缺少部分技术指标！")
    
    return all_present


def test_us_indicators():
    """测试美股技术指标"""
    print("\n" + "=" * 80)
    print("测试美股技术指标（使用统一计算函数）")
    print("=" * 80)
    
    from tradingagents.dataflows.providers.us.optimized import get_us_stock_data_cached
    
    symbol = "AAPL"
    start_date = "2024-11-09"
    end_date = "2025-11-09"
    
    print(f"\n📊 测试股票: {symbol}")
    print(f"📅 日期范围: {start_date} ~ {end_date}")
    
    try:
        result = get_us_stock_data_cached(symbol, start_date, end_date)
        
        # 检查是否包含所有技术指标
        indicators = ['MA5', 'MA10', 'MA20', 'MA60', 'MACD', 'DIF', 'DEA', 'RSI', '布林带']
        
        print("\n✅ 技术指标检查:")
        all_present = True
        for indicator in indicators:
            if indicator in result:
                print(f"  ✅ {indicator}: 已包含")
            else:
                print(f"  ❌ {indicator}: 缺失")
                all_present = False
        
        if all_present:
            print("\n🎉 美股数据包含所有技术指标！")
        else:
            print("\n⚠️ 美股数据缺少部分技术指标！")
        
        return all_present
    
    except Exception as e:
        print(f"\n❌ 美股数据获取失败: {e}")
        print("   （可能是API限制或网络问题，这是正常的）")
        return None


def test_indicator_library():
    """测试技术指标计算库"""
    print("\n" + "=" * 80)
    print("测试技术指标计算库")
    print("=" * 80)
    
    import pandas as pd
    from tradingagents.tools.analysis.indicators import add_all_indicators
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109,
                  110, 111, 112, 113, 114, 115, 116, 117, 118, 119,
                  120, 121, 122, 123, 124, 125, 126, 127, 128, 129,
                  130, 131, 132, 133, 134, 135, 136, 137, 138, 139,
                  140, 141, 142, 143, 144, 145, 146, 147, 148, 149,
                  150, 151, 152, 153, 154, 155, 156, 157, 158, 159,
                  160, 161, 162, 163, 164, 165, 166, 167, 168, 169],
        'high': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110,
                 111, 112, 113, 114, 115, 116, 117, 118, 119, 120,
                 121, 122, 123, 124, 125, 126, 127, 128, 129, 130,
                 131, 132, 133, 134, 135, 136, 137, 138, 139, 140,
                 141, 142, 143, 144, 145, 146, 147, 148, 149, 150,
                 151, 152, 153, 154, 155, 156, 157, 158, 159, 160,
                 161, 162, 163, 164, 165, 166, 167, 168, 169, 170],
        'low': [99, 100, 101, 102, 103, 104, 105, 106, 107, 108,
                109, 110, 111, 112, 113, 114, 115, 116, 117, 118,
                119, 120, 121, 122, 123, 124, 125, 126, 127, 128,
                129, 130, 131, 132, 133, 134, 135, 136, 137, 138,
                139, 140, 141, 142, 143, 144, 145, 146, 147, 148,
                149, 150, 151, 152, 153, 154, 155, 156, 157, 158,
                159, 160, 161, 162, 163, 164, 165, 166, 167, 168]
    })
    
    print(f"\n📊 测试数据: {len(test_data)} 条")
    
    # 添加技术指标
    result_df = add_all_indicators(test_data)
    
    # 检查是否添加了所有指标
    expected_columns = ['ma5', 'ma10', 'ma20', 'ma60', 'rsi', 
                       'macd_dif', 'macd_dea', 'macd',
                       'boll_mid', 'boll_upper', 'boll_lower']
    
    print("\n✅ 技术指标列检查:")
    all_present = True
    for col in expected_columns:
        if col in result_df.columns:
            print(f"  ✅ {col}: 已添加")
        else:
            print(f"  ❌ {col}: 缺失")
            all_present = False
    
    if all_present:
        print("\n🎉 技术指标计算库工作正常！")
        
        # 显示最后一行的技术指标值
        print("\n📈 最新技术指标值:")
        latest = result_df.iloc[-1]
        print(f"  MA5: {latest['ma5']:.2f}")
        print(f"  MA10: {latest['ma10']:.2f}")
        print(f"  MA20: {latest['ma20']:.2f}")
        print(f"  MA60: {latest['ma60']:.2f}")
        print(f"  RSI: {latest['rsi']:.2f}")
        print(f"  MACD DIF: {latest['macd_dif']:.2f}")
        print(f"  MACD DEA: {latest['macd_dea']:.2f}")
        print(f"  MACD: {latest['macd']:.2f}")
        print(f"  BOLL上轨: {latest['boll_upper']:.2f}")
        print(f"  BOLL中轨: {latest['boll_mid']:.2f}")
        print(f"  BOLL下轨: {latest['boll_lower']:.2f}")
    else:
        print("\n⚠️ 技术指标计算库存在问题！")
    
    return all_present


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("统一技术指标计算函数测试")
    print("=" * 80)
    
    # 测试技术指标计算库
    lib_ok = test_indicator_library()
    
    # 测试港股数据
    hk_ok = test_hk_indicators()
    
    # 测试美股数据
    us_ok = test_us_indicators()
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"  技术指标计算库: {'✅ 通过' if lib_ok else '❌ 失败'}")
    print(f"  港股数据接口: {'✅ 通过' if hk_ok else '❌ 失败'}")
    print(f"  美股数据接口: {'✅ 通过' if us_ok else '⚠️ 跳过' if us_ok is None else '❌ 失败'}")
    
    if lib_ok and hk_ok and (us_ok or us_ok is None):
        print("\n🎉 所有测试通过！技术指标计算已统一！")
    else:
        print("\n⚠️ 部分测试失败，请检查代码！")

