#!/usr/bin/env python3
"""
测试数据源降级机制
验证当Tushare返回空数据时是否能正确降级到其他数据源
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_data_source_availability():
    """测试数据源可用性"""
    print("🔍 检查数据源可用性...")
    print("=" * 60)
    
    try:
        from tradingagents.dataflows.data_source_manager import DataSourceManager, ChinaDataSource
        
        manager = DataSourceManager()
        
        print(f"📊 默认数据源: {manager.default_source.value}")
        print(f"📊 当前数据源: {manager.current_source.value}")
        print(f"📊 可用数据源: {[s.value for s in manager.available_sources]}")
        
        return manager
        
    except Exception as e:
        print(f"❌ 数据源管理器初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_fallback_mechanism(manager):
    """测试降级机制"""
    print("\n🔄 测试降级机制...")
    print("=" * 60)
    
    # 测试股票代码 - 选择一个可能在Tushare中没有数据的代码
    test_symbol = "300033"  # 同创科技
    start_date = "2025-01-10"
    end_date = "2025-01-17"
    
    print(f"📊 测试股票: {test_symbol}")
    print(f"📊 时间范围: {start_date} 到 {end_date}")
    
    try:
        # 调用数据获取方法
        result = manager.get_stock_data(test_symbol, start_date, end_date)
        
        print(f"\n📋 获取结果:")
        print(f"   结果长度: {len(result) if result else 0}")
        print(f"   前200字符: {result[:200] if result else 'None'}")
        
        # 检查是否成功
        if result and "❌" not in result and "错误" not in result:
            print("✅ 数据获取成功")
            return True
        else:
            print("⚠️ 数据获取失败或返回错误")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_sources(manager):
    """测试特定数据源"""
    print("\n🎯 测试特定数据源...")
    print("=" * 60)
    
    test_symbol = "000001"  # 平安银行 - 更常见的股票
    start_date = "2025-01-10"
    end_date = "2025-01-17"
    
    # 测试每个可用的数据源
    for source in manager.available_sources:
        print(f"\n📊 测试数据源: {source.value}")
        
        try:
            # 临时切换到该数据源
            original_source = manager.current_source
            manager.current_source = source
            
            result = manager.get_stock_data(test_symbol, start_date, end_date)
            
            # 恢复原数据源
            manager.current_source = original_source
            
            if result and "❌" not in result and "错误" not in result:
                print(f"   ✅ {source.value} 获取成功")
            else:
                print(f"   ❌ {source.value} 获取失败")
                print(f"   错误信息: {result[:100] if result else 'None'}")
                
        except Exception as e:
            print(f"   ❌ {source.value} 异常: {e}")

def main():
    """主函数"""
    print("🧪 数据源降级机制测试")
    print("=" * 80)
    
    # 1. 检查数据源可用性
    manager = test_data_source_availability()
    if not manager:
        print("❌ 无法初始化数据源管理器，测试终止")
        return
    
    # 2. 测试降级机制
    success = test_fallback_mechanism(manager)
    
    # 3. 测试特定数据源
    test_specific_sources(manager)
    
    # 4. 总结
    print("\n📋 测试总结")
    print("=" * 60)
    if success:
        print("✅ 降级机制测试通过")
    else:
        print("⚠️ 降级机制可能存在问题")
    
    print(f"📊 可用数据源数量: {len(manager.available_sources)}")
    print(f"📊 建议: 确保至少有2个数据源可用以支持降级")

if __name__ == "__main__":
    main()
