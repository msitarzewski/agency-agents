#!/usr/bin/env python3
"""
测试增强的Tushare日志功能
验证详细日志是否能帮助追踪数据获取问题
"""

import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_enhanced_logging():
    """测试增强的日志功能"""
    print("🔍 测试增强的Tushare日志功能")
    print("=" * 80)
    
    try:
        from tradingagents.dataflows.data_source_manager import DataSourceManager
        
        manager = DataSourceManager()
        
        # 测试用例1: 正常股票代码
        print("\n📊 测试用例1: 正常股票代码 (000001)")
        print("-" * 60)
        
        symbol = "000001"
        start_date = "2025-01-10"
        end_date = "2025-01-17"
        
        result = manager.get_stock_data(symbol, start_date, end_date)
        
        print(f"结果长度: {len(result) if result else 0}")
        print(f"结果预览: {result[:100] if result else 'None'}")
        
        # 测试用例2: 可能有问题的股票代码
        print("\n📊 测试用例2: 创业板股票 (300033)")
        print("-" * 60)
        
        symbol = "300033"
        start_date = "2025-01-10"
        end_date = "2025-01-17"
        
        result = manager.get_stock_data(symbol, start_date, end_date)
        
        print(f"结果长度: {len(result) if result else 0}")
        print(f"结果预览: {result[:100] if result else 'None'}")
        
        # 测试用例3: 可能不存在的股票代码
        print("\n📊 测试用例3: 可能不存在的股票代码 (999999)")
        print("-" * 60)
        
        symbol = "999999"
        start_date = "2025-01-10"
        end_date = "2025-01-17"
        
        result = manager.get_stock_data(symbol, start_date, end_date)
        
        print(f"结果长度: {len(result) if result else 0}")
        print(f"结果预览: {result[:100] if result else 'None'}")
        
        # 测试用例4: 未来日期范围
        print("\n📊 测试用例4: 未来日期范围")
        print("-" * 60)
        
        symbol = "000001"
        start_date = "2025-12-01"
        end_date = "2025-12-31"
        
        result = manager.get_stock_data(symbol, start_date, end_date)
        
        print(f"结果长度: {len(result) if result else 0}")
        print(f"结果预览: {result[:100] if result else 'None'}")
        
        print("\n✅ 增强日志测试完成")
        print("📋 请查看日志文件以获取详细的调试信息")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_direct_tushare_provider():
    """直接测试Tushare Provider"""
    print("\n🔍 直接测试Tushare Provider")
    print("=" * 80)
    
    try:
        from tradingagents.dataflows.tushare_utils import get_tushare_provider
        
        provider = get_tushare_provider()
        
        if not provider.connected:
            print("❌ Tushare未连接")
            return
        
        # 测试直接调用
        symbol = "300033"
        start_date = "2025-01-10"
        end_date = "2025-01-17"
        
        print(f"📊 直接调用Provider: {symbol}")
        data = provider.get_stock_daily(symbol, start_date, end_date)
        
        if data is not None and not data.empty:
            print(f"✅ 直接调用成功: {len(data)}条数据")
            print(f"📊 数据列: {list(data.columns)}")
            print(f"📊 日期范围: {data['trade_date'].min()} 到 {data['trade_date'].max()}")
        else:
            print(f"❌ 直接调用返回空数据")
            
    except Exception as e:
        print(f"❌ 直接测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_adapter_layer():
    """测试适配器层"""
    print("\n🔍 测试适配器层")
    print("=" * 80)
    
    try:
        from tradingagents.dataflows.tushare_adapter import get_tushare_adapter
        
        adapter = get_tushare_adapter()
        
        if not adapter.provider or not adapter.provider.connected:
            print("❌ 适配器未连接")
            return
        
        # 测试适配器调用
        symbol = "300033"
        start_date = "2025-01-10"
        end_date = "2025-01-17"
        
        print(f"📊 调用适配器: {symbol}")
        data = adapter.get_stock_data(symbol, start_date, end_date)
        
        if data is not None and not data.empty:
            print(f"✅ 适配器调用成功: {len(data)}条数据")
            print(f"📊 数据列: {list(data.columns)}")
        else:
            print(f"❌ 适配器调用返回空数据")
            
    except Exception as e:
        print(f"❌ 适配器测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("🧪 增强日志功能测试")
    print("=" * 80)
    print("📝 此测试将生成详细的日志信息，帮助追踪数据获取问题")
    print("📁 请查看 logs/tradingagents.log 文件获取完整日志")
    print("=" * 80)
    
    # 1. 测试增强日志功能
    test_enhanced_logging()
    
    # 2. 直接测试Provider
    test_direct_tushare_provider()
    
    # 3. 测试适配器层
    test_adapter_layer()
    
    print("\n📋 测试总结")
    print("=" * 60)
    print("✅ 增强日志功能测试完成")
    print("📊 现在每个数据获取步骤都有详细的日志记录")
    print("🔍 包括:")
    print("   - API调用前后的状态")
    print("   - 参数转换过程")
    print("   - 返回数据的详细信息")
    print("   - 异常的完整堆栈")
    print("   - 缓存操作的详细过程")
    print("📁 详细日志请查看: logs/tradingagents.log")

if __name__ == "__main__":
    main()
