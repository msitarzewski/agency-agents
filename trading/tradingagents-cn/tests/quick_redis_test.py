#!/usr/bin/env python3
"""
Redis快速连接测试脚本
"""

import redis
import time
import sys

def quick_redis_test(host=None, port=None, password=None):
    """快速Redis连接和性能测试"""
    
    # 从环境变量获取配置
    host = host or os.getenv('REDIS_HOST', 'localhost')
    port = port or int(os.getenv('REDIS_PORT', 6379))
    password = password or os.getenv('REDIS_PASSWORD')
    
    print(f"🔍 测试Redis连接: {host}:{port}")
    
    try:
        # 创建Redis连接
        start_time = time.time()
        r = redis.Redis(
            host=host, 
            port=port, 
            password=password,
            decode_responses=True,
            socket_connect_timeout=5
        )
        
        # 测试连接
        r.ping()
        connect_time = (time.time() - start_time) * 1000
        print(f"✅ 连接成功! 连接时间: {connect_time:.2f} ms")
        
        # 测试基本操作延迟
        print("\n📊 基本操作延迟测试:")
        
        # SET操作测试
        start_time = time.time()
        r.set("test_key", "test_value")
        set_time = (time.time() - start_time) * 1000
        print(f"  SET操作: {set_time:.2f} ms")
        
        # GET操作测试
        start_time = time.time()
        value = r.get("test_key")
        get_time = (time.time() - start_time) * 1000
        print(f"  GET操作: {get_time:.2f} ms")
        
        # PING操作测试
        ping_times = []
        for i in range(10):
            start_time = time.time()
            r.ping()
            ping_time = (time.time() - start_time) * 1000
            ping_times.append(ping_time)
        
        avg_ping = sum(ping_times) / len(ping_times)
        min_ping = min(ping_times)
        max_ping = max(ping_times)
        
        print(f"  PING操作 (10次平均): {avg_ping:.2f} ms")
        print(f"  PING最小/最大: {min_ping:.2f} / {max_ping:.2f} ms")
        
        # 简单吞吐量测试
        print("\n🚀 简单吞吐量测试 (100次操作):")
        
        start_time = time.time()
        for i in range(100):
            r.set(f"throughput_test_{i}", f"value_{i}")
        set_duration = time.time() - start_time
        set_throughput = 100 / set_duration
        
        start_time = time.time()
        for i in range(100):
            r.get(f"throughput_test_{i}")
        get_duration = time.time() - start_time
        get_throughput = 100 / get_duration
        
        print(f"  SET吞吐量: {set_throughput:.2f} 操作/秒")
        print(f"  GET吞吐量: {get_throughput:.2f} 操作/秒")
        
        # 清理测试数据
        r.delete("test_key")
        for i in range(100):
            r.delete(f"throughput_test_{i}")
        
        # 连接信息
        print(f"\n📋 Redis服务器信息:")
        info = r.info()
        print(f"  Redis版本: {info.get('redis_version', 'N/A')}")
        print(f"  运行模式: {info.get('redis_mode', 'N/A')}")
        print(f"  已连接客户端: {info.get('connected_clients', 'N/A')}")
        print(f"  内存使用: {info.get('used_memory_human', 'N/A')}")
        
        return True
        
    except redis.ConnectionError as e:
        print(f"❌ Redis连接失败: {e}")
        return False
    except redis.TimeoutError as e:
        print(f"❌ Redis连接超时: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) > 1:
        host = sys.argv[1]
    else:
        host = 'localhost'
    
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    else:
        port = 6379
    
    if len(sys.argv) > 3:
        password = sys.argv[3]
    else:
        password = None
    
    success = quick_redis_test(host, port, password)
    
    if success:
        print("\n✅ Redis连接测试完成!")
    else:
        print("\n❌ Redis连接测试失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()
