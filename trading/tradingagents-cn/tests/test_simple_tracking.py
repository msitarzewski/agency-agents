#!/usr/bin/env python3
"""
简单的股票代码追踪测试
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_data_flow():
    """测试数据流中的股票代码处理"""
    print("\n🔍 数据流股票代码追踪测试")
    print("=" * 80)
    
    # 测试分众传媒 002027
    test_ticker = "002027"
    print(f"📊 测试股票代码: {test_ticker} (分众传媒)")
    
    try:
        # 设置日志级别
        from tradingagents.utils.logging_init import get_logger
        logger = get_logger("default")
        logger.setLevel("INFO")
        
        print(f"\n🔧 测试数据源管理器...")
        
        # 测试数据源管理器
        from tradingagents.dataflows.data_source_manager import get_china_stock_data_unified
        
        result = get_china_stock_data_unified(test_ticker, "2025-07-01", "2025-07-15")
        
        print(f"\n✅ 数据源管理器调用完成")
        print(f"📊 返回结果长度: {len(result) if result else 0}")
        
        # 检查结果中的股票代码
        if result:
            print(f"\n🔍 检查结果中的股票代码...")
            if "002027" in result:
                print("✅ 结果中包含正确的股票代码 002027")
            else:
                print("❌ 结果中不包含正确的股票代码 002027")
                
            if "002021" in result:
                print("⚠️ 结果中包含错误的股票代码 002021")
            else:
                print("✅ 结果中不包含错误的股票代码 002021")
                
            # 显示结果的前500字符
            print(f"\n📄 结果前500字符:")
            print("-" * 60)
            print(result[:500])
            print("-" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tushare_direct():
    """直接测试Tushare接口"""
    print("\n🔧 直接测试Tushare接口")
    print("=" * 80)
    
    test_ticker = "002027"
    
    try:
        # 设置日志级别
        from tradingagents.utils.logging_init import get_logger
        logger.setLevel("INFO")
        
        print(f"\n🔧 测试Tushare接口...")
        
        # 测试Tushare接口
        from tradingagents.dataflows.interface import get_china_stock_data_tushare
        
        result = get_china_stock_data_tushare(test_ticker, "2025-07-01", "2025-07-15")
        
        print(f"\n✅ Tushare接口调用完成")
        print(f"📊 返回结果长度: {len(result) if result else 0}")
        
        # 检查结果中的股票代码
        if result:
            print(f"\n🔍 检查结果中的股票代码...")
            if "002027" in result:
                print("✅ 结果中包含正确的股票代码 002027")
            else:
                print("❌ 结果中不包含正确的股票代码 002027")
                
            if "002021" in result:
                print("⚠️ 结果中包含错误的股票代码 002021")
            else:
                print("✅ 结果中不包含错误的股票代码 002021")
                
            # 显示结果的前500字符
            print(f"\n📄 结果前500字符:")
            print("-" * 60)
            print(result[:500])
            print("-" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tushare_provider():
    """测试Tushare提供器"""
    print("\n🔧 测试Tushare提供器")
    print("=" * 80)
    
    test_ticker = "002027"
    
    try:
        # 设置日志级别
        from tradingagents.utils.logging_init import get_logger
        logger.setLevel("INFO")
        
        print(f"\n🔧 测试Tushare提供器...")
        
        # 测试Tushare提供器
        from tradingagents.dataflows.tushare_utils import get_tushare_provider
        
        provider = get_tushare_provider()
        
        if provider and provider.connected:
            print("✅ Tushare提供器连接成功")
            
            # 测试股票信息获取
            stock_info = provider.get_stock_info(test_ticker)
            print(f"📊 股票信息: {stock_info}")
            
            # 测试股票数据获取
            stock_data = provider.get_stock_daily(test_ticker, "2025-07-01", "2025-07-15")
            print(f"📊 股票数据形状: {stock_data.shape if stock_data is not None and hasattr(stock_data, 'shape') else 'None'}")
            
            if stock_data is not None and not stock_data.empty:
                print(f"📊 股票数据列: {list(stock_data.columns)}")
                if 'ts_code' in stock_data.columns:
                    unique_codes = stock_data['ts_code'].unique()
                    print(f"📊 数据中的ts_code: {unique_codes}")
        else:
            print("❌ Tushare提供器连接失败")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始简单股票代码追踪测试")
    
    # 测试1: Tushare提供器
    success1 = test_tushare_provider()
    
    # 测试2: Tushare接口
    success2 = test_tushare_direct()
    
    # 测试3: 数据源管理器
    success3 = test_data_flow()
    
    if success1 and success2 and success3:
        print("\n✅ 所有测试通过")
    else:
        print("\n❌ 部分测试失败")
