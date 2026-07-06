import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tradingagents.dataflows.providers.china.tushare import get_tushare_provider
from datetime import datetime

provider = get_tushare_provider()
api = provider.api

if api is None:
    print("❌ Tushare API 不可用")
    sys.exit(1)

print("✅ Tushare API 可用")

# 测试不同的查询方式
print("\n🔍 测试1: 按 end_date 查询（最近季度）")
try:
    df = api.fina_indicator(end_date='20240930', fields="ts_code,end_date,roe")
    print(f"  结果: {len(df) if df is not None and not df.empty else 0} 条记录")
    if df is not None and not df.empty:
        print(f"  前3条数据:")
        print(df.head(3))
except Exception as e:
    print(f"  ❌ 失败: {e}")

print("\n🔍 测试2: 按 ts_code 查询（单个股票）")
try:
    df = api.fina_indicator(ts_code='601398.SH', fields="ts_code,end_date,roe")
    print(f"  结果: {len(df) if df is not None and not df.empty else 0} 条记录")
    if df is not None and not df.empty:
        print(f"  数据:")
        print(df)
except Exception as e:
    print(f"  ❌ 失败: {e}")

print("\n🔍 测试3: 按 period 查询（最近报告期）")
try:
    df = api.fina_indicator(period='20240930', fields="ts_code,end_date,roe")
    print(f"  结果: {len(df) if df is not None and not df.empty else 0} 条记录")
    if df is not None and not df.empty:
        print(f"  前3条数据:")
        print(df.head(3))
except Exception as e:
    print(f"  ❌ 失败: {e}")

print("\n🔍 测试4: 不指定日期，只查询单个股票")
try:
    df = api.fina_indicator(ts_code='601398.SH', limit=4, fields="ts_code,end_date,roe")
    print(f"  结果: {len(df) if df is not None and not df.empty else 0} 条记录")
    if df is not None and not df.empty:
        print(f"  数据:")
        print(df)
except Exception as e:
    print(f"  ❌ 失败: {e}")

