#!/usr/bin/env python
"""
检查 Redis 连接状态和 PubSub 频道

用法：
    python scripts/check_redis_connections.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
import redis.asyncio as redis


async def check_redis_connections():
    """检查 Redis 连接状态"""
    print("=" * 80)
    print("📊 检查 Redis 连接状态")
    print("=" * 80)
    print()

    # 创建 Redis 客户端
    r = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True
    )

    try:
        # 1. 检查 Redis 服务器信息
        print("1️⃣ Redis 服务器信息:")
        print("-" * 80)
        info = await r.info()
        
        print(f"   Redis 版本: {info.get('redis_version', 'N/A')}")
        print(f"   运行模式: {info.get('redis_mode', 'N/A')}")
        print(f"   已连接客户端数: {info.get('connected_clients', 'N/A')}")
        print(f"   最大客户端数: {info.get('maxclients', 'N/A')}")
        print(f"   已使用内存: {info.get('used_memory_human', 'N/A')}")
        print(f"   内存峰值: {info.get('used_memory_peak_human', 'N/A')}")
        print()

        # 2. 检查客户端连接列表
        print("2️⃣ 客户端连接列表:")
        print("-" * 80)
        client_list = await r.client_list()
        
        # 统计连接类型
        normal_clients = []
        pubsub_clients = []
        
        for client in client_list:
            if 'pubsub' in client.get('flags', ''):
                pubsub_clients.append(client)
            else:
                normal_clients.append(client)
        
        print(f"   普通连接数: {len(normal_clients)}")
        print(f"   PubSub 连接数: {len(pubsub_clients)}")
        print(f"   总连接数: {len(client_list)}")
        print()

        # 3. 显示 PubSub 连接详情
        if pubsub_clients:
            print("3️⃣ PubSub 连接详情:")
            print("-" * 80)
            for i, client in enumerate(pubsub_clients, 1):
                print(f"   [{i}] 地址: {client.get('addr', 'N/A')}")
                print(f"       名称: {client.get('name', 'N/A')}")
                print(f"       年龄: {client.get('age', 'N/A')} 秒")
                print(f"       空闲: {client.get('idle', 'N/A')} 秒")
                print(f"       标志: {client.get('flags', 'N/A')}")
                print(f"       订阅数: {client.get('psub', 'N/A')} 个模式, {client.get('sub', 'N/A')} 个频道")
                print()
        else:
            print("3️⃣ 没有活跃的 PubSub 连接")
            print()

        # 4. 检查 PubSub 频道
        print("4️⃣ PubSub 频道信息:")
        print("-" * 80)
        
        # 获取所有活跃的频道
        channels = await r.pubsub_channels()
        print(f"   活跃频道数: {len(channels)}")
        
        if channels:
            print("   频道列表:")
            for channel in channels:
                # 获取每个频道的订阅者数量
                num_subs = await r.pubsub_numsub(channel)
                if num_subs:
                    channel_name, sub_count = num_subs[0]
                    print(f"      - {channel_name}: {sub_count} 个订阅者")
        else:
            print("   没有活跃的频道")
        print()

        # 5. 检查连接池配置
        print("5️⃣ 应用配置:")
        print("-" * 80)
        print(f"   REDIS_MAX_CONNECTIONS: {settings.REDIS_MAX_CONNECTIONS}")
        print(f"   REDIS_RETRY_ON_TIMEOUT: {settings.REDIS_RETRY_ON_TIMEOUT}")
        print()

        # 6. 警告和建议
        print("6️⃣ 分析和建议:")
        print("-" * 80)
        
        connected_clients = info.get('connected_clients', 0)
        max_clients = info.get('maxclients', 10000)
        
        if connected_clients > max_clients * 0.8:
            print("   ⚠️ 警告: 连接数接近最大值！")
            print(f"      当前: {connected_clients}, 最大: {max_clients}")
            print("      建议: 重启 Redis 服务或增加 maxclients 配置")
        elif connected_clients > 100:
            print("   ⚠️ 警告: 连接数较多！")
            print(f"      当前: {connected_clients}")
            print("      建议: 检查是否有连接泄漏")
        else:
            print("   ✅ 连接数正常")
        
        print()
        
        if len(pubsub_clients) > 10:
            print("   ⚠️ 警告: PubSub 连接数较多！")
            print(f"      当前: {len(pubsub_clients)}")
            print("      建议: 检查是否有 PubSub 连接泄漏")
        elif len(pubsub_clients) > 0:
            print(f"   ℹ️ 信息: 有 {len(pubsub_clients)} 个活跃的 PubSub 连接")
        else:
            print("   ✅ 没有活跃的 PubSub 连接")
        
        print()

    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await r.close()

    print("=" * 80)
    print("✅ 检查完成")
    print("=" * 80)


async def kill_idle_pubsub_connections(idle_threshold: int = 300):
    """
    杀死空闲的 PubSub 连接
    
    Args:
        idle_threshold: 空闲时间阈值（秒），默认 300 秒（5 分钟）
    """
    print("=" * 80)
    print(f"🔪 杀死空闲超过 {idle_threshold} 秒的 PubSub 连接")
    print("=" * 80)
    print()

    r = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True
    )

    try:
        client_list = await r.client_list()
        
        killed_count = 0
        for client in client_list:
            if 'pubsub' in client.get('flags', ''):
                idle = client.get('idle', 0)
                if idle > idle_threshold:
                    addr = client.get('addr', 'N/A')
                    print(f"   🔪 杀死连接: {addr} (空闲 {idle} 秒)")
                    try:
                        # 使用 CLIENT KILL 命令杀死连接
                        await r.execute_command('CLIENT', 'KILL', 'TYPE', 'pubsub', 'SKIPME', 'yes')
                        killed_count += 1
                    except Exception as e:
                        print(f"      ❌ 失败: {e}")
        
        print()
        print(f"✅ 已杀死 {killed_count} 个空闲的 PubSub 连接")
        
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await r.close()

    print("=" * 80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="检查 Redis 连接状态")
    parser.add_argument(
        "--kill-idle",
        type=int,
        metavar="SECONDS",
        help="杀死空闲超过指定秒数的 PubSub 连接（例如：--kill-idle 300）"
    )
    
    args = parser.parse_args()
    
    if args.kill_idle:
        asyncio.run(kill_idle_pubsub_connections(args.kill_idle))
    else:
        asyncio.run(check_redis_connections())

