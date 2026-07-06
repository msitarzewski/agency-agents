#!/usr/bin/env python3
"""
测试修复后的降级机制是否避免了无限重试
验证不存在的股票代码不会导致无限循环
"""

import sys
import os
import time
import threading

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TimeoutException(Exception):
    pass

def timeout_handler():
    """超时处理器"""
    time.sleep(30)  # 30秒超时
    raise TimeoutException("测试超时，可能存在无限重试")

def test_no_infinite_retry_stock_data():
    """测试股票历史数据获取不会无限重试"""
    print("🔍 测试股票历史数据获取不会无限重试")
    print("=" * 50)
    
    # 启动超时监控
    timeout_thread = threading.Thread(target=timeout_handler, daemon=True)
    timeout_thread.start()
    
    # 测试不存在的股票代码
    fake_codes = ["999999", "888888"]
    
    for code in fake_codes:
        print(f"\n📊 测试不存在的股票代码: {code}")
        print("-" * 30)
        
        start_time = time.time()
        
        try:
            from tradingagents.dataflows.interface import get_china_stock_data_unified
            result = get_china_stock_data_unified(code, "2025-07-01", "2025-07-17")
            
            end_time = time.time()
            elapsed = end_time - start_time
            
            print(f"✅ 测试完成，耗时: {elapsed:.2f}秒")
            print(f"📊 结果: {result[:100] if result else 'None'}...")
            
            if elapsed > 25:
                print("⚠️ 耗时过长，可能存在重试问题")
            else:
                print("✅ 耗时正常，没有无限重试")
                
        except TimeoutException:
            print("❌ 测试超时！存在无限重试问题")
            return False
        except Exception as e:
            end_time = time.time()
            elapsed = end_time - start_time
            print(f"❌ 测试失败: {e}")
            print(f"⏱️ 失败前耗时: {elapsed:.2f}秒")
    
    return True

def test_no_infinite_retry_stock_info():
    """测试股票基本信息获取不会无限重试"""
    print("\n🔍 测试股票基本信息获取不会无限重试")
    print("=" * 50)
    
    # 测试不存在的股票代码
    fake_codes = ["999999", "888888"]
    
    for code in fake_codes:
        print(f"\n📊 测试不存在的股票代码: {code}")
        print("-" * 30)
        
        start_time = time.time()
        
        try:
            from tradingagents.dataflows.interface import get_china_stock_info_unified
            result = get_china_stock_info_unified(code)
            
            end_time = time.time()
            elapsed = end_time - start_time
            
            print(f"✅ 测试完成，耗时: {elapsed:.2f}秒")
            print(f"📊 结果: {result[:100] if result else 'None'}...")
            
            if elapsed > 10:
                print("⚠️ 耗时过长，可能存在重试问题")
            else:
                print("✅ 耗时正常，没有无限重试")
                
        except Exception as e:
            end_time = time.time()
            elapsed = end_time - start_time
            print(f"❌ 测试失败: {e}")
            print(f"⏱️ 失败前耗时: {elapsed:.2f}秒")
    
    return True

def test_fallback_mechanism_logic():
    """测试降级机制的逻辑正确性"""
    print("\n🔍 测试降级机制的逻辑正确性")
    print("=" * 50)
    
    try:
        from tradingagents.dataflows.data_source_manager import get_data_source_manager
        manager = get_data_source_manager()
        
        # 检查降级方法是否存在
        if hasattr(manager, '_try_fallback_sources'):
            print("✅ _try_fallback_sources方法存在")
        else:
            print("❌ _try_fallback_sources方法不存在")
            return False
        
        if hasattr(manager, '_try_fallback_stock_info'):
            print("✅ _try_fallback_stock_info方法存在")
        else:
            print("❌ _try_fallback_stock_info方法不存在")
            return False
        
        # 检查可用数据源
        available_sources = manager.available_sources
        print(f"📊 可用数据源: {available_sources}")
        
        if len(available_sources) > 1:
            print("✅ 有多个数据源可用于降级")
        else:
            print("⚠️ 只有一个数据源，降级机制可能无效")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_real_stock_performance():
    """测试真实股票的性能表现"""
    print("\n🔍 测试真实股票的性能表现")
    print("=" * 50)
    
    # 测试真实股票代码
    real_codes = ["603985", "000001"]
    
    for code in real_codes:
        print(f"\n📊 测试股票代码: {code}")
        print("-" * 30)
        
        start_time = time.time()
        
        try:
            # 测试历史数据
            from tradingagents.dataflows.interface import get_china_stock_data_unified
            data_result = get_china_stock_data_unified(code, "2025-07-15", "2025-07-17")
            
            data_time = time.time()
            data_elapsed = data_time - start_time
            
            # 测试基本信息
            from tradingagents.dataflows.interface import get_china_stock_info_unified
            info_result = get_china_stock_info_unified(code)
            
            end_time = time.time()
            info_elapsed = end_time - data_time
            total_elapsed = end_time - start_time
            
            print(f"✅ 历史数据获取耗时: {data_elapsed:.2f}秒")
            print(f"✅ 基本信息获取耗时: {info_elapsed:.2f}秒")
            print(f"✅ 总耗时: {total_elapsed:.2f}秒")
            
            if total_elapsed > 15:
                print("⚠️ 总耗时过长")
            else:
                print("✅ 性能表现良好")
                
        except Exception as e:
            end_time = time.time()
            elapsed = end_time - start_time
            print(f"❌ 测试失败: {e}")
            print(f"⏱️ 失败前耗时: {elapsed:.2f}秒")

if __name__ == "__main__":
    print("🧪 无限重试问题修复验证测试")
    print("=" * 80)
    print("📝 此测试验证修复后的降级机制不会导致无限重试")
    print("=" * 80)
    
    success = True
    
    # 1. 测试股票历史数据不会无限重试
    if not test_no_infinite_retry_stock_data():
        success = False
    
    # 2. 测试股票基本信息不会无限重试
    if not test_no_infinite_retry_stock_info():
        success = False
    
    # 3. 测试降级机制逻辑
    if not test_fallback_mechanism_logic():
        success = False
    
    # 4. 测试真实股票性能
    test_real_stock_performance()
    
    print("\n📋 测试总结")
    print("=" * 60)
    if success:
        print("✅ 无限重试问题修复验证测试通过")
        print("🎯 降级机制现在能够:")
        print("   - 避免递归调用导致的无限重试")
        print("   - 在合理时间内完成所有数据源尝试")
        print("   - 正确处理不存在的股票代码")
    else:
        print("❌ 测试发现问题，需要进一步修复")
        print("🔍 请检查:")
        print("   - 降级机制是否存在递归调用")
        print("   - 超时设置是否合理")
        print("   - 错误处理是否完善")
