#!/usr/bin/env python3
"""启用MongoDB缓存并测试"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("🔧 启用 MongoDB 缓存")
print("=" * 80)

# 1. 检查 .env 文件
env_file = project_root / ".env"
print(f"\n1️⃣ 检查 .env 文件: {env_file}")
print("-" * 80)

if env_file.exists():
    print("✅ .env 文件存在")
    
    # 读取现有内容
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 检查是否已有 TA_CACHE_STRATEGY 配置
    has_cache_strategy = False
    new_lines = []
    
    for line in lines:
        if line.strip().startswith('TA_CACHE_STRATEGY'):
            has_cache_strategy = True
            # 替换为 integrated
            new_lines.append('TA_CACHE_STRATEGY=integrated\n')
            print(f"✅ 更新配置: TA_CACHE_STRATEGY=integrated")
        else:
            new_lines.append(line)
    
    # 如果没有，添加配置
    if not has_cache_strategy:
        new_lines.append('\n# 缓存策略配置\n')
        new_lines.append('TA_CACHE_STRATEGY=integrated\n')
        print(f"✅ 添加配置: TA_CACHE_STRATEGY=integrated")
    
    # 写回文件
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("\n✅ .env 文件已更新")
    
else:
    print("❌ .env 文件不存在，创建新文件")
    
    # 创建新的 .env 文件
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write('# 缓存策略配置\n')
        f.write('TA_CACHE_STRATEGY=integrated\n')
    
    print("✅ .env 文件已创建")

# 2. 测试缓存配置
print("\n2️⃣ 测试缓存配置")
print("-" * 80)

# 重新加载环境变量
from dotenv import load_dotenv
load_dotenv(env_file, override=True)

cache_strategy = os.getenv("TA_CACHE_STRATEGY", "file")
print(f"当前缓存策略: {cache_strategy}")

if cache_strategy in ["integrated", "adaptive"]:
    print("✅ MongoDB 缓存已启用")
else:
    print("❌ 仍在使用文件缓存")
    print("   请重启应用程序以使配置生效")

# 3. 测试缓存系统
print("\n3️⃣ 测试缓存系统初始化")
print("-" * 80)

try:
    from tradingagents.dataflows.cache import get_cache
    
    cache = get_cache()
    cache_type = type(cache).__name__
    
    print(f"缓存类型: {cache_type}")
    
    if cache_type == "IntegratedCacheManager":
        print("✅ 成功初始化集成缓存管理器")
        
        # 检查MongoDB连接
        if hasattr(cache, 'adaptive_cache'):
            adaptive = cache.adaptive_cache
            if hasattr(adaptive, 'mongodb_client') and adaptive.mongodb_client:
                print("✅ MongoDB 连接成功")
            else:
                print("⚠️ MongoDB 连接失败，将使用文件缓存作为降级")
    elif cache_type == "StockDataCache":
        print("⚠️ 仍在使用文件缓存")
        print("   可能原因:")
        print("   1. MongoDB 连接失败")
        print("   2. 需要重启应用程序")
    else:
        print(f"⚠️ 未知的缓存类型: {cache_type}")
        
except Exception as e:
    print(f"❌ 缓存系统初始化失败: {e}")

# 4. 提供下一步指引
print("\n" + "=" * 80)
print("📋 下一步操作")
print("=" * 80)
print("""
1. ✅ .env 文件已更新，TA_CACHE_STRATEGY=integrated

2. 🔄 重启应用程序以使配置生效:
   - 停止当前运行的后端服务
   - 重新启动: python app/main.py

3. 📊 验证MongoDB缓存是否生效:
   - 运行分析任务（例如分析 AAPL）
   - 运行检查脚本: python scripts/check_us_cache_status.py
   - 查看日志中是否有 "💾 股票数据已保存到MongoDB" 的消息

4. 🔍 如果仍然使用文件缓存:
   - 检查 MongoDB 连接是否正常
   - 查看日志中的错误信息
   - 确认 .env 文件中的 MongoDB 连接配置正确

注意：
- 集成缓存会自动选择最佳后端（MongoDB > Redis > File）
- 如果 MongoDB 不可用，会自动降级到文件缓存
- 文件缓存和 MongoDB 缓存可以共存
""")

