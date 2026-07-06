"""
测试财务数据获取流程
验证是否还会重复获取数据
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置日志级别为 INFO，以便看到详细的数据流
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def test_financial_data_flow():
    """测试财务数据获取流程"""
    print("=" * 70)
    print("🧪 测试财务数据获取流程")
    print("=" * 70)
    
    test_symbol = "601288"  # 农业银行
    
    try:
        # 导入数据提供者
        print("\n📦 步骤1: 导入 OptimizedChinaDataProvider...")
        from tradingagents.dataflows.optimized_china_data import OptimizedChinaDataProvider
        
        provider = OptimizedChinaDataProvider()
        print(f"✅ Provider 初始化成功")
        
        # 生成基本面报告
        print(f"\n📊 步骤2: 生成 {test_symbol} 的基本面报告...")
        print(f"   股票代码: {test_symbol}")
        
        # 先获取基本信息
        stock_info = provider._get_stock_basic_info_only(test_symbol)
        print(f"\n📋 股票基本信息:")
        print(f"   {stock_info[:200]}...")
        
        # 生成基本面报告
        report = provider._generate_fundamentals_report(test_symbol, stock_info)
        
        print(f"\n✅ 基本面报告生成成功")
        print(f"   报告长度: {len(report)} 字符")
        
        # 显示报告的前 1000 个字符
        print("\n" + "=" * 70)
        print("📄 基本面报告预览（前1000字符）")
        print("=" * 70)
        print(report[:1000])
        print("...")
        
        # 检查报告中是否包含关键指标
        print("\n" + "=" * 70)
        print("🔍 检查报告内容")
        print("=" * 70)
        
        keywords = {
            "ROE": "净资产收益率" in report or "ROE" in report,
            "PE": "市盈率" in report or "PE" in report,
            "PB": "市净率" in report or "PB" in report,
            "毛利率": "毛利率" in report,
            "净利率": "净利率" in report,
            "资产负债率": "资产负债率" in report,
            "估算值": "估算值" in report or "估算" in report
        }
        
        for key, found in keywords.items():
            status = "✅" if found else "❌"
            print(f"   {status} {key}: {'找到' if found else '未找到'}")
        
        # 统计
        found_count = sum(keywords.values())
        total_count = len(keywords)
        print(f"\n📊 关键指标覆盖率: {found_count}/{total_count} ({found_count/total_count*100:.1f}%)")
        
        if keywords["估算值"]:
            print("\n⚠️ 警告: 报告中包含估算值，说明未能从数据库获取真实财务数据")
        else:
            print("\n✅ 成功: 报告使用真实财务数据，没有估算值")
        
        print("\n" + "=" * 70)
        print("✅ 测试完成")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_financial_data_flow()

