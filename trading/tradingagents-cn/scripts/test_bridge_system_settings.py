#!/usr/bin/env python3
"""
直接测试 _bridge_system_settings 函数
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置日志级别为 DEBUG
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s'
)

async def main():
    """测试 _bridge_system_settings"""
    print("=" * 60)
    print("🧪 测试 _bridge_system_settings 函数")
    print("=" * 60)
    
    # 1. 初始化数据库
    print("\n1️⃣ 初始化数据库连接...")
    from app.core.database import init_db
    await init_db()
    print("✅ 数据库连接成功")
    
    # 2. 直接调用 _bridge_system_settings
    print("\n2️⃣ 调用 _bridge_system_settings...")
    from app.core.config_bridge import _bridge_system_settings
    
    count = _bridge_system_settings()
    print(f"\n✅ 桥接了 {count} 个配置项")
    
    # 3. 检查环境变量
    print("\n3️⃣ 检查环境变量...")
    ta_env_keys = [
        'TA_USE_APP_CACHE',
        'TA_HK_MIN_REQUEST_INTERVAL_SECONDS',
        'TA_HK_TIMEOUT_SECONDS',
        'TA_HK_MAX_RETRIES',
        'TA_HK_RATE_LIMIT_WAIT_SECONDS',
        'TA_HK_CACHE_TTL_SECONDS',
    ]
    
    for key in ta_env_keys:
        value = os.getenv(key)
        if value:
            print(f"  ✅ {key}: {value}")
        else:
            print(f"  ❌ {key}: 未设置")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

