#!/usr/bin/env python3
"""
测试交易时间判断逻辑（包含收盘后30分钟缓冲期）

这个测试不需要数据库连接，只测试核心逻辑
"""

import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.quotes_ingestion_service import QuotesIngestionService
from app.core.config import settings


def test_trading_time_logic():
    """测试交易时间判断逻辑"""
    print("\n" + "=" * 80)
    print("测试: 交易时间判断逻辑（包含收盘后30分钟缓冲期）")
    print("=" * 80)
    
    service = QuotesIngestionService()
    tz = ZoneInfo(settings.TIMEZONE)
    
    # 测试用例
    test_cases = [
        ("09:00", False, "开盘前"),
        ("09:29", False, "开盘前1分钟"),
        ("09:30", True, "上午开盘"),
        ("10:00", True, "上午交易中"),
        ("11:30", True, "上午收盘"),
        ("11:31", False, "午休开始"),
        ("12:00", False, "午休时间"),
        ("12:59", False, "午休结束前"),
        ("13:00", True, "下午开盘"),
        ("14:00", True, "下午交易中"),
        ("14:55", True, "收盘前5分钟"),
        ("15:00", True, "收盘时刻（缓冲期开始）✨"),
        ("15:06", True, "收盘后6分钟（第1次同步机会）✨"),
        ("15:12", True, "收盘后12分钟（第2次同步机会）✨"),
        ("15:18", True, "收盘后18分钟（第3次同步机会）✨"),
        ("15:24", True, "收盘后24分钟（第4次同步机会）✨"),
        ("15:30", True, "收盘后30分钟（缓冲期结束）✨"),
        ("15:31", False, "收盘后31分钟（缓冲期外）"),
        ("16:00", False, "收盘后1小时"),
    ]
    
    print("\n测试结果：")
    print("-" * 80)
    print(f"{'时间':^8} | {'预期':^6} | {'实际':^6} | {'状态':^8} | {'说明'}")
    print("-" * 80)
    
    all_passed = True
    buffer_period_tests = []
    
    for time_str, expected, description in test_cases:
        # 创建测试时间（使用今天的日期 + 指定时间）
        now = datetime.now(tz)
        hour, minute = map(int, time_str.split(":"))
        test_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # 确保是工作日（周一到周五）
        if test_time.weekday() >= 5:
            # 如果是周末，调整到周一
            days_to_monday = 7 - test_time.weekday()
            test_time = test_time.replace(day=test_time.day + days_to_monday)
        
        result = service._is_trading_time(test_time)
        status = "✅ 通过" if result == expected else "❌ 失败"
        
        if result != expected:
            all_passed = False
        
        # 标记缓冲期测试
        if "✨" in description:
            buffer_period_tests.append((time_str, result, expected))
        
        print(f"{time_str:^8} | {str(expected):^6} | {str(result):^6} | {status:^8} | {description}")
    
    print("-" * 80)
    
    # 总结
    if all_passed:
        print("\n✅ 所有测试用例通过！")
    else:
        print("\n❌ 部分测试用例失败")
    
    # 缓冲期测试总结
    print("\n" + "=" * 80)
    print("收盘后缓冲期测试总结")
    print("=" * 80)
    print(f"\n配置的同步间隔: {settings.QUOTES_INGEST_INTERVAL_SECONDS} 秒 ({settings.QUOTES_INGEST_INTERVAL_SECONDS / 60} 分钟)")
    print(f"缓冲期时长: 30 分钟 (15:00-15:30)")
    print(f"理论同步次数: {30 * 60 // settings.QUOTES_INGEST_INTERVAL_SECONDS} 次")
    
    print("\n缓冲期内的同步机会：")
    for i, (time_str, result, expected) in enumerate(buffer_period_tests, 1):
        status = "✅" if result == expected else "❌"
        print(f"  {status} 第{i}次机会: {time_str} - {'可以同步' if result else '不能同步'}")
    
    print("\n💡 说明：")
    print("  - 收盘时间是 15:00")
    print("  - 缓冲期延长到 15:30，增加 30 分钟")
    print(f"  - 假设同步间隔为 {settings.QUOTES_INGEST_INTERVAL_SECONDS / 60} 分钟")
    print(f"  - 在缓冲期内可以进行 {30 * 60 // settings.QUOTES_INGEST_INTERVAL_SECONDS} 次同步")
    print("  - 大大降低了错过收盘价的风险！")
    
    return all_passed


if __name__ == "__main__":
    success = test_trading_time_logic()
    sys.exit(0 if success else 1)

