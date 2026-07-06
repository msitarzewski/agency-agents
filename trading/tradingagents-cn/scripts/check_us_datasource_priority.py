#!/usr/bin/env python3
"""检查美股数据源优先级配置"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_mongo_db_sync

db = get_mongo_db_sync()

print("=" * 70)
print("📊 美股数据源分组配置（datasource_groupings 集合）")
print("=" * 70)

# 查询美股数据源分组
groupings = list(db.datasource_groupings.find({
    "market_category_id": "us_stocks"
}).sort("priority", -1))  # 按优先级降序排列

print(f"\n找到 {len(groupings)} 个美股数据源分组\n")

for g in groupings:
    print(f"数据源: {g.get('data_source_name')}")
    print(f"  优先级: {g.get('priority')}")
    print(f"  启用: {g.get('enabled')}")
    print()

print("=" * 70)
print("📊 数据源配置（system_configs 集合）")
print("=" * 70)

# 查询激活的配置
config = db.system_configs.find_one({"is_active": True})

if config:
    print(f"\n配置版本: {config.get('version')}")
    print(f"是否激活: {config.get('is_active')}\n")
    
    datasources = config.get('data_source_configs', [])
    
    # 过滤美股数据源
    us_datasources = []
    for ds in datasources:
        name = ds.get('name', '').lower()
        if name in ['alpha_vantage', 'finnhub', 'yahoo_finance', 'yfinance']:
            us_datasources.append(ds)
    
    # 按优先级排序
    us_datasources.sort(key=lambda x: x.get('priority', 0), reverse=True)
    
    print(f"美股数据源配置（按优先级排序）:\n")
    for ds in us_datasources:
        name = ds.get('name')
        priority = ds.get('priority', 0)
        enabled = ds.get('enabled', False)
        has_api_key = bool(ds.get('api_key'))
        
        print(f"数据源: {name}")
        print(f"  优先级: {priority}")
        print(f"  启用: {enabled}")
        print(f"  API Key: {'✅ 已配置' if has_api_key else '❌ 未配置'}")
        print()
else:
    print("❌ 没有找到激活的配置")

