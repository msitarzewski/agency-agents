# -*- coding: utf-8 -*-
"""
简化版 AKShare 港股接口测试
"""
import sys
import akshare as ak
import pandas as pd
from datetime import datetime

# 设置输出编码
sys.stdout.reconfigure(encoding='utf-8')

def test_stock_hk_spot():
    """测试新浪财经港股实时行情"""
    print("\n" + "="*80)
    print("测试接口: stock_hk_spot (新浪财经)")
    print("="*80)
    
    try:
        df = ak.stock_hk_spot()
        print(f"成功! 返回 {len(df)} 只港股")
        print(f"列名: {list(df.columns)}")
        
        # 查找腾讯控股
        test_symbol = "00700"
        matched = df[df['代码'] == test_symbol]
        if not matched.empty:
            print(f"\n找到 {test_symbol} (腾讯控股):")
            print(matched.to_string())
        
        print(f"\n前5只股票:")
        print(df.head(5)[['代码', '中文名称', '最新价', '涨跌幅']].to_string())
        
        return True, df
    except Exception as e:
        print(f"失败: {e}")
        return False, None


def test_stock_hk_daily():
    """测试新浪财经港股历史行情"""
    print("\n" + "="*80)
    print("测试接口: stock_hk_daily (新浪财经)")
    print("="*80)
    
    try:
        test_symbol = "00700"
        df = ak.stock_hk_daily(symbol=test_symbol, adjust="qfq")
        print(f"成功! 返回 {len(df)} 条历史数据")
        print(f"列名: {list(df.columns)}")
        
        print(f"\n最近5个交易日:")
        print(df.tail(5).to_string())
        
        return True, df
    except Exception as e:
        print(f"失败: {e}")
        return False, None


def test_stock_hk_spot_em():
    """测试东方财富港股实时行情"""
    print("\n" + "="*80)
    print("测试接口: stock_hk_spot_em (东方财富)")
    print("="*80)
    
    try:
        df = ak.stock_hk_spot_em()
        print(f"成功! 返回 {len(df)} 只港股")
        print(f"列名: {list(df.columns)}")
        
        # 查找腾讯控股
        test_symbol = "00700"
        matched = df[df['代码'] == test_symbol]
        if not matched.empty:
            print(f"\n找到 {test_symbol} (腾讯控股):")
            print(matched.to_string())
        
        print(f"\n前5只股票:")
        print(df.head(5)[['代码', '名称', '最新价', '涨跌幅']].to_string())
        
        return True, df
    except Exception as e:
        print(f"失败: {e}")
        return False, None


def test_stock_individual_info_hk():
    """测试雪球港股个股信息"""
    print("\n" + "="*80)
    print("测试接口: stock_individual_basic_info_hk_xq (雪球)")
    print("="*80)
    
    try:
        test_symbol = "00700"
        result = ak.stock_individual_basic_info_hk_xq(symbol=test_symbol)
        print(f"成功! 返回类型: {type(result)}")
        print(f"数据: {result}")
        
        return True, result
    except AttributeError:
        print("接口不存在")
        return False, None
    except Exception as e:
        print(f"失败: {e}")
        return False, None


def main():
    """主测试函数"""
    print("="*80)
    print("AKShare 港股接口测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    results = {}
    
    # 测试各个接口
    results['stock_hk_spot'] = test_stock_hk_spot()
    results['stock_hk_daily'] = test_stock_hk_daily()
    results['stock_hk_spot_em'] = test_stock_hk_spot_em()
    results['stock_individual_basic_info_hk_xq'] = test_stock_individual_info_hk()
    
    # 总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    
    for api_name, (success, _) in results.items():
        status = "成功" if success else "失败"
        print(f"{api_name}: {status}")
    
    print("\n推荐使用:")
    print("1. stock_hk_spot - 新浪财经实时行情 (获取股票列表+实时价格)")
    print("2. stock_hk_daily - 新浪财经历史行情 (获取K线数据)")
    print("3. stock_hk_spot_em - 东方财富实时行情 (备用)")


if __name__ == "__main__":
    main()

