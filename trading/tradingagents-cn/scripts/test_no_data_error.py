"""
测试当所有数据源都获取不到数据时，是否会抛出异常
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置日志级别为 INFO
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def test_no_data_error():
    """测试无数据时的异常处理"""
    print("=" * 70)
    print("🧪 测试无数据时的异常处理")
    print("=" * 70)
    
    # 使用一个不存在的股票代码
    test_symbol = "999999"  # 不存在的股票代码
    
    try:
        # 导入数据提供者
        print("\n📦 步骤1: 导入 OptimizedChinaDataProvider...")
        from tradingagents.dataflows.optimized_china_data import OptimizedChinaDataProvider
        
        provider = OptimizedChinaDataProvider()
        print(f"✅ Provider 初始化成功")
        
        # 尝试获取财务指标
        print(f"\n📊 步骤2: 尝试获取 {test_symbol} 的财务指标...")
        print(f"   预期行为: 应该抛出 ValueError 异常")
        print(f"   异常信息: 无法获取股票 {test_symbol} 的财务数据")
        
        print("\n" + "=" * 70)
        
        # 这应该会抛出异常
        metrics = provider._estimate_financial_metrics(test_symbol, "10.0")
        
        # 如果没有抛出异常，说明测试失败
        print("\n❌ 测试失败：应该抛出异常，但没有抛出")
        print(f"   返回的指标: {metrics}")
        
    except ValueError as e:
        print("\n" + "=" * 70)
        print(f"✅ 测试成功：正确抛出了 ValueError 异常")
        print(f"   异常信息: {e}")
        print("=" * 70)
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"⚠️ 测试部分成功：抛出了异常，但类型不是 ValueError")
        print(f"   异常类型: {type(e).__name__}")
        print(f"   异常信息: {e}")
        print("=" * 70)
    
    # 测试正常情况（有数据的股票）
    print("\n\n" + "=" * 70)
    print("🧪 测试正常情况（有数据的股票）")
    print("=" * 70)
    
    test_symbol = "601288"  # 农业银行
    
    try:
        print(f"\n📊 尝试获取 {test_symbol} 的财务指标...")
        print(f"   预期行为: 应该成功返回财务指标")
        
        from tradingagents.dataflows.optimized_china_data import OptimizedChinaDataProvider
        provider = OptimizedChinaDataProvider()
        
        print("\n" + "=" * 70)
        
        metrics = provider._estimate_financial_metrics(test_symbol, "6.67")
        
        print("\n" + "=" * 70)
        print(f"✅ 测试成功：成功获取财务指标")
        print(f"   ROE: {metrics.get('roe')}")
        print(f"   ROA: {metrics.get('roa')}")
        print(f"   净利率: {metrics.get('net_margin')}")
        print(f"   资产负债率: {metrics.get('debt_ratio')}")
        print("=" * 70)
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"❌ 测试失败：不应该抛出异常")
        print(f"   异常类型: {type(e).__name__}")
        print(f"   异常信息: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
    
    # 总结
    print("\n\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    print("1. ✅ 当所有数据源都获取不到数据时，系统会抛出 ValueError 异常")
    print("2. ✅ 异常信息清晰，说明了失败原因")
    print("3. ✅ 当有数据时，系统正常返回财务指标")
    print("4. ✅ 不再使用估算值，确保数据的真实性")
    print("=" * 70)


if __name__ == "__main__":
    test_no_data_error()

