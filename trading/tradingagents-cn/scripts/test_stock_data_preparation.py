#!/usr/bin/env python3
"""
股票数据预获取功能测试脚本
验证新的股票数据准备机制是否正常工作
"""

import sys
import os
import time
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_stock_data_preparation():
    """测试股票数据预获取功能"""
    print("🧪 股票数据预获取功能测试")
    print("=" * 80)
    
    try:
        from tradingagents.utils.stock_validator import prepare_stock_data, get_stock_preparation_message
        
        # 测试用例
        test_cases = [
            # A股测试
            {"code": "000001", "market": "A股", "name": "平安银行", "should_exist": True},
            {"code": "603985", "market": "A股", "name": "恒润股份", "should_exist": True},
            {"code": "999999", "market": "A股", "name": "不存在的股票", "should_exist": False},
            
            # 港股测试
            {"code": "0700.HK", "market": "港股", "name": "腾讯控股", "should_exist": True},
            {"code": "9988.HK", "market": "港股", "name": "阿里巴巴", "should_exist": True},
            {"code": "9999.HK", "market": "港股", "name": "不存在的港股", "should_exist": False},
            
            # 美股测试
            {"code": "AAPL", "market": "美股", "name": "苹果公司", "should_exist": True},
            {"code": "TSLA", "market": "美股", "name": "特斯拉", "should_exist": True},
            {"code": "ZZZZ", "market": "美股", "name": "不存在的美股", "should_exist": False},
        ]
        
        success_count = 0
        total_count = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📊 测试 {i}/{total_count}: {test_case['code']} ({test_case['market']})")
            print("-" * 60)
            
            start_time = time.time()
            
            # 测试数据准备
            result = prepare_stock_data(
                stock_code=test_case['code'],
                market_type=test_case['market'],
                period_days=30,  # 测试30天数据
                analysis_date=datetime.now().strftime('%Y-%m-%d')
            )
            
            end_time = time.time()
            elapsed = end_time - start_time
            
            print(f"⏱️ 耗时: {elapsed:.2f}秒")
            print(f"📋 结果: {'成功' if result.is_valid else '失败'}")
            
            if result.is_valid:
                print(f"📈 股票名称: {result.stock_name}")
                print(f"📊 市场类型: {result.market_type}")
                print(f"📅 数据时长: {result.data_period_days}天")
                print(f"💾 缓存状态: {result.cache_status}")
                print(f"📁 历史数据: {'✅' if result.has_historical_data else '❌'}")
                print(f"ℹ️ 基本信息: {'✅' if result.has_basic_info else '❌'}")
            else:
                print(f"❌ 错误信息: {result.error_message}")
                print(f"💡 建议: {result.suggestion}")
            
            # 验证结果是否符合预期
            if result.is_valid == test_case['should_exist']:
                print("✅ 测试通过")
                success_count += 1
            else:
                expected = "存在" if test_case['should_exist'] else "不存在"
                actual = "存在" if result.is_valid else "不存在"
                print(f"❌ 测试失败: 预期{expected}，实际{actual}")
            
            # 测试便捷函数
            message = get_stock_preparation_message(
                test_case['code'], 
                test_case['market'], 
                30
            )
            print(f"📝 便捷函数消息: {message[:100]}...")
        
        # 测试总结
        print(f"\n📋 测试总结")
        print("=" * 60)
        print(f"✅ 成功: {success_count}/{total_count}")
        print(f"❌ 失败: {total_count - success_count}/{total_count}")
        print(f"📊 成功率: {success_count/total_count*100:.1f}%")
        
        if success_count == total_count:
            print("🎉 所有测试通过！股票数据预获取功能正常工作")
            return True
        else:
            print("⚠️ 部分测试失败，需要检查功能实现")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_format_validation():
    """测试格式验证功能"""
    print("\n🔍 格式验证测试")
    print("=" * 60)
    
    try:
        from tradingagents.utils.stock_validator import prepare_stock_data
        
        format_tests = [
            # 格式正确的测试
            {"code": "000001", "market": "A股", "should_pass": True},
            {"code": "0700.HK", "market": "港股", "should_pass": True},
            {"code": "AAPL", "market": "美股", "should_pass": True},
            
            # 格式错误的测试
            {"code": "00001", "market": "A股", "should_pass": False},  # 5位数字
            {"code": "ABC.HK", "market": "港股", "should_pass": False},  # 字母
            {"code": "123", "market": "美股", "should_pass": False},  # 数字
            {"code": "", "market": "A股", "should_pass": False},  # 空字符串
        ]
        
        format_success = 0
        
        for i, test in enumerate(format_tests, 1):
            print(f"\n📝 格式测试 {i}: '{test['code']}' ({test['market']})")
            
            result = prepare_stock_data(test['code'], test['market'])
            
            # 格式错误应该在数据获取前就被拦截
            format_passed = not (result.error_message and "格式错误" in result.error_message)
            
            if format_passed == test['should_pass']:
                print("✅ 格式验证通过")
                format_success += 1
            else:
                print(f"❌ 格式验证失败: {result.error_message}")
        
        print(f"\n📊 格式验证成功率: {format_success}/{len(format_tests)} ({format_success/len(format_tests)*100:.1f}%)")
        return format_success == len(format_tests)
        
    except Exception as e:
        print(f"❌ 格式验证测试异常: {e}")
        return False

def test_performance():
    """测试性能表现"""
    print("\n⚡ 性能测试")
    print("=" * 60)
    
    try:
        from tradingagents.utils.stock_validator import prepare_stock_data
        
        # 测试真实股票的性能
        performance_tests = [
            {"code": "000001", "market": "A股"},
            {"code": "0700.HK", "market": "港股"},
            {"code": "AAPL", "market": "美股"},
        ]
        
        for test in performance_tests:
            print(f"\n🚀 性能测试: {test['code']} ({test['market']})")
            
            start_time = time.time()
            result = prepare_stock_data(test['code'], test['market'], period_days=7)  # 较短时间测试
            end_time = time.time()
            
            elapsed = end_time - start_time
            print(f"⏱️ 耗时: {elapsed:.2f}秒")
            
            if elapsed > 30:
                print("⚠️ 性能较慢，可能需要优化")
            elif elapsed > 15:
                print("⚡ 性能一般")
            else:
                print("🚀 性能良好")
        
        return True
        
    except Exception as e:
        print(f"❌ 性能测试异常: {e}")
        return False

if __name__ == "__main__":
    print("🧪 股票数据预获取功能完整测试")
    print("=" * 80)
    print("📝 此测试验证新的股票数据预获取和验证机制")
    print("=" * 80)
    
    all_passed = True
    
    # 1. 主要功能测试
    if not test_stock_data_preparation():
        all_passed = False
    
    # 2. 格式验证测试
    if not test_format_validation():
        all_passed = False
    
    # 3. 性能测试
    if not test_performance():
        all_passed = False
    
    # 最终结果
    print(f"\n🏁 最终测试结果")
    print("=" * 80)
    if all_passed:
        print("🎉 所有测试通过！股票数据预获取功能可以投入使用")
        print("✨ 功能特点:")
        print("   - 支持A股、港股、美股数据预获取")
        print("   - 自动缓存历史数据和基本信息")
        print("   - 智能格式验证和错误提示")
        print("   - 合理的性能表现")
    else:
        print("❌ 部分测试失败，建议检查和优化功能实现")
        print("🔍 请检查:")
        print("   - 数据源连接是否正常")
        print("   - 网络连接是否稳定")
        print("   - 相关依赖是否正确安装")
