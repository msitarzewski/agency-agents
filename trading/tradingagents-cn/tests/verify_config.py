#!/usr/bin/env python3
"""
验证配置是否正确
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("🔧 验证.env配置")
print("=" * 30)

# 检查启用开关
mongodb_enabled = os.getenv("MONGODB_ENABLED", "false")
redis_enabled = os.getenv("REDIS_ENABLED", "false")

print(f"MONGODB_ENABLED: {mongodb_enabled}")
print(f"REDIS_ENABLED: {redis_enabled}")

# 使用强健的布尔值解析（兼容Python 3.13+）
try:
    from tradingagents.config.env_utils import parse_bool_env
    mongodb_bool = parse_bool_env("MONGODB_ENABLED", False)
    redis_bool = parse_bool_env("REDIS_ENABLED", False)
    print("✅ 使用强健的布尔值解析")
except ImportError:
    # 回退到原始方法
    mongodb_bool = mongodb_enabled.lower() == "true"
    redis_bool = redis_enabled.lower() == "true"
    print("⚠️ 使用传统布尔值解析")

print(f"MongoDB启用: {mongodb_bool}")
print(f"Redis启用: {redis_bool}")

if not mongodb_bool and not redis_bool:
    print("✅ 默认配置：数据库都未启用，系统将使用文件缓存")
else:
    print("⚠️ 有数据库启用，系统将尝试连接数据库")

print("\n💡 配置说明:")
print("- MONGODB_ENABLED=false (默认)")
print("- REDIS_ENABLED=false (默认)")
print("- 系统使用文件缓存，无需数据库")
print("- 如需启用数据库，修改.env文件中的对应值为true")
