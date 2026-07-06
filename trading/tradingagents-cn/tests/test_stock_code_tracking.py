#!/usr/bin/env python3
"""
股票代码追踪测试脚本
专门用于调试股票代码在基本面分析中的误判问题
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_stock_code_tracking():
    """测试股票代码在整个流程中的传递"""
    print("\n🔍 股票代码追踪测试")
    print("=" * 80)
    
    # 测试分众传媒 002027
    test_ticker = "002027"
    print(f"📊 测试股票代码: {test_ticker} (分众传媒)")
    
    try:
        # 导入必要的模块
        from tradingagents.agents.utils.agent_utils import AgentUtils
        from tradingagents.utils.logging_init import get_logger
        
        # 设置日志级别为INFO以显示追踪日志
        logger = get_logger("default")
        logger.setLevel("INFO")
        
        print(f"\n🔧 开始调用统一基本面分析工具...")
        
        # 调用统一基本面分析工具
        result = AgentUtils.get_stock_fundamentals_unified(
            ticker=test_ticker,
            start_date='2025-06-01',
            end_date='2025-07-15',
            curr_date='2025-07-15'
        )
        
        print(f"\n✅ 统一基本面分析工具调用完成")
        print(f"📊 返回结果长度: {len(result) if result else 0}")
        
        # 检查结果中是否包含正确的股票代码
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

def test_individual_components():
    """测试各个组件的股票代码处理"""
    print("\n🔧 测试各个组件的股票代码处理")
    print("=" * 80)
    
    test_ticker = "002027"
    
    try:
        # 1. 测试股票市场识别
        print(f"\n1️⃣ 测试股票市场识别...")
        from tradingagents.utils.stock_utils import StockUtils
        market_info = StockUtils.get_market_info(test_ticker)
        print(f"   市场信息: {market_info}")
        
        # 2. 测试Tushare代码标准化
        print(f"\n2️⃣ 测试Tushare代码标准化...")
        from tradingagents.dataflows.tushare_utils import get_tushare_provider
        provider = get_tushare_provider()
        if provider:
            normalized = provider._normalize_symbol(test_ticker)
            print(f"   标准化结果: {test_ticker} -> {normalized}")
        
        # 3. 测试数据源管理器
        print(f"\n3️⃣ 测试数据源管理器...")
        from tradingagents.dataflows.data_source_manager import get_china_stock_data_unified
        data_result = get_china_stock_data_unified(test_ticker, "2025-07-01", "2025-07-15")
        print(f"   数据获取结果长度: {len(data_result) if data_result else 0}")
        
        return True
        
    except Exception as e:
        print(f"❌ 组件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始股票代码追踪测试")
    
    # 测试1: 完整流程追踪
    success1 = test_stock_code_tracking()
    
    # 测试2: 各个组件测试
    success2 = test_individual_components()
    
    if success1 and success2:
        print("\n✅ 所有测试通过")
    else:
        print("\n❌ 部分测试失败")
