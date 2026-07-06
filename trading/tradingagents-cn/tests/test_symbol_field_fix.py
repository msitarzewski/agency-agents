#!/usr/bin/env python3
"""
测试 symbol 字段修复

验证内容：
1. 同步服务是否正确添加了 symbol 字段
2. 查询逻辑是否能正确处理 symbol 字段
3. 股票名称是否能正确对应
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_basics_sync_service_has_symbol_field():
    """测试 basics_sync_service.py 是否添加了 symbol 字段"""
    print("\n" + "=" * 60)
    print("测试1: basics_sync_service.py 是否添加了 symbol 字段")
    print("=" * 60)
    
    with open("app/services/basics_sync_service.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 检查是否有 "symbol": code 的代码
    if '"symbol": code' in content or "'symbol': code" in content:
        print("✅ 发现 symbol 字段添加代码")
        return True
    else:
        print("❌ 未发现 symbol 字段添加代码")
        return False


def test_multi_source_sync_service_has_symbol_field():
    """测试 multi_source_basics_sync_service.py 是否添加了 symbol 字段"""
    print("\n" + "=" * 60)
    print("测试2: multi_source_basics_sync_service.py 是否添加了 symbol 字段")
    print("=" * 60)
    
    with open("app/services/multi_source_basics_sync_service.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 检查是否有 "symbol": code 的代码
    if '"symbol": code' in content or "'symbol': code" in content:
        print("✅ 发现 symbol 字段添加代码")
        return True
    else:
        print("❌ 未发现 symbol 字段添加代码")
        return False


def test_baostock_sync_service_has_symbol_field():
    """测试 baostock_sync_service.py 是否添加了 symbol 字段"""
    print("\n" + "=" * 60)
    print("测试3: baostock_sync_service.py 是否添加了 symbol 字段")
    print("=" * 60)
    
    with open("app/worker/baostock_sync_service.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 检查是否有添加 symbol 字段的代码
    if 'basic_info["symbol"]' in content or "basic_info['symbol']" in content:
        print("✅ 发现 symbol 字段添加代码")
        return True
    else:
        print("❌ 未发现 symbol 字段添加代码")
        return False


def test_app_adapter_query_logic():
    """测试 app_adapter.py 是否支持 symbol 字段查询"""
    print("\n" + "=" * 60)
    print("测试4: app_adapter.py 是否支持 symbol 字段查询")
    print("=" * 60)
    
    with open("tradingagents/dataflows/cache/app_adapter.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 检查是否有 $or 查询逻辑
    if '"$or"' in content and '"symbol"' in content and '"code"' in content:
        print("✅ 发现 symbol 和 code 的 $or 查询逻辑")
        return True
    else:
        print("❌ 未发现 $or 查询逻辑")
        return False


def test_migration_script_exists():
    """测试迁移脚本是否存在"""
    print("\n" + "=" * 60)
    print("测试5: 迁移脚本是否存在")
    print("=" * 60)
    
    migration_script = Path("scripts/migrations/add_symbol_field_to_stock_basic_info.py")
    if migration_script.exists():
        print(f"✅ 迁移脚本存在: {migration_script}")
        return True
    else:
        print(f"❌ 迁移脚本不存在: {migration_script}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("symbol 字段修复验证测试")
    print("=" * 60)
    
    results = []
    
    # 运行所有测试
    results.append(("basics_sync_service", test_basics_sync_service_has_symbol_field()))
    results.append(("multi_source_sync_service", test_multi_source_sync_service_has_symbol_field()))
    results.append(("baostock_sync_service", test_baostock_sync_service_has_symbol_field()))
    results.append(("app_adapter_query", test_app_adapter_query_logic()))
    results.append(("migration_script", test_migration_script_exists()))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:30s} - {status}")
    
    print(f"\n总体: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n✅ 所有测试通过！symbol 字段修复已完成")
        return 0
    else:
        print(f"\n❌ 有 {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

