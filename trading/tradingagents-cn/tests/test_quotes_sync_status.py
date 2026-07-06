#!/usr/bin/env python3
"""
测试实时行情同步状态功能

验证内容：
1. 交易时间判断逻辑（包含收盘后30分钟缓冲期）
2. 状态记录功能
3. 状态获取功能
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.quotes_ingestion_service import QuotesIngestionService
from app.core.config import settings


def test_trading_time_logic():
    """测试交易时间判断逻辑"""
    print("\n" + "=" * 80)
    print("测试1: 交易时间判断逻辑（包含收盘后30分钟缓冲期）")
    print("=" * 80)
    
    service = QuotesIngestionService()
    tz = ZoneInfo(settings.TIMEZONE)
    
    # 测试用例
    test_cases = [
        ("09:00", False, "开盘前"),
        ("09:30", True, "上午开盘"),
        ("10:00", True, "上午交易中"),
        ("11:30", True, "上午收盘"),
        ("12:00", False, "午休时间"),
        ("13:00", True, "下午开盘"),
        ("14:00", True, "下午交易中"),
        ("15:00", True, "收盘时刻（缓冲期开始）"),
        ("15:06", True, "收盘后6分钟（缓冲期内）"),
        ("15:12", True, "收盘后12分钟（缓冲期内）"),
        ("15:18", True, "收盘后18分钟（缓冲期内）"),
        ("15:30", True, "收盘后30分钟（缓冲期结束）"),
        ("15:31", False, "收盘后31分钟（缓冲期外）"),
        ("16:00", False, "收盘后1小时"),
    ]
    
    print("\n测试结果：")
    print("-" * 80)
    
    all_passed = True
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
        
        print(f"{time_str:6s} | 预期: {str(expected):5s} | 实际: {str(result):5s} | {status} | {description}")
    
    print("-" * 80)
    if all_passed:
        print("✅ 所有测试用例通过")
    else:
        print("❌ 部分测试用例失败")
    
    return all_passed


async def test_status_record_and_get():
    """测试状态记录和获取功能"""
    print("\n" + "=" * 80)
    print("测试2: 状态记录和获取功能")
    print("=" * 80)
    
    service = QuotesIngestionService()
    
    # 测试记录状态
    print("\n📝 测试记录同步状态...")
    await service._record_sync_status(
        success=True,
        source="tushare",
        records_count=5440,
        error_msg=None
    )
    print("✅ 状态记录成功")
    
    # 测试获取状态
    print("\n📊 测试获取同步状态...")
    status = await service.get_sync_status()
    
    print("\n获取到的状态信息：")
    print("-" * 80)
    for key, value in status.items():
        print(f"{key:20s}: {value}")
    print("-" * 80)
    
    # 验证状态
    checks = [
        ("last_sync_time", lambda v: v is not None, "最后同步时间应该存在"),
        ("interval_seconds", lambda v: v == settings.QUOTES_INGEST_INTERVAL_SECONDS, "同步间隔应该正确"),
        ("interval_minutes", lambda v: v == settings.QUOTES_INGEST_INTERVAL_SECONDS / 60, "同步间隔（分钟）应该正确"),
        ("data_source", lambda v: v == "tushare", "数据源应该是 tushare"),
        ("success", lambda v: v is True, "成功状态应该是 True"),
        ("records_count", lambda v: v == 5440, "记录数应该是 5440"),
        ("error_message", lambda v: v is None, "错误信息应该是 None"),
    ]
    
    print("\n验证结果：")
    print("-" * 80)
    
    all_passed = True
    for key, check_func, description in checks:
        value = status.get(key)
        passed = check_func(value)
        status_str = "✅ 通过" if passed else "❌ 失败"
        
        if not passed:
            all_passed = False
        
        print(f"{key:20s}: {status_str} | {description}")
    
    print("-" * 80)
    if all_passed:
        print("✅ 所有验证通过")
    else:
        print("❌ 部分验证失败")
    
    return all_passed


async def test_error_status():
    """测试错误状态记录"""
    print("\n" + "=" * 80)
    print("测试3: 错误状态记录")
    print("=" * 80)
    
    service = QuotesIngestionService()
    
    # 记录错误状态
    print("\n📝 测试记录错误状态...")
    await service._record_sync_status(
        success=False,
        source="akshare_eastmoney",
        records_count=0,
        error_msg="API 限流"
    )
    print("✅ 错误状态记录成功")
    
    # 获取状态
    print("\n📊 测试获取错误状态...")
    status = await service.get_sync_status()
    
    print("\n获取到的错误状态信息：")
    print("-" * 80)
    for key, value in status.items():
        print(f"{key:20s}: {value}")
    print("-" * 80)
    
    # 验证错误状态
    checks = [
        ("success", lambda v: v is False, "成功状态应该是 False"),
        ("records_count", lambda v: v == 0, "记录数应该是 0"),
        ("error_message", lambda v: v == "API 限流", "错误信息应该正确"),
    ]
    
    print("\n验证结果：")
    print("-" * 80)
    
    all_passed = True
    for key, check_func, description in checks:
        value = status.get(key)
        passed = check_func(value)
        status_str = "✅ 通过" if passed else "❌ 失败"
        
        if not passed:
            all_passed = False
        
        print(f"{key:20s}: {status_str} | {description}")
    
    print("-" * 80)
    if all_passed:
        print("✅ 所有验证通过")
    else:
        print("❌ 部分验证失败")
    
    return all_passed


async def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("实时行情同步状态功能测试")
    print("=" * 80)
    
    results = []
    
    # 测试1：交易时间判断逻辑
    results.append(("交易时间判断逻辑", test_trading_time_logic()))
    
    # 测试2：状态记录和获取
    results.append(("状态记录和获取", await test_status_record_and_get()))
    
    # 测试3：错误状态记录
    results.append(("错误状态记录", await test_error_status()))
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:30s} - {status}")
    
    print(f"\n总体: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n✅ 所有测试通过！实时行情同步状态功能正常")
        return 0
    else:
        print(f"\n❌ 有 {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

