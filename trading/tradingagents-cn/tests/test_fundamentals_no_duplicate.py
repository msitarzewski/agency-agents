"""
测试基本面分析师是否还会重复调用工具
"""
import os
import sys
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_fundamentals_analyst():
    """测试基本面分析师"""
    print("=" * 80)
    print("测试基本面分析师 - 检查是否重复调用工具")
    print("=" * 80)
    
    # 导入必要的模块
    from tradingagents.agents.trading_graph import create_trading_graph
    
    # 创建交易图
    print("\n1️⃣ 创建交易图...")
    graph = create_trading_graph()
    
    # 准备测试输入
    test_ticker = "000001"  # 平安银行
    test_date = datetime.now().strftime("%Y-%m-%d")
    
    print(f"\n2️⃣ 测试股票: {test_ticker}")
    print(f"   测试日期: {test_date}")
    
    # 执行基本面分析
    print("\n3️⃣ 开始执行基本面分析...")
    print("   请查看日志，检查以下关键信息：")
    print("   - 是否只调用了1次工具")
    print("   - 是否出现 '跳过重复调用' 的日志")
    print("   - 工具调用总耗时是否减少")
    print("-" * 80)
    
    try:
        result = graph.invoke({
            "company_of_interest": test_ticker,
            "trade_date": test_date,
            "messages": [],
            "fundamentals_report": "",
            "technical_report": "",
            "news_report": "",
            "bull_report": "",
            "bear_report": "",
            "manager_report": "",
            "final_report": ""
        })
        
        print("-" * 80)
        print("\n✅ 基本面分析完成！")
        
        # 检查结果
        if result.get("fundamentals_report"):
            report = result["fundamentals_report"]
            print(f"\n📊 基本面报告长度: {len(report)} 字符")
            print(f"\n📊 报告预览(前500字符):")
            print(report[:500])
            print("...")
        else:
            print("\n⚠️ 未生成基本面报告")
        
        print("\n" + "=" * 80)
        print("测试完成！请检查日志文件 logs/tradingagents.log")
        print("关键检查点：")
        print("1. 搜索 '工具调用' - 应该只有1次工具调用")
        print("2. 搜索 '重复调用检查' - 查看检查逻辑是否生效")
        print("3. 搜索 '跳过强制工具调用' - 如果出现说明修复生效")
        print("4. 搜索 '强制调用统一工具' - 如果出现2次说明仍有问题")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fundamentals_analyst()

