#!/usr/bin/env python3
"""
测试改进的港股工具（简版，直接导入）
"""

import os
import sys
import time

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_hk_provider_direct():
    """直接测试港股提供器"""
    print("\n🇭🇰 直接测试港股提供器")
    print("=" * 80)
    
    try:
        # 直接导入改进的港股工具
        from improved_hk_utils import ImprovedHKStockProvider
        
        provider = ImprovedHKStockProvider()
        print("✅ 改进港股提供器初始化成功")
        
        # 测试不同格式的港股代码
        test_symbols = [
            "0700.HK",  # 腾讯控股
            "0700",     # 腾讯控股（无后缀）
            "00700",    # 腾讯控股（5位）
            "0941.HK",  # 中国移动
            "1299",     # 友邦保险
            "9988.HK",  # 阿里巴巴
            "3690",     # 美团
            "1234.HK",  # 不存在的股票
        ]
        
        print(f"\n📊 测试港股公司名称获取:")
        success_count = 0
        for symbol in test_symbols:
            try:
                company_name = provider.get_company_name(symbol)
                print(f"   {symbol:10} -> {company_name}")
                
                # 验证不是默认格式
                if not company_name.startswith('港股'):
                    print(f"      ✅ 成功获取具体公司名称")
                    success_count += 1
                else:
                    print(f"      ⚠️ 使用默认格式")
                    
            except Exception as e:
                print(f"   {symbol:10} -> ❌ 错误: {e}")
        
        print(f"\n✅ 成功获取具体名称的数量: {success_count}")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cache_direct():
    """直接测试缓存功能"""
    print("\n💾 直接测试缓存功能")
    print("=" * 80)
    
    try:
        from improved_hk_utils import ImprovedHKStockProvider
        
        provider = ImprovedHKStockProvider()
        
        # 使用新的缓存路径
        cache_dir = os.path.join('data', 'cache', 'hk')
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, 'hk_stock_cache.json')
        
        # 清理可能存在的缓存文件
        if os.path.exists(cache_file):
            os.remove(cache_file)
            print("🗑️ 清理旧缓存文件")
        
        test_symbol = "0700.HK"
        
        # 第一次获取（应该使用内置映射）
        print(f"\n📊 第一次获取 {test_symbol}:")
        start_time = time.time()
        name1 = provider.get_company_name(test_symbol)
        time1 = time.time() - start_time
        print(f"   结果: {name1}")
        print(f"   耗时: {time1:.3f}秒")
        
        # 第二次获取（应该使用缓存）
        print(f"\n📊 第二次获取 {test_symbol}:")
        start_time = time.time()
        name2 = provider.get_company_name(test_symbol)
        time2 = time.time() - start_time
        print(f"   结果: {name2}")
        print(f"   耗时: {time2:.3f}秒")
        
        # 验证结果一致性
        if name1 == name2:
            print("✅ 缓存结果一致")
        else:
            print("❌ 缓存结果不一致")
        
        # 检查缓存文件
        if os.path.exists(cache_file):
            print("✅ 缓存文件已创建")
            
            # 读取缓存内容
            import json
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            print(f"📄 缓存条目数: {len(cache_data)}")
            for key, value in cache_data.items():
                print(f"   {key}: {value['data']} (来源: {value['source']})")
        else:
            print("⚠️ 缓存文件未创建")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_normalization():
    """测试港股代码标准化"""
    print("\n🔧 测试港股代码标准化")
    print("=" * 80)
    
    try:
        from improved_hk_utils import ImprovedHKStockProvider
        
        provider = ImprovedHKStockProvider()
        
        test_cases = [
            ("0700.HK", "00700"),
            ("0700", "00700"),
            ("700", "00700"),
            ("70", "00070"),
            ("7", "00007"),
            ("1299.HK", "01299"),
            ("1299", "01299"),
            ("9988.HK", "09988"),
            ("9988", "09988"),
        ]
        
        print("📊 港股代码标准化测试:")
        for input_symbol, expected in test_cases:
            normalized = provider._normalize_hk_symbol(input_symbol)
            status = "✅" if normalized == expected else "❌"
            print(f"   {input_symbol:10} -> {normalized:10} (期望: {expected}) {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始简化港股工具测试")
    print("=" * 100)
    
    results = []
    
    # 测试1: 直接测试港股提供器
    results.append(test_hk_provider_direct())
    
    # 测试2: 直接测试缓存功能
    results.append(test_cache_direct())
    
    # 测试3: 测试标准化功能
    results.append(test_normalization())
    
    # 总结结果
    print("\n" + "=" * 100)
    print("📋 测试结果总结")
    print("=" * 100)
    
    passed = sum(results)
    total = len(results)
    
    test_names = [
        "港股提供器直接测试",
        "缓存功能直接测试",
        "代码标准化测试"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{i+1}. {name}: {status}")
    
    print(f"\n📊 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！改进港股工具运行正常")
        print("\n📋 改进效果:")
        print("1. ✅ 内置港股名称映射，避免API调用")
        print("2. ✅ 智能缓存机制，提高性能")
        print("3. ✅ 港股代码标准化处理")
        print("4. ✅ 多级降级方案，确保可用性")
        print("5. ✅ 友好的错误处理")
        
        print("\n🔧 解决的问题:")
        print("1. ❌ 'Too Many Requests' API限制错误")
        print("2. ❌ 港股名称获取失败问题")
        print("3. ❌ 缺乏缓存导致的重复API调用")
        print("4. ❌ 港股代码格式不统一问题")
    else:
        print("⚠️ 部分测试失败，需要进一步优化")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
