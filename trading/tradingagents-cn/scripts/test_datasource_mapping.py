#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据源名称映射（修复后）
"""

# 模拟数据库返回的数据源优先级（包含脏数据）
us_priority_from_db = ['Alpha Vantage', 'alpha_vantage', 'Yahoo Finance', 'yahoo_finance', 'Finnhub']

print("=" * 80)
print("📊 数据库返回的美股数据源优先级（包含脏数据）:")
print("-" * 80)
for i, source in enumerate(us_priority_from_db, 1):
    print(f"{i}. {source}")

# 数据源名称映射（只有这些是有效的）
source_handlers = {
    'alpha_vantage': 'alpha_vantage',
    'yahoo_finance': 'yfinance',
    'finnhub': 'finnhub',
}

print("\n" + "=" * 80)
print("🔄 过滤有效数据源并去重:")
print("-" * 80)

# 过滤有效数据源并去重
valid_priority = []
seen = set()
for source_name in us_priority_from_db:
    source_key = source_name.lower()
    # 只保留有效的数据源
    if source_key in source_handlers and source_key not in seen:
        seen.add(source_key)
        valid_priority.append(source_name)
        print(f"✅ 保留: {source_name} (小写: {source_key})")
    else:
        if source_key in seen:
            print(f"⚠️ 跳过（重复）: {source_name}")
        else:
            print(f"❌ 跳过（无效）: {source_name}")

print("\n" + "=" * 80)
print("✅ 最终有效的数据源优先级:")
print("-" * 80)

for i, source in enumerate(valid_priority, 1):
    source_key = source.lower()
    handler_name = source_handlers[source_key]
    print(f"{i}. {source} → {handler_name}")

print("=" * 80)

