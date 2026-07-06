#!/usr/bin/env python3
"""
测试市场分析回溯天数配置是否生效
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from tradingagents.dataflows.interface import get_hk_stock_data_unified

def test_lookback_days():
    """测试港股数据是否使用配置的回溯天数"""
    
    print("=" * 80)
    print("测试市场分析回溯天数配置")
    print("=" * 80)
    
    # 测试腾讯控股 (00700)
    symbol = "00700.HK"
    
    # LLM 传入的日期范围（通常是最近几天）
    start_date = "2025-11-01"
    end_date = "2025-11-09"
    
    print(f"\n📊 测试股票: {symbol}")
    print(f"📅 LLM 传入的日期范围: {start_date} ~ {end_date}")
    print(f"📅 预期行为: 自动扩展到 MARKET_ANALYST_LOOKBACK_DAYS 配置的天数（365天）")
    print()
    
    result = get_hk_stock_data_unified(symbol, start_date, end_date)
    
    print("\n" + "=" * 80)
    print("返回结果:")
    print("=" * 80)
    print(result)
    
    # 验证结果
    print("\n" + "=" * 80)
    print("验证结果:")
    print("=" * 80)
    
    # 检查数据条数
    if "数据条数" in result:
        import re
        match = re.search(r'数据条数.*?(\d+)\s*条', result)
        if match:
            data_count = int(match.group(1))
            print(f"📊 实际获取数据条数: {data_count} 条")
            
            # 365天大约有 250-260 个交易日
            if data_count >= 200:
                print(f"✅ 数据条数正确（>=200条，说明获取了约1年的数据）")
            elif data_count >= 50:
                print(f"⚠️ 数据条数偏少（{data_count}条，可能只获取了2-3个月的数据）")
            else:
                print(f"❌ 数据条数太少（{data_count}条，配置未生效）")
    
    # 检查日期范围
    if "日期范围" in result:
        import re
        match = re.search(r'日期范围.*?(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})', result)
        if match:
            actual_start = match.group(1)
            actual_end = match.group(2)
            print(f"📅 实际日期范围: {actual_start} ~ {actual_end}")
            
            # 计算天数
            from datetime import datetime
            start_dt = datetime.strptime(actual_start, '%Y-%m-%d')
            end_dt = datetime.strptime(actual_end, '%Y-%m-%d')
            days = (end_dt - start_dt).days
            
            print(f"📅 实际天数: {days} 天")
            
            if days >= 300:
                print(f"✅ 日期范围正确（>= 300天，说明配置生效）")
            elif days >= 50:
                print(f"⚠️ 日期范围偏短（{days}天，可能配置未完全生效）")
            else:
                print(f"❌ 日期范围太短（{days}天，配置未生效）")

if __name__ == "__main__":
    test_lookback_days()

